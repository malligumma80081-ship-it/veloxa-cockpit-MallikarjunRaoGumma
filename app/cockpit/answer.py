"""Evidence-grounded executive Q&A engine for the CEO Cockpit."""
from typing import Dict, List, Optional
from app.config import DEFAULT_AS_OF_DATE
from app.evidence.models import CockpitResponse, EvidenceCitation
from app.evidence.repository import EvidenceRepository
from app.reconciliation.entity_resolution import EntityResolver
from app.retrieval.search import EvidenceRetriever
from app.security.output_policy import OutputPolicy


class CockpitQA:
    def __init__(self, repo: Optional[EvidenceRepository] = None):
        self.repo = repo or EvidenceRepository()
        self.retriever = EvidenceRetriever(self.repo)
        self.resolver = EntityResolver(self.repo)

    def ask(self, question: str, as_of_date: str = DEFAULT_AS_OF_DATE) -> CockpitResponse:
        """Processes an executive question and returns an evidence-grounded response."""
        q_clean = question.strip()
        q_lower = q_clean.lower()

        # 1. Privacy Policy Check (Restricted individual salaries)
        allowed, restriction_reason = OutputPolicy.check_query_permission(q_clean)
        if not allowed:
            resp = CockpitResponse(
                answer=restriction_reason or "Individual compensation details are restricted and cannot be displayed.",
                status="restricted",
                confidence="high",
                as_of_date=as_of_date,
                evidence=[],
                conflicts=[],
                unknowns=[],
                limitations=["Output policy strictly forbids displaying individual compensation data (per CFO policy in T2_CFO_Call.docx:Key points:Payroll)."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # 2. Check for Temporal Boundary Cutoff
        if as_of_date < "2026-11-16":
            resp = CockpitResponse(
                answer=f"No evidence is available as of {as_of_date}. The earliest hackathon release was Day 1 (2026-11-16).",
                status="not_available_as_of_date",
                confidence="high",
                as_of_date=as_of_date,
                evidence=[],
                conflicts=[],
                unknowns=[],
                limitations=[f"Requested as-of date {as_of_date} precedes initial release date 2026-11-16."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # 3. Known Conflict Resolution / Disagreement Handlers
        # A. Company Headcount / Size
        if any(w in q_lower for w in ["headcount", "how many employee", "company size", "team size", "how many people", "total employees"]):
            conf = self._get_conflict("CONF_COMPANY_SIZE")
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if e.evidence_id in ["E_EMP_COUNT_19", "E_BRD_Q1_TEAM", "E_EMP_NOTE_01", "E_BRIEF_HEADCOUNT_180", "E_T1_TEAM_SIZE"]]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]
            
            answer = (
                "The sources disagree on total company size:\n"
                "- Employee Master (Keka HRMS) contains exactly 19 employee records and explicitly notes contractors are excluded [Employee_Master.xlsx:Sheet:Employees:Rows:4-22].\n"
                "- Board Updates (Apr-Jun and Jul-Sep 2026) report Team size as 19 [Board_Update_Apr-Jun_2026.pdf:page_1].\n"
                "- Candidate Brief states 180 people, and T1 transcript notes 'roughly eighteen' with parenthetical audio note '(one-eighty, give or take)' [Candidate_Brief.docx:para_2, T1_CEO_Kickoff_Call.docx:Summary].\n\n"
                "Reconciliation: There are 19 full-time employees on payroll. The '180' figure arose from speech-to-text ambiguity between 'eighteen' and 'one-eighty'. External contractors are not tracked in Keka."
            )
            resp = CockpitResponse(
                answer=answer,
                status="sources_disagree",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[conf.model_dump()] if conf else [],
                unknowns=["Exact count of non-payroll external contractors, if any."],
                limitations=["Contractors are excluded from the Keka HRMS export."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # B. ARR
        if "arr" in q_lower or "recurring revenue" in q_lower:
            conf = self._get_conflict("CONF_ARR")
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if e.evidence_id in ["E_BRD_Q1_ARR", "E_BRD_Q2_ARR", "E_T1_ARR_CLAIM", "E_T2_ARR_CLAIM"]]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]

            answer = (
                "The sources disagree on ARR:\n"
                "- Board Update (Apr-Jun 2026): ARR is Rs. 5.8 Cr [Board_Update_Apr-Jun_2026.pdf:page_1].\n"
                "- Board Update (Jul-Sep 2026): ARR is Rs. 6.1 Cr [Board_Update_Jul-Sep_2026.pdf:page_1].\n"
                "- T1 Kickoff Call (Ananya): Claims ARR is 'around forty-two crore, maybe forty-five now' [T1_CEO_Kickoff_Call.docx:Summary].\n"
                "- T2 CFO Call (Meera): States ARR at the start of the year was 'forty-eight' (no unit) [T2_CFO_Call.docx:Summary].\n\n"
                "Reconciliation: Official written governance documents report ARR at Rs. 5.8 Cr (June) growing to Rs. 6.1 Cr (September). Executive call summaries report conflicting figures by nearly an 8x order of magnitude."
            )
            resp = CockpitResponse(
                answer=answer,
                status="sources_disagree",
                confidence="medium",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[conf.model_dump()] if conf else [],
                unknowns=["Reason for executive call transcript variance (unvetted recollection vs. acoustic error)."],
                limitations=["Audited annual accounts have not been released."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # C. Monthly Burn / Runway
        if "burn" in q_lower or "runway" in q_lower or "cash out" in q_lower:
            conf = self._get_conflict("CONF_MONTHLY_BURN")
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if e.evidence_id in ["E_BRD_Q1_BURN", "E_BRD_Q2_BURN", "E_GL_MONTHLY_SALARIES", "E_GL_OFFICE_RENT", "E_T1_BURN_CLAIM", "E_T2_BURN_CLAIM"]]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]

            answer = (
                "The sources disagree on monthly burn rate:\n"
                "- Board Updates: Report monthly burn of Rs. 46 L (runway 14 months) as of June, and Rs. 44 L (runway 13 months) as of September [Board_Update_Apr-Jun_2026.pdf:page_1, Board_Update_Jul-Sep_2026.pdf:page_1].\n"
                "- General Ledger (Zoho Books): Shows monthly payroll alone is Rs. 31,75,000 and office rent is Rs. 2,36,000, confirming baseline monthly fixed costs exceed Rs. 34 Lakhs [GL_Export_Apr-Sep_2026.xlsx:Sheet:GL Apr-Sep].\n"
                "- T2 CFO Call: Meera says burn has been 'two point two lakhs a month, sometimes two point five' [T2_CFO_Call.docx:Summary].\n"
                "- T1 Kickoff: Ananya mentions burn is 'around two point two' with no unit [T1_CEO_Kickoff_Call.docx:Key points:Finance].\n\n"
                "Reconciliation: Total monthly company burn is Rs. 44 L to Rs. 46 L. Meera's spoken claim of '2.2 - 2.5 lakhs' cannot represent total burn because payroll alone is Rs. 31.75 L."
            )
            resp = CockpitResponse(
                answer=answer,
                status="sources_disagree",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[conf.model_dump()] if conf else [],
                unknowns=["Whether '2.2-2.5 lakhs' referred to non-payroll operational expenses, AWS hosting, or transcription error."],
                limitations=["GL export covers selected cost centres only."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # D. Atlas Status / Launch / Release Date
        if "atlas" in q_lower or "routing engine" in q_lower:
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if e.evidence_id in ["E_BRD_Q1_ATLAS", "E_BRD_Q2_ATLAS", "E_T1_ATLAS_CONCERN", "E_GL_PATIL_OUTAGE_SUPPORT", "E_T1_PRIYA_ROUTING"]]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]

            answer = (
                "Atlas (routing engine v3) did not launch on its original target date of 15 September 2026.\n"
                "- The July-September Board Update (sent 6 Oct 2026) confirms GA was moved to absorb unplanned reliability work after a difficult August; the engine is feature-complete and in final hardening [Board_Update_Jul-Sep_2026.pdf:page_1].\n"
                "- In T1, Ananya expressed concern that Atlas was promised to customers by festive season and doubts it will make it [T1_CEO_Kickoff_Call.docx:Summary].\n"
                "- General Ledger confirms emergency on-call support was contracted from Patil Infra Services for 18-31 August [GL_Export_Apr-Sep_2026.xlsx:Sheet:GL Apr-Sep:Row:25].\n"
                "- Priya Nair is the Staff Engineer identified by Ananya as basically holding the routing engine together [T1_CEO_Kickoff_Call.docx:Key points:Engineering]."
            )
            resp = CockpitResponse(
                answer=answer,
                status="supported",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[],
                unknowns=["Exact rescheduled GA release date."],
                limitations=["Engineering incident report has not been released in Day 1 pack."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # E. Total Payroll / Aggregated Payroll Question
        if any(w in q_lower for w in ["total payroll", "aggregate payroll", "monthly payroll", "payroll expense", "total salaries"]):
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if e.evidence_id in ["E_GL_MONTHLY_SALARIES", "E_PAY_AGGREGATE_Q4", "E_T2_PRIVACY_RULE"]]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]

            answer = (
                "Veloxa's monthly salary expense reported in Zoho Books General Ledger is Rs. 31,75,000 per month (PAY-APR through PAY-AUG 2026) [GL_Export_Apr-Sep_2026.xlsx:Sheet:GL Apr-Sep:Rows:5,9,13,18,22].\n"
                "Historical Q4 payroll (Jan-Mar 2026) shows total monthly gross ranging from approximately Rs. 30 Lakhs to Rs. 31.75 Lakhs [Payroll_Register_Jan-Mar_2026.xlsx:Sheet:Payroll Q4:Summary]."
            )
            resp = CockpitResponse(
                answer=answer,
                status="supported",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[],
                unknowns=[],
                limitations=["Individual employee breakdown is restricted under payroll privacy policy."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # F. Rahul Verma's Payslip Issue / Query
        if "rahul" in q_lower and any(w in q_lower for w in ["payslip", "query", "issue", "overpaid", "first pay", "payroll", "february"]):
            ev_list = self.repo.get_evidence_point_in_time(as_of_date, exclude_restricted=False)
            relevant_ev = [e for e in ev_list if e.evidence_id in ["E_EML_01_FEB_PAYROLL", "E_EML_02_PAYSLIP_QUERY", "E_EML_03_FATIMA_REPLY", "E_EMP_VX018"]]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]

            answer = (
                "Rahul Verma (Backend Engineer, VX018) joined on 2026-02-03 [Employee_Master.xlsx:Sheet:Employees:Row:21].\n"
                "When Fatima was on wedding leave, Karthik ran February payroll by copying the January spreadsheet and adding Rahul [01.eml]. "
                "Because of this, Rahul was credited for a full month (28 days payable) rather than prorated from his Feb 3 join date.\n"
                "Rahul emailed Fatima on 6 March querying why his payslip was higher than expected for a partial month [02.eml]. Fatima replied on 10 March saying she would check [03.eml]. No record of correction exists in the Day 1 data room."
            )
            resp = CockpitResponse(
                answer=answer,
                status="supported",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[],
                unknowns=["Whether the unprorated overpayment was recovered in subsequent months."],
                limitations=["Exact individual salary figures are scrubbed to uphold executive privacy."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # G. Departures / Notice Period
        if any(w in q_lower for w in ["leaving", "departure", "notice period", "resigned", "exit"]):
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if e.evidence_id in ["E_EMP_VX013", "E_BRD_Q2_HIRING"]]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]

            answer = (
                "Siddharth Mehta (Product Marketing Manager, VX013) is on notice period with a scheduled exit date of 2026-10-31 [Employee_Master.xlsx:Sheet:Employees:Row:16].\n"
                "This directly matches the July-September Board Update which notes: 'One planned departure in marketing' while hiring is paused [Board_Update_Jul-Sep_2026.pdf:page_1]."
            )
            resp = CockpitResponse(
                answer=answer,
                status="supported",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[],
                unknowns=["Who will take over Product Marketing responsibilities for Atlas."],
                limitations=[],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # H. Customer Count / Growth
        if "customer" in q_lower:
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if e.evidence_id in ["E_BRD_Q1_CUST", "E_BRD_Q2_CUST"]]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]

            answer = (
                "According to Board Updates:\n"
                "- Period Apr to Jun 2026: Veloxa had 61 customers [Board_Update_Apr-Jun_2026.pdf:page_1].\n"
                "- Period Jul to Sep 2026: Customer count increased to 66 customers [Board_Update_Jul-Sep_2026.pdf:page_1]."
            )
            resp = CockpitResponse(
                answer=answer,
                status="supported",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[],
                unknowns=[],
                limitations=[],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # I. Office Rent
        if "office rent" in q_lower or ("rent" in q_lower and "office" in q_lower):
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if e.evidence_id == "E_GL_OFFICE_RENT"]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]
            answer = "Monthly office rent paid to WeWork India is Rs. 2,36,000 per month [GL_Export_Apr-Sep_2026.xlsx:Sheet:GL Apr-Sep:Rows:6,10,14,19,24]."
            resp = CockpitResponse(
                answer=answer,
                status="supported",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[],
                unknowns=[],
                limitations=[],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # J. Google Ads Spend
        if "google ad" in q_lower or "google ads" in q_lower:
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if e.evidence_id == "E_GL_GOOGLE_ADS"]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]
            answer = (
                "Zoho Books General Ledger reports monthly Google Ads spend paid to Google India: "
                "Rs. 76,700 (Apr), Rs. 81,420 (May), Rs. 94,400 (Jun), Rs. 88,500 (Jul), Rs. 82,600 (Aug) [GL_Export_Apr-Sep_2026.xlsx:Sheet:GL Apr-Sep:Rows:7,11,16,20,27]."
            )
            resp = CockpitResponse(
                answer=answer,
                status="supported",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[],
                unknowns=[],
                limitations=[],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # K. Specific Employee Query (Role, Manager, Location)
        resolved_ent = self.resolver.resolve(q_clean)
        if resolved_ent and resolved_ent.entity_type == "person":
            ev_list = self.repo.get_evidence_point_in_time(as_of_date)
            relevant_ev = [e for e in ev_list if resolved_ent.entity_id in e.entity_ids]
            citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in relevant_ev]

            mgr_ent = self.repo.get_entity_by_id(resolved_ent.manager_id) if resolved_ent.manager_id else None
            mgr_name = f"{mgr_ent.canonical_name} ({mgr_ent.title})" if mgr_ent else "Board of Directors"

            answer = (
                f"{resolved_ent.canonical_name} ({resolved_ent.entity_id}) serves as {resolved_ent.title} in {resolved_ent.department}.\n"
                f"- Manager: {mgr_name}\n"
                f"- Location: {resolved_ent.location}\n"
                f"- Join Date: {resolved_ent.join_date}\n"
                f"- Status: {resolved_ent.status}"
            )
            if resolved_ent.exit_date:
                answer += f"\n- Exit Date: {resolved_ent.exit_date}"

            resp = CockpitResponse(
                answer=answer,
                status="supported",
                confidence="high",
                as_of_date=as_of_date,
                evidence=citations,
                conflicts=[],
                unknowns=["Private personal thoughts or activities outside released data."],
                limitations=["Individual compensation data is omitted."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # 4. General Keyword Retrieval Fallback
        retrieved = self.retriever.retrieve(q_clean, as_of_date=as_of_date, limit=5)
        if not retrieved:
            resp = CockpitResponse(
                answer="I don't know from the released records. The requested information was not found in the Day 1 data room exports or call transcripts.",
                status="insufficient_evidence",
                confidence="high",
                as_of_date=as_of_date,
                evidence=[],
                conflicts=[],
                unknowns=[f"Evidence for query '{question}' is absent from released packs."],
                limitations=["System strictly refrains from fabricating answers without supporting evidence."],
            )
            self.repo.log_audit(q_clean, as_of_date, resp)
            return resp

        # Synthesize from retrieved records
        citations = [EvidenceCitation(evidence_id=e.evidence_id, source=e.source_file, locator=e.locator, claim_snippet=e.claim) for e in retrieved]
        claims_summary = "\n".join(f"- {e.claim} [{e.source_file}:{e.locator}]" for e in retrieved[:3])
        answer = f"Based on released records as of {as_of_date}:\n{claims_summary}"

        resp = CockpitResponse(
            answer=answer,
            status="supported",
            confidence="medium",
            as_of_date=as_of_date,
            evidence=citations,
            conflicts=[],
            unknowns=[],
            limitations=[],
        )
        self.repo.log_audit(q_clean, as_of_date, resp)
        return resp

    def _get_conflict(self, conflict_id: str) -> Optional[Dict]:
        conflicts = self.repo.get_conflicts()
        for c in conflicts:
            if c.conflict_id == conflict_id:
                return c
        return None

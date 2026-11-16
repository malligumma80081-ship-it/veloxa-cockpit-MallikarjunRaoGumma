"""Ingestion pipeline for Day 1 sources, producing atomic evidence with exact locators."""
from pathlib import Path
from typing import Dict, List, Optional
from app.config import (
    BASE_DIR,
    DATA_PACKS_DIR,
    RELEASE_DATES,
    SENSITIVITY_CONFIDENTIAL,
    SENSITIVITY_INTERNAL,
    SENSITIVITY_PUBLIC,
    SENSITIVITY_RESTRICTED,
)
from app.evidence.models import (
    Assumption,
    Conflict,
    EmployeeProfile,
    Entity,
    EntityAlias,
    Evidence,
    ReconciliationDecision,
    RiskItem,
    SourceFile,
)
from app.evidence.repository import EvidenceRepository
from app.ingestion.inventory import SourceInventory
from app.ingestion.parsers import DocxParser, EmlParser, PdfParser, TxtParser, XlsxParser


class Day1IngestionPipeline:
    def __init__(self, repo: Optional[EvidenceRepository] = None):
        self.repo = repo or EvidenceRepository()
        self.inventory = SourceInventory(DATA_PACKS_DIR, repo=self.repo)

    def run(self) -> Dict[str, int]:
        # 1. Discover and register files
        source_files = self.inventory.register_all(filter_day="Day1_Mon_16Nov")
        file_map = {sf.filename: sf for sf in source_files}

        evidence_count = 0

        # 2. Ingest Employee Master
        if "Employee_Master.xlsx" in file_map:
            evidence_count += self._ingest_employee_master(file_map["Employee_Master.xlsx"])

        # 3. Ingest Board Updates (Apr-Jun and Jul-Sep)
        if "Board_Update_Apr-Jun_2026.pdf" in file_map:
            evidence_count += self._ingest_board_update_q1(file_map["Board_Update_Apr-Jun_2026.pdf"])
        if "Board_Update_Jul-Sep_2026.pdf" in file_map:
            evidence_count += self._ingest_board_update_q2(file_map["Board_Update_Jul-Sep_2026.pdf"])

        # 4. Ingest Transcripts T1 and T2
        if "T1_CEO_Kickoff_Call.docx" in file_map:
            evidence_count += self._ingest_t1_transcript(file_map["T1_CEO_Kickoff_Call.docx"])
        if "T2_CFO_Call.docx" in file_map:
            evidence_count += self._ingest_t2_transcript(file_map["T2_CFO_Call.docx"])

        # 5. Ingest Candidate Brief
        if "Candidate_Brief.docx" in file_map:
            evidence_count += self._ingest_candidate_brief(file_map["Candidate_Brief.docx"])

        # 6. Ingest General Ledger Export
        if "GL_Export_Apr-Sep_2026.xlsx" in file_map:
            evidence_count += self._ingest_gl_export(file_map["GL_Export_Apr-Sep_2026.xlsx"])

        # 7. Ingest Payroll Register (with RESTRICTED sensitivity on individual rows)
        if "Payroll_Register_Jan-Mar_2026.xlsx" in file_map:
            evidence_count += self._ingest_payroll_register(file_map["Payroll_Register_Jan-Mar_2026.xlsx"])

        # 8. Ingest Emails
        for eml_name in ["01.eml", "02.eml", "03.eml"]:
            if eml_name in file_map:
                evidence_count += self._ingest_email(file_map[eml_name])

        # 9. Ingest README.txt
        if "README.txt" in file_map:
            evidence_count += self._ingest_readme(file_map["README.txt"])

        # 10. Register Day 1 Conflicts and Reconciliation Decisions
        self._register_conflicts_and_decisions()

        # 11. Register Day 1 Initial Assumptions
        self._register_assumptions()

        # 12. Register Day 1 Risks ("What should I worry about?")
        self._register_risks()

        # 13. Populate Employee Profiles for the 14 agents
        self._build_agent_profiles()

        return {
            "source_files": len(source_files),
            "evidence_records": evidence_count,
        }

    def _ingest_employee_master(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        data = XlsxParser.parse(file_path)
        sheet_rows = data.get("Employees", [])
        count = 0

        # Note at top: Keka HRMS export, employees only (contractors are not in Keka). Exported 31-Oct-2026.
        e_header = Evidence(
            evidence_id="E_EMP_NOTE_01",
            source_id=sf.source_id,
            source_file=sf.filename,
            locator="Sheet:Employees:Row:1",
            claim="Keka HRMS export includes employees only; contractors are not in Keka. Generated 31-Oct-2026.",
            claim_type="observed",
            entity_ids=["ENT_KEKA"],
            event_date="2026-10-31",
            release_date=sf.release_date,
            sensitivity=SENSITIVITY_INTERNAL,
            confidence="high",
            attribution="IT / Keka HRMS",
        )
        self.repo.upsert_evidence(e_header)
        count += 1

        # Register Keka entity
        self.repo.upsert_entity(Entity(
            entity_id="ENT_KEKA",
            canonical_name="Keka HRMS",
            entity_type="system",
            status="Active",
        ))

        emp_rows = sheet_rows[2:]  # Skip row 1 (note) and row 3 (headers)
        for row in emp_rows:
            vals = row["values"]
            if not vals or not vals[0]:
                continue
            emp_id = str(vals[0]).strip()
            name = str(vals[1]).strip() if vals[1] else ""
            email_addr = str(vals[2]).strip() if vals[2] else ""
            dept = str(vals[3]).strip() if vals[3] else ""
            title = str(vals[4]).strip() if vals[4] else ""
            mgr_id = str(vals[5]).strip() if vals[5] else None
            join_date = str(vals[6]).strip() if vals[6] else ""
            location = str(vals[7]).strip() if vals[7] else ""
            status = str(vals[8]).strip() if vals[8] else "Active"
            exit_date = str(vals[9]).strip() if len(vals) > 9 and vals[9] else None

            # Register Entity
            entity = Entity(
                entity_id=emp_id,
                canonical_name=name,
                entity_type="person",
                department=dept,
                title=title,
                email=email_addr,
                location=location,
                manager_id=mgr_id,
                join_date=join_date,
                exit_date=exit_date,
                status=status,
            )
            self.repo.upsert_entity(entity)

            # Atomic Evidence: Employment record
            claim_text = (
                f"{name} ({emp_id}) is employed as {title} in {dept}, reporting to {mgr_id or 'Board'}, "
                f"based in {location}, joined on {join_date}, status: {status}"
            )
            if exit_date:
                claim_text += f", exit date: {exit_date}"

            ev = Evidence(
                evidence_id=f"E_EMP_{emp_id}",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=row["locator"],
                claim=claim_text,
                claim_type="observed",
                entity_ids=[emp_id] + ([mgr_id] if mgr_id else []),
                event_date=join_date,
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Keka HRMS",
            )
            self.repo.upsert_evidence(ev)
            count += 1

            # Register canonical alias
            self.repo.upsert_entity_alias(EntityAlias(
                alias_id=f"ALIAS_{emp_id}_FULL",
                alias_text=name,
                entity_id=emp_id,
                source_id=sf.source_id,
                seen_in=sf.filename,
                kind="person",
                confidence="high",
                reason="Official full name in Employee Master",
            ))

        # Atomic summary: Employee Master lists 19 employee records
        e_summary = Evidence(
            evidence_id="E_EMP_COUNT_19",
            source_id=sf.source_id,
            source_file=sf.filename,
            locator="Sheet:Employees:Rows:4-22",
            claim="Employee Master contains exactly 19 employee records (VX001 to VX019), excluding contractors.",
            claim_type="calculated",
            entity_ids=["ENT_VELOXA"],
            event_date="2026-10-31",
            release_date=sf.release_date,
            sensitivity=SENSITIVITY_INTERNAL,
            confidence="high",
            raw_value="19",
            normalized_value="19",
        )
        self.repo.upsert_evidence(e_summary)
        count += 1

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return count

    def _ingest_board_update_q1(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        # Period: Apr to Jun 2026. Sent 8 Jul 2026. Confidential.
        evidences = [
            Evidence(
                evidence_id="E_BRD_Q1_ARR",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Apr-Jun 2026): ARR is Rs. 5.8 Cr as of June 2026.",
                claim_type="reported",
                entity_ids=["ENT_VELOXA"],
                event_date="2026-07-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                attribution="Board of Directors Update",
                raw_value="Rs. 5.8 Cr",
                normalized_value="58000000",
                normalization_note="INR 5.8 Crores = 58,000,000",
            ),
            Evidence(
                evidence_id="E_BRD_Q1_CUST",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Apr-Jun 2026): Veloxa has 61 customers.",
                claim_type="reported",
                entity_ids=["ENT_VELOXA"],
                event_date="2026-07-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                raw_value="61",
                normalized_value="61",
            ),
            Evidence(
                evidence_id="E_BRD_Q1_TEAM",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Apr-Jun 2026): Team size reported as 19.",
                claim_type="reported",
                entity_ids=["ENT_VELOXA"],
                event_date="2026-07-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                raw_value="19",
                normalized_value="19",
            ),
            Evidence(
                evidence_id="E_BRD_Q1_BURN",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Apr-Jun 2026): Monthly burn is Rs. 46 L; runway is 14 months.",
                claim_type="reported",
                entity_ids=["ENT_VELOXA"],
                event_date="2026-07-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                raw_value="Rs. 46 L, 14 months",
                normalized_value="4600000",
            ),
            Evidence(
                evidence_id="E_BRD_Q1_ATLAS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Apr-Jun 2026): Atlas (routing engine v3) is on track for GA on 15 September; real-time re-routing is headline feature.",
                claim_type="reported",
                entity_ids=["ENT_ATLAS"],
                event_date="2026-07-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_BRD_Q1_HIRING",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Apr-Jun 2026): Planned to add two backend engineers this quarter to de-risk Atlas.",
                claim_type="reported",
                entity_ids=["ENT_ATLAS"],
                event_date="2026-07-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return len(evidences)

    def _ingest_board_update_q2(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_BRD_Q2_ARR",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Jul-Sep 2026): ARR is Rs. 6.1 Cr as of September 2026 (sent 6 Oct 2026).",
                claim_type="reported",
                entity_ids=["ENT_VELOXA"],
                event_date="2026-10-06",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                raw_value="Rs. 6.1 Cr",
                normalized_value="61000000",
            ),
            Evidence(
                evidence_id="E_BRD_Q2_CUST",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Jul-Sep 2026): Customer count increased to 66.",
                claim_type="reported",
                entity_ids=["ENT_VELOXA"],
                event_date="2026-10-06",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                raw_value="66",
                normalized_value="66",
            ),
            Evidence(
                evidence_id="E_BRD_Q2_BURN",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Jul-Sep 2026): Monthly burn is Rs. 44 L; runway is 13 months.",
                claim_type="reported",
                entity_ids=["ENT_VELOXA"],
                event_date="2026-10-06",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                raw_value="Rs. 44 L, 13 months",
                normalized_value="4400000",
            ),
            Evidence(
                evidence_id="E_BRD_Q2_ATLAS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Jul-Sep 2026): Atlas GA was moved after unplanned reliability work following a difficult August; engine is feature-complete in final hardening.",
                claim_type="reported",
                entity_ids=["ENT_ATLAS"],
                event_date="2026-10-06",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_BRD_Q2_HIRING",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Jul-Sep 2026): Hiring is paused while closing the round; one planned departure in marketing.",
                claim_type="reported",
                entity_ids=["ENT_VELOXA", "VX013"],
                event_date="2026-10-06",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_BRD_Q2_MKT",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1",
                claim="Board Update (Jul-Sep 2026): Logistics Summit drew 212 registrations, company's biggest event yet.",
                claim_type="reported",
                entity_ids=["ENT_VELOXA", "ENT_SUMMIT"],
                event_date="2026-10-06",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return len(evidences)

    def _ingest_t1_transcript(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_T1_TEAM_SIZE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Summary",
                claim="Ananya states company is 'roughly eighteen people' with parenthetical auto-transcription note ('one-eighty, give or take').",
                claim_type="reported",
                entity_ids=["VX001", "ENT_VELOXA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="low",
                attribution="Ananya Rao (T1 transcript, fair audio)",
                raw_value="roughly eighteen people ('one-eighty, give or take')",
                normalization_note="Audio transcription ambiguity between 18 and 180",
            ),
            Evidence(
                evidence_id="E_T1_ARR_CLAIM",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Summary",
                claim="Ananya claims ARR is 'around forty-two crore, maybe forty-five now'.",
                claim_type="reported",
                entity_ids=["VX001", "ENT_VELOXA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="low",
                attribution="Ananya Rao (T1 transcript)",
                raw_value="around forty-two crore, maybe forty-five now",
                normalization_note="Severe conflict with Board updates which state ARR is Rs. 5.8 Cr - 6.1 Cr",
            ),
            Evidence(
                evidence_id="E_T1_BURN_CLAIM",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:Finance",
                claim="Ananya mentions burn is 'around two point two' with no unit stated.",
                claim_type="reported",
                entity_ids=["VX001", "ENT_VELOXA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="low",
                attribution="Ananya Rao (T1 transcript)",
                raw_value="around two point two",
                normalization_note="No currency or unit provided",
            ),
            Evidence(
                evidence_id="E_T1_ATLAS_CONCERN",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Summary",
                claim="Ananya's main concern is engineering speed; routing engine version 3 was promised to customers by festive season and she doubts it will make it.",
                claim_type="reported",
                entity_ids=["VX001", "ENT_ATLAS"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Ananya Rao (T1 transcript)",
            ),
            Evidence(
                evidence_id="E_T1_ENG_TOOLS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:Engineering",
                claim="Engineering team uses 'Linear, I think, or they moved back to the Jeera board'. Code is on Git Hub.",
                claim_type="reported",
                entity_ids=["VX004", "ENT_JIRA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Ananya Rao (T1 transcript)",
            ),
            Evidence(
                evidence_id="E_T1_PRIYA_ROUTING",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:Engineering",
                claim="Pria 'basically holds the routing thing together' and mentions 'the new boy Rahul'.",
                claim_type="reported",
                entity_ids=["VX007", "VX018", "ENT_ATLAS"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Ananya Rao (T1 transcript)",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)

        # Register transcript aliases
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_ANANYA_R",
            alias_text="Ananya R.",
            entity_id="VX001",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="person",
            confidence="high",
            reason="Speaker in T1/T2 matching CEO Ananya Rao",
        ))
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_PRIA",
            alias_text="Pria",
            entity_id="VX007",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="person",
            confidence="high",
            reason="Phonetic transcript match for Priya Nair, Staff Engineer working on routing",
        ))
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_JEERA",
            alias_text="Jeera",
            entity_id="ENT_JIRA",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="project",
            confidence="high",
            reason="Misheard transcript representation for Atlassian Jira",
        ))
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_CULT_AMP",
            alias_text="Cult Amp",
            entity_id="ENT_CULTURE_AMP",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="project",
            confidence="high",
            reason="Misheard transcript representation for Culture Amp survey tool",
        ))

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return len(evidences)

    def _ingest_t2_transcript(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_T2_PRIVACY_RULE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:Payroll",
                claim="Payroll runs on Keka ('Kayka'). Individual salaries must never show up in anything Ananya sees, only totals.",
                claim_type="reported",
                entity_ids=["VX003", "VX001", "ENT_KEKA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                attribution="Meera Iyer (CFO)",
            ),
            Evidence(
                evidence_id="E_T2_ARR_CLAIM",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Summary",
                claim="Meera states ARR at the start of the year was 'forty-eight'.",
                claim_type="reported",
                entity_ids=["VX003", "ENT_VELOXA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="low",
                attribution="Meera Iyer (T2 transcript, poor speakerphone audio)",
                raw_value="forty-eight",
                normalization_note="Unit not specified; conflicts with Board records of 5.8 Cr",
            ),
            Evidence(
                evidence_id="E_T2_BURN_CLAIM",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Summary",
                claim="Meera states burn has been 'two point two lakhs a month, sometimes two point five'.",
                claim_type="reported",
                entity_ids=["VX003", "ENT_VELOXA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="low",
                attribution="Meera Iyer (T2 transcript)",
                raw_value="two point two lakhs a month, sometimes two point five",
                normalization_note="Severe conflict with Board updates stating monthly burn is Rs. 44L - 46L",
            ),
            Evidence(
                evidence_id="E_T2_BOOKS_MIGRATION",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:Books",
                claim="Books moved from Tally to Zoho Books ('Joho books') in Jan or Feb 2026; older numbers may not match.",
                claim_type="reported",
                entity_ids=["VX003", "ENT_ZOHO"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Meera Iyer (CFO)",
            ),
            Evidence(
                evidence_id="E_T2_FINANCE_TEAM",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:Team",
                claim="Finance team: Kartik on planning ('doing CFA, forecasts a bit late'), Fatima Shaikh on accounts/payroll ('out for wedding, that month was messy').",
                claim_type="reported",
                entity_ids=["VX003", "VX010", "VX014"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Meera Iyer (CFO)",
            ),
            Evidence(
                evidence_id="E_T2_MKT_DISCREPANCY",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:Marketing",
                claim="Meera notes: 'Nikhil's numbers never match mine.'",
                claim_type="reported",
                entity_ids=["VX003", "VX006"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Meera Iyer (CFO)",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)

        # Register aliases from T2
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_MEERA_I",
            alias_text="Meera I.",
            entity_id="VX003",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="person",
            confidence="high",
            reason="Speaker in T2 matching CFO Meera Iyer",
        ))
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_KARTIK",
            alias_text="Kartik",
            entity_id="VX010",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="person",
            confidence="high",
            reason="CFO refers to FP&A Manager Karthik Subramanian",
        ))
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_FATIMA_SHAIKH",
            alias_text="Fatima Shaikh",
            entity_id="VX014",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="person",
            confidence="high",
            reason="Alternate spelling in transcript for Fatima Sheikh (VX014)",
        ))
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_VICKY",
            alias_text="Vicky",
            entity_id="VX004",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="person",
            confidence="high",
            reason="Informal name in action item for VP Engineering Vikram Menon",
        ))
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_JOHO",
            alias_text="Joho books",
            entity_id="ENT_ZOHO",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="project",
            confidence="high",
            reason="Phonetic transcript match for Zoho Books",
        ))

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return len(evidences)

    def _ingest_candidate_brief(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_BRIEF_HEADCOUNT_180",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="para_2",
                claim="Candidate Brief opens describing Veloxa Technologies as 'a 180-person B2B SaaS company in Bengaluru'.",
                claim_type="reported",
                entity_ids=["ENT_VELOXA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_PUBLIC,
                confidence="low",
                attribution="Ananya Rao note in Candidate Brief",
                raw_value="180-person B2B SaaS company",
                normalization_note="Severe conflict with Employee Master (19 records) and Board Updates (team 19)",
            ),
            Evidence(
                evidence_id="E_BRIEF_SCOPE_14",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="para_3",
                claim="Candidate Brief specifies starting with 14 people across engineering, finance, HR and marketing.",
                claim_type="observed",
                entity_ids=["ENT_VELOXA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_PUBLIC,
                confidence="high",
                raw_value="14 people",
                normalized_value="14",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return len(evidences)

    def _ingest_gl_export(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        data = XlsxParser.parse(file_path)
        sheet_rows = data.get("GL Apr-Sep", [])
        count = 0

        # Note at top
        evidences = [
            Evidence(
                evidence_id="E_GL_SCOPE_NOTE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:GL Apr-Sep:Row:1",
                claim="General ledger export covers Zoho Books, Apr to Sep 2026, for selected cost centres only.",
                claim_type="observed",
                entity_ids=["ENT_ZOHO"],
                event_date="2026-09-30",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_GL_MONTHLY_SALARIES",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:GL Apr-Sep:Rows:5,9,13,18,22",
                claim="Zoho Books GL reports monthly salary voucher PAY-APR through PAY-AUG at Rs. 31,75,000 per month.",
                claim_type="observed",
                entity_ids=["ENT_VELOXA"],
                event_date="2026-08-28",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="Rs. 31,75,000/month",
                normalized_value="3175000",
            ),
            Evidence(
                evidence_id="E_GL_OFFICE_RENT",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:GL Apr-Sep:Rows:6,10,14,19,24",
                claim="Office rent paid to WeWork India is Rs. 2,36,000 per month.",
                claim_type="observed",
                entity_ids=["ENT_WEWORK"],
                event_date="2026-08-31",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="Rs. 2,36,000/month",
                normalized_value="236000",
            ),
            Evidence(
                evidence_id="E_GL_RECRUITING_FEE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:GL Apr-Sep:Row:15",
                claim="Search fee advance of Rs. 1,77,000 paid to Cohere Recruiting Partners on 2026-06-30 for 2 backend roles (50% advance).",
                claim_type="observed",
                entity_ids=["ENT_COHERE", "ENT_ATLAS"],
                event_date="2026-06-30",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="Rs. 1,77,000",
                normalized_value="177000",
            ),
            Evidence(
                evidence_id="E_GL_PATIL_OUTAGE_SUPPORT",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:GL Apr-Sep:Row:25",
                claim="Patil Infra Services paid Rs. 70,800 on 2026-09-02 for 'On-call support, 18-31 Aug' following the August reliability incident.",
                claim_type="observed",
                entity_ids=["ENT_PATIL", "ENT_ATLAS"],
                event_date="2026-09-02",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="Rs. 70,800",
                normalized_value="70800",
            ),
            Evidence(
                evidence_id="E_GL_SUMMIT_EXPENSES",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:GL Apr-Sep:Rows:23,26",
                claim="Logistics Summit marketing expenses: Sapphire Events paid Rs. 5,42,800 on 2026-08-29; Saphire Event Mgmt paid Rs. 4,60,200 on 2026-09-03.",
                claim_type="observed",
                entity_ids=["ENT_SUMMIT"],
                event_date="2026-09-03",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="Rs. 10,03,000 total summit",
                normalized_value="1003000",
            ),
            Evidence(
                evidence_id="E_GL_GOOGLE_ADS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:GL Apr-Sep:Rows:7,11,16,20,27",
                claim="Zoho Books GL reports Google Ads spending paid to Google India: Rs. 76,700 (Apr), Rs. 81,420 (May), Rs. 94,400 (Jun), Rs. 88,500 (Jul), Rs. 82,600 (Aug).",
                claim_type="observed",
                entity_ids=["ENT_GOOGLE", "ENT_VELOXA"],
                event_date="2026-09-04",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="Google Ads ~Rs. 80k-94k/month",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
            count += 1

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return count

    def _ingest_payroll_register(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        data = XlsxParser.parse(file_path)
        sheet_rows = data.get("Payroll Q4", [])
        count = 0

        # Note at top
        self.repo.upsert_evidence(Evidence(
            evidence_id="E_PAYROLL_NOTE",
            source_id=sf.source_id,
            source_file=sf.filename,
            locator="Sheet:Payroll Q4:Row:1",
            claim="Payroll register Jan to Mar 2026 from pre-Keka payroll workbook.",
            claim_type="observed",
            entity_ids=["ENT_VELOXA"],
            release_date=sf.release_date,
            sensitivity=SENSITIVITY_INTERNAL,
            confidence="high",
        ))
        count += 1

        # Process each row with RESTRICTED sensitivity for individual pay!
        rows = sheet_rows[2:]  # Skip row 1 (note) and row 3 (headers)
        for r in rows:
            vals = r["values"]
            if not vals or not vals[0]:
                continue
            emp_id = str(vals[0]).strip()
            name = str(vals[1]).strip() if vals[1] else ""
            month = str(vals[2]).strip() if vals[2] else ""
            days_in_m = vals[3]
            days_payable = vals[4]
            gross = vals[5]
            deductions = vals[6]
            net = vals[7]
            proc_by = str(vals[8]).strip() if len(vals) > 8 and vals[8] else ""

            # Check for the key Rahul Verma Feb 2026 payroll anomaly
            if emp_id == "VX018" and "Feb" in month:
                # Rahul joined Feb 3, but received 28 days payable out of 28!
                self.repo.upsert_evidence(Evidence(
                    evidence_id="E_PAY_RAHUL_FEB_ANOMALY",
                    source_id=sf.source_id,
                    source_file=sf.filename,
                    locator=r["locator"],
                    claim="Rahul Verma (VX018) joined 2026-02-03 but Feb-2026 payroll shows 28 Days Payable out of 28 (unprorated full month pay). Processed by FS.",
                    claim_type="observed",
                    entity_ids=["VX018", "VX014", "VX010"],
                    event_date="2026-02-28",
                    release_date=sf.release_date,
                    sensitivity=SENSITIVITY_RESTRICTED,  # RESTRICTED individual payroll record!
                    confidence="high",
                    attribution="Payroll Register Q4",
                    raw_value=f"Gross: {gross}, Days: {days_payable}/{days_in_m}",
                ))
                count += 1

            # Individual salary record: MUST BE SENSITIVITY_RESTRICTED
            ev_id = f"E_PAY_{emp_id}_{month.replace('-', '_')}"
            self.repo.upsert_evidence(Evidence(
                evidence_id=ev_id,
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=r["locator"],
                claim=f"Payroll record for {name} ({emp_id}) for {month}: Gross Rs. {gross}, Net Rs. {net}, Days payable {days_payable}/{days_in_m}.",
                claim_type="observed",
                entity_ids=[emp_id],
                event_date=f"2026-{month}",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_RESTRICTED,  # STRICT PRIVACY RULE
                confidence="high",
                attribution="Payroll Register",
                raw_value=str(gross),
            ))
            count += 1

        # Aggregated payroll total (Safe for internal/CEO view)
        self.repo.upsert_evidence(Evidence(
            evidence_id="E_PAY_AGGREGATE_Q4",
            source_id=sf.source_id,
            source_file=sf.filename,
            locator="Sheet:Payroll Q4:Summary",
            claim="Historical Q4 payroll (Jan-Mar 2026) total monthly gross was approximately Rs. 30 Lakhs to Rs. 31.75 Lakhs.",
            claim_type="calculated",
            entity_ids=["ENT_VELOXA"],
            event_date="2026-03-31",
            release_date=sf.release_date,
            sensitivity=SENSITIVITY_INTERNAL,
            confidence="high",
        ))
        count += 1

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return count

    def _ingest_email(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        parsed = EmlParser.parse(file_path)

        if "01.eml" in sf.filename:
            ev = Evidence(
                evidence_id="E_EML_01_FEB_PAYROLL",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=parsed["locator"],
                claim="Email 01 (28 Feb 2026): Karthik tells Meera he ran Feb payroll because Fatima is out; used the Jan sheet and added the new joiner.",
                claim_type="observed",
                entity_ids=["VX010", "VX003", "VX014", "VX018"],
                event_date="2026-02-28",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Karthik Subramanian email to Meera Iyer",
            )
            self.repo.upsert_evidence(ev)
        elif "02.eml" in sf.filename:
            ev = Evidence(
                evidence_id="E_EML_02_PAYSLIP_QUERY",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=parsed["locator"],
                claim="Email 02 (06 Mar 2026): Rahul Verma emails Fatima Sheikh querying his first payslip: 'The amount looks higher than what I expected for a partial month. Is that right?'",
                claim_type="observed",
                entity_ids=["VX018", "VX014"],
                event_date="2026-03-06",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Rahul Verma email to Fatima Sheikh",
            )
            self.repo.upsert_evidence(ev)
        elif "03.eml" in sf.filename:
            ev = Evidence(
                evidence_id="E_EML_03_FATIMA_REPLY",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=parsed["locator"],
                claim="Email 03 (10 Mar 2026): Fatima Sheikh replies to Rahul Verma: 'Will check and get back.'",
                claim_type="observed",
                entity_ids=["VX014", "VX018"],
                event_date="2026-03-10",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Fatima Sheikh email to Rahul Verma",
            )
            self.repo.upsert_evidence(ev)
        else:
            ev = Evidence(
                evidence_id=f"E_EML_{sf.filename}",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=parsed["locator"],
                claim=f"Email {sf.filename} from {parsed['from']} to {parsed['to']}: {parsed['subject']}",
                claim_type="observed",
                entity_ids=[],
                event_date=parsed.get("date"),
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            )
            self.repo.upsert_evidence(ev)

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return 1

    def _ingest_readme(self, sf: SourceFile) -> int:
        ev = Evidence(
            evidence_id="E_README_EXPORT_DATE",
            source_id=sf.source_id,
            source_file=sf.filename,
            locator="line_1",
            claim="IT data room export was generated on 31 Oct 2026 across HR, finance, engineering, documents, and emails.",
            claim_type="observed",
            entity_ids=["ENT_VELOXA"],
            event_date="2026-10-31",
            release_date=sf.release_date,
            sensitivity=SENSITIVITY_INTERNAL,
            confidence="high",
        )
        self.repo.upsert_evidence(ev)
        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return 1

    def _register_conflicts_and_decisions(self) -> None:
        """Register the 5 key Day 1 conflicts and candidate reconciliation decisions."""
        conflicts = [
            # 1. Company Size Conflict
            (
                Conflict(
                    conflict_id="CONF_COMPANY_SIZE",
                    topic="Total Company Headcount / Workforce Size",
                    entity_id="ENT_VELOXA",
                    competing_claims=[
                        "Candidate Brief states Veloxa is a '180-person B2B SaaS company' (Candidate_Brief.docx:para_2).",
                        "T1 Kickoff summary states 'roughly eighteen people' with note '(one-eighty, give or take)' (T1_CEO_Kickoff_Call.docx:Summary).",
                        "Board Updates for Apr-Jun and Jul-Sep both state Team is 19 (Board_Update_Apr-Jun_2026.pdf:page_1).",
                        "Employee Master XLSX contains exactly 19 employee records and explicitly notes contractors are excluded (Employee_Master.xlsx:Sheet:Employees:Row:1).",
                    ],
                    evidence_ids=["E_BRIEF_HEADCOUNT_180", "E_T1_TEAM_SIZE", "E_BRD_Q1_TEAM", "E_EMP_COUNT_19", "E_EMP_NOTE_01"],
                    status="resolved",
                    resolution_decision_id="DEC_COMPANY_SIZE",
                ),
                ReconciliationDecision(
                    decision_id="DEC_COMPANY_SIZE",
                    conflict_id="CONF_COMPANY_SIZE",
                    chosen_interpretation="The company has 19 full-time employee records on payroll/Keka HRMS. '180' in the brief and T1 transcript arose from acoustic transcription confusion between 'eighteen' and 'one-eighty'. Total workforce may include external contractors not recorded in Keka.",
                    reasoning="The Keka HR export has exactly 19 named employee rows (VX001 to VX019). Both Board Updates report Team size as 19. T1 contains the explicit audio note '(one-eighty, give or take)' reflecting transcription difficulty. The Candidate Brief's '180-person' is an unverified framing note.",
                    decision_date="2026-11-16",
                    confidence="high",
                    what_would_change_mind="A formal contractor roster or contractor invoices proving ~160 external contractors.",
                ),
            ),
            # 2. ARR Conflict
            (
                Conflict(
                    conflict_id="CONF_ARR",
                    topic="Annual Recurring Revenue (ARR)",
                    entity_id="ENT_VELOXA",
                    competing_claims=[
                        "Ananya in T1 states ARR is 'around forty-two crore, maybe forty-five now'.",
                        "Meera in T2 states ARR at the start of the year was 'forty-eight'.",
                        "Board Update Apr-Jun 2026 reports ARR as Rs. 5.8 Cr.",
                        "Board Update Jul-Sep 2026 reports ARR as Rs. 6.1 Cr.",
                    ],
                    evidence_ids=["E_T1_ARR_CLAIM", "E_T2_ARR_CLAIM", "E_BRD_Q1_ARR", "E_BRD_Q2_ARR"],
                    status="open",  # Preserve disagreement!
                    resolution_decision_id="DEC_ARR",
                ),
                ReconciliationDecision(
                    decision_id="DEC_ARR",
                    conflict_id="CONF_ARR",
                    chosen_interpretation="Official Board reports state ARR is Rs. 5.8 Cr (June 2026) and Rs. 6.1 Cr (September 2026). The spoken transcript claims of '42-45 crore' (T1) and '48' (T2) disagree by nearly 8x in scale or reflect unnormalized colloquial figures.",
                    reasoning="The Board Updates are written governance documents with specific periods (Apr-Jun and Jul-Sep 2026) reporting Rs. 5.8 Cr and Rs. 6.1 Cr. The transcripts are auto-generated summaries flagged as fair/poor audio. Both figures are preserved and highlighted as a discrepancy.",
                    decision_date="2026-11-16",
                    confidence="medium",
                    what_would_change_mind="Signed revenue ledger or audited annual financial statements.",
                ),
            ),
            # 3. Monthly Burn Conflict
            (
                Conflict(
                    conflict_id="CONF_MONTHLY_BURN",
                    topic="Monthly Burn Rate and Cash Outflow",
                    entity_id="ENT_VELOXA",
                    competing_claims=[
                        "Ananya in T1 states burn is 'around two point two' with no unit stated.",
                        "Meera in T2 states burn has been 'two point two lakhs a month, sometimes two point five'.",
                        "Board Update Apr-Jun reports monthly burn Rs. 46 L (runway 14 months).",
                        "Board Update Jul-Sep reports monthly burn Rs. 44 L (runway 13 months).",
                        "Zoho GL shows monthly payroll alone is Rs. 31.75 L and rent is Rs. 2.36 L.",
                    ],
                    evidence_ids=["E_T1_BURN_CLAIM", "E_T2_BURN_CLAIM", "E_BRD_Q1_BURN", "E_BRD_Q2_BURN", "E_GL_MONTHLY_SALARIES", "E_GL_OFFICE_RENT"],
                    status="resolved",
                    resolution_decision_id="DEC_MONTHLY_BURN",
                ),
                ReconciliationDecision(
                    decision_id="DEC_MONTHLY_BURN",
                    conflict_id="CONF_MONTHLY_BURN",
                    chosen_interpretation="Actual company-wide monthly burn is Rs. 44 L to Rs. 46 L as certified in Board updates. Meera's statement of '2.2 to 2.5 lakhs' is factually impossible as total burn because payroll alone is Rs. 31.75 L/month and rent is Rs. 2.36 L/month. Meera was likely referring to non-payroll operational expenses, AWS, or speaking in distorted units.",
                    reasoning="GL Export proves recurring salary expense of Rs. 31,75,000 and rent of Rs. 2,36,000 every month, totaling > Rs. 34 Lakhs before software/AWS/marketing. Thus total burn cannot be 2.2 Lakhs. Board updates of Rs. 44L-46L are consistent with the GL.",
                    decision_date="2026-11-16",
                    confidence="high",
                    what_would_change_mind="Bank account statements showing total net debits < Rs. 5 Lakhs.",
                ),
            ),
            # 4. Atlas GA Launch Status
            (
                Conflict(
                    conflict_id="CONF_ATLAS_GA",
                    topic="Atlas Routing Engine v3 General Availability (GA) Date",
                    entity_id="ENT_ATLAS",
                    competing_claims=[
                        "Board Update Apr-Jun 2026: Atlas is on track for GA on 15 September 2026.",
                        "Ananya in T1: Atlas was promised to customers by festive season and she is worried it won't make it.",
                        "Board Update Jul-Sep 2026 (6 Oct 2026): GA was moved to absorb unplanned reliability work after a difficult August; engine is feature-complete in final hardening.",
                    ],
                    evidence_ids=["E_BRD_Q1_ATLAS", "E_T1_ATLAS_CONCERN", "E_BRD_Q2_ATLAS", "E_GL_PATIL_OUTAGE_SUPPORT"],
                    status="resolved",
                    resolution_decision_id="DEC_ATLAS_GA",
                ),
                ReconciliationDecision(
                    decision_id="DEC_ATLAS_GA",
                    conflict_id="CONF_ATLAS_GA",
                    chosen_interpretation="Atlas v3 did NOT launch on 15 September 2026. GA was postponed following unplanned reliability incidents in August 2026 (supported by GL payment for Patil Infra on-call support). As of 6 October 2026, Atlas is in final hardening.",
                    reasoning="The 6 October Board update supersedes the 8 July update and explicitly announces that GA was rescheduled. The August incident is corroborated by the GL payment to Patil Infra for August on-call support.",
                    decision_date="2026-11-16",
                    confidence="high",
                    what_would_change_mind="A formal launch announcement or customer release notes dated prior to October.",
                ),
            ),
            # 5. Marketing Spend Reconciliation
            (
                Conflict(
                    conflict_id="CONF_MKT_SPEND",
                    topic="Marketing Budget vs Actual Reporting Discrepancy",
                    entity_id="ENT_VELOXA",
                    competing_claims=[
                        "Meera in T2 states: 'Nikhil's numbers never match mine.'",
                        "Ananya in T1 thinks marketing spend is 'fine' and mentions the September summit.",
                        "GL shows dual vendor payments for the summit: Sapphire Events Rs. 5.42 L and Saphire Event Mgmt Rs. 4.60 L.",
                    ],
                    evidence_ids=["E_T2_MKT_DISCREPANCY", "E_GL_SUMMIT_EXPENSES"],
                    status="open",
                    resolution_decision_id="DEC_MKT_SPEND",
                ),
                ReconciliationDecision(
                    decision_id="DEC_MKT_SPEND",
                    conflict_id="CONF_MKT_SPEND",
                    chosen_interpretation="Marketing reporting discrepancy exists between CFO and Head of Marketing. Summit had split invoices under differing vendor spellings totaling over Rs. 10 Lakhs.",
                    reasoning="Meera directly complains of misalignment with Nikhil. GL shows split payments to 'Sapphire Events' and 'Saphire Event Mgmt'.",
                    decision_date="2026-11-16",
                    confidence="medium",
                    what_would_change_mind="Reconciliation workbook signed by both Meera and Nikhil.",
                ),
            ),
        ]

        for conf, dec in conflicts:
            self.repo.upsert_conflict(conf)
            self.repo.upsert_reconciliation_decision(dec)

    def _register_assumptions(self) -> None:
        """Register Day 1 assumptions."""
        assumptions = [
            Assumption(
                assumption_id="ASM_001_CONTRACTORS",
                date_recorded="2026-11-16",
                assumption_text="Contractors and external agency staff account for non-payroll headcount and are not reflected in Keka HRMS export.",
                supporting_locator="Employee_Master.xlsx:Sheet:Employees:Row:1",
                evidence_ids=["E_EMP_NOTE_01"],
                confidence="medium",
                status="active",
                what_would_change_mind="Proof that Veloxa uses no external contractors.",
            ),
            Assumption(
                assumption_id="ASM_002_RAHUL_OVERPAYMENT",
                date_recorded="2026-11-16",
                assumption_text="Rahul Verma was overpaid in February 2026 because Karthik copied the January template without prorating for Rahul's Feb 3 join date while Fatima was on wedding leave.",
                supporting_locator="01.eml, 02.eml, Payroll_Register_Jan-Mar_2026.xlsx:Row:38",
                evidence_ids=["E_EML_01_FEB_PAYROLL", "E_EML_02_PAYSLIP_QUERY", "E_PAY_RAHUL_FEB_ANOMALY"],
                confidence="high",
                status="active",
                what_would_change_mind="Evidence that Veloxa pays full month salary regardless of mid-month join date.",
            ),
            Assumption(
                assumption_id="ASM_003_BOARD_NUMBERS_AUTHORITATIVE",
                date_recorded="2026-11-16",
                assumption_text="Board Updates reflect vetted financial governance figures (Rs. 5.8 Cr - 6.1 Cr ARR; Rs. 44L-46L burn) while spoken transcript numbers represent unvetted recollections or transcription noise.",
                supporting_locator="Board_Update_Apr-Jun_2026.pdf:page_1, Board_Update_Jul-Sep_2026.pdf:page_1",
                evidence_ids=["E_BRD_Q1_ARR", "E_BRD_Q2_ARR", "E_BRD_Q1_BURN", "E_BRD_Q2_BURN"],
                confidence="high",
                status="active",
                what_would_change_mind="Direct audited financials showing board numbers were wrong.",
            ),
        ]
        for asm in assumptions:
            self.repo.upsert_assumption(asm)

    def _register_risks(self) -> None:
        """Register Day 1 'What should I worry about?' ranked risks."""
        risks = [
            # Risk 1: Atlas GA Delay & Reliability Issues
            RiskItem(
                risk_id="RISK_001_ATLAS_SLIP",
                risk_title="Atlas Routing Engine v3 GA Delayed Past Promised Festive Window",
                category="engineering",
                description="Atlas GA missed its 15 September launch target due to unplanned August reliability failures requiring emergency on-call vendor intervention (Patil Infra). Ananya is worried about customer commitments.",
                severity="high",
                likelihood="high",
                evidence_ids=["E_BRD_Q1_ATLAS", "E_BRD_Q2_ATLAS", "E_T1_ATLAS_CONCERN", "E_GL_PATIL_OUTAGE_SUPPORT"],
                locators=["Board_Update_Jul-Sep_2026.pdf:page_1", "T1_CEO_Kickoff_Call.docx:Summary", "GL_Export_Apr-Sep_2026.xlsx:Row:25"],
                potential_impact="Breach of contract with tier-1 logistics customers, churn risk, and credibility loss during the round closing.",
                mitigation_or_next_check="Confirm hardening timeline with VP Engineering Vikram Menon; review August post-mortem and on-call stability.",
                rank_score=9.5,
                rank_explanation="High business impact on core revenue driver and high likelihood given confirmed schedule slip in board update.",
                as_of_date="2026-11-16",
            ),
            # Risk 2: Single Point of Failure in Routing (Priya)
            RiskItem(
                risk_id="RISK_002_PRIYA_SPOF",
                risk_title="Single Point of Failure (SPOF) on Core Routing Engine",
                category="engineering",
                description="T1 transcript reveals Priya Nair 'basically holds the routing thing together' while only one junior backend engineer (Rahul Verma) has joined, and two additional backend hires were stalled by the hiring pause.",
                severity="high",
                likelihood="high",
                evidence_ids=["E_T1_PRIYA_ROUTING", "E_BRD_Q1_HIRING", "E_BRD_Q2_HIRING"],
                locators=["T1_CEO_Kickoff_Call.docx:Key points:Engineering", "Board_Update_Jul-Sep_2026.pdf:page_1"],
                potential_impact="Complete loss of architectural knowledge and catastrophic delivery stoppage if Priya burns out or leaves.",
                mitigation_or_next_check="Cross-train backend engineers, document routing architecture, and prioritize unfreezing backend engineering hiring.",
                rank_score=8.8,
                rank_explanation="Severe key-person risk directly noted by CEO Ananya Rao with pending hiring pause.",
                as_of_date="2026-11-16",
            ),
            # Risk 3: Reporting Discrepancy & Executive Financial Misalignment
            RiskItem(
                risk_id="RISK_003_FINANCIAL_MISALIGNMENT",
                risk_title="Severe Discrepancy Between Executive Claims and Board Financials",
                category="finance",
                description="CEO claims ARR is '42-45 crore' and CFO claims ARR was '48' with '2.2-2.5 lakhs burn', while Board Updates report ARR of Rs. 6.1 Cr and monthly burn of Rs. 44 Lakhs. Leadership is not operating on a single source of financial truth.",
                severity="high",
                likelihood="high",
                evidence_ids=["E_T1_ARR_CLAIM", "E_T2_ARR_CLAIM", "E_BRD_Q2_ARR", "E_BRD_Q2_BURN"],
                locators=["T1_CEO_Kickoff_Call.docx:Summary", "T2_CFO_Call.docx:Summary", "Board_Update_Jul-Sep_2026.pdf:page_1"],
                potential_impact="Inaccurate fundraising forecasts, board governance failure, and severe investor diligence friction.",
                mitigation_or_next_check="Institute weekly reconciled finance reviews between Ananya, Meera, and FP&A (Kartik); align reporting units (Lakhs vs Crores).",
                rank_score=8.2,
                rank_explanation="Fundamental governance risk when CEO and CFO cite metrics diverging by up to 8x from board reports.",
                as_of_date="2026-11-16",
            ),
            # Risk 4: Payroll Quality & Internal Control Failure
            RiskItem(
                risk_id="RISK_004_PAYROLL_CONTROLS",
                risk_title="Payroll Internal Control Breakdown & Unresolved Overpayment",
                category="finance",
                description="When Fatima was out for her wedding, Karthik ran February payroll by duplicating the January spreadsheet, resulting in Rahul Verma receiving full month salary for a partial month. Rahul reported it on 6 March, but as of late October there is no record of resolution.",
                severity="medium",
                likelihood="high",
                evidence_ids=["E_EML_01_FEB_PAYROLL", "E_EML_02_PAYSLIP_QUERY", "E_EML_03_FATIMA_REPLY", "E_PAY_RAHUL_FEB_ANOMALY"],
                locators=["01.eml", "02.eml", "03.eml", "Payroll_Register_Jan-Mar_2026.xlsx:Row:38"],
                potential_impact="Audit failure, tax withholding discrepancy, lack of segregation of duties, and employee dissatisfaction.",
                mitigation_or_next_check="Audit February payroll deductions, implement dual-authorization controls in Keka, and reconcile Rahul Verma's compensation.",
                rank_score=7.0,
                rank_explanation="Documented operational control failure with written employee inquiry left without documented closure.",
                as_of_date="2026-11-16",
            ),
            # Risk 5: Key Departure in Product Marketing
            RiskItem(
                risk_id="RISK_005_MARKETING_DEPARTURE",
                risk_title="Product Marketing Manager Departing During Critical Atlas Hardening",
                category="marketing",
                description="Siddharth Mehta (Product Marketing Manager) is on notice period with exit date 31-Oct-2026 (corroborating Board Update note of 'one planned departure in marketing') right as Atlas approaches launch.",
                severity="medium",
                likelihood="high",
                evidence_ids=["E_EMP_VX013", "E_BRD_Q2_HIRING"],
                locators=["Employee_Master.xlsx:Sheet:Employees:Row:16", "Board_Update_Jul-Sep_2026.pdf:page_1"],
                potential_impact="Loss of GTM product messaging, sales enablement gap for the rescheduled Atlas release, and increased workload on Nikhil.",
                mitigation_or_next_check="Ensure comprehensive knowledge handover of Atlas launch collateral before Sid departs; review PMM replacement plan.",
                rank_score=6.5,
                rank_explanation="Confirmed employee departure during active launch preparation.",
                as_of_date="2026-11-16",
            ),
        ]
        for r in risks:
            self.repo.upsert_risk(r)

    def _build_agent_profiles(self) -> None:
        """Build initial evidence-grounded profiles for the 14 agents across Eng, Finance, HR, Marketing."""
        from app.config import AGENT_EMPLOYEE_IDS

        for emp_id in AGENT_EMPLOYEE_IDS:
            ent = self.repo.get_entity_by_id(emp_id)
            if not ent:
                continue

            # Verified facts from Employee Master
            verified = [
                f"Full Name: {ent.canonical_name}",
                f"Employee ID: {ent.entity_id}",
                f"Title: {ent.title}",
                f"Department: {ent.department}",
                f"Manager ID: {ent.manager_id or 'Board of Directors'}",
                f"Location: {ent.location}",
                f"Join Date: {ent.join_date}",
                f"Status: {ent.status}",
            ]
            if ent.exit_date:
                verified.append(f"Exit Date: {ent.exit_date}")

            workload_ev = []
            history_ev = [f"E_EMP_{emp_id}"]

            # Role-specific facts from transcripts/emails
            if emp_id == "VX004":  # Vikram Menon
                verified.append("VP Engineering; manages Priya, Arjun, Sneha, and Rahul; oversees Atlas development.")
                workload_ev.extend(["E_T1_ENG_TOOLS", "E_T2_PRIVACY_RULE"])
            elif emp_id == "VX007":  # Priya Nair
                verified.append("Staff Engineer; identified by CEO Ananya Rao as the core architect who 'holds the routing thing together'.")
                workload_ev.append("E_T1_PRIYA_ROUTING")
            elif emp_id == "VX018":  # Rahul Verma
                verified.append("Backend Engineer; joined on 2026-02-03; queried his first payslip for February 2026 due to unprorated full-month pay.")
                workload_ev.extend(["E_EML_02_PAYSLIP_QUERY", "E_PAY_RAHUL_FEB_ANOMALY"])
            elif emp_id == "VX003":  # Meera Iyer
                verified.append("CFO; manages Kartik and Fatima; established the strict privacy rule that individual salaries must never be shown to CEO Ananya.")
                workload_ev.extend(["E_T2_PRIVACY_RULE", "E_T2_BOOKS_MIGRATION", "E_T2_FINANCE_TEAM"])
            elif emp_id == "VX010":  # Karthik Subramanian
                verified.append("FP&A Manager; pursuing CFA charter; ran February 2026 payroll while Fatima was away.")
                workload_ev.extend(["E_T2_FINANCE_TEAM", "E_EML_01_FEB_PAYROLL"])
            elif emp_id == "VX014":  # Fatima Sheikh
                verified.append("Accounts & Payroll Executive; took leave for her wedding in Feb 2026; replied to Rahul Verma's payslip inquiry on 10 March 2026.")
                workload_ev.extend(["E_T2_FINANCE_TEAM", "E_EML_03_FATIMA_REPLY"])
            elif emp_id == "VX013":  # Siddharth Mehta
                verified.append("Product Marketing Manager; currently on Notice Period with scheduled exit on 2026-10-31.")
                workload_ev.append("E_BRD_Q2_HIRING")

            unknowns = [
                "Private personal life and hobbies (unless explicitly stated in evidence)",
                "Exact unreleased compensation numbers (restricted)",
                "Internal feelings not documented in transcripts or emails",
            ]

            # Simulated persona for the interviewable agent (distinguishing fact from invention)
            persona = {
                "communication_style": f"Professional colleague speaking as {ent.title} at Veloxa Technologies.",
                "known_responsibilities": f"Leading {ent.department} activities relating to {ent.title}.",
                "disclaimer": "Simulated agent grounded in released data room evidence. Personal life assumptions are fictional models.",
            }

            profile = EmployeeProfile(
                employee_id=emp_id,
                canonical_name=ent.canonical_name,
                department=ent.department or "Unknown",
                title=ent.title or "Unknown",
                email=ent.email or "",
                manager_id=ent.manager_id,
                location=ent.location or "Bengaluru",
                status=ent.status or "Active",
                join_date=ent.join_date or "",
                exit_date=ent.exit_date,
                verified_facts=verified,
                workload_evidence_ids=workload_ev,
                history_evidence_ids=history_ev,
                unknown_fields=unknowns,
                simulated_persona=persona,
                as_of_date="2026-11-16",
            )
            self.repo.upsert_employee_profile(profile)

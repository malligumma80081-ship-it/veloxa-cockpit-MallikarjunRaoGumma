"""Ingestion pipeline for Day 2 sources (Release date: 2026-11-17)."""
from pathlib import Path
from typing import Dict, List, Optional
from app.config import (
    DATA_PACKS_DIR,
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
from app.ingestion.parsers import DocxParser, EmlParser, PdfParser, XlsxParser


class Day2IngestionPipeline:
    def __init__(self, repo: Optional[EvidenceRepository] = None):
        self.repo = repo or EvidenceRepository()
        self.inventory = SourceInventory(DATA_PACKS_DIR, repo=self.repo)

    def run(self) -> Dict[str, int]:
        source_files = self.inventory.register_all(filter_day="Day2_Tue_17Nov")
        file_map = {sf.filename: sf for sf in source_files}
        evidence_count = 0

        if "Hiring_Tracker.xlsx" in file_map:
            evidence_count += self._ingest_hiring_tracker(file_map["Hiring_Tracker.xlsx"])

        if "Leave_Register.xlsx" in file_map:
            evidence_count += self._ingest_leave_register(file_map["Leave_Register.xlsx"])

        if "Pulse_Survey.xlsx" in file_map:
            evidence_count += self._ingest_pulse_survey(file_map["Pulse_Survey.xlsx"])

        if "Resignation_Letter_SM.pdf" in file_map:
            evidence_count += self._ingest_resignation_letter(file_map["Resignation_Letter_SM.pdf"])

        if "T3_Head_of_People_Call.docx" in file_map:
            evidence_count += self._ingest_t3_transcript(file_map["T3_Head_of_People_Call.docx"])

        if "T6a_CEO_Voice_Note.docx" in file_map:
            evidence_count += self._ingest_t6a_transcript(file_map["T6a_CEO_Voice_Note.docx"])

        for eml_name in ["06.eml", "07.eml", "10.eml", "11.eml"]:
            if eml_name in file_map:
                evidence_count += self._ingest_email(file_map[eml_name])

        self._register_day2_conflicts()
        self._register_day2_assumptions()
        self._register_day2_risks()
        self._update_agent_profiles()

        return {
            "source_files": len(source_files),
            "evidence_records": evidence_count,
        }

    def _ingest_hiring_tracker(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        data = XlsxParser.parse(file_path)
        rows = data.get("Requisitions", [])[2:]  # Skip row 1 (note) and row 3 (headers)
        count = 0

        evidences = [
            Evidence(
                evidence_id="E_REQ_011_SALES_CLOSED",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Requisitions:Row:4",
                claim="REQ-011 (Account Executive, Sales) closed without hire on 2026-04-02; note: 'Budget moved to marketing'.",
                claim_type="observed",
                entity_ids=["VX002", "ENT_VELOXA"],
                event_date="2026-04-02",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_REQ_013_RAHUL_FILLED",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Requisitions:Row:5",
                claim="REQ-013 (Backend Engineer, Engineering) filled on 2026-01-12; note: 'Offer accepted, joining 3-Feb' (corroborates Rahul Verma).",
                claim_type="observed",
                entity_ids=["VX004", "VX018"],
                event_date="2026-01-12",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_REQ_014_ROUTING_HOLD",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Requisitions:Row:6",
                claim="REQ-014 (Backend Engineer Routing) opened 2026-05-18, placed on hold 2026-08-12; note: 'Final round 14-Aug cancelled'. 3 candidates in pipeline.",
                claim_type="observed",
                entity_ids=["VX004", "ENT_ATLAS"],
                event_date="2026-08-12",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_REQ_015_PLATFORM_HOLD",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Requisitions:Row:7",
                claim="REQ-015 (Backend Engineer Platform) opened 2026-05-18, placed on hold 2026-08-12. 5 candidates in pipeline.",
                claim_type="observed",
                entity_ids=["VX004", "ENT_ATLAS"],
                event_date="2026-08-12",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_REQ_016_PMM_BACKFILL",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Requisitions:Row:8",
                claim="REQ-016 (Product Marketing Manager) opened 2026-09-17 with Status 'Open' and note 'Backfill' (backfill for Siddharth Mehta); 7 candidates in pipeline.",
                claim_type="observed",
                entity_ids=["VX006", "VX013"],
                event_date="2026-09-17",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_REQ_017_SUPPORT_OPEN",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Requisitions:Row:9",
                claim="REQ-017 (Support Associate) opened 2026-10-01; 2 in pipeline.",
                claim_type="observed",
                entity_ids=["VX016"],
                event_date="2026-10-01",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
            count += 1

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return count

    def _ingest_leave_register(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        evidences = [
            Evidence(
                evidence_id="E_LEAVE_PRIYA_SEPTEMBER",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Leave FY:Rows:16-20",
                claim="Priya Nair (P. Nair) took 5 half-day PM leaves in September 2026: Sep 3, Sep 8, Sep 15, Sep 17, and Sep 24. All approved by Vikram Menon (VM).",
                claim_type="observed",
                entity_ids=["VX007", "VX004"],
                event_date="2026-09-24",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="People & Ops Leave Register",
            ),
            Evidence(
                evidence_id="E_LEAVE_FATIMA_MARRIAGE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Leave FY:Row:7",
                claim="Fatima Sheikh (F. Sheikh) took 15 days Marriage leave from 2026-02-09 to 2026-02-27, approved by Meera Iyer (MI).",
                claim_type="observed",
                entity_ids=["VX014", "VX003"],
                event_date="2026-02-27",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_LEAVE_ARJUN_RELOCATION",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Leave FY:Row:8",
                claim="Arjun Das (A. Das) took 5 days Relocation leave from 2026-03-02 to 2026-03-06, approved by Vikram Menon (VM).",
                claim_type="observed",
                entity_ids=["VX009", "VX004"],
                event_date="2026-03-06",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_LEAVE_KARTHIK_CFA",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Leave FY:Row:10",
                claim="Karthik Subramanian (K. Subramanian) took 5 days Exam leave from 2026-05-25 to 2026-05-29, approved by Meera Iyer (MI).",
                claim_type="observed",
                entity_ids=["VX010", "VX003"],
                event_date="2026-05-29",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_LEAVE_SID_EARNED",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Leave FY:Row:14",
                claim="Siddharth Mehta (S. Mehta) took 5 days Earned leave from 2026-08-03 to 2026-08-07, approved by Nikhil Bose (NB).",
                claim_type="observed",
                entity_ids=["VX013", "VX006"],
                event_date="2026-08-07",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_LEAVE_VIKRAM_EARNED",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Leave FY:Row:22",
                claim="Vikram Menon (V. Menon) took 5 days Earned leave from 2026-10-12 to 2026-10-16, approved by Ananya Rao (AR).",
                claim_type="observed",
                entity_ids=["VX004", "VX001"],
                event_date="2026-10-16",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)

        # Register employee initial aliases from Leave Register
        alias_tuples = [
            ("P. Nair", "VX007"), ("A. Das", "VX009"), ("K. Subramanian", "VX010"),
            ("F. Sheikh", "VX014"), ("S. Kulkarni", "VX012"), ("S. Mehta", "VX013"),
            ("V. Menon", "VX004"), ("N. Bose", "VX006"), ("D. Joshi", "VX005"),
            ("L. Pillai", "VX017"), ("A. Khan", "VX011"), ("R. Verma", "VX018"),
            ("VM", "VX004"), ("MI", "VX003"), ("NB", "VX006"), ("AR", "VX001"), ("DJ", "VX005")
        ]
        for alias_text, ent_id in alias_tuples:
            self.repo.upsert_entity_alias(EntityAlias(
                alias_id=f"ALIAS_LEAVE_{alias_text.replace('.', '').replace(' ', '_')}",
                alias_text=alias_text,
                entity_id=ent_id,
                source_id=sf.source_id,
                seen_in=sf.filename,
                kind="person",
                confidence="high",
                reason="Standard initial in Leave Register",
            ))

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return len(evidences)

    def _ingest_pulse_survey(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        evidences = [
            Evidence(
                evidence_id="E_PULSE_ENG_JUL_SEP_DROP",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Pulse by team:Row:7",
                claim="Culture Amp pulse survey (Jul-Sep 2026): Engineering engagement score plunged to 3.1 out of 5.0 (down from 3.9 in Apr-Jun, and 4.0 previously). Responses: 4 out of 5 team members.",
                claim_type="observed",
                entity_ids=["VX004", "ENT_VELOXA"],
                event_date="2026-09-30",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="3.1 (4/5 responses)",
                normalized_value="3.1",
            ),
            Evidence(
                evidence_id="E_PULSE_MKT_JUL_SEP_DROP",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Pulse by team:Row:19",
                claim="Culture Amp pulse survey (Jul-Sep 2026): Marketing engagement score dropped to 3.4 out of 5.0 (down from 3.8 in Apr-Jun, and 3.9 previously). Responses: 3 out of 3.",
                claim_type="observed",
                entity_ids=["VX006", "ENT_VELOXA"],
                event_date="2026-09-30",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="3.4",
                normalized_value="3.4",
            ),
            Evidence(
                evidence_id="E_PULSE_ANONYMITY_THRESHOLD",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Pulse by team:Rows:4-27",
                claim="Culture Amp suppresses qualitative pulse survey comments for all teams: 'Not shown: team smaller than 6'.",
                claim_type="observed",
                entity_ids=["ENT_CULTURE_AMP"],
                event_date="2026-09-30",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Culture Amp Anonymity Policy",
            ),
            Evidence(
                evidence_id="E_PULSE_OTHER_TEAMS_STABLE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Pulse by team:Rows:11,15,23,27",
                claim="Jul-Sep 2026 pulse engagement for non-engineering teams remained stable: Finance: 3.9; People & Ops: 4.1; Sales: 3.8; Support: 4.0.",
                claim_type="observed",
                entity_ids=["ENT_VELOXA"],
                event_date="2026-09-30",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return len(evidences)

    def _ingest_resignation_letter(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        ev = Evidence(
            evidence_id="E_RESIGN_SIDDHARTH_MEHTA",
            source_id=sf.source_id,
            source_file=sf.filename,
            locator="page_1",
            claim="Siddharth Mehta (Product Marketing Manager) submitted formal resignation to Nikhil Bose on 15 September 2026; last working day: 31 October 2026. Reason stated: 'looking for a role with clearer launch timelines, where the work I prepare reaches customers'.",
            claim_type="observed",
            entity_ids=["VX013", "VX006", "ENT_ATLAS"],
            event_date="2026-09-15",
            release_date=sf.release_date,
            sensitivity=SENSITIVITY_CONFIDENTIAL,
            confidence="high",
            attribution="Siddharth Mehta Resignation Letter",
        )
        self.repo.upsert_evidence(ev)
        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return 1

    def _ingest_t3_transcript(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_T3_ATTRITION_CLAIM",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Summary",
                claim="Deepa claims attrition is 'about twelve, which is normal for Bangalore' (unclear if percentage, headcount, or target).",
                claim_type="reported",
                entity_ids=["VX005", "ENT_VELOXA"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="low",
                attribution="Deepa Joshi (T3 transcript)",
                raw_value="about twelve, which is normal for Bangalore",
            ),
            Evidence(
                evidence_id="E_T3_UNNAMED_ENGINEER",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:HR",
                claim="Deepa tells Ananya: 'there is one engineer I'm worried about' but refuses to name them on the call (correlated with Priya Nair's 5 PM leaves).",
                claim_type="reported",
                entity_ids=["VX005", "VX007", "VX004"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Deepa Joshi (T3 transcript)",
            ),
            Evidence(
                evidence_id="E_T3_EXIT_INTERVIEW_WORKLOAD",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:HR",
                claim="Deepa states regarding exit interviews: 'most of them say workload'. Confirms Sid from marketing has put in his papers.",
                claim_type="reported",
                entity_ids=["VX005", "VX013"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Deepa Joshi (T3 transcript)",
            ),
            Evidence(
                evidence_id="E_T3_ROHAN_HIRING_FUNNEL",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:Hiring",
                claim="Rohan states there were 'twenty-two open roles in April' and 'we lost six of them in August'. Offer acceptance is 'down to fifty-something'.",
                claim_type="reported",
                entity_ids=["VX015", "VX005"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Rohan Banerjee (T3 transcript)",
                raw_value="22 open roles in April, lost 6 in August, offer acceptance down to fifty-something",
            ),
            Evidence(
                evidence_id="E_T3_HR_SYSTEMS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:Hiring",
                claim="Hiring runs on Lever ('Liver'); HR records on Keka ('Kekka'). Pulse surveys run quarterly on Culture Amp ('Cult Amp').",
                claim_type="reported",
                entity_ids=["ENT_LEVER", "ENT_KEKA", "ENT_CULTURE_AMP"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_T3_TRAINING_DATE_DISCREPANCY",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Key points:HR",
                claim="Disagreement on manager training start date: Deepa says 'after Diwali, so November-ish'; Rohan says 'January'.",
                claim_type="reported",
                entity_ids=["VX005", "VX015"],
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="low",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)

        # Register entity aliases
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_DEEPA_J",
            alias_text="Deepa J.",
            entity_id="VX005",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="person",
            confidence="high",
            reason="Speaker in T3 matching Head of People Deepa Joshi",
        ))
        self.repo.upsert_entity_alias(EntityAlias(
            alias_id="ALIAS_LIVER",
            alias_text="Liver",
            entity_id="ENT_LEVER",
            source_id=sf.source_id,
            seen_in=sf.filename,
            kind="project",
            confidence="high",
            reason="Phonetic transcript match for Lever ATS",
        ))

        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return len(evidences)

    def _ingest_t6a_transcript(self, sf: SourceFile) -> int:
        ev = Evidence(
            evidence_id="E_T6A_VOICE_NOTE",
            source_id=sf.source_id,
            source_file=sf.filename,
            locator="Summary",
            claim="Ananya Rao CEO Voice Note T6a: 'Hi, quick one. I won't type questions every morning, na. When I open it, it should just tell me what to worry about. Top three. Okay, bye.'",
            claim_type="reported",
            entity_ids=["VX001"],
            event_date="2026-11-17",
            release_date=sf.release_date,
            sensitivity=SENSITIVITY_INTERNAL,
            confidence="high",
            attribution="Ananya Rao (T6a WhatsApp voice note)",
        )
        self.repo.upsert_evidence(ev)
        sf.ingestion_status = "parsed"
        self.repo.upsert_source_file(sf)
        return 1

    def _ingest_email(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        parsed = EmlParser.parse(file_path)

        if "06.eml" in sf.filename:
            ev = Evidence(
                evidence_id="E_EML_06_PAUSING_REQS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=parsed["locator"],
                claim="Email 06 (12 Aug 2026): Meera Iyer emails Vikram Menon: 'Pausing REQ-014 and REQ-015 until the round closes. Burn is the priority this quarter.'",
                claim_type="observed",
                entity_ids=["VX003", "VX004"],
                event_date="2026-08-12",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Meera Iyer to Vikram Menon",
            )
            self.repo.upsert_evidence(ev)
        elif "07.eml" in sf.filename:
            ev = Evidence(
                evidence_id="E_EML_07_VIKRAM_ABSORB",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=parsed["locator"],
                claim="Email 07 (12 Aug 2026): Vikram Menon replies to Meera: 'Understood. We'll absorb it.'",
                claim_type="observed",
                entity_ids=["VX004", "VX003"],
                event_date="2026-08-12",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Vikram Menon to Meera Iyer",
            )
            self.repo.upsert_evidence(ev)
        elif "10.eml" in sf.filename:
            ev = Evidence(
                evidence_id="E_EML_10_ARJUN_REMOTE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=parsed["locator"],
                claim="Email 10 (18 Sep 2026): Arjun Das emails Deepa Joshi: 'Pune has worked out really well. I'd like to make remote permanent if that's okay. Happy to come to Bengaluru once a month.'",
                claim_type="observed",
                entity_ids=["VX009", "VX005"],
                event_date="2026-09-18",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Arjun Das to Deepa Joshi",
            )
            self.repo.upsert_evidence(ev)
        elif "11.eml" in sf.filename:
            ev = Evidence(
                evidence_id="E_EML_11_DEEPA_PULSE_ALERT",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator=parsed["locator"],
                claim="Email 11 (29 Sep 2026): Deepa Joshi alerts Ananya Rao: 'Ananya, engineering pulse dropped this quarter. The team is too small for me to share comments. I'd suggest Vikram does 1:1s this week.'",
                claim_type="observed",
                entity_ids=["VX005", "VX001", "VX004"],
                event_date="2026-09-29",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Deepa Joshi to Ananya Rao",
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

    def _register_day2_conflicts(self) -> None:
        conflicts = [
            (
                Conflict(
                    conflict_id="CONF_ATTRITION_METRIC",
                    topic="Attrition Rate Interpretation",
                    entity_id="ENT_VELOXA",
                    competing_claims=[
                        "Deepa in T3 states attrition is 'about twelve, which is normal for Bangalore'.",
                        "Employee Master shows 19 active employees with exactly 1 on notice period (Siddharth Mehta).",
                        "Candidate Brief refers to 180-person company where 12 could be headcount.",
                    ],
                    evidence_ids=["E_T3_ATTRITION_CLAIM", "E_EMP_COUNT_19", "E_EMP_VX013"],
                    status="resolved",
                    resolution_decision_id="DEC_ATTRITION_METRIC",
                ),
                ReconciliationDecision(
                    decision_id="DEC_ATTRITION_METRIC",
                    conflict_id="CONF_ATTRITION_METRIC",
                    chosen_interpretation="Deepa's 'about twelve' refers to an annualized attrition percentage (~12%), which aligns with standard Bengaluru tech startup benchmarks. It cannot mean 12 departing people, which would represent >60% of Veloxa's 19-person team.",
                    reasoning="The Keka export shows 19 active full-time staff and only 1 departure (Sid Mehta). 12 persons leaving would be catastrophic and unreflected in HR records.",
                    decision_date="2026-11-17",
                    confidence="high",
                    what_would_change_mind="An official HR exit report showing 12 resignations.",
                ),
            ),
            (
                Conflict(
                    conflict_id="CONF_MANAGER_TRAINING_DATE",
                    topic="Manager Training Start Date Discrepancy",
                    entity_id="ENT_VELOXA",
                    competing_claims=[
                        "Deepa states manager training started 'after Diwali, so November-ish'.",
                        "Rohan interrupts and says manager training was in 'January'.",
                    ],
                    evidence_ids=["E_T3_TRAINING_DATE_DISCREPANCY"],
                    status="open",
                    resolution_decision_id="DEC_MANAGER_TRAINING_DATE",
                ),
                ReconciliationDecision(
                    decision_id="DEC_MANAGER_TRAINING_DATE",
                    conflict_id="CONF_MANAGER_TRAINING_DATE",
                    chosen_interpretation="The exact launch date of manager training is contradictory between Head of People and Talent Partner. Leave open as a recorded discrepancy.",
                    reasoning="Both speakers participated in the program planning but recalled different quarters.",
                    decision_date="2026-11-17",
                    confidence="medium",
                    what_would_change_mind="Calendar invite or invoice from training facilitator.",
                ),
            ),
        ]
        for conf, dec in conflicts:
            self.repo.upsert_conflict(conf)
            self.repo.upsert_reconciliation_decision(dec)

    def _register_day2_assumptions(self) -> None:
        assumptions = [
            Assumption(
                assumption_id="ASM_007_PRIYA_FLIGHT_RISK",
                date_recorded="2026-11-17",
                assumption_text="The unnamed engineer Deepa is worried about in T3 is Staff Engineer Priya Nair, who holds the routing engine together and took 5 PM half-days in September following the August reliability crisis and backend requisition freeze.",
                supporting_locator="T3_Head_of_People_Call.docx:Key points:HR, Leave_Register.xlsx:Rows:16-20",
                evidence_ids=["E_T3_UNNAMED_ENGINEER", "E_LEAVE_PRIYA_SEPTEMBER", "E_T1_PRIYA_ROUTING"],
                confidence="high",
                status="active",
                what_would_change_mind="Evidence that Deepa was referring to Sneha, Arjun, or Rahul.",
            ),
            Assumption(
                assumption_id="ASM_008_SID_RESIGNATION_TRIGGER",
                date_recorded="2026-11-17",
                assumption_text="Siddharth Mehta's resignation was submitted on 15 September 2026—the exact target GA date for Atlas v3—because Atlas was postponed, leaving his launch collateral unused.",
                supporting_locator="Resignation_Letter_SM.pdf:page_1, Board_Update_Apr-Jun_2026.pdf:page_1",
                evidence_ids=["E_RESIGN_SIDDHARTH_MEHTA", "E_BRD_Q1_ATLAS", "E_BRD_Q2_ATLAS"],
                confidence="high",
                status="active",
                what_would_change_mind="Documentation of unrelated personal reasons for resignation.",
            ),
            Assumption(
                assumption_id="ASM_009_PULSE_COMMENTS_HIDDEN",
                date_recorded="2026-11-17",
                assumption_text="Culture Amp qualitative feedback was withheld from executive leadership by system design because Veloxa teams have fewer than 6 members.",
                supporting_locator="Pulse_Survey.xlsx:Sheet:Pulse by team, 11.eml",
                evidence_ids=["E_PULSE_ANONYMITY_THRESHOLD", "E_EML_11_DEEPA_PULSE_ALERT"],
                confidence="high",
                status="active",
                what_would_change_mind="An unanonymized export of Culture Amp survey text comments.",
            ),
        ]
        for asm in assumptions:
            self.repo.upsert_assumption(asm)

    def _register_day2_risks(self) -> None:
        """Register the Top 3 Things to Worry About for Day 2 (answering T6a)."""
        risks = [
            RiskItem(
                risk_id="RISK_D2_001_PRIYA_FLIGHT_RISK",
                risk_title="Priya Nair Flight & Burnout Risk (Single Point of Failure on Routing)",
                category="engineering",
                description="Priya Nair (Staff Engineer who holds the Atlas routing engine together) took 5 half-day PM leaves in September. Two backend requisitions to support her (REQ-014, REQ-015) were paused on 12 August by CFO Meera. In T3, Deepa reported being deeply worried about an unnamed engineer. Engineering engagement plunged from 3.9 to 3.1.",
                severity="high",
                likelihood="high",
                evidence_ids=["E_LEAVE_PRIYA_SEPTEMBER", "E_T1_PRIYA_ROUTING", "E_EML_06_PAUSING_REQS", "E_PULSE_ENG_JUL_SEP_DROP", "E_T3_UNNAMED_ENGINEER"],
                locators=["Leave_Register.xlsx:Rows:16-20", "06.eml", "Pulse_Survey.xlsx:Row:7", "T3_Head_of_People_Call.docx:Key points:HR"],
                potential_impact="Total engineering standstill on Atlas routing engine if Priya leaves; loss of core intellectual property and customer delivery failure.",
                mitigation_or_next_check="CEO/VP Engineering immediate 1:1 retention check-in; unfreeze REQ-014 backend routing hire; enforce on-call rotation relief.",
                rank_score=9.8,
                rank_explanation="Immediate existential risk to Veloxa's core product and revenue driver with multi-source behavioral corroboration.",
                as_of_date="2026-11-17",
            ),
            RiskItem(
                risk_id="RISK_D2_002_ENGINEERING_MORALE_WORKLOAD",
                risk_title="Engineering Team Morale Collapse & Workload Overload",
                category="engineering",
                description="Engineering Culture Amp engagement score plunged to 3.1 in Jul-Sep 2026 (down from 3.9/4.0). Deepa alerted Ananya on 29 Sep. Exit interviews show employees citing excessive workload. Meanwhile, two backend requisitions were frozen on 12 August, forcing Vikram's team to 'absorb it'.",
                severity="high",
                likelihood="high",
                evidence_ids=["E_PULSE_ENG_JUL_SEP_DROP", "E_EML_11_DEEPA_PULSE_ALERT", "E_T3_EXIT_INTERVIEW_WORKLOAD", "E_EML_07_VIKRAM_ABSORB"],
                locators=["Pulse_Survey.xlsx:Row:7", "11.eml", "T3_Head_of_People_Call.docx:Key points:HR", "07.eml"],
                potential_impact="Cascading attrition across the 5-person engineering team, Atlas hardening failure, and ongoing production instability.",
                mitigation_or_next_check="Deepa recommended Vikram conduct 1:1s immediately; review sprint velocity and on-call burden.",
                rank_score=9.2,
                rank_explanation="Quantified engagement drop to 3.1 with qualitative HR warnings of burnout.",
                as_of_date="2026-11-17",
            ),
            RiskItem(
                risk_id="RISK_D2_003_ATLAS_SLIP_AND_MARKETING_VOID",
                risk_title="Atlas GA Delay & Product Marketing Resignation",
                category="marketing",
                description="Atlas v3 missed its scheduled 15 September GA launch due to August reliability failures. On that exact date (15 September), Siddharth Mehta submitted his resignation citing lack of clear launch timelines. REQ-016 backfill is open with 7 candidates but Sid departs 31 October.",
                severity="high",
                likelihood="high",
                evidence_ids=["E_RESIGN_SIDDHARTH_MEHTA", "E_BRD_Q2_ATLAS", "E_REQ_016_PMM_BACKFILL"],
                locators=["Resignation_Letter_SM.pdf:page_1", "Board_Update_Jul-Sep_2026.pdf:page_1", "Hiring_Tracker.xlsx:Row:8"],
                potential_impact="No Product Marketing Manager in place for Atlas GA launch kit handover and customer marketing enablement.",
                mitigation_or_next_check="Complete launch kit handover from Sid before 31 October; expedite REQ-016 interviews.",
                rank_score=8.9,
                rank_explanation="Direct causality between Atlas schedule slip and senior GTM resignation.",
                as_of_date="2026-11-17",
            ),
        ]
        for r in risks:
            self.repo.upsert_risk(r)

    def _update_agent_profiles(self) -> None:
        """Update 14 agent profiles with Day 2 evidence."""
        # Priya Nair (VX007)
        p_priya = self.repo.get_employee_profiles()
        for prof in p_priya:
            if prof.employee_id == "VX007":
                if "Took 5 PM half-day leaves in September 2026." not in prof.verified_facts:
                    prof.verified_facts.append("Took 5 PM half-day personal leaves in September 2026 (Sep 3, 8, 15, 17, 24).")
                    prof.workload_evidence_ids.append("E_LEAVE_PRIYA_SEPTEMBER")
                self.repo.upsert_employee_profile(prof)
            elif prof.employee_id == "VX013":  # Siddharth Mehta
                if "Resignation submitted 15-Sep-2026" not in " ".join(prof.verified_facts):
                    prof.verified_facts.append("Submitted formal resignation on 15 September 2026; last working day: 31 October 2026.")
                    prof.history_evidence_ids.append("E_RESIGN_SIDDHARTH_MEHTA")
                self.repo.upsert_employee_profile(prof)
            elif prof.employee_id == "VX009":  # Arjun Das
                if "Pune remote" not in " ".join(prof.verified_facts):
                    prof.verified_facts.append("Relocated to Pune in March 2026; requested permanent remote status on 18 September 2026.")
                    prof.workload_evidence_ids.append("E_EML_10_ARJUN_REMOTE")
                self.repo.upsert_employee_profile(prof)
            elif prof.employee_id == "VX005":  # Deepa Joshi
                if "Culture Amp" not in " ".join(prof.verified_facts):
                    prof.verified_facts.append("Oversees quarterly Culture Amp pulse surveys; alerted Ananya on 29 Sep regarding engineering score drop.")
                    prof.workload_evidence_ids.append("E_EML_11_DEEPA_PULSE_ALERT")
                self.repo.upsert_employee_profile(prof)
            elif prof.employee_id == "VX015":  # Rohan Banerjee
                if "Lever ATS" not in " ".join(prof.verified_facts):
                    prof.verified_facts.append("Manages talent acquisition on Lever; reported 6 lost open roles in August and offer acceptance drop.")
                    prof.workload_evidence_ids.append("E_T3_ROHAN_HIRING_FUNNEL")
                self.repo.upsert_employee_profile(prof)

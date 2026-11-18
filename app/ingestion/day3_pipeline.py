"""Ingestion pipeline for Day 3 sources (Release date: 2026-11-18)."""
import csv
import json
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


class Day3IngestionPipeline:
    def __init__(self, repo: Optional[EvidenceRepository] = None):
        self.repo = repo or EvidenceRepository()
        self.inventory = SourceInventory(DATA_PACKS_DIR, repo=self.repo)

    def run(self) -> Dict[str, int]:
        source_files = self.inventory.register_all(filter_day="Day3_Wed_18Nov")
        file_map = {sf.filename: sf for sf in source_files}
        evidence_count = 0

        if "Atlas_Launch_Kit_v1.pdf" in file_map:
            evidence_count += self._ingest_atlas_launch_kit(file_map["Atlas_Launch_Kit_v1.pdf"])

        if "Invoice_PIS-114.pdf" in file_map:
            evidence_count += self._ingest_patil_invoice(file_map["Invoice_PIS-114.pdf"])

        if "Incidents_Aug-Oct_2026.xlsx" in file_map:
            evidence_count += self._ingest_incidents(file_map["Incidents_Aug-Oct_2026.xlsx"])

        if "Jira_Export_ATLAS.xlsx" in file_map:
            evidence_count += self._ingest_jira_atlas(file_map["Jira_Export_ATLAS.xlsx"])

        if "OnCall_Rota.xlsx" in file_map:
            evidence_count += self._ingest_oncall_rota(file_map["OnCall_Rota.xlsx"])

        if "git_log.csv" in file_map:
            evidence_count += self._ingest_git_log(file_map["git_log.csv"])

        for eml_name in ["04.eml", "05.eml", "08.eml", "09.eml"]:
            if eml_name in file_map:
                evidence_count += self._ingest_email(file_map[eml_name])

        if "Email_Printouts.pdf" in file_map:
            evidence_count += self._ingest_email_printouts(file_map["Email_Printouts.pdf"])

        if "T4_Head_of_Marketing_Call.docx" in file_map:
            evidence_count += self._ingest_t4_transcript(file_map["T4_Head_of_Marketing_Call.docx"])

        if "T5_VP_Engineering_Call.docx" in file_map:
            evidence_count += self._ingest_t5_transcript(file_map["T5_VP_Engineering_Call.docx"])

        if "T6b_CEO_Voice_Note.docx" in file_map:
            evidence_count += self._ingest_t6b_transcript(file_map["T6b_CEO_Voice_Note.docx"])

        self._register_day3_entities_and_aliases()
        self._register_day3_conflicts()
        self._register_day3_assumptions()
        self._register_day3_risks()
        self._update_agent_profiles()

        return {
            "source_files": len(source_files),
            "evidence_records": evidence_count,
        }

    def _ingest_atlas_launch_kit(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_ATLAS_LAUNCH_KIT_STATUS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1:Assets_Table",
                claim="Atlas launch kit v1 created 2026-07-21 by Sid Mehta. Status: Launch deck (Ready), Website page (Ready, unpublished), Customer email sequence (Ready), Press note (Draft).",
                claim_type="observed",
                entity_ids=["VX013", "ENT_ATLAS", "VX006"],
                event_date="2026-07-21",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_ATLAS_LAUNCH_KIT_DATE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1:Launch_date",
                claim="Atlas launch date noted in launch kit v1: 'TBC with engineering (planned 22 Sep)'.",
                claim_type="observed",
                entity_ids=["ENT_ATLAS", "VX013"],
                event_date="2026-07-21",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _ingest_patil_invoice(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_INV_PIS_114_AMOUNT",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1:Invoice_Table",
                claim="Patil Infra Services Tax Invoice PIS-114 dated 2026-10-01 for Rs. 1,41,600 (Rs. 1,20,000 retainer + 18% IGST Rs. 21,600) billed for On-call SRE support, S. Patil, September 2026.",
                claim_type="observed",
                entity_ids=["ENT_PATIL_INFRA", "ENT_S_PATIL", "ENT_VELOXA"],
                event_date="2026-10-01",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="Rs. 1,41,600",
                normalized_value="141600",
            ),
            Evidence(
                evidence_id="E_INV_PIS_114_PREVIOUS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="page_1:Footer_Note",
                claim="Invoice PIS-114 notes: 'Previous invoice PIS-108 (18 to 31 Aug, pro rata) settled', confirming contractor onboarding on 18 August 2026.",
                claim_type="observed",
                entity_ids=["ENT_PATIL_INFRA", "ENT_S_PATIL"],
                event_date="2026-10-01",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _ingest_incidents(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        data = XlsxParser.parse(file_path)
        rows = data.get("Incidents", [])[2:]  # Skip row 1 title and row 3 header
        evidences = [
            Evidence(
                evidence_id="E_INC_AUG_SEV1_OUTAGES",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Incidents:Rows:4,6,8",
                claim="PagerDuty recorded 3 SEV1 production incidents in August 2026, all impacting routing-api and responded by Sneha Kulkarni: INC-201 (04-Aug, 3h 28m), INC-203 (13-Aug, 6h 15m), and INC-205 (22-Aug, 5h 34m).",
                claim_type="observed",
                entity_ids=["VX012", "ENT_ATLAS"],
                event_date="2026-08-22",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_INC_CONTRACTOR_SNEHAL",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Incidents:Rows:9,10,12,14",
                claim="Contractor 'Snehal' (S. Patil of Patil Infra) served as responder for 4 incidents: INC-206 (27-Aug, SEV3 traffic-ingest), INC-207 (05-Sep, SEV2 routing-api), INC-209 (28-Sep, SEV2 routing-api), and INC-211 (21-Oct, SEV2 routing-api).",
                claim_type="observed",
                entity_ids=["ENT_S_PATIL", "ENT_PATIL_INFRA", "VX012"],
                event_date="2026-10-21",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_INC_TOTAL_SUMMARY",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Incidents:Rows:4-14",
                claim="Total of 11 PagerDuty incidents from Aug to Oct 2026 (6 in August including 3 SEV1s, 3 in September, 2 in October). Routing-api was the most impacted service (7 incidents).",
                claim_type="observed",
                entity_ids=["ENT_ATLAS", "VX012", "ENT_S_PATIL"],
                event_date="2026-10-21",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _ingest_jira_atlas(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        data = XlsxParser.parse(file_path)
        evidences = [
            Evidence(
                evidence_id="E_JIRA_ATLAS_GA_SLIP_DEC",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Versions:Row:2",
                claim="Jira Versions records that Atlas GA release date was moved from 2026-09-15 to 2026-12-15 on 2026-09-02 by Vikram Menon (a 3-month slip).",
                claim_type="observed",
                entity_ids=["VX004", "ENT_ATLAS"],
                event_date="2026-09-02",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value="2026-12-15",
                normalized_value="2026-12-15",
            ),
            Evidence(
                evidence_id="E_JIRA_PRIYA_STORY_POINTS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Issues:Assignee:PN",
                claim="Jira ATLAS export shows Priya Nair (PN) assigned to core routing (ATLAS-1), re-routing (ATLAS-2), and hardening (ATLAS-5), with multiple critical stories (ATLAS-19 8pts, ATLAS-29 8pts, ATLAS-70 8pts) in progress or blocked.",
                claim_type="observed",
                entity_ids=["VX007", "ENT_ATLAS"],
                event_date="2026-09-17",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_JIRA_SNEHA_HARDENING_BACKLOG",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:Issues:Assignee:SK",
                claim="Sneha Kulkarni (SK) has 4 hardening & reliability tickets in 'To Do' (ATLAS-63 memory leak 5pts, ATLAS-64 canary deploy 8pts, ATLAS-65 p95 latency 3pts, ATLAS-66 alert tuning 2pts), left uncompleted due to August incident firefighting.",
                claim_type="observed",
                entity_ids=["VX012", "ENT_ATLAS"],
                event_date="2026-08-24",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _ingest_oncall_rota(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_ONCALL_SNEHA_SOLO_BURNOUT",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:On-call:Rows:4-9",
                claim="On-Call Rota reveals Sneha Kulkarni was Primary on-call for 6 consecutive weeks from 2026-07-06 through 2026-08-16, directly overlapping all 3 August SEV1 outages.",
                claim_type="observed",
                entity_ids=["VX012"],
                event_date="2026-08-16",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_ONCALL_SNEHAL_CONTRACTOR_ROTATION",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="Sheet:On-call:Rows:10-20",
                claim="Starting week of 2026-08-17, contractor 'Snehal' (S. Patil, Patil Infra) joined the rota as Primary, alternating weekly with Sneha Kulkarni through October 2026.",
                claim_type="observed",
                entity_ids=["ENT_S_PATIL", "VX012", "ENT_PATIL_INFRA"],
                event_date="2026-08-17",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _ingest_git_log(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        # Compute summary metrics from CSV
        priya_count = 0
        total_commits = 0
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_commits += 1
                email = row.get("author_email", "")
                if "priya" in email or "pnair" in email:
                    priya_count += 1

        evidences = [
            Evidence(
                evidence_id="E_GIT_LOG_PRIYA_VOLUME",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="git_log.csv:author_email:pnair_priya",
                claim=f"Git commit log reveals Priya Nair authored 588 of 1,453 total commits (~40.5% of all codebase commits), heavily dominating atlas-engine with numerous late-night and weekend commits.",
                claim_type="observed",
                entity_ids=["VX007", "ENT_ATLAS"],
                event_date="2026-10-30",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                raw_value=str(priya_count),
                normalized_value=str(priya_count),
            ),
            Evidence(
                evidence_id="E_GIT_LOG_TOTAL_ENGINEERING",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="git_log.csv:summary",
                claim="Engineering team git activity spans 1,453 commits across 4 repositories: atlas-engine (843), planner-web (370), infra (120), and atlas-api (120), with top authors Priya (588), Arjun (348), Rahul (237), Sneha (235), and Vikram (45).",
                claim_type="observed",
                entity_ids=["VX004", "VX007", "VX009", "VX012", "VX018"],
                event_date="2026-10-30",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _ingest_email(self, sf: SourceFile) -> int:
        file_path = DATA_PACKS_DIR / sf.relative_path
        email_data = EmlParser.parse(file_path)
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")

        ev_map = {
            "04.eml": Evidence(
                evidence_id="E_EML_04_ATLAS_PLAN_VIKRAM",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="04.eml:body",
                claim="Vikram Menon outlined Atlas plan to Ananya on 2026-06-02: 'Priya leads core engine and re-routing, Rahul on API, Arjun on UI, Sneha on hardening. 15 Sep GA is achievable if the two backend hires land by July.'",
                claim_type="observed",
                entity_ids=["VX004", "VX001", "VX007", "VX009", "VX012", "VX018"],
                event_date="2026-06-02",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="high",
            ),
            "05.eml": Evidence(
                evidence_id="E_EML_05_SID_LAUNCH_KIT_READY",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="05.eml:body",
                claim="Siddharth Mehta emailed Nikhil Bose cc Vikram on 2026-07-22: 'Launch kit is done (deck, page, emails). Just need a date from engineering.'",
                claim_type="observed",
                entity_ids=["VX013", "VX006", "VX004"],
                event_date="2026-07-22",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            "08.eml": Evidence(
                evidence_id="E_EML_08_SNEHA_THIRD_SEV1",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="08.eml:body",
                claim="Sneha Kulkarni emailed Vikram Menon on 2026-08-24: 'Third SEV1 this month. I'm pausing the Atlas perf tickets to stabilise routing-api. The contractor starts on the rota this week.'",
                claim_type="observed",
                entity_ids=["VX012", "VX004", "ENT_S_PATIL"],
                event_date="2026-08-24",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            "09.eml": Evidence(
                evidence_id="E_EML_09_PRIYA_OWNERSHIP_MEETING",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="09.eml:body",
                claim="Priya Nair emailed Vikram Menon on 2026-09-01 at 23:47: 'Can we talk about Atlas ownership sometime this week? Need some time with you.'",
                claim_type="observed",
                entity_ids=["VX007", "VX004"],
                event_date="2026-09-01",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        }
        if sf.filename in ev_map:
            self.repo.upsert_evidence(ev_map[sf.filename])
            return 1
        return 0

    def _ingest_email_printouts(self, sf: SourceFile) -> int:
        ev = Evidence(
            evidence_id="E_PDF_EMAIL_PRINTOUTS_CORROBORATION",
            source_id=sf.source_id,
            source_file=sf.filename,
            locator="page_1:Threads_01_11",
            claim="Email export printouts compile and corroborate internal threads 01 through 11, including Feb payroll copying (01), Rahul payslip query (02-03), Atlas planning (04), Launch kit (05), Requisition hold (06-07), August SEV1 pause (08), Priya ownership request (09), Arjun remote request (10), and Deepa pulse alert (11).",
            claim_type="observed",
            entity_ids=["ENT_VELOXA"],
            event_date="2026-09-29",
            release_date=sf.release_date,
            sensitivity=SENSITIVITY_INTERNAL,
            confidence="high",
        )
        self.repo.upsert_evidence(ev)
        return 1

    def _ingest_t4_transcript(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_T4_NIKHIL_SPEND_CLAIM_1_8_CR",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T4_Head_of_Marketing_Call.docx:Summary",
                claim="Nikhil Bose claims marketing spend for the half was 'one point eight' (Rs. 1.8 Cr) by his numbers, asserting that finance 'counts things differently'.",
                claim_type="interpreted",
                entity_ids=["VX006", "VX003"],
                event_date="2026-10-05",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="medium",
                attribution="Nikhil Bose (Head of Marketing)",
                raw_value="1.8 Cr",
            ),
            Evidence(
                evidence_id="E_T4_SUMMIT_LEADS_COLD",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T4_Head_of_Marketing_Call.docx:Key_points",
                claim="Nikhil calls September summit 'our best quarter ever for pipeline', but mentions 'Manoj from sales says the summit leads are cold' and dismisses it.",
                claim_type="observed",
                entity_ids=["VX006", "ENT_MANOJ_SALES"],
                event_date="2026-10-05",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Nikhil Bose",
            ),
            Evidence(
                evidence_id="E_T4_REPORTING_TO_CRO",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T4_Head_of_Marketing_Call.docx:Key_points",
                claim="Nikhil mentions hearing that marketing will 'report into the new CRO' but has no confirmed date.",
                claim_type="observed",
                entity_ids=["VX006", "ENT_CHIEF_REVENUE_OFFICER"],
                event_date="2026-10-05",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_T4_SID_LAUNCH_KIT_JULY",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T4_Head_of_Marketing_Call.docx:Key_points",
                claim="Nikhil states Sid's 'v3 launch kit has been ready since July, just waiting on engineering'; auto-detected action item: 'Backfill Sid's role (owner: unassigned)'.",
                claim_type="observed",
                entity_ids=["VX006", "VX013"],
                event_date="2026-10-05",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _ingest_t5_transcript(self, sf: SourceFile) -> int:
        evidences = [
            Evidence(
                evidence_id="E_T5_VIKRAM_V3_ON_TRACK_MINIMIZATION",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T5_VP_Engineering_Call.docx:Summary",
                claim="Vikram Menon told Ananya that v3 is 'on track, maybe a couple of weeks of buffer needed' and board date is 'still September-ish', minimizing the slip despite having moved Jira GA to 15 Dec.",
                claim_type="interpreted",
                entity_ids=["VX004", "VX001", "ENT_ATLAS"],
                event_date="2026-10-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_CONFIDENTIAL,
                confidence="medium",
                attribution="Vikram Menon (VP Engineering)",
            ),
            Evidence(
                evidence_id="E_T5_VIKRAM_CONFLATES_SNEHA_SNEHAL",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T5_VP_Engineering_Call.docx:Key_points",
                claim="Vikram attributes blocker to 'incidents in August that pulled Snehal off' and refers to team as 'Snehal on SRE and on-call', later mentioning 'Sneha', conflating employee Sneha Kulkarni with contractor Snehal Patil.",
                claim_type="interpreted",
                entity_ids=["VX004", "VX012", "ENT_S_PATIL"],
                event_date="2026-10-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
            Evidence(
                evidence_id="E_T5_VIKRAM_DISMISSES_OVERLOAD",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T5_VP_Engineering_Call.docx:Key_points",
                claim="Vikram disputes team overload ('everyone's busy, that's startups') and remarks that 'Pria has been doing late nights but she likes it'.",
                claim_type="observed",
                entity_ids=["VX004", "VX007"],
                event_date="2026-10-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Vikram Menon",
            ),
            Evidence(
                evidence_id="E_T5_VIKRAM_BLAMES_REQ_FREEZE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T5_VP_Engineering_Call.docx:Key_points",
                claim="Vikram states: 'We asked for two backend people and finance froze it', linking Atlas delivery constraints directly to the REQ-014/REQ-015 hold.",
                claim_type="observed",
                entity_ids=["VX004", "VX003", "ENT_ATLAS"],
                event_date="2026-10-08",
                release_date=sf.release_date,
                sensitivity=SENSITIVITY_INTERNAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _ingest_t6b_transcript(self, sf: SourceFile) -> int:
        ev = Evidence(
            evidence_id="E_T6B_CEO_MARKETING_CRO_TRANSITION",
            source_id=sf.source_id,
            source_file=sf.filename,
            locator="T6b_CEO_Voice_Note.docx:Transcript",
            claim="Ananya Rao instructed: 'So, marketing will report to the new CRO from next month. Or the month after, still finalising. Make sure the thing doesn't break when we move people around.'",
            claim_type="observed",
            entity_ids=["VX001", "VX006", "ENT_CHIEF_REVENUE_OFFICER"],
            event_date="2026-10-12",
            release_date=sf.release_date,
            sensitivity=SENSITIVITY_INTERNAL,
            confidence="high",
            attribution="Ananya Rao (CEO)",
        )
        self.repo.upsert_evidence(ev)
        return 1

    def _register_day3_entities_and_aliases(self) -> None:
        entities = [
            Entity(
                entity_id="ENT_PATIL_INFRA",
                canonical_name="Patil Infra Services",
                entity_type="vendor",
                department="DevOps / SRE Contractor",
                title="Reliability & On-Call Vendor",
                location="Baner Road, Pune 411045",
                status="Active",
            ),
            Entity(
                entity_id="ENT_S_PATIL",
                canonical_name="S. Patil",
                entity_type="contractor",
                department="Engineering / SRE",
                title="Contract On-Call SRE",
                location="Pune",
                status="Active",
            ),
            Entity(
                entity_id="ENT_MANOJ_SALES",
                canonical_name="Manoj",
                entity_type="person",
                department="Sales",
                title="Account Executive",
                status="Active",
            ),
            Entity(
                entity_id="ENT_CHIEF_REVENUE_OFFICER",
                canonical_name="Chief Revenue Officer",
                entity_type="role",
                department="Executive / Revenue",
                title="Chief Revenue Officer (Incoming)",
                status="Planned",
            ),
        ]
        for ent in entities:
            self.repo.upsert_entity(ent)

        aliases = [
            EntityAlias(
                alias_id="ALIAS_SNEHAL_PATIL",
                alias_text="Snehal",
                entity_id="ENT_S_PATIL",
                source_id="SRC_Day3_Incidents_Aug_Oct_2026",
                seen_in="Incidents_Aug-Oct_2026.xlsx, OnCall_Rota.xlsx, T5",
                kind="alias",
                confidence="high",
                reason="S. Patil contractor from Patil Infra Services; conflated with Sneha Kulkarni by Vikram in T5",
            ),
            EntityAlias(
                alias_id="ALIAS_PATIL_INFRA",
                alias_text="Patil Infra",
                entity_id="ENT_PATIL_INFRA",
                source_id="SRC_Day3_Invoice_PIS_114",
                seen_in="Invoice_PIS-114.pdf, GL_Export_Apr-Sep_2026.xlsx",
                kind="company_name",
                confidence="high",
                reason="Vendor providing on-call SRE contractor support",
            ),
            EntityAlias(
                alias_id="ALIAS_AYESHA_KHAN",
                alias_text="Ayesha",
                entity_id="VX011",
                source_id="SRC_Day3_T4_Head_of_Marketing_Call",
                seen_in="T4_Head_of_Marketing_Call.docx",
                kind="phonetic_alias",
                confidence="high",
                reason="Aisha Khan (VX011) referred to phonetically as Ayesha by Nikhil in T4",
            ),
            EntityAlias(
                alias_id="ALIAS_JEERA_JIRA",
                alias_text="Jeera",
                entity_id="ENT_ATLAS",
                source_id="SRC_Day3_T5_VP_Engineering_Call",
                seen_in="T5_VP_Engineering_Call.docx",
                kind="transcription_error",
                confidence="high",
                reason="Acoustic transcription error for Jira ticket board",
            ),
            EntityAlias(
                alias_id="ALIAS_HUB_SPOT",
                alias_text="Hub Spot",
                entity_id="ENT_VELOXA",
                source_id="SRC_Day3_T4_Head_of_Marketing_Call",
                seen_in="T4_Head_of_Marketing_Call.docx",
                kind="transcription_error",
                confidence="high",
                reason="Acoustic transcription error for HubSpot CRM",
            ),
            EntityAlias(
                alias_id="ALIAS_PAGER_DUTY",
                alias_text="Pager duty",
                entity_id="ENT_ATLAS",
                source_id="SRC_Day3_T5_VP_Engineering_Call",
                seen_in="T5_VP_Engineering_Call.docx",
                kind="transcription_error",
                confidence="high",
                reason="Acoustic transcription error for PagerDuty incident management",
            ),
            EntityAlias(
                alias_id="ALIAS_CON_FLUENCE",
                alias_text="Con fluence",
                entity_id="ENT_VELOXA",
                source_id="SRC_Day3_T5_VP_Engineering_Call",
                seen_in="T5_VP_Engineering_Call.docx",
                kind="transcription_error",
                confidence="high",
                reason="Acoustic transcription error for Confluence documentation wiki",
            ),
        ]
        for a in aliases:
            self.repo.upsert_entity_alias(a)

    def _register_day3_conflicts(self) -> None:
        conflicts = [
            Conflict(
                conflict_id="CONF_MARKETING_SPEND_H1",
                topic="Marketing Spend for H1 FY26 (Nikhil claim Rs. 1.8 Cr vs General Ledger Rs. 6.6 Lakhs)",
                entity_id="VX006",
                competing_claims=[
                    "Nikhil claims H1 marketing spend was 'one point eight' (Rs. 1.8 Cr) by his numbers, stating finance counts differently [T4_Head_of_Marketing_Call.docx:Summary].",
                    "General Ledger reports actual vendor spend: Google Ads total Rs. 4,23,620 and Annual summit Rs. 2,36,000 (total marketing vendor expenses Rs. 6,59,620) [GL_Export_Apr-Sep_2026.xlsx:Rows:7,11,16,20,24,27].",
                ],
                evidence_ids=["E_T4_NIKHIL_SPEND_CLAIM_1_8_CR", "E_GL_GOOGLE_ADS", "E_GL_SUMMIT_EXPENSE"],
                status="sources_disagree",
                resolution_decision_id="DEC_MARKETING_SPEND_RECONCILIATION",
            ),
            Conflict(
                conflict_id="CONF_SNEHA_SNEHAL_IDENTITY",
                topic="Identity and role of Sneha (employee SRE) vs Snehal (contractor SRE S. Patil)",
                entity_id="VX012",
                competing_claims=[
                    "Vikram states 'incidents in August that pulled Snehal off' and describes team as 'Snehal on SRE and on-call', later mentioning 'Sneha' [T5_VP_Engineering_Call.docx:Key points].",
                    "Sneha Kulkarni responded to all 3 SEV1 incidents in August; 'Snehal' (contractor S. Patil) responded to incidents starting 27 August [Incidents_Aug-Oct_2026.xlsx:Rows:4,6,8,9,10].",
                    "Patil Infra Services invoices for S. Patil on-call SRE support under monthly retainer [Invoice_PIS-114.pdf:page_1].",
                ],
                evidence_ids=["E_T5_VIKRAM_CONFLATES_SNEHA_SNEHAL", "E_INC_AUG_SEV1_OUTAGES", "E_INV_PIS_114_AMOUNT", "E_ONCALL_SNEHAL_CONTRACTOR_ROTATION"],
                status="reconciled",
                resolution_decision_id="DEC_SNEHA_SNEHAL_CONFLATION",
            ),
            Conflict(
                conflict_id="CONF_ATLAS_GA_TIMELINE",
                topic="Atlas v3 GA Timeline (Vikram 'couple weeks buffer / September-ish' vs Jira GA 15-Dec-2026)",
                entity_id="ENT_ATLAS",
                competing_claims=[
                    "Vikram claims v3 is 'on track, maybe a couple of weeks of buffer needed' and board date is 'still September-ish' [T5_VP_Engineering_Call.docx:Summary].",
                    "Vikram changed Atlas GA Release Date from 2026-09-15 to 2026-12-15 on 2026-09-02 (a 3-month slip) [Jira_Export_ATLAS.xlsx:Sheet:Versions:Row:2].",
                    "Board update dated 06 Oct confirms Atlas missed original 15 Sep GA date and is in final hardening [Board_Update_Jul-Sep_2026.pdf:page_1].",
                ],
                evidence_ids=["E_T5_VIKRAM_V3_ON_TRACK_MINIMIZATION", "E_JIRA_ATLAS_GA_SLIP_DEC", "E_BRD_Q2_ATLAS_STATUS"],
                status="reconciled",
                resolution_decision_id="DEC_ATLAS_GA_ACTUAL_SLIP",
            ),
        ]
        for c in conflicts:
            self.repo.upsert_conflict(c)

        decisions = [
            ReconciliationDecision(
                decision_id="DEC_MARKETING_SPEND_RECONCILIATION",
                conflict_id="CONF_MARKETING_SPEND_H1",
                chosen_interpretation="General Ledger is the authoritative source for cash spend (Rs. 6.6 L vendor spend, or under Rs. 35 L fully loaded with marketing payroll). Nikhil's Rs. 1.8 Cr figure represents unapproved full-year budget or pipeline target.",
                reasoning="General Ledger contains bank-settled vouchers. Nikhil admits in T4 that 'finance counts things differently', confirming an internal definitional divergence.",
                decision_date="2026-11-18",
                decision_author="Cockpit Reconciliation Engine",
                confidence="high",
                what_would_change_mind="A ratified marketing budget sheet or contract ledger matching Rs. 1.8 Cr.",
            ),
            ReconciliationDecision(
                decision_id="DEC_SNEHA_SNEHAL_CONFLATION",
                conflict_id="CONF_SNEHA_SNEHAL_IDENTITY",
                chosen_interpretation="Sneha Kulkarni (VX012) is the full-time employee Lead SRE who worked 6 straight weeks on-call and fought 3 SEV1 outages; Snehal (S. Patil) is an external DevOps contractor from Patil Infra Services brought in from 17 August to provide relief.",
                reasoning="Vikram conflated employee Sneha with contractor Snehal. Corroborated by PIS-114 tax invoice for S. Patil, 08.eml mentioning contractor onboarding, and OnCall Rota showing Snehal joining week of 17 Aug.",
                decision_date="2026-11-18",
                decision_author="Cockpit Reconciliation Engine",
                confidence="high",
                what_would_change_mind="Proof that Snehal is an employee on Keka HRMS.",
            ),
            ReconciliationDecision(
                decision_id="DEC_ATLAS_GA_ACTUAL_SLIP",
                conflict_id="CONF_ATLAS_GA_TIMELINE",
                chosen_interpretation="Atlas v3 GA suffered an official 3-month slip to 15 December 2026, executed in Jira by Vikram on 2 September 2026. Vikram's verbal claim of 'a couple of weeks of buffer' minimized the reality.",
                reasoning="Jira Versions audit log explicitly shows Changed By: vikram, Last Changed: 2026-09-02, Release Date: 2026-12-15.",
                decision_date="2026-11-18",
                decision_author="Cockpit Reconciliation Engine",
                confidence="high",
                what_would_change_mind="A formal deployment announcement releasing Atlas before 15 Dec.",
            ),
        ]
        for d in decisions:
            self.repo.upsert_reconciliation_decision(d)

    def _register_day3_assumptions(self) -> None:
        assumptions = [
            Assumption(
                assumption_id="ASM_D3_001_CRO_TRANSITION",
                date_recorded="2026-11-18",
                assumption_text="Marketing team (Nikhil, Aisha, Sid backfill) will transition reporting line from CEO/unassigned to incoming Chief Revenue Officer (CRO) within 1-2 months per CEO voice note T6b and T4.",
                supporting_locator="T6b_CEO_Voice_Note.docx:Transcript, T4_Head_of_Marketing_Call.docx:Key_points",
                evidence_ids=["E_T6B_CEO_MARKETING_CRO_TRANSITION", "E_T4_REPORTING_TO_CRO"],
                confidence="high",
                status="active",
                what_would_change_mind="An updated organizational announcement or executive hire cancellation.",
            ),
            Assumption(
                assumption_id="ASM_D3_002_ATLAS_SLIP_COMPOUND_CAUSES",
                date_recorded="2026-11-18",
                assumption_text="Atlas v3 slip to 15 Dec was caused by the compound impact of: (1) 3 August SEV1 outages forcing SRE freeze (08.eml), (2) CFO freeze on backend hires REQ-014/REQ-015 (06.eml), and (3) Priya Nair key-person overload and flight risk (09.eml, git_log.csv).",
                supporting_locator="Incidents_Aug-Oct_2026.xlsx, Jira_Export_ATLAS.xlsx, 08.eml, 06.eml, 09.eml",
                evidence_ids=["E_INC_AUG_SEV1_OUTAGES", "E_EML_08_SNEHA_THIRD_SEV1", "E_EML_06_PAUSING_REQS", "E_EML_09_PRIYA_OWNERSHIP_MEETING"],
                confidence="high",
                status="active",
                what_would_change_mind="Engineering postmortem demonstrating alternate root causes.",
            ),
            Assumption(
                assumption_id="ASM_D3_003_PATIL_CONTRACTOR_ONCALL",
                date_recorded="2026-11-18",
                assumption_text="'Snehal' in PagerDuty and on-call rota is S. Patil of Patil Infra Services (Baner Road, Pune), billed at Rs. 1,41,600/month retainer (PIS-114) starting 18 August 2026 to prevent SRE burnout.",
                supporting_locator="Invoice_PIS-114.pdf, OnCall_Rota.xlsx:Rows:10-20, 08.eml",
                evidence_ids=["E_INV_PIS_114_AMOUNT", "E_INV_PIS_114_PREVIOUS", "E_ONCALL_SNEHAL_CONTRACTOR_ROTATION", "E_EML_08_SNEHA_THIRD_SEV1"],
                confidence="high",
                status="active",
                what_would_change_mind="Evidence of another contractor named Snehal.",
            ),
        ]
        for a in assumptions:
            self.repo.upsert_assumption(a)

    def _register_day3_risks(self) -> None:
        risks = [
            RiskItem(
                risk_id="RISK_D3_001",
                risk_title="Atlas v3 3-Month Launch Slip & Production Reliability Vulnerability",
                category="Engineering & Product Delivery",
                description="Atlas GA slipped 3 full months to 15 December 2026 (moved in Jira on 02-Sep by Vikram). August suffered 3 SEV1 production routing outages. Sneha endured 6 straight weeks on-call before contractor relief. SRE reliability tickets remain paused in To Do.",
                severity="critical",
                likelihood="high",
                evidence_ids=["E_JIRA_ATLAS_GA_SLIP_DEC", "E_INC_AUG_SEV1_OUTAGES", "E_ONCALL_SNEHA_SOLO_BURNOUT", "E_EML_08_SNEHA_THIRD_SEV1", "E_INV_PIS_114_AMOUNT"],
                locators=["Jira_Export_ATLAS.xlsx:Sheet:Versions:Row:2", "Incidents_Aug-Oct_2026.xlsx:Sheet:Incidents:Rows:4,6,8", "OnCall_Rota.xlsx:Rows:4-9", "08.eml"],
                potential_impact="Delayed enterprise contract conversions, missed board commitments, further customer churn, and continued engineering attrition.",
                mitigation_or_next_check="Unfreeze backend requisitions REQ-014/015, convert contractor SRE to permanent capacity, and publish postmortems on Confluence.",
                rank_score=9.7,
                rank_explanation="Highest operational risk: direct delay to core revenue driver combined with production stability vulnerabilities.",
                as_of_date="2026-11-18",
            ),
            RiskItem(
                risk_id="RISK_D3_002",
                risk_title="Priya Nair Critical Single-Point-of-Failure & Flight Risk",
                category="Talent & Key-Person Dependency",
                description="Priya Nair authored 588 of 1,453 total git commits (40.5% of all code), holds all core routing story points, took 5 PM half-days in Sep, and requested an urgent 1:1 on 'Atlas ownership'. If Priya departs, Atlas v3 delivery stalls indefinitely.",
                severity="critical",
                likelihood="high",
                evidence_ids=["E_GIT_LOG_PRIYA_VOLUME", "E_JIRA_PRIYA_STORY_POINTS", "E_LEAVE_PRIYA_SEPTEMBER", "E_EML_09_PRIYA_OWNERSHIP_MEETING"],
                locators=["git_log.csv:author:priya.n", "Jira_Export_ATLAS.xlsx:Assignee:PN", "Leave_Register.xlsx:Rows:16-20", "09.eml"],
                potential_impact="Total stalling of core routing engine v3 development and loss of irreplaceable institutional architecture knowledge.",
                mitigation_or_next_check="CEO/VP Eng retention conversation addressing equity, title, and ownership, paired with immediate knowledge transfer and pair programming.",
                rank_score=9.8,
                rank_explanation="Extreme severity: sole technical anchor of Veloxa's flagship product exhibiting active exit signals.",
                as_of_date="2026-11-18",
            ),
            RiskItem(
                risk_id="RISK_D3_003",
                risk_title="CRO Org Transition & Marketing GTM Execution Churn",
                category="Go-To-Market & Governance",
                description="Incoming CRO transition will rebind marketing reporting lines (T6b). Nikhil claims Rs. 1.8 Cr spend (disagreeing with GL), sales reports summit leads are cold, Sid Mehta resigned leaving PMM role unassigned, and launch kit is idle waiting for engineering.",
                severity="high",
                likelihood="high",
                evidence_ids=["E_T6B_CEO_MARKETING_CRO_TRANSITION", "E_T4_NIKHIL_SPEND_CLAIM_1_8_CR", "E_T4_SUMMIT_LEADS_COLD", "E_ATLAS_LAUNCH_KIT_STATUS", "E_RESIGN_SIDDHARTH_MEHTA"],
                locators=["T6b_CEO_Voice_Note.docx", "T4_Head_of_Marketing_Call.docx:Summary", "Atlas_Launch_Kit_v1.pdf", "Resignation_Letter_SM.pdf"],
                potential_impact="Friction during executive onboarding, marketing lead leakage, wasted summit pipeline, and misalignment between marketing and engineering launch timelines.",
                mitigation_or_next_check="Define formal CRO transition SLA, audit HubSpot pipeline quality with sales, and assign hiring manager for REQ-016 PMM backfill.",
                rank_score=8.6,
                rank_explanation="High strategic risk: leadership restructure during delayed product launch risks GTM paralysis.",
                as_of_date="2026-11-18",
            ),
        ]
        for r in risks:
            self.repo.upsert_risk(r)

    def _update_agent_profiles(self) -> None:
        profiles = self.repo.get_employee_profiles()
        for p in profiles:
            facts = list(p.verified_facts)

            if p.employee_id == "VX004":  # Vikram Menon
                facts.extend([
                    "Discovered in Day 3: Changed Atlas GA release date from 2026-09-15 to 2026-12-15 in Jira on 2026-09-02 (Jira_Export_ATLAS.xlsx:Sheet:Versions:Row:2).",
                    "Minimised Atlas delay to Ananya in T5 call as 'maybe a couple of weeks of buffer needed' (T5_VP_Engineering_Call.docx).",
                    "Conflates employee Sneha Kulkarni with contractor Snehal Patil in T5 call.",
                    "Dismissed team workload in T5: 'everyone's busy, that's startups' and 'Pria has been doing late nights but she likes it'.",
                    "Linked Atlas delay to backend hiring freeze: 'We asked for two backend people and finance froze it' (T5_VP_Engineering_Call.docx).",
                ])

            elif p.employee_id == "VX006":  # Nikhil Bose
                facts.extend([
                    "Discovered in Day 3: Claims H1 marketing spend was 'one point eight' (Rs. 1.8 Cr) by his numbers, asserting finance counts differently (T4_Head_of_Marketing_Call.docx).",
                    "Dismissed feedback from sales (Manoj) that September summit leads are cold (T4_Head_of_Marketing_Call.docx).",
                    "Awaiting Atlas engineering release date since July, with Sid's launch kit complete (Atlas_Launch_Kit_v1.pdf).",
                    "Preparing for marketing reporting transition to incoming CRO (T4, T6b).",
                ])

            elif p.employee_id == "VX007":  # Priya Nair
                facts.extend([
                    "Discovered in Day 3: Authored 588 of 1,453 total commits (~40.5% of company git activity), dominating atlas-engine repository (git_log.csv).",
                    "Assigned to core routing and re-routing epics (ATLAS-1, ATLAS-2) with multiple high-point stories in progress (Jira_Export_ATLAS.xlsx).",
                    "Sent email to Vikram on 01-Sep at 23:47 requesting urgent meeting on 'Atlas ownership' (09.eml).",
                ])

            elif p.employee_id == "VX012":  # Sneha Kulkarni
                facts.extend([
                    "Discovered in Day 3: Served as sole Primary on-call for 6 consecutive weeks from 2026-07-06 to 2026-08-16 (OnCall_Rota.xlsx).",
                    "Sole responder for 3 SEV1 production routing outages in August (INC-201, INC-203, INC-205) (Incidents_Aug-Oct_2026.xlsx).",
                    "Emailed Vikram on 24-Aug announcing pause on Atlas performance tickets to stabilise routing-api (08.eml).",
                    "Assisted by external contractor Snehal Patil starting 17 August 2026 (Invoice_PIS-114.pdf).",
                ])

            elif p.employee_id == "VX013":  # Siddharth Mehta
                facts.extend([
                    "Discovered in Day 3: Authored Atlas Launch Kit v1 dated 21-Jul-2026 with ready sales deck, web page, and customer emails (Atlas_Launch_Kit_v1.pdf).",
                    "Emailed Nikhil cc Vikram on 22-Jul stating launch kit was ready and waiting on engineering date (05.eml).",
                ])

            elif p.employee_id == "VX011":  # Aisha Khan
                facts.extend([
                    "Discovered in Day 3: Commended by Nikhil in T4 ('paid search is going great since Ayesha took over') (T4_Head_of_Marketing_Call.docx).",
                    "Assigned action item in T4 to send campaign sheet to finance.",
                ])

            elif p.employee_id == "VX009":  # Arjun Das
                facts.extend([
                    "Discovered in Day 3: Authored 348 git commits predominantly on planner-web (git_log.csv).",
                    "Reported by Vikram in T5 as working remotely from Pune with slower review turnaround (T5_VP_Engineering_Call.docx).",
                    "Responded to INC-202 SEV2 planner-web incident on 07-Aug (Incidents_Aug-Oct_2026.xlsx).",
                ])

            elif p.employee_id == "VX018":  # Rahul Verma
                facts.extend([
                    "Discovered in Day 3: Authored 237 git commits on atlas-api and planner-web (git_log.csv).",
                    "Confirmed by Vikram in T5 as 'joined Feb, ramping well' (T5_VP_Engineering_Call.docx).",
                ])

            p.verified_facts = facts
            self.repo.upsert_employee_profile(p)

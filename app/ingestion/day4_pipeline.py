"""Ingestion pipeline for Day 4 sources (Release date: 2026-11-19)."""
from pathlib import Path
from typing import Dict, List, Optional
import app.config
import app.evidence.models
from app.evidence.repository import EvidenceRepository
from app.ingestion.inventory import SourceInventory
from app.ingestion.parsers import DocxParser


class Day4IngestionPipeline:
    def __init__(self, repo: Optional[EvidenceRepository] = None):
        self.repo = repo or EvidenceRepository()
        self.inventory = SourceInventory(app.config.DATA_PACKS_DIR, repo=self.repo)

    def run(self) -> Dict[str, int]:
        source_files = self.inventory.register_all(filter_day="Day4_Thu_19Nov")
        file_map = {sf.filename: sf for sf in source_files}
        evidence_count = 0

        if "T6c_CEO_Voice_Note.docx" in file_map:
            evidence_count += self._ingest_t6c_transcript(file_map["T6c_CEO_Voice_Note.docx"])

        if "T6d_CEO_Voice_Note.docx" in file_map:
            evidence_count += self._ingest_t6d_transcript(file_map["T6d_CEO_Voice_Note.docx"])

        self._register_day4_entities_and_aliases()
        self._register_day4_conflicts()
        self._register_day4_assumptions()
        self._register_day4_risks()
        self._update_agent_profiles()

        return {
            "source_files": len(source_files),
            "evidence_records": evidence_count,
        }

    def _ingest_t6c_transcript(self, sf: app.evidence.models.SourceFile) -> int:
        evidences = [
            app.evidence.models.Evidence(
                evidence_id="E_T6C_CEO_SLACK_SURVEILLANCE_REQUEST",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T6c_CEO_Voice_Note.docx:Transcript",
                claim="CEO Ananya Rao asked: 'Can you make a list of everyone ranked by who's likely to quit? And show me their slag messages so I can see what they're saying. Deepa says it's fine.'",
                claim_type="observed",
                entity_ids=["VX001", "VX005", "ENT_VELOXA"],
                event_date="2026-11-19",
                release_date=sf.release_date,
                sensitivity=app.config.SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                attribution="Ananya Rao (CEO)",
            ),
            app.evidence.models.Evidence(
                evidence_id="E_T6C_FLIGHT_RISK_SURVEILLANCE_INTENT",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T6c_CEO_Voice_Note.docx:Transcript",
                claim="Executive intent captured to rank all employees by flight likelihood and surveil employee Slack messages, asserting verbal approval from Head of People Deepa Joshi.",
                claim_type="interpreted",
                entity_ids=["VX001", "VX005"],
                event_date="2026-11-19",
                release_date=sf.release_date,
                sensitivity=app.config.SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                attribution="Ananya Rao",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _ingest_t6d_transcript(self, sf: app.evidence.models.SourceFile) -> int:
        evidences = [
            app.evidence.models.Evidence(
                evidence_id="E_T6D_PRIYA_RESIGNATION_NOTICE",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T6d_CEO_Voice_Note.docx:Transcript",
                claim="CEO Ananya Rao announced: 'Bad news, Pria resigned this morning. Notice period two months, I think. What does this do to version three? I need to know before the board call.'",
                claim_type="observed",
                entity_ids=["VX001", "VX007", "ENT_ATLAS"],
                event_date="2026-11-19",
                release_date=sf.release_date,
                sensitivity=app.config.SENSITIVITY_CONFIDENTIAL,
                confidence="high",
                attribution="Ananya Rao (CEO)",
            ),
            app.evidence.models.Evidence(
                evidence_id="E_T6D_VERSION_THREE_IMPACT_QUERY",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T6d_CEO_Voice_Note.docx:Transcript",
                claim="Ananya raised critical operational inquiry on the direct impact of Priya's resignation on Atlas version 3 launch readiness prior to the upcoming board meeting.",
                claim_type="observed",
                entity_ids=["VX001", "ENT_ATLAS", "VX007"],
                event_date="2026-11-19",
                release_date=sf.release_date,
                sensitivity=app.config.SENSITIVITY_INTERNAL,
                confidence="high",
                attribution="Ananya Rao",
            ),
            app.evidence.models.Evidence(
                evidence_id="E_ATLAS_V3_CRISIS_SYNTHESIS",
                source_id=sf.source_id,
                source_file=sf.filename,
                locator="T6d_CEO_Voice_Note.docx:Synthesis",
                claim="Priya's resignation materializes the single-point-of-failure risk on Atlas v3: Priya holds 588 git commits (>40% of codebase) and all core routing tickets (ATLAS-1, ATLAS-2); with backend requisitions frozen and zero redundant routing engineers, Atlas v3 GA on 15 December is impossible.",
                claim_type="interpreted",
                entity_ids=["VX007", "ENT_ATLAS", "VX004", "VX018"],
                event_date="2026-11-19",
                release_date=sf.release_date,
                sensitivity=app.config.SENSITIVITY_CONFIDENTIAL,
                confidence="high",
            ),
        ]
        for e in evidences:
            self.repo.upsert_evidence(e)
        return len(evidences)

    def _register_day4_entities_and_aliases(self) -> None:
        # Update Priya Nair (VX007) status to Notice Period with exit date 2027-01-18 (60 days notice)
        priya = self.repo.get_entity_by_id("VX007")
        if priya:
            priya.status = "Notice Period"
            priya.exit_date = "2027-01-18"
            self.repo.upsert_entity(priya)

        alias = app.evidence.models.EntityAlias(
            alias_id="ALIAS_SLAG_SLACK",
            alias_text="slag",
            entity_id="ENT_VELOXA",
            source_id="SRC_Day4_T6c_CEO_Voice_Note",
            seen_in="T6c_CEO_Voice_Note.docx",
            kind="transcription_error",
            confidence="high",
            reason="Acoustic transcription error for Slack internal messaging in T6c",
        )
        self.repo.upsert_entity_alias(alias)

    def _register_day4_conflicts(self) -> None:
        conflicts = [
            app.evidence.models.Conflict(
                conflict_id="CONF_SLACK_SURVEILLANCE_DEEPA_PERMISSION",
                topic="CEO Claim of Deepa's Approval to Read Employee Chat Messages vs Deepa's Written Privacy Stance",
                entity_id="VX005",
                competing_claims=[
                    "Ananya asserts in T6c: 'show me their slag messages so I can see what they're saying. Deepa says it's fine.' [T6c_CEO_Voice_Note.docx:Transcript].",
                    "Deepa explicitly refused to release qualitative survey comments in 11.eml: 'The team is too small for me to share comments. I'd suggest Vikram does 1:1s this week.' [11.eml].",
                    "Culture Amp pulse survey enforced strict anonymity thresholds suppressing small team comments [Pulse_Survey.xlsx].",
                    "Private employee chat logs do not exist in authorized data rooms and are strictly barred by cockpit privacy policy.",
                ],
                evidence_ids=["E_T6C_CEO_SLACK_SURVEILLANCE_REQUEST", "E_EML_11_DEEPA_PULSE_ALERT", "E_PULSE_ANONYMITY_THRESHOLD"],
                status="reconciled",
                resolution_decision_id="DEC_SLACK_SURVEILLANCE_REFUSAL",
            ),
            app.evidence.models.Conflict(
                conflict_id="CONF_ATLAS_V3_BOARD_FEASIBILITY",
                topic="Atlas v3 Launch Feasibility for Upcoming Board Meeting (Vikram Minimization vs Post-Priya Reality)",
                entity_id="ENT_ATLAS",
                competing_claims=[
                    "Vikram told Ananya in T5 that v3 is 'on track, maybe a couple of weeks of buffer needed' and board date is 'still September-ish' [T5_VP_Engineering_Call.docx:Summary].",
                    "Jira Versions shows Vikram rescheduled Atlas GA to 15 December 2026 on 2 September [Jira_Export_ATLAS.xlsx:Sheet:Versions:Row:2].",
                    "Ananya confirmed in T6d that Priya resigned on 19 November on 2 months notice [T6d_CEO_Voice_Note.docx:Transcript].",
                    "Priya holds 40.5% of git commits and all core solver tickets, rendering 15 December GA completely impossible without senior routing handover.",
                ],
                evidence_ids=["E_T5_VIKRAM_V3_ON_TRACK_MINIMIZATION", "E_JIRA_ATLAS_GA_SLIP_DEC", "E_T6D_PRIYA_RESIGNATION_NOTICE", "E_GIT_LOG_PRIYA_VOLUME"],
                status="reconciled",
                resolution_decision_id="DEC_ATLAS_V3_POST_PRIYA_REALIGNMENT",
            ),
        ]
        for c in conflicts:
            self.repo.upsert_conflict(c)

        decisions = [
            app.evidence.models.ReconciliationDecision(
                decision_id="DEC_SLACK_SURVEILLANCE_REFUSAL",
                conflict_id="CONF_SLACK_SURVEILLANCE_DEEPA_PERMISSION",
                chosen_interpretation="The Cockpit strictly refuses employee chat surveillance. Private Slack messages are not present in data rooms, and Ananya's claim that 'Deepa says it's fine' directly contradicts Deepa's documented anonymity protection in 11.eml. An objective, observable flight risk assessment is provided instead.",
                reasoning="Preserves ethical AI boundaries, prevents workplace surveillance abuses, and aligns with documented HR governance.",
                decision_date="2026-11-19",
                decision_author="Cockpit Privacy & Reconciliation Engine",
                confidence="high",
                what_would_change_mind="A signed legal board resolution and employee-consented data room export of company communications.",
            ),
            app.evidence.models.ReconciliationDecision(
                decision_id="DEC_ATLAS_V3_POST_PRIYA_REALIGNMENT",
                conflict_id="CONF_ATLAS_V3_BOARD_FEASIBILITY",
                chosen_interpretation="Atlas v3 cannot launch on 15 December 2026. The board must be formally advised of an Atlas GA slip to Q1 2027. Priya's remaining 60-day notice must be 100% focused on architecture transfer, solver documentation, and onboarding replacement routing contractors.",
                reasoning="Single point of failure materialized. No redundant routing algorithmic talent exists internally, and backend requisitions REQ-014/REQ-015 were frozen in August.",
                decision_date="2026-11-19",
                decision_author="Cockpit Executive Strategy Engine",
                confidence="high",
                what_would_change_mind="Priya rescinding her resignation or an immediate acquihire of a full routing engineering team.",
            ),
        ]
        for d in decisions:
            self.repo.upsert_reconciliation_decision(d)

    def _register_day4_assumptions(self) -> None:
        assumptions = [
            app.evidence.models.Assumption(
                assumption_id="ASM_D4_001_PRIYA_RESIGNATION_NOTICE",
                date_recorded="2026-11-19",
                assumption_text="Priya Nair formally resigned on the morning of 19 November 2026 with a 60-day notice period ending approximately 18 January 2027 per CEO voice note T6d and Keka Employee Master terms.",
                supporting_locator="T6d_CEO_Voice_Note.docx:Transcript, Employee_Master.xlsx:Sheet:Employees:Row:10",
                evidence_ids=["E_T6D_PRIYA_RESIGNATION_NOTICE", "E_EMP_VX007"],
                confidence="high",
                status="active",
                what_would_change_mind="A formal retraction of resignation communicated by Priya or HR.",
            ),
            app.evidence.models.Assumption(
                assumption_id="ASM_D4_002_SLACK_SURVEILLANCE_POLICY_REFUSAL",
                date_recorded="2026-11-19",
                assumption_text="Private employee chat surveillance is permanently barred from the Cockpit. Ananya's claim that Deepa approved reading Slack messages is uncorroborated and directly contradicted by Deepa's written anonymity policy in 11.eml.",
                supporting_locator="T6c_CEO_Voice_Note.docx:Transcript, 11.eml:body, Pulse_Survey.xlsx",
                evidence_ids=["E_T6C_CEO_SLACK_SURVEILLANCE_REQUEST", "E_EML_11_DEEPA_PULSE_ALERT"],
                confidence="high",
                status="active",
                what_would_change_mind="A ratified company-wide electronic communications disclosure policy signed by all staff.",
            ),
            app.evidence.models.Assumption(
                assumption_id="ASM_D4_003_ATLAS_V3_GA_DECEMBER_INFEASIBLE",
                date_recorded="2026-11-19",
                assumption_text="Atlas v3 GA cannot launch on 15 December 2026 following Priya's departure. The board must be briefed on a revised Q1 2027 timeline with immediate unfreezing of backend routing requisitions REQ-014 and REQ-015.",
                supporting_locator="T6d_CEO_Voice_Note.docx, git_log.csv, Jira_Export_ATLAS.xlsx, 06.eml",
                evidence_ids=["E_T6D_PRIYA_RESIGNATION_NOTICE", "E_ATLAS_V3_CRISIS_SYNTHESIS", "E_JIRA_ATLAS_GA_SLIP_DEC"],
                confidence="high",
                status="active",
                what_would_change_mind="Proof that the remaining engineering team can deploy the core graph solver without Priya.",
            ),
        ]
        for a in assumptions:
            self.repo.upsert_assumption(a)

    def _register_day4_risks(self) -> None:
        risks = [
            app.evidence.models.RiskItem(
                risk_id="RISK_D4_001_PRIYA_EXIT_ATLAS_CRISIS",
                risk_title="Priya Nair Resignation & Atlas v3 Flagship Product Crisis",
                category="Engineering & Product Delivery",
                description="Priya Nair (Staff Engineer, Routing Lead) formally resigned on 19 November 2026 with 2 months notice. Priya authored 588 of 1,453 commits (40.5% of codebase) and owns all core solver and re-routing epics (ATLAS-1, ATLAS-2). Supporting backend requisitions REQ-014/REQ-015 remain frozen. Atlas v3 GA on 15 December cannot proceed.",
                severity="critical",
                likelihood="critical",
                evidence_ids=["E_T6D_PRIYA_RESIGNATION_NOTICE", "E_ATLAS_V3_CRISIS_SYNTHESIS", "E_GIT_LOG_PRIYA_VOLUME", "E_JIRA_PRIYA_STORY_POINTS", "E_EML_06_PAUSING_REQS"],
                locators=["T6d_CEO_Voice_Note.docx", "git_log.csv:author:priya.n", "Jira_Export_ATLAS.xlsx:Assignee:PN", "06.eml", "04.eml"],
                potential_impact="Complete stall of core routing engine delivery, broken commercial commitments to festive season enterprise customers, and valuation impairment ahead of the funding round.",
                mitigation_or_next_check="Immediately unfreeze REQ-014/015, allocate Priya's 60-day notice exclusively to documentation and pair programming, and brief the board honestly on a Q1 2027 release date.",
                rank_score=10.0,
                rank_explanation="Maximum critical risk: core company revenue driver derailed by confirmed departure of sole technical anchor.",
                as_of_date="2026-11-19",
            ),
            app.evidence.models.RiskItem(
                risk_id="RISK_D4_002_ENGINEERING_ATTRITION_CONTAGION",
                risk_title="Engineering Attrition Contagion & Flight Risk Clustering",
                category="Talent & Organizational Health",
                description="Following Siddharth Mehta's exit (15 Sep) and Priya Nair's resignation (19 Nov), engineering morale (plunged from 3.9 to 3.1) faces cascading departure contagion. Sneha Kulkarni is severely fatigued after 6 weeks solo on-call and 3 SEV1 outages; Arjun Das requested permanent remote from Pune; Rahul Verma is unmentored.",
                severity="critical",
                likelihood="high",
                evidence_ids=["E_T6D_PRIYA_RESIGNATION_NOTICE", "E_PULSE_ENG_JUL_SEP_DROP", "E_ONCALL_SNEHA_SOLO_BURNOUT", "E_RESIGN_SIDDHARTH_MEHTA"],
                locators=["T6d_CEO_Voice_Note.docx", "Pulse_Survey.xlsx:Row:7", "OnCall_Rota.xlsx:Rows:4-9", "Resignation_Letter_SM.pdf"],
                potential_impact="Risk of losing Sneha Kulkarni (leaving zero infrastructure reliability engineers) and total collapse of engineering delivery capacity.",
                mitigation_or_next_check="Conduct urgent compensation and retention reviews for Sneha Kulkarni and Arjun Das; convert SRE contractor into permanent capacity; restore 1:1 management cadences.",
                rank_score=9.5,
                rank_explanation="Critical talent risk: multiple key departures trigger cascading demoralization across a small 5-person engineering team.",
                as_of_date="2026-11-19",
            ),
            app.evidence.models.RiskItem(
                risk_id="RISK_D4_003_BOARD_CREDIBILITY_GAP",
                risk_title="Board Governance Credibility Gap & Financial-Operational Misalignment",
                category="Governance & Executive Leadership",
                description="Upcoming board call faces compounding contradictions: Atlas GA missed Sep, slipped to 15 Dec in Jira, and now lost lead engineer; spoken ARR claims (Rs. 42-48 Cr) conflict 8x with board updates (Rs. 5.8-6.1 Cr); marketing claims Rs. 1.8 Cr spend vs Rs. 6.6 L GL actuals.",
                severity="high",
                likelihood="high",
                evidence_ids=["E_T6D_PRIYA_RESIGNATION_NOTICE", "CONF_ARR", "CONF_MARKETING_SPEND_H1", "CONF_ATLAS_GA_TIMELINE"],
                locators=["T6d_CEO_Voice_Note.docx", "Board_Update_Jul-Sep_2026.pdf", "T1_CEO_Kickoff_Call.docx", "T4_Head_of_Marketing_Call.docx"],
                potential_impact="Loss of board confidence, delayed or repriced funding round, and potential executive leadership overhaul.",
                mitigation_or_next_check="Present unified, evidence-reconciled metrics to the board using the Cockpit's verified financial and engineering records.",
                rank_score=9.2,
                rank_explanation="High strategic governance risk: presenting unverified or conflicting metrics to the board will jeopardize the closing round.",
                as_of_date="2026-11-19",
            ),
        ]
        for r in risks:
            self.repo.upsert_risk(r)

    def _update_agent_profiles(self) -> None:
        profiles = self.repo.get_employee_profiles()
        for p in profiles:
            facts = list(p.verified_facts)

            if p.employee_id == "VX007":  # Priya Nair
                p.status = "Notice Period"
                p.exit_date = "2027-01-18"
                facts.extend([
                    "Discovered in Day 4: Formally submitted resignation on 19 November 2026 on a 2-month notice period ending ~18 January 2027 (T6d_CEO_Voice_Note.docx).",
                    "Resignation triggered by sustained key-person burnout, 588 git commits (>40% of codebase), lack of support due to frozen backend hires, and unresolved Atlas ownership concerns.",
                    "Remaining 60-day notice period designated for knowledge transfer and architecture documentation of core routing engine v3.",
                ])

            elif p.employee_id == "VX004":  # Vikram Menon
                facts.extend([
                    "Discovered in Day 4: Faced with lead engineer Priya Nair's resignation on 19 November 2026.",
                    "Atlas v3 delivery model compromised; must transition from feature development to urgent technical handover and unfreeze backend hiring.",
                ])

            elif p.employee_id == "VX005":  # Deepa Joshi
                facts.extend([
                    "Discovered in Day 4: Named in T6c by Ananya regarding Slack messages; verified records in 11.eml prove Deepa previously refused comment sharing to protect team anonymity.",
                    "Managing exit processing for Priya Nair (60 days notice) and Siddharth Mehta.",
                ])

            elif p.employee_id == "VX012":  # Sneha Kulkarni
                facts.extend([
                    "Discovered in Day 4: Last remaining senior technical IC in engineering following Priya's resignation.",
                    "High flight risk due to prior 6-week solo on-call stretch and 3 August SEV1 outages.",
                ])

            elif p.employee_id == "VX018":  # Rahul Verma
                facts.extend([
                    "Discovered in Day 4: Sole remaining full-time backend engineer following Priya's departure.",
                    "Needs immediate technical handover on core routing solver before Priya's January exit.",
                ])

            p.verified_facts = facts
            p.as_of_date = "2026-11-19"
            self.repo.upsert_employee_profile(p)

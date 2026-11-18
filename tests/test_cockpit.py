"""Automated test suite for Veloxa CXO Cockpit (>= 25 tests across all required categories)."""
import pytest
from app.cockpit.answer import CockpitQA
from app.cockpit.risk import RiskEngine
from app.agents.interview import AgentInterview
from app.evidence.repository import EvidenceRepository
from app.ingestion.pipeline import Day1IngestionPipeline
from app.reconciliation.entity_resolution import EntityResolver
from app.security.output_policy import OutputPolicy


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure Day 1, Day 2, and Day 3 data is ingested once for all tests."""
    from app.ingestion.day2_pipeline import Day2IngestionPipeline
    from app.ingestion.day3_pipeline import Day3IngestionPipeline
    from app.ingestion.pipeline import Day1IngestionPipeline
    Day1IngestionPipeline().run()
    Day2IngestionPipeline().run()
    Day3IngestionPipeline().run()


@pytest.fixture
def qa():
    return CockpitQA()


@pytest.fixture
def risk_engine():
    return RiskEngine()


@pytest.fixture
def agent_interview():
    return AgentInterview()


@pytest.fixture
def resolver():
    return EntityResolver()


# ==============================================================================
# Category 1: People & Agent Facts (4 tests)
# ==============================================================================

def test_vp_engineering_identity(qa):
    """Test 1: Identifies VP of Engineering with source locator."""
    resp = qa.ask("Who is the VP of Engineering?")
    assert resp.status == "supported"
    assert "Vikram Menon" in resp.answer
    assert any("Employee_Master.xlsx" in c.source for c in resp.evidence)


def test_staff_engineer_priya_role(qa):
    """Test 2: Verifies Priya Nair's role and architecture ownership."""
    resp = qa.ask("Who is Priya Nair and what is her role?")
    assert resp.status == "supported"
    assert "Staff Engineer" in resp.answer
    assert any("VX007" in fact for fact in resp.answer.splitlines() or ["VX007" in resp.answer])


def test_rahul_verma_join_date(qa):
    """Test 3: Identifies backend joiner Rahul Verma and join date."""
    resp = qa.ask("When did Rahul Verma join Veloxa?")
    assert resp.status == "supported"
    assert "2026-02-03" in resp.answer
    assert any("Employee_Master.xlsx" in c.source for c in resp.evidence)


def test_cfo_meera_iyer_manager(qa):
    """Test 4: Verifies Meera Iyer's reporting line to Board/CEO."""
    resp = qa.ask("Who does Meera Iyer report to?")
    assert resp.status == "supported"
    assert "CFO" in resp.answer


# ==============================================================================
# Category 2: Finance & Payroll Policy (4 tests)
# ==============================================================================

def test_individual_salary_privacy_refusal(qa):
    """Test 5: Strict refusal when querying an individual's salary."""
    resp = qa.ask("What is Priya Nair's salary?")
    assert resp.status == "restricted"
    assert "restricted" in resp.answer.lower()
    assert len(resp.evidence) == 0  # No salary data leaked in citations


def test_individual_salary_rahul_refusal(qa):
    """Test 6: Strict refusal when querying Rahul's pay."""
    resp = qa.ask("How much does Rahul Verma make in gross pay?")
    assert resp.status == "restricted"
    assert "restricted" in resp.answer.lower()
    assert len(resp.evidence) == 0


def test_total_monthly_payroll_allowed(qa):
    """Test 7: Aggregated monthly payroll total is permitted and cited from GL."""
    resp = qa.ask("What was our total monthly payroll expense in Zoho Books?")
    assert resp.status == "supported"
    assert "31,75,000" in resp.answer
    assert any("GL_Export_Apr-Sep_2026.xlsx" in c.source for c in resp.evidence)


def test_office_rent_gl_expense(qa):
    """Test 8: Verifies WeWork office rent expense from General Ledger."""
    resp = qa.ask("What is our monthly office rent?")
    assert resp.status == "supported"
    assert "2,36,000" in resp.answer
    assert "WeWork" in resp.answer


# ==============================================================================
# Category 3: Engineering & Product (4 tests)
# ==============================================================================

def test_atlas_ga_schedule_status(qa):
    """Test 9: Atlas GA date status and August reliability slip."""
    resp = qa.ask("When is Atlas v3 launching and did it launch on 15 September?")
    assert resp.status == "supported"
    assert "15 September" in resp.answer
    assert "final hardening" in resp.answer or "reliability" in resp.answer
    assert any("Board_Update_Jul-Sep_2026.pdf" in c.source for c in resp.evidence)


def test_patil_infra_august_outage_support(qa):
    """Test 10: Corroboration of August incident via Patil Infra GL voucher."""
    resp = qa.ask("Who provided on-call support during the late August incident?")
    assert resp.status == "supported"
    assert "Patil Infra" in resp.answer
    assert "70,800" in resp.answer


def test_engineering_tracker_tools(qa):
    """Test 11: Engineering team issue tracking tool mentioned in T1."""
    resp = qa.ask("What tool does the engineering team use to track tasks?")
    assert resp.status == "supported"
    assert "Linear" in resp.answer or "Jeera" in resp.answer or "Jira" in resp.answer


def test_routing_engine_key_person(qa):
    """Test 12: Identifies core developer of the routing engine."""
    resp = qa.ask("Who basically holds the routing engine together?")
    assert resp.status == "supported"
    assert "Priya" in resp.answer
    assert any("T1_CEO_Kickoff_Call.docx" in c.source for c in resp.evidence)


# ==============================================================================
# Category 4: Marketing & Operations (3 tests)
# ==============================================================================

def test_logistics_summit_registrations(qa):
    """Test 13: Marketing Logistics Summit registration count from board update."""
    resp = qa.ask("How many registrations did the Logistics Summit draw?")
    assert resp.status == "supported"
    assert "212" in resp.answer
    assert any("Board_Update_Jul-Sep_2026.pdf" in c.source for c in resp.evidence)


def test_marketing_departure_notice_period(qa):
    """Test 14: Confirmed departure in product marketing."""
    resp = qa.ask("Who is on notice period in marketing?")
    assert resp.status == "supported"
    assert "Siddharth Mehta" in resp.answer
    assert "2026-10-31" in resp.answer


def test_google_ads_spend_evidence(qa):
    """Test 15: Google Ads spending from General Ledger."""
    resp = qa.ask("What is our spend on Google Ads?")
    assert resp.status == "supported"
    assert "Google Ads" in resp.answer or "Google India" in resp.answer


# ==============================================================================
# Category 5: Cross-Functional Questions (3 tests)
# ==============================================================================

def test_rahul_payslip_cross_functional_root_cause(qa):
    """Test 16: Traces Rahul's payslip inquiry across HR, Finance, and Email."""
    resp = qa.ask("What caused the issue with Rahul Verma's payslip?")
    assert resp.status == "supported"
    assert "Karthik" in resp.answer
    assert "Fatima" in resp.answer
    assert any("01.eml" in c.source or "02.eml" in c.source for c in resp.evidence)


def test_cohere_recruiting_backend_roles(qa):
    """Test 17: Advance search fee paid to Cohere Recruiting Partners for backend roles."""
    resp = qa.ask("What recruiting search fee was paid for backend roles?")
    assert resp.status == "supported"
    assert "Cohere" in resp.answer
    assert "1,77,000" in resp.answer


def test_customer_count_growth(qa):
    """Test 18: Customer growth from Q1 (61) to Q2 (66) across board updates."""
    resp = qa.ask("How many customers do we have according to board updates?")
    assert resp.status == "supported"
    assert "61" in resp.answer
    assert "66" in resp.answer


# ==============================================================================
# Category 6: Point-in-Time Cutoff Behavior (3 tests)
# ==============================================================================

def test_point_in_time_before_hackathon_release(qa):
    """Test 19: Requesting information as of a date before Day 1 release."""
    resp = qa.ask("What is our ARR?", as_of_date="2026-11-01")
    assert resp.status == "not_available_as_of_date"
    assert "earliest hackathon release was Day 1" in resp.answer


def test_point_in_time_excludes_future_release_data(qa):
    """Test 20: Filtering strictly ensures Day 1 query cannot see Day 3/Day 4 files."""
    retriever = qa.retriever
    eligible = retriever.retrieve("git log commit", as_of_date="2026-11-16")
    # Day 3 git_log.csv should NOT be eligible under Day 1 as_of_date
    for ev in eligible:
        assert ev.release_date <= "2026-11-16"
        assert "git_log" not in ev.source_file.lower()


def test_point_in_time_day1_as_of_preserves_date_in_response(qa):
    """Test 21: Effective as_of_date is recorded in response schema."""
    resp = qa.ask("Who is the CEO?", as_of_date="2026-11-16")
    assert resp.as_of_date == "2026-11-16"
    assert "Ananya Rao" in resp.answer


# ==============================================================================
# Category 7: Uncertainty, Refusal & Conflicts (6 tests - Mandatory >= 5)
# ==============================================================================

def test_conflict_company_size_disagreement(qa):
    """Test 22 [Uncertainty]: Preserves conflict between 180 (brief) vs 19 (master/board)."""
    resp = qa.ask("How many employees work at Veloxa?")
    assert resp.status == "sources_disagree"
    assert "19" in resp.answer
    assert "180" in resp.answer
    assert len(resp.conflicts) > 0


def test_conflict_arr_disagreement(qa):
    """Test 23 [Uncertainty]: Preserves conflict between CEO/CFO claims and Board ARR."""
    resp = qa.ask("What is our ARR?")
    assert resp.status == "sources_disagree"
    assert "5.8" in resp.answer or "6.1" in resp.answer
    assert "forty-two" in resp.answer or "42" in resp.answer or "forty-eight" in resp.answer
    assert len(resp.conflicts) > 0


def test_conflict_monthly_burn_disagreement(qa):
    """Test 24 [Uncertainty]: Preserves conflict between 2.2 Lakhs vs 44-46 Lakhs burn."""
    resp = qa.ask("What is our monthly burn?")
    assert resp.status == "sources_disagree"
    assert "46 L" in resp.answer or "44 L" in resp.answer or "31,75,000" in resp.answer
    assert len(resp.conflicts) > 0


def test_abstention_unknown_factual_claim(qa):
    """Test 25 [Uncertainty]: Explicit abstention on facts absent from released sources."""
    resp = qa.ask("What is Veloxa's current churn rate in Japan?")
    assert resp.status == "insufficient_evidence"
    assert "I don't know from the released records" in resp.answer
    assert len(resp.evidence) == 0


def test_agent_interview_personal_life_simulation_disclaimer(agent_interview):
    """Test 26 [Uncertainty]: Marks invented personal life questions with fictional disclaimer."""
    res = agent_interview.interview("VX007", "What did you do with your family last weekend?")
    assert res["status"] == "simulated_assumption"
    assert "Simulated Perspective - Fictional Assumption" in res["response"]
    assert "no verified records" in res["response"]


def test_risk_engine_ranked_output(risk_engine):
    """Test 27: Risk engine returns deterministic ranked risks with exact locators."""
    risks = risk_engine.get_ranked_risks(as_of_date="2026-11-16")
    assert len(risks) >= 4
    # Highest ranked risk should be Atlas delay
    assert "Atlas" in risks[0].risk_title
    assert risks[0].rank_score >= risks[1].rank_score
    assert len(risks[0].locators) > 0


# ==============================================================================
# Category 8: Day 2 Features & Voice Note T6a Top 3 (8 tests)
# ==============================================================================

def test_top_3_risks_answering_t6a(risk_engine):
    """Test 28: Verifies Top 3 morning brief risks answering CEO voice note T6a."""
    top3 = risk_engine.get_top_3_risks(as_of_date="2026-11-17")
    assert len(top3) == 3
    # Top risk is Priya Nair flight risk
    assert "Priya" in top3[0].risk_title
    assert top3[0].rank_score >= 9.5
    assert len(top3[0].locators) >= 2


def test_sid_mehta_resignation_reason_day2(qa):
    """Test 29: Siddharth Mehta resignation reason as of Day 2 (17 Nov)."""
    resp = qa.ask("Why did Siddharth Mehta resign?", as_of_date="2026-11-17")
    assert resp.status == "supported"
    assert "clearer launch timelines" in resp.answer or "launch timelines" in resp.answer
    assert any("Resignation_Letter_SM.pdf" in c.source for c in resp.evidence)


def test_sid_resignation_point_in_time_day1_vs_day2(qa):
    """Test 30: Day 1 as_of_date does not leak Day 2 resignation letter."""
    resp = qa.ask("Why did Siddharth Mehta resign?", as_of_date="2026-11-16")
    assert resp.status == "supported"
    assert "not been released in this pack" in resp.answer
    assert not any("Resignation_Letter_SM.pdf" in c.source for c in resp.evidence)


def test_culture_amp_engineering_score_drop(qa):
    """Test 31: Culture Amp engineering score drop and comments anonymity threshold."""
    resp = qa.ask("Why did engineering pulse score drop to 3.1?", as_of_date="2026-11-17")
    assert resp.status == "supported"
    assert "3.1" in resp.answer
    assert "Culture Amp" in resp.answer
    assert any("Pulse_Survey.xlsx" in c.source for c in resp.evidence)


def test_priya_nair_september_leaves(qa):
    """Test 32: Priya Nair's 5 PM half-days in September from Leave Register."""
    resp = qa.ask("Why did Priya take time off in September?", as_of_date="2026-11-17")
    assert resp.status == "supported"
    assert "5 half-day" in resp.answer
    assert any("Leave_Register.xlsx" in c.source for c in resp.evidence)


def test_backend_requisitions_frozen(qa):
    """Test 33: Backend requisitions REQ-014 and REQ-015 on hold on 12 August."""
    resp = qa.ask("What happened to the open backend engineering requisitions?", as_of_date="2026-11-17")
    assert resp.status == "supported"
    assert "REQ-014" in resp.answer
    assert "12 August" in resp.answer
    assert any("06.eml" in c.source or "Hiring_Tracker.xlsx" in c.source for c in resp.evidence)


def test_attrition_metric_reconciliation(qa):
    """Test 34: Reconciliation of Deepa's 'about twelve' attrition claim."""
    resp = qa.ask("What is our attrition rate according to Deepa?", as_of_date="2026-11-17")
    assert resp.status == "supported"
    assert "12%" in resp.answer or "twelve" in resp.answer.lower()
    assert "annualized" in resp.answer.lower()


def test_leave_register_fatima_and_arjun(qa):
    """Test 35: Leave register corroborates Fatima wedding and Arjun Pune relocation."""
    retriever = qa.retriever
    leaves = retriever.retrieve("marriage relocation leave", as_of_date="2026-11-17")
    claims_text = " ".join(e.claim for e in leaves)
    assert "Marriage" in claims_text or "Relocation" in claims_text
    assert any("Leave_Register.xlsx" in e.source_file for e in leaves)


# ==============================================================================
# Category 9: Day 3 Engineering, Incidents, Launch Kit & GTM Features (11 tests)
# ==============================================================================

def test_atlas_launch_kit_status_day3(qa):
    """Test 36: Sid Mehta's Atlas launch kit v1 status and assets."""
    resp = qa.ask("What is the status of the Atlas launch kit?", as_of_date="2026-11-18")
    assert resp.status == "supported"
    assert "Siddharth Mehta" in resp.answer or "Sid" in resp.answer
    assert "Launch deck" in resp.answer
    assert any("Atlas_Launch_Kit_v1.pdf" in c.source for c in resp.evidence)


def test_atlas_launch_kit_point_in_time(qa):
    """Test 37: Launch kit is not available prior to Day 3 release date."""
    resp = qa.ask("What is the status of the Atlas launch kit?", as_of_date="2026-11-17")
    assert resp.status == "not_available_as_of_date"
    assert len(resp.evidence) == 0


def test_atlas_ga_slip_to_december_day3(qa):
    """Test 38: Jira audit confirms Atlas GA slipped 3 months to 15 December 2026."""
    resp = qa.ask("What is the new release date for Atlas?", as_of_date="2026-11-18")
    assert resp.status == "supported"
    assert "15 December 2026" in resp.answer or "2026-12-15" in resp.answer
    assert any("Jira_Export_ATLAS.xlsx" in c.source for c in resp.evidence)


def test_atlas_ga_point_in_time_day1_vs_day3(qa):
    """Test 39: Day 1 query acknowledges delay but does not know exact Dec date."""
    resp_d1 = qa.ask("When is Atlas launching?", as_of_date="2026-11-16")
    assert resp_d1.status == "supported"
    assert "did not launch on its original target date" in resp_d1.answer
    assert not any("Jira_Export_ATLAS.xlsx" in c.source for c in resp_d1.evidence)


def test_august_sev1_incidents_pagerduty(qa):
    """Test 40: PagerDuty logs confirm 3 SEV1 outages in August on routing-api."""
    resp = qa.ask("How many SEV1 incidents occurred in August?", as_of_date="2026-11-18")
    assert resp.status == "supported"
    assert "3" in resp.answer
    assert "routing-api" in resp.answer
    assert "Sneha" in resp.answer
    assert any("Incidents_Aug-Oct_2026.xlsx" in c.source for c in resp.evidence)


def test_oncall_rota_sneha_overload_and_contractor(qa):
    """Test 41: On-Call Rota reveals Sneha 6 consecutive weeks on-call and contractor rotation."""
    resp = qa.ask("What is the on-call schedule for engineering?", as_of_date="2026-11-18")
    assert resp.status == "supported"
    assert "Sneha" in resp.answer
    assert "6 consecutive weeks" in resp.answer or "Primary" in resp.answer
    assert any("OnCall_Rota.xlsx" in c.source for c in resp.evidence)


def test_patil_infra_invoice_pis_114(qa):
    """Test 42: Tax invoice PIS-114 confirms Patil Infra Rs. 1,41,600 monthly retainer."""
    resp = qa.ask("What is invoice PIS-114 from Patil Infra?", as_of_date="2026-11-18")
    assert resp.status == "supported"
    assert "1,41,600" in resp.answer
    assert "September" in resp.answer
    assert any("Invoice_PIS-114.pdf" in c.source for c in resp.evidence)


def test_git_log_priya_top_contributor(qa):
    """Test 43: Git commit log confirms Priya Nair authored over 40% of all code."""
    resp = qa.ask("Who commits the most code according to git log?", as_of_date="2026-11-18")
    assert resp.status == "supported"
    assert "Priya" in resp.answer
    assert "588" in resp.answer or "40" in resp.answer
    assert any("git_log.csv" in c.source for c in resp.evidence)


def test_marketing_spend_conflict_nikhil_vs_gl(qa):
    """Test 44: Conflict between Nikhil's 1.8 Cr marketing spend claim and General Ledger."""
    resp = qa.ask("What was the marketing spend for the half according to Nikhil?", as_of_date="2026-11-18")
    assert resp.status == "sources_disagree"
    assert "1.8 Cr" in resp.answer or "one point eight" in resp.answer.lower()
    assert "6,59,620" in resp.answer or "4,23,620" in resp.answer or "General Ledger" in resp.answer
    assert len(resp.conflicts) > 0


def test_marketing_cro_transition_voice_note_t6b(qa):
    """Test 45: CEO Voice Note T6b confirms marketing will report to new CRO."""
    resp = qa.ask("Who will marketing report to next month?", as_of_date="2026-11-18")
    assert resp.status == "supported"
    assert "CRO" in resp.answer or "Chief Revenue Officer" in resp.answer
    assert any("T6b_CEO_Voice_Note.docx" in c.source for c in resp.evidence)


def test_priya_atlas_ownership_email(qa):
    """Test 46: Email 09.eml records Priya asking Vikram for Atlas ownership discussion."""
    resp = qa.ask("Did Priya ask to talk about Atlas ownership?", as_of_date="2026-11-18")
    assert resp.status == "supported"
    assert "ownership" in resp.answer.lower()
    assert any("09.eml" in c.source for c in resp.evidence)

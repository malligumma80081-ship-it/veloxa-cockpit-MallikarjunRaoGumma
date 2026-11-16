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
    """Ensure Day 1 data is ingested once for all tests."""
    pipeline = Day1IngestionPipeline()
    pipeline.run()


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

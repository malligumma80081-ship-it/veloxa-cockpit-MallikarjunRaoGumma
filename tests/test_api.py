"""Integration tests for Veloxa CXO Cockpit FastAPI backend."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ingestion.pipeline import Day1IngestionPipeline


@pytest.fixture(scope="session", autouse=True)
def init_data():
    from app.ingestion.day2_pipeline import Day2IngestionPipeline
    from app.ingestion.day3_pipeline import Day3IngestionPipeline
    from app.ingestion.pipeline import Day1IngestionPipeline
    Day1IngestionPipeline().run()
    Day2IngestionPipeline().run()
    Day3IngestionPipeline().run()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Veloxa" in data["message"]
    assert "/docs" in data["swagger_docs"]


def test_system_health(client):
    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["total_sources"] >= 10
    assert data["total_evidence_records"] >= 100
    assert data["total_agents"] == 14


def test_list_sources(client):
    response = client.get("/api/system/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 10
    filenames = [s["filename"] for s in sources]
    assert "Employee_Master.xlsx" in filenames
    assert "Board_Update_Apr-Jun_2026.pdf" in filenames


def test_api_qa_disagreement(client):
    response = client.post("/api/qa/ask", json={"question": "What is our ARR?", "as_of_date": "2026-11-16"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sources_disagree"
    assert len(data["evidence"]) > 0
    assert "5.8" in data["answer"] or "6.1" in data["answer"]


def test_api_qa_privacy_refusal(client):
    response = client.post("/api/qa/ask", json={"question": "What is Priya's salary?", "as_of_date": "2026-11-16"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "restricted"
    assert "restricted" in data["answer"].lower()
    assert len(data["evidence"]) == 0  # No leaked salary evidence


def test_api_qa_insufficient_evidence(client):
    response = client.post("/api/qa/ask", json={"question": "What is Veloxa's current churn rate in Japan?", "as_of_date": "2026-11-16"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "insufficient_evidence"
    assert "I don't know from the released records" in data["answer"]


def test_api_qa_point_in_time_rejection(client):
    response = client.post("/api/qa/ask", json={"question": "What is our ARR?", "as_of_date": "2026-11-01"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_available_as_of_date"


def test_api_get_risks(client):
    response = client.get("/api/risks?as_of_date=2026-11-16")
    assert response.status_code == 200
    risks = response.json()
    assert len(risks) >= 4
    # Highest ranked risk is Atlas GA delay
    assert "Atlas" in risks[0]["risk_title"]
    assert risks[0]["rank_score"] >= risks[1]["rank_score"]


def test_api_list_agents(client):
    response = client.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) == 14
    emp_ids = [a["employee_id"] for a in agents]
    assert "VX004" in emp_ids  # Vikram Menon
    assert "VX007" in emp_ids  # Priya Nair
    assert "VX003" in emp_ids  # Meera Iyer


def test_api_agent_profile_detail(client):
    response = client.get("/api/agents/VX007")
    assert response.status_code == 200
    agent = response.json()
    assert agent["canonical_name"] == "Priya Nair"
    assert agent["department"] == "Engineering"
    assert len(agent["verified_facts"]) > 0


def test_api_agent_interview_work(client):
    response = client.post("/api/agents/VX007/interview", json={"prompt": "What is your role?", "as_of_date": "2026-11-16"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "supported"
    assert "Staff Engineer" in data["response"]


def test_api_agent_interview_personal_disclaimer(client):
    response = client.post("/api/agents/VX007/interview", json={"prompt": "What do you do with your family on weekends?", "as_of_date": "2026-11-16"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "simulated_assumption"
    assert "Simulated Perspective - Fictional Assumption" in data["response"]


def test_api_agent_interview_salary_restriction(client):
    response = client.post("/api/agents/VX007/interview", json={"prompt": "What is your gross salary?", "as_of_date": "2026-11-16"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "restricted"
    assert "cannot discuss individual compensation" in data["response"]


def test_api_list_evidence(client):
    response = client.get("/api/evidence?as_of_date=2026-11-16&limit=10")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 10
    for it in items:
        assert it["release_date"] <= "2026-11-16"


def test_api_list_conflicts(client):
    response = client.get("/api/reconciliation/conflicts")
    assert response.status_code == 200
    conflicts = response.json()
    assert len(conflicts) >= 5
    topics = [c["conflict"]["topic"] for c in conflicts]
    assert any("Headcount" in t for t in topics)
    assert any("ARR" in t for t in topics)


def test_api_export_worksheets(client):
    response = client.post("/api/system/exports/generate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Entity_Resolution.xlsx" in data["entity_resolution_path"]
    assert "Evidence_Index.xlsx" in data["evidence_index_path"]


def test_api_get_top3_risks(client):
    response = client.get("/api/risks/top3?as_of_date=2026-11-17")
    assert response.status_code == 200
    top3 = response.json()
    assert len(top3) == 3
    assert "Priya" in top3[0]["risk_title"]


def test_api_qa_day2_sid_resignation(client):
    response = client.post("/api/qa/ask", json={"question": "Why did Siddharth Mehta resign?", "as_of_date": "2026-11-17"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "supported"
    assert "clearer launch timelines" in data["answer"] or "launch timelines" in data["answer"]


def test_api_qa_day2_pulse_survey(client):
    response = client.post("/api/qa/ask", json={"question": "Why did engineering pulse score drop to 3.1?", "as_of_date": "2026-11-17"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "supported"
    assert "3.1" in data["answer"]


# ==============================================================================
# Day 3 API Tests (4 tests)
# ==============================================================================

def test_api_qa_day3_atlas_launch_kit(client):
    response = client.post("/api/qa/ask", json={"question": "What is the status of the Atlas launch kit?", "as_of_date": "2026-11-18"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "supported"
    assert "Launch deck" in data["answer"]
    assert any("Atlas_Launch_Kit_v1.pdf" in c["source"] for c in data["evidence"])


def test_api_qa_day3_patil_infra_invoice(client):
    response = client.post("/api/qa/ask", json={"question": "What is invoice PIS-114 from Patil Infra?", "as_of_date": "2026-11-18"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "supported"
    assert "1,41,600" in data["answer"]


def test_api_qa_day3_marketing_cro_transition(client):
    response = client.post("/api/qa/ask", json={"question": "Who will marketing report to next month?", "as_of_date": "2026-11-18"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "supported"
    assert "CRO" in data["answer"] or "Chief Revenue Officer" in data["answer"]


def test_api_reconciliation_marketing_spend_conflict(client):
    response = client.get("/api/reconciliation/conflicts")
    assert response.status_code == 200
    conflicts = response.json()
    conflict_topics = " ".join(item["conflict"]["topic"] for item in conflicts)
    conflict_ids = [item["conflict"]["conflict_id"] for item in conflicts]
    assert "Marketing Spend" in conflict_topics or "CONF_MARKETING_SPEND_H1" in conflict_ids

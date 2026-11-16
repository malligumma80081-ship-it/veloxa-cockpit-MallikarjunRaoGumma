"""Endpoints for 14 evidence-grounded interviewable colleagues."""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from app.agents.interview import AgentInterview
from app.api.schemas import InterviewRequest
from app.config import DEFAULT_AS_OF_DATE
from app.evidence.models import EmployeeProfile

router = APIRouter(prefix="/api/agents", tags=["Colleague Personas & Interviews"])


@router.get("", response_model=List[EmployeeProfile])
def list_agents():
    """Lists all 14 interviewable agent profiles across Engineering, Finance, HR, and Marketing."""
    interview = AgentInterview()
    return interview.list_available_agents()


@router.get("/{employee_id}", response_model=EmployeeProfile)
def get_agent_profile(employee_id: str):
    """Retrieves an employee's verified facts and simulated persona metadata."""
    interview = AgentInterview()
    profile = interview.get_agent_profile(employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Agent '{employee_id}' not found.")
    return profile


@router.post("/{employee_id}/interview")
def interview_agent(employee_id: str, req: InterviewRequest) -> Dict[str, Any]:
    """
    Conducts an interview with an employee persona.
    - Verified employment facts are grounded in Keka HRMS, call transcripts, and internal emails.
    - Personal life and thoughts are explicitly labeled as fictional assumptions.
    - Individual salary figures are strictly refused.
    """
    interview = AgentInterview()
    result = interview.interview(
        employee_id=employee_id,
        prompt=req.prompt,
        as_of_date=req.as_of_date or DEFAULT_AS_OF_DATE,
    )
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=result.get("response"))
    return result

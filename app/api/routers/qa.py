"""Executive question answering endpoints for the CEO Cockpit."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from app.api.schemas import AskQuestionRequest
from app.cockpit.answer import CockpitQA
from app.evidence.models import CockpitResponse
from app.evidence.repository import EvidenceRepository

router = APIRouter(prefix="/api/qa", tags=["Executive Q&A"])


@router.post("/ask", response_model=CockpitResponse)
def ask_cockpit(req: AskQuestionRequest):
    """
    Evaluates an executive question against released data room evidence with:
    - strict temporal point-in-time filtering (as_of_date),
    - payroll privacy enforcement (fails closed with status 'restricted' on individual salaries),
    - disagreement preservation (status 'sources_disagree' with competing citations),
    - exact source citations.
    """
    qa = CockpitQA()
    return qa.ask(question=req.question, as_of_date=req.as_of_date)


@router.get("/audit")
def get_audit_trail(limit: int = 20):
    """Returns recent question audit history."""
    repo = EvidenceRepository()
    with repo.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM answer_audit ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

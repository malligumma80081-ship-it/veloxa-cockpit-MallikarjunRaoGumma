"""Evidence retrieval and provenance search endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.config import DEFAULT_AS_OF_DATE
from app.evidence.models import Evidence
from app.evidence.repository import EvidenceRepository
from app.retrieval.search import EvidenceRetriever

router = APIRouter(prefix="/api/evidence", tags=["Evidence & Provenance"])


@router.get("", response_model=List[Evidence])
def get_evidence(
    as_of_date: str = Query(DEFAULT_AS_OF_DATE, description="Point-in-time date cutoff (YYYY-MM-DD)"),
    query: Optional[str] = Query(None, description="Optional search keywords"),
    limit: int = Query(50, ge=1, le=200, description="Maximum evidence items to return"),
):
    """
    Retrieves eligible evidence records filtered by release date <= as_of_date.
    Restricted individual payroll records are excluded from executive outputs.
    """
    retriever = EvidenceRetriever()
    if query:
        return retriever.retrieve(query=query, as_of_date=as_of_date, limit=limit)
    repo = EvidenceRepository()
    return repo.get_evidence_point_in_time(as_of_date=as_of_date, exclude_restricted=True)[:limit]


@router.get("/{evidence_id}", response_model=Evidence)
def get_evidence_by_id(evidence_id: str, as_of_date: str = DEFAULT_AS_OF_DATE):
    repo = EvidenceRepository()
    ev_list = repo.get_evidence_point_in_time(as_of_date=as_of_date, exclude_restricted=False)
    for e in ev_list:
        if e.evidence_id.lower() == evidence_id.lower():
            return e
    raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found as of {as_of_date}.")

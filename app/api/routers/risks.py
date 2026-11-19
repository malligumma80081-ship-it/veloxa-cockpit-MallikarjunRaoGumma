"""Executive worry list and risk engine endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.cockpit.risk import RiskEngine
from app.config import DEFAULT_AS_OF_DATE
from app.evidence.models import RiskItem

router = APIRouter(prefix="/api/risks", tags=["Worry List & Risks"])


@router.get("", response_model=List[RiskItem])
def get_risks(
    as_of_date: str = Query(DEFAULT_AS_OF_DATE, description="Point-in-time date cutoff (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by risk category (engineering, finance, marketing, etc.)"),
):
    """
    Returns the executive 'What should I worry about?' ranked risk list.
    Scored deterministically using severity * likelihood * evidence confidence.
    """
    engine = RiskEngine()
    return engine.get_ranked_risks(as_of_date=as_of_date, category=category)


@router.get("/top3", response_model=List[RiskItem])
def get_top_3_risks(
    as_of_date: str = Query(DEFAULT_AS_OF_DATE, description="Point-in-time date cutoff (YYYY-MM-DD)"),
):
    """
    Returns the Top 3 things to worry about today (answering CEO Voice Note T6a).
    """
    engine = RiskEngine()
    return engine.get_top_3_risks(as_of_date=as_of_date)


@router.get("/flight-risk")
def get_flight_risk(
    as_of_date: str = Query(DEFAULT_AS_OF_DATE, description="Point-in-time date cutoff (YYYY-MM-DD)"),
):
    """
    Returns the evidence-grounded employee flight risk ranking with privacy refusal for chat surveillance (answering CEO Voice Note T6c).
    """
    engine = RiskEngine()
    return engine.get_flight_risk_ranking(as_of_date=as_of_date)


@router.get("/{risk_id}", response_model=RiskItem)
def get_risk_detail(risk_id: str, as_of_date: str = DEFAULT_AS_OF_DATE):
    engine = RiskEngine()
    risks = engine.get_ranked_risks(as_of_date=as_of_date)
    for r in risks:
        if r.risk_id.lower() == risk_id.lower():
            return r
    raise HTTPException(status_code=404, detail=f"Risk '{risk_id}' not found.")

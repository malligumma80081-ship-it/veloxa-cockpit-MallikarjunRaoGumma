"""Endpoints for conflicts, reconciliation decisions, assumptions, and entities."""
from typing import Any, Dict, List
from fastapi import APIRouter
from app.evidence.models import Assumption, Conflict, Entity, EntityAlias, ReconciliationDecision
from app.evidence.repository import EvidenceRepository

router = APIRouter(prefix="/api/reconciliation", tags=["Conflicts & Assumptions"])


@router.get("/conflicts")
def get_conflicts() -> List[Dict[str, Any]]:
    """Returns all recorded source conflicts and candidate reconciliation decisions."""
    repo = EvidenceRepository()
    conflicts = repo.get_conflicts()
    decisions = {d.conflict_id: d for d in repo.get_decisions()}

    results = []
    for c in conflicts:
        d = decisions.get(c.conflict_id)
        results.append({
            "conflict": c.model_dump(),
            "reconciliation_decision": d.model_dump() if d else None,
        })
    return results


@router.get("/assumptions", response_model=List[Assumption])
def get_assumptions():
    """Returns the operational and simulation assumptions register."""
    repo = EvidenceRepository()
    return repo.get_assumptions()


@router.get("/entities", response_model=List[Entity])
def get_entities():
    """Returns canonical entities."""
    repo = EvidenceRepository()
    return repo.get_all_entities()


@router.get("/aliases", response_model=List[EntityAlias])
def get_aliases():
    """Returns alias resolution mappings."""
    repo = EvidenceRepository()
    return repo.get_aliases()

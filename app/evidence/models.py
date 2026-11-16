"""Data models for evidence, entities, conflicts, assumptions, agents, and cockpit responses."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceFile(BaseModel):
    source_id: str
    relative_path: str
    filename: str
    file_type: str
    release_day: str
    release_date: str
    document_date: Optional[str] = None
    content_hash: str
    source_description: str
    ingestion_status: str = "pending"


class Evidence(BaseModel):
    evidence_id: str
    source_id: str
    source_file: str
    locator: str
    claim: str
    claim_type: str = "observed"  # observed, reported, calculated, inferred
    entity_ids: List[str] = Field(default_factory=list)
    event_date: Optional[str] = None
    release_date: str
    sensitivity: str = "internal"  # public_demo, internal, confidential, restricted
    confidence: str = "high"  # high, medium, low
    attribution: Optional[str] = None
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    normalization_note: Optional[str] = None


class Entity(BaseModel):
    entity_id: str
    canonical_name: str
    entity_type: str  # person, vendor, project, organization, department
    department: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    manager_id: Optional[str] = None
    join_date: Optional[str] = None
    exit_date: Optional[str] = None
    status: Optional[str] = "Active"


class EntityAlias(BaseModel):
    alias_id: str
    alias_text: str
    entity_id: str
    source_id: str
    seen_in: str
    kind: str  # person, vendor, project
    confidence: str = "high"  # high, medium, low
    reason: str = ""


class Conflict(BaseModel):
    conflict_id: str
    topic: str
    entity_id: Optional[str] = None
    competing_claims: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    status: str = "open"  # open, partly_resolved, resolved
    resolution_decision_id: Optional[str] = None


class ReconciliationDecision(BaseModel):
    decision_id: str
    conflict_id: str
    chosen_interpretation: str
    reasoning: str
    decision_date: str
    decision_author: str = "Candidate"
    confidence: str = "high"  # high, medium, low
    what_would_change_mind: str
    revisit_condition: Optional[str] = None


class Assumption(BaseModel):
    assumption_id: str
    date_recorded: str
    assumption_text: str
    supporting_locator: str
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: str = "medium"  # high, medium, low
    status: str = "active"  # active, revised, rejected
    what_would_change_mind: str
    is_invented_agent_detail: bool = False


class EmployeeProfile(BaseModel):
    employee_id: str
    canonical_name: str
    department: str
    title: str
    email: str
    manager_id: Optional[str] = None
    location: str
    status: str
    join_date: str
    exit_date: Optional[str] = None
    verified_facts: List[str] = Field(default_factory=list)
    workload_evidence_ids: List[str] = Field(default_factory=list)
    history_evidence_ids: List[str] = Field(default_factory=list)
    unknown_fields: List[str] = Field(default_factory=list)
    simulated_persona: Optional[Dict[str, Any]] = None
    as_of_date: str


class RiskItem(BaseModel):
    risk_id: str
    risk_title: str
    category: str  # engineering, product, finance, hr, operations, marketing
    description: str
    severity: str  # high, medium, low
    likelihood: str  # high, medium, low, unknown
    evidence_ids: List[str] = Field(default_factory=list)
    locators: List[str] = Field(default_factory=list)
    potential_impact: str
    mitigation_or_next_check: str
    rank_score: float
    rank_explanation: str
    as_of_date: str


class EvidenceCitation(BaseModel):
    evidence_id: str
    source: str
    locator: str
    claim_snippet: Optional[str] = None


class CockpitResponse(BaseModel):
    answer: str
    status: str  # supported, sources_disagree, insufficient_evidence, restricted, not_available_as_of_date
    confidence: str  # high, medium, low
    as_of_date: str
    evidence: List[EvidenceCitation] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

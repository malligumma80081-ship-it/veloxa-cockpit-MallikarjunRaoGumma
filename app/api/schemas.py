"""API request and response schemas for FastAPI endpoints."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.config import DEFAULT_AS_OF_DATE


class AskQuestionRequest(BaseModel):
    question: str = Field(..., description="Executive question to evaluate against data room evidence", json_schema_extra={"example": "What is our ARR?"})
    as_of_date: str = Field(default=DEFAULT_AS_OF_DATE, description="Point-in-time release date cutoff (YYYY-MM-DD)", json_schema_extra={"example": "2026-11-16"})


class InterviewRequest(BaseModel):
    prompt: str = Field(..., description="Question or prompt addressed to the colleague persona", json_schema_extra={"example": "What are your current priorities?"})
    as_of_date: str = Field(default=DEFAULT_AS_OF_DATE, description="Point-in-time release date cutoff (YYYY-MM-DD)", json_schema_extra={"example": "2026-11-16"})


class IngestRequest(BaseModel):
    filter_day: Optional[str] = Field(default="Day1_Mon_16Nov", description="Release pack day to ingest (e.g. Day1_Mon_16Nov)", json_schema_extra={"example": "Day1_Mon_16Nov"})


class SystemHealthResponse(BaseModel):
    status: str
    version: str
    current_release_day: str
    as_of_date: str
    total_sources: int
    total_evidence_records: int
    total_entities: int
    total_agents: int
    total_conflicts: int


class ExportResponse(BaseModel):
    status: str
    message: str
    entity_resolution_path: str
    evidence_index_path: str

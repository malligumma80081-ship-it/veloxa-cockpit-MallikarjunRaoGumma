"""System management, healthcheck, and data ingestion endpoints."""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from app.api.schemas import ExportResponse, IngestRequest, SystemHealthResponse
from app.config import DEFAULT_AS_OF_DATE
from app.evidence.indexer import EvidenceIndexer
from app.evidence.models import SourceFile
from app.evidence.repository import EvidenceRepository
from app.ingestion.inventory import SourceInventory
from app.ingestion.pipeline import Day1IngestionPipeline
from app.reconciliation.entity_resolution import EntityResolver

router = APIRouter(prefix="/api/system", tags=["System & Ingestion"])


@router.get("/health", response_model=SystemHealthResponse)
def get_health():
    repo = EvidenceRepository()
    with repo.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM source_files")
        total_sources = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM evidence")
        total_ev = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM entities")
        total_ent = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM employee_profiles")
        total_agents = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM conflicts")
        total_conflicts = cursor.fetchone()[0]

    return SystemHealthResponse(
        status="healthy",
        version="1.0.0",
        current_release_day="Day1_Mon_16Nov",
        as_of_date=DEFAULT_AS_OF_DATE,
        total_sources=total_sources,
        total_evidence_records=total_ev,
        total_entities=total_ent,
        total_agents=total_agents,
        total_conflicts=total_conflicts,
    )


@router.get("/sources", response_model=List[SourceFile])
def list_sources():
    repo = EvidenceRepository()
    with repo.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM source_files ORDER BY release_day, filename")
        rows = cursor.fetchall()
        return [SourceFile(**dict(r)) for r in rows]


@router.post("/ingest")
def run_ingestion(req: IngestRequest):
    pipeline = Day1IngestionPipeline()
    stats = pipeline.run()
    return {
        "status": "success",
        "message": f"Ingestion completed for {req.filter_day or 'all days'}.",
        "stats": stats,
    }


@router.post("/exports/generate", response_model=ExportResponse)
def generate_worksheets():
    resolver = EntityResolver()
    res_path = resolver.export_worksheet()
    indexer = EvidenceIndexer()
    idx_path = indexer.export_index()
    return ExportResponse(
        status="success",
        message="Worksheets successfully generated and saved to exports directory.",
        entity_resolution_path=str(res_path),
        evidence_index_path=str(idx_path),
    )

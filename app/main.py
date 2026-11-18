"""Main FastAPI application for Veloxa CXO Cockpit."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import agents, conflicts, evidence, qa, risks, system
from app.config import DEFAULT_AS_OF_DATE
from app.evidence.repository import EvidenceRepository
from app.ingestion.day2_pipeline import Day2IngestionPipeline
from app.ingestion.day3_pipeline import Day3IngestionPipeline
from app.ingestion.pipeline import Day1IngestionPipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema and Day 1, Day 2, Day 3 evidence are ingested on startup if not already present
    repo = EvidenceRepository()
    repo.init_schema()
    with repo.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM evidence WHERE release_date = '2026-11-18'")
        d3_count = cursor.fetchone()[0]
    if d3_count == 0:
        Day1IngestionPipeline(repo=repo).run()
        Day2IngestionPipeline(repo=repo).run()
        Day3IngestionPipeline(repo=repo).run()
    yield


app = FastAPI(
    title="Veloxa CXO Cockpit API",
    description=(
        "Evidence-grounded executive decision cockpit backend for Veloxa Technologies. "
        "Evaluates executive Q&A, manages 14 interviewable colleague personas, "
        "ranks evidence-backed risks, enforces payroll privacy guardrails, "
        "and applies strict point-in-time temporal boundaries."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for local frontend / dashboard integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(system.router)
app.include_router(qa.router)
app.include_router(risks.router)
app.include_router(agents.router)
app.include_router(evidence.router)
app.include_router(conflicts.router)


@app.get("/", tags=["Overview"])
def root_overview():
    return {
        "message": "Welcome to the Veloxa Technologies CXO Cockpit Backend API.",
        "release_day": "Day1_Mon_16Nov",
        "default_as_of_date": DEFAULT_AS_OF_DATE,
        "swagger_docs": "/docs",
        "redoc_docs": "/redoc",
        "endpoints": {
            "health": "/api/system/health",
            "qa": "/api/qa/ask",
            "risks": "/api/risks",
            "agents": "/api/agents",
            "evidence": "/api/evidence",
            "conflicts": "/api/reconciliation/conflicts",
            "exports": "/api/system/exports/generate",
        },
    }

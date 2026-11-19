"""Main entrypoint for Veloxa CXO Cockpit."""
import argparse
import subprocess
import sys
from pathlib import Path
import uvicorn
from app.cockpit.answer import CockpitQA
from app.cockpit.risk import RiskEngine
from app.evidence.indexer import EvidenceIndexer
from app.ingestion.day2_pipeline import Day2IngestionPipeline
from app.ingestion.day3_pipeline import Day3IngestionPipeline
from app.ingestion.day4_pipeline import Day4IngestionPipeline
from app.ingestion.pipeline import Day1IngestionPipeline
from app.reconciliation.entity_resolution import EntityResolver


def main():
    parser = argparse.ArgumentParser(description="Veloxa CXO Cockpit")
    parser.add_argument("--api", "--server", action="store_true", dest="run_api", help="Launch FastAPI backend on http://localhost:8000")
    parser.add_argument("--port", type=int, default=8000, help="Port for FastAPI backend (default 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host for FastAPI backend (default 127.0.0.1)")
    parser.add_argument("--ingest", action="store_true", help="Run ingestion pipeline")
    parser.add_argument("--cli", action="store_true", help="Run interactive CLI mode instead of web UI")
    parser.add_argument("--export", action="store_true", help="Export filled Excel templates")
    args = parser.parse_args()

    # Always ensure Day 1, Day 2, Day 3 & Day 4 pipelines are ingested
    print("Ingesting / syncing Day 1, Day 2, Day 3 & Day 4 data rooms...")
    d1 = Day1IngestionPipeline()
    stats1 = d1.run()
    d2 = Day2IngestionPipeline()
    stats2 = d2.run()
    d3 = Day3IngestionPipeline()
    stats3 = d3.run()
    d4 = Day4IngestionPipeline()
    stats4 = d4.run()
    total_files = stats1['source_files'] + stats2['source_files'] + stats3['source_files'] + stats4['source_files']
    total_ev = stats1['evidence_records'] + stats2['evidence_records'] + stats3['evidence_records'] + stats4['evidence_records']
    print(f"Ingestion complete: {total_files} files, {total_ev} evidence records.")

    if args.ingest:
        return

    if args.export:
        print("Exporting Entity_Resolution.xlsx and Evidence_Index.xlsx...")
        resolver = EntityResolver()
        resolver.export_worksheet()
        indexer = EvidenceIndexer()
        indexer.export_index(as_of_date="2026-11-19")
        print("Worksheets saved to exports/ directory.")
        return

    if args.run_api:
        print(f"\n🚀 Starting Veloxa CXO Cockpit FastAPI backend on http://{args.host}:{args.port}")
        print(f"📖 Interactive Swagger API Docs: http://{args.host}:{args.port}/docs")
        print(f"📖 Redoc Documentation: http://{args.host}:{args.port}/redoc\n")
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)
        return

    if args.cli:
        print("\n=== Veloxa CXO Cockpit CLI ===")
        risk_engine = RiskEngine()
        top3 = risk_engine.get_top_3_risks(as_of_date="2026-11-17")
        print("\n🌅 Top 3 Things to Worry About Today (T6a Morning Brief):")
        for idx, r in enumerate(top3):
            print(f"  #{idx+1} [{r.rank_score:.1f}] {r.risk_title} ({r.severity.upper()})")
            print(f"     Impact: {r.potential_impact}")
            print(f"     Locators: {', '.join(r.locators[:2])}")

        qa = CockpitQA()
        while True:
            try:
                q = input("\nEnter question (or 'exit' to quit): ").strip()
                if not q or q.lower() in ["exit", "quit", "q"]:
                    break
                resp = qa.ask(q, as_of_date="2026-11-17")
                print(f"\n[Status: {resp.status.upper()} | Confidence: {resp.confidence.upper()}]")
                print(f"Answer:\n{resp.answer}")
                if resp.evidence:
                    print("\nCitations:")
                    for c in resp.evidence:
                        print(f"  * [{c.evidence_id}] {c.source} ({c.locator})")
            except (KeyboardInterrupt, EOFError):
                break
        return

    # Start Streamlit by default if not cli or api
    dashboard_path = Path(__file__).parent / "app" / "ui" / "dashboard.py"
    print(f"Starting Streamlit dashboard on http://localhost:8501...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)])


if __name__ == "__main__":
    main()

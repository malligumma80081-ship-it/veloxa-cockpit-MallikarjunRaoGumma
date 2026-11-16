"""Main entrypoint for Veloxa CXO Cockpit."""
import argparse
import subprocess
import sys
from pathlib import Path
from app.ingestion.pipeline import Day1IngestionPipeline
from app.reconciliation.entity_resolution import EntityResolver
from app.evidence.indexer import EvidenceIndexer
from app.cockpit.answer import CockpitQA
from app.cockpit.risk import RiskEngine


def main():
    parser = argparse.ArgumentParser(description="Veloxa CXO Cockpit")
    parser.add_argument("--ingest", action="store_true", help="Run Day 1 ingestion pipeline")
    parser.add_argument("--cli", action="store_true", help="Run interactive CLI mode instead of web UI")
    parser.add_argument("--export", action="store_true", help="Export filled Excel templates")
    args = parser.parse_args()

    # Always ensure Day 1 pipeline is ingested
    print("Ingesting / syncing Day 1 data room...")
    pipeline = Day1IngestionPipeline()
    stats = pipeline.run()
    print(f"Ingestion complete: {stats['source_files']} files, {stats['evidence_records']} evidence records.")

    if args.export:
        print("Exporting Entity_Resolution.xlsx and Evidence_Index.xlsx...")
        resolver = EntityResolver()
        resolver.export_worksheet()
        indexer = EvidenceIndexer()
        indexer.export_index()
        print("Worksheets saved to exports/ directory.")

    if args.cli:
        print("\n=== Veloxa CXO Cockpit CLI ===")
        qa = CockpitQA()
        while True:
            try:
                q = input("\nEnter question (or 'exit' to quit): ").strip()
                if not q or q.lower() in ["exit", "quit", "q"]:
                    break
                resp = qa.ask(q)
                print(f"\n[Status: {resp.status.upper()} | Confidence: {resp.confidence.upper()}]")
                print(f"Answer:\n{resp.answer}")
                if resp.evidence:
                    print("\nCitations:")
                    for c in resp.evidence:
                        print(f"  * [{c.evidence_id}] {c.source} ({c.locator})")
            except (KeyboardInterrupt, EOFError):
                break
        return

    # Start Streamlit by default if not cli
    dashboard_path = Path(__file__).parent / "app" / "ui" / "dashboard.py"
    print(f"Starting Streamlit dashboard on http://localhost:8501...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)])


if __name__ == "__main__":
    main()

"""Source inventory discovery and manifest generation."""
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from app.config import DATA_PACKS_DIR, RELEASE_DATES
from app.evidence.models import SourceFile
from app.evidence.repository import EvidenceRepository


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class SourceInventory:
    def __init__(self, data_packs_dir: Path = DATA_PACKS_DIR, repo: Optional[EvidenceRepository] = None):
        self.data_packs_dir = data_packs_dir
        self.repo = repo or EvidenceRepository()

    def discover_files(self, filter_day: Optional[str] = None) -> List[SourceFile]:
        source_files: List[SourceFile] = []
        if not self.data_packs_dir.exists():
            return source_files

        for path in sorted(self.data_packs_dir.glob("**/*")):
            if not path.is_file():
                continue

            rel_path = path.relative_to(self.data_packs_dir)
            parts = rel_path.parts
            day_folder = parts[0] if len(parts) > 0 else "Unknown"

            if filter_day and day_folder != filter_day:
                continue

            release_date = RELEASE_DATES.get(day_folder, "2026-11-20")
            file_type = path.suffix.lower().lstrip(".")
            if not file_type:
                file_type = "txt"

            content_hash = compute_sha256(path)
            # Create a clean source_id
            safe_name = path.stem.replace(" ", "_").replace("-", "_").replace(".", "_")
            source_id = f"SRC_{day_folder[:4]}_{safe_name}"

            description = self._classify_source(path.name, rel_path)

            sf = SourceFile(
                source_id=source_id,
                relative_path=str(rel_path).replace("\\", "/"),
                filename=path.name,
                file_type=file_type,
                release_day=day_folder,
                release_date=release_date,
                content_hash=content_hash,
                source_description=description,
                ingestion_status="pending",
            )
            source_files.append(sf)

        return source_files

    def _classify_source(self, filename: str, rel_path: Path) -> str:
        name_lower = filename.lower()
        if "employee" in name_lower:
            return "Keka HRMS Employee Master"
        if "gl_export" in name_lower:
            return "Zoho Books General Ledger Export"
        if "payroll" in name_lower:
            return "Pre-Keka Payroll Register"
        if "board_update" in name_lower:
            return "Board of Directors Quarterly Update"
        if "kickoff" in name_lower or "cfo_call" in name_lower or "call" in name_lower or "voice_note" in name_lower:
            return "MeetNotes AI Auto-Generated Call Transcript"
        if "brief" in name_lower:
            return "Executive Candidate Brief"
        if name_lower.endswith(".eml"):
            return "Selected Internal Email Correspondence"
        if "entity_resolution" in name_lower:
            return "Entity Resolution Template"
        if "evidence_index" in name_lower:
            return "Evidence Index Template"
        if "worksheet" in name_lower:
            return "Connection Analysis Worksheet"
        if "readme" in name_lower:
            return "Data Room README Manifest"
        return "Internal Document"

    def register_all(self, filter_day: Optional[str] = None) -> List[SourceFile]:
        discovered = self.discover_files(filter_day=filter_day)
        for sf in discovered:
            self.repo.upsert_source_file(sf)
        return discovered

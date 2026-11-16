"""Entity resolution and alias normalization service."""
from pathlib import Path
from typing import Dict, List, Optional
import openpyxl
from app.config import EXPORTS_DIR
from app.evidence.models import Entity, EntityAlias
from app.evidence.repository import EvidenceRepository


class EntityResolver:
    def __init__(self, repo: Optional[EvidenceRepository] = None):
        self.repo = repo or EvidenceRepository()
        self._load_cache()

    def _load_cache(self) -> None:
        self.entities = {e.entity_id: e for e in self.repo.get_all_entities()}
        self.aliases = self.repo.get_aliases()
        self.alias_map: Dict[str, str] = {}
        for a in self.aliases:
            self.alias_map[a.alias_text.strip().lower()] = a.entity_id
        for e in self.entities.values():
            self.alias_map[e.canonical_name.strip().lower()] = e.entity_id
            self.alias_map[e.entity_id.strip().lower()] = e.entity_id
            if e.email:
                self.alias_map[e.email.strip().lower()] = e.entity_id
            if e.title:
                self.alias_map[e.title.strip().lower()] = e.entity_id

        # Additional common roles / abbreviations
        self.alias_map["ceo"] = "VX001"
        self.alias_map["cfo"] = "VX003"
        self.alias_map["vp of engineering"] = "VX004"
        self.alias_map["vp engineering"] = "VX004"
        self.alias_map["head of people"] = "VX005"
        self.alias_map["head of marketing"] = "VX006"
        self.alias_map["staff engineer"] = "VX007"

    def resolve(self, query: str) -> Optional[Entity]:
        """Resolves a raw name, alias, role, or ID to a canonical Entity."""
        import re
        q = query.strip().lower()
        q_clean = re.sub(r'[^\w\s]', ' ', q)

        # Direct full match
        if q in self.alias_map:
            return self.entities.get(self.alias_map[q])
        if q_clean.strip() in self.alias_map:
            return self.entities.get(self.alias_map[q_clean.strip()])

        # Exact token/word match
        words = q_clean.split()
        for w in words:
            if w in ["ceo", "cfo"] and w in self.alias_map:
                return self.entities.get(self.alias_map[w])

        # Key phrases in query
        for alias_text, ent_id in self.alias_map.items():
            if len(alias_text) > 3 and alias_text in q_clean:
                return self.entities.get(ent_id)

        return None

    def export_worksheet(self, target_path: Optional[Path] = None) -> Path:
        """Populates the Entity_Resolution.xlsx template with resolved entities and aliases."""
        target_path = target_path or (EXPORTS_DIR / "Entity_Resolution.xlsx")
        target_path.parent.mkdir(parents=True, exist_ok=True)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Entities"

        ws.append(["Every way a person, vendor or project is identified across the files."])
        ws.append([])
        ws.append(["Name or identifier as seen", "Seen in (file)", "Resolves to", "Kind (person/vendor/project)", "Evidence refs", "Confidence (H/M/L)"])

        for alias in self.aliases:
            ent = self.entities.get(alias.entity_id)
            canonical = f"{ent.canonical_name} ({ent.entity_id})" if ent else alias.entity_id
            conf = "H" if alias.confidence == "high" else ("M" if alias.confidence == "medium" else "L")
            ws.append([
                alias.alias_text,
                alias.seen_in,
                canonical,
                alias.kind,
                alias.source_id,
                conf,
            ])

        wb.save(target_path)
        return target_path

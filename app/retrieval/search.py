"""Retrieval engine with point-in-time temporal filtering."""
import re
from typing import List, Optional, Set
from app.evidence.models import Evidence
from app.evidence.repository import EvidenceRepository

STOPWORDS: Set[str] = {
    "what", "who", "when", "where", "why", "how", "is", "are", "was", "were", "do", "does", "did",
    "the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "by", "from", "and", "or",
    "our", "my", "we", "us", "they", "them", "veloxa", "company", "current", "according", "records",
    "tell", "give", "show", "much", "many", "rate"
}


class EvidenceRetriever:
    def __init__(self, repo: Optional[EvidenceRepository] = None):
        self.repo = repo or EvidenceRepository()

    def retrieve(
        self,
        query: str,
        as_of_date: str = "2026-11-16",
        limit: int = 10,
        exclude_restricted: bool = True,
    ) -> List[Evidence]:
        """
        Retrieves eligible evidence strictly filtered by release_date <= as_of_date.
        """
        eligible_evidence = self.repo.get_evidence_point_in_time(
            as_of_date=as_of_date,
            exclude_restricted=exclude_restricted,
        )

        raw_tokens = [tok for tok in re.split(r"\W+", query.lower()) if len(tok) >= 3]
        meaningful_tokens = [tok for tok in raw_tokens if tok not in STOPWORDS]

        if not meaningful_tokens:
            return []

        scored: List[tuple[int, Evidence]] = []
        for ev in eligible_evidence:
            score = 0
            claim_lower = ev.claim.lower()
            source_lower = ev.source_file.lower()
            locator_lower = ev.locator.lower()

            for tok in meaningful_tokens:
                if tok in claim_lower:
                    score += 5
                if tok in source_lower:
                    score += 3
                if tok in locator_lower:
                    score += 2
                for ent in ev.entity_ids:
                    if tok in ent.lower():
                        score += 6

            # Require at least one meaningful token match
            if score >= 5:
                scored.append((score, ev))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ev for _, ev in scored[:limit]]

"""Risk engine generating the ranked 'What should I worry about?' view."""
from typing import List, Optional
from app.config import DEFAULT_AS_OF_DATE
from app.evidence.models import RiskItem
from app.evidence.repository import EvidenceRepository


class RiskEngine:
    def __init__(self, repo: Optional[EvidenceRepository] = None):
        self.repo = repo or EvidenceRepository()

    def get_ranked_risks(self, as_of_date: str = DEFAULT_AS_OF_DATE, category: Optional[str] = None) -> List[RiskItem]:
        """
        Returns ranked risks filtered by as_of_date and optional category.
        Scored deterministically using severity * likelihood * evidence confidence.
        """
        risks = self.repo.get_risks(as_of_date)
        if category:
            risks = [r for r in risks if r.category.lower() == category.lower()]
        return risks

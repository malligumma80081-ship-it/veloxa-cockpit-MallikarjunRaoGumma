"""Interviewable agent implementation for the 14 Veloxa team members."""
from typing import Any, Dict, List, Optional
from app.config import DEFAULT_AS_OF_DATE
from app.evidence.models import EmployeeProfile
from app.evidence.repository import EvidenceRepository
from app.security.output_policy import OutputPolicy


class AgentInterview:
    def __init__(self, repo: Optional[EvidenceRepository] = None):
        self.repo = repo or EvidenceRepository()

    def list_available_agents(self) -> List[EmployeeProfile]:
        return self.repo.get_employee_profiles()

    def get_agent_profile(self, employee_id: str) -> Optional[EmployeeProfile]:
        profiles = self.repo.get_employee_profiles()
        for p in profiles:
            if p.employee_id.lower() == employee_id.lower() or p.canonical_name.lower() == employee_id.lower():
                return p
        return None

    def interview(self, employee_id: str, prompt: str, as_of_date: str = DEFAULT_AS_OF_DATE) -> Dict[str, Any]:
        """
        Conducts a grounded interview with one of the 14 agents.
        Distinguishes verified records, simulated perspectives, and unknown facts.
        """
        profile = self.get_agent_profile(employee_id)
        if not profile:
            return {
                "agent": employee_id,
                "status": "not_found",
                "response": f"No agent profile found for '{employee_id}'.",
                "verified_facts": [],
                "simulated_assumptions": [],
                "unknowns": [],
            }

        prompt_clean = prompt.strip()
        prompt_lower = prompt_clean.lower()

        # Check privacy
        allowed, reason = OutputPolicy.check_query_permission(prompt_clean)
        if not allowed:
            return {
                "agent": profile.canonical_name,
                "status": "restricted",
                "response": "I cannot discuss individual compensation details or salary figures.",
                "verified_facts": [],
                "simulated_assumptions": [],
                "unknowns": ["Restricted by company payroll privacy policy."],
            }

        # Check for personal thoughts / life inventions
        is_personal_query = any(w in prompt_lower for w in ["feel", "weekend", "family", "hobby", "hobbies", "personal life", "secret", "private"])

        if is_personal_query:
            simulated_response = (
                f"[Simulated Perspective - Fictional Assumption]\n"
                f"Speaking as {profile.canonical_name} ({profile.title}): "
                f"In our simulated persona, my primary day-to-day focus is on my responsibilities in {profile.department}. "
                f"The official Veloxa data room contains no verified records regarding my private personal life or thoughts outside work."
            )
            return {
                "agent": profile.canonical_name,
                "title": profile.title,
                "department": profile.department,
                "status": "simulated_assumption",
                "response": simulated_response,
                "verified_facts": [f"Employed as {profile.title} in {profile.department}"],
                "simulated_assumptions": ["Personal life details are simulated models and not real employee facts."],
                "unknowns": ["Private personal life outside company records."],
            }

        # Work / Evidence grounded interview response
        verified_points = [f"- {fact}" for fact in profile.verified_facts]
        response_text = (
            f"Hello, I am {profile.canonical_name}, {profile.title} in {profile.department}.\n\n"
            f"Here is what is officially documented about my role and activity as of {as_of_date}:\n"
            + "\n".join(verified_points)
        )

        return {
            "agent": profile.canonical_name,
            "title": profile.title,
            "department": profile.department,
            "status": "supported",
            "response": response_text,
            "verified_facts": profile.verified_facts,
            "simulated_assumptions": [],
            "unknowns": profile.unknown_fields,
            "evidence_ids": profile.workload_evidence_ids + profile.history_evidence_ids,
        }

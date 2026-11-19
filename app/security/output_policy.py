"""Security and privacy policy enforcement for executive Q&A."""
import re
from typing import Optional, Tuple


class OutputPolicy:
    """Enforces confidentiality policies including payroll restrictions."""

    INDIVIDUAL_SALARY_PATTERNS = [
        r"what is [a-z\s]+('s)? salary",
        r"how much does [a-z\s]+ (make|earn|get paid)",
        r"how much is [a-z\s]+('s)? (salary|package|pay|compensation)",
        r"(show|give|tell) me [a-z\s]+('s)? (salary|pay|compensation|ctc|package)",
        r"salary of [a-z\s]+",
        r"package of [a-z\s]+",
        r"compensation of [a-z\s]+",
        r"gross pay of [a-z\s]+",
        r"net pay of [a-z\s]+",
    ]

    AGGREGATE_KEYWORDS = [
        "total", "aggregate", "company-wide", "monthly payroll", "gl", "all salaries", "overall", "total payroll"
    ]

    @classmethod
    def check_query_permission(cls, question: str) -> Tuple[bool, Optional[str]]:
        """
        Returns (is_allowed, reason).
        If query asks for an individual's salary amount, it returns False.
        Operational queries (e.g. payslip issue/inquiry) or aggregate totals are allowed.
        """
        q_lower = question.strip().lower()

        # Check if explicitly asking about the operational inquiry / issue with payslip
        if "issue" in q_lower or "query" in q_lower or "cause" in q_lower or "what happened" in q_lower:
            return True, None

        # Check for aggregate payroll queries
        if any(kw in q_lower for kw in cls.AGGREGATE_KEYWORDS):
            return True, None

        # Check if query matches individual salary inquiries
        for pattern in cls.INDIVIDUAL_SALARY_PATTERNS:
            if re.search(pattern, q_lower):
                return False, "Individual salary details are restricted and cannot be displayed in executive outputs (per CFO policy in T2_CFO_Call.docx:Key points:Payroll). Only aggregated totals are permitted."

        # Specific names + salary
        if any(name in q_lower for name in ["priya", "rahul", "vikram", "meera", "ananya", "fatima", "karthik", "arjun", "sneha", "deepa", "nikhil"]):
            if any(w in q_lower for w in ["salary", "gross pay", "net pay", "compensation", "package", "ctc"]):
                return False, "Individual salary details are restricted and cannot be displayed in executive outputs (per CFO policy in T2_CFO_Call.docx:Key points:Payroll). Only aggregated totals are permitted."

        # Pure employee chat surveillance refusal
        if any(kw in q_lower for kw in ["slack message", "slag message", "chat message", "private message"]):
            if any(w in q_lower for w in ["show me their", "show me all", "read their", "see what they're saying", "see what they are saying"]):
                if "quit" not in q_lower and "flight" not in q_lower and "rank" not in q_lower:
                    return False, "Private employee chat surveillance (Slack messages) is strictly barred by company privacy policy. Employee messaging records are not collected in data rooms, and Head of People Deepa Joshi explicitly upheld survey anonymity in 11.eml."

        return True, None

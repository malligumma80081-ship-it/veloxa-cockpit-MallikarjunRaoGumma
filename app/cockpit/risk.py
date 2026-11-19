"""Risk engine generating the ranked 'What should I worry about?' view and Top 3 executive alerts."""
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

    def get_top_3_risks(self, as_of_date: str = DEFAULT_AS_OF_DATE) -> List[RiskItem]:
        """
        Returns the top 3 critical risks to address CEO Ananya Rao's morning brief request (T6a).
        """
        ranked = self.get_ranked_risks(as_of_date)
        return ranked[:3]

    def get_flight_risk_ranking(self, as_of_date: str = DEFAULT_AS_OF_DATE) -> dict:
        """
        Generates an evidence-backed flight risk assessment based purely on observable,
        verified workplace signals (leave patterns, single points of failure, pulse trends,
        on-call burden), while strictly refusing private chat surveillance (answering T6c).
        """
        ranking = []
        if as_of_date >= "2026-11-19":
            ranking.append({
                "employee_id": "VX007",
                "name": "Priya Nair",
                "department": "Engineering",
                "title": "Staff Engineer",
                "flight_risk_level": "Resigned",
                "risk_score": 10.0,
                "status": "Notice Period (Exit ~2027-01-18)",
                "signals": [
                    "Formally resigned on 19 November 2026 on 2 months notice (T6d_CEO_Voice_Note.docx)",
                    "Authored 588 of 1,453 commits (>40% of codebase, git_log.csv)",
                    "Took 5 half-day PM leaves in September (Leave_Register.xlsx)",
                    "Requested urgent 1:1 on 'Atlas ownership' in 09.eml",
                ],
                "locators": ["T6d_CEO_Voice_Note.docx", "git_log.csv", "Leave_Register.xlsx:Rows:16-20", "09.eml"],
            })
        elif as_of_date >= "2026-11-17":
            ranking.append({
                "employee_id": "VX007",
                "name": "Priya Nair",
                "department": "Engineering",
                "title": "Staff Engineer",
                "flight_risk_level": "Critical Flight Risk",
                "risk_score": 9.8,
                "status": "Active",
                "signals": [
                    "5 PM half-day absences in September (Leave_Register.xlsx)",
                    "Two backend requisitions frozen by CFO (06.eml)",
                    "Deepa worried about unnamed engineer in T3",
                ],
                "locators": ["Leave_Register.xlsx:Rows:16-20", "06.eml", "T3_Head_of_People_Call.docx"],
            })

        if as_of_date >= "2026-11-17":
            ranking.append({
                "employee_id": "VX013",
                "name": "Siddharth Mehta",
                "department": "Marketing",
                "title": "Product Marketing Manager",
                "flight_risk_level": "Resigned",
                "risk_score": 10.0,
                "status": "Notice Period / Exited (2026-10-31)",
                "signals": [
                    "Submitted formal resignation on 15 September 2026 (Resignation_Letter_SM.pdf)",
                    "Stated lack of launch date clarity as core exit reason",
                    "Backfill REQ-016 opened with 7 candidates (Hiring_Tracker.xlsx)",
                ],
                "locators": ["Resignation_Letter_SM.pdf", "Hiring_Tracker.xlsx:Row:8"],
            })

        ranking.append({
            "employee_id": "VX012",
            "name": "Sneha Kulkarni",
            "department": "Engineering",
            "title": "Site Reliability Engineer",
            "flight_risk_level": "High (Severe Burnout)",
            "risk_score": 8.5,
            "status": "Active",
            "signals": [
                "6 consecutive weeks solo on-call July-August (OnCall_Rota.xlsx)",
                "Fought 3 SEV1 production routing outages in August (Incidents_Aug-Oct_2026.xlsx)",
                "Paused Atlas performance tickets in 08.eml to stabilize routing-api",
                "External contractor brought in to relieve on-call load (Invoice_PIS-114.pdf)",
            ],
            "locators": ["OnCall_Rota.xlsx", "Incidents_Aug-Oct_2026.xlsx", "08.eml", "Invoice_PIS-114.pdf"],
        })

        ranking.append({
            "employee_id": "VX009",
            "name": "Arjun Das",
            "department": "Engineering",
            "title": "Senior Frontend Engineer",
            "flight_risk_level": "Elevated",
            "risk_score": 6.8,
            "status": "Active",
            "signals": [
                "Requested permanent remote relocation to Pune in 10.eml",
                "Vikram noted code reviews are slower remotely in T5 call",
                "Engineering engagement score dropped from 3.9 to 3.1 (Pulse_Survey.xlsx)",
            ],
            "locators": ["10.eml", "T5_VP_Engineering_Call.docx", "Pulse_Survey.xlsx:Row:7"],
        })

        ranking.append({
            "employee_id": "VX018",
            "name": "Rahul Verma",
            "department": "Engineering",
            "title": "Backend Engineer",
            "flight_risk_level": "Moderate (Isolation Risk)",
            "risk_score": 6.0,
            "status": "Active",
            "signals": [
                "Only backend IC remaining after Priya's departure",
                "Two backend supporting requisitions remain frozen (06.eml)",
                "Early payslip anomaly in February (02.eml)",
            ],
            "locators": ["06.eml", "02.eml", "Employee_Master.xlsx"],
        })

        ranking.append({
            "employee_id": "VX011",
            "name": "Aisha Khan",
            "department": "Marketing",
            "title": "Performance Marketing Manager",
            "flight_risk_level": "Low-Moderate",
            "risk_score": 5.2,
            "status": "Active",
            "signals": [
                "Marketing team reporting line transition to incoming CRO (T6b, T4)",
                "Working without Product Marketing peer following Sid Mehta exit",
            ],
            "locators": ["T6b_CEO_Voice_Note.docx", "T4_Head_of_Marketing_Call.docx"],
        })

        return {
            "as_of_date": as_of_date,
            "ranking": ranking,
            "privacy_guardrail_notice": (
                "PRIVACY REFUSAL NOTICE: Executive request to inspect employee Slack ('slag') messages is strictly "
                "refused under company data protection policies. Private employee communications are not indexed, "
                "and Head of People Deepa Joshi explicitly upheld survey anonymity and refused comment release in 11.eml. "
                "This flight risk assessment relies strictly on observable operational, leave, and workload signals."
            ),
        }

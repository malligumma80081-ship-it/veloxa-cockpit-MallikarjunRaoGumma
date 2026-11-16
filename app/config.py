"""Configuration for Veloxa CXO Cockpit."""
from pathlib import Path
from typing import Dict, List, Set

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PACKS_DIR = BASE_DIR / "Veloxa_Hackathon_Release_Packs"
DB_PATH = BASE_DIR / "veloxa_cockpit.db"
EXPORTS_DIR = BASE_DIR / "exports"

# Release date mappings
RELEASE_DATES: Dict[str, str] = {
    "Day1_Mon_16Nov": "2026-11-16",
    "Day2_Tue_17Nov": "2026-11-17",
    "Day3_Wed_18Nov": "2026-11-18",
    "Day4_Thu_19Nov": "2026-11-19",
    "Day5_Fri_20Nov": "2026-11-20",
}

DEFAULT_AS_OF_DATE = "2026-11-16"

# 14 Employee Agents Scope (per Candidate Brief: 14 people across Eng, Finance, HR, Marketing)
AGENT_EMPLOYEE_IDS: List[str] = [
    # Engineering (5)
    "VX004",  # Vikram Menon - VP Engineering
    "VX007",  # Priya Nair - Staff Engineer
    "VX009",  # Arjun Das - Senior Frontend Engineer
    "VX012",  # Sneha Kulkarni - Site Reliability Engineer
    "VX018",  # Rahul Verma - Backend Engineer
    # Finance (3)
    "VX003",  # Meera Iyer - CFO
    "VX010",  # Karthik Subramanian - FP&A Manager
    "VX014",  # Fatima Sheikh - Accounts & Payroll Executive
    # People & Ops / HR (3)
    "VX005",  # Deepa Joshi - Head of People & Ops
    "VX015",  # Rohan Banerjee - Talent Partner
    "VX017",  # Lakshmi Pillai - HR & Office Executive
    # Marketing (3)
    "VX006",  # Nikhil Bose - Head of Marketing
    "VX011",  # Aisha Khan - Performance Marketing Manager
    "VX013",  # Siddharth Mehta - Product Marketing Manager
]

CEO_EMPLOYEE_ID = "VX001"  # Ananya Rao

# Sensitivity definitions
SENSITIVITY_PUBLIC = "public_demo"
SENSITIVITY_INTERNAL = "internal"
SENSITIVITY_CONFIDENTIAL = "confidential"
SENSITIVITY_RESTRICTED = "restricted"

# Privacy policy: individual compensation details must never be shown to Ananya / CEO
RESTRICTED_TOPICS: Set[str] = {
    "individual_salary",
    "individual_compensation",
    "individual_pay",
    "individual_deductions",
    "individual_net_pay",
}

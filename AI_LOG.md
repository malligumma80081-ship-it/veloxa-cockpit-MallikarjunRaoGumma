# 🤖 Veloxa CXO Cockpit — AI Assistance Log

This document records the prompts, tool interactions, code generation steps, and candidate reviews conducted with AI assistance during the hackathon.

---

## Session: Day 1 (16 November 2026)

### Objective
- Ingest Day 1 release pack (`Veloxa_Hackathon_Release_Packs/Day1_Mon_16Nov`).
- Design and implement the Day 1 baseline architecture for the Veloxa CXO Cockpit.
- Implement point-in-time retrieval, privacy/refusal guardrails, entity resolution, conflict tracking, risk engine, and 14 interviewable agent profiles.
- Build automated test suite (>= 25 tests) and interactive Streamlit UI.

### Key Prompts & Human Guidance
1. **Source Discovery & Parsing**:
   - Prompted AI assistant to extract and inspect the zip archive containing Day 1 to Day 4 packs.
   - Identified that docx files can be parsed using `python-docx` or standard XML parsing, PDF via `pypdf`, and XLSX via `openpyxl`.
   - Directed assistant to retain exact cell/sheet coordinates (`Sheet:Employees:Row:4`) and page numbers (`page_1`) for atomic provenance.

2. **Entity Resolution & 14-Agent Scope**:
   - Analyzed `Employee_Master.xlsx` which has 19 employee records.
   - Guided assistant to map the 14 agents specifically across Engineering (5), Finance (3), HR (3), and Marketing (3) to fulfill the Candidate Brief requirements, while keeping CEO Ananya Rao as the executive querier.
   - Mapped phonetically misheard names in call transcripts (e.g., "Pria" -> Priya Nair, "Vicky" -> Vikram Menon, "Kartik" -> Karthik Subramanian, "Fatima Shaikh" -> Fatima Sheikh).

3. **Payroll Privacy & Output Guardrails**:
   - Highlighted CFO Meera Iyer's rule from `T2_CFO_Call.docx`: *"Individual salaries must never show up in anything Ananya sees, only totals."*
   - Directed implementation of deterministic code-level filtering (`OutputPolicy`) rather than relying on LLM prompt instructions.
   - Verified that individual payroll records carry `sensitivity = "restricted"` and are blocked before retrieval, while aggregated company payroll totals are permitted.

4. **Conflict Modeling & Uncertainty Testing**:
   - Structured the 5 material Day 1 contradictions: Company Size (180 vs 19), ARR (42-45 Cr vs 5.8-6.1 Cr), Burn (2.2 Lakhs vs 44-46 Lakhs), Atlas Launch (15 Sep vs Delayed), and Marketing Spend.
   - Enforced status `sources_disagree` and `insufficient_evidence` when evidence is conflicting or missing.
   - Developed 27 automated tests with `pytest` covering all required categories.

5. **Code Review & Bug Fixes**:
   - Identified indexing offset in `XlsxParser` which initially caused VX001 (Ananya Rao) to be skipped because of empty metadata rows. Corrected slice index to `sheet_rows[2:]`.
   - Verified 100% test pass rate (27/27 passed).

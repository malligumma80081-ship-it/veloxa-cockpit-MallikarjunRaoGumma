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

6. **FastAPI Backend Development**:
   - Developed full REST API backend with modular routers: `system`, `qa`, `risks`, `agents`, `evidence`, and `conflicts`.
   - Added automatic database initialization and ingestion via FastAPI lifespan.
   - Built 16 automated integration tests in `tests/test_api.py` covering health, Q&A, privacy guardrails, risk retrieval, 14-agent interview, and conflict APIs.
   - Total automated test suite expanded to 43 passing tests.
   - Updated CLI `run.py` to support launching the FastAPI server with `--api`.

---

## Session: Day 2 (17 November 2026)

### Objective
- Ingest Day 2 release pack (`Veloxa_Hackathon_Release_Packs/Day2_Tue_17Nov`):
  - `Hiring_Tracker.xlsx`, `Leave_Register.xlsx`, `Pulse_Survey.xlsx`, `Resignation_Letter_SM.pdf`, `T3_Head_of_People_Call.docx`, `T6a_CEO_Voice_Note.docx`, emails `06.eml`, `07.eml`, `10.eml`, `11.eml`.
- Address CEO Voice Note T6a: Implement automatic Top 3 morning brief on system startup.
- Track new Day 2 conflicts (Deepa attrition metric), assumptions, and risks (Priya flight risk, engineering pulse drop).
- Expand test suite to 54 tests.

### Key Work & Implementations
1. **Day 2 Ingestion Pipeline (`app/ingestion/day2_pipeline.py`)**:
   - Ingested Hiring Tracker requisitions (REQ-011 through REQ-017).
   - Ingested Leave Register, identifying Priya Nair's 5 PM half-days in September.
   - Ingested Pulse Survey, capturing engineering drop from 3.9 to 3.1 and Culture Amp anonymity threshold suppression.
   - Ingested Siddharth Mehta's resignation letter citing unclear launch timelines.
   - Resolved Deepa's "about twelve" attrition claim as an annualized ~12% rate rather than 12 departures.
2. **Top 3 Morning Brief (T6a Voice Note Response)**:
   - Added `get_top_3_risks()` to `RiskEngine`.
   - Exposed `GET /api/risks/top3` in FastAPI backend.
   - Integrated Top 3 hero card prominently into the landing view of Streamlit dashboard.
   - Updated CLI startup to print Top 3 morning brief.
   - Documented formal response in `VOICE_NOTE_RESPONSES.md`.

---

## Session: Day 3 (18 November 2026)

### Objective
- Fix 2 failing Day 2 tests (`test_cohere_recruiting_backend_roles` and `test_backend_requisitions_frozen`).
- Ingest Day 3 release pack (`Veloxa_Hackathon_Release_Packs/Day3_Wed_18Nov`):
  - `Atlas_Launch_Kit_v1.pdf`, `Invoice_PIS-114.pdf`, `Incidents_Aug-Oct_2026.xlsx`, `Jira_Export_ATLAS.xlsx`, `OnCall_Rota.xlsx`, `git_log.csv`, emails `04.eml`, `05.eml`, `08.eml`, `09.eml`, `Email_Printouts.pdf`, `T4_Head_of_Marketing_Call.docx`, `T5_VP_Engineering_Call.docx`, `T6b_CEO_Voice_Note.docx`.
- Implement Day 3 ingestion pipeline (`app/ingestion/day3_pipeline.py`).
- Implement Day 3 executive Q&A handlers in `app/cockpit/answer.py`.
- Formulate executive response to CEO Voice Note T6b regarding marketing transition to incoming CRO.
- Expand automated test suite to 69 tests and ensure 100% pass rate.

### Key Work & Implementations
1. **Test Fixes**:
   - Resolved token overlap where "backend roles" intercepted Cohere recruiting search fee queries, creating dedicated handler for advance search fee (`E_GL_RECRUITING_FEE`, Rs. 1,77,000).
   - Broadened requisition hold keyword matching so plural and descriptive queries match REQ-014/REQ-015 freeze before falling through to entity resolution.
2. **Day 3 Ingestion Pipeline (`app/ingestion/day3_pipeline.py`)**:
   - Ingested all 14 Day 3 files with atomic evidence records, locators, and release date `2026-11-18`.
   - Extracted Jira ATLAS version records showing Vikram moved Atlas GA from 15-Sep to 15-Dec on 02-Sep.
   - Parsed 11 PagerDuty incidents, identifying 3 SEV1 outages on routing-api in August.
   - Tracked On-Call Rota showing Sneha on-call for 6 consecutive weeks before contractor relief.
   - Parsed 1,453 git commits, discovering Priya Nair authored 588 commits (>40% of codebase).
   - Ingested Patil Infra Tax Invoice PIS-114 for Rs. 1,41,600 monthly retainer.
   - Registered Day 3 conflicts (`CONF_MARKETING_SPEND_H1`, `CONF_SNEHA_SNEHAL_IDENTITY`, `CONF_ATLAS_GA_TIMELINE`), assumptions (`ASM_D3_001` through `ASM_D3_003`), and risks (`RISK_D3_001` through `RISK_D3_003`).
   - Updated 14 agent verified facts with Day 3 discoveries.
3. **Executive Q&A Handlers (`app/cockpit/answer.py`)**:
   - Added handlers for Atlas Launch Kit, 15-Dec Atlas slip in Jira, August SEV1 incidents, On-Call Rota, Patil Infra PIS-114 invoice, Git log contributions, Marketing spend conflict (Nikhil 1.8 Cr vs GL), CRO transition (T6b), and Priya's late-night ownership email.
4. **Voice Note T6b Response**:
   - Documented operational analysis in `VOICE_NOTE_RESPONSES.md` addressing marketing spend disconnect (₹1.8 Cr vs ₹6.6 L GL actuals), cold leads from summit, and PMM backfill vacancy.
   - Documented system changes for dynamic entity hierarchy and pointer rebinding.
5. **Testing & Verification**:
   - Added 11 domain tests and 4 API tests. Total tests expanded to 69.
   - Ran `pytest`: 69 passed, 0 failures. Execution time: ~12s.
   - Refreshed export worksheets `Entity_Resolution.xlsx` and `Evidence_Index.xlsx`.

# 🧭 Veloxa CXO Cockpit

Evidence-grounded executive decision cockpit for **Veloxa Technologies**, built for the Hiyaku Systems Hackathon (16–20 November 2026).

---

## 🚀 Quick Start (One-Command Setup & Run)

```bash
# 1. Clone repository
git clone <repo-url>
cd veloxa-cockpit

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run automated test suite (27 tests)
pytest -v

# 5. Launch the Streamlit CXO Cockpit
python run.py
```

To run in terminal CLI mode:
```bash
python run.py --cli
```

To re-export populated worksheets (`Entity_Resolution.xlsx` and `Evidence_Index.xlsx`):
```bash
python run.py --export
```

---

## 🎯 Day 1 Core Capabilities (16 Nov 2026)

1. **Evidence-Grounded Executive Q&A**:
   - Queries answered with exact source locators (`[file:sheet:row]` or `[file:page]` or `[file:Message-ID]`).
   - Strict status classification: `supported`, `sources_disagree`, `insufficient_evidence`, `restricted`, `not_available_as_of_date`.
   - Explicit confidence levels (`high`, `medium`, `low`) with transparent reasoning.

2. **Privacy by Design (CFO Payroll Policy)**:
   - Enforces CFO Meera Iyer's strict rule (`T2_CFO_Call.docx:Key points:Payroll`): *“Individual salaries must never show up in anything Ananya sees, only totals.”*
   - Individual compensation queries (e.g., *“What is Priya's salary?”*) immediately fail closed with status `restricted` and zero leaked compensation figures.
   - Company-wide aggregate payroll totals are safely computed and cited from Zoho Books General Ledger.

3. **Point-in-Time Temporal Boundaries**:
   - Every factual record carries an immutable `release_date`.
   - When answering as of `2026-11-16` (Day 1), data released on later days (Day 2/3/4) is filtered out before retrieval.
   - Questions requesting information prior to release return `not_available_as_of_date`.

4. **Preserved Disagreements & Reconciliation Decisions**:
   - Competing source claims are preserved rather than silently averaged or collapsed:
     - **Company Headcount**: 180 (Candidate Brief) vs. 19 (Employee Master & Board Updates). Audio transcription ambiguity between *"eighteen"* and *"one-eighty"*.
     - **ARR**: Spoken transcript claims (*“42–45 crore”* / *“forty-eight”*) vs. official Board Updates (*₹5.8 Cr* / *₹6.1 Cr*).
     - **Monthly Burn**: Spoken transcript claims (*“2.2 lakhs”*) vs. Board Updates (*₹44 L – ₹46 L*), disproved by General Ledger payroll alone (*₹31.75 L*).
     - **Atlas v3 GA Date**: Scheduled 15 September GA was postponed after August reliability issues; engine in final hardening as of October Board update.

5. **"What Should I Worry About?" Ranked Risk Engine**:
   - Ranked executive risk view with severity, likelihood, impact, next check, and direct source locators:
     - **Risk 1**: Atlas v3 GA delay past promised festive customer window.
     - **Risk 2**: Single point of failure (SPOF) on core routing engine (Priya Nair).
     - **Risk 3**: Discrepancy between executive claims and board financial governance.
     - **Risk 4**: Payroll internal control breakdown (unprorated February pay for Rahul Verma).
     - **Risk 5**: Product Marketing Manager departure during launch preparation (Siddharth Mehta).

6. **14 Interviewable People as Evidence-Backed Agents**:
   - 14 profiles spanning Engineering (5), Finance (3), HR/People & Ops (3), and Marketing (3).
   - Strict separation between verified employment facts, unknown fields, and fictional simulated personas.

---

## 📁 Repository Structure

```
.
├── ARCHITECTURE.md             # System architecture and data flow design
├── ASSUMPTIONS.md              # Log of explicit operational assumptions
├── TRANSCRIPT_NOTES.md         # Detailed analysis of call transcripts & conflicts
├── DECISIONS.md                # Trade-off decisions and rationale
├── AI_LOG.md                   # Log of AI assistant interactions and prompt review
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── run.py                      # Main application entry point (UI / CLI / Ingest)
├── exports/                    # Populated Entity_Resolution and Evidence_Index workbooks
├── app/
│   ├── config.py               # Paths, release dates, sensitivity rules
│   ├── ingestion/              # Ingestion manifest, parsers (DOCX, PDF, XLSX, EML), pipeline
│   ├── evidence/               # Relational data models, repository, indexer
│   ├── reconciliation/         # Entity resolution, alias normalization, conflict tracking
│   ├── retrieval/              # Point-in-time filtering and keyword search
│   ├── security/               # Output policy, sensitivity classifications, privacy redactions
│   ├── cockpit/                # Q&A answering engine, risk ranking engine
│   ├── agents/                 # 14 interviewable agent profiles
│   └── ui/                     # Streamlit dashboard
├── tests/
│   └── test_cockpit.py         # 27 automated tests across 7 mandatory categories
└── Veloxa_Hackathon_Release_Packs/ # Extracted hackathon release data
```

---

## 🧪 Automated Testing

Run the full suite with pytest:
```bash
pytest -v tests/test_cockpit.py
```
Test categories covered:
- People & Agent Facts (4 tests)
- Finance & Payroll Policy (4 tests)
- Engineering & Product (4 tests)
- Marketing & Operations (3 tests)
- Cross-Functional Reconciliation (3 tests)
- Point-in-Time Cutoff Boundaries (3 tests)
- Uncertainty, Refusal & Conflicts (6 tests)

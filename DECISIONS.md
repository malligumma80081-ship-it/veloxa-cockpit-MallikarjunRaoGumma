# ⚖️ Veloxa CXO Cockpit — Architectural & Design Decisions

This document records key design trade-offs made during development, documenting alternatives considered, rationale, and revisit triggers.

---

## DEC-001: Relational SQLite Storage over Standalone Vector Database
- **Decision:** Use an embedded relational database (SQLite) as the single source of truth for evidence, entities, aliases, conflicts, and risks, rather than relying on a vector database or pure LLM context stuffing.
- **Alternatives Considered:**
  1. *Vector Database (Chroma / Pinecone / Qdrant)*: Better for fuzzy semantic clustering, but non-deterministic, hard to enforce point-in-time date filters without metadata leaks, and difficult to audit exact row/cell locators.
  2. *In-Memory JSON / Dictionaries*: Fast to code, but lacks SQL query capabilities, transaction boundaries, and persistence.
- **Rationale:**
  - Facilitates 1-command fresh clone setup with zero external daemon dependencies.
  - Enables deterministic point-in-time temporal filtering (`release_date <= :as_of_date`).
  - Ensures exact table-cell and document-page locators are preserved and cited.
- **Revisit Trigger:** If text corpus expands in Day 3/4 beyond what keyword and metadata retrieval can efficiently search.

---

## DEC-002: Enforcing Payroll Privacy at Code Level vs. Prompt Instructions
- **Decision:** Enforce the CFO payroll privacy rule (*“individual salaries must never show up in anything Ananya sees, only totals”*) via a deterministic software policy layer (`OutputPolicy`) that inspects query intent and scrubs individual records, rather than relying on system prompt guardrails.
- **Alternatives Considered:**
  1. *LLM Prompt Instruction*: Instructing the model: *"You must not reveal individual salaries."* Vulnerable to prompt injection, hallucination, or accidental citation leaks in evidence blocks.
  2. *Redacting Payroll Data at Ingestion*: Completely omitting individual salary rows from the database. This would prevent the system from knowing about payroll anomalies (such as Rahul Verma's partial month query) in audit contexts.
- **Rationale:**
  - Deterministic defense-in-depth: individual salary rows are tagged `sensitivity = "restricted"`.
  - When the CEO cockpit answers questions, restricted evidence is excluded before retrieval.
  - Individual salary questions immediately return `status = "restricted"` with an explicit refusal and zero leaked numbers in citations.
  - Aggregate payroll queries (e.g. total monthly payroll vouchers) remain accessible.
- **Revisit Trigger:** If the CFO authorizes specific executive salary bands or compensation reviews.

---

## DEC-003: Selection of the 14 Interviewable Agents
- **Decision:** Select 14 specific employees across the four required departments (Engineering, Finance, HR, Marketing) from the 19 records in Employee Master:
  - **Engineering (5):** Vikram Menon (VP Eng, VX004), Priya Nair (Staff Eng, VX007), Arjun Das (Frontend Eng, VX009), Sneha Kulkarni (SRE, VX012), Rahul Verma (Backend Eng, VX018).
  - **Finance (3):** Meera Iyer (CFO, VX003), Karthik Subramanian (FP&A Manager, VX010), Fatima Sheikh (Payroll Exec, VX014).
  - **HR & People (3):** Deepa Joshi (Head of People, VX005), Rohan Banerjee (Talent Partner, VX015), Lakshmi Pillai (HR Exec, VX017).
  - **Marketing (3):** Nikhil Bose (Head of Marketing, VX006), Aisha Khan (Performance Mktg, VX011), Siddharth Mehta (Product Mktg, VX013).
- **Excluded:**
  - Ananya Rao (VX001) is the executive user querying the system.
  - Sales (Manoj Kumar VX002, Divya Reddy VX008) and Support (Imran Siddiqui VX016, Kavya Narayan VX019) are retained in the entity database but excluded from the 14-agent roster per Candidate Brief instructions.
- **Rationale:**
  - Candidate Brief explicitly requires: *"start with 14 people across engineering, finance, HR and marketing"*.
  - 5 + 3 + 3 + 3 = 14 exactly spans the four designated departments.
- **Revisit Trigger:** If subsequent release packs explicitly introduce Sales or Support incident workflows.

---

## DEC-004: Preserving Disagreements vs. Forcing a Single Number
- **Decision:** For metrics where sources contradict each other (Company Headcount, ARR, Monthly Burn), the system returns `status = "sources_disagree"` and explains both sides with exact citations, rather than silently choosing a winner.
- **Alternatives Considered:**
  1. *Silently Picking Board Updates*: While board updates are more reliable, returning only ₹6.1 Cr ARR would hide the fact that the CEO believes ARR is ₹45 Cr.
  2. *Averaging the Numbers*: Meaningless mathematical blending.
- **Rationale:**
  - Executive cockpits must alert leadership to internal misalignment and data divergence.
  - Ananya needs to know that her spoken understanding differs by 8x from board governance presentations.
- **Revisit Trigger:** If an audited financial report is released that explicitly resolves the delta.

---

## DEC-005: Risk Engine Deterministic Scoring Formula
- **Decision:** Score and rank risks deterministically using:
  $$\text{Rank Score} = \text{Severity Weight} \times \text{Likelihood Weight} \times \text{Evidence Strength}$$
  - Severity: High (3.0), Medium (2.0), Low (1.0)
  - Likelihood: High (3.0), Medium (2.0), Low (1.0)
  - Evidence Strength: Direct multi-source corroboration (1.1), Single source (1.0)
- **Alternatives Considered:**
  1. *LLM Subjective Ranking*: Asking an LLM to rank risks dynamically. Unstable across runs and impossible to unit test deterministically.
- **Rationale:**
  - Ensures predictable, explainable risk prioritization that can be defended in whiteboard review sessions.
- **Revisit Trigger:** If new release packs add quantitative risk probability distributions.

Veloxa CXO Cockpit — Architecture
Version: 1.0
Architecture date: 16 November 2026 (IST)
Status: Day 1 baseline; implementation details may evolve as later release packs arrive.
Scope: Five-day Hiyaku Systems hackathon submission.
1. Product objective
Build an evidence-grounded executive cockpit for the fictional Veloxa Technologies. The CEO should be able to ask a natural-language question and receive a concise answer that:
- cites the exact records supporting each material claim;
- reports a confidence level and explains important uncertainty;
- says “I don't know” when the released evidence is insufficient;
- says “the sources disagree” when material claims conflict;
- provides a ranked “What should I worry about?” view with evidence;
- answers “What did we know on date X?” using only material released on or before that date.
The system will also represent 14 people as interviewable, evidence-grounded AI agents/profiles. Verified facts, unknowns, and invented assumptions must remain distinguishable.

The goal is a small, explainable prototype that can be run and defended—not a large autonomous platform.
2. Requirements and delivery constraints
The five-day hackathon invitation dated 16 November 2026 is the controlling schedule for this implementation:
Release day	Material	Required voice-note response	Due
Day 1 — Mon 16 Nov	T1, T2 and Day 1 data room	Repository link and this architecture document	11:59 PM IST
Day 2 — Tue 17 Nov	T3, T6a and Day 2 data room	T6a	11:59 PM IST
Day 3 — Wed 18 Nov	T4, T5, T6b and Day 3 data room	T6b	11:59 PM IST
Day 4 — Thu 19 Nov	T6c and T6d	T6c and T6d	11:59 PM IST
Day 5 — Fri 20 Nov	No new release	Final frozen submission	6:00 PM IST


The invitation makes point-in-time answers and at least 25 automated tests mandatory. The Candidate Brief describes a different ten-working-day format and calls those two features stretch items. For this five-day submission, the invitation's stricter requirements take precedence.

Other submission constraints:
- Public Git repository, named veloxa-cockpit-[your-name].
- At least two meaningful commits per day.
- Code freeze Friday 20 November at 6:00 PM IST.
- Final email must include repository URL, frozen commit hash, and one fresh-clone setup/run command.
- Maintain README.md, ARCHITECTURE.md, ASSUMPTIONS.md, TRANSCRIPT_NOTES.md, DECISIONS.md, and AI_LOG.md.
- Write a response to each CEO voice note on its release day. Implement a justified change or document a reasoned pushback.
3. Day 1 source context and boundaries
3.1 Day 1 source inventory
The Day 1 release folder contains:
Source	Format	Intended use
T1_CEO_Kickoff_Call.docx	DOCX, machine-generated call summary	CEO priorities and claims; treat names, tools, figures and speaker attribution cautiously
T2_CFO_Call.docx	DOCX, machine-generated call summary	Finance context, accounting-system history, hiring and payroll constraints
Candidate_Brief.docx	DOCX	Product intent, 14-person agent scope, challenge rules and evaluation priorities
Employee_Master.xlsx	XLSX / Employees sheet	Employee identity, department, title, manager, dates and status
GL_Export_Apr-Sep_2026.xlsx	XLSX / GL Apr-Sep sheet	Selected Zoho Books general-ledger transactions and cost centres
Payroll_Register_Jan-Mar_2026.xlsx	XLSX / Payroll Q4 sheet	Historical payroll register; restricted individual compensation data
Board_Update_Apr-Jun_2026.pdf	PDF, one page	Board-reported quarterly metrics and Atlas plan
Board_Update_Jul-Sep_2026.pdf	PDF, one page	Later board-reported metrics and Atlas status
README.txt	TXT	Data-room export description and source-system inventory
email/01.eml–`email/03.eml`	EML	Selected finance/payroll correspondence
Entity_Resolution.xlsx	XLSX template	Alias-to-entity mapping and confidence
Evidence_Index.xlsx	XLSX template	One fact per row, source locator, entity, date and confidence
Connection_Worksheet.pdf	PDF template	Relationship/connection analysis


The data-room README says the exports were made by IT on 31 October 2026. It identifies Keka HRMS, Zoho Books, Jira, Git history, PagerDuty, on-call rota, board documents, invoices, letters, launch materials and selected email threads as source categories across the release packs.
3.2 Known Day 1 source characteristics
- T1 is explicitly an auto-generated summary; it describes fair audio quality and includes uncertain tool names and numbers.
- T2 is explicitly an auto-generated summary; it describes poor speakerphone audio and flags a possible ambiguity in the fiscal-year wording.
- The Employee Master says it is a Keka HRMS employees-only export, generated 31 October 2026, and contractors are not in Keka.
- The GL export is described as a Zoho Books export for April–September 2026 and selected cost centres, not necessarily a complete company-wide ledger.
- The payroll workbook is a January–March 2026 register from the pre-Keka payroll workbook.
- The board PDFs are marked confidential. The April–June update was sent 8 July 2026; the July–September update was sent 6 October 2026.
- Evidence_Index.xlsx instructs the user to record one fact per row. Entity_Resolution.xlsx is supplied to record aliases and identity resolution.
These characteristics inform source evaluation. They do not create a universal rule that one source type is always correct.
3.3 Day 1 claims that must remain separately represented
The sources report different company-size figures:
- Candidate Brief: 180-person company.
- T1: “roughly eighteen people” with an uncertain parenthetical transcription (“one-eighty, give or take”).
- April–June board update: team 19.
- Employee Master: 19 employee records, explicitly excluding contractors.
The system must not silently collapse these into a single total-workforce fact. “19 employee records” is supportable; “total workforce is 19” is not established by this export.

The April–June board update reports ARR ₹5.8 Cr, 61 customers, team 19, monthly burn ₹46 L and runway 14 months. It says Atlas routing engine v3 was on track for GA on 15 September, with real-time re-routing as the headline requested feature, and that two backend engineers were to be added.

The July–September board update (sent 6 October) reports ARR ₹6.1 Cr, 66 customers, team 19, monthly burn ₹44 L and runway 13 months. It says Atlas GA was moved after unplanned reliability work during a difficult August; the engine was feature-complete and in final hardening. It also says hiring was paused while the company closed the round and mentions one planned marketing departure.

T1 reports ARR “around forty-two crore, maybe forty-five now” and burn “around two point two” with no unit stated. T2 reports ARR at the start of the year as “forty-eight” and burn as “two point two lakhs a month, sometimes two point five”. These claims conflict in scale and/or unit with the board figures. The application must retain the claims and their locators, not silently convert units or invent an explanation.

T2 contains a specific instruction that individual salaries must never appear in anything Ananya sees, only totals. This is an access/output policy for the CEO-facing cockpit.
4. Architecture principles
1. Evidence before language generation. Deterministic code decides which records are eligible, retrieves them, and checks citations. An LLM may help interpret or phrase a response but does not decide which source is true.
2. Atomic facts. Store one claim per evidence record wherever practical. Do not store only a whole-document summary.
3. Traceable provenance. Every fact points to a source file and a precise locator: page, sheet and row, email Message-ID, transcript heading/paragraph, or source record identifier.
4. Preserve disagreement. Competing claims remain visible. A reconciliation decision records the human's reasoning, evidence, confidence and revisit condition.
5. Time-aware knowledge. Distinguish when an event happened from when the evidence was released to the hackathon. Historical answers filter by release date before retrieval.
6. Separate fact from invention. Verified facts, model inferences, unknowns and invented agent-life details are separate fields and separate response types.
7. Privacy by design. Sensitive fields are access-controlled and excluded from CEO-facing prompts, retrieval results, logs and citations unless explicitly permitted. In particular, individual payroll amounts are not shown to the CEO.
8. Fail closed on unsupported claims. If evidence is missing, conflicting, out of date, or outside the user's permitted scope, the cockpit abstains or explains the limitation.
9. Small, explainable implementation. Prefer a modular monolith and a simple database over distributed services that cannot be built, tested and defended in five days.
5. Logical system architecture
                  RELEASED HACKATHON SOURCE PACKS
        DOCX | PDF | XLSX | CSV/exports | EML | TXT
                              |
                              v
                    1. INGESTION PIPELINE
             file inventory -> format parsers -> validation
                              |
                              v
                   2. NORMALIZED SOURCE STORE
             original file metadata + extracted content
                              |
                              v
                     3. EVIDENCE LAYER
       atomic claims + source locators + dates + sensitivity
                    /                    \
                   v                      v
         ENTITY RESOLUTION          RECONCILIATION
        aliases -> canonical IDs    competing claims -> human
                                    decision / unresolved status
                   \                      /
                    \                    /
                              v
                    4. KNOWLEDGE SERVICES
            as-of filter | retrieval | evidence ranking
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
        PEOPLE/AGENTS      CEO Q&A          RISK ENGINE
        14 profiles        answer policy    ranked evidence
        evidence memory    citation check   and uncertainty
             |                |                |
             +----------------+----------------+
                              |
                              v
                      5. RESPONSE VALIDATOR
             citation membership | privacy | time cutoff
               unsupported claims | confidence/status
                              |
                              v
                       6. CXO COCKPIT
             ask a question | agent interview | worry list
                    historical as-of date selector
5.1 Application modules
Proposed Python package boundaries:
app/
  main.py                  # application entry point / optional FastAPI
  config.py                # paths, release dates, environment configuration
  ingestion/
    inventory.py           # source manifest and file discovery
    parsers.py             # DOCX, PDF, XLSX, EML, TXT extraction
    normalize.py           # dates, amounts, names and whitespace
    validate.py            # schema and extraction checks
  evidence/
    models.py              # SourceFile, Evidence, Entity, Conflict, Assumption
    repository.py          # persistence and query methods
    indexer.py              # build evidence index
  reconciliation/
    entity_resolution.py   # aliases and canonical identities
    conflicts.py           # competing claims and decision records
  retrieval/
    as_of.py                # release-date cutoff
    search.py               # keyword/metadata retrieval
    ranking.py              # relevance and source context
  agents/
    base_agent.py
    employee_profile.py
    registry.py
    interview.py
    memory.py
  cockpit/
    answer.py
    confidence.py
    refusal.py
    citations.py
    risk.py
    response_schema.py
  security/
    sensitivity.py
    output_policy.py
  ui/
    dashboard.py
    evidence_view.py
    agent_interview.py
tests/
  unit/
  integration/
  fixtures/
A modular monolith is the initial deployment model. FastAPI may expose service endpoints if useful; Streamlit is the primary demo interface. The core domain logic should be callable directly from tests without starting either web server.
6. Data model
Use a relational model as the source of truth. SQLite is the Day 1 prototype choice because it is easy to run from a fresh clone; keep the repository layer isolated so PostgreSQL can replace it if necessary. Do not make a vector database the authoritative store.
6.1 Core entities
source_files
Field	Meaning
source_id	Stable source identifier
relative_path	Original relative path within release pack
filename, file_type	File metadata
release_day, release_date	Hackathon release boundary
document_date	Date printed in the source, if any
content_hash	Detect changed/re-ingested files
source_description	Transcript, HR export, GL export, board update, email, etc.
ingestion_status	pending / parsed / partial / failed


evidence
Field	Meaning
evidence_id	Stable ID such as E001
source_id	Foreign key to source file
locator	Exact page, sheet+row, email Message-ID, paragraph/heading
claim	One atomic fact or attributed statement
claim_type	observed / reported / calculated / inferred
entity_ids	Linked canonical entities
event_date	When the described event occurred, if known
release_date	When this pack became available
valid_from, valid_to	Optional validity interval, only when supported
sensitivity	public_demo / internal / confidential / restricted
extraction_quality	parser quality or manual-review state
attribution	Who or what the source attributes the statement to


entities
- entity_id, canonical_name, entity_type
- department, title, and other typed attributes where relevant
- status and supported validity dates
- created_from_evidence_id
entity_aliases
- alias_id, entity_id, alias_text, source_id
- resolution_confidence, resolution_reason, evidence_ids
This table is the normalized implementation of the supplied Entity Resolution worksheet. Ambiguous aliases must remain unresolved rather than being forced to a person.
conflicts
- conflict_id, topic, entity_id (optional)
- evidence_ids for all competing claims
- status: open / partly_resolved / resolved
- decision_id (optional)
reconciliation_decisions
- decision_id, conflict_id
- chosen_interpretation or explicit unresolved
- reasoning written by the candidate
- decision_date, decision_author
- confidence
- what_would_change_mind
- supersedes_decision_id (optional; preserve history)
assumptions
- assumption_id, date_recorded, assumption_text
- supporting_locator / source evidence IDs
- confidence, status
- what_would_change_mind
- revision_of (optional)
Do not delete an assumption when later evidence disproves it. Mark it revised or rejected and link the new entry.
employee_profiles
- employee_id (canonical entity reference)
- verified_profile_json
- workload_evidence_ids
- history_evidence_ids
- personal_context_evidence_ids
- unknown_fields
- as_of_date
agent_scenarios
- scenario_id, employee_id
- invented_detail, assumption_id
- scenario_start_date, scenario_end_date
- is_simulated
- visible_disclaimer
Any invented personal life, private thought, or activity must be clearly marked as fictional/simulated and linked to an assumption record. It must never be blended into verified employment history.
risks
- risk_id, risk_title, category, description
- severity, likelihood (only when supportable)
- evidence_ids, conflict_ids, assumption_ids
- mitigation_or_next_check
- rank_score, rank_explanation
- as_of_date
answer_audit
- question, as-of date, retrieved evidence IDs
- answer status, confidence, citations emitted
- privacy/refusal validation result
- model/prompt version (if an LLM is used)
- created timestamp
6.2 Supplied worksheets
Use the provided Evidence_Index.xlsx as the initial human-readable evidence register and Entity_Resolution.xlsx as the initial alias-resolution worksheet. Their entries should be imported or kept synchronized with the database. The evidence index explicitly expects one fact per row and includes source, locator, fact, entities, written date, normalized IST date and confidence.
7. Ingestion and normalization
7.1 Pipeline
1. Enumerate files in each release folder and assign its official release date.
2. Preserve the original relative path and compute a content hash.
3. Parse by file type:
   - DOCX: paragraphs and tables.
   - PDF: text by page; retain page numbers.
   - XLSX: workbook, sheet, row and cell coordinates; retain formulas/values as appropriate.
   - EML: headers, Message-ID, sender, recipient, sent date, subject and body.
   - TXT: preserve line numbers.
4. Normalize whitespace, date representations, currency symbols and entity aliases without changing source text.
5. Extract atomic claims and attach exact locators.
6. Mark extraction uncertainty and require manual review for ambiguous names, numbers, units and speaker attribution.
7. Store evidence and update the evidence index.
8. Run validation checks and report parse failures rather than silently dropping files.
7.2 Preserve original and normalized values
For amounts, dates, names and tools, keep:
- raw_value: exactly as found;
- normalized_value: only when normalization is unambiguous;
- normalization_note: method and caveat.
For example, T1's “two point two” has no unit. Do not normalize it to rupees, lakhs or crores. The board's “Rs. 46 L” can be stored as raw text plus a normalized INR value of 4,600,000, with the original label retained.
7.3 Idempotency and re-ingestion
Use (source_id, locator, claim_hash) or an equivalent stable key to avoid duplicate evidence when ingestion is rerun. If a source file changes, its content hash changes and the ingestion report must show the difference. Do not overwrite manually entered reconciliation decisions.
8. Source evaluation and reconciliation
There is no universal rule that “exports always win.” The challenge says exports are generally more reliable than transcripts but also warns that exports have quirks. Evaluate each disagreement using:
1. Directness: transaction-level/system record vs recollection or summary.
2. Specificity: exact metric, unit, period, population and scope.
3. Temporal relevance: date of the source and reporting period.
4. Completeness: selected cost centres, employees-only export, missing contractors, partial email thread, etc.
5. Independent corroboration: whether another source supports the same claim.
6. Known source limitations: machine transcription, migration between accounting systems, legacy payroll, export scope, manual entry.
7. Attribution and incentives: who made the claim and whether it is firsthand or secondhand.
Every material conflict receives a row in TRANSCRIPT_NOTES.md and a structured reconciliation decision. The candidate owns the decision. If no conclusion is defensible, leave the conflict open and make the cockpit say “the sources disagree.”
8.1 Initial Day 1 examples
- Company size: Candidate Brief says 180 people; T1's auto-summary contains ambiguous wording around “eighteen/one-eighty”; board update says team 19; Employee Master contains 19 employee records and says contractors are excluded. Store all claims. The export supports “19 employee records,” not “total workforce is 19.”
- ARR and burn: T1 and T2 transcript figures differ in scale and/or unit from the board updates. Keep the original phrases and period labels. Do not silently convert or explain away the discrepancy.
- Atlas: April–June board update says GA was on track for 15 September; the later July–September update says GA moved after reliability work and Atlas was in final hardening. As of the 6 October board update, report the later status; do not claim GA occurred.
- Payroll privacy: T2 explicitly says individual salaries must never appear in anything Ananya sees, only totals. Enforce this in retrieval and output, not merely in prompt instructions.
9. Point-in-time retrieval
The invitation requires historical answers. Store at least two distinct dates:
- event_date: when the underlying event happened, if known.
- release_date: when the relevant pack became available to the candidate.
For a query with as_of_date = D, the eligible evidence set is:
SELECT e.*
FROM evidence e
WHERE e.release_date <= :as_of_date;
Apply this filter before keyword search, semantic retrieval, ranking, agent memory lookup, risk computation and LLM context construction. Filtering only the final answer is insufficient because future records could influence reasoning.

The release-date configuration is fixed by the invitation:
- 16 November: Day 1 pack.
- 17 November: Day 2 pack.
- 18 November: Day 3 pack.
- 19 November: Day 4 pack.
A later source may update the current answer, but must not rewrite what the system says was knowable on an earlier date. Tests must explicitly attempt to leak Day 2/3/4 evidence into Day 1 answers.
10. The 14 people as interviewable agents
The Candidate Brief asks for 14 people across engineering, finance, HR and marketing. The Employee Master contains 19 employee records; it does not imply that all 19 become agents. Select the 14-person scope using the brief and the actual records, and document the selection.

Implement one reusable agent class with 14 separate evidence-backed profiles—not 14 independently coded LLM applications.

Each agent has:
- canonical employee ID and verified name;
- verified department, title, manager and employment dates;
- workload and project history backed by evidence;
- supported personal context, where available;
- explicit unknown fields;
- links to source evidence;
- assumptions for invented details;
- a knowledge as_of_date.
10.1 Agent interview policy
When asked about a person:
1. Retrieve only evidence allowed for that agent and as-of date.
2. Distinguish “the record says” from “the agent's simulated perspective.”
3. Cite records for work facts.
4. Mark invented life details and private thoughts as fictional assumptions.
5. Never invent sensitive personal attributes or present a simulated thought as a real employee statement.
6. If a fact is absent, answer that it is unknown rather than improvising a factual answer.
The hackathon permits invented details to make agents feel like real colleagues, but every invention must be logged in ASSUMPTIONS.md. Simulated post-31 October activity is a stretch feature and must be clearly labeled as generated activity, not actual company history.
11. CEO question-answering contract
11.1 Request flow
1. Receive question and optional as-of date.
2. Identify intent and entities.
3. Apply authorization and sensitivity policy.
4. Apply release-date cutoff.
5. Retrieve relevant evidence and conflict records.
6. Evaluate whether evidence is sufficient and consistent.
7. Generate a short answer from the retrieved evidence only.
8. Validate each factual sentence against cited evidence.
9. Validate citations, privacy and temporal cutoff.
10. Return answer, status, confidence, evidence and limitations.
11.2 Response schema
{
  "answer": "Short executive answer.",
  "status": "supported",
  "confidence": "medium",
  "as_of_date": "2026-11-16",
  "evidence": [
    {
      "evidence_id": "E001",
      "source": "source filename",
      "locator": "page / sheet and row / email Message-ID"
    }
  ],
  "conflicts": [],
  "unknowns": [],
  "limitations": []
}
Allowed statuses:
- supported
- sources_disagree
- insufficient_evidence
- restricted
- not_available_as_of_date
Confidence is an ordinal explanation (high / medium / low), not a calibrated probability. A numeric score may be used internally for ranking, but the UI must not imply statistical certainty.
11.3 Refusal and uncertainty behavior
- No relevant evidence: insufficient_evidence, say “I don't know from the released records.”
- Material incompatible evidence: sources_disagree, describe the disagreement and cite both sides.
- Evidence released after requested date: not_available_as_of_date.
- Sensitive individual payroll detail: restricted; do not return the amount, including in citations, snippets, logs or LLM context.
- Unsupported inference: omit it or label it as an inference with its basis; do not state it as a fact.
12. Confidence policy
Use transparent rules rather than asking the LLM to invent a confidence number. Consider:
- source directness and reliability;
- precision and completeness of the locator;
- corroboration by independent evidence;
- temporal relevance;
- unresolved conflict;
- extraction quality and ambiguity.
Initial qualitative interpretation:
- High: direct, specific, in-scope record; no material unresolved conflict; locator verified.
- Medium: evidence is relevant but indirect, incomplete, partly corroborated, or has a limited caveat.
- Low: ambiguous transcript, missing unit/scope, material contradiction, weak extraction, or unsupported linkage.
A contradiction should normally lower confidence or produce sources_disagree, not be averaged away. Record the reason for each confidence level.
13. “What should I worry about?” risk view
The risk engine creates a ranked list from evidence-backed issues. It does not generate a list of generic business risks.

Each risk must include:
- concise risk statement;
- category (finance, people, engineering, product, marketing, operations);
- severity and likelihood, only where supportable;
- evidence IDs and exact locators;
- conflict/unknown details;
- potential impact;
- next check or mitigation;
- reason for its rank;
- as-of date.
Use a transparent initial scoring policy, for example:

risk_score = severity_weight * likelihood_weight * evidence_strength

The scoring method and weights must be documented in DECISIONS.md. If likelihood cannot be inferred, mark it unknown and avoid false precision. Evidence strength affects confidence in the risk, not the underlying business severity. The UI should distinguish risk priority from confidence in the assessment.
14. Privacy and security
- Treat payroll rows and compensation fields as restricted.
- For CEO-facing output, aggregate payroll only; suppress individual salaries and any snippets that could reveal them.
- Keep sensitive raw data out of application logs, test failure messages and AI prompts unless strictly needed by an authorized operation.
- Do not expose employee records through unauthenticated endpoints in a deployed environment.
- Keep secrets in environment variables; never commit .env, credentials or access tokens.
- The supplied company, people, emails, transcripts and records are fictional hackathon data. Do not search for Veloxa online or treat the material as real.
- Keep source packs private if the hackathon rules or organizers require it; the repository itself is public, so check whether the data pack may be committed before adding raw source files. If uncertain, keep source data out of Git and provide a clear local data placement instruction.
15. User interface
The Streamlit cockpit should prioritize answer trust over visual complexity.

Main sections:
1. Ask the Cockpit: question input and concise answer.
2. Evidence: citations open the source file/locator or show a safe excerpt.
3. Confidence and uncertainty: visible confidence, status, conflicts and unknowns.
4. What should I worry about?: ranked evidence-backed risk list.
5. People: select and interview one of the 14 agents; show verified facts separately from assumptions.
6. As-of date: choose a release date; show the effective evidence cutoff.
A dashboard metric or chart must be traceable to the underlying records and must not replace the question-answering workflow.
16. Testing and evaluation
At least 25 automated question tests are required by the invitation. Run them with one command (pytest -q).

Proposed minimum distribution:
Test category	Count
People and agent facts	4
Finance and payroll policy	4
Engineering/product	4
Marketing/operations	3
Cross-functional questions	3
Point-in-time behavior	2
Uncertainty/refusal/conflict	5
Total	25


At least five tests must verify correct abstention or uncertainty. Include tests for:
- a fact absent from all released sources;
- a material contradiction;
- a later-release fact requested as of an earlier date;
- a restricted individual payroll amount;
- an unsupported employee personal-life detail.
Also test parser behavior, exact locators, duplicate ingestion, entity resolution, source conflict retention, citation membership, risk ranking determinism and fresh-clone setup. Store question, expected status, expected evidence IDs, expected answer constraints and actual result in a machine-readable test set.
17. Technology and deployment decisions
Initial, time-boxed choices:
Layer	Choice	Reason
Language	Python 3.11+	Readable and suitable for document/data processing
Tabular parsing	Pandas + openpyxl	XLSX/CSV exports
DOCX	python-docx	Transcript and brief extraction
PDF	PyMuPDF or pypdf	Page-aware text extraction
Email	Python email package	Preserve headers and Message-ID
Validation	Pydantic	Typed input/output contracts
Database	SQLite	Minimal local setup and reliable demo
Backend	Python service layer; FastAPI if API endpoints are useful	Testable domain logic
UI	Streamlit	Fast five-day cockpit
LLM	Optional local Ollama model after evidence/refusal rules work	Avoid making core truth logic dependent on generation
Tests	Pytest	One-command evaluation
Version control	Git + public Git hosting	Auditable daily progress


No vector database is required for Day 1. Start with exact metadata filters and keyword retrieval. Add embeddings only if the corpus demonstrates a retrieval need and there is time to evaluate it. The relational evidence store remains authoritative.
17.1 Fresh-clone setup
The final README will provide one command that:
1. creates/uses the Python environment;
2. installs dependencies;
3. initializes the database;
4. ingests the locally supplied data pack;
5. starts the cockpit.
The final command must be tested from a clean clone before the 20 November 6:00 PM IST freeze. The exact command will be finalized after the app entry point and setup script exist.
18. Delivery plan
Day 1 — 16 November
- Inspect Day 1 sources.
- Create repository and initial package structure.
- Define source/evidence/entity/conflict/assumption model.
- Record initial source conflicts and privacy rules.
- Commit this architecture by 11:59 PM IST.
Day 2 — 17 November
- Ingest Day 2 HR material and T3/T6a.
- Select 14 employee profiles from source evidence.
- Implement reusable agent/profile and interview behavior.
- Write and commit T6a response by 11:59 PM IST.
Day 3 — 18 November
- Ingest marketing and engineering release material.
- Implement cross-functional retrieval and evidence linking.
- Write and commit T6b response by 11:59 PM IST.
Day 4 — 19 November
- Analyze T6c/T6d and document implement/pushback decisions.
- Complete CEO answer policy, confidence, risk ranking and point-in-time filtering.
- Commit both voice-note responses by 11:59 PM IST.
Day 5 — 20 November
- Finish Streamlit interface and integration.
- Complete at least 25 automated tests, including at least five uncertainty tests.
- Verify documentation and fresh-clone setup.
- Create final frozen commit and submit by 6:00 PM IST.
19. Open decisions to revisit
The following remain intentionally open until later releases or implementation evidence is available:
- Which exact 14 employee records should become agents, and how to ensure the selection spans the four required departments.
- Which additional aliases in the Entity Resolution worksheet can be resolved confidently.
- Whether keyword retrieval is sufficient or embeddings materially improve recall.
- Which risk weights are defensible after reviewing actual risk examples.
- Whether the prototype needs FastAPI in addition to Streamlit.
- Which agent memory should be persistent versus reconstructed from evidence at query time.
- Whether simulated post-31 October activity adds value without confusing fictional activity with actual records.
Every change to these decisions must be recorded in DECISIONS.md; new evidence and revised interpretations must be recorded without deleting the history.
20. Definition of done
The architecture is considered implemented only when:
- every released file is inventoried and ingestion status is visible;
- every returned factual claim has a valid source locator;
- conflicts and assumptions are preserved and auditable;
- 14 agents are grounded in employee records and distinguish facts from simulations;
- CEO responses show status, confidence, evidence and unknowns;
- restricted individual payroll values cannot reach CEO-facing output;
- risk items are ranked and evidence-backed;
- point-in-time answers exclude later releases before retrieval;
- at least 25 automated tests pass, including five uncertainty/refusal tests;
- T6a–T6d responses are committed on their respective release days;
- a fresh clone can be set up and run with the single command documented in README.
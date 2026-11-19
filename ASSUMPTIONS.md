# 📋 Veloxa CXO Cockpit — Assumptions Log

This document records operational, architectural, and data reconciliation assumptions made during system design and implementation. Per hackathon guidelines, entries are never deleted when revised or disproved; their status is updated with new evidence.

---

### ASM-001: Total Full-Time Employee Headcount is 19
- **Date Recorded:** 2026-11-16 (Day 1)
- **Status:** Active
- **Assumption:** Veloxa Technologies has exactly 19 full-time employees on official payroll as of 31 October 2026. The "180" figure in Candidate Brief and T1 transcript arose from acoustic transcription ambiguity between "eighteen" and "one-eighty".
- **Source Line / Evidence:**
  - `Employee_Master.xlsx:Sheet:Employees:Rows:4-22` (19 distinct named employee records VX001–VX019).
  - `Employee_Master.xlsx:Sheet:Employees:Row:1` ("Keka HRMS export, employees only (contractors are not in Keka)").
  - `Board_Update_Apr-Jun_2026.pdf:page_1` ("Team 19").
  - `Board_Update_Jul-Sep_2026.pdf:page_1` ("Team 19").
  - `T1_CEO_Kickoff_Call.docx:Summary` ("roughly eighteen people ('one-eighty, give or take')").
- **Confidence:** High
- **What Would Change Mind:** Production of a company-wide roster or contractor invoices showing ~160 active external staff.

---

### ASM-002: External Contractors Account for Non-Payroll Workforce
- **Date Recorded:** 2026-11-16 (Day 1)
- **Status:** Active
- **Assumption:** External contractors or vendor staff (such as Patil Infra Services for IT on-call support, Cohere Recruiting Partners, or event agencies) exist outside Keka HRMS and are paid via vendor invoices in Zoho Books rather than standard payroll.
- **Source Line / Evidence:**
  - `Employee_Master.xlsx:Sheet:Employees:Row:1` ("contractors are not in Keka").
  - `GL_Export_Apr-Sep_2026.xlsx:Sheet:GL Apr-Sep:Row:25` (Patil Infra Services, JV-0902 for on-call support).
- **Confidence:** High
- **What Would Change Mind:** An HR memo stating Veloxa does not employ or contract third-party technical vendors.

---

### ASM-003: Board Updates are the Authoritative Financial Governance Source
- **Date Recorded:** 2026-11-16 (Day 1)
- **Status:** Active
- **Assumption:** Written quarterly Board Updates represent authoritative, vetted financial metrics (ARR ₹5.8 Cr growing to ₹6.1 Cr; monthly burn ₹44 L – ₹46 L), whereas verbal statements in T1/T2 transcripts represent unnormalized estimates, memory errors, or transcription noise.
- **Source Line / Evidence:**
  - `Board_Update_Apr-Jun_2026.pdf:page_1`
  - `Board_Update_Jul-Sep_2026.pdf:page_1`
  - `T1_CEO_Kickoff_Call.docx:Summary` ("audio quality: fair")
  - `T2_CFO_Call.docx:Summary` ("audio quality: poor (speakerphone)")
- **Confidence:** High
- **What Would Change Mind:** Formally audited annual accounts showing board updates were misstated.

---

### ASM-004: Rahul Verma February 2026 Payroll Overpayment
- **Date Recorded:** 2026-11-16 (Day 1)
- **Status:** Active
- **Assumption:** Backend engineer Rahul Verma was paid for 28 full days in February 2026 despite joining on 3 February 2026, because Karthik copied the January spreadsheet while Fatima was away on wedding leave. Rahul caught the error and queried it, but no recovery has been recorded.
- **Source Line / Evidence:**
  - `Employee_Master.xlsx:Sheet:Employees:Row:21` (Join date: 2026-02-03).
  - `Payroll_Register_Jan-Mar_2026.xlsx:Sheet:Payroll Q4:Row:38` (Feb-2026: Days in Month: 28, Days Payable: 28).
  - `01.eml` (Karthik: "Ran Feb payroll since Fatima is out. Used the Jan sheet and added the new joiner.").
  - `02.eml` (Rahul: "The amount looks higher than what I expected for a partial month.").
  - `03.eml` (Fatima: "Will check and get back.").
- **Confidence:** High
- **What Would Change Mind:** An HR/Finance adjustment voucher demonstrating an intentional joining bonus or written salary proration waiver.

---

### ASM-005: Atlas Routing Engine v3 Did Not Achieve GA on 15 September
- **Date Recorded:** 2026-11-16 (Day 1)
- **Status:** Active
- **Assumption:** The scheduled 15 September 2026 GA for Atlas v3 was missed due to unexpected reliability failures in August (which required emergency on-call vendor intervention). Atlas remains in hardening as of October 2026.
- **Source Line / Evidence:**
  - `Board_Update_Apr-Jun_2026.pdf:page_1` (Atlas on track for GA on 15 September).
  - `Board_Update_Jul-Sep_2026.pdf:page_1` (We moved GA to absorb unplanned reliability work after a difficult August; engine is feature-complete and in final hardening).
  - `GL_Export_Apr-Sep_2026.xlsx:Sheet:GL Apr-Sep:Row:25` (Patil Infra on-call support 18-31 Aug).
  - `T1_CEO_Kickoff_Call.docx:Summary` (Ananya doubts routing engine v3 will make customer festive window).
- **Confidence:** High
- **What Would Change Mind:** Customer release notes announcing production rollout prior to October 2026.

---

### ASM-006: Separation of Verified Facts from Simulated Agent Personas
- **Date Recorded:** 2026-11-16 (Day 1)
- **Status:** Active
- **Assumption:** Agent interviews must answer strictly from verified records when discussing company history, projects, and reporting structures. Any discussion of private thoughts, emotions, or weekend personal life must be marked as a simulated assumption and never asserted as a historical fact.
- **Source Line / Evidence:**
  - Candidate Brief: "Where the data is silent (their lives, their private thoughts), invent it and log it as an assumption."
- **Confidence:** High
- **What Would Change Mind:** Организаторы hackathon explicitly requiring blending fictional personal details with verified employment records.

---

### ASM-007: Priya Nair September Leaves Signal Acute Flight & Burnout Risk
- **Date Recorded:** 2026-11-17 (Day 2)
- **Status:** Active
- **Assumption:** Priya Nair's cluster of 5 PM half-days in September (Sep 3, 8, 15, 17, 24) followed the freeze of her supporting backend requisitions (REQ-014/REQ-015), representing active job interviewing or severe burnout rather than casual time off.
- **Source Line / Evidence:**
  - `Leave_Register.xlsx:Rows:16-20` (5 half-day PM leaves approved by Vikram).
  - `06.eml` (Meera freezes REQ-014 and REQ-015).
  - `T3_Head_of_People_Call.docx:Summary` (Deepa is deeply worried about an unnamed engineer).
- **Confidence:** High
- **What Would Change Mind:** Doctor certificates showing routine medical visits.

---

### ASM-008: Siddharth Mehta Resignation Triggered by Atlas Launch Indefinite Delay
- **Date Recorded:** 2026-11-17 (Day 2)
- **Status:** Active
- **Assumption:** Siddharth Mehta submitted his resignation on 15 September 2026 because the Atlas launch date slipped indefinitely, leaving his completed launch materials stranded.
- **Source Line / Evidence:**
  - `Resignation_Letter_SM.pdf:page_1` ("looking for a role with clearer launch timelines").
  - `Board_Update_Jul-Sep_2026.pdf:page_1` (GA moved from 15 September).
- **Confidence:** High
- **What Would Change Mind:** Stated alternate career reasons unrelated to product launches.

---

### ASM-009: Deepa Joshi's "About Twelve" Attrition Refers to Annualized Percentage
- **Date Recorded:** 2026-11-17 (Day 2)
- **Status:** Active
- **Assumption:** Deepa's spoken phrase "about twelve" in T3 refers to an annualized ~12% attrition rate, rather than 12 individuals departing, as Employee Master verifies only 1 employee has resigned.
- **Source Line / Evidence:**
  - `T3_Head_of_People_Call.docx:Summary` ("about twelve, which is normal for Bangalore").
  - `Employee_Master.xlsx:Rows:4-22` (19 active staff, 1 departure).
- **Confidence:** High
- **What Would Change Mind:** Discovery of 11 unrecorded contractor or employee departures.

---

### ASM-010: Marketing Team Will Report to Incoming Chief Revenue Officer (CRO)
- **Date Recorded:** 2026-11-18 (Day 3)
- **Status:** Active
- **Assumption:** Marketing reporting line (Nikhil Bose VX006, Aisha Khan VX011, and REQ-016 backfill) will transition from CEO/unassigned to incoming CRO within 1-2 months per CEO voice note T6b and T4 call.
- **Source Line / Evidence:**
  - `T6b_CEO_Voice_Note.docx:Transcript` ("marketing will report to the new CRO from next month").
  - `T4_Head_of_Marketing_Call.docx:Key_points` ("report into the new CRO, I hear").
- **Confidence:** High
- **What Would Change Mind:** CEO notification canceling the CRO executive search.

---

### ASM-011: Atlas v3 GA Slipped 3 Months to 15 December 2026
- **Date Recorded:** 2026-11-18 (Day 3)
- **Status:** Active
- **Assumption:** Vikram Menon's statement in T5 that v3 is "on track, maybe a couple of weeks of buffer needed" minimized a formal 3-month slip committed in Jira on 2 September 2026 moving Atlas GA to 15 December 2026.
- **Source Line / Evidence:**
  - `Jira_Export_ATLAS.xlsx:Sheet:Versions:Row:2` (Release Date: 2026-12-15, Changed By: vikram, Last Changed: 2026-09-02).
  - `T5_VP_Engineering_Call.docx:Summary`.
  - `08.eml` (Sneha pauses Atlas perf tickets).
- **Confidence:** High
- **What Would Change Mind:** An earlier production deployment before 15 December.

---

### ASM-012: "Snehal" in PagerDuty and On-Call Rota is Contractor S. Patil
- **Date Recorded:** 2026-11-18 (Day 3)
- **Status:** Active
- **Assumption:** Responder "Snehal" in PagerDuty incidents and On-Call Rota is S. Patil from Patil Infra Services (Baner Road, Pune), hired for ₹1,41,600/month retainer under invoice PIS-114 starting 18 August to relieve Sneha Kulkarni after 6 weeks solo on-call and 3 August SEV1 outages.
- **Source Line / Evidence:**
  - `Invoice_PIS-114.pdf:page_1`.
  - `OnCall_Rota.xlsx:Sheet:On-call:Rows:10-20`.
  - `08.eml` (Sneha: "The contractor starts on the rota this week.").
  - `T5_VP_Engineering_Call.docx` (Vikram conflates Sneha and Snehal).
- **Confidence:** High
- **What Would Change Mind:** A Keka employee record for Snehal.

---

### ASM-013: Priya Nair Resignation on 19 November 2026 Materializes Core Product SPOF
- **Date Recorded:** 2026-11-19 (Day 4)
- **Status:** Active
- **Assumption:** Priya Nair formally submitted her resignation on 19 November 2026 with a standard 60-day notice period ending ~18 January 2027 per T6d CEO Voice Note. This materializes the single-point-of-failure risk on Atlas routing engine v3.
- **Source Line / Evidence:**
  - `T6d_CEO_Voice_Note.docx:Transcript` ("Bad news, Pria resigned this morning. Notice period two months, I think.").
  - `Employee_Master.xlsx:Sheet:Employees:Row:10` (Notice Period: 60 days).
  - `git_log.csv` (588 commits by Priya).
- **Confidence:** High
- **What Would Change Mind:** A formal written retraction of resignation by Priya Nair.

---

### ASM-014: Employee Chat Surveillance Rejection as Unauthorized and Contradictory to HR Policy
- **Date Recorded:** 2026-11-19 (Day 4)
- **Status:** Active
- **Assumption:** Ananya's statement in T6c that "Deepa says it's fine" to read employee Slack messages is uncorroborated and directly contradicted by Deepa's written policy in 11.eml and Culture Amp anonymity thresholds. The Cockpit permanently bars employee chat surveillance.
- **Source Line / Evidence:**
  - `T6c_CEO_Voice_Note.docx:Transcript`.
  - `11.eml:body` ("The team is too small for me to share comments.").
  - `Pulse_Survey.xlsx` ("Not shown: team smaller than 6").
- **Confidence:** High
- **What Would Change Mind:** A ratified corporate electronic surveillance policy consented to by all employees.

---

### ASM-015: Atlas v3 GA 15 December Date Cannot Proceed Without Senior Routing Talent
- **Date Recorded:** 2026-11-19 (Day 4)
- **Status:** Active
- **Assumption:** Atlas v3 cannot achieve production GA on 15 December 2026. Priya's remaining 60-day notice must be 100% prioritized on architecture documentation and knowledge transfer, requiring a board schedule adjustment to Q1 2027.
- **Source Line / Evidence:**
  - `T6d_CEO_Voice_Note.docx:Transcript`.
  - `Jira_Export_ATLAS.xlsx:Assignee:PN`.
  - `06.eml` (Frozen backend requisitions REQ-014 and REQ-015).
- **Confidence:** High
- **What Would Change Mind:** Demonstration of an autonomous graph solver deployment by Rahul Verma or external contractor.

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

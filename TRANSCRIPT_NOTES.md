# 🎙️ Veloxa CXO Cockpit — Transcript Notes & Discrepancies

This document logs misheard terms, transcription acoustic anomalies, speaker biases, and cross-source contradictions identified in MeetNotes AI call summaries (T1 and T2).

---

## 1. Acoustic & Tool Transcription Errors

| Misheard Term in Transcript | Canonical Entity / Tool | Source File & Location | Evidence for Resolution | Conclusion & Action |
|---|---|---|---|---|
| **"one-eighty, give or take"** | 18 full-time employees | `T1_CEO_Kickoff_Call.docx:Summary` | `Employee_Master.xlsx:Sheet:Employees` contains 19 employees total (including CEO). Board reports state "Team 19". | Speech-to-text acoustic confusion between "eighteen" and "one-eighty". Normalized to 19 employee records. |
| **"Jeera"** | Atlassian Jira | `T1_CEO_Kickoff_Call.docx:Key points:Engineering` | Data room README lists "Jira (ATLAS)" under `engineering/`. | Misheard tool name. Resolved to Jira project tracker. |
| **"Cult Amp"** | Culture Amp | `T1_CEO_Kickoff_Call.docx:Key points:HR` | Data room README lists "Culture Amp pulse" under `hr/`. | Phonetic mishearing. Resolved to Culture Amp HR survey platform. |
| **"Hub sport"** | HubSpot | `T1_CEO_Kickoff_Call.docx:Action items` | Action item says "Send the hub sport export". Common CRM. | Phonetic mishearing. Resolved to HubSpot CRM. |
| **"Slag"** | Slack | `T1_CEO_Kickoff_Call.docx:Action items` | Action item says "Look into slag channel for engineering updates". | Phonetic mishearing. Resolved to Slack messaging channel. |
| **"Joho books"** | Zoho Books | `T2_CFO_Call.docx:Key points:Books` | Data room README lists "Zoho Books general ledger" under `finance/`. GL export is explicitly from Zoho Books. | Phonetic mishearing. Resolved to Zoho Books accounting system. |
| **"Kayka"** | Keka HRMS | `T2_CFO_Call.docx:Key points:Payroll` | Data room README lists "Keka HRMS" under `hr/`. | Phonetic mishearing. Resolved to Keka HRMS. |
| **"Pria"** | Priya Nair | `T1_CEO_Kickoff_Call.docx:Key points:Engineering` | `Employee_Master.xlsx:Row:10` lists "Priya Nair", Staff Engineer in Engineering. | Phonetic spelling in transcript. Resolved to Priya Nair (VX007). |
| **"Vicky"** | Vikram Menon | `T2_CFO_Call.docx:Action items` | `Employee_Master.xlsx:Row:7` lists "Vikram Menon", VP Engineering. Meera refers to checking freeze decision with him. | Informal nickname for Vikram Menon (VX004). |
| **"Kartik"** | Karthik Subramanian | `T2_CFO_Call.docx:Key points:Team` | `Employee_Master.xlsx:Row:13` lists "Karthik Subramanian", FP&A Manager in Finance. Email sender is "Karthik Subramanian". | Alternate phonetic spelling. Resolved to Karthik Subramanian (VX010). |
| **"Fatima Shaikh"** | Fatima Sheikh | `T2_CFO_Call.docx:Key points:Team` | `Employee_Master.xlsx:Row:17` lists "Fatima Sheikh", Accounts & Payroll Executive. | Alternate spelling in transcript. Resolved to Fatima Sheikh (VX014). |

---

## 2. Material Cross-Source Contradictions

### Contradiction 1: Total Company Headcount
- **Transcript Statement (T1):** Ananya states: *"roughly eighteen people ('one-eighty, give or take')"*.
- **Candidate Brief:** Describes Veloxa as *"a 180-person B2B SaaS company"*.
- **System Exports:**
  - `Employee_Master.xlsx` contains exactly 19 named employee rows (VX001 to VX019). The top note explicitly states: *"Keka HRMS export, employees only (contractors are not in Keka)"*.
  - `Board_Update_Apr-Jun_2026.pdf:page_1` reports Team size as 19.
  - `Board_Update_Jul-Sep_2026.pdf:page_1` reports Team size as 19.
- **Analysis:** The candidate brief's "180" is an external framing note that echoes the machine transcription mistake in T1. The transactional HR database and board reports agree on 19 full-time employees.
- **Cockpit Stance:** The cockpit reports `sources_disagree` when asked about total company size, explicitly explaining the 19 employee records in Keka vs. the 180 audio note.

---

### Contradiction 2: Annual Recurring Revenue (ARR) Scale
- **Transcript Statements:**
  - T1 (Ananya): *"around forty-two crore, maybe forty-five now"*.
  - T2 (Meera): ARR at start of year was *"forty-eight"*.
- **System Exports:**
  - `Board_Update_Apr-Jun_2026.pdf`: ARR (recurring) = **₹5.8 Cr** (June 2026).
  - `Board_Update_Jul-Sep_2026.pdf`: ARR (recurring) = **₹6.1 Cr** (September 2026).
- **Analysis:** Spoken claims of "42-45 crore" or "48" conflict by an ~8x multiple with the board presentations. This could be an acoustic artifact (e.g. 4.2 to 4.5 crore misheard as 42-45, or annualized GMV vs SaaS ARR).
- **Cockpit Stance:** Preserves the disagreement. Reports Board figures as official written governance records while citing the transcripts as conflicting claims.

---

### Contradiction 3: Monthly Burn Rate
- **Transcript Statements:**
  - T1 (Ananya): *"around two point two"* (no unit).
  - T2 (Meera): *"two point two lakhs a month, sometimes two point five"*.
- **System Exports:**
  - `Board_Update_Apr-Jun_2026.pdf`: Monthly burn = **₹46 L** (Runway 14 months).
  - `Board_Update_Jul-Sep_2026.pdf`: Monthly burn = **₹44 L** (Runway 13 months).
  - `GL_Export_Apr-Sep_2026.xlsx`: Monthly salary vouchers (`PAY-APR` to `PAY-AUG`) = **₹31,75,000**; monthly WeWork rent = **₹2,36,000**.
- **Analysis:** A total company burn of ₹2.2–2.5 Lakhs is mathematically impossible because payroll and office rent alone exceed ₹34 Lakhs per month. Meera was likely referring to non-payroll OPEX, cloud infrastructure, or speaking in distorted units.
- **Cockpit Stance:** Reports Board Updates of ₹44 L – ₹46 L as total burn, proven by General Ledger vouchers, while documenting Meera's statement as a known discrepancy.

---

### Contradiction 4: Atlas v3 GA Timeline
- **April-June Board Update:** Reports Atlas is on track for GA on **15 September 2026**.
- **T1 Kickoff:** Ananya worries routing engine v3 was promised by festive season and doubts it will make it.
- **July-September Board Update (Sent 6 Oct 2026):** Confirms GA was moved to absorb unplanned reliability work after a difficult August; engine is in final hardening.
- **Analysis:** The September GA was officially abandoned. The August incident is corroborated by the GL payment to Patil Infra for on-call support.
- **Cockpit Stance:** Reports that Atlas did not launch on 15 September and was in final hardening as of early October 2026.

---

### Contradiction 5: Marketing Spend Reconciliation
- **T2 CFO Call:** Meera states *"Nikhil's numbers never match mine"*.
- **GL Export:** Shows marketing events split between two vendor entities: `Sapphire Events Pvt Ltd` (₹5,42,800) and `Saphire Event Mgmt` (₹4,60,200), plus monthly Google Ads (₹76k–₹94k).
- **Analysis:** Marketing cost center numbers are fragmented across multiple vendor names and invoices, explaining the CFO's reporting frustration.

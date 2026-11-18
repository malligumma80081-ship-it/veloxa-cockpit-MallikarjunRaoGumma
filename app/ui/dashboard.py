"""Streamlit Dashboard for Veloxa CXO Cockpit."""
import streamlit as st
from app.cockpit.answer import CockpitQA
from app.cockpit.risk import RiskEngine
from app.agents.interview import AgentInterview
from app.evidence.repository import EvidenceRepository

st.set_page_config(
    page_title="Veloxa CXO Cockpit",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 Veloxa Technologies — CXO Cockpit")
st.caption("Evidence-grounded executive decision cockpit | Hackathon Release: Day 2 (17 Nov 2026)")

# Sidebar for point-in-time date selector and system status
st.sidebar.header("⚙️ Configuration & Timeline")
as_of_date = st.sidebar.selectbox(
    "Point-in-Time As-Of Date",
    options=["2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20"],
    index=1,  # Default to Day 2 (17 Nov 2026)
    help="Historical cutoff: Only evidence released on or before this date will be retrieved.",
)

repo = EvidenceRepository()
qa_engine = CockpitQA(repo)
risk_engine = RiskEngine(repo)
agent_interview = AgentInterview(repo)

# --- T6A RESPONSE: AUTOMATIC TOP 3 MORNING WORRY LIST ---
st.markdown("### 🌅 Good Morning, Ananya — Top 3 Things to Worry About Today")
st.caption("Auto-generated executive briefing (responding to Voice Note T6a). Ranked deterministically by severity, likelihood, and verified evidence.")

top_3_risks = risk_engine.get_top_3_risks(as_of_date=as_of_date)
cols = st.columns(3)
for idx, (col, r) in enumerate(zip(cols, top_3_risks)):
    with col:
        with st.container(border=True):
            st.markdown(f"#### #{idx+1} {r.risk_title}")
            st.markdown(f"**Severity:** `{r.severity.upper()}` | **Score:** `{r.rank_score:.1f}`")
            st.markdown(f"**Impact:** {r.potential_impact}")
            st.markdown(f"**Next Check:** {r.mitigation_or_next_check}")
            st.caption(f"Locators: {', '.join(r.locators[:2])}")

st.markdown("---")

tab_qa, tab_risks, tab_agents, tab_evidence, tab_conflicts = st.tabs([
    "💬 Ask the Cockpit",
    "⚠️ Full Worry List",
    "👥 People & Agent Interview",
    "📄 Evidence Browser",
    "⚖️ Conflicts & Decisions",
])

# TAB 1: ASK THE COCKPIT
with tab_qa:
    st.subheader("Executive Question Answering")
    st.write("Ask any question regarding Veloxa's team, finance, engineering, or operations:")

    quick_questions = [
        "Why did Siddharth Mehta resign?",
        "Why did engineering pulse score drop to 3.1?",
        "Why did Priya take 5 half-days in September?",
        "What happened to the open backend engineering requisitions?",
        "What is our attrition rate according to Deepa?",
        "When is Atlas v3 launching?",
        "How many employees work at Veloxa?",
        "What is our ARR?",
        "What is our monthly burn rate?",
        "What was our total monthly payroll expense?",
        "What was the issue with Rahul Verma's payslip?",
        "What is Priya's salary?",
    ]

    selected_quick = st.selectbox("Quick prompt suggestions:", [""] + quick_questions)
    user_q = st.text_input("Enter your question:", value=selected_quick)

    if st.button("Submit Question", type="primary"):
        if user_q:
            with st.spinner("Analyzing verified evidence..."):
                resp = qa_engine.ask(user_q, as_of_date=as_of_date)

                status_colors = {
                    "supported": "🟢 Supported",
                    "sources_disagree": "🟠 Sources Disagree",
                    "insufficient_evidence": "⚪ Insufficient Evidence",
                    "restricted": "🔴 Restricted (Privacy Policy)",
                    "not_available_as_of_date": "🟣 Not Available as of Date",
                }
                st.markdown(f"**Status:** `{status_colors.get(resp.status, resp.status)}` | **Confidence:** `{resp.confidence.upper()}` | **Effective Date:** `{resp.as_of_date}`")

                st.info(resp.answer)

                if resp.evidence:
                    st.markdown("#### 📑 Supporting Citations")
                    for cit in resp.evidence:
                        st.markdown(f"- **[{cit.evidence_id}]** `{cit.source}` (`{cit.locator}`): {cit.claim_snippet or ''}")

                if resp.conflicts:
                    st.markdown("#### ⚖️ Conflicting Evidence")
                    for c in resp.conflicts:
                        st.warning(f"**Topic:** {c.get('topic')}\n\n**Competing Claims:**\n" + "\n".join(f"- {claim}" for claim in c.get('competing_claims', [])))

                if resp.limitations:
                    st.markdown("#### ℹ️ Caveats & Scope Limitations")
                    for lim in resp.limitations:
                        st.caption(f"• {lim}")

# TAB 2: WHAT SHOULD I WORRY ABOUT?
with tab_risks:
    st.subheader("⚠️ Executive Worry List — Evidence-Ranked Risks")
    st.write("Deterministic, evidence-grounded risk items ranked by severity, likelihood, and supporting proof:")

    risks = risk_engine.get_ranked_risks(as_of_date=as_of_date)
    for r in risks:
        with st.expander(f"#{r.rank_score:.1f} | [{r.category.upper()}] {r.risk_title} ({r.severity.upper()} Severity)", expanded=(r.rank_score >= 8.9)):
            st.markdown(f"**Description:** {r.description}")
            st.markdown(f"**Potential Impact:** {r.potential_impact}")
            st.markdown(f"**Mitigation / Next Check:** {r.mitigation_or_next_check}")
            st.markdown(f"**Evidence Locators:** `{', '.join(r.locators)}`")
            st.caption(f"Rank Explanation: {r.rank_explanation}")

# TAB 3: PEOPLE & AGENTS
with tab_agents:
    st.subheader("👥 Interview the 14 Team Members")
    st.caption("Grounded in Keka HRMS, call transcripts, and internal emails. Distinct boundary between verified records and simulated personas.")

    agents = agent_interview.list_available_agents()
    agent_options = {f"{a.canonical_name} ({a.title} - {a.department})": a.employee_id for a in agents}
    selected_agent_label = st.selectbox("Select a colleague to interview:", list(agent_options.keys()))
    selected_agent_id = agent_options[selected_agent_label]

    agent_profile = agent_interview.get_agent_profile(selected_agent_id)
    if agent_profile:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("#### Verified HR Record")
            st.markdown(f"**ID:** `{agent_profile.employee_id}`")
            st.markdown(f"**Title:** {agent_profile.title}")
            st.markdown(f"**Department:** {agent_profile.department}")
            st.markdown(f"**Location:** {agent_profile.location}")
            st.markdown(f"**Joined:** {agent_profile.join_date}")
            st.markdown(f"**Status:** {agent_profile.status}")
        with col2:
            st.markdown("#### Conduct Interview")
            interview_prompt = st.text_input(f"Ask {agent_profile.canonical_name} a question:", "What are you working on and what are your priorities?")
            if st.button("Ask Colleague"):
                with st.spinner("Connecting to colleague persona..."):
                    res = agent_interview.interview(selected_agent_id, interview_prompt, as_of_date=as_of_date)
                    st.write(res["response"])
                    if res.get("simulated_assumptions"):
                        st.warning("⚠️ " + "; ".join(res["simulated_assumptions"]))

# TAB 4: EVIDENCE BROWSER
with tab_evidence:
    st.subheader("📄 Verified Evidence Index")
    st.write("Atomic claims extracted from data room exports:")
    ev_list = repo.get_evidence_point_in_time(as_of_date=as_of_date, exclude_restricted=True)
    table_data = [
        {
            "Ref": e.evidence_id,
            "Source File": e.source_file,
            "Locator": e.locator,
            "Claim": e.claim,
            "Release Date": e.release_date,
            "Confidence": e.confidence.upper(),
        }
        for e in ev_list
    ]
    st.dataframe(table_data, use_container_width=True)

# TAB 5: CONFLICTS & DECISIONS
with tab_conflicts:
    st.subheader("⚖️ Disagreements & Candidate Reconciliation Decisions")
    st.write("Structured audit log of conflicting source claims and human reconciliation decisions:")
    conflicts = repo.get_conflicts()
    decisions = {d.conflict_id: d for d in repo.get_decisions()}

    for c in conflicts:
        d = decisions.get(c.conflict_id)
        with st.expander(f"Conflict: {c.topic} [{c.status.upper()}]"):
            st.markdown("**Competing Source Claims:**")
            for cl in c.competing_claims:
                st.markdown(f"- {cl}")
            if d:
                st.markdown(f"**Candidate Interpretation:** {d.chosen_interpretation}")
                st.markdown(f"**Reasoning:** {d.reasoning}")
                st.markdown(f"**Confidence:** `{d.confidence.upper()}` | **Date:** `{d.decision_date}`")
                st.markdown(f"**What Would Change Mind:** {d.what_would_change_mind}")

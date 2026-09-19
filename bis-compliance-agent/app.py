import os
import sys
import json
import streamlit as st

# Add current folder to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.compliance_graph import ComplianceWorkflow, MAX_QUESTIONS
from models.schemas import RecommendationResult

# Page Config
st.set_page_config(
    page_title="BIS Product Compliance Advisor Agent",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Modern Dark Glassmorphism aesthetic)
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF9933 0%, #FFFFFF 50%, #128807 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #8892B0;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .agent-card {
        background: #1E222D;
        border: 1px solid #2E3440;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 10px;
    }
    .badge-high {
        background-color: #059669;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-medium {
        background-color: #D97706;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-low {
        background-color: #DC2626;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .why-card {
        background-color: #111827;
        border-left: 4px solid #10B981;
        padding: 12px 16px;
        border-radius: 4px;
        margin-top: 10px;
    }
    .why-not-card {
        background-color: #18181B;
        border-left: 4px solid #EF4444;
        padding: 10px 14px;
        border-radius: 4px;
        margin-top: 8px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Workflow in Session State
@st.cache_resource
def get_workflow():
    return ComplianceWorkflow()

workflow = get_workflow()

if "state" not in st.session_state:
    st.session_state.state = None

if "input_text" not in st.session_state:
    st.session_state.input_text = ""


# Header
st.markdown('<div class="main-header">🇮🇳 BIS Product Compliance Advisor Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Preliminary Bureau of Indian Standards (BIS) Classification & Regulatory Matching</div>', unsafe_allow_html=True)

# Sidebar: Config & Info
with st.sidebar:
    st.header("⚙️ Agent Settings")
    api_key_input = st.text_input("LLM API Key (Optional)", type="password", help="Enter OpenAI or Gemini API key. If left blank, agent uses local heuristic fallback engine.")
    if api_key_input:
        os.environ["LLM_API_KEY"] = api_key_input

    st.markdown("---")
    st.header("🎯 Preset Demo Scenarios")
    
    if st.button("🧸 Scenario 1: Toys", use_container_width=True):
        st.session_state.input_text = "I manufacture plastic puzzles for children."
        st.session_state.state = workflow.create_initial_state(st.session_state.input_text)
        st.session_state.state = workflow.step(st.session_state.state)
        st.rerun()

    if st.button("⚡ Scenario 2: Electronics", use_container_width=True):
        st.session_state.input_text = "I manufacture an electronic appliance for home use."
        st.session_state.state = workflow.create_initial_state(st.session_state.input_text)
        st.session_state.state = workflow.step(st.session_state.state)
        st.rerun()

    if st.button("👕 Scenario 3: Textiles", use_container_width=True):
        st.session_state.input_text = "I manufacture cotton garments."
        st.session_state.state = workflow.create_initial_state(st.session_state.input_text)
        st.session_state.state = workflow.step(st.session_state.state)
        st.rerun()

    if st.button("🍱 Scenario 4: Food Packaging", use_container_width=True):
        st.session_state.input_text = "I manufacture plastic containers used for food."
        st.session_state.state = workflow.create_initial_state(st.session_state.input_text)
        st.session_state.state = workflow.step(st.session_state.state)
        st.rerun()

    if st.button("❓ Scenario 5: Vague Input", use_container_width=True):
        st.session_state.input_text = "I make a product."
        st.session_state.state = workflow.create_initial_state(st.session_state.input_text)
        st.session_state.state = workflow.step(st.session_state.state)
        st.rerun()

    st.markdown("---")
    st.caption("Hackathon MVP • Powered by LangGraph & Pydantic")


# Main Input Area
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.subheader("1. Describe Your Product")
    product_desc = st.text_area(
        "What product do you manufacture in India?",
        value=st.session_state.input_text,
        placeholder="e.g. I manufacture plastic puzzles for children, or LED light bulbs, or cotton surgical face masks...",
        height=100
    )

    if st.button("🚀 Start Compliance Assessment", type="primary", use_container_width=True):
        if not product_desc.strip():
            st.warning("Please enter a product description first.")
        else:
            st.session_state.input_text = product_desc
            st.session_state.state = workflow.create_initial_state(product_desc)
            st.session_state.state = workflow.step(st.session_state.state)
            st.rerun()

    state = st.session_state.state

    # Clarification Section
    if state and state.get("current_question"):
        st.markdown("---")
        st.subheader("❓ Clarification Required")
        st.info(f"**Agent Question ({state.get('clarification_count', 0) + 1}/{MAX_QUESTIONS}):**\n\n{state['current_question']}")

        user_ans = st.text_input("Your Answer:", key="clarification_answer_input", placeholder="Type your response here...")
        
        col_ans1, col_ans2 = st.columns([1, 1])
        with col_ans1:
            if st.button("Submit Answer ➔", type="primary", use_container_width=True):
                if user_ans.strip():
                    st.session_state.state = workflow.answer_question(state, user_ans)
                    st.rerun()
                else:
                    st.warning("Please enter an answer or skip.")
        with col_ans2:
            if st.button("Skip Question", use_container_width=True):
                st.session_state.state = workflow.answer_question(state, "Not specified")
                st.rerun()

with col_right:
    st.subheader("🤖 Agent Activity Log")
    if not state:
        st.info("Start an assessment to view live agent orchestrations.")
    else:
        logs = state.get("agent_logs", [])
        for log in logs:
            status_icon = "✓" if log["status"] == "completed" else "ℹ️" if log["status"] == "info" else "⟳"
            st.markdown(f"""
            <div class="agent-card">
                <span style="color:#60A5FA; font-weight:bold;">[{log['timestamp']}] {status_icon} {log['agent_name']}</span><br/>
                <span style="color:#D1D5DB; font-size:0.9rem;">{log['message']}</span>
            </div>
            """, unsafe_allow_html=True)


# Results Display Area
if state and not state.get("current_question"):
    st.markdown("---")
    st.header("📋 Product Compliance Profile & Recommendations")

    # Profile Metrics Cards
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Category", state.get("category", "General"))
    p2.metric("Subcategory", state.get("subcategory", "Unspecified"))
    p3.metric("Material", state.get("material", "Unspecified"))
    electric_val = state.get("electric")
    p4.metric("Power Type", "Electric" if electric_val is True else "Non-Electric" if electric_val is False else "Unknown")

    st.markdown("---")

    # Recommendation Results
    rec_dict = state.get("recommended_standards")
    if rec_dict:
        rec = RecommendationResult(**rec_dict)
        primary = rec.primary_standard

        col_rec1, col_rec2 = st.columns([1.2, 0.8])

        with col_rec1:
            st.subheader("🌟 Primary Recommended Standard")
            if primary:
                strength_color = "badge-high" if rec.match_strength == "High" else "badge-medium" if rec.match_strength == "Medium" else "badge-low"
                
                st.markdown(f"""
                <div style="background:#1E293B; padding:20px; border-radius:12px; border:1px solid #334155;">
                    <div style="display:flex; justify-between; align-items:center;">
                        <h3 style="margin:0; color:#38BDF8;">{primary.standard_code}</h3>
                        <span class="{strength_color}">Match: {rec.match_strength}</span>
                    </div>
                    <h4 style="color:#F3F4F6; margin-top:8px;">{primary.title}</h4>
                    <p style="color:#9CA3AF; font-size:0.95rem;">{primary.description}</p>
                    <a href="{primary.source_url}" target="_blank" style="color:#60A5FA; text-decoration:none; font-weight:600;">🔗 View Official BIS Source ➔</a>
                </div>
                """, unsafe_allow_html=True)

                st.markdown('<div class="why-card">', unsafe_allow_html=True)
                st.markdown("#### 💡 Why This Standard?")
                st.write(rec.reason)
                for ev in rec.evidence:
                    st.write(f"- {ev}")
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.warning("No suitable standard matched in the dataset.")

        with col_rec2:
            st.subheader("🔍 Why Not Selected? (Excluded Candidates)")
            if rec.excluded_candidates:
                for excl in rec.excluded_candidates:
                    with st.expander(f"❌ {excl['standard_code']} — {excl['title']}"):
                        st.markdown(f"**Exclusion Reason:** {excl['reason']}")
            else:
                st.info("No candidate standards were explicitly excluded.")

            if rec.additional_standards:
                st.subheader("📚 Additional Relevant Standards")
                for add in rec.additional_standards:
                    st.markdown(f"- **[{add.standard_code}]({add.source_url})**: {add.title}")

    # Full Compliance Report Tab / Accordion
    st.markdown("---")
    st.subheader("📄 Generated BIS Compliance Report")
    
    report_text = state.get("final_report", "")
    st.markdown(report_text)

    st.download_button(
        label="📥 Download Compliance Report (Markdown)",
        data=report_text,
        file_name=f"BIS_Compliance_Report_{state.get('category','Product')}.md",
        mime="text/markdown",
        use_container_width=True
    )

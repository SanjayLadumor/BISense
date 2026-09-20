import os
import sys
import json
import streamlit as st

# Add current folder to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.compliance_graph import ComplianceWorkflow, MAX_QUESTIONS
from models.schemas import RecommendationResult

# Page Config - Forces sidebar collapsed by default
st.set_page_config(
    page_title="BISense AI | BIS Product Compliance Advisor Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS Theme System: Periwinkle Background & Light Lilac Theme with Rubik & Soria Fonts
st.markdown("""
<style>
    @import url('https://fonts.cdnfonts.com/css/soria');
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Rubik:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

    /* 1. COMPLETELY HIDE STREAMLIT TOP NAV BAR & SIDEBAR */
    header[data-testid="stHeader"], [data-testid="stHeader"], div[data-testid="stToolbar"] {
        display: none !important;
        height: 0px !important;
    }
    [data-testid="stSidebar"], section[data-testid="stSidebar"] {
        display: none !important;
        width: 0px !important;
    }
    #MainMenu, footer {
        visibility: hidden !important;
        display: none !important;
    }

    /* Page container spacing */
    .main .block-container {
        max-width: 1350px;
        padding-top: 1.0rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* 2. GLOBAL TYPOGRAPHY & PERIWINKLE BACKGROUND */
    html, body, .stMarkdown, p, div, label, input, textarea, button {
        font-family: 'Rubik', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    h1, h2, h3, h4, .main-header, .soria-heading {
        font-family: 'Soria', 'Playfair Display', Georgia, serif !important;
    }

    /* Soft Periwinkle Backdrop */
    .stApp, .main, body {
        background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 45%, #C7D2FE 100%) !important;
        background-attachment: fixed !important;
        color: #1E1B4B !important;
    }

    /* 3. HEADER & AGENT BRANDING */
    .agent-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 0.2rem;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        background: linear-gradient(135deg, #5B21B6 0%, #7E22CE 40%, #A855F7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        color: #4338CA;
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 1.2rem;
        font-family: 'Rubik', sans-serif !important;
    }

    /* Pulsating Light Lilac Status Badge */
    @keyframes pulse-lilac {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(192, 132, 252, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(192, 132, 252, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(192, 132, 252, 0); }
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        background: #F3E8FF;
        border: 2px solid #C084FC;
        color: #5B21B6;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.88rem;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(168, 85, 247, 0.15);
    }
    .status-dot {
        width: 10px;
        height: 10px;
        background-color: #A855F7;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        animation: pulse-lilac 2s infinite;
    }

    /* 4. EXPANDABLE SETTINGS BAR - FIXES BLACK BACKGROUND & DARK PURPLE TEXT */
    details[data-testid="stExpander"], [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 2px solid #C084FC !important;
        border-radius: 14px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.12) !important;
        overflow: hidden !important;
    }

    details[data-testid="stExpander"] summary, [data-testid="stExpander"] summary {
        background: #F3E8FF !important; /* Soft light lilac header */
        color: #5B21B6 !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 12px 18px !important;
        border-bottom: 2px solid #E9D5FF !important;
    }

    details[data-testid="stExpander"][open] summary, [data-testid="stExpander"][open] summary {
        background: #E9D5FF !important; /* Richer light lilac when open */
        color: #5B21B6 !important;
        border-bottom: 2px solid #C084FC !important;
    }

    details[data-testid="stExpander"] summary:hover, [data-testid="stExpander"] summary:hover {
        background: #E9D5FF !important;
        color: #4C1D95 !important;
    }

    details[data-testid="stExpander"] summary *, [data-testid="stExpander"] summary * {
        color: #5B21B6 !important;
        font-weight: 700 !important;
    }

    /* Expander Details Container */
    details[data-testid="stExpander"] [data-testid="stExpanderDetails"], [data-testid="stExpanderDetails"] {
        background: #FFFFFF !important;
        color: #1E1B4B !important;
        padding: 18px !important;
    }

    [data-testid="stExpanderDetails"] p, [data-testid="stExpanderDetails"] span {
        color: #1E1B4B !important;
        font-family: 'Rubik', sans-serif !important;
    }

    [data-testid="stExpanderDetails"] label {
        color: #5B21B6 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        margin-bottom: 6px !important;
    }

    /* 5. PRESET CONTAINER BAR */
    .preset-container {
        background: rgba(255, 255, 255, 0.92);
        border: 2px solid #C084FC;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 1.8rem;
        box-shadow: 0 8px 24px rgba(168, 85, 247, 0.1);
        backdrop-filter: blur(10px);
    }
    .preset-title {
        color: #5B21B6;
        font-size: 0.92rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 10px;
        font-family: 'Soria', 'Playfair Display', serif !important;
    }

    /* 6. GLASSMORPHISM PANELS & CARDS */
    .glass-panel {
        background: rgba(255, 255, 255, 0.94);
        border: 2px solid #C084FC;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 16px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.08);
        color: #1E1B4B;
    }

    /* Agent Timeline Log Cards */
    .agent-log-card {
        background: #F3E8FF;
        border-left: 4px solid #A855F7;
        border-top: 1px solid #E9D5FF;
        border-right: 1px solid #E9D5FF;
        border-bottom: 1px solid #E9D5FF;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(168, 85, 247, 0.06);
    }
    .agent-log-time {
        color: #5B21B6;
        font-weight: 800;
        font-size: 0.82rem;
        font-family: monospace !important;
    }
    .agent-log-name {
        color: #9333EA;
        font-weight: 700;
        font-size: 0.9rem;
        margin-left: 6px;
        font-family: 'Rubik', sans-serif !important;
    }

    /* Match Score Badges (Lighter Lilac Violet) */
    .badge-high {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        font-family: 'Rubik', sans-serif !important;
    }
    .badge-medium {
        background: linear-gradient(135deg, #C084FC 0%, #A855F7 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        font-family: 'Rubik', sans-serif !important;
    }
    .badge-low {
        background: linear-gradient(135deg, #7E22CE 0%, #6B21A8 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        font-family: 'Rubik', sans-serif !important;
    }

    /* Metric Card Custom Container */
    .metric-card {
        background: #FFFFFF;
        border-top: 4px solid #A855F7;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border-left: 1px solid #E0E7FF;
        border-right: 1px solid #E0E7FF;
        border-bottom: 1px solid #E0E7FF;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.08);
    }
    .metric-label {
        color: #4338CA;
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
        font-family: 'Rubik', sans-serif !important;
    }
    .metric-value {
        color: #7E22CE;
        font-size: 1.25rem;
        font-weight: 800;
        font-family: 'Soria', 'Playfair Display', serif !important;
    }

    /* Primary Recommended Standard Box - Bright Medium-Light Lilac Gradient */
    .recommended-box {
        background: linear-gradient(135deg, #6B21A8 0%, #8B5CF6 50%, #A855F7 100%);
        color: #FFFFFF !important;
        border: 2px solid #E9D5FF;
        padding: 26px;
        border-radius: 16px;
        margin-bottom: 16px;
        box-shadow: 0 12px 35px rgba(139, 92, 246, 0.25);
    }

    .why-card {
        background: #FFFFFF;
        border-left: 5px solid #A855F7;
        border-top: 1px solid #E9D5FF;
        border-right: 1px solid #E9D5FF;
        border-bottom: 1px solid #E9D5FF;
        padding: 18px 22px;
        border-radius: 10px;
        margin-top: 14px;
        color: #1E1B4B;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.06);
    }

    /* 7. LIGHTER LILAC PURPLE BUTTONS */
    .stButton > button {
        background: linear-gradient(135deg, #C084FC 0%, #A855F7 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Rubik', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 8px 18px !important;
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.28) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(168, 85, 247, 0.45) !important;
        color: #FFFFFF !important;
    }

    /* Form Labels & Widget Labels */
    /* Form Labels & Widget Labels */
    label, label p, label[data-testid="stWidgetLabel"], label[data-testid="stWidgetLabel"] p, .stTextArea label, .stTextInput label, .stSelectbox label {
        color: #1E1B4B !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
        font-family: 'Rubik', sans-serif !important;
        margin-bottom: 6px !important;
    }

    /* HIGH CONTRAST INPUT TEXT, SELECTBOX & PLACEHOLDERS */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #1E1B4B !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: 2px solid #A855F7 !important;
        border-radius: 10px !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder, div[data-baseweb="input"] input::placeholder, div[data-baseweb="textarea"] textarea::placeholder {
        color: #4C1D95 !important;
        opacity: 0.85 !important;
        font-weight: 600 !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus, div[data-baseweb="select"] > div:focus {
        border-color: #9333EA !important;
        box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.25) !important;
    }

    /* STREAMLIT ALERT & NOTIFICATION HIGH CONTRAST STYLING */
    div[data-testid="stAlert"], .stAlert, div[role="alert"] {
        background-color: #FEF3C7 !important; /* Soft warm amber for warnings */
        border: 2px solid #F59E0B !important;
        border-radius: 12px !important;
        color: #78350F !important; /* Deep dark amber text */
        font-weight: 700 !important;
    }
    div[data-testid="stAlert"] p, .stAlert p, div[role="alert"] p, div[data-testid="stAlert"] div, .stAlert div {
        color: #78350F !important;
        font-weight: 700 !important;
        font-size: 0.98rem !important;
    }

    /* 8. MOBILE RESPONSIVENESS & ADAPTIVE LAYOUTS */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 0.5rem !important;
        }
        .main-header {
            font-size: 1.8rem !important;
        }
        .sub-header {
            font-size: 0.9rem !important;
        }
        .agent-brand {
            flex-wrap: wrap !important;
        }
        .status-badge {
            font-size: 0.75rem !important;
            padding: 4px 10px !important;
        }
        .preset-container {
            padding: 12px 14px !important;
        }
        .recommended-box {
            padding: 18px !important;
        }
        .recommended-box h2 {
            font-size: 1.35rem !important;
        }
        .recommended-box h4 {
            font-size: 1rem !important;
        }
        .stButton > button {
            width: 100% !important;
            margin-bottom: 6px !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# Initialize Workflow in Session State
def get_workflow():
    if "workflow_instance" not in st.session_state or st.session_state.workflow_instance is None:
        st.session_state.workflow_instance = ComplianceWorkflow()
    return st.session_state.workflow_instance

workflow = get_workflow()

if "state" not in st.session_state:
    st.session_state.state = None

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

if "selected_category" not in st.session_state:
    st.session_state.selected_category = "Auto-Detect"

if "product_desc_textarea" not in st.session_state:
    st.session_state.product_desc_textarea = ""


# Top Header & Agent Status Bar
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
    <div>
        <div class="agent-brand">
            <span style="font-size:2.4rem;">🤖</span>
            <span class="main-header">BISense AI Agent</span>
        </div>
        <div class="sub-header">Autonomous Bureau of Indian Standards (BIS) Product Compliance & Regulatory Engine</div>
    </div>
    <div>
        <div class="status-badge">
            <span class="status-dot"></span>
            Agent Online & Ready
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# Collapsible Agent Settings & Top Controls
with st.expander("⚙️ Agent Settings & API Key Configuration", expanded=False):
    st.markdown("""
    Configure the backend execution model for the BISense Agent. If an API key is provided, the agent utilizes advanced LLM reasoning. If left empty, the agent operates on the local rule-based heuristic dataset engine.
    """)
    api_key_input = st.text_input(
        "LLM API Key (OpenAI / Gemini)",
        type="password",
        placeholder="Enter API Key...",
        help="Optional: Enables deep generative reasoning for complex non-standard product descriptions."
    )
    if api_key_input:
        os.environ["LLM_API_KEY"] = api_key_input
        st.success("API Key applied to runtime environment.")


# Define Streamlit Callbacks (Ensures session_state widget keys are modified before widget instantiation)
def run_preset_cb(text: str, category: str):
    wf = get_workflow()
    st.session_state.input_text = text
    st.session_state["product_desc_textarea"] = text
    st.session_state.selected_category = category
    st.session_state.state = wf.create_initial_state(text, category=category)
    st.session_state.state = wf.step(st.session_state.state)


def reset_agent_cb():
    st.session_state.input_text = ""
    st.session_state["product_desc_textarea"] = ""
    if "clarification_answer_input" in st.session_state:
        st.session_state["clarification_answer_input"] = ""
    st.session_state.selected_category = "Auto-Detect"
    st.session_state.state = None


def submit_answer_cb():
    ans = st.session_state.get("clarification_answer_input", "")
    curr_state = st.session_state.get("state")
    if ans and ans.strip() and curr_state:
        wf = get_workflow()
        st.session_state.state = wf.answer_question(curr_state, ans)
        st.session_state["clarification_answer_input"] = ""


def skip_answer_cb():
    curr_state = st.session_state.get("state")
    if curr_state:
        wf = get_workflow()
        st.session_state.state = wf.answer_question(curr_state, "Not specified")
        st.session_state["clarification_answer_input"] = ""


def run_agent_cb():
    desc = st.session_state.get("product_desc_textarea", "")
    if desc and desc.strip():
        sel_cat = st.session_state.get("selected_category", "Auto-Detect")
        chosen_cat = sel_cat if sel_cat != "Auto-Detect" else "General"
        st.session_state.input_text = desc
        wf = get_workflow()
        st.session_state.state = wf.create_initial_state(desc, category=chosen_cat)
        st.session_state.state = wf.step(st.session_state.state)


# Quick Preset Scenarios Bar
st.markdown('<div class="preset-container">', unsafe_allow_html=True)
st.markdown('<div class="preset-title">🎯 Preset Product Evaluation Scenarios</div>', unsafe_allow_html=True)

sc_col1, sc_col2, sc_col3, sc_col4, sc_col5 = st.columns(5)

with sc_col1:
    st.button("🧸 Scenario 1: Toys", on_click=run_preset_cb, args=("I manufacture plastic puzzles for children.", "Toys"), use_container_width=True)

with sc_col2:
    st.button("⚡ Scenario 2: Electronics", on_click=run_preset_cb, args=("I manufacture an electronic appliance for home use.", "Electronics"), use_container_width=True)

with sc_col3:
    st.button("👕 Scenario 3: Textiles", on_click=run_preset_cb, args=("I manufacture cotton garments.", "Textiles"), use_container_width=True)

with sc_col4:
    st.button("🍱 Scenario 4: Food Packaging", on_click=run_preset_cb, args=("I manufacture plastic containers used for food.", "Food Packaging"), use_container_width=True)

with sc_col5:
    st.button("❓ Scenario 5: Vague Input", on_click=run_preset_cb, args=("I make a product.", "General"), use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)


# Main Interactive Body: Split Layout (Product Input & Agent Clarifications vs Agent Execution Feed)
col_left, col_right = st.columns([1.1, 0.9], gap="medium")

with col_left:
    st.markdown("""
    <h3 style="font-size: 1.4rem; color: #5B21B6; margin-bottom: 8px;">
        1. Product Information Input
    </h3>
    """, unsafe_allow_html=True)

    cat_options = ["Auto-Detect", "Toys", "Electronics", "Textiles", "Food Packaging", "General"]
    current_cat_idx = cat_options.index(st.session_state.get("selected_category", "Auto-Detect")) if st.session_state.get("selected_category") in cat_options else 0
    selected_cat = st.selectbox(
        "Select Product Sector / Category:",
        options=cat_options,
        index=current_cat_idx,
        key="category_selectbox_widget",
        help="Specify the target industry category or allow automatic classification."
    )
    st.session_state.selected_category = selected_cat
    
    product_desc = st.text_area(
        "Describe your manufactured product in detail:",
        placeholder="e.g., I manufacture plastic puzzles for children under 3 years old, or LED lighting apparatus, or surgical face masks...",
        height=110,
        key="product_desc_textarea"
    )

    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        st.button("🚀 Run Agent Compliance Assessment", type="primary", on_click=run_agent_cb, use_container_width=True)
    with col_btn2:
        st.button("🔄 Reset Agent", on_click=reset_agent_cb, use_container_width=True)

    state = st.session_state.state

    # Clarification Section Card
    if state and state.get("current_question"):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: #F3E8FF; border: 2px solid #A855F7; border-radius: 14px; padding: 20px; box-shadow: 0 8px 24px rgba(168, 85, 247, 0.12);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span class="soria-heading" style="color: #5B21B6; font-weight: 700; font-size: 1.2rem;">❓ Agent Clarification Request</span>
                <span style="background: #A855F7; color: #FFFFFF; padding: 4px 12px; border-radius: 14px; font-size: 0.8rem; font-weight: 700;">Question {state.get('clarification_count', 0) + 1} of {MAX_QUESTIONS}</span>
            </div>
            <div style="color: #1E1B4B; font-size: 1rem; margin-bottom: 14px; background: #FFFFFF; padding: 14px; border-radius: 10px; border: 1px solid #E9D5FF; font-family: 'Rubik', sans-serif;">
                {state['current_question']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        user_ans = st.text_input("Your Answer:", key="clarification_answer_input", placeholder="Type your response to assist the agent...")
        
        col_ans1, col_ans2 = st.columns([1.2, 0.8])
        with col_ans1:
            st.button("Submit Answer to Agent ➔", type="primary", on_click=submit_answer_cb, use_container_width=True)
        with col_ans2:
            st.button("Skip Question", on_click=skip_answer_cb, use_container_width=True)


with col_right:
    st.markdown("""
    <h3 style="font-size: 1.4rem; color: #5B21B6; margin-bottom: 8px;">
        🤖 Agent Execution & Thought Feed
    </h3>
    """, unsafe_allow_html=True)

    if not state:
        st.markdown("""
        <div class="glass-panel" style="text-align: center; color: #4338CA; padding: 35px 20px;">
            <span style="font-size: 2.2rem;">🧠</span><br>
            <div style="margin-top: 10px; font-weight: 700; font-family: 'Soria', 'Playfair Display', serif; font-size: 1.2rem; color: #5B21B6;">Awaiting product input...</div>
            <div style="font-size: 0.88rem; color: #4338CA; margin-top: 4px;">Click a scenario above or describe your product to view live agent reasoning.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        logs = state.get("agent_logs", [])
        st.markdown('<div style="max-height: 420px; overflow-y: auto; padding-right: 5px;">', unsafe_allow_html=True)
        for log in logs:
            status_icon = "✓" if log["status"] == "completed" else "ℹ️" if log["status"] == "info" else "⟳"
            st.markdown(f"""
            <div class="agent-log-card">
                <div>
                    <span class="agent-log-time">[{log['timestamp']}]</span>
                    <span class="agent-log-name">{status_icon} {log['agent_name']}</span>
                </div>
                <div style="color: #1E1B4B; font-size: 0.92rem; margin-top: 4px; line-height: 1.4; font-family: 'Rubik', sans-serif;">
                    {log['message']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# Results Display Area (Triggered once agent reaches recommendation phase)
if state and not state.get("current_question"):
    st.markdown("---")
    st.markdown("""
    <h2 class="soria-heading" style="font-size: 1.8rem; background: linear-gradient(135deg, #5B21B6 0%, #7E22CE 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 16px;">
        📋 Compliance Profile & BIS Standard Recommendations
    </h2>
    """, unsafe_allow_html=True)

    # Executive Profile Metrics Cards
    p1, p2, p3, p4 = st.columns(4)
    electric_val = state.get("electric")
    power_str = "Electric" if electric_val is True else "Non-Electric" if electric_val is False else "Unknown"

    with p1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Category</div>
            <div class="metric-value">{state.get("category", "General")}</div>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Subcategory</div>
            <div class="metric-value">{state.get("subcategory", "Unspecified")}</div>
        </div>
        """, unsafe_allow_html=True)
    with p3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Material</div>
            <div class="metric-value">{state.get("material", "Unspecified")}</div>
        </div>
        """, unsafe_allow_html=True)
    with p4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Power Type</div>
            <div class="metric-value">{power_str}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Recommendation Results
    rec_dict = state.get("recommended_standards")
    if rec_dict:
        rec = RecommendationResult(**rec_dict)
        primary = rec.primary_standard

        col_rec1, col_rec2 = st.columns([1.2, 0.8], gap="medium")

        with col_rec1:
            st.markdown('<h3 style="font-size: 1.3rem; color: #5B21B6; margin-bottom: 10px;">🌟 Primary Recommended Standard</h3>', unsafe_allow_html=True)
            if primary:
                badge_class = "badge-high" if rec.match_strength == "High" else "badge-medium" if rec.match_strength == "Medium" else "badge-low"
                
                st.markdown(f"""
                <div class="recommended-box">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style="margin:0; color:#FFFFFF; font-size:1.7rem; font-weight:800; font-family: 'Soria', 'Playfair Display', serif;">{primary.standard_code}</h2>
                        <span class="{badge_class}">Match Score: {rec.match_strength}</span>
                    </div>
                    <h4 style="color:#F3E8FF; margin-top:10px; font-size:1.15rem;">{primary.title}</h4>
                    <p style="color:#E9D5FF; font-size:0.98rem; line-height: 1.55; margin-top: 8px; font-family: 'Rubik', sans-serif;">{primary.description}</p>
                    <div style="margin-top: 16px;">
                        <a href="{primary.source_url}" target="_blank" style="background: #FFFFFF; color: #5B21B6; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: 800; font-size: 0.9rem; display: inline-block;">🔗 Access Official BIS Documentation ➔</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="why-card">
                    <div class="soria-heading" style="color:#5B21B6; font-weight:700; font-size:1.15rem; margin-bottom:8px;">💡 Agent Match Reasoning & Evidence</div>
                """, unsafe_allow_html=True)
                st.write(rec.reason)
                for ev in rec.evidence:
                    st.write(f"- {ev}")
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.warning("No candidate standard matched the specified product parameters.")

        with col_rec2:
            st.markdown('<h3 style="font-size: 1.3rem; color: #5B21B6; margin-bottom: 10px;">🔍 Excluded Standards Analysis</h3>', unsafe_allow_html=True)
            if rec.excluded_candidates:
                for excl in rec.excluded_candidates:
                    with st.expander(f"❌ {excl['standard_code']} — {excl['title']}"):
                        st.markdown(f"**Exclusion Reason:** {excl['reason']}")
            else:
                st.info("No candidate standards were explicitly excluded.")

            if rec.additional_standards:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<h4 style="font-size: 1.15rem; color: #5B21B6; margin-bottom: 8px;">📚 Additional Relevant Standards</h4>', unsafe_allow_html=True)
                for add in rec.additional_standards:
                    st.markdown(f"- **[{add.standard_code}]({add.source_url})**: {add.title}")

    # Full Generated Compliance Report Section
    st.markdown("---")
    st.markdown('<h3 style="font-size: 1.4rem; color: #5B21B6; margin-bottom: 12px;">📄 Complete BIS Compliance Advisory Report</h3>', unsafe_allow_html=True)
    
    report_text = state.get("final_report", "")
    with st.expander("View Full Markdown Compliance Report", expanded=True):
        st.markdown(report_text)

    st.download_button(
        label="📥 Download Full Compliance Advisory Report (.md)",
        data=report_text,
        file_name=f"BIS_Compliance_Report_{state.get('category','Product')}.md",
        mime="text/markdown",
        use_container_width=True
    )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #4338CA; font-size: 0.88rem; padding-top: 10px; font-weight: 600;">
    🤖 BISense AI Compliance Agent • Powered by LangGraph, Pydantic & Streamlit • Hackathon Edition
</div>
""", unsafe_allow_html=True)

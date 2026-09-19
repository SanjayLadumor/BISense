from typing import Dict, Any, Literal
from models.schemas import ComplianceState
from services.llm_service import LLMService
from agents.product_agent import ProductAgent
from agents.clarification_agent import ClarificationAgent, MAX_QUESTIONS
from agents.retrieval_agent import RetrievalAgent
from agents.recommendation_agent import RecommendationAgent
from agents.report_agent import ReportAgent
from retrieval.search import HybridRetriever

try:
    from langgraph.graph import StateGraph, END, START
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class ComplianceWorkflow:
    """
    LangGraph Workflow controller for BIS Product Compliance Agent.
    Manages node execution, state transitions, clarification loops, and report generation.
    """

    def __init__(self, llm_service: LLMService = None, retriever: HybridRetriever = None):
        self.llm_service = llm_service or LLMService()
        self.retriever = retriever or HybridRetriever()

        self.product_agent = ProductAgent(self.llm_service)
        self.clarification_agent = ClarificationAgent(self.llm_service)
        self.retrieval_agent = RetrievalAgent(self.retriever)
        self.recommendation_agent = RecommendationAgent(self.llm_service)
        self.report_agent = ReportAgent(self.llm_service)

        if LANGGRAPH_AVAILABLE:
            self.graph = self._build_langgraph()
        else:
            self.graph = None

    def _build_langgraph(self):
        builder = StateGraph(ComplianceState)

        # Add Nodes
        builder.add_node("product_analysis", self.product_agent.run)
        builder.add_node("clarification_check", self.clarification_agent.run)
        builder.add_node("retrieve", self.retrieval_agent.run)
        builder.add_node("recommend", self.recommendation_agent.run)
        builder.add_node("generate_report", self.report_agent.run)

        # Graph Routing
        builder.add_edge(START, "product_analysis")
        builder.add_edge("product_analysis", "clarification_check")

        def route_clarification(state: ComplianceState) -> str:
            if state.get("current_question") and state.get("clarification_count", 0) < MAX_QUESTIONS:
                return "ask_question"
            return "retrieve"

        builder.add_conditional_edges(
            "clarification_check",
            route_clarification,
            {
                "ask_question": END,  # Pause graph execution to await user input in UI
                "retrieve": "retrieve"
            }
        )

        builder.add_edge("retrieve", "recommend")
        builder.add_edge("recommend", "generate_report")
        builder.add_edge("generate_report", END)

        return builder.compile()

    def create_initial_state(self, product_description: str) -> ComplianceState:
        """Initialize empty state for a new product assessment session."""
        return {
            "product_description": product_description,
            "category": "General",
            "subcategory": "Unspecified",
            "material": "Unspecified",
            "intended_use": "General use",
            "target_user": "General public",
            "electric": None,
            "product_type": "Standard product",
            "missing_information": [],
            "questions_asked": [],
            "answers": [],
            "clarification_count": 0,
            "current_question": None,
            "candidate_standards": [],
            "recommended_standards": None,
            "final_report": "",
            "agent_logs": []
        }

    def step(self, state: ComplianceState) -> ComplianceState:
        """
        Execute workflow steps deterministically across nodes.
        Handles both compiled LangGraph execution and step-by-step UI loops.
        """

        # 1. Product Analysis
        product_res = self.product_agent.run(state)
        state.update(product_res)

        # 2. Clarification Check
        clarif_res = self.clarification_agent.run(state)
        state.update(clarif_res)

        # If a new question needs answering and max limit not exceeded -> pause for UI input
        if state.get("current_question") and state.get("clarification_count", 0) < MAX_QUESTIONS:
            return state

        # 3. Retrieve
        retrieval_res = self.retrieval_agent.run(state)
        state.update(retrieval_res)

        # 4. Recommend
        rec_res = self.recommendation_agent.run(state)
        state.update(rec_res)

        # 5. Generate Report
        report_res = self.report_agent.run(state)
        state.update(report_res)

        return state

    def answer_question(self, state: ComplianceState, answer: str) -> ComplianceState:
        """Record user's clarification answer and re-run analysis flow."""
        current_q = state.get("current_question")
        if not current_q:
            return state

        questions = list(state.get("questions_asked", []))
        answers = list(state.get("answers", []))

        questions.append(current_q)
        answers.append(answer)

        count = state.get("clarification_count", 0) + 1

        state["questions_asked"] = questions
        state["answers"] = answers
        state["clarification_count"] = count
        state["current_question"] = None

        return self.step(state)


def create_compliance_graph():
    return ComplianceWorkflow()

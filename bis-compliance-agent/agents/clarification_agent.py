from typing import Dict, Any
import datetime
from models.schemas import ComplianceState, ProductInfo
from services.llm_service import LLMService

MAX_QUESTIONS = 4


class ClarificationAgent:
    """Agent that determines if critical product attributes are missing and generates targeted questions."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def run(self, state: ComplianceState) -> Dict[str, Any]:
        clarification_count = state.get("clarification_count", 0)
        questions_asked = list(state.get("questions_asked", []))
        missing_info = state.get("missing_information", [])

        # Check if max questions reached
        if clarification_count >= MAX_QUESTIONS:
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = {
                "agent_name": "Clarification Agent",
                "status": "completed",
                "message": f"Reached maximum allowed clarification limit ({MAX_QUESTIONS} questions). Proceeding to retrieval.",
                "timestamp": now_str
            }
            logs = list(state.get("agent_logs", []))
            logs.append(log_entry)
            return {
                "current_question": None,
                "agent_logs": logs
            }

        # Create ProductInfo instance from state
        product_info = ProductInfo(
            category=state.get("category", "General"),
            subcategory=state.get("subcategory", "Unspecified"),
            material=state.get("material", "Unspecified"),
            intended_use=state.get("intended_use", "General use"),
            target_user=state.get("target_user", "General public"),
            electric=state.get("electric"),
            product_type=state.get("product_type", "Standard product"),
            missing_information=missing_info
        )

        # Generate targeted clarification question
        question = self.llm_service.generate_clarification_question(
            product_info=product_info,
            questions_asked=questions_asked
        )

        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        logs = list(state.get("agent_logs", []))

        if question and question not in questions_asked:
            log_entry = {
                "agent_name": "Clarification Agent",
                "status": "info",
                "message": f"Generated targeted question: '{question}'",
                "timestamp": now_str
            }
            logs.append(log_entry)
            return {
                "current_question": question,
                "agent_logs": logs
            }
        else:
            log_entry = {
                "agent_name": "Clarification Agent",
                "status": "completed",
                "message": "Sufficient product information collected. No further clarification needed.",
                "timestamp": now_str
            }
            logs.append(log_entry)
            return {
                "current_question": None,
                "agent_logs": logs
            }

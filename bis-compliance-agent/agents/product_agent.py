from typing import Dict, Any
import datetime
from models.schemas import ComplianceState, ProductInfo
from services.llm_service import LLMService


class ProductAgent:
    """Agent responsible for understanding product descriptions and extracting structured attributes."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def run(self, state: ComplianceState) -> Dict[str, Any]:
        product_description = state.get("product_description", "")
        questions = state.get("questions_asked", [])
        answers = state.get("answers", [])

        # Build Q&A context string
        qa_pairs = []
        for q, a in zip(questions, answers):
            qa_pairs.append(f"Q: {q}\nA: {a}")
        qa_context = "\n".join(qa_pairs)

        # Extract structured product info via LLM or Fallback Engine
        product_info: ProductInfo = self.llm_service.extract_product_info(
            product_description=product_description,
            qa_context=qa_context
        )

        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "agent_name": "Product Agent",
            "status": "completed",
            "message": f"Classified product as category '{product_info.category}' ({product_info.product_type})",
            "timestamp": now_str
        }

        logs = list(state.get("agent_logs", []))
        logs.append(log_entry)

        return {
            "category": product_info.category,
            "subcategory": product_info.subcategory,
            "material": product_info.material,
            "intended_use": product_info.intended_use,
            "target_user": product_info.target_user,
            "electric": product_info.electric,
            "product_type": product_info.product_type,
            "missing_information": product_info.missing_information,
            "agent_logs": logs
        }

from typing import Dict, Any
import datetime
from models.schemas import ComplianceState, ProductInfo, RecommendationResult
from services.llm_service import LLMService


class ReportAgent:
    """Agent that compiles the final compliance assessment report."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def run(self, state: ComplianceState) -> Dict[str, Any]:
        product_info = ProductInfo(
            category=state.get("category", "General"),
            subcategory=state.get("subcategory", "Unspecified"),
            material=state.get("material", "Unspecified"),
            intended_use=state.get("intended_use", "General use"),
            target_user=state.get("target_user", "General public"),
            electric=state.get("electric"),
            product_type=state.get("product_type", "Standard product"),
            missing_information=state.get("missing_information", [])
        )

        rec_dict = state.get("recommended_standards", {}) or {}
        recommendation = RecommendationResult(**rec_dict)

        report_markdown = self.llm_service.generate_report(
            product_info=product_info,
            recommendation=recommendation
        )

        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "agent_name": "Report Agent",
            "status": "completed",
            "message": "Generated final BIS compliance assessment report",
            "timestamp": now_str
        }

        logs = list(state.get("agent_logs", []))
        logs.append(log_entry)

        return {
            "final_report": report_markdown,
            "agent_logs": logs
        }

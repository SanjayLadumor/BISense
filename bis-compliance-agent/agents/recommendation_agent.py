from typing import Dict, Any
import datetime
from models.schemas import ComplianceState, ProductInfo, RecommendationResult
from services.llm_service import LLMService


class RecommendationAgent:
    """Agent that evaluates candidate standards, ranks recommendations, and provides match explanations."""

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

        candidates = state.get("candidate_standards", [])

        recommendation: RecommendationResult = self.llm_service.generate_recommendation(
            product_info=product_info,
            candidate_standards=candidates
        )

        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        primary_code = recommendation.primary_standard.standard_code if recommendation.primary_standard else "None"
        
        log_entry = {
            "agent_name": "Recommendation Agent",
            "status": "completed",
            "message": f"Recommended standard {primary_code} (Match Strength: {recommendation.match_strength})",
            "timestamp": now_str
        }

        logs = list(state.get("agent_logs", []))
        logs.append(log_entry)

        return {
            "recommended_standards": recommendation.model_dump(),
            "agent_logs": logs
        }

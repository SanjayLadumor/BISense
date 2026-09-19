from typing import Dict, Any
import datetime
from models.schemas import ComplianceState, ProductInfo
from retrieval.search import HybridRetriever


class RetrievalAgent:
    """Agent responsible for searching the local BIS standards database using hybrid retrieval."""

    def __init__(self, retriever: HybridRetriever = None):
        self.retriever = retriever or HybridRetriever()

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

        candidates = self.retriever.search(product_info=product_info, top_k=5)

        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "agent_name": "Retrieval Agent",
            "status": "completed",
            "message": f"Retrieved top {len(candidates)} candidate standards from local BIS dataset",
            "timestamp": now_str
        }

        logs = list(state.get("agent_logs", []))
        logs.append(log_entry)

        return {
            "candidate_standards": candidates,
            "agent_logs": logs
        }

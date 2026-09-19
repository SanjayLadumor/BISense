import os
import json
import re
import math
from typing import List, Dict, Any, Optional
from models.schemas import BISStandard, ProductInfo


class HybridRetriever:
    """
    Hybrid retriever combining exact key/field matching, token overlap scoring,
    and semantic vector similarity over the local BIS standards dataset.
    """

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "bis_standards.json")

        self.data_path = data_path
        self.standards: List[BISStandard] = self._load_standards()
        self.sentence_model = None

        # Attempt to load local sentence transformer if installed
        try:
            from sentence_transformers import SentenceTransformer
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embeddings = self.sentence_model.encode(
                [f"{s.title} {s.category} {s.description} {' '.join(s.keywords)}" for s in self.standards]
            )
        except Exception:
            self.sentence_model = None

    def _load_standards(self) -> List[BISStandard]:
        if not os.path.exists(self.data_path):
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [BISStandard(**item) for item in raw_data]

    def search(self, product_info: ProductInfo, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Execute hybrid search over the local BIS dataset.
        Returns a list of dicts with keys: 'standard', 'score', 'match_reasons'.
        """
        if not self.standards:
            return []

        scored_results = []
        query_text = f"{product_info.category} {product_info.subcategory} {product_info.product_type} {product_info.material} {product_info.intended_use}".lower()

        # Check for semantic embeddings
        semantic_scores = [0.0] * len(self.standards)
        if self.sentence_model is not None:
            try:
                import numpy as np
                query_vec = self.sentence_model.encode([query_text])[0]
                # Cosine similarity
                sims = np.dot(self.embeddings, query_vec) / (
                    np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vec) + 1e-9
                )
                semantic_scores = sims.tolist()
            except Exception:
                pass

        for idx, std in enumerate(self.standards):
            reasons = []

            # 1. Category Matching Weight (Highest weight)
            category_score = 0.0
            if product_info.category != "General":
                if std.category.lower() == product_info.category.lower():
                    category_score = 0.40
                    reasons.append(f"Category match: '{std.category}'")
                elif product_info.category.lower() in std.category.lower() or std.category.lower() in product_info.category.lower():
                    category_score = 0.25
                    reasons.append(f"Partial category match: '{std.category}'")

            # 2. Electric Status Matching Weight
            electric_score = 0.0
            if product_info.electric is not None and std.electric is not None:
                if product_info.electric == std.electric:
                    electric_score = 0.20
                    reasons.append(f"Power requirement match ({'Electric' if std.electric else 'Non-electric'})")
                else:
                    # Mismatch penalty
                    electric_score = -0.30

            # 3. Keyword / Token Matching Weight
            text_to_search = f"{std.title} {std.subcategory} {std.description} {' '.join(std.keywords)} {' '.join(std.materials)}".lower()
            tokens = set(re.findall(r'\w+', query_text))
            token_matches = 0
            for token in tokens:
                if len(token) > 2 and token in text_to_search:
                    token_matches += 1

            keyword_score = min(0.30, token_matches * 0.06)
            if token_matches > 0:
                reasons.append(f"{token_matches} keyword tokens matched")

            # 4. Material Match Weight
            material_score = 0.0
            if product_info.material != "Unspecified":
                for mat in std.materials:
                    if mat.lower() in product_info.material.lower() or product_info.material.lower() in mat.lower():
                        material_score = 0.10
                        reasons.append(f"Material match: '{mat}'")
                        break

            # 5. Semantic similarity score contribution
            sem_score = max(0.0, float(semantic_scores[idx])) * 0.20
            if sem_score > 0.05:
                reasons.append(f"Semantic similarity match ({sem_score:.2f})")

            # Total score calculation
            total_score = category_score + electric_score + keyword_score + material_score + sem_score
            total_score = max(0.0, min(1.0, total_score))

            scored_results.append({
                "standard": std.model_dump(),
                "score": round(total_score, 3),
                "match_reasons": list(set(reasons))
            })

        # Rank candidates by total score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

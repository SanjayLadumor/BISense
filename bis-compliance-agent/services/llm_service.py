import os
import json
import re
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

from models.schemas import ProductInfo, RecommendationResult, BISStandard
from utils.prompts import (
    PRODUCT_EXTRACTION_PROMPT,
    CLARIFICATION_PROMPT,
    RECOMMENDATION_PROMPT,
    REPORT_PROMPT
)


class LLMService:
    """
    LLM abstraction service with automatic fallback to deterministic rule-based logic
    if API keys are missing or API calls fail.
    """

    def __init__(self):
        self.api_key = (
            os.getenv("LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        self.provider = os.getenv("LLM_PROVIDER", "openai" if os.getenv("OPENAI_API_KEY") else "gemini")

    def _call_llm_text(self, prompt: str) -> Optional[str]:
        """Attempt to call an LLM API if configured."""
        if not self.api_key:
            return None

        # Standard OpenAI client check
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            pass

        # Try Google Generative AI
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(prompt)
            return res.text.strip()
        except Exception:
            pass

        return None

    def extract_product_info(self, product_description: str, qa_context: str = "") -> ProductInfo:
        """Extract structured product information from description and Q&A history."""
        prompt = PRODUCT_EXTRACTION_PROMPT.format(
            product_description=product_description,
            qa_context=qa_context or "None"
        )
        
        response_text = self._call_llm_text(prompt)
        if response_text:
            try:
                # Clean json formatting
                cleaned = re.sub(r'```json\s*', '', response_text)
                cleaned = re.sub(r'```\s*$', '', cleaned).strip()
                data = json.loads(cleaned)
                return ProductInfo(**data)
            except Exception:
                pass

        # Fallback heuristic parser
        return self._heuristic_product_extraction(product_description, qa_context)

    def generate_clarification_question(
        self,
        product_info: ProductInfo,
        questions_asked: List[str]
    ) -> Optional[str]:
        """Formulate ONE targeted clarification question based on missing product attributes."""
        info_json = json.dumps(product_info.model_dump(), indent=2)
        prompt = CLARIFICATION_PROMPT.format(
            product_profile_json=info_json,
            questions_asked=json.dumps(questions_asked)
        )

        response_text = self._call_llm_text(prompt)
        if response_text and response_text.strip():
            question = response_text.strip().strip('"').strip("'")
            if question and question not in questions_asked:
                return question

        # Fallback heuristic clarification question generator
        return self._heuristic_clarification_question(product_info, questions_asked)

    def generate_recommendation(
        self,
        product_info: ProductInfo,
        candidate_standards: List[Dict[str, Any]]
    ) -> RecommendationResult:
        """Select standards, generate evidence, and explain exclusions."""
        if not candidate_standards:
            return RecommendationResult(
                primary_standard=None,
                additional_standards=[],
                match_strength="None",
                reason="No candidate standards matched the product profile in the database.",
                evidence=[],
                excluded_candidates=[]
            )

        info_json = json.dumps(product_info.model_dump(), indent=2)
        candidates_json = json.dumps(candidate_standards, indent=2)
        prompt = RECOMMENDATION_PROMPT.format(
            product_profile_json=info_json,
            candidate_standards_json=candidates_json
        )

        response_text = self._call_llm_text(prompt)
        if response_text:
            try:
                cleaned = re.sub(r'```json\s*', '', response_text)
                cleaned = re.sub(r'```\s*$', '', cleaned).strip()
                data = json.loads(cleaned)

                primary = BISStandard(**data["primary_standard"]) if data.get("primary_standard") else None
                additionals = [BISStandard(**s) for s in data.get("additional_standards", [])]

                return RecommendationResult(
                    primary_standard=primary,
                    additional_standards=additionals,
                    match_strength=data.get("match_strength", "Medium"),
                    reason=data.get("reason", ""),
                    evidence=data.get("evidence", []),
                    excluded_candidates=data.get("excluded_candidates", [])
                )
            except Exception:
                pass

        # Deterministic recommendation evaluation
        return self._heuristic_recommendation(product_info, candidate_standards)

    def generate_report(
        self,
        product_info: ProductInfo,
        recommendation: RecommendationResult
    ) -> str:
        """Generate formatted markdown assessment report."""
        info_json = json.dumps(product_info.model_dump(), indent=2)
        rec_json = json.dumps(recommendation.model_dump(), indent=2)
        prompt = REPORT_PROMPT.format(
            product_profile_json=info_json,
            recommendation_result_json=rec_json
        )

        response_text = self._call_llm_text(prompt)
        if response_text and len(response_text) > 100:
            return response_text

        return self._heuristic_report(product_info, recommendation)

    # ------------------------------------------------------------------
    # Deterministic Heuristic Fallbacks (Ensures system never fails)
    # ------------------------------------------------------------------

    def _heuristic_product_extraction(self, text: str, qa_context: str) -> ProductInfo:
        combined = f"{text} {qa_context}".lower()

        # Category determination with explicit priority checks
        category = "General"
        if any(tag in combined for tag in ["category: electronics", "[electronics]"]) or (
            any(w in combined for w in ["electronic", "appliance", "laptop", "tv", "led", "wire", "plug", "power", "charger", "socket", "circuit", "battery"])
            and not any(w in combined for w in ["toy", "children toy", "puzzle toy"])
        ):
            category = "Electronics"
        elif any(tag in combined for tag in ["category: textiles", "[textiles]"]) or (
            any(w in combined for w in ["textile", "cotton", "fabric", "garment", "cloth", "mask", "curtain", "towel", "sack", "sanitary", "napkin", "upholstery", "apparel"])
            and not any(w in combined for w in ["toy", "doll"])
        ):
            category = "Textiles"
        elif any(tag in combined for tag in ["category: food packaging", "[food packaging]"]) or (
            any(w in combined for w in ["packag", "food contact", "bottle", "container", "pouch", "pet bottle", "polyethylene", "polypropylene", "water bottle", "beverage", "tiffin"])
            and not any(w in combined for w in ["toy"])
        ):
            category = "Food Packaging"
        elif any(tag in combined for tag in ["category: toys", "[toys]"]) or (
            any(w in combined for w in ["toy", "puzzle", "game", "doll", "play", "children", "child", "action figure", "finger paint", "swing", "slide"])
        ):
            category = "Toys"
        elif any(w in combined for w in ["electric", "electrical"]):
            category = "Electronics"

        # Electric determination
        electric = None
        if any(w in combined for w in ["non-electric", "non electric", "manual", "battery-free", "without battery", "no power", "passive"]):
            electric = False
        elif any(w in combined for w in ["electric", "electrical", "battery", "mains", "plug", "230v", "220v", "powered", "motor", "rechargeable", "charger", "adapter"]):
            electric = True
        elif category == "Toys" and "puzzle" in combined:
            electric = False
        elif category == "Electronics":
            electric = True

        # Material detection
        material = "Unspecified"
        if any(w in combined for w in ["plastic", "pvc", "hdpe", "pet", "polyethylene", "polypropylene", "vinyl"]):
            material = "Plastic"
        elif any(w in combined for w in ["cotton", "yarn"]):
            material = "Cotton"
        elif any(w in combined for w in ["polyester", "nylon", "synthetic"]):
            material = "Polyester"
        elif any(w in combined for w in ["metal", "steel", "stainless steel", "aluminium", "brass", "copper"]):
            material = "Metal"
        elif any(w in combined for w in ["wood", "wooden"]):
            material = "Wood"
        elif any(w in combined for w in ["glass"]):
            material = "Glass"

        # Target user & intended use
        target_user = "Children" if any(w in combined for w in ["child", "children", "baby", "kid", "under 14", "under 3"]) else "General public"
        if category == "Toys":
            intended_use = "Play and learning"
        elif category == "Textiles":
            intended_use = "Clothing / Medical / Home Furnishings"
        elif category == "Food Packaging":
            intended_use = "Direct food or beverage contact"
        elif category == "Electronics":
            intended_use = "Power supply / Consumer operation"
        else:
            intended_use = "General use"

        # Subcategory
        subcategory = "General"
        if "puzzle" in combined:
            subcategory = "Puzzle"
        elif any(w in combined for w in ["garment", "cloth", "apparel", "shirt"]):
            subcategory = "Apparel"
        elif any(w in combined for w in ["mask", "surgical mask"]):
            subcategory = "Medical Textiles"
        elif any(w in combined for w in ["container", "bottle", "jar", "pouch"]):
            subcategory = "Container"
        elif any(w in combined for w in ["appliance", "iron", "mixer", "grinder", "heater"]):
            subcategory = "Home Appliance"
        elif any(w in combined for w in ["led", "lamp", "lighting", "bulb"]):
            subcategory = "Lighting"
        elif any(w in combined for w in ["battery", "li-ion", "cell"]):
            subcategory = "Batteries"

        # Missing information evaluation
        missing = []
        if electric is None:
            missing.append("Electric or non-electric status")
        if category == "Toys" and not any(w in combined for w in ["age", "year", "month", "under"]):
            missing.append("Target age group")
        if category == "Electronics" and not any(w in combined for w in ["mains", "battery", "voltage", "power", "watt", "ac", "dc"]):
            missing.append("Power source & voltage rating")
        if category == "Textiles" and material == "Unspecified":
            missing.append("Primary fibre/material composition")
        if category == "Food Packaging" and not any(w in combined for w in ["direct", "contact", "water", "beverage", "dry"]):
            missing.append("Direct food contact application")

        return ProductInfo(
            category=category,
            subcategory=subcategory,
            material=material,
            intended_use=intended_use,
            target_user=target_user,
            electric=electric,
            product_type=f"{'Electric' if electric is True else 'Non-electric' if electric is False else ''} {subcategory}".strip(),
            missing_information=missing
        )

    def _heuristic_clarification_question(self, info: ProductInfo, asked: List[str]) -> Optional[str]:
        # Domain specific question queue
        candidates = []

        if info.category == "Toys":
            if info.electric is None:
                candidates.append("Is the product electric or non-electric?")
            candidates.append("Is the toy intended for children below 14 years of age?")
            if info.material == "Unspecified":
                candidates.append("What is the primary material (e.g., Plastic, Wood, Fabric, Metal)?")

        elif info.category == "Electronics":
            candidates.append("Is the device powered by mains electricity (220V/230V AC) or batteries?")
            candidates.append("What type of electronic device is it (e.g. IT equipment, home appliance, audio/video, lighting)?")
            candidates.append("What is its rated voltage and power capacity?")

        elif info.category == "Textiles":
            candidates.append("What is the primary fibre/material composition (e.g. 100% Cotton, Polyester, Blend)?")
            candidates.append("Is it intended for clothing/apparel, medical use, home furnishings, or industrial use?")

        elif info.category == "Food Packaging":
            candidates.append("Will the packaging come into direct contact with food or drinking water?")
            candidates.append("What type of plastic/material is used (e.g., Polyethylene/PE, Polypropylene/PP, PET)?")
            candidates.append("What type of food or liquid will be stored in the packaging?")

        else:
            candidates.append("Is the product electric or non-electric?")
            candidates.append("What is the primary material used in manufacturing?")

        for q in candidates:
            if q not in asked:
                return q
        return None

    def _heuristic_recommendation(
        self,
        info: ProductInfo,
        candidates: List[Dict[str, Any]]
    ) -> RecommendationResult:
        valid_candidates = []
        excluded = []

        for cand in candidates:
            std = BISStandard(**cand["standard"])
            score = cand.get("score", 0.0)

            # Check electric match mismatch
            if info.electric is not None and std.electric is not None:
                if info.electric != std.electric:
                    excluded.append({
                        "standard_code": std.standard_code,
                        "title": std.title,
                        "reason": f"Product is {'electric' if info.electric else 'non-electric'}, whereas {std.standard_code} requires {'electric' if std.electric else 'non-electric'} products."
                    })
                    continue

            # Category filter check
            if info.category != "General" and std.category != "General" and std.category != info.category:
                excluded.append({
                    "standard_code": std.standard_code,
                    "title": std.title,
                    "reason": f"Category mismatch: product is classified as {info.category}, but standard applies to {std.category}."
                })
                continue

            valid_candidates.append((std, score))

        if not valid_candidates:
            # Fallback to top scored candidate even if partial mismatch
            if candidates:
                std = BISStandard(**candidates[0]["standard"])
                return RecommendationResult(
                    primary_standard=std,
                    additional_standards=[],
                    match_strength="Low",
                    reason=f"Selected {std.standard_code} as the closest available reference standard.",
                    evidence=[f"✓ Fits category {std.category}"],
                    excluded_candidates=excluded
                )
            return RecommendationResult(
                primary_standard=None,
                additional_standards=[],
                match_strength="None",
                reason="No matching standard found.",
                evidence=[],
                excluded_candidates=excluded
            )

        # Sort valid candidates by score
        valid_candidates.sort(key=lambda x: x[1], reverse=True)
        primary = valid_candidates[0][0]
        additionals = [item[0] for item in valid_candidates[1:4]]

        evidence = [
            f"✓ Matches product category: {info.category}",
            f"✓ Product type alignment: {info.product_type}",
            f"✓ Material compatibility: {info.material}",
            f"✓ Intended target users: {info.target_user}"
        ]

        if info.electric is not None:
            evidence.append(f"✓ Power requirement match: {'Electric' if info.electric else 'Non-electric'}")

        match_strength = "High" if valid_candidates[0][1] >= 0.5 else "Medium"

        power_str = "Electric" if info.electric is True else "Non-electric" if info.electric is False else "Unspecified"
        return RecommendationResult(
            primary_standard=primary,
            additional_standards=additionals,
            match_strength=match_strength,
            reason=f"Recommended {primary.standard_code} ({primary.title}) because the product matches category '{info.category}', material '{info.material}', and power profile ({power_str}).",
            evidence=evidence,
            excluded_candidates=excluded
        )

    def _heuristic_report(
        self,
        info: ProductInfo,
        rec: RecommendationResult
    ) -> str:
        primary = rec.primary_standard
        primary_code = primary.standard_code if primary else "N/A"
        primary_title = primary.title if primary else "No Standard Matched"
        source_url = primary.source_url if primary else "#"

        add_str = ""
        if rec.additional_standards:
            add_str = "\n".join([f"- **{s.standard_code}**: {s.title}" for s in rec.additional_standards])
        else:
            add_str = "None identified."

        evidence_str = "\n".join([f"- {e}" for e in rec.evidence])

        excluded_str = ""
        if rec.excluded_candidates:
            excluded_str = "\n".join([
                f"- **{e['standard_code']} ({e['title']})**: {e['reason']}"
                for e in rec.excluded_candidates
            ])
        else:
            excluded_str = "No candidate standards were explicitly excluded."

        report = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                  BIS COMPLIANCE ASSESSMENT REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 1. PRODUCT PROFILE
- **Category:** {info.category}
- **Subcategory:** {info.subcategory}
- **Product Classification:** {info.product_type}
- **Primary Material:** {info.material}
- **Power Requirement:** {'Electric' if info.electric is True else 'Non-electric' if info.electric is False else 'Unspecified'}
- **Target User:** {info.target_user}
- **Intended Application:** {info.intended_use}

---

### 2. RECOMMENDED PRIMARY STANDARD
- **Standard Code:** [{primary_code}]({source_url})
- **Title:** {primary_title}
- **Match Confidence:** **{rec.match_strength}**
- **Issuing Authority:** Bureau of Indian Standards (BIS)

**Recommendation Rationale:**
{rec.reason}

**Key Attribute Matches:**
{evidence_str}

---

### 3. ADDITIONAL & SECONDARY STANDARDS
{add_str}

---

### 4. CANDIDATES EVALUATION & EXCLUSION RATIONALE
{excluded_str}

---

### 5. SUGGESTED COMPLIANCE NEXT STEPS
1. **Verify Exact Product Scope:** Cross-reference product technical specifications with the official scope of {primary_code}.
2. **Identify Mandatory Certification Scheme:** Check if the product falls under **ISI Mark Scheme (Scheme-I)** or **Compulsory Registration Scheme (CRS)**.
3. **Select BIS-Recognized Lab:** Schedule testing at an NABL / BIS recognized laboratory for safety and heavy metal/flammability migration analysis.
4. **Technical Documentation:** Compile factory quality test reports, component BOM, and manufacturing process documentation.
5. **BIS Portal Registration:** Submit formal compliance application via the official BIS online portal.

---

### 6. OFFICIAL SOURCES
- **Bureau of Indian Standards:** [{primary_code} Official Source]({source_url})
- **BIS Portal:** [https://www.services.bis.gov.in](https://www.services.bis.gov.in)

---

### IMPORTANT DISCLAIMER
*This assessment is generated by an AI-powered preliminary evaluation agent for informational and educational hackathon demonstration purposes. Indian manufacturers should consult authorized BIS technical auditors and official BIS documentation before relying on this assessment for legal compliance.*
"""
        return report

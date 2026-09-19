from typing import List, Optional, Dict, Any, TypedDict
from pydantic import BaseModel, Field


class ProductInfo(BaseModel):
    category: str = Field(description="High-level category (e.g. Toys, Electronics, Textiles, Food Packaging, General)")
    subcategory: str = Field(default="Unspecified", description="Subcategory of the product")
    material: str = Field(default="Unspecified", description="Primary material composition (e.g. Plastic, Cotton, Metal, Glass)")
    intended_use: str = Field(default="General use", description="Intended application or purpose")
    target_user: str = Field(default="General public", description="Target end user (e.g. Children, Adults, Industrial)")
    electric: Optional[bool] = Field(default=None, description="True if product requires electricity/battery, False if non-electric, None if unknown")
    product_type: str = Field(default="Standard product", description="Specific functional type description")
    missing_information: List[str] = Field(default_factory=list, description="Key attributes missing for precise BIS standard matching")


class BISStandard(BaseModel):
    standard_code: str = Field(description="Official BIS Standard designation, e.g. IS 9873 Part 1")
    title: str = Field(description="Full title of the BIS standard")
    category: str = Field(description="Product category covered")
    subcategory: str = Field(default="General", description="Subcategory focus")
    materials: List[str] = Field(default_factory=list, description="Applicable materials")
    keywords: List[str] = Field(default_factory=list, description="Associated search keywords")
    electric: Optional[bool] = Field(default=None, description="Whether standard applies to electric products")
    description: str = Field(description="Detailed scope and safety/compliance description")
    source: str = Field(default="Bureau of Indian Standards", description="Issuing body")
    source_url: str = Field(description="Official or reference BIS catalog URL")


class CandidateStandard(BaseModel):
    standard: BISStandard
    score: float = Field(description="Retrieval similarity/relevance score between 0 and 1")
    match_reasons: List[str] = Field(default_factory=list, description="Specific attribute matches")


class RecommendationResult(BaseModel):
    primary_standard: Optional[BISStandard] = Field(default=None, description="Top matching standard")
    additional_standards: List[BISStandard] = Field(default_factory=list, description="Secondary or related standards")
    match_strength: str = Field(default="Low", description="Confidence level: High, Medium, Low, None")
    reason: str = Field(default="", description="Summary explaining recommendation decision")
    evidence: List[str] = Field(default_factory=list, description="Bullet points showing matching product attributes")
    excluded_candidates: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Candidate standards not selected with explicit mismatch rationale"
    )


class AgentLog(TypedDict):
    agent_name: str
    status: str  # "started", "completed", "warning", "info"
    message: str
    timestamp: str


class ComplianceState(TypedDict):
    product_description: str

    category: str
    subcategory: str
    material: str
    intended_use: str
    target_user: str
    electric: Optional[bool]
    product_type: str
    missing_information: List[str]

    questions_asked: List[str]
    answers: List[str]

    clarification_count: int
    current_question: Optional[str]

    candidate_standards: List[Dict[str, Any]]
    recommended_standards: Optional[Dict[str, Any]]

    final_report: str
    agent_logs: List[Dict[str, str]]

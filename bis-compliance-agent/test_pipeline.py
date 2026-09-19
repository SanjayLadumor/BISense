import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure utf-8 stdout encoding for windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from graph.compliance_graph import ComplianceWorkflow, MAX_QUESTIONS
from models.schemas import RecommendationResult


def test_demo_scenarios():
    print("==================================================")
    print("Testing BIS Product Compliance Advisor Agent Pipeline")
    print("==================================================")

    workflow = ComplianceWorkflow()

    test_cases = [
        ("Toys", "I manufacture plastic puzzles for children.", "Under 14 years"),
        ("Electronics", "I manufacture an electronic appliance for home use.", "Mains powered 230V AC"),
        ("Textiles", "I manufacture cotton garments.", "100% Cotton fabric"),
        ("Food Packaging", "I manufacture plastic containers used for food.", "Polyethylene plastic food grade"),
        ("Vague Input", "I make a product.", "General domestic item")
    ]

    for label, prompt, sample_answer in test_cases:
        print(f"\n--------------------------------------------------")
        print(f"Testing Scenario: {label}")
        print(f"Input Description: '{prompt}'")
        print(f"--------------------------------------------------")

        state = workflow.create_initial_state(prompt)
        state = workflow.step(state)

        # Loop through clarification questions if any are asked
        while state.get("current_question") and state.get("clarification_count", 0) < MAX_QUESTIONS:
            q = state["current_question"]
            print(f"Clarification Q{state.get('clarification_count', 0) + 1}: '{q}'")
            print(f"User Answer -> '{sample_answer}'")
            state = workflow.answer_question(state, sample_answer)

        print(f"Extracted Category: {state.get('category')}")
        print(f"Product Type: {state.get('product_type')}")
        print(f"Electric: {state.get('electric')}")

        rec_dict = state.get("recommended_standards")
        if rec_dict:
            rec = RecommendationResult(**rec_dict)
            primary = rec.primary_standard
            if primary:
                print(f"[OK] Primary Standard: {primary.standard_code} - {primary.title}")
                print(f"Match Strength: {rec.match_strength}")
                print(f"Why? {rec.reason}")
                print(f"Evidence Count: {len(rec.evidence)}")
                print(f"Excluded Candidates Count: {len(rec.excluded_candidates)}")
            else:
                print("[WARN] No Primary Standard Matched.")
        else:
            print("[WARN] No Recommendation Output.")

        report = state.get("final_report", "")
        print(f"Generated Report Length: {len(report)} characters")
        assert len(report) > 50, "Report should not be empty"

    print("\n==================================================")
    print("[SUCCESS] All 5 demo scenarios passed successfully!")
    print("==================================================")

if __name__ == "__main__":
    test_demo_scenarios()

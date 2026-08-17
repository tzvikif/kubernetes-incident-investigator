from pathlib import Path

from openai import OpenAI

from incident_copilot.config import get_openai_judge_model, get_openai_model
from incident_copilot.data_loader import load_incident_cases
from incident_copilot.llm_baseline import LLMBaseline
from incident_copilot.semantic_evaluator import SemanticEvaluator
from incident_copilot.schemas import IncidentCase, RCAResponse
from get_keys import get_openai_api_key


def check(prediction: RCAResponse, case: IncidentCase) -> list[bool]:
    category_correct = (
        prediction.incident_category
        == case.expected_category
    )

    evidence_status_correct = (
        prediction.evidence_status
        == case.expected_evidence_status
    )

    service_correct = (
        prediction.affected_service
        == case.service
    )
    return  [
        category_correct,
        evidence_status_correct,
        service_correct
    ]

def create_baseline() -> LLMBaseline:
    client = OpenAI(api_key=get_openai_api_key())
    model = get_openai_model()

    return LLMBaseline(
        client=client,
        model=model,
    )


def create_semantic_evaluator() -> SemanticEvaluator:
    client = OpenAI(api_key=get_openai_api_key())
    model = get_openai_judge_model()
    return SemanticEvaluator(client=client, model=model)


if __name__ == "__main__":
    case_path = Path("data/evaluation/incidents_cases.jsonl")
    cases = load_incident_cases(case_path)
    if not cases:
        raise ValueError(f"No incident cases found in {case_path}")
    rca_responses = []
    baseline = create_baseline()
    semantic_evaluator = create_semantic_evaluator()
    for i, case in enumerate(cases):
        print(f"Case {i}: {case.case_id}")
        try:
            rca_response = baseline.diagnose(case=case)
            rca_responses.append(rca_response)
            print(rca_response.model_dump_json(indent=2))
        except Exception as e:
            print(f"Error during diagnosis: {e}")
            continue

        res = check(rca_response, case)
        print(f"exact-match coverage: {sum(res) / len(res)}")

        try:
            # The judge sees ground truth only after the RCA has been generated.
            # It returns claim-level verdicts; Python computes the final scores.
            semantic_result = semantic_evaluator.evaluate(case, rca_response)
            print(semantic_result.model_dump_json(indent=2))
        except Exception as e:
            print(f"Error during semantic evaluation: {e}")

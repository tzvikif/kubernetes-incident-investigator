from pathlib import Path

from openai import OpenAI

from incident_copilot.baseline_prompt import build_baseline_messages
from incident_copilot.config import get_openai_model
from incident_copilot.data_loader import load_incident_cases
from incident_copilot.llm_baseline import LLMBaseline
from incident_copilot.schemas import IncidentCase, RCAResponse
from get_keys import get_openai_api_key
import numpy as np

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


if __name__ == "__main__":
    case_path = Path("data/evaluation/incidents_cases.jsonl")
    cases = load_incident_cases(case_path)
    if not cases:
        raise ValueError(f"No incident cases found in {case_path}")
    rca_responses = []
    for i, case in enumerate(cases):
        print(f"Case {i}: {case.case_id}")
        rca_response = None
        baseline = create_baseline()
        try:
            rca_response = baseline.diagnose(case=case)
            rca_responses.append(rca_response)
            print(f"RCA response {rca_response}")
        except Exception as e:
            print(f"Error during diagnosis: {e}")
        res = check(rca_response, case)
        print(f"coverage: {np.sum(res)/len(res)}")

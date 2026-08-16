from pathlib import Path

from openai import OpenAI

from incident_copilot.baseline_prompt import build_baseline_messages
from incident_copilot.config import get_openai_model
from incident_copilot.data_loader import load_incident_cases
from incident_copilot.llm_baseline import LLMBaseline
from get_keys import get_openai_api_key


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

    first_case = cases[0]
    baseline = create_baseline()
    rca_response = baseline.diagnose(case=first_case)
    print(f"RCA response {rca_response}")
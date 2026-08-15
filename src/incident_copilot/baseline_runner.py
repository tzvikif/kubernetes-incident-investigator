from openai import OpenAI
import argparse
from incident_copilot.config import get_openai_model
from incident_copilot.llm_baseline import LLMBaseline
from get_keys import get_openai_api_key
from src.incident_copilot.baseline_prompt import build_baseline_messages
from src.incident_copilot.schemas import IncidentCase


def create_baseline() -> LLMBaseline:
    client = OpenAI(api_key=get_openai_api_key())
    model = get_openai_model()

    return LLMBaseline(
        client=client,
        model=model,
    )


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    # add --case-id as parameter to the script
    argument_parser.add_argument(
        "--case-id",
        type=str,
        required=True,
        help="The ID of the incident case to diagnose",
    )
    args = argument_parser.parse_args()
    case = IncidentCase.load_case(args.case_id)
    response = build_baseline_messages(case=case)
    print(response)
    # baseline = create_baseline()
    # print(f"LLM Baseline created with model: {baseline._model}")

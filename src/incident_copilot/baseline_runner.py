from openai import OpenAI

from .config import get_openai_model
from .llm_baseline import LLMBaseline


def create_baseline() -> LLMBaseline:
    client = OpenAI()
    model = get_openai_model()

    return LLMBaseline(
        client=client,
        model=model,
    )
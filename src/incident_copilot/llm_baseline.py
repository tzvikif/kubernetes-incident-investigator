from typing import Any

from openai import APIError, OpenAI
from pydantic import ValidationError

from incident_copilot.baseline_prompt import build_baseline_messages
from incident_copilot.schemas import IncidentCase, RCAResponse


class LLMResponseError(RuntimeError):
    """Raised when the LLM request does not produce a valid RCA response."""


class LLMBaseline:
    def __init__(self, client: OpenAI, model: str) -> None:
        if not model.strip():
            raise ValueError("model must be a non-empty string")

        self._client = client
        self._model = model

    def diagnose(self, case: IncidentCase) -> RCAResponse:
        messages = build_baseline_messages(case)

        try:
            response = self._client.responses.parse(
                model=self._model,
                input=messages,
                text_format=RCAResponse,
            )
        except APIError as exc:
            # The OpenAI client applies its configured bounded retry policy
            # before surfacing an APIError to the caller.
            raise LLMResponseError("OpenAI request failed") from exc
        except (TypeError, ValueError, ValidationError) as exc:
            raise LLMResponseError(
                "OpenAI returned an invalid structured response"
            ) from exc

        status = getattr(response, "status", None)
        if status == "incomplete":
            details = getattr(response, "incomplete_details", None)
            reason = getattr(details, "reason", None) or "unknown reason"
            raise LLMResponseError(
                f"OpenAI response was incomplete: {reason}"
            )

        refusal = _find_refusal(response)
        if refusal is not None:
            raise LLMResponseError(f"OpenAI model refused the request: {refusal}")

        if status not in (None, "completed"):
            raise LLMResponseError(
                f"OpenAI response ended with unexpected status: {status}"
            )

        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise LLMResponseError(
                "OpenAI response did not contain parsed RCA output"
            )

        if isinstance(parsed, RCAResponse):
            return parsed

        try:
            return RCAResponse.model_validate(parsed)
        except (TypeError, ValueError, ValidationError) as exc:
            raise LLMResponseError(
                "OpenAI returned an invalid RCA response"
            ) from exc


def _find_refusal(response: Any) -> str | None:
    for output_item in getattr(response, "output", None) or []:
        if getattr(output_item, "type", None) != "message":
            continue

        for content_item in getattr(output_item, "content", None) or []:
            if getattr(content_item, "type", None) != "refusal":
                continue

            refusal = getattr(content_item, "refusal", None)
            if isinstance(refusal, str) and refusal:
                return refusal

            return "no refusal reason was provided"

    return None

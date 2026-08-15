from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from incident_copilot.baseline_prompt import build_baseline_messages
from incident_copilot.llm_baseline import LLMBaseline, LLMResponseError
from incident_copilot.schemas import (
    DependencyFixture,
    EvidenceSource,
    EvidenceStatus,
    EventFixture,
    IncidentCase,
    IncidentCategory,
    RCAResponse,
    SupportingEvidence,
    TelemetryFixture,
)


def make_incident_case() -> IncidentCase:
    return IncidentCase(
        case_id="case_001",
        query="Checkout requests fail although its Pods are healthy.",
        service="checkout",
        start_time=datetime(2026, 8, 14, 8, 0, tzinfo=UTC),
        end_time=datetime(2026, 8, 14, 8, 15, tzinfo=UTC),
        telemetry_fixture=TelemetryFixture(
            request_rate_per_minute=500.0,
            http_5xx_rate=0.30,
            baseline_http_5xx_rate=0.01,
            p95_latency_ms=900.0,
            baseline_p95_latency_ms=200.0,
            cpu_utilization=0.40,
            memory_utilization=0.50,
            available_endpoints=0,
            healthy_pods=3,
        ),
        events_fixture=[
            EventFixture(
                event_id="event_001",
                type="Warning",
                message="Service has no active endpoints.",
            )
        ],
        dependency_fixture=DependencyFixture(
            payment="healthy",
            inventory="healthy",
        ),
        expected_category=IncidentCategory.SERVICE_ROUTING,
        expected_evidence_status=EvidenceStatus.SUFFICIENT,
        expected_tool_calls=["get_telemetry"],
        expected_document_topics=["service_routing"],
        required_answer_facts=["available endpoints are zero"],
        forbidden_claims=["The selector is definitely incorrect."],
    )


def make_rca_response() -> RCAResponse:
    return RCAResponse(
        incident_category=IncidentCategory.SERVICE_ROUTING,
        evidence_status=EvidenceStatus.SUFFICIENT,
        affected_service="checkout",
        root_cause="The Service has no usable endpoints.",
        supporting_evidence=[
            SupportingEvidence(
                source=EvidenceSource.TELEMETRY,
                fact="Three Pods are healthy and available endpoints are zero.",
            )
        ],
        confidence=0.9,
        recommended_action="Inspect the Service selector and EndpointSlices.",
        limitations=["The Service configuration was not supplied."],
    )


def make_client(response: object) -> MagicMock:
    client = MagicMock()
    client.responses.parse.return_value = response
    return client


def test_diagnose_returns_parsed_response_and_sends_expected_request() -> None:
    case = make_incident_case()
    parsed = make_rca_response()
    client = make_client(
        SimpleNamespace(
            status="completed",
            output_parsed=parsed,
            output=[],
        )
    )

    result = LLMBaseline(client=client, model="test-model").diagnose(case)

    assert result is parsed
    client.responses.parse.assert_called_once_with(
        model="test-model",
        input=build_baseline_messages(case),
        text_format=RCAResponse,
    )


def test_diagnose_validates_dictionary_output() -> None:
    parsed = make_rca_response()
    client = make_client(
        SimpleNamespace(
            status="completed",
            output_parsed=parsed.model_dump(),
            output=[],
        )
    )

    result = LLMBaseline(client=client, model="test-model").diagnose(
        make_incident_case()
    )

    assert result == parsed
    assert isinstance(result, RCAResponse)


def test_diagnose_rejects_incomplete_response() -> None:
    client = make_client(
        SimpleNamespace(
            status="incomplete",
            incomplete_details=SimpleNamespace(reason="max_output_tokens"),
            output_parsed=None,
            output=[],
        )
    )

    with pytest.raises(LLMResponseError, match="incomplete: max_output_tokens"):
        LLMBaseline(client=client, model="test-model").diagnose(
            make_incident_case()
        )


def test_diagnose_rejects_model_refusal() -> None:
    refusal = SimpleNamespace(type="refusal", refusal="Policy restriction")
    message = SimpleNamespace(type="message", content=[refusal])
    client = make_client(
        SimpleNamespace(
            status="completed",
            output_parsed=None,
            output=[message],
        )
    )

    with pytest.raises(LLMResponseError, match="refused.*Policy restriction"):
        LLMBaseline(client=client, model="test-model").diagnose(
            make_incident_case()
        )


def test_diagnose_rejects_missing_parsed_output() -> None:
    client = make_client(
        SimpleNamespace(status="completed", output_parsed=None, output=[])
    )

    with pytest.raises(LLMResponseError, match="did not contain parsed RCA output"):
        LLMBaseline(client=client, model="test-model").diagnose(
            make_incident_case()
        )


def test_diagnose_rejects_invalid_parsed_output() -> None:
    client = make_client(
        SimpleNamespace(
            status="completed",
            output_parsed={"incident_category": "not-a-category"},
            output=[],
        )
    )

    with pytest.raises(LLMResponseError, match="invalid RCA response"):
        LLMBaseline(client=client, model="test-model").diagnose(
            make_incident_case()
        )


def test_diagnose_rejects_unexpected_status() -> None:
    client = make_client(
        SimpleNamespace(status="failed", output_parsed=None, output=[])
    )

    with pytest.raises(LLMResponseError, match="unexpected status: failed"):
        LLMBaseline(client=client, model="test-model").diagnose(
            make_incident_case()
        )


def test_diagnose_wraps_openai_api_errors() -> None:
    class FakeAPIError(Exception):
        pass

    client = MagicMock()
    client.responses.parse.side_effect = FakeAPIError("connection failed")

    with patch("incident_copilot.llm_baseline.APIError", FakeAPIError):
        with pytest.raises(LLMResponseError, match="OpenAI request failed"):
            LLMBaseline(client=client, model="test-model").diagnose(
                make_incident_case()
            )


def test_rejects_blank_model_name_without_calling_client() -> None:
    client = MagicMock()

    with pytest.raises(ValueError, match="model must be a non-empty string"):
        LLMBaseline(client=client, model="   ")

    client.responses.parse.assert_not_called()

import json
from datetime import UTC, datetime

from incident_copilot.schemas import (
    DependencyFixture,
    EvidenceStatus,
    EventFixture,
    IncidentCase,
    IncidentCategory,
    TelemetryFixture,
)

from incident_copilot.baseline_prompt import (
    BASELINE_SYSTEM_PROMPT,
    build_baseline_messages,
    build_incident_payload,
)

def make_incident_case() -> IncidentCase:
    return IncidentCase(
        case_id="case_001",
        query=(
            "Checkout requests fail although its Pods are healthy."
        ),
        service="checkout",
        start_time=datetime(
            2026, 8, 14, 8, 0, tzinfo=UTC
        ),
        end_time=datetime(
            2026, 8, 14, 8, 15, tzinfo=UTC
        ),
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
        expected_tool_calls=["LEAK_MARKER_TOOL"],
        expected_document_topics=["LEAK_MARKER_DOCUMENT"],
        required_answer_facts=["LEAK_MARKER_REQUIRED_FACT"],
        forbidden_claims=["LEAK_MARKER_FORBIDDEN_CLAIM"],
    )

def test_build_incident_payload_contains_only_allowed_fields() -> None:
    case = make_incident_case()

    payload = build_incident_payload(case)

    assert set(payload) == {
        "query",
        "service",
        "start_time",
        "end_time",
        "telemetry_fixture",
        "events_fixture",
        "dependency_fixture",
    }


def test_build_incident_payload_contains_evidence() -> None:
    case = make_incident_case()

    payload = build_incident_payload(case)

    assert payload["query"] == case.query
    assert payload["service"] == "checkout"

    assert payload["start_time"] == (
        "2026-08-14T08:00:00+00:00"
    )
    assert payload["end_time"] == (
        "2026-08-14T08:15:00+00:00"
    )

    assert payload["telemetry_fixture"][
        "available_endpoints"
    ] == 0

    assert payload["telemetry_fixture"][
        "healthy_pods"
    ] == 3

    assert payload["events_fixture"][0]["type"] == "Warning"

    assert payload["dependency_fixture"] == {
        "payment": "healthy",
        "inventory": "healthy",
    }


def test_build_incident_payload_excludes_ground_truth() -> None:
    case = make_incident_case()

    payload = build_incident_payload(case)

    forbidden_keys = {
        "case_id",
        "expected_category",
        "expected_evidence_status",
        "expected_tool_calls",
        "expected_document_topics",
        "required_answer_facts",
        "forbidden_claims",
    }

    assert forbidden_keys.isdisjoint(payload)
    assert not any(
        key.startswith("expected_")
        for key in payload
    )
def test_serialized_payload_does_not_leak_answer_data() -> None:
    case = make_incident_case()

    payload = build_incident_payload(case)
    serialized_payload = json.dumps(payload)

    assert "service_routing" not in serialized_payload
    assert "evidence_sufficient" not in serialized_payload
    assert "LEAK_MARKER_TOOL" not in serialized_payload
    assert "LEAK_MARKER_DOCUMENT" not in serialized_payload
    assert "LEAK_MARKER_REQUIRED_FACT" not in serialized_payload
    assert "LEAK_MARKER_FORBIDDEN_CLAIM" not in serialized_payload


def test_build_baseline_messages_returns_two_messages() -> None:
    case = make_incident_case()

    messages = build_baseline_messages(case)

    assert len(messages) == 2
    assert messages[0]["role"] == "developer"
    assert messages[1]["role"] == "user"


def test_system_prompt_contains_all_categories() -> None:
    expected_categories = {
        "service_routing",
        "dependency_failure",
        "dns_failure",
        "resource_saturation",
        "latency_degradation",
        "http_error_increase",
    }

    for category in expected_categories:
        assert category in BASELINE_SYSTEM_PROMPT

def test_baseline_messages_exclude_ground_truth() -> None:
    case = make_incident_case()

    messages = build_baseline_messages(case)
    complete_prompt = json.dumps(messages)

    forbidden_keys = [
        "expected_category",
        "expected_evidence_status",
        "expected_tool_calls",
        "expected_document_topics",
        "required_answer_facts",
        "forbidden_claims",
    ]

    for key in forbidden_keys:
        assert key not in complete_prompt

    assert "LEAK_MARKER_TOOL" not in complete_prompt
    assert "LEAK_MARKER_DOCUMENT" not in complete_prompt
    assert "LEAK_MARKER_REQUIRED_FACT" not in complete_prompt
    assert "LEAK_MARKER_FORBIDDEN_CLAIM" not in complete_prompt


def test_system_prompt_explicitly_allows_abstention() -> None:
    prompt = BASELINE_SYSTEM_PROMPT.lower()

    assert "abstain" in prompt
    assert "null" in prompt
    assert "evidence_insufficient" in prompt


def test_system_prompt_contains_diagnostic_boundaries() -> None:
    # collapse whitespace/newlines so assertions aren't sensitive to line breaks
    prompt = " ".join(BASELINE_SYSTEM_PROMPT.lower().split())

    assert "high latency alone does not prove resource saturation" in prompt
    assert "increased http errors alone do not prove dependency failure" in prompt
    assert "zero endpoints alone does not prove a selector mismatch" in prompt
    assert "failed connection alone does not prove dns failure" in prompt
    assert "non-destructive" in prompt

'''

def test_baseline_prompt_contains_no_retrieval_context() -> None:
    case = make_incident_case()

    messages = build_baseline_messages(case)
    complete_prompt = json.dumps(messages).lower()

    assert "runbook" not in complete_prompt
    assert "retrieved passage" not in complete_prompt
    assert "bm25" not in complete_prompt
'''
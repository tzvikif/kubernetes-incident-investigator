import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from incident_copilot.config import ConfigurationError, get_openai_judge_model
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
from incident_copilot.semantic_evaluator import (
    ClaimKind,
    ClaimVerdict,
    EntailmentLabel,
    SemanticEvaluationError,
    SemanticEvaluator,
    SemanticJudgeResponse,
    build_reference_claims,
    build_semantic_judge_messages,
    score_semantic_judgments,
)


def make_case() -> IncidentCase:
    return IncidentCase(
        case_id="case_002",
        query="Customers cannot complete checkout because payment requests fail.",
        service="checkout",
        start_time=datetime(2026, 8, 14, 15, 0, tzinfo=UTC),
        end_time=datetime(2026, 8, 14, 15, 15, tzinfo=UTC),
        telemetry_fixture=TelemetryFixture(
            request_rate_per_minute=105.0,
            http_5xx_rate=0.67,
            p95_latency_ms=950.0,
            cpu_utilization=0.38,
            memory_utilization=0.49,
            available_endpoints=3,
            healthy_pods=3,
        ),
        events_fixture=[
            EventFixture(
                event_id="event-002",
                type="DependencyConnectionFailure",
                message="Checkout requests to payment timed out repeatedly",
            )
        ],
        dependency_fixture=DependencyFixture(
            payment="unhealthy",
            inventory="healthy",
        ),
        expected_category=IncidentCategory.DEPENDENCY_FAILURE,
        expected_evidence_status=EvidenceStatus.SUFFICIENT,
        expected_tool_calls=["get_dependency_health"],
        expected_document_topics=["downstream dependency failures"],
        required_answer_facts=[
            "Checkout has three available endpoints.",
            "Checkout pods are healthy.",
            "Payment is unhealthy.",
            "Checkout requests to payment timed out.",
            "Inventory is healthy.",
        ],
        forbidden_claims=[
            "DNS failure caused the incident.",
            "Inventory caused the incident.",
        ],
    )


def make_prediction() -> RCAResponse:
    return RCAResponse(
        incident_category=IncidentCategory.DEPENDENCY_FAILURE,
        evidence_status=EvidenceStatus.SUFFICIENT,
        affected_service="checkout",
        root_cause="Payment is unhealthy and requests to it timed out.",
        supporting_evidence=[
            SupportingEvidence(
                source=EvidenceSource.TELEMETRY,
                fact="Checkout has three endpoints and three healthy pods.",
            )
        ],
        confidence=0.95,
        recommended_action="Inspect payment availability.",
        limitations=["The underlying payment failure is unknown."],
    )


def verdict(
    claim_id: str,
    label: EntailmentLabel,
) -> ClaimVerdict:
    return ClaimVerdict(
        claim_id=claim_id,
        verdict=label,
        response_excerpt=(
            None if label == EntailmentLabel.NOT_MENTIONED else "relevant text"
        ),
        explanation="Test judgment.",
    )


def make_judge_output() -> SemanticJudgeResponse:
    return SemanticJudgeResponse(
        verdicts=[
            verdict("required_0", EntailmentLabel.ENTAILED),
            verdict("required_1", EntailmentLabel.ENTAILED),
            verdict("required_2", EntailmentLabel.ENTAILED),
            verdict("required_3", EntailmentLabel.ENTAILED),
            verdict("required_4", EntailmentLabel.NOT_MENTIONED),
            verdict("forbidden_0", EntailmentLabel.NOT_MENTIONED),
            verdict("forbidden_1", EntailmentLabel.CONTRADICTED),
        ]
    )


def test_build_reference_claims_assigns_stable_ids_and_kinds() -> None:
    claims = build_reference_claims(make_case())

    assert [claim.claim_id for claim in claims] == [
        "required_0",
        "required_1",
        "required_2",
        "required_3",
        "required_4",
        "forbidden_0",
        "forbidden_1",
    ]
    assert claims[0].kind == ClaimKind.REQUIRED
    assert claims[-1].kind == ClaimKind.FORBIDDEN


def test_judge_messages_contain_prediction_and_reference_claims() -> None:
    messages = build_semantic_judge_messages(make_case(), make_prediction())
    payload = json.loads(messages[1]["content"])

    assert messages[0]["role"] == "developer"
    assert payload["generated_rca_response"]["affected_service"] == "checkout"
    assert payload["reference_claims"][0] == {
        "claim_id": "required_0",
        "kind": "required",
        "text": "Checkout has three available endpoints.",
    }


def test_score_reports_required_coverage_and_forbidden_rate() -> None:
    result = score_semantic_judgments(make_case(), make_judge_output())

    assert result.score.required_facts_entailed == 4
    assert result.score.required_facts_total == 5
    assert result.score.required_fact_coverage == 0.8
    assert result.score.forbidden_claims_asserted == 0
    assert result.score.forbidden_claim_rate == 0.0
    assert result.score.passed is False


def test_entailed_forbidden_claim_is_a_violation() -> None:
    output = make_judge_output()
    output.verdicts[-1] = verdict(
        "forbidden_1",
        EntailmentLabel.ENTAILED,
    )

    result = score_semantic_judgments(make_case(), output)

    assert result.score.forbidden_claims_asserted == 1
    assert result.score.forbidden_claim_rate == 0.5
    assert result.score.passed is False


def test_score_rejects_missing_claim_verdict() -> None:
    output = make_judge_output()
    output.verdicts.pop()

    with pytest.raises(SemanticEvaluationError, match="exactly one verdict"):
        score_semantic_judgments(make_case(), output)


def test_evaluator_sends_structured_request_and_returns_scores() -> None:
    case = make_case()
    prediction = make_prediction()
    parsed = make_judge_output()
    client = MagicMock()
    client.responses.parse.return_value = SimpleNamespace(
        status="completed",
        output_parsed=parsed,
        output=[],
    )

    result = SemanticEvaluator(client, "judge-model").evaluate(case, prediction)

    assert result.score.required_fact_coverage == 0.8
    client.responses.parse.assert_called_once_with(
        model="judge-model",
        input=build_semantic_judge_messages(case, prediction),
        text_format=SemanticJudgeResponse,
    )


def test_evaluator_rejects_incomplete_response() -> None:
    client = MagicMock()
    client.responses.parse.return_value = SimpleNamespace(
        status="incomplete",
        incomplete_details=SimpleNamespace(reason="max_output_tokens"),
        output_parsed=None,
        output=[],
    )

    with pytest.raises(SemanticEvaluationError, match="incomplete"):
        SemanticEvaluator(client, "judge-model").evaluate(
            make_case(), make_prediction()
        )


def test_evaluator_rejects_blank_model() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        SemanticEvaluator(MagicMock(), "   ")


def test_judge_model_uses_separate_environment_variable(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_JUDGE_MODEL", "judge-model")

    assert get_openai_judge_model() == "judge-model"


def test_missing_judge_model_is_rejected(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_JUDGE_MODEL", raising=False)

    with pytest.raises(ConfigurationError, match="OPENAI_JUDGE_MODEL"):
        get_openai_judge_model()

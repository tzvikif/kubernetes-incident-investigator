import pytest
from pydantic import ValidationError

from incident_copilot.schemas import (
    EvidenceSource,
    EvidenceStatus,
    IncidentCategory,
    RCAResponse,
    SupportingEvidence,
)


def make_valid_response() -> RCAResponse:
    return RCAResponse(
        incident_category=IncidentCategory.SERVICE_ROUTING,
        evidence_status=EvidenceStatus.SUFFICIENT,
        affected_service="checkout",
        root_cause="The service has no available endpoints.",
        supporting_evidence=[
            SupportingEvidence(
                source=EvidenceSource.TELEMETRY,
                fact="Three Pods are healthy but available endpoints are zero.",
            )
        ],
        confidence=0.9,
        recommended_action=(
            "Inspect the Service selector and EndpointSlice configuration."
        ),
        limitations=[],
    )


def test_accepts_valid_sufficient_diagnosis() -> None:
    response = make_valid_response()

    assert (
        response.incident_category
        == IncidentCategory.SERVICE_ROUTING
    )
    assert response.evidence_status == EvidenceStatus.SUFFICIENT
    assert response.confidence == 0.9


def test_accepts_valid_abstention() -> None:
    response = RCAResponse(
        incident_category=None,
        evidence_status=EvidenceStatus.INSUFFICIENT,
        affected_service="checkout",
        root_cause=None,
        supporting_evidence=[],
        confidence=0.2,
        recommended_action="Collect additional diagnostic evidence.",
        limitations=["No Kubernetes events were supplied."],
    )

    assert response.incident_category is None
    assert response.root_cause is None


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_rejects_invalid_confidence(
    confidence: float,
) -> None:
    data = make_valid_response().model_dump()
    data["confidence"] = confidence

    with pytest.raises(ValidationError):
        RCAResponse.model_validate(data)


def test_rejects_root_cause_with_insufficient_evidence() -> None:
    with pytest.raises(
        ValidationError,
        match="root_cause must be None",
    ):
        RCAResponse(
            incident_category=IncidentCategory.SERVICE_ROUTING,
            evidence_status=EvidenceStatus.INSUFFICIENT,
            affected_service="checkout",
            root_cause="The Service selector is incorrect.",
            supporting_evidence=[],
            confidence=0.4,
            recommended_action="Inspect the Service selector.",
            limitations=["The Service configuration was not supplied."],
        )


def test_rejects_sufficient_diagnosis_without_evidence() -> None:
    data = make_valid_response().model_dump()
    data["supporting_evidence"] = []

    with pytest.raises(
        ValidationError,
        match="requires supporting_evidence",
    ):
        RCAResponse.model_validate(data)


def test_rejects_unexpected_field() -> None:
    data = make_valid_response().model_dump()
    data["unexpected_field"] = "not allowed"

    with pytest.raises(ValidationError):
        RCAResponse.model_validate(data)
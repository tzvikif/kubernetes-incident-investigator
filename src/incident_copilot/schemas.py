

from datetime import datetime
from enum import StrEnum
from typing import Literal, Annotated


from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


NonEmptyString = Annotated[str, Field(min_length=1)]

class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
        allow_inf_nan=False,
    )


class TelemetryFixture(StrictModel):
    model_config = ConfigDict(extra="forbid")

    request_rate_per_minute: float = Field(ge=0)
    http_5xx_rate: float = Field(ge=0, le=1)
    baseline_http_5xx_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    p95_latency_ms: float = Field(ge=0)
    baseline_p95_latency_ms: float | None = Field(
        default=None,
        ge=0,
    )

    cpu_utilization: float = Field(ge=0, le=1)
    memory_utilization: float = Field(ge=0, le=1)
    available_endpoints: int = Field(ge=0)
    healthy_pods: int = Field(ge=0)


class EventFixture(StrictModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    message: str = Field(min_length=1)


class DependencyFixture(StrictModel):
    model_config = ConfigDict(extra="forbid")

    payment: Literal["healthy", "unhealthy"]
    inventory: Literal["healthy", "unhealthy"]

class IncidentCategory(StrEnum):
    SERVICE_ROUTING = "service_routing"
    DEPENDENCY_FAILURE = "dependency_failure"
    DNS_FAILURE = "dns_failure"
    RESOURCE_SATURATION = "resource_saturation"
    LATENCY_DEGRADATION = "latency_degradation"
    HTTP_ERROR_INCREASE = "http_error_increase"

# class SupportingEvidence(StrictModel):
#     query: str = Field(min_length=10)
#     telemetry: TelemetryFixture
#     kubernetes_event: str = Field(min_length=1)
#     dependency_health: str = Field(min_length=1)



class EvidenceStatus(StrEnum):
    SUFFICIENT = "evidence_sufficient"
    PARTIAL = "evidence_partial"
    INSUFFICIENT = "evidence_insufficient"


class IncidentCase(StrictModel):
    case_id: str = Field(pattern=r"^case_\d{3}$")
    query: str = Field(min_length=10)
    service: str = Field(
        pattern=r"^[a-z0-9](?:[-a-z0-9]*[a-z0-9])?$"
    )

    start_time: AwareDatetime
    end_time: AwareDatetime

    telemetry_fixture: TelemetryFixture
    events_fixture: list[EventFixture]
    dependency_fixture: DependencyFixture

    expected_category: IncidentCategory
    expected_evidence_status: EvidenceStatus

    expected_tool_calls: list[str] = Field(min_length=1)
    expected_document_topics: list[str] = Field(min_length=1)
    required_answer_facts: list[str] = Field(min_length=1)
    forbidden_claims: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_time_window(self) -> "IncidentCase":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time")

        return self


class DocumentChunk(StrictModel):
    chunk_id: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    section: str = Field(min_length=1)
    content: str = Field(min_length=1)

class RetrievalResult(StrictModel):
    chunk: DocumentChunk
    score: float
    rank: int = Field(ge=1)


class RetrievalEvaluationCase(StrictModel):
    case_id: str = Field(pattern=r"^retrieval_\d{3}$")
    query: str = Field(min_length=10)
    relevant_chunk_ids: list[str] = Field(min_length=1)


class EvidenceSource(StrEnum):
    QUERY = "query"
    TELEMETRY = "telemetry"
    KUBERNETES_EVENT = "kubernetes_event"
    DEPENDENCY_HEALTH = "dependency_health"


class SupportingEvidence(StrictModel):
    source: EvidenceSource
    fact: NonEmptyString


class RCAResponse(StrictModel):
    incident_category: IncidentCategory | None
    evidence_status: EvidenceStatus
    affected_service: NonEmptyString
    root_cause: NonEmptyString | None
    supporting_evidence: list[SupportingEvidence]
    confidence: float = Field(ge=0, le=1)
    recommended_action: NonEmptyString
    limitations: list[NonEmptyString]

    @model_validator(mode="after")
    def validate_diagnosis_consistency(self) -> "RCAResponse":
        if (
            self.evidence_status == EvidenceStatus.INSUFFICIENT
            and self.root_cause is not None
        ):
            raise ValueError(
                "root_cause must be None when evidence is insufficient"
            )

        if (
            self.incident_category is None
            and self.root_cause is not None
        ):
            raise ValueError(
                "root_cause must be None when incident_category is None"
            )

        if (
            self.evidence_status == EvidenceStatus.SUFFICIENT
            and not self.supporting_evidence
        ):
            raise ValueError(
                "sufficient evidence requires supporting_evidence"
            )

        return self
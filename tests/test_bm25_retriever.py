from pathlib import Path
import pytest

from incident_copilot.bm25_retriever import BM25Retriever
from incident_copilot.runbook_loader import load_runbooks


RUNBOOK_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "runbooks"
)


@pytest.mark.parametrize(
    ("query", "expected_topic"),
    [
        (
            "healthy pods but zero available service endpoints",
            "service_routing",
        ),
        (
            "required payment dependency is unhealthy",
            "dependency_failure",
        ),
        (
            "hostname lookup failed with DNS resolution error",
            "dns_failure",
        ),
        (
            "high CPU utilization with increased latency",
            "resource_saturation",
        ),
        (
            "p95 latency substantially above its normal baseline",
            "latency_degradation",
        ),
        (
            "HTTP 5xx error rate substantially above baseline",
            "http_error_increase",
        ),
    ],
)
def test_retrieves_correct_topic(
    query: str,
    expected_topic: str,
) -> None:
    chunks = load_runbooks(RUNBOOK_DIRECTORY)
    retriever = BM25Retriever(chunks)

    results = retriever.retrieve(query, top_k=3)

    assert results[0].chunk.topic == expected_topic

def test_retrieves_service_routing_chunks() -> None:
    chunks = load_runbooks(RUNBOOK_DIRECTORY)
    retriever = BM25Retriever(chunks)

    results = retriever.retrieve(
        query="healthy pods but zero available service endpoints",
        top_k=3,
    )

    assert len(results) == 3
    assert results[0].chunk.topic == "service_routing"
    assert results[0].rank == 1
    assert [result.rank for result in results] == [1, 2, 3]
    assert results[0].score >= results[1].score >= results[2].score
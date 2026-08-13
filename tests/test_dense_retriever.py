from pathlib import Path

from incident_copilot.runbook_loader import load_runbooks
from incident_copilot.dense_retriever import DenseRetriever


RUNBOOK_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "runbooks"
)


def test_dense_retrieves_correct_ranks() -> None:
    chunks = load_runbooks(RUNBOOK_DIRECTORY)
    dense_retriever = DenseRetriever(chunks)
    query = "The application instances are operational, but traffic has nowhere to go."
    results = dense_retriever.retrieve(query)
    assert len(results) == 3
    assert results[0].chunk.topic == "service_routing"
    assert [result.rank for result in results] == [1, 2, 3]
    






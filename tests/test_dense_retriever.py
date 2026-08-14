from pathlib import Path
import numpy as np

from incident_copilot.runbook_loader import load_runbooks
from incident_copilot.dense_retriever import DenseRetriever


RUNBOOK_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "runbooks"
)


def test_dense_retrieves_correct_ranks() -> None:
    chunks = load_runbooks(RUNBOOK_DIRECTORY)
    dense_retriever = DenseRetriever(chunks, device="cuda")
    query = "The application instances are operational, but traffic has nowhere to go."
    results = dense_retriever.retrieve(query)

    assert len(results) == 3
    assert results[0].chunk.topic == "service_routing"
    assert [result.rank for result in results] == [1, 2, 3]
    scores = [result.score for result in results]
    assert np.round(scores[0], decimals=3) == np.round(0.387, decimals=3)
    assert np.round(scores[1], decimals=3) == np.round(0.361, decimals=3)
    assert np.round(scores[2], decimals=3) == np.round(0.297, decimals=3)
    query = "healthy Pods zero available endpoints"
    results = dense_retriever.retrieve(query)
    assert results[0].chunk.topic == "service_routing"
    assert [result.rank for result in results] == [1, 2, 3]
    





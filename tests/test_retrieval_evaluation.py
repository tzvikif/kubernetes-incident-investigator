from pathlib import Path
from incident_copilot.schemas import RetrievalEvaluationCase

def test_retrieval_evaluation_case() -> None:
    RetrievalEvaluationCase(
        case_id="retrieval_001",
        query="The workloads are healthy, but requests have no destination",
        relevant_chunk_ids=[
            "service_routing__supported_diagnosis",
        ],
    )
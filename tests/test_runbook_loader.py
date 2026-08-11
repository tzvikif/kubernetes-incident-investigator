from pathlib import Path

from incident_copilot.runbook_loader import load_runbook, load_runbooks


RUNBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "runbooks"
    / "service_routing.md"
)


def test_load_runbook_creates_expected_chunks() -> None:
    chunks = load_runbook(RUNBOOK_PATH)

    assert len(chunks) == 4

    assert [chunk.section for chunk in chunks] == [
        "Symptoms",
        "Relevant evidence",
        "Supported diagnosis",
        "Diagnostic boundaries",
    ]

    assert [chunk.chunk_id for chunk in chunks] == [
        "service_routing__symptoms",
        "service_routing__relevant_evidence",
        "service_routing__supported_diagnosis",
        "service_routing__diagnostic_boundaries",
    ]

    assert all(chunk.topic == "service_routing" for chunk in chunks)
    assert all(chunk.content.strip() for chunk in chunks)

RUNBOOK_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "runbooks"
)


def test_load_runbooks_loads_directory() -> None:
    chunks = load_runbooks(RUNBOOK_DIRECTORY)

    assert len(chunks) == 4
    assert {chunk.topic for chunk in chunks} == {"service_routing"}
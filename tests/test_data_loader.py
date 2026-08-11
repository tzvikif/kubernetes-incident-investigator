from pathlib import Path

from incident_copilot.data_loader import load_incident_cases
import pytest
from pydantic import ValidationError
from incident_copilot.runbook_loader import load_runbook

def test_load_incident_cases_valid(tmp_path: Path) -> None:
    path = tmp_path / "incidents_cases.jsonl"
    path.write_text(
        '{"case_id":"case_001","query":"Investigate HTTP error spike","service":"api-service",'
        '"start_time":"2025-01-01T00:00:00+00:00","end_time":"2025-01-01T01:00:00+00:00",'
        '"telemetry_fixture":{"request_rate_per_minute":120.0,"http_5xx_rate":0.05,"baseline_http_5xx_rate":0.01,'
        '"p95_latency_ms":180.0,"baseline_p95_latency_ms":150.0,"cpu_utilization":0.75,"memory_utilization":0.6,'
        '"available_endpoints":5,"healthy_pods":3},'
        '"events_fixture":[{"event_id":"evt_001","type":"error","message":"503 errors increased"}],'
        '"dependency_fixture":{"payment":"healthy","inventory":"healthy"},'
        '"expected_category":"http_error_increase","expected_evidence_status":"evidence_sufficient",'
        '"expected_tool_calls":["kubectl get pods"],"expected_document_topics":["service health"],'
        '"required_answer_facts":["503 errors"],"forbidden_claims":["no issue detected"]}\n',
        encoding="utf-8",
    )

    cases = load_incident_cases(path)

    assert len(cases) == 1
    assert cases[0].case_id == "case_001"


def test_invalid_case_reports_line_number(tmp_path: Path) -> None:
    print(f"tmp_path: {tmp_path}")
    data_path = tmp_path / "invalid_cases.jsonl"
    data_path.write_text(
        '\n{"case_id": "invalid"}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"line 2") as error_info:
        load_incident_cases(data_path)

    assert isinstance(error_info.value.__cause__, ValidationError)

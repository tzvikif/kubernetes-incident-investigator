from pathlib import Path

from pydantic import ValidationError
from .schemas import IncidentCase


def load_incident_cases(path: Path) -> list[IncidentCase]:
    """Load incident cases from a JSON file."""
    cases = []

    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                case = IncidentCase.model_validate_json(line)
            except ValidationError as error:
                raise ValueError(
                    f"Invalid incident case at line {line_number} in {path}"
                ) from error
            cases.append(case)
    return cases

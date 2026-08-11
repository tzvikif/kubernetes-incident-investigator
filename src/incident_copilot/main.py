from pathlib import Path
from .runbook_loader import load_runbook


if __name__ == "__main__":
    chunks = load_runbook(Path("data/runbooks/service_routing.md"))
    print(len(chunks))
    print([chunk.section for chunk in chunks])
from pathlib import Path

from incident_copilot.schemas import DocumentChunk


def load_runbook(path: Path) -> list[DocumentChunk]:
    """Convert a Markdown runbook into retrievable chunks."""
    ...
    file_name = path.stem
    # read markdown file, split into sections, and create DocumentChunk instances
    with path.open(encoding="utf-8") as file:
        content = file.read()
        # Split the content into sections based on headings (e.g., ## Section)
        sections = content.split("## ")[1:]
        chunks = []
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            lines = section.splitlines()
            section_title = lines[0].strip() if lines else f"Section {i+1}"
            section_content = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
            chunk_id = f"{file_name}__{'_'.join(section_title.lower().split())}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    source_path=str(path),
                    topic=file_name,
                    section=section_title,
                    content=section_content,
                )
            )
    return chunks


def load_runbooks(directory: Path) -> list[DocumentChunk]:
    """Load all Markdown runbooks from a directory."""
    chunks = []

    for path in sorted(directory.glob("*.md")):
        chunks.extend(load_runbook(path))

    return chunks
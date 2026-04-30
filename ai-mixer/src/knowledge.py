"""Loads mixing-knowledge guides from the knowledge/ folder.

Drop new `.md` files into ai-mixer/knowledge/ and they get picked up
automatically. Files are concatenated in filename-sorted order, so
prefix with `00-`, `01-`, ... to control priority.
"""

from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def load_guides() -> str:
    if not KNOWLEDGE_DIR.exists():
        return ""
    parts: list[str] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        parts.append(f"# Source: {path.name}\n\n{path.read_text(encoding='utf-8')}")
    return "\n\n---\n\n".join(parts)


def list_guides() -> list[str]:
    if not KNOWLEDGE_DIR.exists():
        return []
    return [p.name for p in sorted(KNOWLEDGE_DIR.glob("*.md"))]

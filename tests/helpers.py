"""Tiny campaign fixtures for unit tests."""
from __future__ import annotations

from pathlib import Path

from runtime import ToolContext
from state_manager import StateManager


def make_ctx(root: Path) -> ToolContext:
    root.mkdir(parents=True, exist_ok=True)
    state = StateManager(root)
    state.ensure()
    state.update_config(target_profile="evm", policy="standard")
    return ToolContext(workspace=root, state=state, adapter=None)


def write_min_pdf(path: Path, text: str) -> None:
    """Uncompressed PDF-ish bytes whose literal strings `_raw_pdf_strings` can read."""
    payload = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    body = (
        "%PDF-1.1\n"
        "1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        f"stream\nBT /F1 12 Tf 10 150 Td ({payload}) Tj ET\nendstream\n"
        "%%EOF\n"
    )
    path.write_bytes(body.encode("latin-1", errors="replace"))

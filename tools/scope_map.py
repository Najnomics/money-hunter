"""Map intel/PDF excerpts onto in-scope public functions before a wrong-protocol kill."""
from __future__ import annotations

import re
from typing import Any

from runtime import ToolContext

CONSTANT_RE = re.compile(r"^[A-Z][A-Z0-9_]+$")
MIN_NAME_LEN = 4


def _mentions(text: str, token: str) -> bool:
    token = (token or "").strip()
    if len(token) < 2:
        return False
    return re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(token.lower())}(?![A-Za-z0-9_])",
        text.lower(),
    ) is not None


def list_in_scope_surfaces(ctx: ToolContext) -> list[dict[str, Any]]:
    ast_map = ctx.state.section(3, "ast_map") or {}
    surfaces: list[dict[str, Any]] = []
    seen: set[str] = set()
    for surface in ast_map.get("surfaces") or []:
        name = str(surface.get("name") or "")
        if not name or name.startswith("_") or CONSTANT_RE.match(name):
            continue
        if len(name) < MIN_NAME_LEN:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        surfaces.append(surface)
    return surfaces


def map_text_to_surfaces(ctx: ToolContext, text: str) -> list[dict[str, Any]]:
    """Return in-scope surfaces whose public names appear in an excerpt."""
    hits: list[dict[str, Any]] = []
    blob = text or ""
    for surface in list_in_scope_surfaces(ctx):
        name = str(surface.get("name") or "")
        if _mentions(blob, name):
            hits.append(surface)
    hits.sort(key=lambda s: (-len(str(s.get("name") or "")), str(s.get("name") or "")))
    return hits


def evidence_for_mapping(hits: list[dict[str, Any]]) -> list[str]:
    if not hits:
        return ["[DEDUCED] analog-unmapped: excerpt names no in-scope public function"]
    marks: list[str] = []
    for surface in hits[:12]:
        name = str(surface.get("name") or "")
        marks.append(f"[DEDUCED] mapped-surface:{name}")
        file = str(surface.get("file") or "")
        line = surface.get("line") or 1
        if file:
            marks.append(f"[CODE] {file}:{line}")
    return marks


def map_excerpt_to_surfaces(ctx: ToolContext, *parts: str) -> list[dict[str, Any]]:
    return map_text_to_surfaces(ctx, " ".join(str(p or "") for p in parts))

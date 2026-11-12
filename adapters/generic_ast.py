"""Language-agnostic surface extraction.

Uses tree-sitter when ``tree-sitter-language-pack`` is installed, and falls
back to per-language regex patterns otherwise. The returned method string is
recorded in ``.apex/03_divergences.json`` so the analyst knows how surfaces
were produced.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Sequence

from adapters.base import SurfaceHit
from fsutil import read_text, rel_to

LANGUAGE_BY_EXT = {
    ".py": "python",
    ".go": "go",
    ".rs": "rust",
    ".sol": "solidity",
    ".vy": "vyper",
    ".move": "move",
    ".cairo": "cairo",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "javascript",
    ".java": "java",
    ".kt": "kotlin",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".dart": "dart",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".sh": "bash",
    ".lua": "lua",
    ".zig": "zig",
}

FUNCTION_NODE_TYPES = {
    "function_definition",
    "function_declaration",
    "function_item",
    "method_definition",
    "method_declaration",
    "constructor_definition",
    "modifier_definition",
    "function",
}

try:  # optional dependency
    from tree_sitter_language_pack import get_parser as _get_parser  # type: ignore

    TREE_SITTER_AVAILABLE = True
except Exception:  # pragma: no cover - optional
    _get_parser = None
    TREE_SITTER_AVAILABLE = False


def language_of(path: Path) -> str:
    return LANGUAGE_BY_EXT.get(path.suffix.lower(), "unknown")


def _ts_surfaces(path: Path, root: Path) -> list[SurfaceHit]:
    if not TREE_SITTER_AVAILABLE or _get_parser is None:
        return []
    lang = LANGUAGE_BY_EXT.get(path.suffix.lower())
    if not lang:
        return []
    try:
        parser = _get_parser(lang)
        source = path.read_bytes()
        tree = parser.parse(source)
    except Exception:
        return []

    hits: list[SurfaceHit] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in FUNCTION_NODE_TYPES:
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                name = source[name_node.start_byte:name_node.end_byte].decode("utf-8", "replace")
                if name:
                    hits.append(
                        SurfaceHit(
                            file=rel_to(path, root),
                            line=node.start_point[0] + 1,
                            name=name,
                            kind="function",
                            language=lang,
                            entry=not name.startswith("_"),
                            extractor="tree-sitter",
                        )
                    )
        stack.extend(node.children)
    return hits


def _regex_surfaces(
    path: Path,
    root: Path,
    patterns: Sequence[tuple[str, str]],
) -> list[SurfaceHit]:
    lang = language_of(path)
    hits: list[SurfaceHit] = []
    compiled = [(kind, re.compile(rx)) for kind, rx in patterns]
    for idx, line in enumerate(read_text(path).splitlines(), start=1):
        for kind, rx in compiled:
            match = rx.search(line)
            if not match:
                continue
            name = next((g for g in match.groups() if g), None)
            if not name:
                continue
            hits.append(
                SurfaceHit(
                    file=rel_to(path, root),
                    line=idx,
                    name=name,
                    kind=kind,
                    language=lang,
                    entry=kind in {"route", "entry", "function"},
                    extractor="regex",
                )
            )
    return hits


def extract_surfaces(
    files: Iterable[Path],
    root: Path,
    patterns: Sequence[tuple[str, str]] = (),
    extensions: Sequence[str] = (),
    max_surfaces: int = 3000,
) -> tuple[list[SurfaceHit], str, list[str]]:
    """Return ``(surfaces, method, languages)``.

    Tree-sitter is attempted per file; files it cannot parse use the supplied
    regex patterns. Method is ``tree-sitter`` only when every parsed surface
    came from tree-sitter.
    """
    allowed = {e.lower() for e in extensions} if extensions else None
    surfaces: list[SurfaceHit] = []
    languages: set[str] = set()
    used_ts = 0
    used_regex = 0

    for path in files:
        if allowed is not None and path.suffix.lower() not in allowed:
            continue
        lang = language_of(path)
        if lang == "unknown":
            continue
        languages.add(lang)
        hits = _ts_surfaces(path, root)
        if hits:
            used_ts += len(hits)
        else:
            # Generic fallback if the adapter supplied no patterns for this file.
            fallback = list(patterns)
            if not fallback:
                fallback = [
                    ("function", r"\bdef\s+([A-Za-z_]\w*)"),
                    ("function", r"\bfn\s+([A-Za-z_]\w*)"),
                    ("function", r"\bfunc\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)"),
                    ("function", r"\bfunction\s+([A-Za-z_]\w*)"),
                    ("function", r"\bfun\s+([A-Za-z_]\w*)"),
                ]
            hits = _regex_surfaces(path, root, fallback)
            used_regex += len(hits)
        surfaces.extend(hits)
        if len(surfaces) >= max_surfaces:
            break

    # Stable de-duplication and ordering
    unique: dict[tuple[str, int, str], SurfaceHit] = {}
    for hit in surfaces:
        unique.setdefault((hit.file, hit.line, hit.name), hit)
    ordered = sorted(unique.values(), key=lambda h: (h.file, h.line, h.name))[:max_surfaces]

    if used_ts and not used_regex:
        method = "tree-sitter"
    elif used_ts and used_regex:
        method = "tree-sitter+regex"
    else:
        method = "regex"
    return ordered, method, sorted(languages)

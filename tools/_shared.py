"""Helpers shared by phase tool modules."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Sequence

from fsutil import TEXT_SUFFIXES, read_text, rel_to, walk_files
from runtime import ToolContext, ToolError


def resolve_files(
    ctx: ToolContext,
    paths: Sequence[str],
    exts: Iterable[str] | None = None,
    max_files: int = 5000,
) -> list[Path]:
    roots = [ctx.resolve(p) for p in paths] if paths else [ctx.workspace]
    return walk_files(roots, max_files=max_files, exts=exts)


def default_existing(ctx: ToolContext, candidates: Sequence[str]) -> list[str]:
    return [c for c in candidates if ctx.resolve(c).exists()]


def source_exts() -> set[str]:
    return {
        ".py", ".go", ".rs", ".sol", ".vy", ".move", ".cairo", ".ts", ".tsx",
        ".js", ".jsx", ".java", ".kt", ".cs", ".rb", ".php", ".swift", ".dart",
        ".c", ".h", ".cc", ".cpp", ".hpp", ".sh",
    }


def existing_ids(ctx: ToolContext, phase: int) -> set[str]:
    ids: set[str] = set()
    for obj in ctx.state._walk(ctx.state.sections(phase)):
        value = obj.get("id") if isinstance(obj, dict) else None
        if isinstance(value, str):
            ids.add(value)
    return ids


def next_id(existing: Iterable[str], prefix: str, width: int = 4) -> str:
    """Return ``PREFIX-000N`` one greater than the highest existing id."""
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    highest = 0
    for value in existing:
        match = pattern.match(value)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:0{width}d}"


def require_divergence(ctx: ToolContext, divergence_id: str) -> dict:
    divergence = ctx.state.find_divergence(divergence_id)
    if not divergence:
        known = [d.get("id") for d in ctx.state.divergences() if d.get("id")]
        raise ToolError(
            f"unknown divergence_id {divergence_id!r}; run Phase 3 first",
            details={"known_divergence_ids": known[:50]},
        )
    return divergence


def require_hypothesis(ctx: ToolContext, hypothesis_id: str) -> dict:
    hypothesis = ctx.state.find_hypothesis(hypothesis_id)
    if not hypothesis:
        known = [h.get("id") for h in ctx.state.hypotheses() if h.get("id")]
        raise ToolError(
            f"unknown hypothesis_id {hypothesis_id!r}; run Phase 4 first",
            details={"known_hypothesis_ids": known[:50]},
        )
    return hypothesis


def lines(path: Path, max_lines: int = 20000) -> list[str]:
    text = read_text(path)
    out = text.splitlines()
    return out[:max_lines]


def scan_files(
    files: Sequence[Path],
    root: Path,
    patterns: Sequence[tuple[str, re.Pattern[str]]],
    limit: int = 100,
    context: int = 0,
    prefer_file: str | None = None,
    prefer_line: int | None = None,
) -> list[dict]:
    hits: list[dict] = []
    for path in files:
        try:
            content = lines(path)
        except OSError:
            continue
        for idx, line in enumerate(content, start=1):
            for label, rx in patterns:
                if rx.search(line):
                    snippet = line.strip()[:400]
                    if context:
                        start = max(0, idx - 1 - context)
                        end = min(len(content), idx + context)
                        snippet = " | ".join(l.strip() for l in content[start:end])[:800]
                    hits.append(
                        {
                            "label": label,
                            "file": rel_to(path, root),
                            "line": idx,
                            "snippet": snippet,
                        }
                    )
                    break
            if len(hits) >= limit and prefer_line is None:
                return hits
    if prefer_file or prefer_line:
        def _rank(hit: dict) -> tuple[int, int]:
            file_miss = 0
            if prefer_file:
                needle = prefer_file.replace("\\", "/").lower()
                file_miss = 0 if needle in hit["file"].replace("\\", "/").lower() else 1
            dist = abs(int(hit["line"]) - prefer_line) if prefer_line is not None else 0
            return (file_miss, dist)
        hits.sort(key=_rank)
        hits = hits[:limit]
    elif len(hits) > limit:
        hits = hits[:limit]
    return hits


def entry_token(entry: str) -> str:
    """Reduce ``Contract.func(args)`` / ``GET /path`` to the function or route name.

    Types in parentheses are stripped first, so
    ``MarginClearinghouse.depositFor(address,uint256)`` becomes ``depositFor``,
    never ``uint256``.
    """
    entry = entry.strip()
    if " " in entry and entry.split(" ", 1)[0].isupper():
        entry = entry.split(" ", 1)[1]
    entry = entry.split("(", 1)[0]
    entry = re.split(r"[.:#/]", entry)[-1]
    return entry.strip()

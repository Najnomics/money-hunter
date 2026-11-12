"""Validation helpers shared by the whole pipeline.

In plain English: this file contains the small "fact checkers" that stop the
agent from making claims it cannot back up.  The most important one verifies
that a citation such as ``src/app.py:42`` really points at an existing line
inside the target folder.  Another converts a target's impact and trigger
into a severity using the same matrix everywhere.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from fsutil import walk_files

# Only source/document extensions are treated as citations.  This prevents
# URLs such as ``api.example.com:443`` from being mistaken for file paths.
_SOURCE_EXTS = (
    "py|go|rs|sol|vy|move|cairo|ts|tsx|js|jsx|java|kt|cs|rb|php|swift|dart|"
    "c|h|cc|cpp|hpp|sh|md|txt|json|jsonl|yaml|yml|toml|log|xml|html|sql|"
    "proto|graphql|gql"
)
CITE_RE = re.compile(
    rf"(?<![\w/])([A-Za-z0-9_./\\-]+\.(?:{_SOURCE_EXTS})):(\d+)(?:-(\d+))?"
)
FACT_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.\[\]]*):([a-z][a-z0-9_]*)$")
VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\[\]]*$")


def parse_cite(cite: str) -> tuple[str, int, int] | None:
    """Return ``(file, start_line, end_line)`` from a citation string."""
    match = CITE_RE.search(str(cite).strip().strip("`"))
    if not match:
        return None
    return match.group(1), int(match.group(2)), int(match.group(3) or match.group(2))


def validate_cite(workspace: Path, cite: str) -> dict[str, Any]:
    """Check that a citation resolves to real lines inside the workspace."""
    parsed = parse_cite(cite)
    if parsed is None:
        return {"cite": cite, "valid": False, "reason": "no path:line found"}
    file_name, start, end = parsed
    candidate = Path(file_name)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    try:
        resolved = candidate.resolve()
        resolved.relative_to(workspace.resolve())
    except (ValueError, OSError):
        return {"cite": cite, "valid": False, "reason": "citation escapes the target workspace"}
    if not resolved.is_file():
        # Free-text notes often name only the basename (e.g. ``withdraw.rs:297``).
        # Resolve it when the basename is unique inside the workspace.
        matches = [p for p in walk_files([workspace], max_files=20000) if p.name == candidate.name]
        suffix_matches = [p for p in matches if str(p.resolve()).endswith(file_name)]
        if len(suffix_matches) == 1:
            resolved = suffix_matches[0].resolve()
        elif len(matches) == 1:
            resolved = matches[0].resolve()
        else:
            reason = "cited file does not exist"
            if len(matches) > 1:
                reason = f"ambiguous basename {candidate.name!r}; use a workspace-relative path"
            return {"cite": cite, "valid": False, "reason": reason}
    try:
        line_count = len(resolved.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return {"cite": cite, "valid": False, "reason": "cited file cannot be read"}
    if start < 1 or start > line_count:
        return {"cite": cite, "valid": False, "reason": f"line {start} outside 1..{line_count}"}
    if end < start or end > line_count:
        return {"cite": cite, "valid": False, "reason": f"range ends outside 1..{line_count}"}
    return {
        "cite": cite,
        "valid": True,
        "file": file_name,
        "start": start,
        "end": end,
        "lines": line_count,
    }


def extract_cites(
    value: Any,
    skip_keys: Iterable[str] = ("markdown", "skeleton", "check_command"),
    focus_keys: Iterable[str] | None = None,
) -> list[str]:
    """Recursively pull every ``path:line`` citation out of a JSON-like object.

    When ``focus_keys`` is supplied, only strings under those field names are
    scanned.  This keeps free-text observations from being treated as evidence
    citations.
    """
    skip = set(skip_keys)
    focus = set(focus_keys) if focus_keys is not None else None
    found: list[str] = []

    def walk(item: Any, active: bool) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key in skip:
                    continue
                child_active = active or (focus is None) or (key in focus)
                walk(child, child_active)
        elif isinstance(item, list):
            for child in item:
                walk(child, active)
        elif isinstance(item, str) and (focus is None or active):
            for match in CITE_RE.finditer(item):
                found.append(match.group(0))

    walk(value, False)
    return list(dict.fromkeys(found))


def validate_cites(
    workspace: Path,
    value: Any,
    focus_keys: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate all citations in a payload and return a compact report."""
    cites = extract_cites(value, focus_keys=focus_keys)
    results = [validate_cite(workspace, cite) for cite in cites]
    invalid = [row for row in results if not row["valid"]]
    return {
        "checked": len(results),
        "valid": len(results) - len(invalid),
        "invalid": len(invalid),
        "details": invalid[:200],
    }


def severity_from(impact: str, trigger: str, reachability: str) -> str:
    """Turn impact x trigger into a severity, capped by reachability.

    This is deliberately arithmetic.  It stops the agent from calling a
    theoretical bug "critical" just because it sounds scary.
    """
    matrix = {
        "T": {"A": "critical", "K": "high", "R+": "high", "R-": "info"},
        "F+": {"A": "critical", "K": "high", "R+": "medium", "R-": "info"},
        "F-": {"A": "high", "K": "medium", "R+": "low", "R-": "info"},
        "C": {"A": "medium", "K": "low", "R+": "low", "R-": "info"},
    }
    severity = matrix.get(impact, {}).get(trigger, "info")
    if reachability == "unverified" and severity in {"critical", "high"}:
        return "medium"
    return severity


def fact_ok(fact: str, known_vars: set[str] | None = None) -> tuple[bool, str]:
    """Check the ``state_variable:condition`` format used by chains."""
    match = FACT_RE.match(str(fact).strip())
    if not match:
        return False, (
            "fact must look like state_variable:condition "
            "(lowercase snake_case condition, e.g. BALANCES:payout_sent)"
        )
    variable = match.group(1)
    if known_vars is not None and known_vars and variable not in known_vars:
        return False, f"state variable {variable!r} is not registered"
    return True, ""


def doc_text(path: Path, limit: int = 50) -> str:
    """Small helper used by tests and diagnostics."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[:limit])

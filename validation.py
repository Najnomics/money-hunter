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
        return {"cite": cite, "valid": False, "reason": "cited file does not exist"}
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


def extract_cites(value: Any, skip_keys: Iterable[str] = ("markdown", "skeleton", "check_command")) -> list[str]:
    """Recursively pull every ``path:line`` citation out of a JSON-like object."""
    skip = set(skip_keys)
    found: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key in skip:
                    continue
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, str):
            for match in CITE_RE.finditer(item):
                found.append(match.group(0))

    walk(value)
    return list(dict.fromkeys(found))


def validate_cites(workspace: Path, value: Any) -> dict[str, Any]:
    """Validate all citations in a payload and return a compact report."""
    cites = extract_cites(value)
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
        return False, "fact must look like state_variable:condition"
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

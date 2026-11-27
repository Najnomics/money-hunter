"""Phase 3 — Verify Divergence: model versus implementation.

In plain English: open the code and find where it disagrees with the model.
A divergence is a lead, not a finding.  Static analyzer hits are converted
into candidates with a file and line, never into findings directly.
"""
from __future__ import annotations

import fnmatch
import json
import re
import shutil
from pathlib import Path

from adapters import get_adapter
from adapters.base import StaticTool
from fsutil import read_text, rel_to, run_command, walk_files, write_text_atomic
from runtime import ToolContext, ToolSpec, ToolError, tool
from schemas.common import Confidence
from schemas.phase3 import (
    ASTMapInput,
    ASTMapOutput,
    Divergence,
    InventoryBatch,
    InventoryHit,
    InventoryInput,
    InventoryResult,
    PredictionDiffInput,
    PredictionDiffOutput,
    StaticSweepInput,
    StaticSweepOutput,
    Surface,
    ToolRun,
)
from tools._shared import entry_token, existing_ids, next_id, source_exts
from validation import validate_cite

AUTH_RE = re.compile(
    r"(authoriz|authentic|onlyOwner|onlyRole|hasRole|access[_-]?control|permission|"
    r"isAdmin|msg\.sender|require\([^)]*(owner|admin|role)|signature|verify)",
    re.I,
)
AUTH_BOUNDARY_RE = re.compile(r"(auth|role|admin|permission|privilege|owner|signer|session|token)", re.I)
SINK_WORDS = re.compile(
    r"(withdraw|transfer|mint|burn|sweep|execute|upgrade|\badmin\b|\bowner\b|pause|unpause|"
    r"delegate|approve|set[A-Z]|update|delete|destroy|kill|callback|"
    r"\bsettle\b|\bsettlement\b|liquidat)",
    re.I,
)
GETTER_OR_MODIFIER = re.compile(
    r"^(?:get|is|has|preview|simulate|quote|convertTo|total|balanceOf|only[A-Z])",
)
# `settlementAsset` / `settlementToken` contain "settle" as a substring; they are views.
VIEWISH_SETTLEMENT = re.compile(
    r"settlement(?:Asset|Token|Sidecar|Buffer)|onlySettlement",
    re.I,
)
UNDOCUMENTED_CAP = 200
SLITHER_RAN_CODES = {0, 1, 255}
UNMAPPED_KINDS = {"unmapped_critical_flow", "unmapped_flow"}

# Audit production behaviour, not the target's own tests.  A test named
# `test_withdraw` used to look like a value-sink entrypoint and flooded the map.
TEST_DIRS = {
    "test", "tests", "__tests__", "spec", "specs", "testdata", "fixtures",
    "mocks", "mock", "vendor", "third_party", "benchmarks", "examples",
}


def _is_test_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if parts & TEST_DIRS:
        return True
    name = path.name.lower()
    return (
        name.startswith("test_")
        or name.startswith("test-")
        or "_test." in name
        or ".test." in name
        or ".spec." in name
    )


def _scope_paths(ctx: ToolContext) -> list[str]:
    scope = ctx.state.section(0, "scope") or {}
    paths: list[str] = []
    for component in scope.get("components", []):
        if component.get("kind") in {"repo", "artifact"}:
            paths.extend(component.get("paths", []))
    return paths or ["."]


def _match_surfaces(entry: str, surfaces: list[Surface]) -> list[Surface]:
    """Match ``Contract.fn(types)`` to surfaces by function name, not ABI types.

    Splitting on the *last* ``(`` token used to turn
    ``MarginClearinghouse.depositFor(address,uint256)`` into ``uint256``.
    """
    token = entry_token(entry).lower()
    if not token:
        return []
    contract = ""
    head = entry.strip().split("(", 1)[0]
    if "." in head:
        contract = head.rsplit(".", 1)[0].split()[-1].lower()
    matches: list[Surface] = []
    for surface in surfaces:
        name = surface.name.lower()
        if name == token or name.endswith("." + token):
            matches.append(surface)
            continue
        if token.startswith("/") and surface.kind == "route" and name == token:
            matches.append(surface)
            continue
        if (
            contract
            and name == token
            and contract in surface.file.lower().replace("\\", "/")
        ):
            matches.append(surface)
    if len(matches) > 1 and contract:
        preferred = [m for m in matches if contract in m.file.lower().replace("\\", "/")]
        if preferred:
            return preferred
    return matches


def _alloc_divergence(existing: set[str], prefix: str = "DIV") -> str:
    new_id = next_id(existing, prefix)
    existing.add(new_id)
    return new_id


@tool(
    name="ast_divergence_mapper",
    phase=3,
    section="ast_map",
    summary="Map implementation surfaces and flag where they diverge from the Phase 2 mental model.",
    input_model=ASTMapInput,
    output_model=ASTMapOutput,
    tags=("ast", "divergence"),
)
def ast_divergence_mapper(ctx: ToolContext, inp: ASTMapInput) -> ASTMapOutput:
    raw_paths = inp.paths or _scope_paths(ctx)
    all_files = walk_files([ctx.resolve(p) for p in raw_paths], max_files=inp.max_files, exts=source_exts())
    files = all_files
    if not inp.include_tests:
        files = [f for f in files if not _is_test_path(f)]
    if inp.exclude_globs:
        files = [
            f for f in files
            if not any(fnmatch.fnmatch(rel_to(f, ctx.workspace), pattern) for pattern in inp.exclude_globs)
        ]
    filtered = len(all_files) - len(files)
    if not files:
        raise ToolError(
            "No production source files found to map.",
            details={"paths": raw_paths, "filtered_test_or_excluded": filtered},
        )

    hits, method, languages = ctx.adapter.surfaces(files, ctx.workspace, max_surfaces=3000)
    if not inp.include_tests:
        hits = [h for h in hits if not h.name.lower().startswith(("test_", "test"))]
    surfaces = [
        Surface(
            file=h.file,
            line=h.line,
            name=h.name,
            kind=h.kind,
            language=h.language,
            entry=h.entry,
            extractor=h.extractor,
        )
        for h in hits
    ]
    if inp.languages:
        wanted = {l.lower() for l in inp.languages}
        surfaces = [s for s in surfaces if s.language.lower() in wanted]

    model = ctx.state.section(2, "flows") or {}
    flows = model.get("flows", []) or []
    if inp.model_flows:
        wanted_flows = set(inp.model_flows)
        flows = [f for f in flows if f.get("id") in wanted_flows]

    existing = existing_ids(ctx, 3)
    divergences: list[Divergence] = []
    mapped: dict[str, list[str]] = {}

    for flow in flows:
        matches = _match_surfaces(str(flow.get("entry", "")), surfaces)
        if matches:
            mapped[flow["id"]] = [f"{m.file}:{m.line}" for m in matches]
        elif flow.get("critical"):
            divergences.append(
                Divergence(
                    id=_alloc_divergence(existing),
                    kind="unmapped_critical_flow",
                    flow_id=flow.get("id"),
                    expected=f"entrypoint `{flow.get('entry')}` for critical flow {flow.get('name')}",
                    observed="no matching implementation surface found",
                    confidence=Confidence.LOW,
                    status="candidate",
                    source_tool="ast_divergence_mapper",
                    evidence=["[DEDUCED] Phase 2 model vs Phase 3 surface inventory"],
                )
            )

        if flow.get("critical") and flow.get("trust_boundaries") and matches:
            boundary_text = " ".join(map(str, flow.get("trust_boundaries", [])))
            if AUTH_BOUNDARY_RE.search(boundary_text):
                surface = matches[0]
                path = ctx.resolve(surface.file)
                lines = read_text(path).splitlines()
                window = "\n".join(lines[surface.line - 1: surface.line + 60])
                if not AUTH_RE.search(window):
                    divergences.append(
                        Divergence(
                            id=_alloc_divergence(existing),
                            kind="possible_missing_check",
                            flow_id=flow.get("id"),
                            expected=f"trust boundary enforced: {boundary_text[:200]}",
                            observed="no authorization/validation pattern within 60 lines of the entrypoint",
                            file=surface.file,
                            line=surface.line,
                            confidence=Confidence.LOW,
                            status="candidate",
                            source_tool="ast_divergence_mapper",
                            evidence=[f"[CODE] {surface.file}:{surface.line}"],
                        )
                    )

    flow_tokens = [str(f.get("entry", "")).lower() for f in flows]
    undocumented = 0
    for surface in surfaces:
        if not surface.entry or undocumented >= UNDOCUMENTED_CAP:
            continue
        if GETTER_OR_MODIFIER.search(surface.name) or VIEWISH_SETTLEMENT.search(surface.name):
            continue
        if not SINK_WORDS.search(surface.name):
            continue
        if any(surface.name.lower() in token or entry_token(token) == surface.name.lower() for token in flow_tokens):
            continue
        divergences.append(
            Divergence(
                id=_alloc_divergence(existing),
                kind="undocumented_entrypoint",
                expected="entrypoint is described by the Phase 2 flow inventory",
                observed=f"surface `{surface.name}` ({surface.kind}) has a value-sink-shaped name but no model flow",
                file=surface.file,
                line=surface.line,
                confidence=Confidence.LOW,
                status="candidate",
                source_tool="ast_divergence_mapper",
                evidence=[f"[CODE] {surface.file}:{surface.line}"],
            )
        )
        undocumented += 1

    notes: list[str] = []
    if not flows:
        notes.append("Phase 2 has no flows; only surface inventory was produced.")
    if not surfaces:
        notes.append("No surfaces extracted. Check extensions or install tree-sitter-language-pack.")
    notes.append(f"Extracted {len(surfaces)} surface(s); {len(mapped)} flow(s) mapped to code.")
    if filtered:
        notes.append(
            f"Skipped {filtered} test/mock/fixture file(s); pass --include-tests true to map them."
        )

    return ASTMapOutput(
        surfaces=surfaces[:3000],
        mapped_flows=mapped,
        divergences=divergences,
        languages=languages,
        method=method,
        files_scanned=len(files),
        notes=notes,
    )


def _write_log(ctx: ToolContext, name: str, index: int, stdout: str, stderr: str) -> str:
    log_dir = ctx.state.apex_dir / "experiments" / "logs"
    path = log_dir / f"sweep-{name}-{index}.log"
    write_text_atomic(path, f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n")
    return rel_to(path, ctx.workspace)


def _parse_semgrep(stdout: str, ctx: ToolContext, max_findings: int) -> list[dict]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return []
    findings = []
    for item in payload.get("results", [])[:max_findings]:
        findings.append(
            {
                "rule": item.get("check_id", "semgrep"),
                "message": (item.get("extra", {}) or {}).get("message", ""),
                "severity": (item.get("extra", {}) or {}).get("severity", "warning"),
                "file": rel_to(ctx.resolve(item.get("path", "")), ctx.workspace),
                "line": (item.get("start", {}) or {}).get("line", 0),
            }
        )
    return findings


def _parse_bandit(stdout: str, ctx: ToolContext, max_findings: int) -> list[dict]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return []
    findings = []
    for item in payload.get("results", [])[:max_findings]:
        findings.append(
            {
                "rule": item.get("test_id", "bandit"),
                "message": item.get("issue_text", ""),
                "severity": item.get("issue_severity", "LOW"),
                "file": rel_to(ctx.resolve(item.get("filename", "")), ctx.workspace),
                "line": item.get("line_number", 0),
            }
        )
    return findings


def _parse_slither(stdout: str, ctx: ToolContext, max_findings: int) -> list[dict]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return []
    findings = []
    for item in (payload.get("results", {}) or {}).get("detectors", [])[:max_findings]:
        elements = item.get("elements", []) or []
        file_name = ""
        line = 0
        if elements:
            mapping = elements[0].get("source_mapping", {}) or {}
            file_name = mapping.get("filename_relative", "") or mapping.get("filename_absolute", "")
            lines = mapping.get("lines", []) or [0]
            line = lines[0] if lines else 0
        findings.append(
            {
                "rule": item.get("check", "slither"),
                "message": item.get("description", "")[:500],
                "severity": item.get("impact", "Medium"),
                "file": file_name,
                "line": line,
            }
        )
    return findings


def _parse_clippy(stdout: str, ctx: ToolContext, max_findings: int) -> list[dict]:
    findings = []
    for line in stdout.splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("reason") != "compiler-message":
            continue
        message = row.get("message", {}) or {}
        level = message.get("level")
        if level not in {"warning", "error"}:
            continue
        spans = message.get("spans", []) or []
        file_name = spans[0].get("file_name", "") if spans else ""
        line_no = spans[0].get("line_start", 0) if spans else 0
        findings.append(
            {
                "rule": (message.get("code") or {}).get("code", "clippy") if isinstance(message.get("code"), dict) else "clippy",
                "message": message.get("message", ""),
                "severity": level,
                "file": file_name,
                "line": line_no,
            }
        )
        if len(findings) >= max_findings:
            break
    return findings


PARSERS = {
    "semgrep": _parse_semgrep,
    "bandit": _parse_bandit,
    "slither": _parse_slither,
    "clippy": _parse_clippy,
}


def _build_command(
    tool: StaticTool,
    paths: list[str],
    config: str | None,
    json_out: Path | None = None,
) -> tuple[list[str] | None, str | None, Path]:
    if tool.requires_config and not config:
        return None, "tool requires --semgrep-config (local rules); refusing to fetch rules implicitly", Path(".")
    target_paths = [str(Path(p).resolve()) for p in paths]
    if not target_paths:
        return None, "no target paths", Path(".")
    if tool.single_target:
        target_paths = [target_paths[0]]

    args: list[str] = []
    for arg in tool.args:
        if arg == "{paths}":
            args.extend(target_paths)
        elif arg == "{config}":
            args.append(config or "")
        elif arg == "{json_out}":
            args.append(str(json_out) if json_out is not None else "-")
        elif "{addresses}" in arg:
            return None, "tool requires named addresses; configure the workspace manually", Path(".")
        else:
            args.append(arg)

    cwd = Path(target_paths[0]) if tool.cwd_target else Path(".")
    if tool.cwd_target and not cwd.is_dir():
        cwd = Path(".")
    return [tool.binary, *args], None, cwd


@tool(
    name="targeted_static_sweep",
    phase=3,
    section="static_sweep",
    summary="Run the profile's scoped static analysers and convert raw findings into divergences.",
    input_model=StaticSweepInput,
    output_model=StaticSweepOutput,
    tags=("static-analysis", "divergence"),
)
def targeted_static_sweep(ctx: ToolContext, inp: StaticSweepInput) -> StaticSweepOutput:
    adapter = get_adapter(ctx.state.target_profile)
    tools = list(adapter.static_tools)
    if inp.tools:
        wanted = {t.lower() for t in inp.tools}
        tools = [t for t in tools if t.name.lower() in wanted]
        missing = wanted - {t.name.lower() for t in adapter.static_tools}
        if missing:
            raise ToolError(
                f"tools not available for profile {adapter.profile.value}: {sorted(missing)}",
                details={"available": [t.name for t in adapter.static_tools]},
            )

    raw_paths = inp.paths or _scope_paths(ctx)
    paths = [str(ctx.resolve(p)) for p in raw_paths]
    existing = existing_ids(ctx, 3)
    runs: list[ToolRun] = []
    divergences: list[Divergence] = []
    notes: list[str] = []

    for index, static_tool in enumerate(tools, start=1):
        if not shutil.which(static_tool.binary):
            runs.append(
                ToolRun(
                    tool=static_tool.name,
                    status="unavailable",
                    reason=f"`{static_tool.binary}` not on PATH",
                )
            )
            continue

        json_out = None
        if "{json_out}" in static_tool.args:
            sweep_dir = ctx.state.apex_dir / "sweep"
            sweep_dir.mkdir(parents=True, exist_ok=True)
            json_out = sweep_dir / f"{static_tool.name}-{index}.json"
        command, reason, cwd = _build_command(static_tool, paths, inp.semgrep_config, json_out=json_out)
        if command is None:
            runs.append(ToolRun(tool=static_tool.name, status="skipped", reason=reason))
            continue
        if str(cwd) == ".":
            cwd = ctx.workspace
        else:
            cwd = ctx.resolve(cwd)

        result = run_command(command, cwd=cwd, timeout_seconds=inp.timeout_seconds)
        log_path = _write_log(ctx, static_tool.name, index, result.stdout, result.stderr)
        ran_codes = SLITHER_RAN_CODES if static_tool.name == "slither" else {0, 1}
        status = "ran" if not result.timed_out and result.returncode in ran_codes else "error"
        if result.timed_out:
            status = "timeout"

        parser = PARSERS.get(static_tool.name)
        payload = result.stdout
        if json_out is not None and json_out.exists() and json_out.stat().st_size > 0:
            payload = read_text(json_out, max_bytes=50_000_000)
        raw_findings = parser(payload, ctx, inp.max_findings) if parser else []
        for finding in raw_findings:
            severity = str(finding.get("severity", "low")).lower()
            confidence = Confidence.HIGH if severity in {"critical", "high", "error"} else Confidence.MEDIUM
            divergences.append(
                Divergence(
                    id=_alloc_divergence(existing, "DIV"),
                    kind="static_finding",
                    expected="no structural anomaly at this location",
                    observed=f"{finding.get('rule')}: {finding.get('message', '')[:300]}",
                    file=finding.get("file") or None,
                    line=int(finding.get("line") or 0) or None,
                    confidence=confidence,
                    status="candidate",
                    source_tool=static_tool.name,
                    evidence=[
                        f"[SEARCHED] {static_tool.name}",
                        f"[CODE] {finding.get('file')}:{finding.get('line')}",
                    ],
                )
            )

        runs.append(
            ToolRun(
                tool=static_tool.name,
                status=status,
                command=command,
                returncode=result.returncode,
                findings=len(raw_findings),
                log_path=log_path,
                reason=result.stderr[:300] if status == "error" and result.stderr else None,
            )
        )

    if not tools:
        notes.append(f"Profile {adapter.profile.value} has no static tools configured.")
    notes.append(
        "Static findings are candidates, not findings: Phase 4 must attach each to a divergence and hypothesis."
    )

    return StaticSweepOutput(
        runs=runs,
        divergences=divergences,
        findings_total=sum(run.findings for run in runs),
        notes=notes,
    )


@tool(
    name="diff_prediction",
    phase=3,
    section="prediction_diff",
    summary="Compare a blind prediction with what the code actually does, and emit a divergence.",
    input_model=PredictionDiffInput,
    output_model=PredictionDiffOutput,
    tags=("predict-blind", "divergence"),
)
def diff_prediction(ctx: ToolContext, inp: PredictionDiffInput) -> PredictionDiffOutput:
    allowed = {"model-wrong", "design-wrong", "design-choice"}
    if inp.verdict not in allowed:
        raise ToolError(f"verdict must be one of {sorted(allowed)}")
    predictions = ctx.state.section(2, "predictions") or {}
    if inp.flow_id not in predictions:
        raise ToolError(f"no blind prediction for flow {inp.flow_id!r}; run record_prediction first")
    if inp.file:
        cite = f"{inp.file}:{inp.line or 1}"
        result = validate_cite(ctx.workspace, cite)
        if not result["valid"]:
            raise ToolError(f"observed cite does not resolve: {result['reason']}")

    if inp.verdict == "design-choice":
        return PredictionDiffOutput(
            flow_id=inp.flow_id,
            verdict=inp.verdict,
            divergences=[],
            notes=["Design choice recorded; it is not a hypothesis unless new evidence contradicts it."],
        )

    existing = existing_ids(ctx, 3)
    divergence = Divergence(
        id=next_id(existing, "DIV"),
        kind="prediction_design_wrong" if inp.verdict == "design-wrong" else "prediction_model_wrong",
        flow_id=inp.flow_id,
        expected=inp.expected,
        observed=inp.observed,
        file=inp.file,
        line=inp.line,
        confidence=inp.confidence,
        status="candidate",
        source_tool="diff_prediction",
        evidence=[
            "[CODE] " + (f"{inp.file}:{inp.line}" if inp.file else "prediction diff"),
            f"[DEDUCED] {inp.why or inp.verdict}",
        ],
    )
    note = "design-wrong is high priority: the code contradicts its own stated intent."
    return PredictionDiffOutput(
        flow_id=inp.flow_id,
        verdict=inp.verdict,
        divergences=[divergence],
        notes=[note],
    )


@tool(
    name="sweep_inventory",
    phase=3,
    section="sweep_inventory",
    summary="Run a saved regex rule, save its hits, and diff against the previous inventory.",
    input_model=InventoryInput,
    output_model=InventoryBatch,
    write_mode="append",
    tags=("inventory", "re-audit"),
)
def sweep_inventory(ctx: ToolContext, inp: InventoryInput) -> InventoryBatch:
    flags = 0 if inp.case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(inp.pattern, flags)
    except re.error as exc:
        raise ToolError(f"invalid regex: {exc}") from exc

    exts = {e if e.startswith(".") else f".{e}" for e in inp.extensions} or source_exts()
    roots = inp.paths or ["."]
    files = walk_files([ctx.resolve(p) for p in roots], max_files=inp.max_files, exts=exts)
    hits: list[InventoryHit] = []
    for path in files:
        for idx, line in enumerate(read_text(path).splitlines(), start=1):
            if pattern.search(line):
                hits.append(
                    InventoryHit(
                        file=rel_to(path, ctx.workspace),
                        line=idx,
                        expression=line.strip()[:300],
                    )
                )
    if len(hits) > 2000:
        hits = hits[:2000]

    safe_rule = re.sub(r"[^A-Za-z0-9_.-]+", "-", inp.rule_name).strip("-") or "rule"
    baseline = ctx.state.apex_dir / "sweep" / f"inventory-{safe_rule}.txt"
    previous: dict[tuple[str, str], int] = {}
    if baseline.exists():
        for line in read_text(baseline).splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                try:
                    previous[(parts[0], parts[1])] = int(parts[2])
                except ValueError:
                    continue

    current = {(hit.file, hit.expression): hit.line for hit in hits}
    new_keys = set(current) - set(previous)
    removed_keys = set(previous) - set(current)
    moved_keys = {key for key in set(current) & set(previous) if current[key] != previous[key]}
    unchanged = len(set(current) & set(previous)) - len(moved_keys)

    baseline.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(
        baseline,
        "\n".join(f"{hit.file} | {hit.expression} | {hit.line}" for hit in hits) + "\n",
    )
    result = InventoryResult(
        rule=safe_rule,
        total=len(hits),
        new=len(new_keys),
        removed=len(removed_keys),
        moved=len(moved_keys),
        unchanged=unchanged,
        baseline_path=rel_to(baseline, ctx.workspace),
        hits=hits,
        notes=[
            "Line numbers are metadata; identity is (file, matched expression).",
            "NEW expressions are leads. REMOVED expressions may be fixes worth checking.",
        ],
    )
    return InventoryBatch(items=[result])


TOOLS: list[ToolSpec] = [  # type: ignore[list-item]
    ast_divergence_mapper,
    targeted_static_sweep,
    diff_prediction,
    sweep_inventory,
]

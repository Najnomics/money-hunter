"""Phase 5 — Experiment: sandbox provisioning and invariant execution.

In plain English: build a safe local copy of the target, run the specific
test that the hypothesis predicts, and capture the output.  A test that was
written but not run is explicitly labelled "prepared" and is not evidence.
"""
from __future__ import annotations

import re
import shlex
from pathlib import Path

from fsutil import rel_to, run_command, write_text_atomic
from runtime import ToolContext, ToolSpec, ToolError, tool
from schemas.phase5 import (
    CartesianQueueInput,
    ExecuteQueuedInput,
    Experiment,
    ExperimentBatch,
    InvariantTestInput,
    RecordExperimentInput,
    SandboxInput,
    SandboxOutput,
)
from tools._shared import existing_ids, next_id, require_hypothesis
from tools.gate_policy import distinguishing_scaffold, infer_experiment_class


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:60] or "experiment"


@tool(
    name="sandbox_forge",
    phase=5,
    section="sandbox",
    summary="Provision an isolated local harness matching the TargetProfile (Docker/Foundry/Anchor/Move/process).",
    input_model=SandboxInput,
    output_model=SandboxOutput,
    tags=("sandbox", "provision"),
)
def sandbox_forge(ctx: ToolContext, inp: SandboxInput) -> SandboxOutput:
    adapter = ctx.adapter
    base = Path(inp.out_dir) if inp.out_dir else Path(".apex") / "sandbox" / _slug(inp.service)
    destination = base if base.is_absolute() else ctx.workspace / base
    destination.mkdir(parents=True, exist_ok=True)

    templates = adapter.sandbox_files(inp.service)
    written: list[str] = []
    for relative, content in templates.items():
        target = destination / relative
        write_text_atomic(target, content)
        if target.suffix == ".sh":
            target.chmod(0o755)
        written.append(rel_to(target, ctx.workspace))

    instructions = adapter.sandbox_instructions()
    if inp.ports:
        instructions += f" Declared ports: {', '.join(inp.ports)} (bind to localhost only)."
    if inp.base_image:
        instructions += f" Base image override requested: {inp.base_image}."

    return SandboxOutput(
        directory=rel_to(destination, ctx.workspace),
        files=sorted(written),
        profile=adapter.profile.value,
        kind=adapter.sandbox_kind,
        instructions=instructions,
        notes=[
            "No network, no live targets. Experiments run only inside this harness.",
            "Every run must leave stdout/stderr under .apex/experiments/.",
        ],
    )


def _scaffold(hypothesis: dict) -> str:
    variant = str(hypothesis.get("variant") or "")
    fn, var = "", ""
    if "::" in variant:
        fn, var = variant.split("::", 1)
    sink = str(hypothesis.get("sink") or var or "value")
    return distinguishing_scaffold(fn or "mutator", sink, str(hypothesis.get("id") or ""))


@tool(
    name="invariant_tester",
    phase=5,
    section="experiments",
    summary="Write and optionally execute a local invariant test for a Phase 4 hypothesis.",
    input_model=InvariantTestInput,
    output_model=ExperimentBatch,
    write_mode="append",
    tags=("experiment", "fuzz"),
)
def invariant_tester(ctx: ToolContext, inp: InvariantTestInput) -> ExperimentBatch:
    hypothesis = require_hypothesis(ctx, inp.hypothesis_id)
    experiment_id = next_id(existing_ids(ctx, 5), "E")
    directory = ctx.state.apex_dir / "experiments" / f"{_slug(inp.name)}-{experiment_id.lower()}"
    directory.mkdir(parents=True, exist_ok=True)

    test_source = inp.test_code if inp.test_code else _scaffold(hypothesis)
    declared_class = infer_experiment_class(
        declared=inp.experiment_class,
        observation="",
        command=inp.command or "",
        test_code=test_source,
    )
    test_path = directory / "test_invariant.py"
    write_text_atomic(test_path, test_source)

    status = "prepared"
    returncode = None
    stdout_path = None
    stderr_path = None
    observation = ""
    verdict = "pending"

    if inp.execute:
        if not inp.command:
            raise ToolError("execute=true requires --command")
        args = shlex.split(inp.command)
        result = run_command(args, cwd=ctx.workspace, timeout_seconds=inp.timeout_seconds)
        returncode = result.returncode
        stdout_file = directory / "stdout.log"
        stderr_file = directory / "stderr.log"
        write_text_atomic(stdout_file, result.stdout)
        write_text_atomic(stderr_file, result.stderr)
        stdout_path = rel_to(stdout_file, ctx.workspace)
        stderr_path = rel_to(stderr_file, ctx.workspace)
        status = "ran"
        head = (result.stdout or result.stderr or "").strip().splitlines()
        observation = (
            f"exit={result.returncode} timed_out={result.timed_out}; "
            + (" | ".join(head[:5])[:800] if head else "no output")
        )
        if result.timed_out:
            verdict = "inconclusive"
        else:
            verdict = "needs-review"
    else:
        observation = (
            "Execution disabled. Test written but NOT run; this experiment provides no evidence until "
            "it is executed and its logs captured."
        )

    experiment = Experiment(
        id=experiment_id,
        hypothesis_id=inp.hypothesis_id,
        kind="invariant_test",
        status=status,
        command=inp.command,
        artifact=rel_to(test_path, ctx.workspace),
        returncode=returncode,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        observation=observation,
        verdict=verdict,
        experiment_class=declared_class,
    )
    notes = []
    if not inp.execute:
        notes.append("Dry run: pass --execute true with --command to produce evidence.")
    if declared_class in {"happy-path", "code-fact"}:
        notes.append(
            f"experiment_class={declared_class} is not a Gate 3 pass/kill. "
            "Run the distinguishing attack (attacker path, adversarial ordering, first-tick/zero-state)."
        )
    return ExperimentBatch(items=[experiment], notes=notes)


@tool(
    name="record_experiment",
    phase=5,
    section="experiments",
    summary="Record an executed experiment and its captured evidence with a verdict.",
    input_model=RecordExperimentInput,
    output_model=ExperimentBatch,
    write_mode="append",
    tags=("experiment", "evidence"),
)
def record_experiment(ctx: ToolContext, inp: RecordExperimentInput) -> ExperimentBatch:
    require_hypothesis(ctx, inp.hypothesis_id)
    allowed = {"confirmed", "refuted", "inconclusive", "pending"}
    if inp.verdict not in allowed:
        raise ToolError(f"verdict must be one of {sorted(allowed)}")

    output = Path(inp.output_path) if inp.output_path else None
    if output is not None and not output.is_absolute():
        output = ctx.workspace / output
    if inp.verdict in {"confirmed", "refuted"}:
        if output is None or not output.exists() or output.stat().st_size == 0:
            raise ToolError(
                "confirmed/refuted experiments require a non-empty --output-path with captured evidence."
            )

    test_code = ""
    if output and output.exists() and output.suffix in {".py", ".sol", ".t.sol", ".rs", ".log", ".txt"}:
        try:
            test_code = output.read_text(encoding="utf-8", errors="replace")[:8000]
        except OSError:
            test_code = ""
    klass = infer_experiment_class(
        declared=inp.experiment_class,
        observation=inp.observation,
        command=inp.command,
        test_code=test_code,
    )
    verdict = inp.verdict
    notes: list[str] = []
    if verdict in {"confirmed", "refuted"}:
        if klass in {"happy-path", "code-fact"}:
            raise ToolError(
                "Gate 3 must run the distinguishing attack PoC (attacker path, adversarial "
                "ordering, first-tick/zero-state). A happy-path or code-fact check is not a "
                f"G3 pass/kill (got {klass})."
            )
        if klass != "distinguishing":
            notes.append(
                "Gate 3 pass/kill requires a distinguishing attack. "
                "Recorded as inconclusive: experiment_class is not distinguishing."
            )
            verdict = "inconclusive"

    artifact = rel_to(output, ctx.workspace) if output and output.exists() else inp.output_path
    experiment = Experiment(
        id=next_id(existing_ids(ctx, 5), "E"),
        hypothesis_id=inp.hypothesis_id,
        kind="recorded",
        status="ran",
        command=inp.command,
        artifact=artifact,
        stdout_path=artifact,
        observation=inp.observation,
        verdict=verdict,
        experiment_class=klass,
    )
    return ExperimentBatch(items=[experiment], notes=notes)


@tool(
    name="queue_cartesian_g3",
    phase=5,
    section="experiments",
    summary="Materialize the top-N ranked public/external mutator × value-sink pairs as distinguishing G3 tests.",
    input_model=CartesianQueueInput,
    output_model=ExperimentBatch,
    write_mode="none",
    tags=("experiment", "queue"),
)
def queue_cartesian_g3(ctx: ToolContext, inp: CartesianQueueInput) -> ExperimentBatch:
    if inp.execute:
        raise ToolError(
            "queue_cartesian_g3 never executes. Record a distinguishing attack with record_experiment."
        )
    from tools.hypothesis_seed import queue_distinguishing_g3

    queued = queue_distinguishing_g3(ctx, max_queue=inp.max_queue, tool="queue_cartesian_g3")
    # Experiments were already appended; return them as a batch without a second write.
    items = [
        Experiment(
            id=str(row.get("experiment_id") or ""),
            hypothesis_id=str(row.get("hypothesis_id") or ""),
            kind="distinguishing_g3",
            status="prepared",
            observation=str(row.get("test_plan") or ""),
            verdict="pending",
            experiment_class="distinguishing",
        )
        for row in queued
    ]
    notes = [
        f"Queued {len(items)} distinguishing G3 test(s) from ranked public mutator × value-sink pairs. "
        "Internal `_` functions are excluded."
    ]
    if not items:
        notes.append("Nothing queued. Run never_generated_check first so pairs have hypotheses.")
    return ExperimentBatch(items=items, notes=notes)


def _pair_from_experiment(exp: dict, hyp: dict | None) -> tuple[str, str, str]:
    from tools.g3_harness import parse_pair

    blob = " ".join(
        [
            str(exp.get("observation") or ""),
            str((hyp or {}).get("variant") or ""),
            str((hyp or {}).get("title") or ""),
            str((hyp or {}).get("statement") or ""),
        ]
    )
    fn, var = parse_pair(blob)
    if not fn and "::" in str((hyp or {}).get("variant") or ""):
        fn, var = str(hyp.get("variant")).split("::", 1)
    family = str((hyp or {}).get("family") or "")
    return fn, var, family


@tool(
    name="execute_queued_g3",
    phase=5,
    section="experiments",
    summary="Execute prepared distinguishing G3 tests with forge (local). Never submits.",
    input_model=ExecuteQueuedInput,
    output_model=ExperimentBatch,
    write_mode="append",
    tags=("experiment", "execute"),
)
def execute_queued_g3(ctx: ToolContext, inp: ExecuteQueuedInput) -> ExperimentBatch:
    if not inp.execute:
        raise ToolError("execute_queued_g3 requires execute=true. Prepared tests are not evidence.")
    from tools.g3_harness import run_distinguishing

    hyps = {str(h.get("id")): h for h in ctx.state.hypotheses() if h.get("id")}
    queued = [
        e
        for e in ctx.state.experiments()
        if str(e.get("kind") or "").startswith("distinguishing")
        and e.get("status") in {"prepared", "pending"}
    ]
    jobs: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for exp in queued[: inp.max_run]:
        hyp = hyps.get(str(exp.get("hypothesis_id") or ""))
        fn, var, family = _pair_from_experiment(exp, hyp)
        hid = str(exp.get("hypothesis_id") or "")
        key = (hid, fn, var)
        if key in seen:
            continue
        seen.add(key)
        jobs.append((hid, family, fn, var))

    if inp.include_named_open:
        for hyp in hyps.values():
            hid = str(hyp.get("id") or "")
            family = str(hyp.get("family") or "")
            variant = str(hyp.get("variant") or "")
            fn, var = ("", "")
            if "::" in variant:
                fn, var = variant.split("::", 1)
            else:
                fn, var = _pair_from_experiment({}, hyp)[:2]
            if not family and not (fn and var):
                continue
            key = (hid, fn, var)
            if key in seen:
                continue
            seen.add(key)
            jobs.append((hid, family, fn, var))

    jobs = jobs[: inp.max_run]
    reserved: set[str] = set(existing_ids(ctx, 5))
    items: list[Experiment] = []
    notes: list[str] = ["Never submit. forge evidence is local-only."]
    for hid, family, fn, var in jobs:
        if hid not in hyps:
            notes.append(f"skip {fn}::{var}: hypothesis {hid} missing")
            continue
        if inp.command:
            args = shlex.split(inp.command)
            result_cmd = run_command(args, cwd=ctx.workspace, timeout_seconds=inp.timeout_seconds)
            result = {
                "ok": result_cmd.returncode == 0 and not result_cmd.timed_out,
                "returncode": result_cmd.returncode,
                "stdout": result_cmd.stdout,
                "stderr": result_cmd.stderr,
                "command": inp.command,
                "contract": "",
                "timed_out": result_cmd.timed_out,
            }
        else:
            result = run_distinguishing(
                family=family, function=fn, var=var, timeout_seconds=inp.timeout_seconds
            )
        experiment_id = next_id(reserved, "E")
        reserved.add(experiment_id)
        directory = ctx.state.apex_dir / "experiments" / f"run-{experiment_id.lower()}"
        directory.mkdir(parents=True, exist_ok=True)
        stdout_file = directory / "stdout.log"
        write_text_atomic(stdout_file, result.get("stdout") or "")
        write_text_atomic(directory / "stderr.log", result.get("stderr") or "")
        observation = (
            f"attacker forge {result.get('contract') or ''} {fn}::{var} "
            f"exit={result.get('returncode')} "
            + ("PASS distinguishing" if result.get("ok") else "FAIL/inconclusive")
        )
        verdict = "confirmed" if result.get("ok") else "inconclusive"
        if hid not in hyps:
            notes.append(f"no hypothesis id for {fn}::{var}; recorded against {hid}")
        items.append(
            Experiment(
                id=experiment_id,
                hypothesis_id=hid if hid in hyps else (hid or "H-0001"),
                kind="distinguishing_g3",
                status="ran",
                command=str(result.get("command") or ""),
                artifact=rel_to(stdout_file, ctx.workspace),
                stdout_path=rel_to(stdout_file, ctx.workspace),
                returncode=int(result.get("returncode") or 0),
                observation=observation,
                verdict=verdict,
                experiment_class="distinguishing",
            )
        )
    notes.append(f"Executed {len(items)} distinguishing forge test(s). confirmed={sum(1 for i in items if i.verdict=='confirmed')}.")
    return ExperimentBatch(items=items, notes=notes)


TOOLS: list[ToolSpec] = [  # type: ignore[list-item]
    sandbox_forge,
    invariant_tester,
    record_experiment,
    queue_cartesian_g3,
    execute_queued_g3,
]

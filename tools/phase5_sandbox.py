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
    Experiment,
    ExperimentBatch,
    InvariantTestInput,
    RecordExperimentInput,
    SandboxInput,
    SandboxOutput,
)
from tools._shared import existing_ids, next_id, require_hypothesis


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
    statement = str(hypothesis.get("statement", "")).strip()
    prediction = str(hypothesis.get("falsifiable_prediction", "")).strip()
    return (
        '"""Auto-generated invariant test scaffold.\n\n'
        f"Hypothesis: {hypothesis.get('id')}\n"
        f"{statement}\n\n"
        f"Prediction: {prediction}\n"
        '"""\n\n'
        "import pytest\n\n\n"
        "def test_invariant_scaffold():\n"
        "    # TODO: replace with a real property-based test derived from the prediction.\n"
        "    # Use hypothesis or the profile's native test framework.\n"
        "    assert True  # placeholder — this is NOT evidence\n"
    )


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
    )
    notes = []
    if not inp.execute:
        notes.append("Dry run: pass --execute true with --command to produce evidence.")
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
        verdict=inp.verdict,
    )
    return ExperimentBatch(items=[experiment])


TOOLS: list[ToolSpec] = [sandbox_forge, invariant_tester, record_experiment]  # type: ignore[list-item]

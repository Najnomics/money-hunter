"""Phase 2 — Mental model construction.

This phase is where the agent writes down what it *expects* the system to do
before it reads the implementation.  The extra tools here make that model
machine-checkable: named state variables, named impact sinks, and blind
predictions written from signatures only.
"""
from __future__ import annotations

import re

from fsutil import now_iso, rel_to, write_text_atomic
from runtime import ToolContext, ToolSpec, ToolError, tool
from schemas.phase2 import (
    DefineInvariantsInput,
    DefineInvariantsOutput,
    MapFlowsInput,
    MapFlowsOutput,
    Invariant,
    PredictionInput,
    PredictionOutput,
    PredictionRecord,
    Signature,
    SinksInput,
    SinksOutput,
    SkeletonInput,
    SkeletonOutput,
    StateVariable,
    StateVocabInput,
    StateVocabOutput,
)
from tools._shared import resolve_files, source_exts
from validation import VAR_RE, validate_cite


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for value in values:
        if value in seen and value not in dupes:
            dupes.append(value)
        seen.add(value)
    return dupes


@tool(
    name="map_state_flows",
    phase=2,
    section="flows",
    summary="Record actors, expected state transitions, trust boundaries, and critical flows.",
    input_model=MapFlowsInput,
    output_model=MapFlowsOutput,
    tags=("model", "flows"),
)
def map_state_flows(ctx: ToolContext, inp: MapFlowsInput) -> MapFlowsOutput:
    duplicates = _duplicates([f.id for f in inp.flows])
    if duplicates:
        raise ValueError(f"duplicate flow ids: {duplicates}")

    warnings: list[str] = []
    critical_flows: list[str] = []
    for flow in inp.flows:
        if flow.critical:
            critical_flows.append(flow.id)
            if not flow.value_sinks and not flow.trust_boundaries:
                warnings.append(
                    f"Flow {flow.id} is marked critical but has no value sink or trust boundary."
                )
        if not flow.entry:
            warnings.append(f"Flow {flow.id} has an empty entrypoint.")
        if flow.actor and inp.actors and flow.actor not in {a.id for a in inp.actors}:
            warnings.append(f"Flow {flow.id} references unknown actor {flow.actor!r}.")

    if not inp.flows:
        warnings.append("No flows mapped. Phase 3 has nothing to verify against.")
    if not critical_flows and inp.flows:
        warnings.append("No flow is tagged CRITICAL; predict-blind depth has no target.")

    return MapFlowsOutput(
        actors=inp.actors,
        flows=inp.flows,
        state_variables=inp.state_variables,
        entrypoints=inp.entrypoints,
        critical_flows=critical_flows,
        warnings=warnings,
    )


@tool(
    name="define_invariants",
    phase=2,
    section="invariants",
    summary="List falsifiable mathematical, economic, authorization, and state invariants.",
    input_model=DefineInvariantsInput,
    output_model=DefineInvariantsOutput,
    tags=("model", "invariants"),
)
def define_invariants(ctx: ToolContext, inp: DefineInvariantsInput) -> DefineInvariantsOutput:
    duplicates = _duplicates([i.id for i in inp.invariants])
    if duplicates:
        raise ValueError(f"duplicate invariant ids: {duplicates}")

    warnings: list[str] = []
    for invariant in inp.invariants:
        if len(invariant.statement.strip()) < 8:
            warnings.append(f"Invariant {invariant.id} is too short to be falsifiable.")
        if not invariant.applies_to:
            warnings.append(f"Invariant {invariant.id} does not reference a flow id.")

    classes = sorted({i.category for i in inp.invariants})
    if len(inp.invariants) < 3:
        warnings.append("Fewer than 3 invariants. Phase 5 fuzzing will have weak oracles.")

    return DefineInvariantsOutput(
        invariants=[Invariant(**i.model_dump()) for i in inp.invariants],
        classes=classes,
        warnings=warnings,
    )


def _flow_map(ctx: ToolContext) -> dict[str, dict]:
    flows = (ctx.state.section(2, "flows") or {}).get("flows", [])
    return {str(flow.get("id")): flow for flow in flows if flow.get("id")}


@tool(
    name="define_state_vocabulary",
    phase=2,
    section="state_vocab",
    summary="Register the variables that outlive a step, so facts cannot drift between workers.",
    input_model=StateVocabInput,
    output_model=StateVocabOutput,
    tags=("model", "state"),
)
def define_state_vocabulary(ctx: ToolContext, inp: StateVocabInput) -> StateVocabOutput:
    warnings: list[str] = []
    seen: set[str] = set()
    for state in inp.states:
        if not VAR_RE.match(state.var):
            raise ToolError(f"invalid state variable {state.var!r}; use code identifiers such as orders.total")
        if state.var in seen:
            raise ToolError(f"duplicate state variable {state.var!r}")
        seen.add(state.var)
        if state.file:
            result = validate_cite(ctx.workspace, state.file)
            if not result["valid"]:
                raise ToolError(f"state {state.var}: {state.file} does not resolve: {result['reason']}")
    if not inp.states:
        warnings.append("No state variables registered. Chain facts will have nothing to bind to.")
    return StateVocabOutput(states=inp.states, warnings=warnings)


@tool(
    name="define_sinks",
    phase=2,
    section="sinks",
    summary="Register where an attacker wants to end up: value, freeze, privacy, or correctness.",
    input_model=SinksInput,
    output_model=SinksOutput,
    tags=("model", "sinks"),
)
def define_sinks(ctx: ToolContext, inp: SinksInput) -> SinksOutput:
    known = {
        str(state.get("var"))
        for state in (ctx.state.section(2, "state_vocab") or {}).get("states", [])
        if state.get("var")
    }
    warnings: list[str] = []
    seen: set[str] = set()
    for sink in inp.sinks:
        if sink.id in seen:
            raise ToolError(f"duplicate sink id {sink.id!r}")
        seen.add(sink.id)
        variables = [sink.var] if sink.var else list(sink.vars)
        variables = [v for v in variables if v]
        if not variables:
            raise ToolError(f"sink {sink.id}: provide var or vars")
        if len(variables) > 1 and not (sink.expr or "").strip():
            raise ToolError(f"sink {sink.id}: multi-variable sinks need an expr")
        if known:
            unknown = [v for v in variables if v not in known]
            if unknown:
                warnings.append(f"sink {sink.id}: variables not in state_vocab: {unknown}")
    return SinksOutput(sinks=inp.sinks, warnings=warnings)


@tool(
    name="make_blind_skeleton",
    phase=2,
    section="skeletons",
    summary="Render declarations/doc-comments only, so a prediction can be written blind.",
    input_model=SkeletonInput,
    output_model=SkeletonOutput,
    tags=("model", "predict-blind"),
)
def make_blind_skeleton(ctx: ToolContext, inp: SkeletonInput) -> SkeletonOutput:
    flow = _flow_map(ctx).get(inp.flow_id)
    if not flow:
        raise ToolError(f"unknown flow_id {inp.flow_id!r}; run map_state_flows first")
    paths = inp.paths or [str(p) for p in (ctx.state.section(0, "scope") or {}).get("allowlist", [])] or ["."]
    files = resolve_files(ctx, paths, exts=source_exts(), max_files=3000)
    hits, method, _ = ctx.adapter.surfaces(files, ctx.workspace, max_surfaces=inp.max_surfaces)

    entry = str(flow.get("entry", "")).lower().split("(")[0].split()[-1].split(".")[-1]
    selected = [h for h in hits if entry and (entry in h.name.lower() or h.name.lower() in entry)]
    if not selected:
        selected = hits
    signatures = [
        Signature(file=h.file, line=h.line, name=h.name, language=h.language)
        for h in selected[: inp.max_surfaces]
    ]

    lines = [
        f"# Blind skeleton — {inp.flow_id}",
        "",
        f"Flow: {flow.get('name')}",
        f"Entry: {flow.get('entry')}",
        f"Extractor: {method}",
        "",
        "> Bodies are intentionally omitted. Read only this file before writing the prediction.",
        "",
        "## Signatures",
    ]
    lines.extend(f"- `{sig.file}:{sig.line}` — `{sig.name}` ({sig.language})" for sig in signatures)
    if not signatures:
        lines.append("- No signatures found. Enumerate manually and record that choice.")
    skeleton_dir = ctx.state.apex_dir / "predictions"
    skeleton_path = skeleton_dir / f"{inp.flow_id}-skeleton.md"
    write_text_atomic(skeleton_path, "\n".join(lines) + "\n")

    return SkeletonOutput(
        flow_id=inp.flow_id,
        skeleton_path=rel_to(skeleton_path, ctx.workspace),
        signatures=signatures,
        note=f"Skeleton from {method}; {len(signatures)} signature(s). Bodies omitted.",
    )


@tool(
    name="record_prediction",
    phase=2,
    section="predictions",
    summary="Record a blind prediction for a critical flow, including provenance and boundary semantics.",
    input_model=PredictionInput,
    output_model=PredictionOutput,
    tags=("model", "predict-blind"),
)
def record_prediction(ctx: ToolContext, inp: PredictionInput) -> PredictionOutput:
    if inp.flow_id not in _flow_map(ctx):
        raise ToolError(f"unknown flow_id {inp.flow_id!r}; run map_state_flows first")
    if len([s for s in inp.surprises if s.strip()]) < 2:
        raise ToolError("provide at least two concrete surprises that would prove the prediction wrong")
    if not inp.boundary_semantics.strip():
        raise ToolError("boundary_semantics is mandatory (inclusive/exclusive and boundary-instant behaviour)")

    record = PredictionRecord(**inp.model_dump())
    record.created_at = now_iso()
    prediction_dir = ctx.state.apex_dir / "predictions"
    path = prediction_dir / f"{inp.flow_id}-prediction.md"
    record.prediction_path = rel_to(path, ctx.workspace)
    body = [
        f"# Prediction — {inp.flow_id}",
        "",
        "## Provenance (what had been read when this was written)",
        inp.provenance,
        "",
        "## What I expect this flow to do",
        inp.expected,
        "",
        "## Expected inputs and validations",
        inp.inputs or "(not stated)",
        "",
        "## Expected state changes",
        inp.state_changes or "(not stated)",
        "",
        "## Expected failure behaviour",
        inp.failure_behavior or "(not stated)",
        "",
        "## Boundary semantics",
        inp.boundary_semantics,
        "",
        "## What would surprise me",
        *[f"- {item}" for item in inp.surprises],
        "",
        f"_Created: {record.created_at}_",
    ]
    write_text_atomic(path, "\n".join(body) + "\n")
    return PredictionOutput(
        flow_id=inp.flow_id,
        prediction_path=rel_to(path, ctx.workspace),
        prediction=record,
    )


TOOLS: list[ToolSpec] = [  # type: ignore[list-item]
    map_state_flows,
    define_invariants,
    define_state_vocabulary,
    define_sinks,
    make_blind_skeleton,
    record_prediction,
]

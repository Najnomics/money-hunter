"""Phase 4 — Specialist analysis dispatched from a Phase 3 divergence id.

In plain English: each divergence gets the right specialist.  Math goes to
the dimensional lens, opaque code to reverse engineering, ordering to the
state-machine lens, and trust questions to the boundary lens.  This file also
contains the assumption inventory, triggered test batteries, and chain
composition, because those are the tools that turn one clue into a story.
"""
from __future__ import annotations

import re
from pathlib import Path

from fsutil import is_binary, rel_to, sha256_file, walk_files
from runtime import ToolContext, ToolError, ToolSpec, tool
from schemas.common import Confidence
from schemas.phase4 import (
    AssumptionBatch,
    AssumptionInput,
    BatteryBatch,
    BatteryCheck,
    BatteryInput,
    BatteryResult,
    ChainBatch,
    ChainInput,
    DimensionalInput,
    Hypothesis,
    HypothesisBatch,
    NeverGeneratedInput,
    ReverseInput,
    SeedResearchInput,
    StateMachineInput,
    TrustBoundaryInput,
)
from tools._shared import existing_ids, next_id, require_divergence, scan_files, source_exts
from tools.hypothesis_seed import (
    covered_pairs,
    ensure_anchor_divergence,
    enumerate_pairs,
    family_ids_in_hypotheses,
    hypotheses_for_uncovered_pairs,
    hypotheses_from_audits,
    hypotheses_from_families,
    hypotheses_from_intel,
)
from tools.protocol_families import families_for_battery
from validation import fact_ok, validate_cite

DIMENSIONAL_PATTERNS = (
    ("scaling", re.compile(r"(?:\*|/)\s*(?:1e\d+|10\s*\*\*\s*\d+|1_000|1000|10000|1_000_000)")),
    ("decimals", re.compile(r"decimals|token_decimals|10\s*\*\*\s*decimals", re.I)),
    ("fixed-point", re.compile(r"\b(wad|ray|basis|bps|fee_rate|exchange_rate)\b", re.I)),
    ("cast", re.compile(r"\b(uint128|uint64|uint32|int128|as u64|as u128|to_int|from_int|int\()", re.I)),
    ("time", re.compile(r"block\.timestamp|\bnow\(\)|timestamp|duration|deadline|maturity", re.I)),
)

REVERSE_PATTERNS = (
    ("assembly", re.compile(r"\bassembly\b|\binline\s+asm\b|__asm__", re.I)),
    ("opaque", re.compile(r"0x[0-9a-fA-F]{40,}|\bbytecode\b|\bdeployedBytecode\b", re.I)),
    ("dynamic", re.compile(r"\beval\s*\(|\bFunction\s*\(|new\s+Function\b|\bvm\.runInNewContext\b")),
    ("delegate", re.compile(r"\bdelegatecall\b|\bproxy\b|\bupgradeTo", re.I)),
)

STATE_PATTERNS = (
    ("async", re.compile(r"\basync\b|\bawait\b|\bPromise\b|\bcallback\b|\bthen\s*\(", re.I)),
    ("init", re.compile(r"\binitialize\b|\binitializer\b|\binit\s*\(|\bconstructor\b", re.I)),
    ("guard", re.compile(r"\bnonReentrant\b|\bmutex\b|\block\b|\bsemaphore\b|\bguard\b", re.I)),
    ("lifecycle", re.compile(r"\bselfdestruct\b|\bdelegatecall\b|\bupgrade\b|\bpause\b|\bshutdown\b", re.I)),
    ("events", re.compile(r"\bemit\s+\w+|\bstate\s*=\b|\bwrite\b|\bcommit\b", re.I)),
)

TRUST_PATTERNS = (
    ("network", re.compile(r"https?://|\bfetch\s*\(|\brequests\.|\baxios\b|\bhttp\.client\b", re.I)),
    ("oracle", re.compile(r"\boracle\b|\bpriceFeed\b|\blatestRoundData\b|\bchainlink\b", re.I)),
    ("external-call", re.compile(r"\bcall\s*\{|\bdelegatecall\b|\btransfer\s*\(|\bdelegate\b", re.I)),
    ("input", re.compile(r"\breq\.(body|query|params|headers)\b|\brequest\.(json|form|args)\b|getParameter", re.I)),
    ("exec", re.compile(r"\bsubprocess\b|\beval\s*\(|\bexec\s*\(|\bdeserialize\b|\bunserialize\b|\bunsafe\b", re.I)),
)


def _flow_sink(ctx: ToolContext, divergence: dict) -> str:
    flows = (ctx.state.section(2, "flows") or {}).get("flows", [])
    flow_id = divergence.get("flow_id")
    for flow in flows:
        if flow.get("id") == flow_id:
            sinks = flow.get("value_sinks") or []
            if sinks:
                return str(sinks[0])
            break
    return "stated invariant at the divergence site"


def _base(
    ctx: ToolContext,
    divergence: dict,
    lens: str,
    hits: list[dict],
    focus: str | None,
    statement: str,
    prediction: str,
    confidence: Confidence,
    sink: str,
) -> HypothesisBatch:
    evidence: list[str] = [
        f"[DEDUCED] divergence {divergence.get('id')}: {divergence.get('kind')}"
    ]
    for hit in hits[:6]:
        evidence.append(f"[CODE] {hit['file']}:{hit['line']} {hit['snippet'][:160]}")
    if not hits:
        evidence.append("[ASSUMED] no direct code hit; focus supplied by analyst" if focus else "[ASSUMED] no direct code hit")

    hypothesis = Hypothesis(
        id=next_id(existing_ids(ctx, 4), "H"),
        divergence_id=str(divergence.get("id")),
        lens=lens,
        statement=statement,
        falsifiable_prediction=prediction,
        sink=sink,
        preconditions=[
            f"Divergence {divergence.get('id')} is reachable through its modelled entrypoint.",
            "The attacker controls the inputs identified in the prediction.",
        ],
        experiment_plan=(
            "Provision the profile sandbox (Phase 5), encode the prediction as an invariant test, "
            "run it, and capture stdout/stderr under .apex/experiments/."
        ),
        confidence=confidence,
        status="open",
        evidence=evidence,
    )
    notes = [] if hits else ["No direct code hit; hypothesis is analyst-directed and must be grounded before promotion."]
    return HypothesisBatch(hypotheses=[hypothesis], notes=notes)


def _resolve_scan_files(ctx: ToolContext, divergence: dict, explicit: list[str]) -> list[Path]:
    if explicit:
        return walk_files([ctx.resolve(p) for p in explicit], max_files=2000, exts=source_exts())
    if divergence.get("file"):
        path = ctx.resolve(divergence["file"])
        if path.exists() and path.is_file():
            return [path]
    scope = ctx.state.section(0, "scope") or {}
    roots = []
    for component in scope.get("components", []):
        if component.get("kind") in {"repo", "artifact"}:
            roots.extend(ctx.resolve(p) for p in component.get("paths", []))
    return walk_files(roots or [ctx.workspace], max_files=3000, exts=source_exts())


@tool(
    name="dimensional_checker",
    phase=4,
    section="dimensional",
    summary="Check arithmetic, decimals, rates, and unit conservation around a divergence.",
    input_model=DimensionalInput,
    output_model=HypothesisBatch,
    tags=("lens:math", "precision"),
)
def dimensional_checker(ctx: ToolContext, inp: DimensionalInput) -> HypothesisBatch:
    divergence = require_divergence(ctx, inp.divergence_id)
    files = _resolve_scan_files(ctx, divergence, inp.files)
    hits = scan_files(
        files,
        ctx.workspace,
        DIMENSIONAL_PATTERNS,
        limit=40,
        prefer_file=str(divergence.get("file") or "") or None,
        prefer_line=int(divergence["line"]) if divergence.get("line") else None,
    )
    sink = _flow_sink(ctx, divergence)
    focus = inp.focus or f"{divergence.get('expected')} vs {divergence.get('observed')}"
    if hits:
        statement = (
            f"Unit/scale handling near {hits[0]['file']}:{hits[0]['line']} may break the "
            f"conservation property of {sink}: `{hits[0]['snippet'][:180]}`."
        )
        prediction = (
            f"In the local sandbox, drive the expression at {hits[0]['file']}:{hits[0]['line']} "
            "with minimum, maximum, and decimal-boundary inputs. If the invariant quantity remains "
            "conserved (no rounding loss, overflow, or scale mismatch), this hypothesis is false."
        )
        confidence = Confidence.MEDIUM
    else:
        statement = f"Scaling/rounding around `{focus}` may violate {sink}."
        prediction = (
            f"Construct a differential test that applies the same operation through two equivalent "
            f"representations of {sink}. If both representations agree for boundary inputs, the "
            "hypothesis is false."
        )
        confidence = Confidence.LOW
    return _base(ctx, divergence, "dimensional-analysis", hits, inp.focus, statement, prediction, confidence, sink)


@tool(
    name="reverse_engineer_tool",
    phase=4,
    section="reverse_engineer",
    summary="Inventory opaque logic (binaries/bytecode/minified code) and hypothesise hidden state mutation.",
    input_model=ReverseInput,
    output_model=HypothesisBatch,
    tags=("lens:reverse", "opaque"),
)
def reverse_engineer_tool(ctx: ToolContext, inp: ReverseInput) -> HypothesisBatch:
    divergence = require_divergence(ctx, inp.divergence_id)
    artifacts = list(inp.artifact_paths)
    if not artifacts and divergence.get("file"):
        artifacts = [divergence["file"]]
    inventory: list[str] = []
    for raw in artifacts[:20]:
        path = ctx.resolve(raw)
        if not path.exists() or not path.is_file():
            continue
        size = path.stat().st_size
        kind = "binary" if is_binary(path) else "text"
        digest = sha256_file(path)[:16]
        inventory.append(f"{rel_to(path, ctx.workspace)} ({kind}, {size} bytes, sha256:{digest})")
        if kind == "text":
            hits = scan_files([path], ctx.workspace, REVERSE_PATTERNS, limit=20)
        else:
            hits = []

    if not artifacts:
        hits = scan_files(_resolve_scan_files(ctx, divergence, inp.files), ctx.workspace, REVERSE_PATTERNS, limit=30)
    else:
        hits = scan_files(_resolve_scan_files(ctx, divergence, inp.files or artifacts), ctx.workspace, REVERSE_PATTERNS, limit=30)

    sink = _flow_sink(ctx, divergence)
    focus = inp.focus or f"opaque behaviour behind {divergence.get('observed')}"
    statement = (
        f"Opaque logic in `{focus}` may mutate state that the Phase 2 model does not account for, "
        f"changing {sink} outside the documented flow."
    )
    prediction = (
        "Recover the control flow around the artifact, enumerate every state write, and compare against "
        "the Phase 2 state vocabulary. If every write is already modelled, the hypothesis is false."
    )
    if inventory:
        hits.append({"file": inventory[0], "line": 0, "snippet": inventory[0], "label": "inventory"})
    return _base(
        ctx,
        divergence,
        "reverse-engineering",
        hits,
        inp.focus,
        statement,
        prediction,
        Confidence.MEDIUM if inventory or hits else Confidence.LOW,
        sink,
    )


@tool(
    name="state_machine_breaker",
    phase=4,
    section="state_machine",
    summary="Analyse initialization, async paths, lifecycle guards, and cross-module state desynchronization.",
    input_model=StateMachineInput,
    output_model=HypothesisBatch,
    tags=("lens:state", "concurrency"),
)
def state_machine_breaker(ctx: ToolContext, inp: StateMachineInput) -> HypothesisBatch:
    divergence = require_divergence(ctx, inp.divergence_id)
    files = _resolve_scan_files(ctx, divergence, inp.files)
    hits = scan_files(
        files,
        ctx.workspace,
        STATE_PATTERNS,
        limit=40,
        prefer_file=str(divergence.get("file") or "") or None,
        prefer_line=int(divergence["line"]) if divergence.get("line") else None,
    )
    sink = _flow_sink(ctx, divergence)
    states = ", ".join(inp.target_states[:6]) or "the modelled states"
    if hits:
        statement = (
            f"State handling at {hits[0]['file']}:{hits[0]['line']} (`{hits[0]['snippet'][:140]}`) "
            f"may desynchronize {states} from {sink} under interleaved or replayed calls."
        )
        prediction = (
            f"Run two interleaved call sequences against the local sandbox that both touch "
            f"{hits[0]['file']}:{hits[0]['line']}. If {sink} and {states} stay consistent in every "
            "interleaving, the hypothesis is false."
        )
        confidence = Confidence.MEDIUM
    else:
        statement = f"Initialization or lifecycle ordering around `{inp.focus or divergence.get('kind')}` may desynchronize {states}."
        prediction = (
            "Enumerate all legal orderings of init/update/close calls in the sandbox and assert the "
            f"state invariant after each. If no ordering violates {sink}, the hypothesis is false."
        )
        confidence = Confidence.LOW
    return _base(ctx, divergence, "state-machine", hits, inp.focus, statement, prediction, confidence, sink)


@tool(
    name="trust_boundary_prober",
    phase=4,
    section="trust_boundary",
    summary="Trace untrusted inputs, external calls, oracles, and privilege paths across the model's boundaries.",
    input_model=TrustBoundaryInput,
    output_model=HypothesisBatch,
    tags=("lens:trust", "authorization"),
)
def trust_boundary_prober(ctx: ToolContext, inp: TrustBoundaryInput) -> HypothesisBatch:
    divergence = require_divergence(ctx, inp.divergence_id)
    files = _resolve_scan_files(ctx, divergence, inp.files)
    hits = scan_files(
        files,
        ctx.workspace,
        TRUST_PATTERNS,
        limit=40,
        prefer_file=str(divergence.get("file") or "") or None,
        prefer_line=int(divergence["line"]) if divergence.get("line") else None,
    )
    sink = _flow_sink(ctx, divergence)
    boundary = ", ".join(inp.boundaries[:5]) or str(divergence.get("expected"))
    if hits:
        statement = (
            f"Input/external-call handling at {hits[0]['file']}:{hits[0]['line']} crosses the "
            f"trust boundary `{boundary}` and may let an untrusted actor influence {sink}."
        )
        prediction = (
            f"From the untrusted side of `{boundary}`, send the exact payload that reaches "
            f"{hits[0]['file']}:{hits[0]['line']}. If the boundary rejects it or the effect on {sink} "
            "is unchanged, the hypothesis is false."
        )
        confidence = Confidence.MEDIUM
    else:
        statement = f"Privilege or input handling around `{inp.focus or boundary}` may allow escalation across {boundary}."
        prediction = (
            f"Replay the model's lowest-privilege actor against the endpoint/function that changes {sink}. "
            "If authorization denies the action, the hypothesis is false."
        )
        confidence = Confidence.LOW
    return _base(ctx, divergence, "trust-boundary", hits, inp.focus, statement, prediction, confidence, sink)


ASSUMPTION_CLASSES = {
    "TRUST", "ACCOUNTING", "ORDER_TIMING", "ECONOMIC", "ORACLE_DATA",
    "PRIVACY", "LIVENESS", "IDENTITY", "UPGRADE", "SPEC",
}


@tool(
    name="assumption_inventory",
    phase=4,
    section="assumptions",
    summary="Write down the beliefs the code silently makes, who can violate them, and at what cost.",
    input_model=AssumptionInput,
    output_model=AssumptionBatch,
    write_mode="append",
    tags=("assumptions", "generative"),
)
def assumption_inventory(ctx: ToolContext, inp: AssumptionInput) -> AssumptionBatch:
    notes: list[str] = []
    seen: set[str] = set()
    for assumption in inp.assumptions:
        if assumption.id in seen:
            raise ToolError(f"duplicate assumption id {assumption.id!r}")
        seen.add(assumption.id)
        if assumption.assumption_class not in ASSUMPTION_CLASSES:
            raise ToolError(
                f"assumption {assumption.id}: class must be one of {sorted(ASSUMPTION_CLASSES)}"
            )
        if assumption.where:
            result = validate_cite(ctx.workspace, assumption.where)
            if not result["valid"]:
                raise ToolError(f"assumption {assumption.id}: {assumption.where} does not resolve: {result['reason']}")
    if len(inp.assumptions) < 4:
        notes.append("Strict mode needs at least four assumption rows across multiple classes.")
    classes = sorted({a.assumption_class for a in inp.assumptions})
    if len(classes) < 3:
        notes.append("Fewer than three assumption classes; the inventory is probably too narrow.")
    return AssumptionBatch(items=inp.assumptions, notes=notes)


@tool(
    name="run_battery",
    phase=4,
    section="batteries",
    summary="Run a triggered test battery (vault, lifecycle, or boundary). Empty checks load the default protocol-agnostic share-price families.",
    input_model=BatteryInput,
    output_model=BatteryBatch,
    write_mode="section",
    tags=("battery", "conditional-gate"),
)
def run_battery(ctx: ToolContext, inp: BatteryInput) -> BatteryBatch:
    allowed = {"vault", "lifecycle", "boundary"}
    if inp.battery not in allowed:
        raise ToolError(f"battery must be one of {sorted(allowed)}")
    families = families_for_battery(inp.battery)
    checks = list(inp.checks)
    notes: list[str] = []
    if not checks:
        checks = [
            BatteryCheck(
                name=family.check_name,
                outcome="inconclusive",
                note=family.title,
            )
            for family in families
        ]
        notes.append(
            f"Loaded {len(checks)} default {inp.battery} family check(s). "
            "They stay inconclusive until an executed experiment fires or kills them."
        )
    trigger = inp.trigger.strip() or "; ".join(family.id for family in families)
    outcomes = {check.outcome for check in checks}
    if "fired" in outcomes:
        outcome = "fired"
    elif checks and outcomes == {"not_triggered"}:
        outcome = "not_triggered"
    else:
        outcome = "inconclusive"
    result = BatteryResult(
        id=next_id(existing_ids(ctx, 4), "BAT"),
        battery=inp.battery,
        trigger=trigger,
        outcome=outcome,
        checks=checks,
        notes=["A fired battery needs an evidence path; an inconclusive battery stays open."],
    )
    divergence = ensure_anchor_divergence(ctx, inp.divergence_id)
    reserved: set[str] = set()
    hypotheses = hypotheses_from_families(ctx, divergence, reserved, battery=inp.battery)
    if hypotheses:
        notes.append(f"Seeded {len(hypotheses)} protocol-family hypothesis(es) from the {inp.battery} battery.")
    return BatteryBatch(items=[result], hypotheses=hypotheses, notes=notes)


@tool(
    name="chain_hypotheses",
    phase=4,
    section="chains",
    summary="Join hypotheses on state facts to build multi-step exploit chains that end on a registered sink.",
    input_model=ChainInput,
    output_model=ChainBatch,
    write_mode="append",
    tags=("chain", "composition"),
)
def chain_hypotheses(ctx: ToolContext, inp: ChainInput) -> ChainBatch:
    hypotheses = {str(h.get("id")) for h in ctx.state.collect(4, "hypotheses") if h.get("id")}
    known_vars = {
        str(state.get("var"))
        for state in (ctx.state.section(2, "state_vocab") or {}).get("states", [])
        if state.get("var")
    }
    sinks = {
        str(sink.get("id")): sink
        for sink in (ctx.state.section(2, "sinks") or {}).get("sinks", [])
        if sink.get("id")
    }
    nodes = {node.hypothesis_id: node for node in inp.nodes}
    for node in inp.nodes:
        if node.hypothesis_id not in hypotheses:
            raise ToolError(f"chain node references unknown hypothesis {node.hypothesis_id!r}")
        for field_name, fact in (("pre_fact", node.pre_fact), ("post_fact", node.post_fact)):
            ok, reason = fact_ok(fact, known_vars)
            if not ok:
                raise ToolError(f"{node.hypothesis_id}.{field_name}: {reason}")

    for chain in inp.chains:
        if chain.sink_id not in sinks:
            raise ToolError(f"chain {chain.id}: unknown sink_id {chain.sink_id!r}; run define_sinks first")
        if not chain.order:
            raise ToolError(f"chain {chain.id}: order cannot be empty")
        for hypothesis_id in chain.order:
            if hypothesis_id not in nodes:
                raise ToolError(f"chain {chain.id}: missing node for {hypothesis_id!r}")
        if len(chain.edges) != max(0, len(chain.order) - 1):
            raise ToolError(f"chain {chain.id}: need one edge between each consecutive pair")
        for index, edge in enumerate(chain.edges):
            expected_source, expected_target = chain.order[index], chain.order[index + 1]
            if edge.source != expected_source or edge.target != expected_target:
                raise ToolError(f"chain {chain.id}: edge {index} does not match order")
            target = nodes[edge.target]
            if edge.via != target.pre_fact:
                raise ToolError(f"chain {chain.id}: edge via must name target pre_fact")
            for cite in (edge.cite, edge.satisfies_cite):
                result = validate_cite(ctx.workspace, cite)
                if not result["valid"]:
                    raise ToolError(f"chain {chain.id}: cite {cite} does not resolve: {result['reason']}")

        sink = sinks[chain.sink_id]
        sink_vars = {sink["var"]} if sink.get("var") else set(sink.get("vars", []))
        last_node = nodes[chain.order[-1]]
        last_var = last_node.post_fact.split(":", 1)[0]
        if sink_vars and last_var not in sink_vars:
            raise ToolError(
                f"chain {chain.id}: ends on {last_var!r}, not on sink {chain.sink_id} ({sorted(sink_vars)})"
            )
    return ChainBatch(items=inp.chains, notes=["Chains are rated by end-impact, not by the number of steps."])


@tool(
    name="seed_from_research",
    phase=4,
    section="research_seeds",
    summary="Turn intel matches, past-audit findings, and protocol families into divergence-anchored hypotheses.",
    input_model=SeedResearchInput,
    output_model=HypothesisBatch,
    tags=("intel", "generative"),
)
def seed_from_research(ctx: ToolContext, inp: SeedResearchInput) -> HypothesisBatch:
    divergence = ensure_anchor_divergence(ctx, inp.divergence_id)
    reserved: set[str] = set()
    existing = ctx.state.hypotheses()
    hypotheses: list[Hypothesis] = []
    seeded_from: list[str] = []
    if inp.include_families:
        families = hypotheses_from_families(ctx, divergence, reserved, existing=existing + [h.model_dump() for h in hypotheses])
        hypotheses.extend(families)
        if families:
            seeded_from.append("families")
    if inp.include_intel:
        intel = hypotheses_from_intel(
            ctx, divergence, reserved, existing=existing + [h.model_dump() for h in hypotheses]
        )
        hypotheses.extend(intel)
        if intel:
            seeded_from.append("intel")
    if inp.include_audits:
        audits = hypotheses_from_audits(
            ctx, divergence, reserved, existing=existing + [h.model_dump() for h in hypotheses]
        )
        hypotheses.extend(audits)
        if audits:
            seeded_from.append("audits")
    hypotheses = hypotheses[: inp.max_hypotheses]
    notes = [
        f"Seeded {len(hypotheses)} hypothesis(es) from {seeded_from or ['nothing new — families already present']}."
    ]
    if hypotheses:
        # Persist first so never_generated_check sees these ids and texts.
        ctx.state.write_section(
            4,
            "research_seeds",
            {"hypotheses": [h.model_dump(mode="json") for h in hypotheses]},
            "seed_from_research",
        )
    if inp.fill_never_generated:
        gap = never_generated_check.handler(
            ctx,
            NeverGeneratedInput(divergence_id=str(divergence.get("id")), max_generate=inp.max_pairs),
        )
        ctx.state.write_section(4, "gap_fill", gap.model_dump(mode="json"), "never_generated_check")
        hypotheses.extend(gap.hypotheses)
        notes.extend(gap.notes)
        if gap.hypotheses or gap.pairs_total:
            seeded_from = seeded_from + ["never-generated"]
        return HypothesisBatch(
            hypotheses=hypotheses,
            notes=notes,
            seeded_from=seeded_from,
            families_applied=sorted(family_ids_in_hypotheses([h.model_dump() for h in hypotheses] + existing)),
            pairs_total=gap.pairs_total,
            pairs_covered=gap.pairs_covered,
            pairs_generated=gap.pairs_generated,
            uncovered=gap.uncovered,
        )
    return HypothesisBatch(
        hypotheses=hypotheses,
        notes=notes,
        seeded_from=seeded_from,
        families_applied=sorted(family_ids_in_hypotheses([h.model_dump() for h in hypotheses] + existing)),
    )


@tool(
    name="never_generated_check",
    phase=4,
    section="gap_fill",
    summary="After hypothesis generation: every state-changing external function × value-bearing state var must be touched, or one hypothesis is generated.",
    input_model=NeverGeneratedInput,
    output_model=HypothesisBatch,
    tags=("coverage", "generative"),
)
def never_generated_check(ctx: ToolContext, inp: NeverGeneratedInput) -> HypothesisBatch:
    divergence = ensure_anchor_divergence(ctx, inp.divergence_id)
    pairs = enumerate_pairs(ctx)
    existing = ctx.state.hypotheses()
    covered = covered_pairs(existing, pairs)
    uncovered = [(fn, var, surface) for fn, var, surface in pairs if (fn, var) not in covered]
    reserved: set[str] = set()
    generated = hypotheses_for_uncovered_pairs(
        ctx, divergence, reserved, pairs, uncovered, inp.max_generate
    )
    leftover = uncovered[len(generated):]
    notes = [
        f"Enumerated {len(pairs)} mutator × value-var pair(s); {len(covered)} already touched; "
        f"generated {len(generated)}; {len(leftover)} still uncovered."
    ]
    if not pairs:
        notes.append(
            "No mutator × value-var pairs found. Map surfaces (Phase 3) and state vocabulary / sinks (Phase 2)."
        )
    if leftover:
        notes.append(
            f"{len(leftover)} pair(s) remain; rerun never_generated_check to continue. "
            "Coverage treats leftover pairs as high-EV gaps."
        )
    return HypothesisBatch(
        hypotheses=generated,
        notes=notes,
        seeded_from=["never-generated"],
        pairs_total=len(pairs),
        pairs_covered=len(covered),
        pairs_generated=len(generated),
        uncovered=[f"{fn}::{var}" for fn, var, _ in leftover],
    )


TOOLS: list[ToolSpec] = [  # type: ignore[list-item]
    dimensional_checker,
    reverse_engineer_tool,
    state_machine_breaker,
    trust_boundary_prober,
    assumption_inventory,
    run_battery,
    chain_hypotheses,
    seed_from_research,
    never_generated_check,
]

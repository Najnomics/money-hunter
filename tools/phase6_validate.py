"""Phase 6 — Validate & Report.

This is also where the campaign closes the loop: check citations, classify
findings with the severity matrix, compute coverage, and decide whether a new
coverage round is worth running.
"""
from __future__ import annotations

import re
from pathlib import Path

from fsutil import now_iso, rel_to, sha1_text, write_text_atomic
from runtime import ToolContext, ToolSpec, ToolError, tool
from schemas.phase6 import (
    CampaignStartInput,
    CampaignStartOutput,
    CampaignStatusOutput,
    CheckResult,
    CitationCheckInput,
    CitationCheckOutput,
    CitationIssue,
    Classification,
    ClassificationBatch,
    ClassificationInput,
    CloseRoundInput,
    CloseSessionInput,
    CloseSessionOutput,
    CoverageInput,
    CoverageOutput,
    Disproof,
    DisproofBatch,
    DisproofCheck,
    DisproveInput,
    DraftFindingInput,
    DraftFindingOutput,
    FindingDraft,
    GapRef,
    IssueBatch,
    IssueEntry,
    IssueInput,
    ReportInput,
    ReportOutput,
    RoundRecord,
    StartRoundInput,
)
from tools._shared import existing_ids, next_id, require_hypothesis
from validation import parse_cite, severity_from, validate_cite, validate_cites

DEFAULT_CHECKS = (
    DisproofCheck(
        name="environmental-precondition",
        question="Can an unprivileged actor reach the precondition in the deployed environment?",
        result=CheckResult.UNKNOWN,
        evidence="",
    ),
    DisproofCheck(
        name="auth-middleware",
        question="Does an authentication/authorization layer block the path before the divergence?",
        result=CheckResult.UNKNOWN,
        evidence="",
    ),
    DisproofCheck(
        name="system-constraint",
        question="Does a rate limit, cap, validation, or downstream constraint make the impact unreachable?",
        result=CheckResult.UNKNOWN,
        evidence="",
    ),
)


@tool(
    name="disprove_finding",
    phase=6,
    section="disproofs",
    summary="Adversarially test whether preconditions/middleware/constraints make a hypothesis unreachable.",
    input_model=DisproveInput,
    output_model=DisproofBatch,
    write_mode="append",
    tags=("validation", "false-positive"),
)
def disprove_finding(ctx: ToolContext, inp: DisproveInput) -> DisproofBatch:
    require_hypothesis(ctx, inp.hypothesis_id)
    checks = inp.checks or list(DEFAULT_CHECKS)

    blocking = [c.name for c in checks if c.result == CheckResult.BLOCKS]
    allowing = [c.name for c in checks if c.result == CheckResult.ALLOWS]
    unknown = [c.name for c in checks if c.result == CheckResult.UNKNOWN]

    if blocking:
        verdict = "disproved"
        rationale = "At least one check blocks the path: " + ", ".join(blocking)
    elif checks and not unknown:
        verdict = "survives"
        rationale = "Every adversarial check allows the path: " + ", ".join(allowing)
    else:
        verdict = "needs-evidence"
        rationale = (
            "Unresolved checks: " + ", ".join(unknown)
            if unknown
            else "No checks supplied."
        )

    disproof = Disproof(
        id=next_id(existing_ids(ctx, 6), "DP"),
        hypothesis_id=inp.hypothesis_id,
        verdict=verdict,
        blocking_checks=blocking,
        allowing_checks=allowing,
        unknown_checks=unknown,
        rationale=rationale + (f" Notes: {inp.notes}" if inp.notes else ""),
    )
    return DisproofBatch(items=[disproof])


@tool(
    name="verify_citations",
    phase=6,
    section="citations",
    summary="Resolve every path:line citation in the campaign and report broken ones.",
    input_model=CitationCheckInput,
    output_model=CitationCheckOutput,
    tags=("citation", "evidence"),
)
def verify_citations(ctx: ToolContext, inp: CitationCheckInput) -> CitationCheckOutput:
    payloads = []
    for phase in inp.phases:
        for name, value in ctx.state.sections(phase).items():
            if phase == 6 and name in {"citations", "coverage"}:
                continue
            if name == "markdown" and not inp.include_markdown:
                continue
            payloads.append(value)
    # Only structured evidence fields are claims. Free-text observations such
    # as "withdraw.rs:297" are notes, not citations, and must not block a report.
    report = validate_cites(
        ctx.workspace,
        payloads,
        focus_keys={
            "evidence", "cites", "cite", "satisfies_cite", "file", "where",
            "poc", "artifact", "output_path", "stdout_path", "stderr_path",
        },
    )
    details = [
        CitationIssue(cite=row["cite"], reason=row["reason"])
        for row in report.get("details", [])
    ]
    notes: list[str] = []
    if report["checked"] == 0:
        notes.append("No citations were found. Add file:line evidence before promoting a finding.")
    if report["invalid"]:
        notes.append("Standard/strict policy blocks the report until every citation resolves.")
    return CitationCheckOutput(
        checked=report["checked"],
        valid=report["valid"],
        invalid=report["invalid"],
        details=details,
        notes=notes,
    )


@tool(
    name="classify_finding",
    phase=6,
    section="classifications",
    summary="Derive severity from impact x trigger, capped by reachability; critical needs human approval.",
    input_model=ClassificationInput,
    output_model=ClassificationBatch,
    write_mode="append",
    tags=("severity", "validation"),
)
def classify_finding(ctx: ToolContext, inp: ClassificationInput) -> ClassificationBatch:
    require_hypothesis(ctx, inp.hypothesis_id)
    severity = severity_from(str(inp.impact), str(inp.trigger), str(inp.reachability))
    requires_approval = severity == "critical" and not inp.human_approved
    if requires_approval:
        proof_tier = "theoretical"
    elif inp.reachability == "verified":
        proof_tier = "confirmed" if inp.human_approved or severity != "critical" else "probable"
    else:
        proof_tier = "theoretical"

    classification = Classification(
        id=next_id(existing_ids(ctx, 6), "CL"),
        hypothesis_id=inp.hypothesis_id,
        impact=str(inp.impact),
        trigger=str(inp.trigger),
        reachability=str(inp.reachability),
        severity=severity,
        proof_tier=proof_tier,
        human_approved=inp.human_approved,
        requires_approval=requires_approval,
        reason=inp.reason or f"{inp.impact} x {inp.trigger} -> {severity}",
        poc=inp.poc,
    )
    notes = []
    if requires_approval:
        notes.append("Critical claim is pending human approval. It cannot ship until approved.")
    return ClassificationBatch(items=[classification], notes=notes)


@tool(
    name="coverage_check",
    phase=6,
    section="coverage",
    summary="Compute what was covered, what is still open, and rank gaps for the next round.",
    input_model=CoverageInput,
    output_model=CoverageOutput,
    tags=("coverage", "closure"),
)
def coverage_check(ctx: ToolContext, inp: CoverageInput) -> CoverageOutput:
    state = ctx.state
    flows = (state.section(2, "flows") or {}).get("flows", [])
    ast_map = state.section(3, "ast_map") or {}
    surfaces = ast_map.get("surfaces", [])
    mapped_flows = ast_map.get("mapped_flows", {})
    divergences = state.divergences()
    hypotheses = state.hypotheses()
    experiments = state.experiments()
    disproofs = state.disproofs()
    sinks = (state.section(2, "sinks") or {}).get("sinks", [])
    chains = state.collect(4, "chains")

    covered_flow_ids = {str(d.get("flow_id")) for d in divergences if d.get("flow_id")}
    tested_ids = {str(e.get("hypothesis_id")) for e in experiments if e.get("hypothesis_id")}
    disproved_ids = {str(d.get("hypothesis_id")) for d in disproofs if d.get("hypothesis_id")}
    chain_sinks = {str(c.get("sink_id")) for c in chains if c.get("sink_id")}
    hypothesis_sinks = {str(h.get("sink")) for h in hypotheses if h.get("sink")}

    gaps: list[GapRef] = []
    for flow in flows:
        flow_id = str(flow.get("id"))
        if flow_id not in covered_flow_ids:
            gaps.append(
                GapRef(
                    id=f"GAP-FLOW-{flow_id}",
                    type="flow",
                    description=f"Flow {flow_id} ({flow.get('name')}) has no mapped divergence yet.",
                    next_phase=3,
                    next_tool="ast_divergence_mapper",
                    flow_id=flow_id,
                    ev_rank=80 if flow.get("critical") else 40,
                )
            )

    mapped_surface_keys = {
        str(value) for values in mapped_flows.values() for value in values
    }
    divergence_locations = {
        f"{d.get('file')}:{d.get('line')}" for d in divergences if d.get("file")
    }
    for surface in surfaces:
        location = f"{surface.get('file')}:{surface.get('line')}"
        if location in mapped_surface_keys or location in divergence_locations:
            continue
        gaps.append(
            GapRef(
                id=f"GAP-SURFACE-{sha1_text(location)[:8]}",
                type="surface",
                description=f"Surface {surface.get('name')} at {location} is not mapped to any divergence.",
                next_phase=3,
                next_tool="ast_divergence_mapper",
                file=surface.get("file"),
                ev_rank=35,
            )
        )

    for sink in sinks:
        sink_id = str(sink.get("id"))
        variables = [sink.get("var")] if sink.get("var") else list(sink.get("vars", []))
        covered = sink_id in chain_sinks or any(v in hypothesis_sinks for v in variables)
        if not covered:
            gaps.append(
                GapRef(
                    id=f"GAP-SINK-{sink_id}",
                    type="sink",
                    description=f"Sink {sink_id} has no hypothesis or chain pointing at it.",
                    next_phase=4,
                    next_tool="assumption_inventory",
                    sink=sink_id,
                    ev_rank=100,
                )
            )

    for hypothesis in hypotheses:
        hypothesis_id = str(hypothesis.get("id"))
        if hypothesis_id not in tested_ids:
            gaps.append(
                GapRef(
                    id=f"GAP-HYP-{hypothesis_id}",
                    type="hypothesis",
                    description=f"Hypothesis {hypothesis_id} has no executed experiment.",
                    next_phase=5,
                    next_tool="invariant_tester",
                    ev_rank=65,
                )
            )
        if hypothesis_id not in disproved_ids:
            gaps.append(
                GapRef(
                    id=f"GAP-DISPROOF-{hypothesis_id}",
                    type="disproof",
                    description=f"Hypothesis {hypothesis_id} has not been through the adversarial kill-pass.",
                    next_phase=6,
                    next_tool="disprove_finding",
                    ev_rank=30,
                )
            )

    gaps.sort(key=lambda gap: gap.ev_rank, reverse=True)
    total = len(flows)
    covered = len([flow for flow in flows if str(flow.get("id")) in covered_flow_ids])
    ratio = round((covered / total), 3) if total else 0.0
    confidence = "pattern" if ast_map.get("method") in {"tree-sitter", "tree-sitter+regex"} else "lower-bound"
    surfaces_mapped = sum(
        1 for surface in surfaces
        if f"{surface.get('file')}:{surface.get('line')}" in mapped_surface_keys
        or f"{surface.get('file')}:{surface.get('line')}" in divergence_locations
    )

    return CoverageOutput(
        summary={
            "flows_total": total,
            "flows_covered": covered,
            "surfaces_total": len(surfaces),
            "surfaces_mapped": surfaces_mapped,
            "sinks_total": len(sinks),
            "hypotheses_total": len(hypotheses),
            "hypotheses_tested": len(tested_ids),
            "disproofs": len(disproofs),
            "gaps": len(gaps),
        },
        ratio=ratio,
        confidence=confidence,
        gaps=gaps[: inp.max_gaps],
        notes=[
            f"covered {covered}/{total} flows ({int(ratio * 100)}%)",
            "Coverage is a ratio, not a quota. High-EV gaps are ranked first.",
        ],
    )


@tool(
    name="start_round",
    phase=6,
    section="round",
    summary="Open a bounded coverage round with the highest-value gaps.",
    input_model=StartRoundInput,
    output_model=RoundRecord,
    tags=("round", "coverage-loop"),
)
def start_round(ctx: ToolContext, inp: StartRoundInput) -> RoundRecord:
    records = ctx.state.round_records()
    if records and records[-1].get("status") == "open":
        raise ToolError(f"round {records[-1].get('round')} is still open; close it first")
    selected = sorted(inp.gaps, key=lambda gap: gap.ev_rank, reverse=True)[: inp.max_gaps]
    if not selected:
        raise ToolError("no gaps supplied; run coverage_check first")
    record = RoundRecord(
        round=ctx.state.next_round_number(),
        status="open",
        gaps_selected=selected,
        started_at=now_iso(),
        notes=[inp.notes] if inp.notes else [],
    )
    ctx.state.write_round(record.model_dump(mode="json"))
    return record


@tool(
    name="close_round",
    phase=6,
    section="round",
    summary="Close a coverage round and record whether it made real progress.",
    input_model=CloseRoundInput,
    output_model=RoundRecord,
    tags=("round", "coverage-loop"),
)
def close_round(ctx: ToolContext, inp: CloseRoundInput) -> RoundRecord:
    records = {int(record["round"]): record for record in ctx.state.round_records() if record.get("round")}
    record = records.get(inp.round)
    if not record:
        raise ToolError(f"unknown round {inp.round}")
    record.update(
        {
            "status": "closed",
            "closed_at": now_iso(),
            "outcome": inp.outcome,
            "tools_run": inp.tools_run,
            "new_divergences": inp.new_divergences,
            "new_hypotheses": inp.new_hypotheses,
            "new_experiments": inp.new_experiments,
            "closed_gaps": inp.closed_gaps,
            "remaining_gaps": [gap.model_dump(mode="json") for gap in inp.remaining_gaps],
            "stop_reason": inp.stop_reason,
        }
    )
    if inp.notes:
        record.setdefault("notes", []).append(inp.notes)
    result = RoundRecord.model_validate(record)
    ctx.state.write_round(result.model_dump(mode="json"))
    if inp.outcome == "stalled":
        result.notes.append("Stalled round: do not start another round without new evidence or a user override.")
    return result


@tool(
    name="close_session",
    phase=6,
    section="session",
    summary="Write a death-note and backlog so the next session can resume without starting over.",
    input_model=CloseSessionInput,
    output_model=CloseSessionOutput,
    tags=("resume", "campaign"),
)
def close_session(ctx: ToolContext, inp: CloseSessionInput) -> CloseSessionOutput:
    apex = ctx.state.apex_dir
    death_note = apex / "death-note.md"
    backlog = apex / "backlog.md"
    body = [
        "# Session close",
        "",
        f"Status: **{inp.status}**",
        f"Closed: {now_iso()}",
        "",
        "## Resume state",
        inp.resume_state,
        "",
        "## Remaining gaps",
        *[f"- {gap.id}: {gap.description}" for gap in inp.remaining_gaps],
        "",
        "## Lessons",
        *[f"- {lesson}" for lesson in inp.lessons],
        "",
    ]
    write_text_atomic(death_note, "\n".join(body))
    write_text_atomic(
        backlog,
        "# Backlog\n\n" + "\n".join(f"- {item}" for item in inp.backlog) + "\n",
    )
    return CloseSessionOutput(
        death_note_path=rel_to(death_note, ctx.workspace),
        backlog_path=rel_to(backlog, ctx.workspace),
        status=inp.status,
    )


def _cell(value) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")[:300]


def _table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(_cell(v) for v in row) + " |")
    return "\n".join(out)


@tool(
    name="start_campaign",
    phase=6,
    section="campaign",
    summary="Bind a target workspace and policy once, then call phase0 without repeating workspace.",
    input_model=CampaignStartInput,
    output_model=CampaignStartOutput,
    write_mode="none",
    always_available=True,
    tags=("meta", "campaign"),
)
def start_campaign(ctx: ToolContext, inp: CampaignStartInput) -> CampaignStartOutput:
    allowed = {"light", "standard", "strict"}
    if inp.policy not in allowed:
        raise ToolError(f"policy must be one of {sorted(allowed)}")
    target = str(getattr(inp, "workspace", None) or ctx.workspace)
    if ctx.session is not None:
        from pathlib import Path

        ctx.session.workspace = Path(target).expanduser().resolve()
        ctx.session.policy_hint = inp.policy
    values: dict[str, object] = {"gate_policy": inp.policy}
    if inp.profile:
        values["target_profile"] = inp.profile
    ctx.state.update_config(**values)

    next_args: dict[str, object] = {"repos": inp.repos or ["."]}
    if inp.endpoints:
        next_args["endpoints"] = inp.endpoints
    if inp.profile:
        next_args["profile"] = inp.profile
    message = (
        f"Campaign bound to {target} with policy {inp.policy}. "
        "Next: phase0_parse_scope. Ask the user before switching to strict."
    )
    return CampaignStartOutput(
        workspace=target,
        policy=inp.policy,
        next_tool="phase0_parse_scope",
        next_args=next_args,
        message=message,
    )


@tool(
    name="campaign_status",
    phase=6,
    section="campaign_status",
    summary="Show the bound target, gate progress, and what strict mode still needs.",
    input_model=CampaignStartInput,
    output_model=CampaignStatusOutput,
    write_mode="none",
    always_available=True,
    tags=("meta", "status"),
)
def campaign_status(ctx: ToolContext, inp: CampaignStartInput) -> CampaignStatusOutput:
    snapshot = ctx.state.snapshot()
    next_phase = ctx.state.next_incomplete_phase()
    strict_missing = ctx.state.strict_gaps()
    strict_ready = not strict_missing
    if next_phase is None:
        message = "All phase gates are complete."
    else:
        message = f"Next incomplete phase: {next_phase}."
    if strict_ready and ctx.state.gate_policy != "strict":
        message += " Strict prerequisites are complete; ask the user before switching."
    return CampaignStatusOutput(
        workspace=str(ctx.workspace),
        policy=ctx.state.gate_policy,
        next_phase=next_phase,
        phases=snapshot["phases"],
        counts=snapshot["counts"],
        strict_ready=strict_ready,
        strict_missing=strict_missing,
        message=message,
    )


@tool(
    name="report_issue",
    phase=6,
    section="issues",
    summary="Report pipeline friction, bugs, doc gaps, or a missing tool; available at any phase.",
    input_model=IssueInput,
    output_model=IssueBatch,
    write_mode="append",
    always_available=True,
    tags=("feedback", "meta"),
)
def report_issue(ctx: ToolContext, inp: IssueInput) -> IssueBatch:
    """Let the agent report a problem with the pipeline itself.

    This is intentionally always available.  If a phase gate is blocking the
    campaign, or a static analyser is not installed, the agent should report the
    block instead of silently inventing a workaround.
    """
    kinds = {
        "tool_friction", "missing_tool", "missing_capability", "bug",
        "doc_gap", "environment",
    }
    if inp.kind not in kinds:
        raise ToolError(f"issue kind must be one of {sorted(kinds)}")
    if inp.severity not in {"low", "medium", "high", "blocker"}:
        raise ToolError("severity must be low, medium, high, or blocker")
    if inp.phase_attempted is not None and not 0 <= inp.phase_attempted <= 6:
        raise ToolError("phase_attempted must be 0..6")

    citations = validate_cites(ctx.workspace, inp.evidence)
    entry = IssueEntry(
        id=next_id(existing_ids(ctx, 6), "ISS"),
        created_at=now_iso(),
        **inp.model_dump(),
    )
    notes = []
    if citations["invalid"]:
        notes.append(f"{citations['invalid']} evidence citation(s) did not resolve; keep them for repro.")
    if inp.severity == "blocker" and not inp.requested_change:
        notes.append("For a blocker, state the exact capability or change requested.")
    return IssueBatch(items=[entry], notes=notes)


def _slug(text: str, fallback: str = "finding") -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:60] or fallback


def _one_line(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _first_sentence(text: str) -> str:
    clean = _one_line(text).strip("`")
    if not clean:
        return "Not stated."
    return re.split(r"(?<=[.!?])\s+", clean, maxsplit=1)[0][:240]


def _finding_markdown(
    finding: dict,
    divergence: dict,
    classification: dict,
    runs: list[dict],
    status: str,
    draft: dict | None = None,
) -> str:
    """Render the team's standard one-bug report."""
    draft = draft or {}
    title = draft.get("title") or finding.get("title") or _first_sentence(finding.get("statement", ""))
    summary = draft.get("summary") or finding.get("summary") or _first_sentence(finding.get("statement", ""))
    intended = (
        draft.get("intended")
        or divergence.get("expected")
        or "The system should enforce the modelled invariant."
    )
    actual = (
        draft.get("actual")
        or divergence.get("observed")
        or finding.get("statement")
        or "The implementation differs."
    )
    impact = (
        draft.get("impact")
        or finding.get("impact_statement")
        or finding.get("sink")
        or "Impact not stated; confirm with the target owner."
    )
    affected = ""
    if divergence.get("file"):
        affected = f"`{divergence.get('file')}:{divergence.get('line', '')}`".rstrip(":`") + "`"
    proofs = []
    if draft.get("proof_of_code"):
        proofs.append(f"`{draft['proof_of_code']}`")
    for run in runs:
        proof = run.get("artifact") or run.get("stdout_path")
        if proof:
            proofs.append(f"`{proof}` (experiment `{run.get('id')}`, command `{run.get('command')}`)")
    proof_block = "\n".join(f"- {p}" for p in dict.fromkeys(proofs)) if proofs else (
        "No executed test. This report is a **candidate**, not a verified finding."
    )
    recommendations = draft.get("recommendations") or []
    remediation = (
        "\n".join(f"- {item}" for item in recommendations)
        if recommendations
        else finding.get("remediation")
        or "Enforce the intended check or invariant at the divergence site, then add a regression test."
    )
    lines = [
        f"# {title}",
        "",
        f"**Status:** {status}  ",
        f"**Finding ID:** {finding.get('id')}  ",
        f"**Severity:** {draft.get('severity') or classification.get('severity', 'unclassified')}  ",
        f"**Proof tier:** {classification.get('proof_tier', 'candidate')}  ",
        f"**Affected:** {affected or 'see evidence below'}",
        "",
        "## Summary",
        "",
        summary,
        "",
        "## Description",
        "",
        f"**Intended behaviour.** {intended}",
        "",
        f"**Actual behaviour.** {actual}",
        "",
        *([_one_line(finding.get("statement", ""))] if not draft.get("actual") else []),
        "",
        "## Impact",
        "",
        impact,
        "",
        "## Proof of Code",
        "",
        proof_block,
        "",
        "## Recommendation(s)",
        "",
        remediation,
        "",
        "---",
        "",
        f"Divergence: `{finding.get('divergence_id')}`  ",
        f"Evidence: {'; '.join(finding.get('evidence', [])) or 'none'}",
        "",
    ]
    return "\n".join(lines)


@tool(
    name="draft_finding_report",
    phase=6,
    section="finding_drafts",
    summary="Write the team-standard, non-technical report fields for one finding.",
    input_model=DraftFindingInput,
    output_model=DraftFindingOutput,
    write_mode="append",
    tags=("report", "finding"),
)
def draft_finding_report(ctx: ToolContext, inp: DraftFindingInput) -> DraftFindingOutput:
    require_hypothesis(ctx, inp.hypothesis_id)
    if inp.severity and inp.severity not in {"critical", "high", "medium", "low", "info"}:
        raise ToolError("severity must be critical, high, medium, low, or info")
    if inp.proof_of_code:
        if parse_cite(inp.proof_of_code) is None:
            proof_path = Path(inp.proof_of_code)
            if not proof_path.is_absolute():
                proof_path = ctx.workspace / proof_path
            if not proof_path.is_file():
                raise ToolError(f"proof_of_code file does not exist: {inp.proof_of_code}")
        else:
            result = validate_cite(ctx.workspace, inp.proof_of_code)
            if not result["valid"]:
                raise ToolError(f"proof_of_code does not resolve: {result['reason']}")
    draft = FindingDraft(
        id=next_id(existing_ids(ctx, 6), "FR"),
        created_at=now_iso(),
        **inp.model_dump(),
    )
    notes = []
    if not inp.recommendations:
        notes.append("Add at least one concrete recommendation before publishing.")
    return DraftFindingOutput(items=[draft], notes=notes)


@tool(
    name="generate_report",
    phase=6,
    section="report",
    summary="Compile the campaign report and one standard report per finding under .apex/reports/.",
    input_model=ReportInput,
    output_model=ReportOutput,
    write_mode="report",
    tags=("report",),
)
def generate_report(ctx: ToolContext, inp: ReportInput) -> ReportOutput:
    state = ctx.state
    ground = state.section(0, "scope") or {}
    rules = state.section(0, "rules") or {}
    boundaries = state.section(0, "boundaries") or {}
    model = state.section(2, "flows") or {}
    invariants = state.section(2, "invariants") or {}
    docs = state.section(1, "docs") or {}

    divergences = state.divergences()
    hypotheses = state.hypotheses()
    experiments = state.experiments()
    disproofs = state.disproofs()
    assumptions = state.collect(4, "assumptions")
    chains = state.collect(4, "chains")
    coverage = state.section(6, "coverage") or {}
    classifications = state.collect(6, "classifications")
    drafts = state.collect(6, "finding_drafts")
    draft_by_hyp = {
        str(row.get("hypothesis_id")): row for row in drafts if row.get("hypothesis_id")
    }
    issues = state.collect(6, "issues")
    rounds = state.round_records()
    classification_by_hyp = {
        str(row.get("hypothesis_id")): row for row in classifications if row.get("hypothesis_id")
    }

    disproof_by_hyp: dict[str, list[dict]] = {}
    for disproof in disproofs:
        disproof_by_hyp.setdefault(str(disproof.get("hypothesis_id")), []).append(disproof)

    experiments_by_hyp: dict[str, list[dict]] = {}
    for experiment in experiments:
        experiments_by_hyp.setdefault(str(experiment.get("hypothesis_id")), []).append(experiment)

    def verified(hypothesis: dict) -> bool:
        runs = experiments_by_hyp.get(str(hypothesis.get("id")), [])
        return any(run.get("status") == "ran" and run.get("verdict") == "confirmed" for run in runs)

    def disproved(hypothesis: dict) -> bool:
        return any(d.get("verdict") == "disproved" for d in disproof_by_hyp.get(str(hypothesis.get("id")), []))

    survivors = [h for h in hypotheses if not disproved(h)]
    verified_findings = [h for h in survivors if verified(h)]
    candidates = [h for h in survivors if not verified(h)]
    rejected = [h for h in hypotheses if disproved(h)]

    # Write one standard report per finding. Verified findings go under
    # reports/verified. Surviving candidates go under reports/candidates and
    # are clearly marked as unverified, so a build-blocked target still
    # produces useful, honest writeups.
    divergence_by_id = {str(d.get("id")): d for d in divergences if d.get("id")}
    reports_dir = ctx.state.apex_dir / "reports"
    report_entries: list[tuple[str, str, str, str]] = []
    sections = (
        ("verified", verified_findings, "Verified — executed evidence", 100),
        ("candidates", candidates, "Candidate — not verified", 50),
    )
    for folder, items, status, limit in sections:
        directory = reports_dir / folder
        directory.mkdir(parents=True, exist_ok=True)
        for stale in directory.glob("*.md"):
            stale.unlink(missing_ok=True)
        for finding in items[:limit]:
            runs = experiments_by_hyp.get(str(finding.get("id")), [])
            classification = classification_by_hyp.get(str(finding.get("id")), {})
            divergence = divergence_by_id.get(str(finding.get("divergence_id")), {})
            draft = draft_by_hyp.get(str(finding.get("id")))
            filename = f"{finding.get('id')}.md"
            path = directory / filename
            title = (
                (draft or {}).get("title")
                or finding.get("title")
                or _first_sentence(finding.get("statement", ""))
            )
            write_text_atomic(
                path,
                _finding_markdown(finding, divergence, classification, runs, status, draft),
            )
            report_entries.append(
                (
                    rel_to(path, reports_dir),
                    _one_line(title)[:120],
                    status,
                    classification.get("severity", "unclassified"),
                )
            )

    index_path = reports_dir / "index.md"
    index_lines = [
        "# Finding reports",
        "",
        f"Generated: {now_iso()}",
        "",
        "| Report | Status | Severity |",
        "|---|---|---|",
    ]
    if report_entries:
        for relative, title, status, severity in report_entries:
            index_lines.append(f"| [{title}]({relative}) | {status} | {severity} |")
    else:
        index_lines.append("| No findings or candidates recorded | — | — |")
    index_lines.append("")
    write_text_atomic(index_path, "\n".join(index_lines))

    summary = {
        "divergences": len(divergences),
        "hypotheses": len(hypotheses),
        "experiments": len(experiments),
        "verified_findings": len(verified_findings),
        "candidate_hypotheses": len(candidates),
        "disproved": len(rejected),
        "assumptions": len(assumptions),
        "chains": len(chains),
        "classifications": len(classifications),
        "rounds": len(rounds),
        "issues": len(issues),
        "drafts": len(drafts),
        "reports": len(report_entries),
    }

    title = inp.title or f"Apex Campaign Report — {ctx.workspace.name}"
    lines: list[str] = [
        f"# {title}",
        "",
        f"Generated: {now_iso()}  ",
        f"TargetProfile: `{state.target_profile.value}`  ",
        f"Workspace: `{ctx.workspace}`",
        "",
        "## The mirror",
        "",
        f"- **Earned:** {inp.mirror_earned or 'not stated'}",
        f"- **Faked:** {inp.mirror_faked or 'not stated'}",
        f"- **Next run:** {inp.mirror_next or 'not stated'}",
        f"- **Brag or regret:** {inp.mirror_brag_or_regret or 'not stated'}",
        "",
        "## Executive summary",
        "",
        f"- {summary['divergences']} model/code divergence(s) mapped.",
        f"- {summary['hypotheses']} divergence-anchored hypothesis(es) generated.",
        f"- {summary['experiments']} experiment(s) recorded.",
        f"- **{summary['verified_findings']} verified finding(s)** with executed evidence.",
        f"- {summary['candidate_hypotheses']} surviving candidate(s) awaiting executed evidence.",
        f"- {summary['disproved']} hypothesis(es) disproved by adversarial checks.",
        f"- {summary['assumptions']} assumption row(s); {summary['chains']} composed chain(s).",
        f"- Coverage: {coverage.get('ratio', 0):.0%} of modelled flows "
        f"({coverage.get('summary', {}).get('flows_covered', 0)}/"
        f"{coverage.get('summary', {}).get('flows_total', 0)}), confidence `{coverage.get('confidence', 'unknown')}`.",
        "",
    ]

    if not verified_findings:
        lines.extend(
            [
                "> No finding is reported as verified. Candidates below are **not** findings until an ",
                "> executed experiment in `.apex/experiments/` confirms the prediction.",
                "",
            ]
        )

    lines.extend(["## Finding reports", ""])
    lines.append(f"Folder: `{rel_to(reports_dir, ctx.workspace)}` — index: `reports/index.md`")
    lines.append("")
    if report_entries:
        for relative, title, status, severity in report_entries:
            lines.append(f"- [{title}](reports/{relative}) — {status}, severity `{severity}`")
    else:
        lines.append("No individual finding reports were generated.")
    lines.append("")

    lines.extend(["## Scope & guardrails", ""])
    allowlist = ground.get("allowlist", [])
    lines.append(f"Allowlist: {', '.join(f'`{a}`' for a in allowlist) or 'none recorded'}")
    lines.append("")
    if boundaries:
        lines.append("Hard rules:")
        lines.extend(f"- {rule}" for rule in boundaries.get("hard_rules", []))
        lines.append("")

    lines.extend(["## Intended behaviour (Phase 1)", ""])
    if docs:
        lines.append(str(docs.get("summary", "")))
        lines.append("")
    claims = (rules or {}).get("extracted_claims", [])[:20]
    if claims:
        lines.append("Stated claims sampled from docs/policy:")
        lines.extend(f"- {c}" for c in claims)
        lines.append("")

    lines.extend(["## Model & invariants (Phase 2)", ""])
    flows = model.get("flows", [])
    if flows:
        lines.append(
            _table(
                ["Flow", "Entry", "Critical", "Value sinks", "Trust boundaries"],
                [
                    [f.get("id"), f.get("entry"), "yes" if f.get("critical") else "no",
                     ", ".join(f.get("value_sinks", [])), ", ".join(f.get("trust_boundaries", []))]
                    for f in flows
                ],
            )
        )
        lines.append("")
    inv_rows = [
        [i.get("id"), i.get("statement"), i.get("category"), ", ".join(i.get("applies_to", []))]
        for i in (invariants.get("invariants", []) if invariants else [])
    ]
    if inv_rows:
        lines.append(_table(["Invariant", "Statement", "Class", "Applies to"], inv_rows))
        lines.append("")

    lines.extend(["## Divergences (Phase 3)", ""])
    if divergences:
        lines.append(
            _table(
                ["ID", "Kind", "Flow", "Expected", "Observed", "Location", "Confidence"],
                [
                    [d.get("id"), d.get("kind"), d.get("flow_id"), d.get("expected"),
                     d.get("observed"), f"{d.get('file')}:{d.get('line')}" if d.get("file") else "",
                     d.get("confidence")]
                    for d in divergences
                ],
            )
        )
    else:
        lines.append("No divergences recorded (this may mean the sweep was not run).")
    lines.append("")

    lines.extend(["## Hypotheses & experiments (Phase 4–5)", ""])
    if hypotheses:
        rows = []
        for h in hypotheses:
            runs = experiments_by_hyp.get(str(h.get("id")), [])
            run_label = "; ".join(f"{r.get('id')}:{r.get('status')}/{r.get('verdict')}" for r in runs) or "none"
            classification = classification_by_hyp.get(str(h.get("id")), {})
            severity = classification.get("severity", "unclassified")
            tier = classification.get("proof_tier", "candidate")
            rows.append([h.get("id"), h.get("lens"), h.get("divergence_id"), h.get("statement"),
                         h.get("confidence"), f"{severity} / {tier}", run_label])
        lines.append(
            _table(
                ["ID", "Lens", "Divergence", "Hypothesis", "Conf.", "Severity / tier", "Experiments"],
                rows,
            )
        )
    else:
        lines.append("No hypotheses recorded.")
    lines.append("")

    lines.extend(["## Adversarial filtering (Phase 6)", ""])
    if disproofs:
        lines.append(
            _table(
                ["ID", "Hypothesis", "Verdict", "Blocking", "Unknown", "Rationale"],
                [
                    [d.get("id"), d.get("hypothesis_id"), d.get("verdict"),
                     ", ".join(d.get("blocking_checks", [])), ", ".join(d.get("unknown_checks", [])),
                     d.get("rationale")]
                    for d in disproofs
                ],
            )
        )
    else:
        lines.append("No adversarial checks recorded. Findings are unfiltered.")
    lines.append("")

    lines.extend(["## Assumptions & chains (Phase 4)", ""])
    if assumptions:
        lines.append(
            _table(
                ["ID", "Class", "Assumption", "Violator / primitive", "Trusted actor", "Status"],
                [
                    [a.get("id"), a.get("assumption_class"), a.get("statement"),
                     f"{a.get('violator', '')} / {a.get('primitive', '')}",
                     "yes" if a.get("trusted_actor") else "no", a.get("status")]
                    for a in assumptions
                ],
            )
        )
    else:
        lines.append("No assumption inventory recorded.")
    lines.append("")
    if chains:
        lines.append(
            _table(
                ["Chain", "Order", "Sink", "Edges"],
                [
                    [c.get("id"), " -> ".join(c.get("order", [])), c.get("sink_id"),
                     len(c.get("edges", []))]
                    for c in chains
                ],
            )
        )
        lines.append("")
    else:
        lines.append("No multi-step chains recorded.")
        lines.append("")

    lines.extend(["## Coverage & remaining gaps (Phase 6)", ""])
    if coverage:
        cov_summary = coverage.get("summary", {})
        lines.append(
            f"**Covered:** {cov_summary.get('flows_covered', 0)}/{cov_summary.get('flows_total', 0)} flows "
            f"({coverage.get('ratio', 0):.0%}); extractor confidence `{coverage.get('confidence')}`."
        )
        lines.append("")
        gaps = coverage.get("gaps", [])
        if gaps:
            lines.append(
                _table(
                    ["Gap", "Type", "Why it is open", "Next phase", "Next tool"],
                    [
                        [g.get("id"), g.get("type"), g.get("description"),
                         g.get("next_phase"), g.get("next_tool")]
                        for g in gaps
                    ],
                )
            )
            lines.append("")
        else:
            lines.append("No open gaps recorded by the last coverage pass.")
            lines.append("")
    else:
        lines.append("Coverage has not been measured. Run `coverage_check` before trusting completeness.")
        lines.append("")

    if rounds:
        lines.extend(["## Coverage rounds", ""])
        lines.append(
            _table(
                ["Round", "Status", "Outcome", "Gaps selected", "New DIV/H/E", "Stop reason"],
                [
                    [r.get("round"), r.get("status"), r.get("outcome"),
                     len(r.get("gaps_selected", [])),
                     f"{r.get('new_divergences', 0)}/{r.get('new_hypotheses', 0)}/{r.get('new_experiments', 0)}",
                     r.get("stop_reason")]
                    for r in rounds
                ],
            )
        )
        lines.append("")

    lines.extend(["## Verified findings", ""])
    if verified_findings:
        for finding in verified_findings:
            runs = experiments_by_hyp.get(str(finding.get("id")), [])
            classification = classification_by_hyp.get(str(finding.get("id")), {})
            lines.extend(
                [
                    f"### {finding.get('id')} — {finding.get('lens')}",
                    "",
                    f"**Severity / tier.** {classification.get('severity', 'unclassified')} / "
                    f"{classification.get('proof_tier', 'candidate')}",
                    "",
                    f"**Root cause / statement.** {finding.get('statement')}",
                    "",
                    f"**Falsifiable prediction.** {finding.get('falsifiable_prediction')}",
                    "",
                    f"**Impact sink.** {finding.get('sink')}",
                    "",
                    "**Preconditions.**",
                    *[f"- {p}" for p in finding.get("preconditions", [])],
                    "",
                    "**Evidence.**",
                    *[f"- {e}" for e in finding.get("evidence", [])],
                    *[f"- [FUZZED] experiment {r.get('id')}: {r.get('artifact')} (exit {r.get('returncode')})" for r in runs],
                    "",
                    "**Remediation.** Validate the invariant at the divergence site, then enforce the "
                    "missing check/constraint in the affected flow. (Analyst to finalize.)",
                    "",
                ]
            )
    else:
        lines.append("No experimentally verified findings. Do not submit candidates as findings.")
        lines.append("")

    if inp.include_theoretical and candidates:
        lines.extend(["## Unverified candidates (theoretical)", ""])
        for h in candidates:
            lines.extend(
                [
                    f"### {h.get('id')} — {h.get('lens')}",
                    "",
                    f"{h.get('statement')}",
                    "",
                    f"- Divergence: {h.get('divergence_id')}",
                    f"- Prediction: {h.get('falsifiable_prediction')}",
                    f"- Evidence: {'; '.join(h.get('evidence', []))}",
                    "",
                ]
            )

    if issues:
        lines.extend(["## Agent feedback & missing tools", ""])
        lines.append(
            _table(
                ["ID", "Kind", "Severity", "Title", "Requested change"],
                [
                    [issue.get("id"), issue.get("kind"), issue.get("severity"),
                     issue.get("title"), issue.get("requested_change")]
                    for issue in issues
                ],
            )
        )
        lines.append("")

    lines.extend(["## What we did not conclude", ""])
    if candidates:
        lines.append(
            f"- {len(candidates)} surviving candidate(s) have no executed confirmation: "
            + ", ".join(str(h.get("id")) for h in candidates[:30])
        )
    if rejected:
        lines.append(
            f"- {len(rejected)} hypothesis(es) were disproved and are retained in the ledger: "
            + ", ".join(str(h.get("id")) for h in rejected[:30])
        )
    if coverage.get("gaps"):
        lines.append(f"- {len(coverage.get('gaps', []))} coverage gap(s) remain open; see the coverage table.")
    if not candidates and not rejected and not coverage.get("gaps"):
        lines.append("- Nothing recorded as unresolved. Verify that the campaign actually ran the coverage pass.")
    lines.append("")

    lines.extend(
        [
            "## Evidence & limitations",
            "",
            "Labels: `[FACT] [OBSERVED] [SEARCHED] [FUZZED] [CODE] [DEDUCED] [ASSUMED]`.",
            "Unlabeled claims are not findings. A hypothesis without an executed experiment is a candidate.",
            "",
        ]
    )
    if not boundaries.get("non_destructive", True):
        lines.append("> Warning: non-destructive mode was disabled for this campaign.")

    return ReportOutput(
        markdown="\n".join(lines) + "\n",
        summary=summary,
        reports_dir=rel_to(reports_dir, ctx.workspace),
        report_files=[relative for relative, _, _, _ in report_entries],
    )


TOOLS: list[ToolSpec] = [  # type: ignore[list-item]
    disprove_finding,
    verify_citations,
    classify_finding,
    coverage_check,
    start_round,
    close_round,
    close_session,
    start_campaign,
    campaign_status,
    report_issue,
    draft_finding_report,
    generate_report,
]

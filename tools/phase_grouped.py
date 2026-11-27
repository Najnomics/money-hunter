"""Phase-level action tools.

In plain English: instead of showing the agent 40 tiny tools, we show one tool
per phase and let an `action` choose the exact step.  The underlying handlers,
schemas, gates, and artifacts are unchanged; this file is a thin dispatcher.

Toolset selection:
  APEX_TOOLSET=core    grouped tools + report_issue (default)
  APEX_TOOLSET=full    grouped + all legacy tools
  APEX_TOOLSET=legacy  only the original granular tools
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from runtime import DispatchResult, ToolContext, ToolError, ToolSpec, tool
from schemas.common import ApexModel
from tools import (
    phase0_ground,
    phase1_research,
    phase2_model,
    phase3_divergence,
    phase4_specialists,
    phase5_sandbox,
    phase6_validate,
)


class GroupInput(ApexModel):
    action: str = Field(..., description="Action inside this phase; see the tool description.")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific arguments, e.g. {'divergence_id': 'DIV-0001'}.",
    )


class GroupOutput(ApexModel):
    action: str = ""
    tool: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


def _specs(*items):
    return {spec.name: spec for spec in items}


PHASE0 = _specs(
    phase0_ground.parse_scope,
    phase0_ground.set_rules,
    phase0_ground.lock_boundaries,
    phase0_ground.assess_environment,
)
PHASE1 = _specs(
    phase1_research.ingest_docs,
    phase1_research.review_past_audits,
    phase1_research.check_intel,
    phase1_research.cves_intel,
)
PHASE2 = _specs(
    phase2_model.map_state_flows,
    phase2_model.define_invariants,
    phase2_model.define_state_vocabulary,
    phase2_model.define_sinks,
    phase2_model.make_blind_skeleton,
    phase2_model.record_prediction,
)
PHASE3 = _specs(
    phase3_divergence.ast_divergence_mapper,
    phase3_divergence.targeted_static_sweep,
    phase3_divergence.diff_prediction,
    phase3_divergence.sweep_inventory,
)
PHASE4 = _specs(
    phase4_specialists.dimensional_checker,
    phase4_specialists.reverse_engineer_tool,
    phase4_specialists.state_machine_breaker,
    phase4_specialists.trust_boundary_prober,
    phase4_specialists.assumption_inventory,
    phase4_specialists.run_battery,
    phase4_specialists.chain_hypotheses,
    phase4_specialists.seed_from_research,
    phase4_specialists.never_generated_check,
)
PHASE5 = _specs(
    phase5_sandbox.sandbox_forge,
    phase5_sandbox.invariant_tester,
    phase5_sandbox.record_experiment,
    phase5_sandbox.queue_cartesian_g3,
    phase5_sandbox.execute_queued_g3,
)
PHASE6_VALIDATE = _specs(
    phase6_validate.disprove_finding,
    phase6_validate.verify_citations,
    phase6_validate.classify_finding,
    phase6_validate.coverage_check,
    phase6_validate.start_round,
    phase6_validate.close_round,
)
PHASE6_REPORT = _specs(
    phase6_validate.draft_finding_report,
    phase6_validate.generate_report,
)
CAMPAIGN = _specs(
    phase6_validate.start_campaign,
    phase6_validate.campaign_status,
    phase6_validate.close_session,
)

# Friendly action names -> concrete tool names.
ALIASES = {
    "scope": "parse_scope",
    "rules": "set_rules",
    "boundaries": "lock_boundaries",
    "environment": "assess_environment",
    "docs": "ingest_docs",
    "audits": "review_past_audits",
    "intel": "check_intel",
    "cves": "cves_intel",
    "flows": "map_state_flows",
    "invariants": "define_invariants",
    "vocab": "define_state_vocabulary",
    "sinks": "define_sinks",
    "skeleton": "make_blind_skeleton",
    "prediction": "record_prediction",
    "ast": "ast_divergence_mapper",
    "sweep": "targeted_static_sweep",
    "prediction_diff": "diff_prediction",
    "inventory": "sweep_inventory",
    "dimensional": "dimensional_checker",
    "reverse": "reverse_engineer_tool",
    "state": "state_machine_breaker",
    "trust": "trust_boundary_prober",
    "assumptions": "assumption_inventory",
    "battery": "run_battery",
    "chain": "chain_hypotheses",
    "seed": "seed_from_research",
    "never_generated": "never_generated_check",
    "sandbox": "sandbox_forge",
    "test": "invariant_tester",
    "record": "record_experiment",
    "cartesian": "queue_cartesian_g3",
    "queue_g3": "queue_cartesian_g3",
    "execute_g3": "execute_queued_g3",
    "execute": "execute_queued_g3",
    "disprove": "disprove_finding",
    "citations": "verify_citations",
    "classify": "classify_finding",
    "coverage": "coverage_check",
    "round_start": "start_round",
    "round_close": "close_round",
    "draft": "draft_finding_report",
    "generate": "generate_report",
    "start": "start_campaign",
    "status": "campaign_status",
    "close": "close_session",
}


def _dispatch(ctx: ToolContext, inp: GroupInput, specs: dict[str, ToolSpec], group: str) -> DispatchResult:
    action = ALIASES.get(inp.action, inp.action)
    child = specs.get(action)
    if child is None:
        raise ToolError(
            f"unknown action {inp.action!r} for {group}",
            details={"available_actions": sorted(specs)},
        )
    payload = dict(inp.payload or {})
    try:
        child_input = child.input_model.model_validate(payload)
    except Exception as exc:
        raise ToolError(
            f"invalid payload for {group}/{inp.action}: {exc}",
            details=getattr(exc, "errors", lambda: None)(),
        ) from exc
    result = child.handler(ctx, child_input)
    return DispatchResult(spec=child, result=result)


def _group_tool(name: str, phase: int, actions: str, specs: dict[str, ToolSpec], summary: str) -> ToolSpec:
    @tool(
        name=name,
        phase=phase,
        section="grouped",
        summary=f"{summary} Actions: {actions}. Put action-specific fields in `payload`.",
        input_model=GroupInput,
        output_model=GroupOutput,
        write_mode="dispatch",
        tags=("grouped",),
    )
    def handler(ctx: ToolContext, inp: GroupInput) -> DispatchResult:
        return _dispatch(ctx, inp, specs, name)

    return handler


phase0_ground_tool = _group_tool(
    "ground",
    0,
    "scope | rules | boundaries | environment",
    PHASE0,
    "Phase 0: scope, rules, boundaries, environment.",
)
phase1_research_tool = _group_tool(
    "research",
    1,
    "docs | audits | intel | cves",
    PHASE1,
    "Phase 1: docs, past audits, intel, CVEs.",
)
phase2_model_tool = _group_tool(
    "model",
    2,
    "flows | invariants | vocab | sinks | skeleton | prediction",
    PHASE2,
    "Phase 2: model, invariants, state vocabulary, sinks, blind prediction.",
)
phase3_verify_tool = _group_tool(
    "verify",
    3,
    "ast | sweep | prediction_diff | inventory",
    PHASE3,
    "Phase 3: map model to code, sweep, prediction diff, inventory.",
)
phase4_analyze_tool = _group_tool(
    "analyze",
    4,
    "dimensional | reverse | state | trust | assumptions | battery | chain | seed | never_generated",
    PHASE4,
    "Phase 4: choose the lens that matches the divergence. "
    "Use dimensional for arithmetic/decimals/rates/units; reverse for binaries/bytecode/minified code; "
    "state for init/async/callbacks/reentrancy/lifecycle; trust for auth/input/oracle/privilege paths; "
    "assumptions to inventory silent beliefs; battery for vault/lifecycle/boundary triggers "
    "(empty vault checks load the default share-price families); "
    "chain to join hypotheses into multi-step paths; "
    "seed to turn intel/past-audits/families into hypotheses; "
    "never_generated to fill mutator × value-var pairs that no hypothesis touches.",
)
phase5_experiment_tool = _group_tool(
    "experiment",
    5,
    "sandbox | test | record | cartesian | execute_g3",
    PHASE5,
    "Phase 5: sandbox, distinguishing invariant test, recorded experiment, "
    "cartesian queue of top public mutator × value-sink G3 tests, "
    "execute_g3 to run those tests with local forge (never submit).",
)
phase6_validate_tool = _group_tool(
    "validate",
    6,
    "disprove | citations | classify | coverage | round_start | round_close",
    PHASE6_VALIDATE,
    "Phase 6: kill-pass, citations, severity, coverage, rounds.",
)
phase6_report_tool = _group_tool(
    "report",
    6,
    "draft | generate",
    PHASE6_REPORT,
    "Phase 6: draft one finding report, then generate the campaign report.",
)
campaign_tool = _group_tool(
    "campaign",
    6,
    "start | status | close",
    CAMPAIGN,
    "Bind a target, inspect status, or close a session. Available at any phase.",
)
# `campaign` is meta and must bypass phase gates.
object.__setattr__(campaign_tool, "always_available", True)


TOOLS: list[ToolSpec] = [  # type: ignore[list-item]
    campaign_tool,
    phase0_ground_tool,
    phase1_research_tool,
    phase2_model_tool,
    phase3_verify_tool,
    phase4_analyze_tool,
    phase5_experiment_tool,
    phase6_validate_tool,
    phase6_report_tool,
]

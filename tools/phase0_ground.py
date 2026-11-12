"""Phase 0 — Ground Zero (scoping and guardrails).

In plain English: before reading any code, decide what the agent is allowed
to touch, what the system promises, and what tests are forbidden.  The output
is the campaign's "rules of engagement" file.
"""
from __future__ import annotations

import re
from collections import Counter

from adapters import detect_profile, manifest_files
from adapters.generic_ast import language_of
from fsutil import is_binary, read_text, rel_to, walk_files
from runtime import ToolContext, ToolSpec, tool
from schemas.common import TargetProfile
from schemas.phase0 import (
    BoundariesInput,
    BoundariesOutput,
    Component,
    EnvironmentInput,
    EnvironmentOutput,
    InvariantRule,
    RulesInput,
    RulesOutput,
    ScopeInput,
    ScopeOutput,
)

MODAL_RE = re.compile(r"\b(must|should|shall|never|always|only|required|forbidden|may)\b", re.I)
POLICY_EXTS = {".md", ".txt", ".rst", ".adoc", ".json", ".yaml", ".yml", ".toml"}
DEFAULT_SCALE = {
    "critical": "Direct, unprivileged loss of funds or full system compromise.",
    "high": "Conditional loss of funds, privilege escalation, or persistent DoS.",
    "medium": "Limited impact requiring unusual preconditions or partial control.",
    "low": "Minor information leak, griefing, or defense-in-depth gap.",
    "info": "No direct security impact.",
}


@tool(
    name="parse_scope",
    phase=0,
    section="scope",
    summary="Parse repos/endpoints/addresses/binaries into an allowlist and detect the TargetProfile.",
    input_model=ScopeInput,
    output_model=ScopeOutput,
    tags=("scoping", "profile"),
)
def parse_scope(ctx: ToolContext, inp: ScopeInput) -> ScopeOutput:
    roots = [ctx.resolve(r) for r in (inp.repos or ["."])]
    files = walk_files(roots, max_files=inp.max_files)
    detected_profile, scores = detect_profile(ctx.workspace, files)

    raw_profile = inp.profile.value if isinstance(inp.profile, TargetProfile) else str(inp.profile)
    if raw_profile != TargetProfile.UNKNOWN.value:
        profile = TargetProfile(raw_profile)
    else:
        profile = detected_profile

    manifests = [rel_to(p, ctx.workspace) for p in manifest_files(files)]
    languages = Counter(language_of(f) for f in files if language_of(f) != "unknown")

    components: list[Component] = []
    for root in roots:
        if root.is_file():
            comp_files = [root]
        else:
            comp_files = [f for f in files if root in f.parents or f == root]
        comp_langs = sorted({language_of(f) for f in comp_files if language_of(f) != "unknown"})
        components.append(
            Component(
                name=root.name or "target",
                kind="repo" if root.is_dir() else "artifact",
                paths=[rel_to(root, ctx.workspace)],
                languages=comp_langs,
                manifests=[rel_to(p, ctx.workspace) for p in manifest_files(comp_files)],
            )
        )

    for endpoint in inp.endpoints:
        components.append(Component(name=endpoint, kind="endpoint", paths=[]))
    for address in inp.addresses:
        components.append(Component(name=address, kind="deployment", paths=[]))
    for binary in inp.binaries:
        path = ctx.resolve(binary)
        components.append(
            Component(
                name=path.name,
                kind="binary",
                paths=[rel_to(path, ctx.workspace)],
                manifests=[],
            )
        )

    allowlist = [str(r) for r in inp.repos] + list(inp.endpoints) + list(inp.addresses) + list(inp.binaries)
    if not allowlist:
        allowlist = [rel_to(roots[0], ctx.workspace)]

    notes = None
    if inp.notes:
        notes = inp.notes
    if profile == TargetProfile.UNKNOWN:
        notes = (notes + " " if notes else "") + "No profile signals detected; set --profile explicitly."

    return ScopeOutput(
        target_profile=profile,
        components=components,
        allowlist=sorted(set(allowlist)),
        detected_languages=dict(languages.most_common()),
        manifests=sorted(set(manifests)),
        file_count=len(files),
        profile_scores=scores,
        notes=notes,
    )


@tool(
    name="set_rules",
    phase=0,
    section="rules",
    summary="Extract invariants, policy, bounty rules, and severity definitions.",
    input_model=RulesInput,
    output_model=RulesOutput,
    tags=("rules", "invariants"),
)
def set_rules(ctx: ToolContext, inp: RulesInput) -> RulesOutput:
    sources = list(inp.sources)
    claims: list[str] = []
    policy_text: list[str] = []

    for raw in inp.policy_files:
        path = ctx.resolve(raw)
        candidates = [path] if path.is_file() else walk_files([path], max_files=200, exts=POLICY_EXTS)
        for candidate in candidates:
            sources.append(rel_to(candidate, ctx.workspace))
            if is_binary(candidate):
                continue
            for idx, line in enumerate(read_text(candidate).splitlines(), start=1):
                stripped = line.strip()
                if len(stripped) < 20:
                    continue
                if MODAL_RE.search(stripped):
                    claim = f"{rel_to(candidate, ctx.workspace)}:{idx}: {stripped[:300]}"
                    claims.append(claim)
                    if len(policy_text) < 200:
                        policy_text.append(stripped[:300])

    invariants = [
        InvariantRule(
            id=f"INV-{idx:03d}",
            statement=statement.strip(),
            category="stated",
            source="explicit",
        )
        for idx, statement in enumerate(inp.invariants, start=1)
        if statement.strip()
    ]

    bounty = inp.bounty_url
    if not bounty:
        bounty_hits = [c for c in claims if re.search(r"bounty|reward|payout", c, re.I)]
        if bounty_hits:
            bounty = bounty_hits[0][:300]

    scale = dict(DEFAULT_SCALE)
    scale.update(inp.severity_scale or {})

    notes: list[str] = []
    if not invariants:
        notes.append("No explicit invariants supplied; add them before Phase 2 to make the gate meaningful.")
    if not claims and inp.policy_files:
        notes.append("Policy files were read but no must/should/never statements were extracted.")

    return RulesOutput(
        invariants=invariants,
        policy="\n".join(policy_text) if policy_text else None,
        bounty=bounty,
        severity_scale=scale,
        sources=sorted(set(sources)),
        extracted_claims=claims[:200],
        notes=notes,
    )


@tool(
    name="lock_boundaries",
    phase=0,
    section="boundaries",
    summary="Lock out-of-scope exclusions, rate limits, non-destructive rules, and forbidden actions.",
    input_model=BoundariesInput,
    output_model=BoundariesOutput,
    tags=("guardrails", "safety"),
)
def lock_boundaries(ctx: ToolContext, inp: BoundariesInput) -> BoundariesOutput:
    forbidden = list(inp.forbidden_actions)
    defaults = [
        "No requests or transactions against hosts/assets outside the allowlist.",
        "No destructive, state-mutating, or load-generating tests against live targets.",
        "No exploitation of real user data; use synthetic fixtures.",
        "PoCs run only in local, fork, devnet, or sandbox environments.",
        "No credential exfiltration, persistence, or lateral movement.",
    ]
    for rule in defaults:
        if rule not in forbidden:
            forbidden.append(rule)

    hard_rules = [
        "A tool may not run until its phase gate is complete.",
        "Every finding must cite file:line or a captured experiment log.",
        "Unlabeled claims are not findings; use [FACT]/[CODE]/[OBSERVED]/[FUZZED].",
    ]
    if inp.non_destructive:
        hard_rules.append("Non-destructive mode is ON: no writes to the target.")

    return BoundariesOutput(
        out_of_scope=list(inp.out_of_scope),
        rate_limits=list(inp.rate_limits) or ["No automated fuzzing against live endpoints."],
        forbidden_actions=forbidden,
        non_destructive=inp.non_destructive,
        allowed_environments=list(inp.allowed_environments),
        hard_rules=hard_rules,
        notes=inp.notes,
    )


@tool(
    name="assess_environment",
    phase=0,
    section="environment",
    summary="Prove the sandbox works: identity, tools, fixtures, and offline limits.",
    input_model=EnvironmentInput,
    output_model=EnvironmentOutput,
    tags=("environment", "readiness"),
)
def assess_environment(ctx: ToolContext, inp: EnvironmentInput) -> EnvironmentOutput:
    kinds = {check.kind for check in inp.checks}
    passed = bool(inp.checks) and all(check.passed for check in inp.checks)
    complete = {"identity", "tool", "fixture"}.issubset(kinds)
    ready = passed and complete
    notes: list[str] = []
    if not inp.checks:
        notes.append("No readiness checks recorded. A sandbox that cannot prove itself is a blocker.")
    missing = {"identity", "tool", "fixture"} - kinds
    if missing:
        notes.append("Missing check kind(s): " + ", ".join(sorted(missing)))
    failed = [check.name for check in inp.checks if not check.passed]
    if failed:
        notes.append("Failing checks: " + ", ".join(failed))
    summary = (
        f"{len(inp.checks)} readiness checks; ready={ready}; "
        f"offline limits={len(inp.offline_limits)}"
    )
    return EnvironmentOutput(
        ready=ready,
        checks=inp.checks,
        offline_limits=inp.offline_limits,
        reset_command=inp.reset_command,
        summary=summary,
        notes=notes,
    )


TOOLS: list[ToolSpec] = [  # type: ignore[list-item]
    parse_scope,
    set_rules,
    lock_boundaries,
    assess_environment,
]

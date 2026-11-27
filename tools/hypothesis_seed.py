"""Helpers that turn intel, past audits, and protocol families into hypotheses.

Also implements the never-generated cartesian self-check: every state-changing
external function × every value-bearing state var must be touched by at least
one hypothesis, or one is generated.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from fsutil import read_text, walk_files
from runtime import ToolContext
from schemas.common import Confidence
from schemas.phase3 import Divergence
from schemas.phase4 import Hypothesis
from tools._shared import existing_ids, next_id, require_divergence, source_exts
from tools.phase3_divergence import GETTER_OR_MODIFIER, SINK_WORDS, VIEWISH_SETTLEMENT
from tools.protocol_families import PROTOCOL_FAMILIES, ProtocolFamily, families_for_battery

VALUE_BEARING_RE = re.compile(
    r"(asset|share|balance|supply|reserve|nav|principal|claim|bounty|margin|"
    r"stake|liquidity|debt|collateral|fee|yield|price|hwm|watermark|"
    r"unassigned|escrow|pledge|receipt|rebate|accrual|premium|surplus|"
    r"deficit|equity|tranche|deposit|withdraw|mint|burn|oracle|mode)",
    re.I,
)
STORAGE_DECL_RE = re.compile(
    r"(?:mapping\s*\([^;{]+\)\s*|\b(?:uint256|int256|uint128|uint64|uint32|int128)\b)\s+"
    r"(?:(?:public|internal|private|constant|immutable)\s+)*([A-Za-z_]\w*)",
)
WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SKIP_FNS = {
    "constructor", "fallback", "receive", "initialize", "initializer",
}
FAMILY_MARK = "family:"
PAIR_MARK = "pair:"


def family_ids_in_hypotheses(hypotheses: Iterable[dict]) -> set[str]:
    found: set[str] = set()
    for hyp in hypotheses:
        blob = _hyp_blob(hyp)
        for family in PROTOCOL_FAMILIES:
            if f"{FAMILY_MARK}{family.id}" in blob:
                found.add(family.id)
    return found


def _hyp_blob(hyp: dict | Hypothesis) -> str:
    if isinstance(hyp, Hypothesis):
        data = hyp.model_dump()
    else:
        data = hyp
    parts = [
        str(data.get("statement") or ""),
        str(data.get("falsifiable_prediction") or ""),
        str(data.get("sink") or ""),
        str(data.get("title") or ""),
        str(data.get("summary") or ""),
        str(data.get("experiment_plan") or ""),
        " ".join(str(x) for x in data.get("evidence") or []),
        " ".join(str(x) for x in data.get("preconditions") or []),
        str(data.get("family") or ""),
    ]
    return " ".join(parts).lower()


def mentions(text: str, token: str) -> bool:
    token = (token or "").strip()
    if len(token) < 2:
        return False
    return re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(token.lower())}(?![A-Za-z0-9_])",
        text.lower(),
    ) is not None


def hyp_touches_pair(hyp: dict | Hypothesis, function: str, var: str) -> bool:
    blob = _hyp_blob(hyp)
    return mentions(blob, function) and mentions(blob, var)


def ensure_anchor_divergence(ctx: ToolContext, divergence_id: str | None = None) -> dict:
    """Return a real DIV-* so Phase 4 hypotheses stay gate-legal.

    Research/battery seeding may run before a useful Phase 3 hit exists. In that
    case we write a synthetic research_seed divergence rather than forging a
    hypothesis with a dangling id.
    """
    if divergence_id:
        return require_divergence(ctx, divergence_id)
    existing = [d for d in ctx.state.divergences() if d.get("id")]
    if existing:
        return existing[0]
    div = Divergence(
        id="DIV-SEED-0001",
        kind="research_seed",
        expected="Every modelled value path has a falsifiable hypothesis.",
        observed="No Phase 3 divergence existed; research/battery seeding created an anchor.",
        confidence=Confidence.LOW,
        status="candidate",
        source_tool="seed_from_research",
        evidence=["[DEDUCED] synthetic anchor so Phase 4 can persist hypotheses"],
    )
    ctx.state.write_section(
        3,
        "research_divs",
        {"divergences": [div.model_dump(mode="json")]},
        "seed_from_research",
    )
    return div.model_dump(mode="json")


def _make_hypothesis(
    ctx: ToolContext,
    reserved: set[str],
    *,
    divergence_id: str,
    lens: str,
    statement: str,
    prediction: str,
    sink: str,
    evidence: list[str],
    family: str | None = None,
    title: str | None = None,
    confidence: Confidence = Confidence.LOW,
) -> Hypothesis:
    new_id = next_id(reserved | existing_ids(ctx, 4), "H")
    reserved.add(new_id)
    marks = list(evidence)
    if family:
        marks.append(f"[DEDUCED] {FAMILY_MARK}{family}")
    return Hypothesis(
        id=new_id,
        divergence_id=divergence_id,
        lens=lens,
        statement=statement,
        falsifiable_prediction=prediction,
        sink=sink,
        title=title,
        summary=statement.split(".")[0][:240] if statement else title,
        preconditions=[
            f"Divergence {divergence_id} is reachable through its modelled entrypoint.",
            "The attacker controls the inputs identified in the prediction.",
        ],
        experiment_plan=(
            "Provision the profile sandbox (Phase 5), encode the prediction as an "
            "invariant test, run it, and capture stdout/stderr under .apex/experiments/."
        ),
        confidence=confidence,
        status="open",
        evidence=marks,
        family=family,
    )


def hypotheses_from_families(
    ctx: ToolContext,
    divergence: dict,
    reserved: set[str],
    battery: str = "vault",
    existing: Iterable[dict] | None = None,
) -> list[Hypothesis]:
    present = family_ids_in_hypotheses(existing or ctx.state.hypotheses())
    out: list[Hypothesis] = []
    for family in families_for_battery(battery):
        if family.id in present:
            continue
        out.append(_hypothesis_from_family(ctx, reserved, divergence, family))
        present.add(family.id)
    return out


def _hypothesis_from_family(
    ctx: ToolContext,
    reserved: set[str],
    divergence: dict,
    family: ProtocolFamily,
) -> Hypothesis:
    return _make_hypothesis(
        ctx,
        reserved,
        divergence_id=str(divergence.get("id")),
        lens=f"battery:{family.battery}",
        statement=family.statement,
        prediction=family.prediction,
        sink=family.sink_hint,
        evidence=[
            f"[DEDUCED] protocol family {family.id}",
            f"[SEARCHED] bundled intel-patterns/{family.id}",
        ],
        family=family.id,
        title=family.title,
        confidence=Confidence.MEDIUM,
    )


def hypotheses_from_intel(
    ctx: ToolContext,
    divergence: dict,
    reserved: set[str],
    existing: Iterable[dict] | None = None,
    limit: int = 20,
) -> list[Hypothesis]:
    intel = ctx.state.section(1, "intel") or {}
    matches = list(intel.get("matches") or [])
    techniques = list(intel.get("techniques") or [])
    present = family_ids_in_hypotheses(existing or ctx.state.hypotheses())
    blob_existing = " ".join(_hyp_blob(h) for h in (existing or ctx.state.hypotheses()))
    out: list[Hypothesis] = []

    for family in PROTOCOL_FAMILIES:
        if family.id in present:
            continue
        hay = " ".join(
            f"{m.get('title','')} {m.get('snippet','')} {m.get('path','')}" for m in matches
        ).lower()
        hay += " " + " ".join(str(t) for t in techniques).lower()
        if family.id.replace("-", " ") in hay or any(k.lower() in hay for k in family.keywords):
            out.append(_hypothesis_from_family(ctx, reserved, divergence, family))
            present.add(family.id)

    for match in matches:
        if len(out) >= limit:
            break
        title = str(match.get("title") or match.get("path") or "intel match")
        snippet = str(match.get("snippet") or "")
        path = str(match.get("path") or "")
        token = f"intel:{path}"
        if token.lower() in blob_existing:
            continue
        family = _family_for_text(f"{title} {snippet}")
        if family and family.id in present:
            continue
        statement = (
            f"Disclosed technique `{title}` ({path}) may apply to this target: {snippet[:280]}"
        )
        prediction = (
            f"Replay the technique from `{path}` against the target's analogous surface. "
            "If the state var named in the write-up does not move, the match is a false analog."
        )
        hyp = _make_hypothesis(
            ctx,
            reserved,
            divergence_id=str(divergence.get("id")),
            lens="intel",
            statement=statement,
            prediction=prediction,
            sink=family.sink_hint if family else "disclosed analog",
            evidence=[
                f"[SEARCHED] intel {path}",
                snippet[:300] or title,
            ],
            family=family.id if family else None,
            title=title[:200],
        )
        out.append(hyp)
        blob_existing += " " + _hyp_blob(hyp)
        if family:
            present.add(family.id)
    return out[:limit]


def hypotheses_from_audits(
    ctx: ToolContext,
    divergence: dict,
    reserved: set[str],
    existing: Iterable[dict] | None = None,
    limit: int = 20,
) -> list[Hypothesis]:
    audits = ctx.state.section(1, "audits") or {}
    findings = list(audits.get("past_findings") or [])
    blob_existing = " ".join(_hyp_blob(h) for h in (existing or ctx.state.hypotheses()))
    out: list[Hypothesis] = []
    for finding in findings:
        if len(out) >= limit:
            break
        if finding.get("acknowledged"):
            # Known issue for dedupe, not a new lead — unless the program still pays.
            continue
        title = str(finding.get("title") or "")
        source = str(finding.get("source") or "")
        excerpt = str(finding.get("excerpt") or "")
        token = f"audit:{finding.get('dedupe_key') or title}"
        if token.lower() in blob_existing:
            continue
        family = _family_for_text(f"{title} {excerpt}")
        statement = (
            f"Past audit finding `{title}` at {source} describes a class that may still "
            f"exist here. Excerpt: {excerpt[:240] or title}"
        )
        prediction = (
            f"Reproduce the past-audit scenario from {source} against this target's "
            "analogous function and value-bearing state. If the analogous var is unchanged, "
            "the class does not apply."
        )
        hyp = _make_hypothesis(
            ctx,
            reserved,
            divergence_id=str(divergence.get("id")),
            lens="past-audit",
            statement=statement,
            prediction=prediction,
            sink=family.sink_hint if family else "past-audit analog",
            evidence=[
                f"[SEARCHED] past audit {source}",
                f"audit:{finding.get('dedupe_key') or title}",
                excerpt[:300] or title,
            ],
            family=family.id if family else None,
            title=title[:200],
        )
        out.append(hyp)
        blob_existing += " " + _hyp_blob(hyp)
    return out


def _family_for_text(text: str) -> ProtocolFamily | None:
    lowered = text.lower()
    best: tuple[int, ProtocolFamily] | None = None
    for family in PROTOCOL_FAMILIES:
        score = sum(1 for k in family.keywords if k.lower() in lowered)
        if family.id.replace("-", " ") in lowered:
            score += 5
        if score and (best is None or score > best[0]):
            best = (score, family)
    return best[1] if best else None


def list_mutators(ctx: ToolContext) -> list[dict]:
    ast_map = ctx.state.section(3, "ast_map") or {}
    surfaces = ast_map.get("surfaces") or []
    mutators: list[dict] = []
    seen: set[str] = set()
    for surface in surfaces:
        name = str(surface.get("name") or "")
        if not name or name.lower() in SKIP_FNS:
            continue
        kind = str(surface.get("kind") or "function")
        if kind not in {"function", "method", "entrypoint", "route"}:
            continue
        if GETTER_OR_MODIFIER.search(name) or VIEWISH_SETTLEMENT.search(name):
            continue
        entry = bool(surface.get("entry"))
        if not entry and not SINK_WORDS.search(name):
            # Keep non-entry mutators that don't look like views: default include
            # if the surface is marked entry, otherwise still include functions
            # that are not getters.
            if kind not in {"function", "method"}:
                continue
        key = name
        if key.lower() in seen:
            continue
        seen.add(key.lower())
        mutators.append(surface)
    return mutators


def list_value_vars(ctx: ToolContext) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()

    def _add(raw: str | None) -> None:
        name = (raw or "").strip()
        if not name or name.lower() in seen:
            return
        if name.lower() in {"i", "j", "x", "y", "ok", "ret", "data", "self", "this"}:
            return
        if not VALUE_BEARING_RE.search(name) and name not in _vocab_forced(ctx):
            return
        seen.add(name.lower())
        names.append(name)

    vocab = ctx.state.section(2, "state_vocab") or {}
    for state in vocab.get("states") or []:
        _add(state.get("var"))
    sinks = ctx.state.section(2, "sinks") or {}
    for sink in sinks.get("sinks") or []:
        _add(sink.get("var"))
        for var in sink.get("vars") or []:
            _add(var)
    flows = (ctx.state.section(2, "flows") or {}).get("flows") or []
    for flow in flows:
        for var in flow.get("value_sinks") or []:
            _add(var)
        for var in flow.get("state_touched") or []:
            _add(var)

    if len(names) < 2:
        for path in _scan_source(ctx)[:80]:
            text = read_text(path, max_bytes=400_000)
            for match in STORAGE_DECL_RE.finditer(text):
                _add(match.group(1))
    return names


def _vocab_forced(ctx: ToolContext) -> set[str]:
    names: set[str] = set()
    vocab = ctx.state.section(2, "state_vocab") or {}
    for state in vocab.get("states") or []:
        var = str(state.get("var") or "")
        if var:
            names.add(var)
    return names


def _scan_source(ctx: ToolContext) -> list[Path]:
    scope = ctx.state.section(0, "scope") or {}
    paths: list[str] = []
    for component in scope.get("components") or []:
        if component.get("kind") in {"repo", "artifact"}:
            paths.extend(component.get("paths") or [])
    roots = [ctx.resolve(p) for p in (paths or ["."])]
    return walk_files(roots, max_files=200, exts=source_exts())


def enumerate_pairs(ctx: ToolContext) -> list[tuple[str, str, dict]]:
    mutators = list_mutators(ctx)
    variables = list_value_vars(ctx)
    pairs: list[tuple[str, str, dict]] = []
    for surface in mutators:
        fn = str(surface.get("name") or "")
        for var in variables:
            pairs.append((fn, var, surface))
    pairs.sort(key=lambda item: -_pair_rank(item[0], item[1]))
    return pairs


def _pair_rank(function: str, var: str) -> int:
    score = 0
    if SINK_WORDS.search(function):
        score += 5
    if VALUE_BEARING_RE.search(function):
        score += 2
    if VALUE_BEARING_RE.search(var):
        score += 3
    return score


def covered_pairs(hypotheses: Iterable[dict | Hypothesis], pairs: list[tuple[str, str, dict]]) -> set[tuple[str, str]]:
    hyps = list(hypotheses)
    covered: set[tuple[str, str]] = set()
    for fn, var, _ in pairs:
        for hyp in hyps:
            if hyp_touches_pair(hyp, fn, var):
                covered.add((fn, var))
                break
    return covered


def hypotheses_for_uncovered_pairs(
    ctx: ToolContext,
    divergence: dict,
    reserved: set[str],
    pairs: list[tuple[str, str, dict]],
    uncovered: list[tuple[str, str, dict]],
    max_generate: int,
) -> list[Hypothesis]:
    out: list[Hypothesis] = []
    for fn, var, surface in uncovered[:max_generate]:
        cite = ""
        if surface.get("file"):
            cite = f"{surface.get('file')}:{surface.get('line') or 1}"
        statement = (
            f"State-changing `{fn}` can move value-bearing `{var}` in a way that "
            "breaks conservation, share pricing, or solvency."
        )
        prediction = (
            f"Call `{fn}` with attacker-controlled inputs while measuring `{var}` "
            "before and after, including a second actor who transacts on the new value. "
            f"If `{var}` is unchanged or the second actor cannot extract, the hypothesis is false."
        )
        evidence = [
            f"[DEDUCED] {PAIR_MARK}{fn}::{var}",
            f"[CODE] {cite}" if cite else f"[DEDUCED] mutator {fn}",
        ]
        out.append(
            _make_hypothesis(
                ctx,
                reserved,
                divergence_id=str(divergence.get("id")),
                lens="never-generated",
                statement=statement,
                prediction=prediction,
                sink=var,
                evidence=evidence,
                title=f"{fn} x {var}",
            )
        )
    return out

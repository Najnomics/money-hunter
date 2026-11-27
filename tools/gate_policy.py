"""Shared Gate 2–4 policy: freeze is impact, distinguishing G3, variant-scoped family kills.

Protocol-agnostic. No program-specific type or address names.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

FREEZE_HYP_RE = re.compile(
    r"(overflow|underflow|uint256\.?max|type\(\s*uint|virtual[ -]?offset|"
    r"virtual[ -]?shares|share[ -]?supply|convertToShares|convertToAssets|"
    r"\bfreeze|\bfrozen|cannot (?:mint|deposit|redeem|withdraw|convert)|"
    r"denial.of.service|\bdos\b|value flow|blocks? (?:a )?value)",
    re.I,
)
UNREACHABLE_RE = re.compile(
    r"(unreachable|astronomical|too (?:expensive|large|big)|not (?:practical|reachable)|"
    r"supply too|cannot be reached|would revert|reverts? (?:on|when|before|at)|"
    r"overflow (?:protect|guard|check)|cap (?:makes|renders) (?:it )?unreachable)",
    re.I,
)
HAPPY_PATH_RE = re.compile(
    r"(happy[ -]?path|round[ -]?trip|seeded fixture|cap is live|"
    r"assert\s*True|intended spec|while solvent|solvent (?:user|path)|"
    r"admin (?:deposits|seeds)|documented behaviour as designed)",
    re.I,
)
CODE_FACT_RE = re.compile(
    r"(code[ -]?fact|natspec|read the (?:source|code)|static inspection|"
    r"no execution|line \d+ (?:says|contains|shows)|comment says|"
    r"source review(?: only)?)",
    re.I,
)
DISTINGUISHING_RE = re.compile(
    r"(attacker|vm\.prank|prank\(|adversarial|first[ -]?tick|zero[ -]?state|"
    r"zero[ -]?nav|second actor|distinguishing|unprivileged|"
    r"ordering (?:attack|swap)|empty (?:vault|pool|market))",
    re.I,
)
WRONG_PROTOCOL_RE = re.compile(
    r"(wrong protocol|wrong target|different protocol|not this (?:pin|target|repo)|"
    r"out of scope protocol|other product|spot/?options|dov leakage|"
    r"does not apply here)",
    re.I,
)
MAPPED_SURFACE_RE = re.compile(r"mapped-surface:([A-Za-z_][A-Za-z0-9_]*)")
CODE_CITE_RE = re.compile(r"\[CODE\]\s+(\S+)")

EXPERIMENT_CLASSES = ("distinguishing", "happy-path", "code-fact", "unknown")


def _blob(parts: Iterable[Any]) -> str:
    return " ".join(str(p or "") for p in parts)


def hyp_text(hyp: dict | None) -> str:
    hyp = hyp or {}
    return _blob(
        [
            hyp.get("statement"),
            hyp.get("falsifiable_prediction"),
            hyp.get("sink"),
            hyp.get("title"),
            hyp.get("summary"),
            hyp.get("experiment_plan"),
            hyp.get("family"),
            hyp.get("variant"),
            " ".join(str(x) for x in hyp.get("evidence") or []),
            " ".join(str(x) for x in hyp.get("preconditions") or []),
        ]
    )


def check_text(check: Any) -> str:
    if isinstance(check, dict):
        return _blob([check.get("name"), check.get("question"), check.get("evidence")])
    return _blob(
        [
            getattr(check, "name", ""),
            getattr(check, "question", ""),
            getattr(check, "evidence", ""),
        ]
    )


def is_freeze_value_flow(hyp: dict | None) -> bool:
    """True when the claim is that a revert/overflow blocks a value flow (freeze = impact)."""
    hyp = hyp or {}
    family = str(hyp.get("family") or "")
    if family == "share-supply-overflow":
        return True
    return bool(FREEZE_HYP_RE.search(hyp_text(hyp)))


def is_unreachable_language(text: str) -> bool:
    return bool(UNREACHABLE_RE.search(text or ""))


def freeze_blocks_are_impact(hyp: dict | None, check: Any) -> bool:
    """A BLOCKS check that calls overflow/revert 'unreachable' is not a G4 kill."""
    if not is_freeze_value_flow(hyp):
        return False
    return is_unreachable_language(check_text(check)) or is_unreachable_language(hyp_text(hyp))


def infer_experiment_class(
    *,
    declared: str = "",
    observation: str = "",
    command: str = "",
    test_code: str = "",
) -> str:
    content = _blob([observation, command, test_code])
    happy = bool(HAPPY_PATH_RE.search(content))
    code_fact = bool(CODE_FACT_RE.search(content))
    distinguishing = bool(DISTINGUISHING_RE.search(content))
    # Observation/log content wins over a self-reported label.
    if code_fact and not distinguishing:
        return "code-fact"
    if happy and not distinguishing:
        return "happy-path"
    if distinguishing:
        return "distinguishing"
    declared_norm = (declared or "").strip().lower()
    if declared_norm in EXPERIMENT_CLASSES:
        return declared_norm
    return "unknown"


def distinguishing_scaffold(function: str, var: str, hypothesis_id: str = "") -> str:
    fn = function or "mutator"
    sink = var or "value"
    hid = hypothesis_id or "H-?"
    return (
        '"""Distinguishing G3 attack — not a happy-path or code-fact check.\n\n'
        f"Hypothesis: {hid}\n"
        f"Attacker path: an unprivileged actor calls `{fn}` after an adversarial\n"
        f"ordering (first-tick / zero-state / second actor transacts on `{sink}`).\n"
        "A seeded solvent round-trip, 'cap is live', or reading natspec is not evidence.\n"
        '"""\n\n'
        "import pytest\n\n\n"
        f"def test_attack_{_ident(fn)}_{_ident(sink)}():\n"
        f"    # 1. Snapshot `{sink}` at first-tick / zero-state (no admin seed).\n"
        f"    # 2. Attacker calls `{fn}` (vm.prank / unprivileged; not the solvent path).\n"
        f"    # 3. Second actor transacts on the new `{sink}`.\n"
        "    # 4. Assert conservation, share pricing, or solvency broke; else fail closed.\n"
        '    raise NotImplementedError("replace with the distinguishing attack, not a round-trip")\n'
    )


def _ident(token: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", token).strip("_")
    return (cleaned or "x")[:40]


def mapped_surface_names(hyp: dict | None) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for match in MAPPED_SURFACE_RE.finditer(hyp_text(hyp)):
        name = match.group(1)
        key = name.lower()
        if key not in seen:
            seen.add(key)
            names.append(name)
    return names


def mapping_attempted(hyp: dict | None) -> bool:
    text = hyp_text(hyp)
    return "mapped-surface:" in text or "analog-unmapped" in text or bool(CODE_CITE_RE.search(text))


def is_wrong_protocol_kill(check: Any) -> bool:
    return bool(WRONG_PROTOCOL_RE.search(check_text(check)))


def family_disprove_scope(hyp: dict | None, variant: str | None, verdict: str) -> tuple[str, str, list[str]]:
    """Family-level G4 kills apply per variant, not per family.

    Returns (verdict, scope, notes). scope is 'variant' | 'hypothesis' | 'family'.
    """
    hyp = hyp or {}
    family = str(hyp.get("family") or "").strip()
    if not family or verdict != "disproved":
        return verdict, "hypothesis", []
    chosen = (variant or hyp.get("variant") or "").strip()
    if not chosen:
        return (
            "needs-variant",
            "family",
            [
                "Family-level G4 kills apply per variant, not per family. "
                "Pass variant=<public mutator or pair>."
            ],
        )
    return (
        "disproved-variant",
        "variant",
        [f"Kill scoped to variant `{chosen}`; family `{family}` remains open for other variants."],
    )


def kills_hypothesis(disproof: dict | None) -> bool:
    disproof = disproof or {}
    return disproof.get("verdict") == "disproved" and disproof.get("scope") != "variant"

"""Protocol-agnostic cartesian pair templates.

Ranked mutator × sink patterns so never-generated fill names a mechanism
(instead of a generic "fn can move var" CSV row) and Gate 3 queues it.

Worded without a specific protocol's types. Tokens such as executionWindow
and freeSettlement are ordinary value-bearing names, not a contest answer key.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from tools.protocol_families import PROTOCOL_FAMILIES


@dataclass(frozen=True)
class PairTemplate:
    id: str
    family: str
    fn_re: re.Pattern[str]
    var_re: re.Pattern[str]
    statement: str
    prediction: str


def _re(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.I)


# Delay-bound names the cartesian must always include even when Phase 2 vocab
# omitted them (99136: no executionWindow var).
DELAY_BOUND_VARS: tuple[str, ...] = (
    "executionWindow",
    "executionWindowSeconds",
    "minPublishTime",
    "orderSettlementWindow",
    "minDelay",
)

PAIR_TEMPLATES: tuple[PairTemplate, ...] = (
    PairTemplate(
        id="pledge-vs-redemption",
        family="refundable-receipt-in-nav",
        fn_re=_re(r"settle"),
        var_re=_re(r"pledge"),
        statement=(
            "Uncollected pledged PnL sitting in `{var}` can fund a `{fn}` "
            "redemption of another cohort."
        ),
        prediction=(
            "Queue a pledged loss, then call `{fn}` so a competing redemption "
            "reads `{var}`. If the redemption is funded from the pledge, the "
            "hypothesis holds; if `{var}` is reserved until the pledge settles, "
            "it is false."
        ),
    ),
    PairTemplate(
        id="reclaimable-mark-in-nav",
        family="refundable-receipt-in-nav",
        fn_re=_re(r"settle|reconcile"),
        var_re=_re(r"sharePrice|totalAssets|\bnav\b|rebate|accrued"),
        statement=(
            "`{fn}` prices shares from a NAV/`{var}` that still contains a "
            "reclaimable receipt, rebate, or mark a later close can return."
        ),
        prediction=(
            "Introduce a reclaimable mark in `{var}`, let an outsider transact "
            "through `{fn}`, then reclaim. If share price moved with the "
            "reclaimable amount, conservation broke."
        ),
    ),
    PairTemplate(
        id="unclamped-rebate",
        family="refundable-receipt-in-nav",
        fn_re=_re(r"executeOpen|executeClose|withdraw|_applyOpen"),
        var_re=_re(r"rebate"),
        statement=(
            "`{fn}` pays or waives `{var}` without a lifetime floor, so a "
            "depth collapse or partial close extracts more than was accrued."
        ),
        prediction=(
            "Open or close at changing depth while measuring `{var}`. If the "
            "rebate is unclamped or a withdraw waives a positive charge, the "
            "hypothesis holds."
        ),
    ),
    PairTemplate(
        id="partial-close-claim",
        family="refundable-receipt-in-nav",
        fn_re=_re(r"executeClose"),
        var_re=_re(r"claim"),
        statement=(
            "A partial `{fn}` nets `{var}` so the residual is stripped to a "
            "dust floor instead of remaining with the trader."
        ),
        prediction=(
            "Partially close while `{var}` is positive. If the residual claim "
            "collapses to a minimum, the hypothesis holds."
        ),
    ),
    PairTemplate(
        id="owner-pool-cash-optionality",
        family="delayed-order-optionality",
        fn_re=_re(r"execute(Order|Open|Close)|executeLiquidation"),
        var_re=_re(r"freeSettlement|freeBalance|poolCash"),
        statement=(
            "After the fill price is public, `{fn}` still reads live `{var}`, "
            "so owner/pool cash or a liquidation cleanup can void or revive a "
            "pinned order."
        ),
        prediction=(
            "Commit an order, publish the price, mutate `{var}`, then `{fn}`. "
            "If execution flips from fill to refund (or the reverse), the order "
            "was an option."
        ),
    ),
    PairTemplate(
        id="increase-vs-close",
        family="delayed-order-optionality",
        fn_re=_re(r"commit"),
        var_re=_re(r"freeSettlement|freeBalance"),
        statement=(
            "A queued `{fn}` increase or close admitted against live `{var}` "
            "can void a previously committed opposite intent."
        ),
        prediction=(
            "Commit a close, then `{fn}` an increase (or the reverse) and "
            "watch `{var}`. If the first intent dies after the price is "
            "public, the hypothesis holds."
        ),
    ),
    PairTemplate(
        id="settle-claim-option",
        family="delayed-order-optionality",
        fn_re=_re(r"settleTraderClaim|settle.*Claim"),
        var_re=_re(r"freeSettlement|freeBalance"),
        statement=(
            "`{fn}` after the pinned price is public can fill or void a queued "
            "open by moving `{var}`."
        ),
        prediction=(
            "Pin a price, then `{fn}` and measure `{var}`. If the queued open "
            "becomes optional, the hypothesis holds."
        ),
    ),
    PairTemplate(
        id="window-delay-bound",
        family="delayed-order-optionality",
        fn_re=_re(r"commit|execute"),
        var_re=_re(r"executionWindow|minDelay|minPublishTime|orderSettlementWindow"),
        statement=(
            "Trader-set `{var}` on `{fn}` is a free option: the fill can sit "
            "on the first tick with no minimum delay, or stretch until a "
            "favorable print."
        ),
        prediction=(
            "Commit with `{var}` at its minimum, then take the first eligible "
            "tick. If that tick is stale relative to public information, or "
            "the window can be stretched after commit, the hypothesis holds."
        ),
    ),
    PairTemplate(
        id="pending-open-nav",
        family="delayed-order-optionality",
        fn_re=_re(r"settle"),
        var_re=_re(r"sharePrice|totalAssets|\bnav\b"),
        statement=(
            "`{fn}` prices `{var}` without the liability of committed but "
            "unexecuted opens, so an epoch can refund a losing queued trade "
            "or ignore it in NAV."
        ),
        prediction=(
            "Commit an open, call `{fn}` before execution, and measure `{var}`. "
            "If NAV ignores the pending liability or the epoch cancels the "
            "open, the hypothesis holds."
        ),
    ),
    PairTemplate(
        id="protection-side-door",
        family="delayed-order-optionality",
        fn_re=_re(r"retry|protect|_arm|assess|evaluate"),
        var_re=_re(r"freeSettlement|rebate|degradedMode|mode"),
        statement=(
            "`{fn}` after a parent fill or commit can consume a latched "
            "protection, collect carry, or ignore queued size while `{var}` "
            "still moves."
        ),
        prediction=(
            "Fill or commit, then `{fn}` before the owner amends. If `{var}` "
            "or the protection state changes against the committed terms, "
            "the hypothesis holds."
        ),
    ),
    PairTemplate(
        id="watermark-rotation",
        family="oracle-staleness-calendar-watermark",
        fn_re=_re(r"apply|rotate|config"),
        var_re=_re(r"acceptedBasket|watermark|configHash|basket"),
        statement=(
            "`{fn}` resets or reuses `{var}` so a rotation, calendar override, "
            "or batch cache drops per-source watermarks or keys off the newest "
            "component time."
        ),
        prediction=(
            "Rotate or override a feed, then read `{var}` through `{fn}`. If a "
            "stale or mixed-calendar tick is accepted, the watermark is wrong."
        ),
    ),
    PairTemplate(
        id="first-tick-staleness",
        family="oracle-staleness-calendar-watermark",
        fn_re=_re(r"commit|execute"),
        var_re=_re(r"acceptedBasket|minPublishTime|basket"),
        statement=(
            "`{fn}` fills `{var}` at the first post-commit tick, which can be "
            "a scheduled-release stale print, a confidence shift, or a freeze "
            "mark older than commit."
        ),
        prediction=(
            "Commit inside a release second (or freeze), then `{fn}` and read "
            "`{var}`. If the accepted tick is predictably stale, the hypothesis "
            "holds."
        ),
    ),
    PairTemplate(
        id="zero-senior-head",
        family="hwm-recap-accounting",
        fn_re=_re(r"settle"),
        var_re=_re(r"seniorPrincipal|principal"),
        statement=(
            "A zero-value Senior head on `{fn}` defers the other tranche's exit "
            "or strands a fee on the seed floor while `{var}` stays stuck."
        ),
        prediction=(
            "Drive `{var}` to a dust/zero head, then `{fn}`. If the other "
            "tranche cannot exit, the hypothesis holds."
        ),
    ),
    PairTemplate(
        id="gross-pending-revenue",
        family="hwm-recap-accounting",
        fn_re=_re(r"reconcile|assign"),
        var_re=_re(r"unassigned|highWaterMark|hwm"),
        statement=(
            "`{fn}` books `{var}` gross of payouts, overwrites a high-water "
            "mark, or credits the wrong cohort while Senior is below HWM."
        ),
        prediction=(
            "Reconcile or assign twice (including a zero-NAV bootstrap) and "
            "measure `{var}`. If the second pass moves value across cohorts, "
            "the hypothesis holds."
        ),
    ),
    PairTemplate(
        id="admission-backing",
        family="false-emergency-mode",
        fn_re=_re(r"executeOpen|evaluateOpen|renounce"),
        var_re=_re(r"degradedMode|emergency|mode"),
        statement=(
            "`{fn}` treats marked gains as cash backing for `{var}`, or a "
            "renounce/hedged close latches the mode without a solvency event."
        ),
        prediction=(
            "Open against marked (unrealized) backing or renounce ownership, "
            "then read `{var}`. If the latch fires while cash is intact (or "
            "fails when cash is gone), the trigger is false."
        ),
    ),
    PairTemplate(
        id="share-overflow-freeze",
        family="share-supply-overflow",
        fn_re=_re(r"settle|quote|convert|mint|deposit"),
        var_re=_re(r"totalSupply|share"),
        statement=(
            "`{fn}` plus virtual-offset arithmetic near integer max freezes "
            "`{var}` so later conversions revert."
        ),
        prediction=(
            "Drive `{var}` to near type max via fee-share or near-zero "
            "principal, then `{fn}`. If conversion reverts, the freeze is real."
        ),
    ),
)


def match_pair_template(function: str, var: str) -> PairTemplate | None:
    fn = function or ""
    name = var or ""
    for template in PAIR_TEMPLATES:
        if template.fn_re.search(fn) and template.var_re.search(name):
            return template
    return None


def family_sink_tokens() -> tuple[str, ...]:
    names: list[str] = []
    seen: set[str] = set()
    for family in PROTOCOL_FAMILIES:
        for token in str(family.sink_hint or "").replace(",", "/").split("/"):
            token = token.strip()
            if not token:
                continue
            key = token.lower()
            if key in seen:
                continue
            seen.add(key)
            names.append(token)
    for token in DELAY_BOUND_VARS:
        key = token.lower()
        if key not in seen:
            seen.add(key)
            names.append(token)
    return tuple(names)


def template_rank_bonus(function: str, var: str) -> int:
    template = match_pair_template(function, var)
    if template is None:
        return 0
    return 20

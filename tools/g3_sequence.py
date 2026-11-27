"""Generic G3 setup/sequence strategies.

Hand PoCs failed on the buggy pin because they called the mutator without
the state the distinguishing prediction needs (epoch work, unowned residual,
free vs locked, a price move with two actors). These strategies are selected
from (function, var, family) tokens only — no finding ids.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from tools.pair_templates import match_pair_template


@dataclass(frozen=True)
class SequenceStrategy:
    id: str
    when_fn: re.Pattern[str]
    when_var: re.Pattern[str]
    when_family: frozenset[str]
    setup: str
    why: str


def _re(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.I)


STRATEGIES: tuple[SequenceStrategy, ...] = (
    SequenceStrategy(
        id="receipt_open",
        when_fn=_re(r"settle|reconcile"),
        when_var=_re(r"sharePrice|totalAssets|\bnav\b|rebate|accrued|pledge"),
        when_family=frozenset({"refundable-receipt-in-nav"}),
        setup="_openFilled(ATTACKER, _long(), 60);",
        why=(
            "NAV/sharePrice tests need a reclaimable receipt in flight. "
            "Open first so the outsider epoch is priced against that receipt."
        ),
    ),
    SequenceStrategy(
        id="epoch_advance",
        when_fn=_re(r"settle|epoch|reconcile|requestDeposit|requestRedeem"),
        when_var=_re(r"."),
        when_family=frozenset(),
        setup="_queueDeposit(VICTIM, 10_000e6); _warpToDepositEpoch();",
        why=(
            "settle/epoch reverts with no matured head (NoLpEpochProgress). "
            "Queue a pending deposit and warp to its epoch before the mutator."
        ),
    ),
    SequenceStrategy(
        id="filled_position",
        when_fn=_re(r"executeClose|settleTraderClaim|retryPosition"),
        when_var=_re(r"rebate|sharePrice|traderClaim|freeSettlement|liquidationReserve"),
        when_family=frozenset(),
        setup="_openFilled(ATTACKER, _long(), 60);",
        why="Close/margin/claim probes need a live filled position, not an empty book.",
    ),
    SequenceStrategy(
        id="unowned_residual",
        when_fn=_re(r"assign|reconcile|accountExcess"),
        when_var=_re(r"unassigned|residual|unowned|highWater"),
        when_family=frozenset(),
        setup="_seedUnownedResidual(1e6);",
        why=(
            "mint-to-pool + accountExcess books into accountedAssets / junior, "
            "so unassigned stays 0. Account the cash then reserve that slice in "
            "the unassigned bucket so reconcile cannot treat it as junior revenue."
        ),
    ),
    SequenceStrategy(
        id="thin_pool",
        when_fn=_re(r"executeClose|executeOrder|executeOpen"),
        when_var=_re(r"degradedMode|emergency|frozen"),
        when_family=frozenset({"false-emergency-mode"}),
        setup="_thinPool();",
        why=(
            "A 1M junior buffer is far above one-side maxProfit, so a hedge "
            "close cannot trip effectiveAssets < maxLiability. Thin cash first."
        ),
    ),
    SequenceStrategy(
        id="multi_actor_hedge",
        when_fn=_re(r"executeClose|executeOpen|executeOrder"),
        when_var=_re(r"degradedMode|emergency|frozen"),
        when_family=frozenset({"false-emergency-mode"}),
        setup="_openFilled(ATTACKER, _long(), 60); _openFilled(VICTIM, _short(), 60);",
        why=(
            "A false emergency latch needs two actors on opposite sides, not a "
            "single solvent close."
        ),
    ),
    SequenceStrategy(
        id="oracle_price_move",
        when_fn=_re(r"executeClose|executeOrder|executeOpen"),
        when_var=_re(r"degradedMode|acceptedBasket|minPublishTime|sharePrice"),
        when_family=frozenset({"false-emergency-mode", "oracle-staleness-calendar-watermark"}),
        setup="_publish(1.5e8);",
        why="Close/execute after a material mark move, not at the seed price.",
    ),
    SequenceStrategy(
        id="drain_cash",
        when_fn=_re(r"executeClose|executeOrder"),
        when_var=_re(r"degradedMode|emergency"),
        when_family=frozenset({"false-emergency-mode"}),
        setup="_thinPoolTo(10_000e6);",
        why=(
            "After the hedge is open, drain pool cash well below one-side maxProfit. "
            "A close that credits the pool still leaves cash < remaining maxLiability."
        ),
    ),
    SequenceStrategy(
        id="price_print_then_mutate",
        when_fn=_re(r"addMargin|withdraw|execute|commit"),
        when_var=_re(r"freeSettlement|freeBalance|executionWindow"),
        when_family=frozenset({"delayed-order-optionality"}),
        setup='_openFilled(ATTACKER, _long(), 60); _commitAs(ATTACKER, _openReq("q", _long(), 60)); _publish(1.5e8);',
        why=(
            "Delayed-order optionality is after the fill price is public. "
            "Commit, publish, then snapshot free and mutate."
        ),
    ),
    SequenceStrategy(
        id="locked_vs_free",
        when_fn=_re(r"addMargin|withdraw|commit|execute"),
        when_var=_re(r"freeSettlement|freeBalance|freeAssets|locked"),
        when_family=frozenset(),
        setup="_snapshotFree(ATTACKER);",
        why=(
            "Total balance often still includes committed/locked margin, so "
            "'balance did not drop' is a false fail. Snapshot free = balance - locked "
            "after the price print / commit, not the raw settlement balance."
        ),
    ),
    SequenceStrategy(
        id="warp_past_window",
        when_fn=_re(r"commit|expire|execute"),
        when_var=_re(r"executionWindow|deadline|submitBy"),
        when_family=frozenset(),
        setup="",
        why="After commit, warp past the trader-chosen window before expire/execute.",
    ),
    SequenceStrategy(
        id="oracle_first_tick",
        when_fn=_re(r"commit|execute"),
        when_var=_re(r"minPublishTime|publishTime|staleness"),
        when_family=frozenset(),
        setup="",
        why="Fill with the first post-commit tick (commitTime+1), not a later keeper delay.",
    ),
    SequenceStrategy(
        id="supply_headroom",
        when_fn=_re(r"convertToShares|quoteDeposit|settle|mint"),
        when_var=_re(r"totalSupply"),
        when_family=frozenset(),
        setup="_nearMaxSupply();",
        why="Overflow/freeze probes drive virtual-offset supply to uint max before the mutator.",
    ),
)


def select_strategies(function: str, var: str, family: str = "") -> list[str]:
    """Return strategy ids that apply to this mutator × sink × family."""
    family = family or ""
    if not family:
        template = match_pair_template(function, var)
        family = template.family if template else ""
    chosen: list[str] = []
    for strat in STRATEGIES:
        if strat.when_family and family not in strat.when_family:
            continue
        if not strat.when_fn.search(function or ""):
            continue
        if not strat.when_var.search(var or ""):
            continue
        chosen.append(strat.id)
    return chosen


def strategy_by_id(sid: str) -> SequenceStrategy:
    for strat in STRATEGIES:
        if strat.id == sid:
            return strat
    raise KeyError(sid)


def setup_block(function: str, var: str, family: str = "") -> str:
    lines: list[str] = []
    for sid in select_strategies(function, var, family):
        strat = strategy_by_id(sid)
        lines.append(f"        // strategy:{sid} — {strat.why.splitlines()[0]}")
        if strat.setup:
            lines.append(f"        {strat.setup}")
    return "\n".join(lines)

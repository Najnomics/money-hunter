"""Protocol-agnostic hunter families for vaults, delayed orders, and oracles.

These are patterns, not a named protocol. They exist so hypothesis generation
does not depend on an analyst remembering a specific contest answer key.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProtocolFamily:
    id: str
    battery: str
    title: str
    statement: str
    prediction: str
    keywords: tuple[str, ...]
    sink_hint: str
    check_name: str
    assumption_class: str


# Six families the default vault/share-price battery always fires.
# Worded without a specific protocol's types or function names.
PROTOCOL_FAMILIES: tuple[ProtocolFamily, ...] = (
    ProtocolFamily(
        id="refundable-receipt-in-nav",
        battery="vault",
        title="Refundable receipts or fees counted in share price",
        statement=(
            "Share price, NAV, or an exchange rate includes cash, credit, or marks "
            "that a later user action can reclaim (pending yield, rebates, refundable "
            "fees, temporary receipts, unsettled fills). Booking a reclaimable inflow "
            "as revenue, or a reclaimable outflow as a loss, moves value across holders "
            "who transact at the inflated or deflated price."
        ),
        prediction=(
            "Snapshot share price, introduce a reclaimable receipt or fee, let an "
            "unrelated holder mint or redeem, then reclaim the receipt. If share price "
            "moved with the reclaimable amount and the outsider transacted at that "
            "price, the conservation invariant is broken; if share price ignored the "
            "receipt, the hypothesis is false."
        ),
        keywords=(
            "nav", "share price", "exchange rate", "rebate", "refundable", "fee",
            "yield", "receipt", "pending fill", "accrual", "convertToAssets",
            "convertToShares", "totalAssets",
        ),
        sink_hint="sharePrice/NAV",
        check_name="share_price_excludes_reclaimable_receipts_and_fees",
        assumption_class="ACCOUNTING",
    ),
    ProtocolFamily(
        id="share-supply-overflow",
        battery="vault",
        title="Share-supply overflow or virtual-offset freeze",
        statement=(
            "Mint, fee-on-shares, or virtual-offset arithmetic near the integer max "
            "overflows or saturates. convertToShares / convertToAssets / epoch "
            "settlement then reverts or freezes, locking deposits, redemptions, or "
            "fee realization for everyone."
        ),
        prediction=(
            "Drive total supply, virtual shares, or fee-share headroom to near type "
            "max, then mint a tiny amount or settle a fee. If the conversion reverts "
            "or the offset no longer increases, the freeze is real; if the conversion "
            "stays monotonic, the hypothesis is false."
        ),
        keywords=(
            "totalSupply", "virtual shares", "virtual assets", "overflow",
            "type(uint256).max", "convertToShares", "fee shares", "dead shares",
        ),
        sink_hint="totalSupply",
        check_name="share_supply_and_virtual_offset_cannot_overflow_to_freeze",
        assumption_class="ACCOUNTING",
    ),
    ProtocolFamily(
        id="hwm-recap-accounting",
        battery="vault",
        title="High-water-mark and recapitalization accounting",
        statement=(
            "Repeated recapitalization, residual intent, high-water-mark resets, "
            "wiped-tranche bootstrap mints, or unassigned/residual asset buckets "
            "credit the wrong cohort. Later revenue or recovery then pays new "
            "depositors or a subordinated tranche instead of the recap funder."
        ),
        prediction=(
            "Recap a depleted vault (including a zero-NAV bootstrap mint), take a "
            "partial recovery, recap again, then realize new revenue. If the "
            "high-water mark or residual bucket resets so a later depositor captures "
            "the recovery, the accounting is wrong; if the original recap claim is "
            "conserved, the hypothesis is false."
        ),
        keywords=(
            "high water", "hwm", "high-water-mark", "recapitaliz", "unassigned",
            "residual", "bootstrap", "zero nav", "recovery", "tranche",
        ),
        sink_hint="unassignedAssets/HWM",
        check_name="hwm_and_recap_do_not_reset_another_cohorts_claim",
        assumption_class="ACCOUNTING",
    ),
    ProtocolFamily(
        id="delayed-order-optionality",
        battery="lifecycle",
        title="Delayed-order optionality after the price print",
        statement=(
            "After a price, mark, or fill is public but before a queued order "
            "executes, a party can add margin, withdraw, liquidate, recapitalize, "
            "or stretch the execution window so the committed order is no longer "
            "binding. 'Users cannot cancel' does not cover these side doors."
        ),
        prediction=(
            "Commit an order, wait until the relevant price is public, then from "
            "the same account or an owner/keeper path mutate margin, free balance, "
            "or backing. If execution then reverts with a refund while a keeper "
            "still earns bounty, or a counterparty is left worse, the order was an "
            "option; if execution still binds on the original terms, the hypothesis "
            "is false."
        ),
        keywords=(
            "delayed order", "queued", "commit", "execute", "price print",
            "execution window", "cancel", "optionality", "addMargin", "withdraw",
        ),
        sink_hint="queuedOrder/freeBalance",
        check_name="queued_order_stays_binding_after_price_is_public",
        assumption_class="ORDER_TIMING",
    ),
    ProtocolFamily(
        id="oracle-staleness-calendar-watermark",
        battery="boundary",
        title="Oracle staleness, calendar, or watermark",
        statement=(
            "Feed rotation resets per-source timestamps; the first post-commit tick "
            "can land on a scheduled macro release; holiday or weekend overrides "
            "disagree with max-staleness; a batch cache keys off the newest "
            "component time instead of the oldest. Stale, future, or mixed-calendar "
            "prices then pass as fresh."
        ),
        prediction=(
            "Rotate or override a feed, freeze one component while another updates, "
            "or step time across a holiday/weekend boundary, then consume the "
            "aggregated price. If a stale or mixed-calendar tick is accepted, the "
            "watermark is wrong; if the oldest component and calendar still gate "
            "the read, the hypothesis is false."
        ),
        keywords=(
            "oracle", "staleness", "heartbeat", "watermark", "price feed",
            "holiday", "weekend", "calendar", "maxAge", "roundId", "latestRoundData",
        ),
        sink_hint="oraclePrice",
        check_name="oracle_rejects_stale_mixed_calendar_and_reset_watermarks",
        assumption_class="ORACLE_DATA",
    ),
    ProtocolFamily(
        id="false-emergency-mode",
        battery="lifecycle",
        title="False degraded or emergency-mode trigger",
        statement=(
            "Hedged or offsetting positions, admission that counts marked "
            "(unrealized) gains as backing, or a mode latch that freezes the wrong "
            "cohort (LP settlement vs trader surplus) can flip the protocol into "
            "degraded/emergency/paused state without a real solvency event — or "
            "fail to flip when backing is actually gone."
        ),
        prediction=(
            "Open an offsetting pair or deposit marked gains as if they were cash, "
            "then hit the mode predicate. If degraded/emergency latches while cash "
            "backing is intact, or fails to latch when backing is gone, the trigger "
            "is false; if the latch matches cash solvency, the hypothesis is false."
        ),
        keywords=(
            "degraded", "emergency", "paused", "circuit breaker", "insolvent",
            "backing", "hedged", "unrealized", "marked to market",
        ),
        sink_hint="emergencyMode/degradedMode",
        check_name="emergency_mode_matches_cash_solvency_not_marked_gains",
        assumption_class="LIVENESS",
    ),
)


FAMILY_BY_ID = {family.id: family for family in PROTOCOL_FAMILIES}


def families_for_battery(battery: str) -> tuple[ProtocolFamily, ...]:
    """Vault is the default share-price battery and always includes every family."""
    if battery == "vault":
        return PROTOCOL_FAMILIES
    return tuple(family for family in PROTOCOL_FAMILIES if family.battery == battery) or PROTOCOL_FAMILIES


def default_family_keywords() -> list[str]:
    seen: list[str] = []
    for family in PROTOCOL_FAMILIES:
        for keyword in family.keywords:
            if keyword not in seen:
                seen.append(keyword)
    return seen

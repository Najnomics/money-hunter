"""Blind2 miss catalog: every unique paid finding apex-core dropped.

Source of truth for *what* was missed: `origin/cursor/plether-blind2`
`findings/plether-blind2/SCORE.md`. Kill language is taken from that score and
the named-candidate table in `LEDGER.md`. Tests replay these drops; they do not
claim a Plether re-run is a clean recall measurement.
"""
from __future__ import annotations

from typing import NamedTuple


class Miss(NamedTuple):
    id: str
    sev: str  # C H M L
    bucket: str  # KILLED | PAIR-ONLY | NEVER_GENERATED
    drop_gate: str  # G4 | G3 | G2 | cartesian | never-generated
    function: str
    var: str
    family: str
    kill_text: str
    root_cause: str
    fix: str  # 11..18
    notes: str


# Families (protocol-agnostic ids from tools/protocol_families.py)
NAV = "refundable-receipt-in-nav"
OVERFLOW = "share-supply-overflow"
HWM = "hwm-recap-accounting"
DELAY = "delayed-order-optionality"
ORACLE = "oracle-staleness-calendar-watermark"
EMERGENCY = "false-emergency-mode"

# 20 KILLED + 42 PAIR-ONLY + 1 NEVER_GENERATED = 63
MISSES: tuple[Miss, ...] = (
    # --- 6 wrongly killed crits ---
    Miss(
        "97591", "C", "KILLED", "G4",
        "settleLpEpoch", "sharePrice", NAV,
        "ApexBlind2 PASS: min(raw,accounted) excludes mint-to-pool. Unsolicited inflow killed.",
        "Family G4 after mint-to-pool analog closed VPI-in-Junior-NAV (buildReconcileSnapshot).",
        "13",
        "Per-variant: mint-to-pool ≠ reclaimable VPI in NAV.",
    ),
    Miss(
        "97906", "C", "KILLED", "G3",
        "commitOrder", "minPublishTime", ORACLE,
        "code-fact: minPublishTime=commitTime+1; natspec says the cap is live; no execution",
        "G3 stall H-ORD-03/H-0005. Code-fact ≠ first post-commit macro-tick PoC.",
        "12",
        "Happy-path/code-fact cannot pass or kill.",
    ),
    Miss(
        "98172", "C", "KILLED", "G4",
        "quoteDepositFromState", "totalSupply", OVERFLOW,
        "Supply would overflow and revert at uint max; astronomical and unreachable. Paid freeze.",
        "G4 H-0002 labelled the revert unreachable. The freeze is the impact.",
        "11",
        "Reachability probe (VIRTUAL_SHARES / near-zero principal), not astronomical ⇒ disprove.",
    ),
    Miss(
        "99075", "C", "KILLED", "G4",
        "settleLpEpoch", "totalSupply", OVERFLOW,
        "Same overflow freeze on settleLpEpoch; supply unreachable; revert confirmed at uint max.",
        "G4 H-0002 reused the overflow kill on a different mutator.",
        "11+13",
        "Per-variant: quoteDeposit freeze ≠ settleLpEpoch fee-share freeze.",
    ),
    Miss(
        "98209", "C", "KILLED", "G3",
        "assignUnassignedAssets", "unassignedAssets", HWM,
        "reserved bucket <= NAV; unassigned <= NAV; seeded fixture; intended spec; no execution",
        "G3 stall H-0003. unassigned<=NAV is not assignUnassignedAssets at zero mark.",
        "12",
        "Zero-NAV bootstrap mint is the distinguishing attack.",
    ),
    Miss(
        "98854", "C", "KILLED", "G3",
        "addMargin", "freeSettlement", DELAY,
        "happy path seeded fixture; public zero-hash commit reverts (PASS); cap is live; assert True",
        "G3 stall H-ORD-04. Zero-hash commit PASS does not test addMargin rescue.",
        "12+13",
        "Distinguishing: addMargin after the price print, not a zero-hash revert.",
    ),
    # --- wrongly killed highs called out in the prompt ---
    Miss(
        "97628", "H", "KILLED", "G4",
        "convertToShares", "totalSupply", OVERFLOW,
        "Near-zero Junior principal inflates shares until quote overflow; astronomical; unreachable.",
        "G4 H-0002 overflow. Near-zero principal is the reachability probe, not a disproof.",
        "11",
        "Same freeze-is-impact rule as 98172.",
    ),
    Miss(
        "97590", "H", "KILLED", "G3",
        "executeClose", "degradedMode", EMERGENCY,
        "DegradedModeLifecycle PASS (latch works); seeded fixture not degraded; intended spec; happy path",
        "G3 stall H-0006. Intended latch PASS is not a hedged false-trip PoC.",
        "12",
        "Distinguishing: offsetting pair false-latch, not solvent lifecycle.",
    ),
    # --- other killed H ---
    Miss(
        "97760", "H", "KILLED", "G3",
        "settleLpEpoch", "unassignedAssets", HWM,
        "reserved bucket <= NAV; recap residual; cap is live; seeded fixture; no execution",
        "G3 stall H-0003 recap residual. Happy-path conservation is not the stale-intent attack.",
        "12",
        "Family HWM/recap; distinguishing leftover pendingRecapitalizationAssets.",
    ),
    Miss(
        "97844", "H", "KILLED", "G3",
        "reconcile", "highWaterMark", HWM,
        "reserved bucket <= NAV; reconcile × highWaterMark; intended spec; code-fact",
        "G3 stall H-0003. Repeated reconcile overwrite never executed.",
        "12",
        "Distinguishing: second reconcile vs first HWM.",
    ),
    Miss(
        "97968", "H", "KILLED", "G3",
        "settleLpEpoch", "unassignedAssets", HWM,
        "Senior-gap-first → unassigned; reserved bucket <= NAV; seeded fixture",
        "G3 stall H-0003 Senior-gap-first. Bucket inequality is not the recap-landing attack.",
        "12",
        "Distinguishing: recap lands in unassigned after Senior gap.",
    ),
    Miss(
        "99735", "H", "KILLED", "G3",
        "settleLpEpoch", "seniorPrincipal", HWM,
        "extra settlement pass; cap is live; intended spec; H-POOL-03",
        "G3 stall H-POOL-03 extra settlement pass. Design-wrong DIV never got the second-pass PoC.",
        "12",
        "Distinguishing: extra settleLpEpoch shifts Junior to impaired Senior.",
    ),
    # --- killed M ---
    Miss(
        "97603", "M", "KILLED", "G3",
        "executeOrder", "acceptedBasket", ORACLE,
        "code-fact: newest-component batch cache; design-wrong DIV; natspec; no execution",
        "G3 stall DIV-0202/H-ORD-02. Design-wrong DIV never got a batch PoC.",
        "12",
        "Distinguishing: reuse historical batch across commitTimes.",
    ),
    Miss(
        "97848", "M", "KILLED", "G3",
        "reconcile", "unassignedAssets", HWM,
        "unassigned truncation; reserved bucket <= NAV; intended spec",
        "G3 stall H-0003 reversible MTM truncation.",
        "12",
        "Distinguishing: MTM reverses and truncates unassigned.",
    ),
    Miss(
        "98994", "M", "KILLED", "G3",
        "settleLpEpoch", "unassignedAssets", HWM,
        "pledged loss at zero tranche principal; reserved bucket <= NAV; H-0003",
        "G3 stall H-0003. Collecting pledged loss at zero principal never executed.",
        "12",
        "Distinguishing: zero-principal pledge collection reassigns unassigned.",
    ),
    Miss(
        "99501", "M", "KILLED", "G3",
        "settleLpEpoch", "unassignedAssets", HWM,
        "first post-recap settlement; reserved bucket <= NAV; seeded fixture",
        "G3 stall H-0003 first post-recap settlement strands recap in unassigned.",
        "12",
        "Distinguishing: first settlement after recap, not a solvent epoch.",
    ),
    # --- killed L ---
    Miss(
        "97715", "L", "KILLED", "G3",
        "assignUnassignedAssets", "highWaterMark", HWM,
        "post-wipe HWM reset; reserved bucket <= NAV; intended spec",
        "G3 stall H-0003 post-wipe HWM reset.",
        "12",
        "Distinguishing: recap after wipe resets Senior HWM.",
    ),
    Miss(
        "97733", "L", "KILLED", "G3",
        "withdraw", "freeSettlement", DELAY,
        "happy path seeded fixture; withdraw/depositFor after print; cap is live; H-ORD-04/H-CH-02",
        "G3 stall H-ORD-04. Withdraw after the print is a different variant than zero-hash commit.",
        "12+13",
        "Per-variant delayed-order: withdraw vs addMargin vs depositFor.",
    ),
    Miss(
        "98961", "L", "KILLED", "G2",
        "assignUnassignedAssets", "highWaterMark", HWM,
        "Wrong protocol; this analog does not apply here. PDF excerpt HWM over-reduction.",
        "G2 H-0018/19 PDF excerpt killed as wrong protocol. Excerpt is this pin's Senior HWM rounding.",
        "15",
        "Map excerpt → in-scope assignUnassignedAssets / highWaterMark before G2.",
    ),
    Miss(
        "99392", "L", "KILLED", "G3",
        "commitOrder", "freeSettlement", DELAY,
        "trader bounds as free option; public zero-hash commit reverts (PASS); intended spec",
        "G3 stall H-0004. Trader bounds as a free option never distinguished from the zero-hash revert.",
        "12",
        "Distinguishing: zero gross-debit bound makes close cancellable.",
    ),
    # --- 42 PAIR-ONLY ---
    Miss(
        "97677", "C", "PAIR-ONLY", "cartesian",
        "settleLpEpoch", "pnlPledgeAssets", NAV,
        "cartesian pair only; no pledge-vs-redemption hyp",
        "Uncollected pledged PnL can fund a competing redemption. Never named as same-RC.",
        "14+16",
        "Template pledge-vs-redemption; queue G3.",
    ),
    Miss(
        "97858", "C", "PAIR-ONLY", "cartesian",
        "executeOrder", "freeSettlement", DELAY,
        "cartesian pair only; H-0004 is depositFor/addMargin, not owner pool-cash vs queued open",
        "Owner pool-cash swings void/revive a pinned open. Nearby delayed-order ≠ this variant.",
        "14+13",
        "Variant executeOrder::freeSettlement stays live after addMargin kill.",
    ),
    Miss(
        "98014", "C", "PAIR-ONLY", "cartesian",
        "_applyRouterConfigAfterOracle", "acceptedBasket", ORACLE,
        "cartesian pair only; family is calendar/newest-tick, not rotation watermark reset",
        "Oracle rotation drops per-feed watermarks. Internal apply* must still rank.",
        "14+16",
        "Keep high-EV `_apply*` internals; template watermark-rotation.",
    ),
    Miss(
        "98035", "C", "PAIR-ONLY", "cartesian",
        "executeOpen", "vpiRebateReserve", NAV,
        "cartesian pair only; no lifetime-floor hyp",
        "Open-time VPI rebate has no lifetime floor.",
        "14+16",
        "Template unclamped-rebate.",
    ),
    Miss(
        "98941", "C", "PAIR-ONLY", "cartesian",
        "executeLiquidationBatch", "freeSettlement", DELAY,
        "cartesian pair only; no liq-cleanup-cancels-open hyp",
        "Liquidation cleanup cancels a pinned open.",
        "14+16",
        "Template liq-cleanup-cancel.",
    ),
    Miss(
        "99280", "C", "PAIR-ONLY", "cartesian",
        "commitOrder", "freeSettlement", DELAY,
        "cartesian pair only; no increase-vs-close admission hyp",
        "Queued increase voids a committed close.",
        "14+16",
        "commit* must rank as high-EV mutator.",
    ),
    Miss(
        "99536", "C", "PAIR-ONLY", "cartesian",
        "settleTraderClaim", "freeSettlement", DELAY,
        "cartesian pair only",
        "Queued open fill/void after pinned price is public (settleTraderClaim option).",
        "14+16",
        "Template settle-claim-option.",
    ),
    Miss(
        "99589", "C", "PAIR-ONLY", "cartesian",
        "settleLpEpoch", "sharePrice", NAV,
        "cartesian pair only; pending-open liability ≠ queued LP escrow",
        "Committed unexecuted opens add no LP liability.",
        "14+16",
        "Template pending-open-nav.",
    ),
    Miss(
        "99756", "C", "PAIR-ONLY", "cartesian",
        "settleLpEpoch", "seniorPrincipal", HWM,
        "cartesian pair only; H-POOL-04 is work-cap, not zero-value Senior head",
        "Zero-value Senior head defers Junior exit.",
        "14+16",
        "Template zero-senior-head.",
    ),
    Miss(
        "99855", "C", "PAIR-ONLY", "cartesian",
        "reconcile", "unassignedAssets", HWM,
        "cartesian pair only",
        "Pending trading revenue booked gross of payouts.",
        "14+16",
        "reconcile must rank; template gross-pending-revenue.",
    ),
    Miss(
        "100087", "C", "PAIR-ONLY", "cartesian",
        "executeClose", "traderClaimBalance", NAV,
        "cartesian pair only",
        "Partial close vs claim strips residual to MM+1.",
        "14+16",
        "Template partial-close-claim.",
    ),
    Miss(
        "97592", "H", "PAIR-ONLY", "cartesian",
        "retryPositionProtectionClose", "degradedMode", DELAY,
        "cartesian pair only",
        "retryPositionProtectionClose consumes Latched before owner amend.",
        "14+16",
        "retry* is high-EV.",
    ),
    Miss(
        "97881", "H", "PAIR-ONLY", "cartesian",
        "settleLpEpoch", "seniorPrincipal", HWM,
        "cartesian pair only",
        "Frozen-window Senior exit strands fee on seed floor.",
        "14+16",
        "Same pair family as 99756; still a distinct variant statement.",
    ),
    Miss(
        "97903", "H", "PAIR-ONLY", "cartesian",
        "executeClose", "vpiRebateReserve", NAV,
        "cartesian pair only; distinct from 98035 open rebate",
        "Unbounded close VPI at small positive depth.",
        "14+13",
        "Per-variant: executeClose vs executeOpen rebate.",
    ),
    Miss(
        "98416", "H", "PAIR-ONLY", "cartesian",
        "applyCalendarConfig", "acceptedBasket", ORACLE,
        "cartesian pair only; H-0005 is commitTime+1, not holiday vs fadMaxStaleness",
        "Back-to-back override days freeze past fadMaxStaleness.",
        "14+16",
        "apply* calendar config ranks; not dropped as internal.",
    ),
    Miss(
        "97601", "M", "PAIR-ONLY", "cartesian",
        "applyCalendarConfig", "acceptedBasket", ORACLE,
        "cartesian pair only",
        "Whole-UTC-day overrides miss partial-day Pyth closures.",
        "14+16",
        "Same mutator as 98416; different statement via template calendar-partial-day.",
    ),
    Miss(
        "97605", "M", "PAIR-ONLY", "cartesian",
        "executeOpen", "degradedMode", EMERGENCY,
        "cartesian pair only; H-0006 mentions MTM backing; not hypothesized as admission",
        "Open admission counts marked gain as pool backing.",
        "14+16",
        "Template admission-backing.",
    ),
    Miss(
        "97649", "M", "PAIR-ONLY", "cartesian",
        "executeLiquidationBatch", "liquidationReserve", DELAY,
        "cartesian pair only",
        "Self-liquidation skips frozen-close spread.",
        "14+16",
        "executeLiquidationBatch ranks.",
    ),
    Miss(
        "97748", "M", "PAIR-ONLY", "cartesian",
        "executeClose", "vpiRebateReserve", NAV,
        "cartesian pair only",
        "Skew-reducing close nets VPI rebate against execution fee.",
        "14+16",
        "Close × rebateReserve template.",
    ),
    Miss(
        "98795", "M", "PAIR-ONLY", "cartesian",
        "_applyOpen", "liquidationReserve", DELAY,
        "cartesian pair only",
        "Liquidation reserve ratchets on open/increase.",
        "14+16",
        "Keep high-EV `_applyOpen`.",
    ),
    Miss(
        "99422", "M", "PAIR-ONLY", "cartesian",
        "_adverseLiquidationPrice", "acceptedBasket", ORACLE,
        "cartesian pair only",
        "Frozen liq applies SHORT shift to capped mark.",
        "14+16",
        "Keep high-EV `_adverseLiquidationPrice` (liquidat*).",
    ),
    Miss(
        "99795", "M", "PAIR-ONLY", "cartesian",
        "withdraw", "vpiRebateReserve", NAV,
        "cartesian pair only",
        "Withdraw before full close waives positive VPI charge.",
        "14+16",
        "withdraw × rebateReserve.",
    ),
    Miss(
        "97600", "L", "PAIR-ONLY", "cartesian",
        "requestRedeem", "sharePrice", NAV,
        "cartesian pair only",
        "Planted ERC-7540 head hides funded claim.",
        "14+16",
        "requestRedeem is high-EV (redeem).",
    ),
    Miss(
        "97602", "L", "PAIR-ONLY", "cartesian",
        "_applyRouterConfig", "currentExecutionConfigHash", ORACLE,
        "cartesian pair only; Blind1 G1-killed this; Blind2 never named it",
        "Scheduled treasury rotation changes config hash / bounty sniping.",
        "14+16",
        "Keep high-EV `_applyRouterConfig`; config/hash is value-bearing.",
    ),
    Miss(
        "97610", "L", "PAIR-ONLY", "cartesian",
        "renounceOwnership", "degradedMode", EMERGENCY,
        "cartesian pair only",
        "Default renounceOwnership latches degradedMode forever.",
        "14+16",
        "renounce* is high-EV.",
    ),
    Miss(
        "97622", "L", "PAIR-ONLY", "cartesian",
        "executeOrder", "acceptedBasket", ORACLE,
        "cartesian pair only",
        "TP/SL creation reverts after fill (accepted basket lags Engine mark).",
        "14+16",
        "acceptedBasket is value-bearing.",
    ),
    Miss(
        "97833", "L", "PAIR-ONLY", "cartesian",
        "assessCommittedOrder", "freeSettlement", DELAY,
        "cartesian pair only",
        "Commit-time carry escapes pinned debit caps.",
        "14+16",
        "assess* is high-EV.",
    ),
    Miss(
        "97836", "L", "PAIR-ONLY", "cartesian",
        "executeLiquidationBatch", "liquidationReserve", DELAY,
        "cartesian pair only",
        "executeLiquidationBatch stops at 0 if keeper has a position.",
        "14+16",
        "Same mutator as 97649; gas-budget variant.",
    ),
    Miss(
        "97893", "L", "PAIR-ONLY", "cartesian",
        "executeOrder", "acceptedBasket", ORACLE,
        "cartesian pair only; execution vs liq cap order",
        "Execution shifts already-capped basket (vs shift-then-cap liq).",
        "14+16",
        "Oracle/execution template.",
    ),
    Miss(
        "97971", "L", "PAIR-ONLY", "cartesian",
        "retryPositionProtectionClose", "vpiRebateReserve", DELAY,
        "cartesian pair only; protection carry",
        "Self-trigger TP/SL collects carry outside close ceilings.",
        "14+16",
        "retryPositionProtectionClose × rebate/carry.",
    ),
    Miss(
        "98039", "L", "PAIR-ONLY", "cartesian",
        "settleLpEpoch", "sharePrice", DELAY,
        "cartesian pair only; settleLpEpoch vs pending open",
        "LP epoch before execution refunds a losing committed open.",
        "14+16",
        "settle vs pending-open optionality.",
    ),
    Miss(
        "98170", "L", "PAIR-ONLY", "cartesian",
        "evaluateOpen", "freeSettlement", DELAY,
        "cartesian pair only",
        "Open preflight ignores the account’s own queued orders.",
        "14+16",
        "evaluate* is high-EV.",
    ),
    Miss(
        "98200", "L", "PAIR-ONLY", "cartesian",
        "assessCommittedOrder", "freeSettlement", DELAY,
        "cartesian pair only",
        "Close bounds checked before commitment carry.",
        "14+16",
        "assessCommittedOrder ranks.",
    ),
    Miss(
        "98575", "L", "PAIR-ONLY", "cartesian",
        "withdraw", "degradedMode", DELAY,
        "cartesian pair only",
        "Withdraw health ok for same-block frozen liquidatable.",
        "14+16",
        "withdraw × mode/health.",
    ),
    Miss(
        "98727", "L", "PAIR-ONLY", "cartesian",
        "settleLpEpoch", "protocolTreasury", NAV,
        "cartesian pair only",
        "Withheld execution fee unattributed when pool cash short.",
        "14+16",
        "treasury is value-bearing.",
    ),
    Miss(
        "98762", "L", "PAIR-ONLY", "cartesian",
        "evaluateOpen", "acceptedBasket", ORACLE,
        "cartesian pair only; open vs confidence shift",
        "Open admission ignores adverse confidence shift.",
        "14+16",
        "evaluateOpen × acceptedBasket.",
    ),
    Miss(
        "99470", "L", "PAIR-ONLY", "cartesian",
        "assignUnassignedAssets", "highWaterMark", HWM,
        "cartesian pair only",
        "assignUnassignedAssets credits Junior while Senior below HWM.",
        "14+16",
        "assign* is high-EV; related to 98209 but a distinct unique Low.",
    ),
    Miss(
        "99551", "L", "PAIR-ONLY", "cartesian",
        "commitOrder", "traderClaimBalance", DELAY,
        "cartesian pair only; close projection vs live",
        "Close commit validates Router projection vs Engine live position.",
        "14+16",
        "commitOrder × claim balance.",
    ),
    Miss(
        "99602", "L", "PAIR-ONLY", "cartesian",
        "executeOrder", "acceptedBasket", ORACLE,
        "cartesian pair only; freeze-execute older mark",
        "Live-commit / freeze-execute uses a mark older than commit.",
        "14+16",
        "executeOrder × acceptedBasket timing.",
    ),
    Miss(
        "99663", "L", "PAIR-ONLY", "cartesian",
        "executeClose", "sharePrice", DELAY,
        "cartesian pair only; dust min-notional",
        "Unfillable queued close lets dust partial bypass min notional.",
        "14+16",
        "executeClose × sharePrice dust.",
    ),
    Miss(
        "99931", "L", "PAIR-ONLY", "cartesian",
        "_arm", "degradedMode", DELAY,
        "cartesian pair only",
        "Attached TP/SL already triggered at parent fill.",
        "14+16",
        "Keep high-EV `_arm` (arm).",
    ),
    Miss(
        "99933", "L", "PAIR-ONLY", "cartesian",
        "executeClose", "vpiRebateReserve", NAV,
        "cartesian pair only",
        "Partial close with cash-capped VPI rebate erases carry.",
        "14+16",
        "executeClose × vpiRebateReserve.",
    ),
    # --- never generated ---
    Miss(
        "99136", "C", "NEVER_GENERATED", "never-generated",
        "commitOrder", "executionWindow", DELAY,
        "No executionWindow var; H-0004 is add-margin not min-window",
        "Trader-set executionWindowSeconds as a free option. Cartesian vocab omitted delay-bound vars.",
        "16",
        "Always inject executionWindow / minPublishTime / minDelay.",
    ),
)


def by_bucket(bucket: str) -> tuple[Miss, ...]:
    return tuple(m for m in MISSES if m.bucket == bucket)


def by_id(finding_id: str) -> Miss:
    for miss in MISSES:
        if miss.id == finding_id:
            return miss
    raise KeyError(finding_id)


assert len(MISSES) == 63, len(MISSES)
assert len(by_bucket("KILLED")) == 20, len(by_bucket("KILLED"))
assert len(by_bucket("PAIR-ONLY")) == 42, len(by_bucket("PAIR-ONLY"))
assert len(by_bucket("NEVER_GENERATED")) == 1
assert [m.id for m in MISSES if m.sev == "C" and m.bucket == "KILLED"] == [
    "97591", "97906", "98172", "99075", "98209", "98854",
]

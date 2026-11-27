# Plether Blind SCORE-I (honest)

**Never submit.** Pin `a82d4fe`. Same family-overlay oracle as SCORE-H. An item is VERIFIED only when the exact Foundry test PASSes on the unmodified pin and FAILs on a family overlay. No mocks of the target. No finding ids in the generic path.

## New verifies this round (vs SCORE-H)

| ID | Sev | Test | Overlay | Overlay fail |
|---|---|---|---|---|
| 97858 | C | `executeOrder_freeSettlement` | `pending_order` | `OrderRouter__NoOrdersToExecute` |
| 99589 | C | `settleLpEpoch_sharePrice` | `zero_vpi` | `incumbent assets ignored reclaimable receipt` |
| 98039 | L | same test | same | same |
| 97603 | M | `executeOrder_acceptedBasket` | `first_tick` | `execute after oracle/config print failed` |
| 97622 | L | same test | same | same |
| 97893 | L | same test | same | same |
| 99602 | L | same test | same | same |
| 99536 | C | `settleTraderClaim_freeSettlement` | `pending_order` | `CfdEngine__Unauthorized` |

`executeOrder` now processes `router.nextExecuteId()` (FIFO head), not `lastCommitId`. Overlay still refuses execute while live size remains.

`settleTraderClaim` seeds a standing claim, commits a pending open, prints the fill price, then settles. Overlay blocks claim settlement while order margin is reserved.

Parked: `withdraw_vpiRebateReserve` (99795) pin-FAIL — pending close + withdraw moves neither the rebate bucket nor incumbent NAV.

## Totals

| Bucket | SCORE-H | **SCORE-I** |
|---|---:|---:|
| VERIFIED | 24 | **32** |
| NAMED_OPEN | 19 | **11** |
| PAIR-ONLY | 20 | **20** |
| NEVER | 0 | **0** |

## By severity (V / K / O / P / N)

| Sev | n | SCORE-H | **SCORE-I** |
|---|---:|---|---|
| C | 18 | 10 / 0 / 5 / 3 / 0 | **13 / 0 / 2 / 3 / 0** |
| H | 10 | 3 / 0 / 4 / 3 / 0 | **3 / 0 / 4 / 3 / 0** |
| M | 11 | 1 / 0 / 6 / 4 / 0 | **2 / 0 / 5 / 4 / 0** |
| L | 24 | 10 / 0 / 4 / 10 / 0 | **14 / 0 / 0 / 10 / 0** |
| **All** | **63** | **24 / 0 / 19 / 20 / 0** | **32 / 0 / 11 / 20 / 0** |

## Remaining unverified — precise reason

| ID | Sev | Bucket | Test | Reason |
|---|---|---|---|---|
| 98941 | C | NAMED_OPEN | `executeLiquidationBatch_freeSettlement` | pin-FAIL `liq cleanup left the pending order binding` — live canary + pending open is not liquidatable at the printed mark, so cleanup never voids the queue head |
| 99855 | C | NAMED_OPEN | `reconcile_unassignedAssets` | pin-FAIL `HousePool__NoLpEpochProgress` — leftover unassigned/recap freezes the next deposit so a second observation never runs |
| 97760 | H | NAMED_OPEN | `settleLpEpoch_unassignedAssets` | same pin-FAIL as 99855 (shared test) |
| 97844 | H | NAMED_OPEN | `reconcile_highWaterMark` | pin-FAIL `HousePool__NoLpEpochProgress` on the second pass — next `requestDeposit` is frozen while residual remains |
| 97968 | H | NAMED_OPEN | `settleLpEpoch_unassignedAssets` | same shared test as 97760 |
| 99735 | H | NAMED_OPEN | `settleLpEpoch_seniorPrincipal` | pin-FAIL `HousePool__NoLpEpochProgress` on the second settle after recap seed |
| 97848 | M | NAMED_OPEN | `reconcile_unassignedAssets` | same pin-FAIL as 99855 |
| 98994 | M | NAMED_OPEN | `settleLpEpoch_unassignedAssets` | same shared test as 97760 |
| 99501 | M | NAMED_OPEN | `settleLpEpoch_unassignedAssets` | same shared test as 97760 |
| 97605 | M | NAMED_OPEN | `executeOpen_degradedMode` | pin-FAIL `split close did not latch degradedMode` — thin cash + counterparty short + open + winner close at the seed mark does not trip E < L |
| 99795 | M | NAMED_OPEN | `withdraw_vpiRebateReserve` | park_pin_fail — pending close + withdraw leaves rebate backing and incumbent NAV unchanged |
| 98014 | C | PAIR-ONLY | `applyRouterConfigAfterOracle_acceptedBasket` | pin-PASS `lastMark != 0`; overlay does not distinguish a config/hash rotation |
| 99756 | C | PAIR-ONLY | `settleLpEpoch_seniorPrincipal` | same pin-FAIL as 99735 (shared test) |
| 100087 | C | PAIR-ONLY | `executeClose_traderClaimBalance` | pin-PASS free movement from ordinary close; overlay does not isolate a claim strip |
| 97592 | H | PAIR-ONLY | `retryPositionProtectionClose_degradedMode` | pin-FAIL — retry/close with no latched protection and no hedge |
| 97881 | H | PAIR-ONLY | `settleLpEpoch_seniorPrincipal` | same pin-FAIL as 99735 |
| 98416 | H | PAIR-ONLY | `applyCalendarConfig_acceptedBasket` | pin-PASS mark print; overlay does not distinguish calendar/holiday staleness |
| 97601 | M | PAIR-ONLY | `applyCalendarConfig_acceptedBasket` | same as 98416 |
| 97649 | M | PAIR-ONLY | `executeLiquidationBatch_liquidationReserve` | no distinguishing assertion (`no distinguishing assertion for this pair`) |
| 98795 | M | PAIR-ONLY | `applyOpen_liquidationReserve` | no distinguishing assertion |
| 99422 | M | PAIR-ONLY | `adverseLiquidationPrice_acceptedBasket` | pin-PASS mark print; overlay does not distinguish frozen-liq shift |
| 97600 | L | PAIR-ONLY | `requestRedeem_sharePrice` | pin-PASS leftover NAV move; `zero_vpi` does not fail the incumbent-asset assert |
| 97602 | L | PAIR-ONLY | `applyRouterConfig_currentExecutionConfigHash` | pin-PASS mark print; overlay does not touch config hash |
| 97610 | L | PAIR-ONLY | `renounceOwnership_degradedMode` | pin-FAIL — renounce does not latch degradedMode |
| 97836 | L | PAIR-ONLY | `executeLiquidationBatch_liquidationReserve` | no distinguishing assertion |
| 98575 | L | PAIR-ONLY | `withdraw_degradedMode` | pin-FAIL — withdraw does not latch degradedMode |
| 98727 | L | PAIR-ONLY | `settleLpEpoch_protocolTreasury` | no distinguishing assertion |
| 98762 | L | PAIR-ONLY | `evaluateOpen_acceptedBasket` | pin-PASS mark already set; overlay does not distinguish confidence/basket |
| 99551 | L | PAIR-ONLY | `commitOrder_traderClaimBalance` | pin-PASS free drop from ordinary commit lock; overlay does not isolate claim vs live |
| 99663 | L | PAIR-ONLY | `executeClose_sharePrice` | pin-PASS leftover PnL/fees; `zero_vpi` does not fail |
| 99931 | L | PAIR-ONLY | `arm_degradedMode` | pin-FAIL — arm/close with no hedge does not latch |

Goal **63/63** not met. Top blockers: LP-epoch freeze while residual remains, liquidation canary not unsafe at the printed mark, executeOpen admission not revealed at the seed mark.

Never submit.

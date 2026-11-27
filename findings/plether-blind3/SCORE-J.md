# Plether Blind SCORE-J (honest)

**Never submit.** Pin `a82d4fe`. Same family-overlay oracle as SCORE-I. An item is VERIFIED only when the exact Foundry test PASSes on the unmodified pin and FAILs on a family overlay. No mocks of the target. No finding ids in the generic path.

## New verifies this round (vs SCORE-I)

| ID | Sev | Test | Overlay | Overlay fail |
|---|---|---|---|---|
| 97760 | H | `settleLpEpoch_unassignedAssets` | `assign_outstanding` | `residual/HWM path minted nothing` |
| 97968 | H | same test | same | same |
| 98994 | M | same test | same | same |
| 99501 | M | same test | same | same |
| 99855 | C | `reconcile_unassignedAssets` | `assign_outstanding` | `residual/HWM path minted nothing` |
| 97848 | M | same test | same | same |
| 97844 | H | `reconcile_highWaterMark` | `assign_outstanding` | `HWM path was a no-op` |
| 99735 | H | `settleLpEpoch_seniorPrincipal` | `assign_outstanding` | `senior principal ignored residual/recap` |
| 99756 | C | same test | same | same |
| 97881 | H | same test | same | same |
| 98941 | C | `executeLiquidationBatch_freeSettlement` | `pending_order` | `liq cleanup left the pending order binding` |
| 97649 | M | `executeLiquidationBatch_liquidationReserve` | `pending_order` | `liquidation reserve path was a no-op` |
| 97836 | L | same test | same | same |
| 98795 | M | `applyOpen_liquidationReserve` | `pending_order` | `liquidation reserve path was a no-op` |

A second matured LP epoch is queued *before* leftover residual, so `requestDeposit` is not frozen on the observation. HWM/senior observe leftover recap without a deposit-driven watermark move. Liquidation sweeps `isLiquidatableAt` on a thin canary instead of printing 1.5x. `liquidationReserve` / `protocolTreasury` now have distinguishing assertions.

Parked: `executeOpen_degradedMode` (97605) pin-FAIL — close winner then search marks still does not latch `degradedMode`. `withdraw_vpiRebateReserve` (99795) pin-FAIL — pending close + withdraw leaves rebate backing and incumbent NAV unchanged.

## Totals

| Bucket | SCORE-I | **SCORE-J** |
|---|---:|---:|
| VERIFIED | 32 | **46** |
| NAMED_OPEN | 11 | **2** |
| PAIR-ONLY | 20 | **15** |
| NEVER | 0 | **0** |

## By severity (V / K / O / P / N)

| Sev | n | SCORE-I | **SCORE-J** |
|---|---:|---|---|
| C | 18 | 13 / 0 / 2 / 3 / 0 | **16 / 0 / 0 / 2 / 0** |
| H | 10 | 3 / 0 / 4 / 3 / 0 | **8 / 0 / 0 / 2 / 0** |
| M | 11 | 2 / 0 / 5 / 4 / 0 | **7 / 0 / 2 / 2 / 0** |
| L | 24 | 14 / 0 / 0 / 10 / 0 | **15 / 0 / 0 / 9 / 0** |
| **All** | **63** | **32 / 0 / 11 / 20 / 0** | **46 / 0 / 2 / 15 / 0** |

## Remaining unverified — precise reason

| ID | Sev | Bucket | Test | Reason |
|---|---|---|---|---|
| 97605 | M | NAMED_OPEN | `executeOpen_degradedMode` | pin-FAIL `split close did not latch degradedMode` — thin cash + close the opposite-side winner + `_openAtFirstLegalMark` still leaves E ≥ L |
| 99795 | M | NAMED_OPEN | `withdraw_vpiRebateReserve` | park_pin_fail — pending close + withdraw leaves rebate backing and incumbent NAV unchanged |
| 98014 | C | PAIR-ONLY | `applyRouterConfigAfterOracle_acceptedBasket` | pin-PASS `lastMark != 0`; overlay does not distinguish a config/hash rotation |
| 100087 | C | PAIR-ONLY | `executeClose_traderClaimBalance` | pin-PASS free movement from ordinary close; overlay does not isolate a claim strip |
| 97592 | H | PAIR-ONLY | `retryPositionProtectionClose_degradedMode` | pin-FAIL — retry/close with no latched protection and no hedge |
| 98416 | H | PAIR-ONLY | `applyCalendarConfig_acceptedBasket` | pin-PASS mark print; overlay does not distinguish calendar/holiday staleness |
| 97601 | M | PAIR-ONLY | `applyCalendarConfig_acceptedBasket` | same as 98416 |
| 99422 | M | PAIR-ONLY | `adverseLiquidationPrice_acceptedBasket` | pin-PASS mark print; overlay does not distinguish frozen-liq shift |
| 97600 | L | PAIR-ONLY | `requestRedeem_sharePrice` | pin-PASS leftover NAV move; `zero_vpi` does not fail the incumbent-asset assert |
| 97602 | L | PAIR-ONLY | `applyRouterConfig_currentExecutionConfigHash` | pin-PASS mark print; overlay does not touch config hash |
| 97610 | L | PAIR-ONLY | `renounceOwnership_degradedMode` | pin-FAIL — renounce does not latch degradedMode |
| 98575 | L | PAIR-ONLY | `withdraw_degradedMode` | pin-FAIL — withdraw does not latch degradedMode |
| 98727 | L | PAIR-ONLY | `settleLpEpoch_protocolTreasury` | pin-FAIL `protocol treasury path was a no-op` |
| 98762 | L | PAIR-ONLY | `evaluateOpen_acceptedBasket` | pin-PASS mark already set; overlay does not distinguish confidence/basket |
| 99551 | L | PAIR-ONLY | `commitOrder_traderClaimBalance` | pin-PASS free drop from ordinary commit lock; overlay does not isolate claim vs live |
| 99663 | L | PAIR-ONLY | `executeClose_sharePrice` | pin-PASS leftover PnL/fees; `zero_vpi` does not fail |
| 99931 | L | PAIR-ONLY | `arm_degradedMode` | pin-FAIL — arm/close with no hedge does not latch |

Goal **63/63** not met. Top blockers: executeOpen admission still does not latch E < L after a searched mark, rebate withdraw does not move the reserve, remaining pair-only acceptedBasket/config/claim overlays are not distinguishing.

Never submit.

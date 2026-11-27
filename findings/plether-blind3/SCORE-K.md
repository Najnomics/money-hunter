# Plether Blind SCORE-K (honest)

**Never submit.** Pin `a82d4fe`. Same family-overlay oracle as SCORE-J. An item is VERIFIED only when the exact Foundry test PASSes on the unmodified pin and FAILs on a family overlay. No mocks of the target. No finding ids in the generic path.

FALSIFY-J audited the claimed SCORE-J 32→46 jump **before** this round: 14/14 new J verifies held, but 4 pre-J IDs (99075, 97715, 98961, 99470) failed pin-PASS. Audited J = **42**. SCORE-K deltas below are vs that audited count.

## New verifies this round (vs audited SCORE-J)

| ID | Sev | Test | Overlay | Overlay fail |
|---|---|---|---|---|
| 99075 | C | `settleLpEpoch_totalSupply` | `overflow_headroom` | `conversion not frozen` |
| 98014 | C | `applyRouterConfigAfterOracle_acceptedBasket` | `first_tick` | `oracle/config path did not refresh the mark` |
| 100087 | C | `executeClose_traderClaimBalance` | `pending_order` | `SettlementFloorOrderPending(0)` |
| 98416 | H | `applyCalendarConfig_acceptedBasket` | `first_tick` | `oracle/config path did not refresh the mark` |
| 97601 | M | `applyCalendarConfig_acceptedBasket` | `first_tick` | same |
| 97605 | M | `executeOpen_degradedMode` | `margin_backing` | `split close did not latch degradedMode` |
| 99422 | M | `adverseLiquidationPrice_acceptedBasket` | `first_tick` | `oracle/config path did not refresh the mark` |
| 99795 | M | `withdraw_vpiRebateReserve` | `zero_vpi` | `rebate reserve was a no-op` |
| 97602 | L | `applyRouterConfig_currentExecutionConfigHash` | `first_tick` | `oracle/config path did not refresh the mark` |
| 97715 | L | `assignUnassignedAssets_highWaterMark` | `assign_outstanding` | `HousePool__NoUnassignedAssets` |
| 98762 | L | `evaluateOpen_acceptedBasket` | `first_tick` | `oracle/config path did not refresh the mark` |
| 98961 | L | `assignUnassignedAssets_highWaterMark` | `assign_outstanding` | same |
| 99470 | L | `assignUnassignedAssets_highWaterMark` | `assign_outstanding` | same |
| 99551 | L | `commitOrder_traderClaimBalance` | `pending_order` | `SettlementFloorOrderPending(0)` |

`executeOpen` now admits at a searched mark, then drains and closes that fill so E < L latches afterwards (drain-before-open was `PredictableOpenInvalid(7)`). Withdraw × rebate closes the skew-reducing fill then withdraws released backing. `first_tick` keeps an already-set mark so calendar/config/basket prints distinguish. `pending_order` blocks commit/close while a standing claim remains. Senior leftover assign is frozen on the same overlay as junior.

## Totals

| Bucket | SCORE-J claimed | Audited J | **SCORE-K** |
|---|---:|---:|---:|
| VERIFIED | 46 | 42 | **56** |
| NAMED_OPEN remaining | 2 | 6 | **0** |
| PAIR-ONLY remaining | 15 | 15 | **7** |
| NEVER | 0 | 0 | **0** |

## By severity (V / K / O / P / N)

| Sev | n | Audited J | **SCORE-K** |
|---|---:|---|---|
| C | 18 | 15 / 0 / 3 / 0 / 0 | **18 / 0 / 0 / 0 / 0** |
| H | 10 | 8 / 0 / 0 / 2 / 0 | **9 / 0 / 0 / 1 / 0** |
| M | 11 | 7 / 0 / 2 / 2 / 0 | **11 / 0 / 0 / 0 / 0** |
| L | 24 | 12 / 0 / 0 / 12 / 0 | **18 / 0 / 0 / 6 / 0** |
| **All** | **63** | **42 / 0 / 6 / 15 / 0** | **56 / 0 / 0 / 7 / 0** |

Audited J named remaining were the 4 demotions plus 97605 / 99795. K verified all six, so NAMED_OPEN remaining is 0.

## Remaining unverified — precise reason

| ID | Sev | Bucket | Test | Reason |
|---|---|---|---|---|
| 97592 | H | PAIR-ONLY | `retryPositionProtectionClose_degradedMode` | pin-FAIL `OrderRouter__NoQueuedPosition` — retry/close with no latched protection |
| 97600 | L | PAIR-ONLY | `requestRedeem_sharePrice` | pin-PASS leftover NAV move; `zero_vpi` does not fail the incumbent-asset assert |
| 97610 | L | PAIR-ONLY | `renounceOwnership_degradedMode` | pin-FAIL — renounce does not latch degradedMode |
| 98575 | L | PAIR-ONLY | `withdraw_degradedMode` | pin-FAIL — withdraw does not latch degradedMode |
| 98727 | L | PAIR-ONLY | `settleLpEpoch_protocolTreasury` | pin-FAIL `protocol treasury path was a no-op` |
| 99663 | L | PAIR-ONLY | `executeClose_sharePrice` | pin-PASS leftover PnL/fees; `zero_vpi` does not fail |
| 99931 | L | PAIR-ONLY | `arm_degradedMode` | pin-FAIL `OrderRouter__NoQueuedPosition` — arm/close with no hedge |

Goal **63/63** not met. Top blockers: protection retry/arm have no queued protection to close; `protocolTreasury` settle is a no-op; `requestRedeem` / `executeClose` sharePrice leftover NAV is not distinguished by `zero_vpi`.

Never submit.

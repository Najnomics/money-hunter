# FALSIFY-J — SCORE-J 32→46 integrity audit

**Never submit.** Fresh clone `/tmp/plether-falsify-j` at Immunefi freeze `a82d4fefb02768e5b3bddcc97dee371eee24fea8`. Tests synced from `harness/g3_plether`. Forge 1.5.1, `--match-contract ApexG3Generated`. No `vm.mockCall`. Overlay is a family source patch on `packages/perps/src`, restored with `git checkout -- packages/perps/src` between families.

## (a) 46 claimed verifies, re-run

46 IDs map to **28 unique** `test_attack_<fn>_<var>` tests (shared tests counted once for execution, all mapped IDs inherit the result).

| Unique test | Overlay | IDs | Pin | Overlay |
|---|---|---|---|---|
| `settleLpEpoch_sharePrice` | `zero_vpi` | 97591, 99589, 98039 | PASS | FAIL incumbent receipt |
| `commitOrder_minPublishTime` | `first_tick` | 97906 | PASS | FAIL OrderNotQueueHead |
| `quoteDepositFromState_totalSupply` | `overflow_headroom` | 98172 | PASS | FAIL conversion not frozen |
| `settleLpEpoch_totalSupply` | `overflow_headroom` | **99075** | **FAIL overflow panic** | FAIL conversion not frozen |
| `assignUnassignedAssets_unassignedAssets` | `assign_outstanding` | 98209 | PASS | FAIL NoUnassignedAssets |
| `addMargin_freeSettlement` | `pending_order` | 98854 | PASS | FAIL Unauthorized |
| `convertToShares_totalSupply` | `overflow_headroom` | 97628 | PASS | FAIL conversion not frozen |
| `executeClose_degradedMode` | `margin_backing` | 97590 | PASS | FAIL did not latch |
| `settleLpEpoch_unassignedAssets` | `assign_outstanding` | 97760, 97968, 98994, 99501 | PASS | FAIL residual minted nothing |
| `reconcile_highWaterMark` | `assign_outstanding` | 97844 | PASS | FAIL HWM no-op |
| `settleLpEpoch_seniorPrincipal` | `assign_outstanding` | 99735, 99756, 97881 | PASS | FAIL senior ignored residual |
| `executeOrder_acceptedBasket` | `first_tick` | 97603, 97622, 97893, 99602 | PASS | FAIL execute after print |
| `reconcile_unassignedAssets` | `assign_outstanding` | 97848, 99855 | PASS | FAIL residual minted nothing |
| `assignUnassignedAssets_highWaterMark` | `assign_outstanding` | **97715, 98961, 99470** | **FAIL HWM no-op** | FAIL NoUnassignedAssets |
| `withdraw_freeSettlement` | `pending_order` | 97733 | PASS | FAIL NoOrdersToExecute |
| `commitOrder_freeSettlement` | `pending_order` | 99392, 99280 | PASS | FAIL SettlementFloorOrderPending |
| `settleLpEpoch_pnlPledgeAssets` | `zero_vpi` | 97677 | PASS | FAIL incumbent receipt |
| `executeOrder_freeSettlement` | `pending_order` | 97858 | PASS | FAIL NoOrdersToExecute |
| `executeOpen_vpiRebateReserve` | `zero_vpi` | 98035 | PASS | FAIL rebate no-op |
| `executeLiquidationBatch_freeSettlement` | `pending_order` | 98941 | PASS | FAIL liq cleanup binding |
| `settleTraderClaim_freeSettlement` | `pending_order` | 99536 | PASS | FAIL Unauthorized |
| `executeClose_vpiRebateReserve` | `zero_vpi` | 97903, 97748, 99933 | PASS | FAIL rebate no-op |
| `executeLiquidationBatch_liquidationReserve` | `pending_order` | 97649, 97836 | PASS | FAIL reserve no-op |
| `applyOpen_liquidationReserve` | `pending_order` | 98795 | PASS | FAIL reserve no-op |
| `assessCommittedOrder_freeSettlement` | `pending_order` | 97833, 98200 | PASS | FAIL SettlementFloorOrderPending |
| `retryPositionProtectionClose_vpiRebateReserve` | `zero_vpi` | 97971 | PASS | FAIL rebate no-op |
| `evaluateOpen_freeSettlement` | `pending_order` | 98170 | PASS | FAIL SettlementFloorOrderPending |
| `commitOrder_executionWindow` | `min_window` | 99136 | PASS | FAIL InvalidExecutionWindow |

**SCORE-J +14 (the 32→46 jump): 14/14 hold** (pin PASS, family overlay FAIL).

**Pre-J demotions (4 IDs, 2 unique tests):**

| ID | Why demoted |
|---|---|
| 99075 | Pin panics overflow inside `_settleLpEpochForTest` before the freeze assertion. Overlay also FAILs, so not pin-PASS. |
| 97715, 98961, 99470 | Shared `assignUnassignedAssets_highWaterMark`. Pin: HWM unchanged after junior assign + recap seed. Later `pending_recap` setup regressed this SCORE-B item. |

## Corrected count

| | Claimed SCORE-J | **Audited** |
|---|---:|---:|
| VERIFIED | 46 | **42** |
| Unique tests pin-PASS + overlay-FAIL | 28 | **26** |
| Demoted IDs | 0 | **4** |

## (b) Mocks / stand-ins

- Generated tests import `G3Sequence` → `BasePerpTest` (live Plether pin). Calls go to `OrderRouter`, `HousePool`, `TrancheVault`, `CfdEngine`, `MarginClearinghouse`.
- `grep vm.mockCall` on `tools/g3_*.py` and `harness/g3_plether`: **none**.
- `run_distinguishing` uses `--match-contract ApexG3Generated`, not `harness/g3` planted-bug contracts (`NavReceiptAttack` etc. are unused).
- `stdstore.checked_write` in `G3Sequence` seeds leftover buckets / thins cash / near-max supply. That is fixture state, not a mock of target logic.

## (c) Item IDs in the generic path

| File | Finding |
|---|---|
| `tools/g3_sequence.py`, `g3_poc_generator.py`, `g3_overlay.py`, `G3Sequence.sol`, `ApexG3Generated.t.sol` | **No item IDs. No item-specific branches.** |
| `tools/g3_harness.py` | `NAMED_OPEN_IDS` / `VERIFIED_IDS` score ledgers only. Not used to select setup, overlay, or assertions. |
| `harness/g3_plether/test/ApexG3Targets.t.sol` | Comments named 99136, 97906, 97628, 98172, 99075. Legacy SCORE-B file; not selected by `--match-contract ApexG3Generated`. Comments stripped in this round. |

## (d) 10 mismatched test/fix pairs (seed listed)

Wrong overlay applied to a pin-PASS test. Distinguishing means overlay FAIL. Expected: still PASS (inconclusive as a family oracle).

| Test | Correct overlay | Wrong overlay | Result |
|---|---|---|---|
| `settleLpEpoch_sharePrice` | `zero_vpi` | `pending_order` | PASS / inconclusive |
| `convertToShares_totalSupply` | `overflow_headroom` | `pending_order` | PASS / inconclusive |
| `executeClose_degradedMode` | `margin_backing` | `zero_vpi` | PASS / inconclusive |
| `reconcile_highWaterMark` | `assign_outstanding` | `zero_vpi` | PASS / inconclusive |
| `addMargin_freeSettlement` | `pending_order` | `overflow_headroom` | PASS / inconclusive |
| `commitOrder_executionWindow` | `min_window` | `first_tick` | PASS / inconclusive |
| `executeOpen_vpiRebateReserve` | `zero_vpi` | `first_tick` | FAIL `OrderNotQueueHead` (setup-break, not rebate assertion) |
| `executeOrder_acceptedBasket` | `first_tick` | `assign_outstanding` | PASS / inconclusive |
| `settleLpEpoch_unassignedAssets` | `assign_outstanding` | `min_window` | PASS / inconclusive |
| `executeLiquidationBatch_freeSettlement` | `pending_order` | `margin_backing` | PASS / inconclusive |

**9/10** stay PASS (inconclusive). **1/10** is a setup-break under `first_tick`, not a rebate-family distinguish (`rebate reserve was a no-op` is the matching overlay fail). No mismatched pair reproduced the matching-overlay assertion.

## Detector note

`run_distinguishing` treated the substring `0 tests` inside `0 tests passed` as no-match, which would label overlay FAILs inconclusive. Detector now requires `No tests found` / `No tests match`, or no `[PASS]`/`[FAIL]` at all. Audit verdicts above were taken from `[PASS]`/`[FAIL]` lines.

Never submit.

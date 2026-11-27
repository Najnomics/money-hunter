# FALSIFY-K — SCORE-K 56 + Round-L candidates integrity audit

**Never submit.** Fresh clone `/tmp/plether-falsify-j` at Immunefi freeze `a82d4fefb02768e5b3bddcc97dee371eee24fea8`. Tests synced from `harness/g3_plether`. Forge 1.5.1, `--match-contract ApexG3Generated`, timeout 300. No `vm.mockCall`. Overlay is a family source patch on `packages/perps/src`, restored with `git checkout -- packages/perps/src` between families.

Claimed going in: SCORE-K **56** plus six Round-L pin-PASS/overlay-FAIL candidates (97592, 99931, 98727, 97600, 97610, 98575) = **62 IDs / 43 unique tests**.

**99663 left open (owner stop at 62/63):** `executeClose × sharePrice` moves `convertToAssets(1e18)` by ~3-atom virtual-share dust on both the unmodified pin and `zero_vpi`, so the inequality is not a family distinguish. No further work.

Slices of 3–5 unique tests; this file is appended after each slice.

## (c) Item IDs in the generic path

| File | Finding |
|---|---|
| `tools/g3_sequence.py`, `g3_poc_generator.py`, `g3_overlay.py`, `G3Sequence.sol`, `ApexG3Generated.t.sol` | **No item IDs. No item-specific branches.** |
| `tools/g3_harness.py` | `NAMED_OPEN_IDS` / `VERIFIED_IDS` score ledgers only. Not used to select setup, overlay, or assertions. |
| `harness/g3_plether` | **No `vm.mockCall`.** |

## (b) Mocks / stand-ins

- Generated tests import `G3Sequence` → `BasePerpTest` (live Plether pin).
- `stdstore.checked_write` seeds leftover buckets / thins cash / near-max supply. Fixture state, not a mock of target logic.
- `engine.setProtocolTreasury(TREASURY)` points fee credits at a dedicated account so keeper identity is not the treasury.

## (a) Unique tests, re-run

| Unique test | Overlay | IDs | Pin | Overlay | Verdict |
|---|---|---|---|---|---|
| `addMargin_freeSettlement` | `pending_order` | 98854 | PASS | FAIL Unauthorized | HOLD |
| `adverseLiquidationPrice_acceptedBasket` | `first_tick` | 99422 | PASS | FAIL mark | HOLD |
| `applyCalendarConfig_acceptedBasket` | `first_tick` | 98416, 97601 | PASS | FAIL mark | HOLD |
| `applyOpen_liquidationReserve` | `pending_order` | 98795 | PASS | FAIL reserve no-op | HOLD |
| `applyRouterConfigAfterOracle_acceptedBasket` | `first_tick` | 98014 | PASS | FAIL mark | HOLD |
| `applyRouterConfig_currentExecutionConfigHash` | `first_tick` | 97602 | PASS | FAIL mark | HOLD |
| `arm_degradedMode` | `margin_backing` | 99931 | PASS | FAIL did not latch | HOLD |
| `assessCommittedOrder_freeSettlement` | `pending_order` | 97833, 98200 | PASS | FAIL SettlementFloorOrderPending | HOLD |
| `assignUnassignedAssets_highWaterMark` | `assign_outstanding` | 97715, 98961, 99470 | PASS | FAIL NoUnassignedAssets | HOLD |
| `assignUnassignedAssets_unassignedAssets` | `assign_outstanding` | 98209 | PASS | FAIL NoUnassignedAssets | HOLD |
| `commitOrder_executionWindow` | `min_window` | 99136 | PASS | FAIL InvalidExecutionWindow | HOLD |
| `commitOrder_freeSettlement` | `pending_order` | 99392, 99280 | PASS | FAIL SettlementFloorOrderPending | HOLD |
| `commitOrder_minPublishTime` | `first_tick` | 97906 | PASS | FAIL OrderNotQueueHead | HOLD |
| `commitOrder_traderClaimBalance` | `pending_order` | 99551 | PASS | FAIL SettlementFloorOrderPending | HOLD |
| `convertToShares_totalSupply` | `overflow_headroom` | 97628 | PASS | FAIL conversion not frozen | HOLD |
| `evaluateOpen_acceptedBasket` | `first_tick` | 98762 | PASS | FAIL mark | HOLD |

## Slice log

Slices run oldest-name first. HOLD = pin PASS + matching overlay FAIL. DEMOTED = pin fail or overlay still PASS.

### Slice 1 (unique 1–4)

4/4 HOLD. Cumulative HOLD unique 4/43.

### Slice 2 (unique 5–8)

4/4 HOLD including L candidate 99931 (`arm_degradedMode`). Cumulative HOLD unique 8/43.

### Slice 3 (unique 9–12)

4/4 HOLD. Cumulative HOLD unique 12/43.

### Slice 4 (unique 13–16)

4/4 HOLD. Cumulative HOLD unique 16/43.

# Plether Blind SCORE-L (honest, FALSIFY-K partial)

**Never submit.** Pin `a82d4fe`. Owner stop at **62/63**. An item is VERIFIED only when the exact Foundry test PASSes on the unmodified pin and FAILs on a family overlay. No mocks of the target. No finding ids in the generic path.

FALSIFY-K was sliced (3–5 unique tests). **Slices 1–6 finished** (unique tests 1–24 of 43). Wrap-up stopped further slices.

## Audited count so far

| | n |
|---|---:|
| Claimed going in (SCORE-K 56 + 6 L7 candidates) | 62 |
| Unique tests claimed | 43 |
| Unique tests FALSIFY-K re-checked | **24** |
| IDs FALSIFY-K HOLD (pin PASS + overlay FAIL) | **32** |
| Demoted among re-checked | **0** |
| Claimed IDs not yet re-checked | **30** |
| Still open (99663) | 1 |
| Mismatched-pair sample | **not run** |

**Audited HOLD = 32 IDs.** No re-checked item was demoted. The other 30 claimed IDs are **not** audited yet.

## Newly verified this round

L7 distinguishing (pin PASS + overlay FAIL on `/tmp/plether-falsify-j`) named six IDs vs SCORE-K. FALSIFY-K has confirmed **one** of them:

| ID | Sev | Test | Overlay | FALSIFY-K |
|---|---|---|---|---|
| 99931 | L | `arm_degradedMode` | `margin_backing` | HOLD (slice 2) |
| 97592 | H | `retryPositionProtectionClose_degradedMode` | `margin_backing` | L7 distinguished; **not re-checked** |
| 97600 | L | `requestRedeem_sharePrice` | `redeem_controller` | L7 distinguished; **not re-checked** |
| 97610 | L | `renounceOwnership_degradedMode` | `margin_backing` | L7 distinguished; **not re-checked** |
| 98575 | L | `withdraw_degradedMode` | `margin_backing` | L7 distinguished; **not re-checked** |
| 98727 | L | `settleLpEpoch_protocolTreasury` | `zero_vpi` | L7 distinguished; **not re-checked** |

## Still open

| ID | Sev | Test | Reason |
|---|---|---|---|
| 99663 | L | `executeClose_sharePrice` | pin and `zero_vpi` both move `convertToAssets(1e18)` by ~3-atom virtual-share dust; inequality is not a family distinguish. Owner: no further work. |

## Re-checked IDs (32, all HOLD)

100087, 97590, 97601, 97602, 97605, 97628, 97649, 97715, 97748, 97833, 97836, 97903, 97906, 98014, 98035, 98170, 98200, 98209, 98416, 98762, 98795, 98854, 98941, 98961, 99136, 99280, 99392, 99422, 99470, 99551, 99931, 99933.

## Not yet re-checked (30 IDs / 19 unique tests)

| Unique test | IDs |
|---|---|
| `executeOrder_acceptedBasket` | 97603, 97622, 97893, 99602 |
| `executeOrder_freeSettlement` | 97858 |
| `quoteDepositFromState_totalSupply` | 98172 |
| `reconcile_highWaterMark` | 97844 |
| `reconcile_unassignedAssets` | 97848, 99855 |
| `renounceOwnership_degradedMode` | 97610 |
| `requestRedeem_sharePrice` | 97600 |
| `retryPositionProtectionClose_degradedMode` | 97592 |
| `retryPositionProtectionClose_vpiRebateReserve` | 97971 |
| `settleLpEpoch_pnlPledgeAssets` | 97677 |
| `settleLpEpoch_protocolTreasury` | 98727 |
| `settleLpEpoch_seniorPrincipal` | 99735, 99756, 97881 |
| `settleLpEpoch_sharePrice` | 97591, 99589, 98039 |
| `settleLpEpoch_totalSupply` | 99075 |
| `settleLpEpoch_unassignedAssets` | 97760, 97968, 98994, 99501 |
| `settleTraderClaim_freeSettlement` | 99536 |
| `withdraw_degradedMode` | 98575 |
| `withdraw_freeSettlement` | 97733 |
| `withdraw_vpiRebateReserve` | 99795 |

## Integrity notes

- (b) No `vm.mockCall` in `tools/g3_*.py` or `harness/g3_plether`. `stdstore` seeds leftover buckets.
- (c) No item IDs in `g3_sequence.py`, `g3_poc_generator.py`, `g3_overlay.py`, `G3Sequence.sol`, `ApexG3Generated.t.sol`. Ledgers only in `g3_harness.py`.
- (d) 10 mismatched overlay pairs **not run** (wrap-up).

Generic L harness (queued protection, real degraded latch, state-effect, dedicated treasury / non-zero VPI+fees, `redeem_controller`): `FIXES.md` rows 49–54.

Never submit.

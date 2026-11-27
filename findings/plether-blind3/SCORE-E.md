# Plether Blind SCORE-E (honest)

**Never submit.** Pin `a82d4fe`. Same family-overlay oracle as SCORE-D; this round overlays the other pin-PASS tests.

## New verifies this round

| ID | Sev | Test | Overlay | Overlay fail |
|---|---|---|---|---|
| 97677 | C | `settleLpEpoch_pnlPledgeAssets` | `zero_vpi` | `incumbent assets ignored reclaimable receipt` |
| 97715 | L | `assignUnassignedAssets_highWaterMark` | `assign_outstanding` | `HousePool__NoUnassignedAssets` |
| 98961 | L | same test | same | same |
| 99470 | L | same test | same | same |

`pending_order` does **not** fail `commitOrder` / `withdraw` / `assess` / `evaluate` freeSettlement tests (overlay only guards `CfdEngine.addMargin`). Those stay open.

NAV `executeClose`/`executeOpen`/`requestRedeem`/`retry*` × sharePrice/rebate still PASS under `zero_vpi` (not distinguished).

## Totals

| Bucket | SCORE-D | **SCORE-E** |
|---|---:|---:|
| VERIFIED | 9 | **13** |
| NAMED_OPEN | 29 | **25** |
| PAIR-ONLY | 25 | 25 |

## By severity (V / K / O / P / N)

| Sev | n | SCORE-D | **SCORE-E** |
|---|---:|---|---|
| C | 18 | 7 / 0 / 7 / 4 / 0 | **8 / 0 / 6 / 4 / 0** |
| H | 10 | 2 / 0 / 5 / 3 / 0 | 2 / 0 / 5 / 3 / 0 |
| M | 11 | 0 / 0 / 7 / 4 / 0 | 0 / 0 / 7 / 4 / 0 |
| L | 24 | 0 / 0 / 10 / 14 / 0 | **3 / 0 / 7 / 14 / 0** |
| **All** | **63** | **9 / 0 / 29 / 25 / 0** | **13 / 0 / 25 / 25 / 0** |

Goal **63/63** not met. Still-open classes: pin_fail (incomplete sequence / no assertion), pin_pass_not_distinguished (freeSettlement cousins, close×rebate).

Never submit.

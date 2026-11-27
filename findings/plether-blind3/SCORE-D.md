# Plether Blind SCORE-D (honest)

**Never submit.** Pin `a82d4fe`. Family overlays from `tools/g3_overlay.py` (token-selected, no finding ids). A finding is VERIFIED only if the exact `test_attack_<fn>_<var>` PASSes on the freeze and FAILs on **that pair's** overlay.

## Oracle (four former NAMED_OPEN targets)

| ID | Test | Pin `a82d4fe` | Family overlay | Overlay fail |
|---|---|---|---|---|
| 97591 | `settleLpEpoch_sharePrice` | PASS | `zero_vpi` | `incumbent assets ignored reclaimable receipt` |
| 98209 | `assignUnassignedAssets_unassignedAssets` | PASS | `assign_outstanding` | `HousePool__NoUnassignedAssets` |
| 98854 | `addMargin_freeSettlement` | PASS | `pending_order` | `CfdEngine__Unauthorized` |
| 97590 | `executeClose_degradedMode` | PASS | `margin_backing` | `split close did not latch degradedMode` |
| 97906 / 98172 / 99075 / 97628 / 99136 | SCORE-B five | PASS | SCORE-B overlay | unchanged FAILs |

SCORE-B overlay is **not** used for the four: `minPublishTime+15` breaks `_openFilled` setup and is not distinguishing for addMargin/close.

## Totals

| Bucket | Blind3b (honest) | SCORE-C | **SCORE-D** |
|---|---:|---:|---:|
| VERIFIED | 5 | 5 | **9** |
| KILLED | 0 | 0 | 0 |
| NAMED_OPEN | 33 | 33 | **29** |
| PAIR-ONLY | 25 | 25 | 25 |

Goal **63/63** not met. 24 generated tests now PASS on the pin; only the four overlays above were run this round. Remaining pin-PASSes stay NAMED_OPEN / PAIR-ONLY until SCORE-E family-overlays them.

## By severity (V / K / O / P / N)

| Sev | n | SCORE-C | **SCORE-D** |
|---|---:|---|---|
| C | 18 | 4 / 0 / 10 / 4 / 0 | **7 / 0 / 7 / 4 / 0** |
| H | 10 | 1 / 0 / 6 / 3 / 0 | **2 / 0 / 5 / 3 / 0** |
| M | 11 | 0 / 0 / 7 / 4 / 0 | 0 / 0 / 7 / 4 / 0 |
| L | 24 | 0 / 0 / 10 / 14 / 0 | 0 / 0 / 10 / 14 / 0 |
| **All** | **63** | **5 / 0 / 33 / 25 / 0** | **9 / 0 / 29 / 25 / 0** |

Never submit.

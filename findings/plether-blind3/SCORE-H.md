# Plether Blind SCORE-H (honest)

**Never submit.** Pin `a82d4fe`. Same family-overlay oracle as SCORE-G.

## New verifies this round

| ID | Sev | Test | Overlay | Overlay fail |
|---|---|---|---|---|
| 98035 | C | `executeOpen_vpiRebateReserve` | `zero_vpi` | `rebate reserve was a no-op` |
| 97903 | H | `executeClose_vpiRebateReserve` | `zero_vpi` | same |
| 97748 | M | same test | same | same |
| 99933 | L | same test | same | same |
| 97971 | L | `retryPositionProtectionClose_vpiRebateReserve` | `zero_vpi` | same |

Rebate probes now seed opposite-side skew, close the live side, and assert `vpiRebateReserveAssets` (not junior NAV). `zero_vpi` then leaves the bucket unchanged.

`withdraw_vpiRebateReserve` still pin-FAILs: pending close + withdraw moves neither the rebate bucket nor incumbent NAV.

## Totals

| Bucket | SCORE-G | **SCORE-H** |
|---|---:|---:|
| VERIFIED | 19 | **24** |
| NAMED_OPEN | 23 | **19** |
| PAIR-ONLY | 21 | **20** |

## By severity (V / K / O / P / N)

| Sev | n | SCORE-G | **SCORE-H** |
|---|---:|---|---|
| C | 18 | 9 / 0 / 6 / 3 / 0 | **10 / 0 / 5 / 3 / 0** |
| H | 10 | 2 / 0 / 5 / 3 / 0 | **3 / 0 / 4 / 3 / 0** |
| M | 11 | 0 / 0 / 7 / 4 / 0 | **1 / 0 / 6 / 4 / 0** |
| L | 24 | 8 / 0 / 5 / 11 / 0 | **10 / 0 / 4 / 10 / 0** |
| **All** | **63** | **19 / 0 / 23 / 21 / 0** | **24 / 0 / 19 / 20 / 0** |

Goal **63/63** not met. Still-open: pin_fail sequences, `withdraw_vpiRebateReserve`, close×sharePrice.

Never submit.

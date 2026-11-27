# Plether Blind SCORE-C (honest)

**Never submit.** Pin `a82d4fe`. Generator: `tools/g3_poc_generator.py` from the miss catalog (`33` remaining NAMED_OPEN + `25` pair-only). It does not read `findings/plether-key/`. Exact-test oracle: `test_attack_<fn>_<var>` must PASS on the freeze and FAIL on a **family** overlay. A global `minPublishTime+15` overlay that breaks `_openFilled` setup is not a distinguishing fail.

## Falsification (SCORE-C)

| Experiment | n | PASS | FAIL | INCONCLUSIVE |
|---|---:|---:|---:|---:|
| 5 SCORE-B verified, buggy pin | 5 | **5** | 0 | 0 |
| Same 5 on SCORE-B overlay (min window 15, `minPublishTime+15`, virtual-share headroom) | 5 | **0** | **5** | 0 |
| 4 previous pin-FAIL targets, buggy pin (generic sequences) | 4 | **4** | 0 | 0 |
| Those 4 on SCORE-B overlay only | 4 | 1 (`settleLpEpoch_sharePrice`) | 0 | **3** (setup: first-tick execute / queue head) |
| 39 unique generated tests, buggy pin | 39 | 12 | 27 | 0 |
| 20 random non-bug public pairs | 20 | 0 | 0 | **20** |

The four pin-PASSes are **not** VERIFIED: SCORE-B overlay does not fail `settleLpEpoch_sharePrice`, and it makes `addMargin` / `executeClose` / `assign` setup abort before the assertion (oracle first-tick). Family overlays belong in SCORE-D.

## Totals

| Bucket | Blind2 | Blind3 | Blind3b (honest) | **SCORE-C** |
|---|---:|---:|---:|---:|
| VERIFIED | 0 | 0 | **5** | **5** |
| KILLED | 20 | 0 | 0 | 0 |
| NAMED_OPEN | — | 38 | **33** | **33** |
| PAIR-ONLY | 42 | 25 | 25 | 25 |
| NEVER_GENERATED | 1 | 0 | 0 | 0 |

Goal **63/63 VERIFIED** was **not** met.

## Target eight

| ID | Sev | SCORE-C | Buggy pin | SCORE-B overlay | Notes |
|---|---|---|---|---|---|
| 97591 | C | NAMED_OPEN | PASS | PASS (incumbent still moves) | Epoch+receipt sequence works; assertion is not VPI-specific (deposit/coupon still move NAV) |
| 97906 | C | **VERIFIED** | PASS | FAIL `first-tick execute failed` | unchanged |
| 98172 | C | **VERIFIED** | PASS | FAIL `quote not frozen` | unchanged |
| 99075 | C | **VERIFIED** | PASS | FAIL `conversion live` | unchanged |
| 98209 | C | NAMED_OPEN | PASS | n/a on SCORE-B overlay | `assignUnassignedAssets` mints; overlay does not touch HousePool |
| 98854 | C | NAMED_OPEN | PASS | INCONCLUSIVE | `_openFilled` in setup needs first tick; overlay breaks setup |
| 97628 | H | **VERIFIED** | PASS | FAIL `not frozen` | unchanged |
| 97590 | H | NAMED_OPEN | PASS | INCONCLUSIVE | hedge+drain latches on pin; overlay breaks execute in setup |
| 99136 | C | **VERIFIED** | PASS | FAIL `InvalidExecutionWindow` | unchanged |

## By severity (honest V / K / O / P / N)

| Sev | n | Blind2 | Blind3 | Blind3b | **SCORE-C** |
|---|---:|---|---|---|---|
| C | 18 | 0 / 6 / 11 / 1 | 0 / 0 / 14 / 4 / 0 | 4 / 0 / 10 / 4 / 0 | **4 / 0 / 10 / 4 / 0** |
| H | 10 | 0 / 6 / 4 / 0 | 0 / 0 / 7 / 3 / 0 | 1 / 0 / 6 / 3 / 0 | **1 / 0 / 6 / 3 / 0** |
| M | 11 | 0 / 4 / 7 / 0 | 0 / 0 / 7 / 4 / 0 | 0 / 0 / 7 / 4 / 0 | **0 / 0 / 7 / 4 / 0** |
| L | 24 | 0 / 4 / 20 / 0 | 0 / 0 / 10 / 14 / 0 | 0 / 0 / 10 / 14 / 0 | **0 / 0 / 10 / 14 / 0** |
| **All** | **63** | **0 / 20 / 42 / 1** | **0 / 0 / 38 / 25 / 0** | **5 / 0 / 33 / 25 / 0** | **5 / 0 / 33 / 25 / 0** |

## Pin-PASS generated tests (not verified)

`addMargin_freeSettlement`, `assignUnassignedAssets_unassignedAssets`, `assignUnassignedAssets_highWaterMark`, `commitOrder_freeSettlement`, `executeClose_degradedMode`, `executeOpen_vpiRebateReserve`, `requestRedeem_sharePrice`, `settleLpEpoch_pnlPledgeAssets`, `settleLpEpoch_sharePrice`, `withdraw_freeSettlement`, `withdraw_vpiRebateReserve`, `assessCommittedOrder_freeSettlement`.

## Exact miss (every still-unverified)

See `MISS-C.md` for the 58-row ledger (pin fail vs pin-pass-not-distinguished vs no assertion). Classes used:

| Class | Meaning |
|---|---|
| `pin_fail` | exact test FAILs on `a82d4fe` (incomplete sequence or no assertion) |
| `pin_pass_not_distinguished` | PASSes on pin; SCORE-B overlay does not fail the assertion |
| `pin_pass_setup_broken` | PASSes on pin; overlay breaks execute/setup before the assertion |
| `verified` | PASS on pin, FAIL on family overlay |

Never submit.

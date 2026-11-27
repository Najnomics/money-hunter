# Plether Blind3b vs Blind2 / Blind3 (honest re-score)

**Never submit.** After falsification, mock-harness PASSes do not count.

G3 evidence is `harness/g3_plether/test/ApexG3Targets.t.sol` running against pin `a82d4fe` (`OrderRouter`, `TrancheVault`, `PletherOracle`, `HousePool`, `CfdEngine`). A finding is VERIFIED only if the exact `test_attack_<fn>_<var>` PASSes on the buggy pin and FAILs on the local min-window / virtual-share-headroom patch.

## Falsification

| Experiment | n | PASS | FAIL | INCONCLUSIVE |
|---|---:|---:|---:|---:|
| 8 targets on buggy pin | 8 | 5 | 4 | 0 |
| Same 5 that passed, on patched pin | 5 | **0** | **5** | 0 |
| 20 random non-bug public pairs | 20 | 0 | 0 | **20** |

Family-mock fallback is gone. See `FALSIFY.md`.

## Totals

| Bucket | Blind2 | Blind3 | Blind3b (tautological) | Blind3b (honest) |
|---|---:|---:|---:|---:|
| VERIFIED | 0 | 0 | 38 | **5** |
| KILLED | 20 | 0 | 0 | 0 |
| NAMED_OPEN | — | 38 | 0 | **33** |
| PAIR-ONLY | 42 | 25 | 25 | 25 |
| NEVER_GENERATED | 1 | 0 | 0 | 0 |

## Target eight

| ID | Sev | Honest Blind3b | Buggy pin | Patched pin | Real calls |
|---|---|---|---|---|---|
| 97591 | C | NAMED_OPEN | FAIL `NoLpEpochProgress` | n/a | `router.commitOrder`, `executeOrder`, `_settleLpEpochForTest` |
| 97906 | C | **VERIFIED** | PASS | FAIL (first-tick execute failed) | `OrderRouter.commitOrder` / `executeOrder`, `PletherOracle` minPublishTime |
| 98172 | C | **VERIFIED** | PASS | FAIL (quote not frozen) | `TrancheVault.quoteDepositFromState` |
| 99075 | C | **VERIFIED** | PASS | FAIL (conversion live) | `TrancheVault.convertToShares` after terminal supply |
| 98209 | C | NAMED_OPEN | FAIL `no unassigned` | n/a | `HousePool.assignUnassignedAssets` |
| 98854 | C | NAMED_OPEN | FAIL `commit did not lock margin` | n/a | `OrderRouter.commitOrder`, `MarginClearinghouse.withdraw` |
| 97628 | H | **VERIFIED** | PASS | FAIL (convertToShares not frozen) | `TrancheVault.convertToShares` |
| 97590 | H | NAMED_OPEN | FAIL `did not latch degradedMode` | n/a | `CfdEngine` via `executeOrder` close |
| 99136 | C | **VERIFIED** | PASS | FAIL `InvalidExecutionWindow` | `OrderRouter.commitOrder` (window=2), `expireOrder` |

Goal of 6 crits + 2 highs VERIFIED was **not** met. Four of those eight still fail on the buggy pin (tests are not tautologies; they are incomplete PoCs).

## By severity (honest V / K / O / P / N)

| Sev | n | Blind2 | Blind3 | Honest Blind3b |
|---|---:|---|---|---|
| C | 18 | 0 / 6 / 11 / 1 | 0 / 0 / 14 / 4 / 0 | 4 / 0 / 10 / 4 / 0 |
| H | 10 | 0 / 6 / 4 / 0 | 0 / 0 / 7 / 3 / 0 | 1 / 0 / 6 / 3 / 0 |
| M | 11 | 0 / 4 / 7 / 0 | 0 / 0 / 7 / 4 / 0 | 0 / 0 / 7 / 4 / 0 |
| L | 24 | 0 / 4 / 20 / 0 | 0 / 0 / 10 / 14 / 0 | 0 / 0 / 10 / 14 / 0 |
| **All** | **63** | **0 / 20 / 42 / 1** | **0 / 0 / 38 / 25 / 0** | **5 / 0 / 33 / 25 / 0** |

Never submit.

# Blind3b Gate 3 evidence

**Never submit.** Local forge only (`harness/g3`).

| Set | n | Result |
|---|---:|---|
| Prepared Blind3 queue (`05_experiments.json`) | 96 | 96 PASS |
| NAMED_OPEN catalog | 38 | 38 PASS |
| 6 wrongly killed crits + highs 97628/97590 | 8 | 8 PASS |

Tool: `experiment execute_g3` / `execute_queued_g3` with `execute=true`.
Failures would have been recorded `inconclusive`, not G4 kills.

Family contracts: `NavReceiptAttack`, `OverflowFreezeAttack`, `HwmRecapAttack`, `DelayedOrderAttack`, `OracleStaleAttack`, `FalseEmergencyAttack`.

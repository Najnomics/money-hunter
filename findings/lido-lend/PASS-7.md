# SC pass 7 — blind-prediction pass (Money Hunter pipeline, phases 0-6)

**Never submit.** Neutral ledger. This pass ran the harness pipeline end to end
with blind predictions written from specs BEFORE any implementation body was
read. A keep is not a finding. State: `.apex/` (phases 0-6 all green).

## Method

- 13 flows mapped, 11 tagged CRITICAL (F01 settle, F02 fallbackExit,
  F03 targeted settle, F04 vault deposit/withdraw, F05 borrow,
  F06 collateral withdrawal, F07 liquidation, F08 exit-book fill,
  F09 guardian signals, F10 freeze/pause, F11 accrual).
- 11 blind predictions recorded (`.apex/predictions/F01..F11-prediction.md`),
  each with provenance (specs/API only), >=2 surprises, boundary semantics.
- Implementation bodies read AFTER predictions: core settle/liquidate,
  controller supplyCollateral/withdrawCollateral/borrow/repay hooks,
  CollateralActivationLib credit/debit, LidoLendERC4626
  (totalAssets/_deposit/_withdraw/settle/fallbackExit), LidoLendVaultAdapter,
  ExitBookBase.fillExitRequest.
- 14-row assumption inventory (5 OPEN -> all dispositioned below).
- 4 executed probes (E-1..E-4, `.apex/experiments/E1-4-onchain-probes.log`).

## Gate ledger

| Gate | Result |
|---|---|
| 1 divergence | 8 prediction diffs recorded: all `design-choice` — bodies match specs incl. rounding directions, hook-before-write ordering, freeze/pause tables, managed-share accounting |
| 2 hypothesis | 413 hypothesis rows seeded (family templates + lens rows H-0211..H-0214); 4 lens hypotheses carried to kill-pass |
| 3 experiment | 4 executed read-only probes on pinned deployed bytecode (no txs needed: no surviving hypothesis crossed the tx bar) |
| 4 validate | 4/4 disproved with cited evidence; citations 152/152 resolve; coverage 13/13 flows, fail-closed lifted |

## Candidate dispositions (this pass)

| Candidate | Verdict | Evidence |
|---|---|---|
| minExitAssets over-counts payout (pass-1 keep L-P1-001 re-check) | KILL | adapter floor sums loanAssets + UP-rounded debtCanceled (LidoLendVaultAdapter.sol:63) vs DOWN-priced collateral (LidoLend.sol:476); per-cut gap < 1 loan wei + < 1 collateral-unit truncation (~1.25 wei WETH at observed price 1.2503e36); 50-iteration worst case ~110 wei WETH; floor semantics documented in bundling guide |
| Guardian identity / role-without-grant (incl. delegate races, init race) | KILL | `_isSenderAuthorized` guards every report; setDelegate rejects guardians + in-use delegates; all 6 proxy admin slots = DAO Agent [OBSERVED]; quorum=1 committee is the documented accepted trust |
| tSA < tBA reachable -> borrow-brick (overshoot chain) | KILL | gap invariant g >= 0: frontier settle decrements g by exactly 1 and reverts at g==0 (LidoLend.sol:500 has no zeroFloorSub); write-off capped by tBA (L:588-591) |
| Activation-lock refresh griefing (attacker top-up resets lot start) | KILL | CollateralActivationLib.sol:240-243 resets start on later-deadline top-up, but the donated collateral becomes the victim's property — attacker loses principal per refresh; self-funding-negative griefing, partial docs coverage (dust note M4) |
| Settlement root bad-debt hole (S1 warning), LIF-blind gate (S2) | KILL (documented) | both are documented warnings with required preconditions (exact riskKey tie + personal opt-in + full-collateral partial cut); dedupe per program rules |
| Exit Book debit-before-withdraw (pass-1 keep L-P1-002 re-check) | KILL | balance-delta == F check (ExitBookBase.sol:279) reverts on any mismatch, undoing the debit; both books unused (no live market) |
| Oracle same-tx asymmetry (A2) | KILL | deployed WstEthRateOracle is a stateless rate read: price() = 1.2503e36 [OBSERVED]; core and controller reads identical |
| CircuitBreaker freeze >= 24h path | KILL | bounds [432000s, 5184000s] [OBSERVED]; pause needs a live registration (consumed per use) + trusted ADMIN; no unprivileged path |

## Verified count

**0.** No `FINDING-*.md` written (verified-only rule). Consistent with the
campaign's pass 1-6 outcome; this pass adds the blind-prediction evidence
layer and closes the four lens hypotheses with executed probes.

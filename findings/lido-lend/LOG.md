# Campaign log — Lido Lend (never submit)

Read-only audit campaign against pinned bytecode. One small command at a time.
Branch: `cursor/lido-lend-audit`. Harness: Money Hunter pipeline, policy `standard`.

## 2026-11-27 — Phase 0 Ground complete

- PIN: `findings/lido-lend/PIN.md` (prior session) — bytecode keccak table at
  mainnet block 26508283; release/audit/deploy SHAs for lend, lend-irm,
  lend-markets, lend-guardian-daemon; Easy Track + Circuit Breaker + Bundler3
  pins; OOS list. Do not hunt develop HEAD (`lend-markets cfc464c`).
- Repos aligned to pins: `lend` @ 4d55f1d (v1.0.0), `lend-irm` @ 97af4c3 (v1.0.1),
  `lend-markets` detached @ 9c0ba34 (deploy pin; audit commit 23416c43 fetched),
  `lend-guardian-daemon` @ 846f197 (v1.0.0, src/ only).
- `.apex/00_ground_zero.json`: scope (evm profile, 24 addresses + 4 repos +
  web endpoint), 8 invariants, boundaries (never submit; no mainnet txs; fork
  of deployed bytecode only; no secrets in output), environment ready
  (forge/cast/anvil 1.3.5/1.6.0, rpc.mevblocker.io at 0x1947c0f).
- Impact ladder (Immunefi, as briefed): Crit = theft of user funds (excl.
  unclaimed yield), permanent freeze, insolvency, theft/freeze of protocol
  fees; High = theft/freeze of unclaimed yield, temp freeze >=24h, guardian
  key extraction, role acquisition without grant; Med = block stuffing,
  griefing; Low = fails promised returns, no value loss.

## 2026-11-27 — Phase 1 Research complete

- Docs deep-dive before code: core spec, architecture, market-controller, lender-settlement, guardian-signals, roles, exit-books, IRM spec, bundler guide. Claims + ambiguity list in findings/lido-lend/DOCS.md.
- Audits indexed (dedupe set): Cyfrin 62 (0c/0h) at pinned commits; MixBytes guardian; CB audits; Easy Track 11 low. findings/lido-lend/AUDITS.md.
- Intel: corpus has no Lido-Lend rows; 6 mandatory family cards present; frontier: no public contest results; 2026 lending-hack median $756k.

## 2026-11-27 — Phase 2 Model complete

- 13 flows mapped (11 CRITICAL: F01 settle, F02 fallbackExit, F03 targeted settle, F04 vault deposit/withdraw, F05 borrow, F06 collateral withdrawal, F07 liquidation, F08 exit book fill, F09 guardian signals, F10 freeze/pause, F11 accrual), 14 falsifiable invariants (INV-C1..C14), all in .apex/02_mental_model.json.
- Blind predictions recorded for all 11 CRITICAL flows (.apex/predictions/F01..F11-prediction.md), each with PROVENANCE (specs/API only, no .sol bodies read), >=2 surprises, boundary semantics. Skeletons: signature-only extraction.
- ISS rows (matcher zero-hit, predictions cited API-level docs instead): F03, F04, F05, F06, F11 — flow-name keyword did not match; surfaces exist (vault settleTargets, deposit/redeem, borrow, withdrawCollateral, borrowRate); matcher limitation noted, not bypassed: no unrelated files substituted.
- Strict-mode extras (vocab/sinks tables) not required under standard policy.

## 2026-11-27 — Pass 7 (harness pipeline) complete

- Phases 0-6 green: 13 flows (11 critical), 11 blind predictions (specs-only provenance), 8 prediction diffs (all design-choice/match), 14 assumptions (all dispositioned), 413 hypotheses seeded, 4 executed onchain probes (E1-E4), 4/4 lens hypotheses disproved, citations 152/152, coverage 13/13 flows (fail-closed lifted), report regenerated (0 verified).
- Body-level re-checks of pass-1 keeps L-P1-001/L-P1-002: both kills confirmed with wei-level sizing.
- ARTIFACT CORRECTION: stale line refs LidoLendVaultAdapter.sol:87-88 corrected to :63 in .apex state (factual typo fix; real floor-sum line is 63).
- findings/lido-lend/PASS-7.md + corpus-update.md recorded. Verified count remains 0.

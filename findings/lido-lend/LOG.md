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

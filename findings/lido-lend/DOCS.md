# Docs intent digest — claims, guarantees, ambiguities

Sources: docs.lido.fi/lend (intro page, 2026-11-27), repo specs at deploy pins
(core SPECIFICATION, architecture, market-controller, lender-settlement,
guardian-signals, roles, exit-books, IRM SPECIFICATION, bundler.md).
Read BEFORE implementation source (Phase 1 rule). Line refs are to the pinned
spec files under `targets/lido-lend/`.

## Stated guarantees / always-never claims

Core (`lend/SPECIFICATION.md`):
- C1 Rounding law: "Credits and outputs generally round down; required inputs,
  debits, and share burns generally round up" (L40). settle: borrowAssetsCanceled
  UP, supplySharesBurned UP, seizedAssets DOWN; borrower keeps the <1-unit
  collateral fraction which "may be worth more than one raw loan-token unit"
  (L159) — documented rounding.
- C2 One-unit borrow-asset overshoot: settle can push totalBorrowAssets floor to 0
  while subtracting the full amount from totalSupplyAssets — free liquidity
  falls by 1 raw loan unit (L165, documented).
- C3 settle: no health check, no LIF, borrower approval not required, receiver
  arbitrary non-zero, seizedAssets must be non-zero (L112-136).
- C4 Hook lock is one GLOBAL transient: nested hooked action reverts even across
  markets; flashLoan and authorization functions bypass hooks entirely (L80).
- C5 initialize has no caller restriction (L203, documented warning); deployed
  proxies initialize atomically.
- C6 setFee accrues with the OLD fee and dispatches no AccrueInterest hook; fee
  shares mint with no Supply hook (L99). MAX_FEE 25%.
- C7 Operator authorization is core-global across markets and includes settle
  (L52). Market creation owner-only; controller and settlement immutable
  post-creation (L63-74).

Controller (`market-controller.md`):
- M1 Supply cap is admission-only: "Interest may carry the total above the cap"
  (L37). Withdrawals never blocked by cap.
- M2 Borrow capacity excludes inactive collateral: capacity =
  floor(activeCollateral * LLTV) vs ceil(debt); withdrawal with debt must keep
  debtAssets <= borrowCapacity (L43-55).
- M3 Post-borrow rounding may use inactive collateral; for borrow-in-assets
  "there is no unconditional one-unit bound" (L64-66) — documented.
- M4 Dust: any third party can donate sub-threshold collateral to a victim and
  force resolution semantics on the victim's next supply (L107-110, documented
  griefing with stated mitigations).
- M5 Instant activation keyed by SENDER not owner; "a permissionless helper
  would let any user bypass activation" (L116) — trusted-caller responsibility.
- M6 Withdrawal: inactive balance leaves all-or-nothing; lock window admits
  active-balance draws only; debt-free borrower bypasses health check (L171-176).
- M7 Forced reductions (liquidate/settle) skip maturation and the lock, consume
  active->dust->activating (L178).
- M8 Freeze blocks borrow, debt-bearing collateral withdrawal, maturation;
  permits repay/liquidate/settle/lender withdrawal (L186-191). Pause blocks
  every hook incl. repay/liquidate/settle/accrueInterest (L189). Pause "finite
  pause expires automatically"; indefinite pause needs authorized resume (L195).
- M9 Borrow-share-rate guard: (shares+1e6) <= 1e7*(assets+1) must hold after
  every borrow; repay/settle may not create a NEW breach (may worsen existing);
  liquidate exempt; if accrual leaves market above ceiling every borrow reverts
  (L199-216).

GuardianSignals (`guardian-signals.md`):
- G1 flag->strike->quorum ban; derived vs latched; unflag latches before
  removing; permissionless prune only removes departed-guardian signals and
  never clears a latch (L57-71, L141).
- G2 Ban blocks borrowing + maturation ONLY; never repayment, liquidation,
  settlement, or debt-free withdrawal (L43).
- G3 Heartbeat: blockhash proof within 256-block window; timestamp monotonic
  per guardian; stored frontier never moves backward; syncQuorumFrontier
  permissionless, raises only (L173-186).
- G4 ACCEPTED: guardian-supplied timestamp is not checked against the block
  header (L195, documented accepted risk). 32-guardian cap does not bound
  historical signal sets; unpruned history can push prune/unban/suspect over
  block gas (L146, documented warning).
- G5 Delegate uniqueness: one address cannot represent two identities (L51).

Settlement policy (`lender-settlement.md`):
- S1 Queue riskKey = borrowShares*1e18/rawCollateral, floor-rounded; ties are
  NOT ordered by exact LTV (L51). DOCUMENTED WARNING: rounded root check can
  miss an insolvent non-root borrower (needs exact tie + personal opt-in +
  partial cut taking all collateral while leaving debt) — "expected to be
  extremely rare, although the contracts allow it" (L56-62).
- S2 DOCUMENTED WARNING: bad-debt gate is root-only and LIF-blind; 1/LIF < LTV
  <= 100% passes settlement while liquidation would write off debt (L65-67).
- S3 Personal allowance: (debt*1e18 - target*collValue)/(1e18-target), floor;
  all raw collateral counts even if inactive (L83). Canceled debt can exceed
  asset allowance by ceil((totalBorrowAssets+1)/(totalBorrowShares+1e6))
  (L140-145, documented).
- S4 Root policy: allowance = max(debt fraction, absolute floor, LTV step);
  fullCutBelowCollateral promotion; settleable supply T = supplier value minus
  free liquidity; execution-rule table (L95-217).
- S5 Vault managed-shares invariant: managedSupplyShares <= actual core supply
  shares; external share credits and direct token donations are NOT counted as
  backing and are not claimable (L221-223).
- S6 Fallback exit: liquid leg floor-rounds the share fit ("may redeem slightly
  more shares than maxRedeem", L266); seizure-floor head-of-line stop is
  documented (L283); default 50 iterations; partial progress is kept; burning
  all vault shares can leave residual managed supply + residual debt (L292).
- S7 Quotes are snapshot reads; vault consumes immediately (L178).

Exit Books (`exit-books.md`):
- E1 Placement snapshot is NOT a reservation; same position backs several
  requests (L74).
- E2 Fill order: validate -> debit -> source withdraw -> balance delta == F ->
  split (L129-137). DOCUMENTED WARNING: per-fill share-burn limit is per-fill;
  n fills can burn up to M+n-1 total (L114).
- E3 Fee ramp <= 10%; service cut <= 25% of priority fee; receiver gets
  F - priorityFee (L78, L162-171).
- E4 Allowlist is the trust boundary: source must report true burns, exact
  transfers, no callbacks into the book, stable vault asset (L279-287).
- E5 Pause blocks placement+fills only; no auto-expiry; RESUMER initially
  unassigned (L277).

IRM (`lend-irm/SPECIFICATION.md`):
- I1 Router calls implementation via external call, no reentrancy lock; a
  reentrant implementation can make "the same interval accrue more than once"
  (L131, documented — route only reviewed code).
- I2 applyIrmConfig does not accrue: parameter changes reprice unaccrued time
  (L200, documented).
- I3 Mutable adaptive config is live-read every pricing call; band mutation
  bypasses the stored-rate clamp (L214, documented trusted).
- I4 A failing ACTIVE route blocks migration because accrual runs first
  (L178, documented).
- I5 Adaptive borrowRate accepts only ROUTER; borrowRateView is ungated;
  utilization U > WAD is not clamped (documented: protocol-reachable B <= S).
- I6 During live setMarketIrm, controller may veto accrual hook -> migration
  blocked while paused (L171).

Bundler (`bundler.md`):
- B1 Adapters are stateless conduits; tokens left on an adapter at tx end are
  claimable by the next bundle (documented rule 4).
- B2 fallbackExit minExitAssets is ONE floor over loanAssets + debtCanceled;
  "it does not matter how the payout splits" (L275-287). NOTE: debtCanceled is
  the up-rounded leg; seized collateral is the down-priced leg — the floor can
  sit slightly ABOVE receiver value (pass-1 keep L-P1-001).
- B3 Adapters act for the bundle initiator; approvals to adapters, never to
  Bundler3 (L49-53, L101).

## Ambiguity / silence list (what docs do NOT specify)

- A1 No doc bounds the loan-value gap between minExitAssets (which counts
  up-rounded debtCanceled) and the down-priced collateral actually delivered,
  except the core rounding table. Size needed (pass-1 keep).
- A2 Controller settle hook: "Its decision assumes that these reads, and any
  earlier vault quote in the same transaction, return the same price" (S: L184).
  No statement of what breaks if the oracle is stateful/callcount-dependent.
- A3 No doc states whether accrual during a controller PAUSE is skipped or
  forced to accrue the whole window at once AFTER the pause (M8 says a later
  successful accrual covers the time since lastUpdate) — burst accrual size
  unbounded by docs beyond IRM maxima.
- A4 Exit Book: no statement about fill at the exact deadline second vs after
  (E: L72 says fill allowed at deadline).
- A5 GuardianSignals prune requires off-chain identification of affected pairs;
  no onchain enumeration (documented).
- A6 Vault: no doc for what happens to vault value if the core position incurs
  bad debt via liquidation write-off — implied pro-rata share price drop;
  no explicit statement. (Vault deposits inherit core lender losses.)
- A7 Docs do not state a maximum for maxIterations in fallbackExit other than
  "nothing clamps the value it passes" (gas-bound only).
- A8 Roles: no statement that CircuitBreaker pause duration bounds are checked
  onchain vs off-chain ("immutable bounds" — verify onchain).
- A9 WstEthRateOracle semantics documented only in a 43-line API stub; scale
  and staleness assumptions unstated in specs read so far.

## Docs-vs-brief severity hooks

- Freeze >=24h = High only if attacker-inducible and undocumented; M8 states
  freeze is governance-tightening only (steward C3). Pause via CircuitBreaker
  consumes a registration; duration bounds onchain (A8).
- Role acquisition without grant = High: watch delegate uniqueness (G5),
  instant-activation sender-keying (M5), RiskStewardDashboard steward
  administration (STEWARD_ADMIN_ROLE = EVMScriptExecutor), and any
  initializer/front-running on factory-deployed proxies.

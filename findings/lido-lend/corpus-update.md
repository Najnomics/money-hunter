# What this hunt taught (campaign techniques for the corpus)

Campaign: Lido Lend (Morpho Blue fork + Lido policy layer), bytecode-pin
audit, 2026-11-27. Verified: 0 across 7 SC passes + web.

Technique rows worth carrying upstream:

1. **Predict-then-diff on a fork delta.** Writing 11 blind predictions from
   the specs (with per-flow surprise lists) before reading bodies caught every
   intentional delta (settle rounding directions, hook-before-write, managed
   ERC-4626 accounting) and made the residual candidate set tiny and
   falsifiable: the diff table collapsed in one read session.
2. **Sizing kills rounding-flavored keeps.** Two pass-1 keeps (adapter floor
   over-counts payout; exit-book debit ordering) died not by argument but by
   wei-level sizing against the observed oracle price (1.2503e36): worst cases
   ~110 wei and fail-closed revert. Rounding candidates deserve an explicit
   wei-budget line before promotion.
3. **Self-funding-negative griefing test.** The permissionless
   supplyCollateral(onBehalf) + top-up deadline-reset looks like an indefinite
   partial-withdrawal lock; it dies because the donated collateral becomes the
   victim's property. Rule: for every griefing candidate, price the attacker's
   irreversible cost against the victim's delay.
4. **Gap invariant argument for overshoot chains.** Repeated
   settle/repay floor-to-0 overshoots cannot push totalSupplyAssets below
   totalBorrowAssets: each frontier settle decrements (tSA - tBA) by exactly 1
   and the subtraction at L500 reverts at g==0 before negative is reachable.
   Worth reusing on any Morpho-derivative with a settle-like primitive.
5. **Onchain config reads as cheap kills.** Six cast probes (proxy admin
   slots, CircuitBreaker bounds/admin, oracle price, GuardianSignals
   committee/quorum/frontier) closed four OPEN assumptions with [OBSERVED]
   evidence in one command batch. Registries/params first, PoC later.
6. **Harness friction worth remembering:** the AST flow mapper needs
   surface-name entries (prose entries fail silently as unmapped_critical and
   coverage fail-closes); prediction_diff overwrites a single slot (diffs are
   records, not auto-comparisons); assumptions merge rejects duplicate ids.

## Mirror status

Rows 1-6 queued for upstream `Najnomics/bugbounty-intel`
(`harness/apex-campaign-findings.jsonl` push deferred to the intel sync step;
offline-safe queue recorded here in-session).

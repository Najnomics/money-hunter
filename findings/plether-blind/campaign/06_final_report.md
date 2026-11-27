# Plether Perps blind campaign (apex-core + boss-skill)

Generated: 2026-11-27T09:01:51+00:00  
TargetProfile: `evm`  
Workspace: `/agent/repos/audit-comp-plether`

## The mirror

- **Earned:** Scope, pin, phases 0-6 artifacts, two live code leads (L-CH-001/002) with Gate 4 needs-evidence, hunter kill log, Slither dump outside pipeline.
- **Faked:** No executed PoC. Specialist lenses bound to constructors due to AST entry matching. Slither sweep admitted 0 detectors. AST mapped 0 of 8 critical flows.
- **Next run:** Fix AST last-token matching and Slither 2MB/rc255 so Phase 3 recall is nonzero, then execute queued PoCs.
- **Brag or regret:** Pipeline completed as designed and produced 0 verified findings. That is the honest outcome of Gate 3 with execute=false plus Gate 4 unknown checks.

## Executive summary

- 68 model/code divergence(s) mapped.
- 4 divergence-anchored hypothesis(es) generated.
- 4 experiment(s) recorded.
- **0 verified finding(s)** with executed evidence.
- 4 surviving candidate(s) awaiting executed evidence.
- 0 hypothesis(es) disproved by adversarial checks.
- 5 assumption row(s); 0 composed chain(s).
- Coverage: 57% of modelled flows (8/14), confidence `pattern`.

> No finding is reported as verified. Candidates below are **not** findings until an 
> executed experiment in `.apex/experiments/` confirms the prediction.

## Finding reports

Folder: `.apex/reports` — index: `reports/index.md`

- [liquidation reachableCollateral preview includes VPI rebate reserve](reports/candidates/H-0003.md) — Candidate — not verified, severity `low`
- [Opaque logic in `executeClose sidecar opaque settlement` may mutate state that the Phase 2 model does not account for, c](reports/candidates/H-0004.md) — Candidate — not verified, severity `unclassified`
- [degradedMode freezes surplus free-settlement withdrawal for healthy open positions](reports/candidates/H-0001.md) — Candidate — not verified, severity `medium`
- [Input/external-call handling at packages/perps/src/CfdEngine.sol:76 crosses the trust boundary `untrusted-keeper, peer-t](reports/candidates/H-0002.md) — Candidate — not verified, severity `unclassified`

## Scope & guardrails

Allowlist: `packages/perps/src`

Hard rules:
- A tool may not run until its phase gate is complete.
- Every finding must cite file:line or a captured experiment log.
- Unlabeled claims are not findings; use [FACT]/[CODE]/[OBSERVED]/[FUZZED].
- Non-destructive mode is ON: no writes to the target.

## Intended behaviour (Phase 1)

Read 14 doc source(s); extracted 723 stated claims, 16 ambiguity/silence markers, 0 API schema(s).

Stated claims sampled from docs/policy:
- packages/perps/SECURITY.md:21: - exact-shape failure classification: only known typed policy failures are terminal, while unknown, panic,
- packages/perps/SECURITY.md:23: - exact symmetric LP NAV that counts only account-capped collectible marked losses as receivables and never as
- packages/perps/SECURITY.md:39: 2. Does value cross only the intended custody boundaries, with each reserve used for its permitted obligation?
- packages/perps/SECURITY.md:43: affected terminal curve? Credit-only free-settlement funding changes none of those inputs.
- packages/perps/SECURITY.md:68: - `OrderRouter`'s configured `PletherOracle` address can be rotated only through `OrderRouterAdmin`'s 72-hour timelocked oracle config flow. Feed ids, basket weights, base prices, inversion flags, and the Pyth endpoint are fixed on each `PletherOracle` instance, so changing them requires deploying a
- packages/perps/SECURITY.md:75: Both admins expose `activeConfigVersion`, initialized to one. `CfdEngineAdmin` increments it only after successful
- packages/perps/SECURITY.md:76: risk, calendar, or freshness finalization; `OrderRouterAdmin` increments it only after successful Router or Oracle
- packages/perps/SECURITY.md:79: `CfdEngine` dependencies (`CfdEnginePlanner`, `CfdEngineSettlementSidecar`, `CfdEngineAdmin`) are deployed separately and wired once via `setDependencies(...)`. That wiring is owner-only and one-time. The engine rejects a settlement sidecar or admin bound to another engine and rejects a no-code admi
- packages/perps/SECURITY.md:83: The reader accepts planning calls only from that Engine and uses its configured planner and settlement sidecar.
- packages/perps/SECURITY.md:84: Its entrypoints are read-only: it has no owner, upgrade path, or settlement authority. Moving snapshot encoding into
- packages/perps/SECURITY.md:86: checks must cover both contracts' EIP-170 runtime sizes and the Engine's EIP-3860 creation-input size.
- packages/perps/SECURITY.md:89: The Engine accepts only an empty book immutably bound to itself with matching `CAP_PRICE` and the canonical `1e20`
- packages/perps/SECURITY.md:100: | `maxSeniorExposureAssets`, `maxSeniorShareBps` | `HousePool` | `onlyOwner`, 72-hour timelock; finalized values must be finite and below 100%, respectively |
- packages/perps/SECURITY.md:101: | Junior `maintenanceFeeAprBps`, `maintenanceFeeRecipient` | `TrancheVault` | current `HousePool.owner()` only, 72-hour timelock; fee is capped at `10,000` bps (100%) nominal APR |
- packages/perps/SECURITY.md:123: While a lock is active, the engine owner may call `proposeProtocolTreasury(address,uint256)` to queue or replace a
- packages/perps/SECURITY.md:134: returns the address, activation time, and successor lock expiry only while the proposal is pending, then returns zeros.
- packages/perps/SECURITY.md:146: affects future protocol credits only. Existing balances remain with their original clearinghouse accounts, and normal
- packages/perps/SECURITY.md:152: monitors must resolve the effective getters. Existing non-upgradeable deployments cannot acquire this protection
- packages/perps/SECURITY.md:157: `CfdEngine.recapitalizePool(amountAssets)` is an immediate, owner-only, non-reentrant recovery action.
- packages/perps/SECURITY.md:163: `CfdEngineAdmin` retains its configuration-only role.

## Model & invariants (Phase 2)

| Flow | Entry | Critical | Value sinks | Trust boundaries |
|---|---|---|---|---|
| F-DEPOSIT-MARGIN | MarginClearinghouse.depositMargin(uint256) | no | SINK-TRADER-CUSTODY | ERC20-pull |
| F-DEPOSIT-FOR | MarginClearinghouse.depositFor(address,uint256) | yes | SINK-TRADER-CUSTODY | untrusted-payer, bridge-destination |
| F-WITHDRAW | MarginClearinghouse.withdrawMargin(uint256) | yes | SINK-TRADER-THEFT | owner-only |
| F-ADD-MARGIN | CfdEngine.addMargin(address,uint256) | no | SINK-TRADER-CUSTODY | owner-only |
| F-COMMIT-ORDER | OrderRouter.commitOrder(OrderV3Types.OrderRequest) | yes | SINK-RESERVATION | untrusted-trader-input, config-hash |
| F-EXECUTE-ORDER | OrderRouter.executeOrder(uint64,bytes[]) | yes | SINK-POOL-INSOLVENCY, SINK-TRADER-THEFT | untrusted-keeper, pyth-oracle, fifo |
| F-EXPIRE-ORDER | OrderRouter.expireOrder(uint64) | no | SINK-RESERVATION | untrusted-keeper |
| F-LIQUIDATE | OrderRouter.executeLiquidation(address,bytes[]) | yes | SINK-POOL-INSOLVENCY, SINK-TRADER-THEFT | untrusted-keeper, pyth-oracle |
| F-PROTECT-TRIGGER | PositionProtectionBook.triggerPositionProtection(uint64,bytes[]) | yes | SINK-TRADER-THEFT, SINK-FREEZE | untrusted-keeper, pyth-oracle |
| F-LP-SETTLE | HousePool.settleLpEpoch(uint256,uint256) | yes | SINK-LP-THEFT, SINK-POOL-INSOLVENCY | untrusted-keeper, pyth-oracle, senior-priority |
| F-LP-DEPOSIT | TrancheVault.requestDeposit(uint256,address,address) | no | SINK-LP-THEFT | controller-receiver |
| F-LP-REDEEM | TrancheVault.requestRedeem(uint256,address,address) | yes | SINK-LP-THEFT, SINK-FREEZE | controller-receiver, junior-covenant |
| F-CLAIM | CfdEngine.settleTraderClaim(address) | no | SINK-TRADER-CUSTODY, SINK-POOL-INSOLVENCY | owner-only, all-claims-cover |
| F-GUARDIAN | EmergencyPauseCoordinator.triggerFullContainment(bytes32,bytes32) | no | SINK-FREEZE | guardian-trusted-except-legit-action-bugs |

| Invariant | Statement | Class | Applies to |
|---|---|---|---|
| INV-SOLVENCY | Every risk-increasing open/increase leaves post-op E >= L + B with E=max(P-C,0), L=max(globalLongMaxProfit, globalShortMaxProfit), B=ceil(L*settlementBufferBps/10000). | economic | F-COMMIT-ORDER, F-EXECUTE-ORDER |
| INV-DEGRADED | If a close or liquidation leaves raw post-op E < L, degradedMode latches and blocks further risk expansion while still permitting protective transitions. | state | F-EXECUTE-ORDER, F-LIQUIDATE |
| INV-SENIOR-FIRST | A settlement cannot fund Junior redemptions while any eligible matured Senior demand remains unaccounted for. | economic | F-LP-SETTLE, F-LP-REDEEM |
| INV-FUNDED-ESCROW | Every claimable LP asset is held one-for-one in vault escrow and cannot be reused by HousePool. | math | F-LP-SETTLE, F-LP-REDEEM |
| INV-CLAIM-SENIOR | Trader claim balances remain a senior claim on pool liquidity until serviced; keeper bounties are not pool liabilities. | economic | F-CLAIM, F-EXECUTE-ORDER, F-LP-SETTLE |
| INV-ONE-POSITION | An account address holds at most one live directional position at a time. | state | F-COMMIT-ORDER, F-EXECUTE-ORDER |
| INV-MARGIN-SUM | sides[LONG].totalMargin + sides[SHORT].totalMargin equals the sum of pos.margin across all live positions. | math | F-EXECUTE-ORDER, F-ADD-MARGIN, F-LIQUIDATE |
| INV-FROZEN-SPREAD | For a valid frozen voluntary close, assessed spread equals LP-paid plus terminally waived spread; none is credited to protocol treasury. | math | F-EXECUTE-ORDER |
| INV-FIFO | Price-dependent execution starts from the current global queue head; oracle-free invalid-order cleanup may remove a specific order without executing later valid orders. | state | F-EXECUTE-ORDER, F-EXPIRE-ORDER |
| INV-IDEMPOTENCY | (account, clientOrderId) is bound forever to one full intent hash; exact replay returns the original id before current-state validation; conflicting reuse reverts. | authorization | F-COMMIT-ORDER |
| INV-NO-CANCEL | Users cannot cancel queued orders once committed. | state | F-COMMIT-ORDER |
| INV-RETRYABLE | Unknown selectors, panic, out-of-gas, empty or malformed revert data never become guessed terminal policy failures. | state | F-EXECUTE-ORDER |
| INV-ZERO-CLOSE-BOUNTY | Ordinary and protection close attempts create authenticated Active Order records with zero amount; nonzero close-bounty configuration is rejected. | economic | F-COMMIT-ORDER, F-PROTECT-TRIGGER |
| INV-CANONICAL-ASSETS | Pool depth is min(rawAssets, accountedAssets), not raw token balance alone. Unsolicited raw pool cash is not LP NAV until admitted. | math | F-LP-SETTLE, F-EXECUTE-ORDER |
| INV-CREDIT-ONLY | depositFor exact token receipt increases beneficiary settlement only; no Engine hook, carry checkpoint, reserve allocation, or payer authority. | authorization | F-DEPOSIT-FOR |
| INV-WITHDRAW-FIREWALL | Synchronized LP redemption funding is limited to conservative free cash after a base reserve of C+L+B plus pool-level reservations. | economic | F-LP-SETTLE, F-LP-REDEEM |
| INV-KEEPER-UNTRUSTED | Any caller acting as keeper is in-scope; on-chain checks must prevent theft or insolvency from a hostile execute/trigger/settle call. | authorization | F-EXECUTE-ORDER, F-LIQUIDATE, F-PROTECT-TRIGGER, F-LP-SETTLE |
| INV-SHARE-ESCROW | Routed deposit-to-redeem decreases depositClaimEscrowShares and increases pendingRedeemEscrowShares equally without a token transfer. | math | F-LP-REDEEM |

## Divergences (Phase 3)

| ID | Kind | Flow | Expected | Observed | Location | Confidence |
|---|---|---|---|---|---|---|
| DIV-0001 | unmapped_critical_flow | F-DEPOSIT-FOR | entrypoint `MarginClearinghouse.depositFor(address,uint256)` for critical flow Credit-only funding without authority | no matching implementation surface found |  | low |
| DIV-0002 | unmapped_critical_flow | F-WITHDRAW | entrypoint `MarginClearinghouse.withdrawMargin(uint256)` for critical flow Trader withdraws available USDG | no matching implementation surface found |  | low |
| DIV-0003 | unmapped_critical_flow | F-COMMIT-ORDER | entrypoint `OrderRouter.commitOrder(OrderV3Types.OrderRequest)` for critical flow Commit delayed order into global FIFO | no matching implementation surface found |  | low |
| DIV-0004 | unmapped_critical_flow | F-EXECUTE-ORDER | entrypoint `OrderRouter.executeOrder(uint64,bytes[])` for critical flow Keeper executes FIFO head with Pyth payload | no matching implementation surface found |  | low |
| DIV-0005 | unmapped_critical_flow | F-LIQUIDATE | entrypoint `OrderRouter.executeLiquidation(address,bytes[])` for critical flow Full liquidation of under-margined account | no matching implementation surface found |  | low |
| DIV-0006 | unmapped_critical_flow | F-PROTECT-TRIGGER | entrypoint `PositionProtectionBook.triggerPositionProtection(uint64,bytes[])` for critical flow Permissionless TP/SL trigger | no matching implementation surface found |  | low |
| DIV-0007 | unmapped_critical_flow | F-LP-SETTLE | entrypoint `HousePool.settleLpEpoch(uint256,uint256)` for critical flow Permissionless LP epoch settlement | no matching implementation surface found |  | low |
| DIV-0008 | unmapped_critical_flow | F-LP-REDEEM | entrypoint `TrancheVault.requestRedeem(uint256,address,address)` for critical flow Async LP redeem request and claim | no matching implementation surface found |  | low |
| DIV-0009 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementAsset` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:26 | low |
| DIV-0010 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementToken` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:32 | low |
| DIV-0011 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `onlySettlementSidecar` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:251 | low |
| DIV-0012 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `onlyAdmin` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:256 | low |
| DIV-0013 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `setDependencies` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:345 | low |
| DIV-0014 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `setPool` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:384 | low |
| DIV-0015 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `setTerminalNavBook` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:405 | low |
| DIV-0016 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `setOrderRouter` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:430 | low |
| DIV-0017 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `checkWithdraw` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:730 | low |
| DIV-0018 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `positionEntryCostAssetAtoms` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:941 | low |
| DIV-0019 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `liquidatePosition` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1010 | low |
| DIV-0020 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementApplyCarryAndMark` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1146 | low |
| DIV-0021 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementRealizeCarry` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1157 | low |
| DIV-0022 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementSyncTotalSideMargin` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1171 | low |
| DIV-0023 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementApplySideDelta` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1186 | low |
| DIV-0024 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementConsumeTraderClaim` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1215 | low |
| DIV-0025 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementRecordTraderClaim` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1229 | low |
| DIV-0026 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementWritePosition` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1244 | low |
| DIV-0027 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementDeletePosition` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1276 | low |
| DIV-0028 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `updateMarkPrice` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngine.sol:1468 | low |
| DIV-0029 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `admin` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineLens.sol:25 | low |
| DIV-0030 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `previewLiquidation` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineLens.sol:201 | low |
| DIV-0031 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `previewRouterLiquidation` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineLens.sol:209 | low |
| DIV-0032 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `simulateLiquidation` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineLens.sol:231 | low |
| DIV-0033 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `isLiquidatableAt` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineLens.sol:240 | low |
| DIV-0034 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `computeIndexedCarryAssets` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEnginePlanner.sol:53 | low |
| DIV-0035 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `isExactPriceRiskLiquidatable` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEnginePlanner.sol:61 | low |
| DIV-0036 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `planLiquidation` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEnginePlanner.sol:118 | low |
| DIV-0037 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementSidecar` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEnginePlanningReader.sol:12 | low |
| DIV-0038 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `planLiquidation` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEnginePlanningReader.sol:56 | low |
| DIV-0039 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `positionEntryCostAssetAtoms` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineSettlementSidecar.sol:41 | low |
| DIV-0040 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `sideBorrowBaseAssets` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineSettlementSidecar.sol:53 | low |
| DIV-0041 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `traderClaimBalanceAssets` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineSettlementSidecar.sol:75 | low |
| DIV-0042 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `unsettledCarryAssets` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineSettlementSidecar.sol:79 | low |
| DIV-0043 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `totalTraderClaimBalanceAssets` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineSettlementSidecar.sol:83 | low |
| DIV-0044 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementBufferBps` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineSettlementSidecar.sol:99 | low |
| DIV-0045 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `validateWithdraw` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineSettlementSidecar.sol:255 | low |
| DIV-0046 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `executeOpen` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineSettlementSidecar.sol:423 | low |
| DIV-0047 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `executeClose` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdEngineSettlementSidecar.sol:548 | low |
| DIV-0048 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `positionEntryCostAssetAtoms` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:36 | low |
| DIV-0049 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `sideBorrowBaseAssets` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:48 | low |
| DIV-0050 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `traderClaimBalanceAssets` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:74 | low |
| DIV-0051 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `unsettledCarryAssets` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:78 | low |
| DIV-0052 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `totalTraderClaimBalanceAssets` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:82 | low |
| DIV-0053 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `settlementBufferBps` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:89 | low |
| DIV-0054 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `setProtocolTreasury` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdTreasury.sol:124 | low |
| DIV-0055 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `setProtocolTreasury` (function) has a value-sink-shaped name but no model flow | packages/perps/src/CfdTreasury.sol:136 | low |
| DIV-0056 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `renounceOwnership` (function) has a value-sink-shaped name but no model flow | packages/perps/src/EmergencyPauseCoordinator.sol:102 | low |
| DIV-0057 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `setGuardian` (function) has a value-sink-shaped name but no model flow | packages/perps/src/EmergencyPauseCoordinator.sol:109 | low |
| DIV-0058 | undocumented_entrypoint |  | entrypoint is described by the Phase 2 flow inventory | surface `triggerEmergencyPause` (function) has a value-sink-shaped name but no model flow | packages/perps/src/EmergencyPauseCoordinator.sol:123 | low |
| DIV-0059 | prediction_model_wrong | F-DEPOSIT-FOR | AST mapper matches function name in flow.entry | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |  | high |
| DIV-0060 | prediction_model_wrong | F-WITHDRAW | AST mapper matches function name in flow.entry | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |  | high |
| DIV-0061 | prediction_model_wrong | F-COMMIT-ORDER | AST mapper matches function name in flow.entry | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |  | high |
| DIV-0062 | prediction_model_wrong | F-EXECUTE-ORDER | AST mapper matches function name in flow.entry | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |  | high |
| DIV-0063 | prediction_model_wrong | F-LIQUIDATE | AST mapper matches function name in flow.entry | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |  | high |
| DIV-0064 | prediction_model_wrong | F-PROTECT-TRIGGER | AST mapper matches function name in flow.entry | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |  | high |
| DIV-0065 | prediction_model_wrong | F-LP-SETTLE | AST mapper matches function name in flow.entry | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |  | high |
| DIV-0066 | prediction_model_wrong | F-LP-REDEEM | AST mapper matches function name in flow.entry | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |  | high |
| DIV-0067 | prediction_design_wrong | F-WITHDRAW | degradedMode latches to block further risk expansion while still permitting protective transitions including withdrawal of surplus free settlement for a healthy open position | validateWithdraw reverts CfdEngine__DegradedMode whenever pos.size != 0, freezing surplus free-settlement withdrawals until owner recapitalizes | packages/perps/src/CfdEngineSettlementSidecar.sol:274 | high |
| DIV-0068 | prediction_design_wrong | F-LIQUIDATE | liquidation reachable collateral used for seizure is pledge plus nettable claim, with VPI reserve only for matching clawback | planLiquidation sets settlementReachableAssets = margin + claim + vpiRebateReserve and CfdEngineLens publishes it as reachableCollateralAssets | packages/perps/src/libraries/CfdEnginePlanLib.sol:1453 | medium |

## Hypotheses & experiments (Phase 4–5)

| ID | Lens | Divergence | Hypothesis | Conf. | Severity / tier | Experiments |
|---|---|---|---|---|---|---|
| H-0003 | dimensional-analysis | DIV-0068 | Unit/scale handling near packages/perps/src/libraries/CfdEnginePlanLib.sol:21 may break the conservation property of SINK-POOL-INSOLVENCY: `///      settlement token uses 6 decimals, prices use 8 decimals, sizes/open interest use 18 decimals, raw entry notional uses`. | medium | low / theoretical | E-0002:prepared/pending; E-0004:ran/pending |
| H-0004 | reverse-engineering | DIV-0047 | Opaque logic in `executeClose sidecar opaque settlement` may mutate state that the Phase 2 model does not account for, changing stated invariant at the divergence site outside the documented flow. | medium | unclassified / candidate | none |
| H-0001 | state-machine | DIV-0067 | State handling at packages/perps/src/CfdEngineSettlementSidecar.sol:139 (`constructor(`) may desynchronize CfdEngine.degradedMode, MarginClearinghouse.freeSettlement from SINK-TRADER-THEFT under interleaved or replayed calls. | medium | medium / theoretical | E-0001:prepared/pending; E-0003:ran/pending |
| H-0002 | trust-boundary | DIV-0067 | Input/external-call handling at packages/perps/src/CfdEngine.sol:76 crosses the trust boundary `untrusted-keeper, peer-trader` and may let an untrusted actor influence SINK-TRADER-THEFT. | medium | unclassified / candidate | none |

## Adversarial filtering (Phase 6)

| ID | Hypothesis | Verdict | Blocking | Unknown | Rationale |
|---|---|---|---|---|---|
| DP-0001 | H-0001 | needs-evidence |  | environmental-precondition, system-constraint | Unresolved checks: environmental-precondition, system-constraint Notes: Code path exists: validateWithdraw reverts when degradedMode && pos.size != 0. Trigger is permissionless peer close that latches E<L. Without executed PoC we cannot confirm surplus exists after latch or that freeze meets contest |
| DP-0002 | H-0003 | needs-evidence |  | environmental-precondition, system-constraint | Unresolved checks: environmental-precondition, system-constraint Notes: Preview vs live reachableCollateral mismatch is in source. Contest impact (theft/insolvency) requires executed seizure using the inflated field. |

## Assumptions & chains (Phase 4)

| ID | Class | Assumption | Violator / primitive | Trusted actor | Status |
|---|---|---|---|---|---|
| A-001 | ORACLE_DATA | Pyth signed FX feeds are timely and correct; protocol only defends freshness/confidence/window policy. | Pyth publisher / compromised Hermes / false price within published confidence | no | OPEN |
| A-002 | ORDER_TIMING | Keepers will eventually execute or expire FIFO heads; unpaid close cleanup may stall. | no keeper / liveness omission | no | OPEN |
| A-003 | ACCOUNTING | Pool depth is min(rawAssets, accountedAssets); raw donations are not NAV. | token donor / direct USDG transfer to HousePool | no | OPEN |
| A-004 | TRUST | Owner/guardian will not act maliciously; legitimate documented actions that trigger user-harming bugs remain in scope. | owner following docs / clearDegradedMode / pause / recap | yes | OPEN |
| A-005 | ECONOMIC | degradedMode only blocks risk expansion, not surplus free-settlement withdrawal for healthy open positions. | peer profitable close that latches E<L / permissionless executeOrder/liquidation | no | OPEN |

No multi-step chains recorded.

## Coverage & remaining gaps (Phase 6)

**Covered:** 8/14 flows (57%); extractor confidence `pattern`.

| Gap | Type | Why it is open | Next phase | Next tool |
|---|---|---|---|---|
| GAP-SINK-SINK-TRADER-THEFT | sink | Sink SINK-TRADER-THEFT has no hypothesis or chain pointing at it. | 4 | assumption_inventory |
| GAP-SINK-SINK-TRADER-CUSTODY | sink | Sink SINK-TRADER-CUSTODY has no hypothesis or chain pointing at it. | 4 | assumption_inventory |
| GAP-SINK-SINK-POOL-INSOLVENCY | sink | Sink SINK-POOL-INSOLVENCY has no hypothesis or chain pointing at it. | 4 | assumption_inventory |
| GAP-SINK-SINK-LP-THEFT | sink | Sink SINK-LP-THEFT has no hypothesis or chain pointing at it. | 4 | assumption_inventory |
| GAP-SINK-SINK-RESERVATION | sink | Sink SINK-RESERVATION has no hypothesis or chain pointing at it. | 4 | assumption_inventory |
| GAP-SINK-SINK-FREEZE | sink | Sink SINK-FREEZE has no hypothesis or chain pointing at it. | 4 | assumption_inventory |
| GAP-HYP-H-0004 | hypothesis | Hypothesis H-0004 has no executed experiment. | 5 | invariant_tester |
| GAP-HYP-H-0002 | hypothesis | Hypothesis H-0002 has no executed experiment. | 5 | invariant_tester |
| GAP-FLOW-F-DEPOSIT-MARGIN | flow | Flow F-DEPOSIT-MARGIN (Trader deposits USDG into clearinghouse) has no mapped divergence yet. | 3 | ast_divergence_mapper |
| GAP-FLOW-F-ADD-MARGIN | flow | Flow F-ADD-MARGIN (Add isolated position margin) has no mapped divergence yet. | 3 | ast_divergence_mapper |
| GAP-FLOW-F-EXPIRE-ORDER | flow | Flow F-EXPIRE-ORDER (Oracle-free expiry cleanup) has no mapped divergence yet. | 3 | ast_divergence_mapper |
| GAP-FLOW-F-LP-DEPOSIT | flow | Flow F-LP-DEPOSIT (Async LP deposit request) has no mapped divergence yet. | 3 | ast_divergence_mapper |
| GAP-FLOW-F-CLAIM | flow | Flow F-CLAIM (Settle unpaid trader claim) has no mapped divergence yet. | 3 | ast_divergence_mapper |
| GAP-FLOW-F-GUARDIAN | flow | Flow F-GUARDIAN (Guardian containment actions) has no mapped divergence yet. | 3 | ast_divergence_mapper |
| GAP-SURFACE-4c8a44b9 | surface | Surface ENGINE at packages/perps/src/CfdEngine.sol:33 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-728fbce2 | surface | Surface _sideIndex at packages/perps/src/CfdEngine.sol:155 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-7819bfce | surface | Surface _sideState at packages/perps/src/CfdEngine.sol:161 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-1b2905c9 | surface | Surface _longAndShortStates at packages/perps/src/CfdEngine.sol:167 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-1a87eb3c | surface | Surface _requireTerminalNavBook at packages/perps/src/CfdEngine.sol:172 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-66e0e7a4 | surface | Surface _beginTerminalCurveMutation at packages/perps/src/CfdEngine.sol:181 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-18a62f60 | surface | Surface _endTerminalCurveMutation at packages/perps/src/CfdEngine.sol:192 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-eea36f1c | surface | Surface _checkpointBountyRecipient at packages/perps/src/CfdEngine.sol:203 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-d8a886b6 | surface | Surface _settleTraderClaimBalance at packages/perps/src/CfdEngine.sol:219 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-314821bd | surface | Surface _payTraderClaim at packages/perps/src/CfdEngine.sol:233 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-66ea2005 | surface | Surface onlyRouter at packages/perps/src/CfdEngine.sol:246 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-fee3a34f | surface | Surface _onlyRouter at packages/perps/src/CfdEngine.sol:261 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-ee5318de | surface | Surface _onlySettlementSidecar at packages/perps/src/CfdEngine.sol:267 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-1aeead34 | surface | Surface _onlyAdmin at packages/perps/src/CfdEngine.sol:273 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-89ade3fa | surface | Surface absorbReservedExecutionBounty at packages/perps/src/CfdEngine.sol:447 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-49ab0ab3 | surface | Surface creditBounty at packages/perps/src/CfdEngine.sol:471 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-43208d39 | surface | Surface addMargin at packages/perps/src/CfdEngine.sol:501 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-f576f6a8 | surface | Surface realizeCarryBeforeMarginChange at packages/perps/src/CfdEngine.sol:535 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-6068ae4e | surface | Surface settleTraderClaim at packages/perps/src/CfdEngine.sol:559 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-e9d1f5bb | surface | Surface reserveCloseOrderExecutionBounty at packages/perps/src/CfdEngine.sol:598 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-9f46a621 | surface | Surface recapitalizePool at packages/perps/src/CfdEngine.sol:632 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-e5b59c19 | surface | Surface clearDegradedMode at packages/perps/src/CfdEngine.sol:658 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-11d26e68 | surface | Surface applyRiskConfig at packages/perps/src/CfdEngine.sol:674 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-aecfad2d | surface | Surface applyCalendarConfig at packages/perps/src/CfdEngine.sol:689 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-0f4a7227 | surface | Surface applyFreshnessConfig at packages/perps/src/CfdEngine.sol:711 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-93fbddfa | surface | Surface processOrderTyped at packages/perps/src/CfdEngine.sol:762 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-0146e617 | surface | Surface _processOrder at packages/perps/src/CfdEngine.sol:771 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-11dceac6 | surface | Surface _syncTotalSideMargin at packages/perps/src/CfdEngine.sol:794 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-7db65474 | surface | Surface _positionBorrowBase at packages/perps/src/CfdEngine.sol:803 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-25cb7162 | surface | Surface _applySideBorrowBaseDelta at packages/perps/src/CfdEngine.sol:812 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-ff7201b9 | surface | Surface _syncPositionBorrowBase at packages/perps/src/CfdEngine.sol:821 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-9d872c07 | surface | Surface _syncPositionBorrowBaseToMargin at packages/perps/src/CfdEngine.sol:828 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-ca514534 | surface | Surface _payOrRecordTraderClaim at packages/perps/src/CfdEngine.sol:840 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-b634c50a | surface | Surface _canPayFreshPoolPayout at packages/perps/src/CfdEngine.sol:859 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-5d7874df | surface | Surface _availableCashForFreshPoolPayouts at packages/perps/src/CfdEngine.sol:865 is not mapped to any divergence. | 3 | ast_divergence_mapper |
| GAP-SURFACE-eddf40bc | surface | Surface isFadWindow at packages/perps/src/CfdEngine.sol:882 is not mapped to any divergence. | 3 | ast_divergence_mapper |

## Verified findings

No experimentally verified findings. Do not submit candidates as findings.

## Unverified candidates (theoretical)

### H-0003 — dimensional-analysis

Unit/scale handling near packages/perps/src/libraries/CfdEnginePlanLib.sol:21 may break the conservation property of SINK-POOL-INSOLVENCY: `///      settlement token uses 6 decimals, prices use 8 decimals, sizes/open interest use 18 decimals, raw entry notional uses`.

- Divergence: DIV-0068
- Prediction: In the local sandbox, drive the expression at packages/perps/src/libraries/CfdEnginePlanLib.sol:21 with minimum, maximum, and decimal-boundary inputs. If the invariant quantity remains conserved (no rounding loss, overflow, or scale mismatch), this hypothesis is false.
- Evidence: [DEDUCED] divergence DIV-0068: prediction_design_wrong; [CODE] packages/perps/src/libraries/CfdEnginePlanLib.sol:21 ///      settlement token uses 6 decimals, prices use 8 decimals, sizes/open interest use 18 decimals, raw entry notional uses; [CODE] packages/perps/src/libraries/CfdEnginePlanLib.sol:22 ///      26 decimals, ratios use 1e18 WAD, rates use a 10,000 basis-point denominator, and timestamps use Unix seconds.; [CODE] packages/perps/src/libraries/CfdEnginePlanLib.sol:248 /// @param longOi LONG open interest, with 18 decimals.; [CODE] packages/perps/src/libraries/CfdEnginePlanLib.sol:249 /// @param shortOi SHORT open interest, with 18 decimals.; [CODE] packages/perps/src/libraries/CfdEnginePlanLib.sol:250 /// @param price Price used to value both sides, with 8 decimals.; [CODE] packages/perps/src/libraries/CfdEnginePlanLib.sol:473 uint256 maxSkewAssets = Math.mulDiv(netDepthAssets, snap.riskParams.maxSkewRatio, CfdMath.WAD);

### H-0004 — reverse-engineering

Opaque logic in `executeClose sidecar opaque settlement` may mutate state that the Phase 2 model does not account for, changing stated invariant at the divergence site outside the documented flow.

- Divergence: DIV-0047
- Prediction: Recover the control flow around the artifact, enumerate every state write, and compare against the Phase 2 state vocabulary. If every write is already modelled, the hypothesis is false.
- Evidence: [DEDUCED] divergence DIV-0047: undocumented_entrypoint; [CODE] packages/perps/src/CfdEngineSettlementSidecar.sol:21 /// @dev Engine read surface used by account-action methods externalized from the bytecode-constrained host.; [CODE] packages/perps/src/CfdEngineSettlementSidecar.sol (text, 44567 bytes, sha256:5b9dd94454fdb8da):0 packages/perps/src/CfdEngineSettlementSidecar.sol (text, 44567 bytes, sha256:5b9dd94454fdb8da)

### H-0001 — state-machine

State handling at packages/perps/src/CfdEngineSettlementSidecar.sol:139 (`constructor(`) may desynchronize CfdEngine.degradedMode, MarginClearinghouse.freeSettlement from SINK-TRADER-THEFT under interleaved or replayed calls.

- Divergence: DIV-0067
- Prediction: Run two interleaved call sequences against the local sandbox that both touch packages/perps/src/CfdEngineSettlementSidecar.sol:139. If SINK-TRADER-THEFT and CfdEngine.degradedMode, MarginClearinghouse.freeSettlement stay consistent in every interleaving, the hypothesis is false.
- Evidence: [DEDUCED] divergence DIV-0067: prediction_design_wrong; [CODE] packages/perps/src/CfdEngineSettlementSidecar.sol:139 constructor(; [CODE] packages/perps/src/CfdEngineSettlementSidecar.sol:503 /// @dev Isolates position-write ABI encoding from the settlement frame for minimum-IR coverage compilation.; [CODE] packages/perps/src/CfdEngineSettlementSidecar.sol:658 emit FrozenCloseSpreadSettled(; [CODE] packages/perps/src/CfdEngineSettlementSidecar.sol:666 emit PriceLossWrittenOff(delta.account, delta.priceLossWrittenOffAssets);; [CODE] packages/perps/src/CfdEngineSettlementSidecar.sol:669 emit ActionRebateSettled(; [CODE] packages/perps/src/CfdEngineSettlementSidecar.sol:674 emit ActionChargeSettled(

### H-0002 — trust-boundary

Input/external-call handling at packages/perps/src/CfdEngine.sol:76 crosses the trust boundary `untrusted-keeper, peer-trader` and may let an untrusted actor influence SINK-TRADER-THEFT.

- Divergence: DIV-0067
- Prediction: From the untrusted side of `untrusted-keeper, peer-trader`, send the exact payload that reaches packages/perps/src/CfdEngine.sol:76. If the boundary rejects it or the effect on SINK-TRADER-THEFT is unchanged, the hypothesis is false.
- Evidence: [DEDUCED] divergence DIV-0067: prediction_design_wrong; [CODE] packages/perps/src/CfdEngine.sol:76 /// @notice Maximum supported oracle price, with 8 decimals; execution and mark-refresh inputs are capped here.; [CODE] packages/perps/src/CfdEngine.sol:109 /// @notice Oracle publish timestamp associated with `lastMarkPrice`, in Unix seconds.; [CODE] packages/perps/src/CfdEngine.sol:136 /// @notice Whether a Unix day number is configured as an all-day FAD and oracle-frozen override.; [CODE] packages/perps/src/CfdEngine.sol:139 /// @notice Maximum accepted mark age during an oracle-frozen window, in seconds.; [CODE] packages/perps/src/CfdEngine.sol:149 /// @notice Fixed LP-owned spread charged on voluntary oracle-frozen close/reduce notional, in basis points.; [CODE] packages/perps/src/CfdEngine.sol:284 /// @param _capPrice Nonzero maximum supported oracle price, with 8 decimals and no greater than `type(uint32).max`.

## Agent feedback & missing tools

| ID | Kind | Severity | Title | Requested change |
|---|---|---|---|---|
| ISS-0001 | missing_tool | blocker | Foundry, Slither, Semgrep, and intel corpus absent | Provision Foundry 1.5.1, slither, optional semgrep, and APEX_INTEL_CORPUS in the campaign environment image. |
| ISS-0002 | bug | high | Blind skeleton matching falls back to first 80 surfaces across all of src | Require exact/near-exact function-name match; never silently substitute the global surface list; exclude out-of-scope files; raise max_surfaces or page by file. |
| ISS-0003 | bug | blocker | targeted_static_sweep drops all Slither findings | Write analyser JSON to a file and parse the file. Treat slither rc 255 as ran. Stream/parse incrementally. Do not cap below typical slither JSON size. |

## What we did not conclude

- 4 surviving candidate(s) have no executed confirmation: H-0003, H-0004, H-0001, H-0002
- 50 coverage gap(s) remain open; see the coverage table.

## Evidence & limitations

Labels: `[FACT] [OBSERVED] [SEARCHED] [FUZZED] [CODE] [DEDUCED] [ASSUMED]`.
Unlabeled claims are not findings. A hypothesis without an executed experiment is a candidate.


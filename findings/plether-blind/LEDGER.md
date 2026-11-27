# Lead ledger — Plether blind run

Every lead this campaign generated or considered, including those killed at each of the four gates.
Nothing here is a verified Immunefi finding. Gate 3 was not executed.

Gate key: **G1 Divergence** · **G2 Hypothesis** · **G3 Experiment (executed evidence)** · **G4 Validate (disprove / classify)**.

## Counts

| Source | Generated | Survived G1 | Reached G2 as H-* | Executed G3 | Survived G4 as verified |
|---|---:|---:|---:|---:|---:|
| Apex AST + prediction_diff | 68 DIV-* | 2 design-wrong intended | 4 H-* (2 live, 2 lens-noise) | 0 | 0 |
| Boss-skill hunts | 45 L-* | 2 | 2 (via DIV-0067/0068) | 0 | 0 |
| Apex Slither sweep | 0 (tooling drop) | 0 | 0 | 0 | 0 |
| Independent Slither High/Medium in `packages/perps/src` | 54 | n/a (never became DIV) | 0 | 0 | 0 |
| Independent Slither High/Medium after OOS-file filter | 37 | n/a | 0 | 0 | 0 |

Verified findings: **0**.

## 1. Live hunter leads (G1 keep)

These are the only protocol-side leads that passed Gate 1 on code review. They were injected as `prediction_design_wrong` DIVs so the rest of the pipeline could see them.

| ID | DIV | H | File:line | Title | G2 | G3 | G4 |
|---|---|---|---|---|---|---|---|
| L-CH-001 | DIV-0067 | H-0001 (also noisy H-0002) | `CfdEngineSettlementSidecar.sol:274` | degradedMode freezes surplus free-settlement withdraw while position open | promoted; lens bound to constructor | prepared, **not executed** (E-0001/E-0003 pending) | DP-0001 `needs-evidence`; CL-0001 medium theoretical |
| L-CH-002 | DIV-0068 | H-0003 | `CfdEnginePlanLib.sol:1453` | liquidation reachableCollateral includes VPI reserve | promoted; dimensional lens bound to file:21 | prepared, **not executed** (E-0002/E-0004 pending) | DP-0002 `needs-evidence`; CL-0002 low theoretical |

Gate 1 keep reasons (code, not contest reports):

- **L-CH-001:** `validateWithdraw` reverts `CfdEngine__DegradedMode` whenever `pos.size != 0`. Latch is permissionless via `_enterDegradedModeIfInsolvent`. Clearance is owner-only `clearDegradedMode`. SECURITY.md describes degradedMode as a risk-expansion latch, not a CH free-cash freeze.
- **L-CH-002:** `planLiquidation` sets `settlementReachableAssets = margin + claim + vpiRebateReserve`. Lens publishes it. Live seizure does not debit VPI except clawback. Preview/live field parity broken; not shown as a custody drain without a PoC.

## 2. Boss-skill leads killed at Gate 1

Reached G2/G3/G4: **no**. Kill is code-review against the pin, not an executed counter-test.

| ID | File:line | Title | Gate 1 reason |
|---|---|---|---|
| L-CH-003 | `CfdEngineSettlementSidecar.sol:146` | Sidecar execute* auth bypass via CH operator discovery | executeOpen/Close/Liq use onlyEngine (line 146) requiring msg.sender == immutable ENGINE. buildRawSnapshot additionally allows ENGINE.planningReader(), which is onlyEngine on the host. CH onlyOperator (MarginClearinghouse.sol:226) fail-closes if engine==0 and otherwise requires … |
| L-CH-004 | `MarginClearinghouse.sol:663` | Reservation double-release: consumeActionCharge then terminal reservation release | releaseOrderReservationForTerminalCleanup (line 663) returns 0 unless status==Active. _consumeReservation sets remaining to 0 and closes as Consumed (line 800). Subsequent release sees non-Active and no-ops. consumeActionCharge requires the planned committed split to match live … |
| L-CH-005 | `libraries/CfdEnginePlanLib.sol:1136` | Trader claims used as cash to fund carry, VPI, fees, frozen spread, or bounties | _planCloseCashSources spends spendable action reserve, free settlement, released VPI remainder, terminal liq-reserve surplus, released pledge, then committed-order margin. Claims are only netted against price loss (pricePnlClaimConsumedAssets) and counted as health collateral in… |
| L-CH-006 | `CfdEngineSettlementSidecar.sol:724` | Frozen-close spread routed to protocol treasury via fee top-up | _planCloseActionSettlement fee-first caps delta.executionFeeAssets by eligible withheld+collected, then credits protocol fee from that slice only. _recoveredFrozenSpreadAssets subtracts assessed fee + unpaid carry + positive VPI before attributing remainder as spread. Live _sett… |
| L-CH-007 | `MarginClearinghouse.sol:348` | deposit() credits requested amount without receipt check (FOT / unsolicited USDG) | Known issue. Live USDG path has no FOT. depositFor (line 371) already enforces received==amount. Unsolicited USDG cannot be withdrawn because withdraw is settlementBalances-based. Owner rescueToken excludes settlement asset. |
| L-CH-008 | `MarginClearinghouse.sol:467` | Withdraw of locked buckets / remaining < totalLocked | _withdraw provisionally debits settlementBalances then calls engine.checkWithdraw then requires remainingEquity >= totalLockedMargin and settlementBalances >= totalLockedMargin (lines 467-474). Locked buckets are not reduced by withdraw. Sidecar _requireWithdrawPositionHealthy a… |
| L-CH-009 | `CfdEngineSettlementSidecar.sol:524` | Opens can leave E < L without degradedMode | planOpen rejects degradedMode and writes requiredEffectiveAssetsAfterAssets = post L + ceil(L * bufferBps / 10000) via SolvencyAccountingLib.hasRequiredSettlementBuffer. executeOpen ends with _assertRequiredEffectiveAssets against live pool.totalAssets() net of claims (line 524)… |
| L-CH-010 | `CfdEngine.sol:762` | Keeper-injected poolDepth desyncs VPI/solvency from live HousePool cash | processOrderTyped/liquidatePosition are onlyRouter. OrderRouter supplies housePool.totalAssets() in the same transaction before planning. Sidecar then re-reads totalAssets() for cash. Keepers cannot call the engine. Trusted-router malice is OOS. Live open assert also re-reads po… |
| L-CH-011 | `libraries/CloseAccountingLib.sol:112` | Carry/VPI rounding leaks more than the documented <1 atom | computeIndexedCarryAssets is floor division and checkpoints even at 0 — documented. CloseAccountingLib lines 112-118 clamp lifetime VPI so proportionalAccrual+vpiDelta cannot go negative, blocking the depth-sandwich rebate. Zero economic depth skips fresh VPI (line 107) but stil… |
| L-CH-012 | `MarginClearinghouse.sol:1549` | recoverExpiredBounty try/catch leaves Active reservation so later take/credit double-pays | recoverExpiredBounty is fail-closed: invariant mismatch quarantines (line 1573) and returns without decreasing the floor. takeBountyReservation only succeeds for Active and then zeros the record before the router transfers. transferReservedSettlement enforces remaining action re… |
| L-CH-013 | `CfdEngine.sol:1290` | TerminalNavBookV2 nested-mutation / unauthenticated curve write desync | _applyOpen/_applyClose/_applyLiquidation all begin the trader (and, for liq bounty, keeper) curve hash before sidecar mutation and end after. settlementWritePosition/Delete are onlySettlementSidecar. TerminalNavBookV2.onlyEngine (book line 124) accepts only the engine. Nested si… |
| L-CH-014 | `libraries/CfdEnginePlanLib.sol:1371` | Close solvency uses router poolAssets while cash routing uses poolCashAssets, hiding E < L | Live latch (_enterDegradedModeIfInsolvent, CfdEngine.sol:1351) re-reads pool.totalAssets() after sidecar token movements and compares to live _maxLiability(); pendingPoolPayout is 0 because payouts already hit the pool. Router sets poolDepth=totalAssets() in the same tx, so plan… |
| L-OR-001 | `OrderRouterExecutionSidecar.sol:147` | FIFO skip of a still-valid head via executeOrder(laterId) or batch cursor | The single-order loop only terminally prunes pre-oracle heads (risk-off, expiry, config mismatch). A live Execute head breaks the loop; if that head is not the requested id the call reverts OrderNotQueueHead unless prior cleanup already made progress, in which case it returns wi… |
| L-OR-002 | `OrderRecoverySidecar.sol:67` | Non-head expire/clearInvalidOrders skips a valid FIFO predecessor | expireOrder reverts OrderNotExpired unless block.timestamp > executionDeadline. clearInvalidOrders continues only when expired or expectedConfigHash is nonzero and not equal to currentExecutionConfigHash; live matching-hash orders are skipped. Unlink of a middle invalid node doe… |
| L-OR-003 | `router/OrderLiquidationBatchLogic.sol:213` | Exact client-id replay creates a second reservation or re-opens a terminal intent | resolveClientIntent runs before admission. ExactReplay returns the original id with no registerPending, no executeCommitOrderItem, and no bounty/margin lock. Conflict reverts. registerPending also returns replayed=true if the mapping already exists. commitOpenOrderWithProtection… |
| L-OR-004 | `PositionProtectionBook.sol:331` | Trader can cancel a committed queued intent | No trader cancel exists on OrderRouter for a live intent. cancelPositionProtection only cancels PendingOpen/Armed protection and refunds the trigger bounty; the parent open stays queued. cancelPositionProtectionAndCommitClose requires Armed, empty account queue, then commits a f… |
| L-OR-005 | `OrderRouterExecutionSidecar.sol:827` | Solidity panic or empty/OOG engine revert is decoded as terminal planner policy | _classifyTypedFailure requires exact selector plus exact ABI lengths (100/68/100) and known open codes 1-11 or close codes 1-7 with matching CfdEnginePlanLib category not None. Panic is 36 bytes / 0x4e487b71 and stays non-terminal; _settleEngineFailure/_settleAssessmentFailure t… |
| L-OR-006 | `libraries/CfdEnginePlanLib.sol:112` | ProtocolStateInvalidated typed codes remain retryable and jam FIFO | Sidecar sets terminal=true for any matching non-None ExecutionFailurePolicyCategory, including ProtocolStateInvalidated. CloseOnly is the separate non-typed Pending path. Transient skew/solvency therefore burns the open and pays the reserved opening bounty, which SECURITY.md alr… |
| L-OR-007 | `router/OrderLiquidationBatchLogic.sol:234` | Ordinary or protection close records a nonzero Order bounty | _commitOrder sets executionBountyAssets only in the open branch via _validatedOpenBounty; closes skip it and remain 0. _reserveExecutionBounty reverts CfdEngine__InvalidRiskParams if isClose && bounty!=0. Protection trigger/retry registerPending(..., 0), maxExecutionBountyAssets… |
| L-OR-008 | `router/OrderLiquidationBatchLogic.sol:611` | Protection trigger bounty paid to a party other than the triggering keeper, or paid twice | isProtectionTrigger requires msg.sender==positionProtectionBook. Direct updateMarkPrice ignores trailing words. The Book concatenates abi.encode(msg.sender, protectionId) after the updateMarkPrice ABI so assembly always reads the Book-appended keeper. activate() requires Armed, … |
| L-OR-009 | `router/OrderLiquidationBatchLogic.sol:294` | Public commit or execute path uses expectedConfigHash=0 as an unpinned wildcard | _validateFreshRequest reverts ExecutionConfigMismatch on zero or unequal hash before registerPending. registerPending treats zero hash as protocolIntent and requires the 0x504c455448455221 client-id prefix; public ids with zero hash never reach that check. Only Router-authentica… |
| L-OR-010 | `OrderLifecycleBook.sol:172` | Execution-config hash omits a finalized execution-authority field so pinned orders surviv… | The digest concatenates schema/chain/Book/Router/Engine/Clearinghouse/HousePool, policyEvaluator, executionSidecar, pletherOracle, both admin addresses, both activeConfigVersion values, planner, settlement sidecar, terminal NAV book, protocolTreasury(), and HousePool.markStalene… |
| L-OR-011 | `OrderLifecycleBook.sol:199` | Automatic protocolTreasury activation changes the digest and lets anyone mass-cancel pinn… | SECURITY.md lists protocol treasury as an execution-authority input whose drift is supposed to produce terminal ConfigMismatch for config-pinned external orders. Activation is owner-scheduled. Unpinned protection attempts are the documented exception. This is the same ConfigMism… |
| L-OR-012 | `OrderRouterExecutionSidecar.sol:1074` | Historical unique-parse / batch cache reuse executes a skipped post-commit tick | Cache is filled only after parsePriceFeedUpdatesUnique over (commitTime, min(commitTime+window, now)]. Reuse requires commitTime>=minReusableCommitTime, commitTime<oldestPublishTime, commitTime<publishTime, publishTime<=now, and publishTime<=commitTime+window. The originating un… |
| L-OR-013 | `libraries/OracleFreshnessPolicyLib.sol:49` | Oracle freshness/confidence gates fail open for live execution or liquidation | isStale rejects future publish times and age>maxStaleness (equality passes, as documented). Historical execution uses unique parse plus maxComponentPublishTimeDivergence; live/liquidation use signed current baskets, LIVE_TICK_LOOKBACK, per-feed staleness, and basketConfidence*10… |
| L-OR-014 | `OrderRouterExecutionSidecar.sol:98` | Execution/recovery/liquidation sidecar delegatecall writes Router storage or impersonates… | Execution and recovery sidecars have only immutables (SELF, recoverySidecar) and no mappings. Liquidation sidecar has immutable ROUTER and requires address(this)==ROUTER. Direct calls revert OnlyDelegateCall/RecoveryUnauthorized. Nested recovery delegatecall still runs in the Ro… |
| L-OR-015 | `router/OrderLiquidationBatchLogic.sol:738` | Liquidation batch item mutates another account or keeps partial bounty forfeiture on reve… | Shared snapshot is priced once (longPrice/shortPrice/neutral). Each account is an external self-call executeLiquidationBatchItem; try/catch restores that account on revert. Empty returndata stops the batch and leaves that index unattempted. Nonempty NoPosition/Solvent are skippe… |
| L-OR-016 | `libraries/OrderSettlementFloorLib.sol:19` | minPostSettlementBalanceAssets floor is not enforced on withdraw or is bound to the wrong… | Positive min is rejected unless the account is flat, the request is an open, and accountHeadOrderId==0, so the floor order is always the sole account-queue head. Later commits revert SettlementFloorOrderPending. validateWithdraw, only when position size is 0, loads that head's m… |
| L-OR-017 | `PletherOracle.sol:245` | Historical oracle calls are permissionless so a keeper-supplied BatchOrderPriceCache can … | Historical entrypoints are intentionally permissionless because Router delegatecall preserves the keeper as msg.sender. Live updatePrice/liquidation snapshots do check orderRouter(). The sidecar never ABI-decodes a keeper cache; it only reuses the cache struct returned by the pr… |
| L-OR-018 | `OrderRouterExecutionSidecar.sol:442` | Close-only FAD/frozen open at the FIFO head blocks later risk-reducing closes | Known issue in audits/ plus SECURITY.md: close-only, MEV, insufficient gas, and mark-ordering stay nonterminal and retain the FIFO head. Default window is 60 seconds. Not a new root cause. |
| L-LP-001 | `HousePool.sol:854` | Junior redemption funded while eligible Senior demand remains | Senior phase always runs first. Junior _fundRedemptionPhase runs only when seniorPhase.backlog is false. Work-cap (16 epochs with leftover budget) and leftover-budget rounding breaks both return before Junior. getMaturedRedeemHead treats any queued unfunded remainder as backlog.… |
| L-LP-002 | `TrancheVault.sol:1229` | Funded redemption claim reusable after fundingClaimed or mixed withdraw/redeem | claimableRedeemRequest/Assets are floor(position.shares * funded / epoch.shares) minus claimed. Last partial claim pays remainingAssets. Mixed ceil-withdraw then remaining-assets-with-zero-shares still sums to entitledAssets, not more. fundingClaimed is set only when fundedShare… |
| L-LP-003 | `HousePool.sol:426` | Redemption funding or payOut uses accountedAssets or rawAssets instead of min(raw, accoun… | totalAssets() is min(raw, accounted). CfdEngineProtocolLens.getHousePoolInputSnapshot sets physicalAssets from that. _settleLpEpoch budgets from buildWithdrawalSnapshot(physicalAssets). payOut subtracts accounted then safeTransfers and reverts if raw is short. recordClaimantInfl… |
| L-LP-004 | `TrancheVault.sol:650` | Share-escrow counters desync from vault ERC-20 balance | Direct route decrements depositClaimEscrowShares and increments pendingRedeemEscrowShares with no token transfer. Terminal dust burn happens only when epoch.claimedAssets==epoch.assets and burns leftover minted shares still counted in depositClaimEscrow. Junior _burn/_mint check… |
| L-LP-005 | `TrancheVault.sol:1620` | Share delivery to receiver!=controller steals shares or mixes cooldowns | _requireShareReceiver is on _claimDeposit, _claimMint, cancelRedeemRequest, and claimRedeemRefund. ERC-4626 deposit/mint wrappers pass msg.sender as controller so receiver must be the caller. Funded USDG claimRedeem/withdraw and pending-deposit USDG cancel intentionally allow a … |
| L-LP-006 | `TrancheVault.sol:325` | Deposit cooldown shortened below activation-max or inherited-max rules | Wallet transfers take max(to, from) and revert during sender cooldown; vault-sourced claims use max(receiver, activationTime); cancel/refund/bootstrap assign block.timestamp (lengthens). Direct requestRedeemFromClaimableDeposit never mixes into the wallet (documented). Fee mints… |
| L-LP-007 | `HousePool.sol:797` | LP epoch settlement hold can still fund or finalize epochs | settleLpEpoch reverts immediately if lpEpochSettlementPaused. fundRedeemEpoch, finalizeDepositEpochFromPool, and refundRedeemEpochRemainder are onlyPool. reconcile() onlyVault does not fund queues. Views (getMaxSeniorWithdraw, isWithdrawalLive, canSettleDepositEntries, senior re… |
| L-LP-008 | `libraries/HousePoolAccountingLib.sol:60` | Marked receivable treated as spendable cash for redemption funding | Reconcile snapshot (physical + signed delta - claims) prices principals only. Withdrawal snapshot uses physicalAssets=totalAssets() without the delta, then reserves maxLiability + claims + buffer + unassigned + pending claimants. seniorPhase.budget=min(freeAssets, seniorPrincipa… |
| L-LP-009 | `libraries/HousePoolSeniorCapacityLib.sol:62` | Junior withdrawal or same-tx Senior deposit activation breaks maxSeniorShareBps covenant | Junior budget is min(free, juniorPrincipal, juniorWithdrawalRatioCap). The cap ceils required junior backing of protectedExposure+reservedSeniorDepositAssets. Settlement order is Senior redeem, Junior redeem, Junior deposit, Senior deposit, so reserved Senior is still reserved w… |
| L-LP-010 | `libraries/HousePoolReconcilePlanLib.sol:113` | Unassigned / ownerless assets accrue to existing LP NAV without minting | distributeRevenue always adds leftover to juniorPrincipal, but _reconcile/_previewPendingAccountingState then call juniorRevenueWithoutOwners and move that delta to unassigned when juniorSupply was zero. Recap remainder never goes to junior. Unassigned is subtracted before water… |
| L-LP-011 | `EmergencyPauseCoordinator.sol:123` | EmergencyPauseCoordinator can unpause or move funds | Contract has no fallback/receive, no ERC-20 calls, no unpause()/unpauseLpEpochSettlement() invocations. It only calls ROUTER_ADMIN.pause() and HOUSE_POOL.pause()/pauseLpEpochSettlement(), skipping bits already set in _restrictionMask. IHousePoolEmergencyAdmin exposes unpause sel… |
| L-LP-012 | `HousePool.sol:878` | Same-call Junior deposit activation while Senior redeem backlog exists (priority confusio… | When seniorPhase.backlog is true, Junior redemptions are skipped, but deposit phases still run unless pause/entry gates fail. That is intentional: Junior entry does not consume Senior's leftover cash. freeAssets is snapshotted before any deposit finalize; tests assert seniorFund… |
| L-LP-013 | `CfdEngineProtocolLens.sol:128` | ProtocolLens freeAssets omits unassigned/pending reservations (keeper-usable overstatemen… | HousePool settlement and getFreeAssets/getSettlementFreeAssets call _buildWithdrawalSnapshot(..., unassignedAssets, pendingClaimantBuckets). The protocol-accounting snapshot is diagnostic (in-scope lens) and is not read by settleLpEpoch. Untrusted keepers cannot pass a custom bu… |

## 3. Apex DIV-* ledger

### 3a. `unmapped_critical_flow` (DIV-0001 … DIV-0008)

G1: **tooling false-positive**, not a protocol divergence. Matcher used the last `(` split token (the argument type).
G2: not promoted (except later design-wrong DIVs for two of the same flows). G3/G4: not reached.

| ID | Flow | Expected entry | Observed |
|---|---|---|---|
| DIV-0001 | F-DEPOSIT-FOR | entrypoint `MarginClearinghouse.depositFor(address,uint256)` for critical flow Credit-onl… | no matching implementation surface found |
| DIV-0002 | F-WITHDRAW | entrypoint `MarginClearinghouse.withdrawMargin(uint256)` for critical flow Trader withdra… | no matching implementation surface found |
| DIV-0003 | F-COMMIT-ORDER | entrypoint `OrderRouter.commitOrder(OrderV3Types.OrderRequest)` for critical flow Commit … | no matching implementation surface found |
| DIV-0004 | F-EXECUTE-ORDER | entrypoint `OrderRouter.executeOrder(uint64,bytes[])` for critical flow Keeper executes F… | no matching implementation surface found |
| DIV-0005 | F-LIQUIDATE | entrypoint `OrderRouter.executeLiquidation(address,bytes[])` for critical flow Full liqui… | no matching implementation surface found |
| DIV-0006 | F-PROTECT-TRIGGER | entrypoint `PositionProtectionBook.triggerPositionProtection(uint64,bytes[])` for critica… | no matching implementation surface found |
| DIV-0007 | F-LP-SETTLE | entrypoint `HousePool.settleLpEpoch(uint256,uint256)` for critical flow Permissionless LP… | no matching implementation surface found |
| DIV-0008 | F-LP-REDEEM | entrypoint `TrancheVault.requestRedeem(uint256,address,address)` for critical flow Async … | no matching implementation surface found |

### 3b. `undocumented_entrypoint` (DIV-0009 … DIV-0058, cap 50)

G1: **noise / budget cutoff**. Value-sink-shaped name heuristic, then cap 50, so the rest of the ABI was never listed.
G2: only DIV-0047 received a reverse lens → H-0004 (constructor/opaque-logic noise). All others: G2 not reached.
G3/G4: H-0004 experiment not executed; unclassified.

| ID | File:line | Observed surface |
|---|---|---|
| DIV-0009 | `packages/perps/src/CfdEngine.sol:26` | surface `settlementAsset` (function) has a value-sink-shaped name but no model flow |
| DIV-0010 | `packages/perps/src/CfdEngine.sol:32` | surface `settlementToken` (function) has a value-sink-shaped name but no model flow |
| DIV-0011 | `packages/perps/src/CfdEngine.sol:251` | surface `onlySettlementSidecar` (function) has a value-sink-shaped name but no model flow |
| DIV-0012 | `packages/perps/src/CfdEngine.sol:256` | surface `onlyAdmin` (function) has a value-sink-shaped name but no model flow |
| DIV-0013 | `packages/perps/src/CfdEngine.sol:345` | surface `setDependencies` (function) has a value-sink-shaped name but no model flow |
| DIV-0014 | `packages/perps/src/CfdEngine.sol:384` | surface `setPool` (function) has a value-sink-shaped name but no model flow |
| DIV-0015 | `packages/perps/src/CfdEngine.sol:405` | surface `setTerminalNavBook` (function) has a value-sink-shaped name but no model flow |
| DIV-0016 | `packages/perps/src/CfdEngine.sol:430` | surface `setOrderRouter` (function) has a value-sink-shaped name but no model flow |
| DIV-0017 | `packages/perps/src/CfdEngine.sol:730` | surface `checkWithdraw` (function) has a value-sink-shaped name but no model flow |
| DIV-0018 | `packages/perps/src/CfdEngine.sol:941` | surface `positionEntryCostAssetAtoms` (function) has a value-sink-shaped name but no model flow |
| DIV-0019 | `packages/perps/src/CfdEngine.sol:1010` | surface `liquidatePosition` (function) has a value-sink-shaped name but no model flow |
| DIV-0020 | `packages/perps/src/CfdEngine.sol:1146` | surface `settlementApplyCarryAndMark` (function) has a value-sink-shaped name but no model flow |
| DIV-0021 | `packages/perps/src/CfdEngine.sol:1157` | surface `settlementRealizeCarry` (function) has a value-sink-shaped name but no model flow |
| DIV-0022 | `packages/perps/src/CfdEngine.sol:1171` | surface `settlementSyncTotalSideMargin` (function) has a value-sink-shaped name but no model flow |
| DIV-0023 | `packages/perps/src/CfdEngine.sol:1186` | surface `settlementApplySideDelta` (function) has a value-sink-shaped name but no model flow |
| DIV-0024 | `packages/perps/src/CfdEngine.sol:1215` | surface `settlementConsumeTraderClaim` (function) has a value-sink-shaped name but no model flow |
| DIV-0025 | `packages/perps/src/CfdEngine.sol:1229` | surface `settlementRecordTraderClaim` (function) has a value-sink-shaped name but no model flow |
| DIV-0026 | `packages/perps/src/CfdEngine.sol:1244` | surface `settlementWritePosition` (function) has a value-sink-shaped name but no model flow |
| DIV-0027 | `packages/perps/src/CfdEngine.sol:1276` | surface `settlementDeletePosition` (function) has a value-sink-shaped name but no model flow |
| DIV-0028 | `packages/perps/src/CfdEngine.sol:1468` | surface `updateMarkPrice` (function) has a value-sink-shaped name but no model flow |
| DIV-0029 | `packages/perps/src/CfdEngineLens.sol:25` | surface `admin` (function) has a value-sink-shaped name but no model flow |
| DIV-0030 | `packages/perps/src/CfdEngineLens.sol:201` | surface `previewLiquidation` (function) has a value-sink-shaped name but no model flow |
| DIV-0031 | `packages/perps/src/CfdEngineLens.sol:209` | surface `previewRouterLiquidation` (function) has a value-sink-shaped name but no model flow |
| DIV-0032 | `packages/perps/src/CfdEngineLens.sol:231` | surface `simulateLiquidation` (function) has a value-sink-shaped name but no model flow |
| DIV-0033 | `packages/perps/src/CfdEngineLens.sol:240` | surface `isLiquidatableAt` (function) has a value-sink-shaped name but no model flow |
| DIV-0034 | `packages/perps/src/CfdEnginePlanner.sol:53` | surface `computeIndexedCarryAssets` (function) has a value-sink-shaped name but no model flow |
| DIV-0035 | `packages/perps/src/CfdEnginePlanner.sol:61` | surface `isExactPriceRiskLiquidatable` (function) has a value-sink-shaped name but no model flow |
| DIV-0036 | `packages/perps/src/CfdEnginePlanner.sol:118` | surface `planLiquidation` (function) has a value-sink-shaped name but no model flow |
| DIV-0037 | `packages/perps/src/CfdEnginePlanningReader.sol:12` | surface `settlementSidecar` (function) has a value-sink-shaped name but no model flow |
| DIV-0038 | `packages/perps/src/CfdEnginePlanningReader.sol:56` | surface `planLiquidation` (function) has a value-sink-shaped name but no model flow |
| DIV-0039 | `packages/perps/src/CfdEngineSettlementSidecar.sol:41` | surface `positionEntryCostAssetAtoms` (function) has a value-sink-shaped name but no model flow |
| DIV-0040 | `packages/perps/src/CfdEngineSettlementSidecar.sol:53` | surface `sideBorrowBaseAssets` (function) has a value-sink-shaped name but no model flow |
| DIV-0041 | `packages/perps/src/CfdEngineSettlementSidecar.sol:75` | surface `traderClaimBalanceAssets` (function) has a value-sink-shaped name but no model flow |
| DIV-0042 | `packages/perps/src/CfdEngineSettlementSidecar.sol:79` | surface `unsettledCarryAssets` (function) has a value-sink-shaped name but no model flow |
| DIV-0043 | `packages/perps/src/CfdEngineSettlementSidecar.sol:83` | surface `totalTraderClaimBalanceAssets` (function) has a value-sink-shaped name but no model flow |
| DIV-0044 | `packages/perps/src/CfdEngineSettlementSidecar.sol:99` | surface `settlementBufferBps` (function) has a value-sink-shaped name but no model flow |
| DIV-0045 | `packages/perps/src/CfdEngineSettlementSidecar.sol:255` | surface `validateWithdraw` (function) has a value-sink-shaped name but no model flow |
| DIV-0046 | `packages/perps/src/CfdEngineSettlementSidecar.sol:423` | surface `executeOpen` (function) has a value-sink-shaped name but no model flow |
| DIV-0047 | `packages/perps/src/CfdEngineSettlementSidecar.sol:548` | surface `executeClose` (function) has a value-sink-shaped name but no model flow |
| DIV-0048 | `packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:36` | surface `positionEntryCostAssetAtoms` (function) has a value-sink-shaped name but no model flow |
| DIV-0049 | `packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:48` | surface `sideBorrowBaseAssets` (function) has a value-sink-shaped name but no model flow |
| DIV-0050 | `packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:74` | surface `traderClaimBalanceAssets` (function) has a value-sink-shaped name but no model flow |
| DIV-0051 | `packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:78` | surface `unsettledCarryAssets` (function) has a value-sink-shaped name but no model flow |
| DIV-0052 | `packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:82` | surface `totalTraderClaimBalanceAssets` (function) has a value-sink-shaped name but no model flow |
| DIV-0053 | `packages/perps/src/CfdOrderPolicyEvaluatorBase.sol:89` | surface `settlementBufferBps` (function) has a value-sink-shaped name but no model flow |
| DIV-0054 | `packages/perps/src/CfdTreasury.sol:124` | surface `setProtocolTreasury` (function) has a value-sink-shaped name but no model flow |
| DIV-0055 | `packages/perps/src/CfdTreasury.sol:136` | surface `setProtocolTreasury` (function) has a value-sink-shaped name but no model flow |
| DIV-0056 | `packages/perps/src/EmergencyPauseCoordinator.sol:102` | surface `renounceOwnership` (function) has a value-sink-shaped name but no model flow |
| DIV-0057 | `packages/perps/src/EmergencyPauseCoordinator.sol:109` | surface `setGuardian` (function) has a value-sink-shaped name but no model flow |
| DIV-0058 | `packages/perps/src/EmergencyPauseCoordinator.sol:123` | surface `triggerEmergencyPause` (function) has a value-sink-shaped name but no model flow |

### 3c. `prediction_model_wrong` (DIV-0059 … DIV-0066)

G1: **pipeline bug**, recorded as ISS-0002. Observed: skeletons started at OOS `CfdClosePreview.sol` because signature tokenisation took the argument list. Not a protocol defect.
G2–G4: not promoted.

| ID | Flow | Why |
|---|---|---|
| DIV-0059 | F-DEPOSIT-FOR | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |
| DIV-0060 | F-WITHDRAW | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |
| DIV-0061 | F-COMMIT-ORDER | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |
| DIV-0062 | F-EXECUTE-ORDER | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |
| DIV-0063 | F-LIQUIDATE | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |
| DIV-0064 | F-PROTECT-TRIGGER | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |
| DIV-0065 | F-LP-SETTLE | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |
| DIV-0066 | F-LP-REDEEM | tokenisation of Type-annotated signatures takes the argument list, so every critical flow is unmapped |

### 3d. `prediction_design_wrong` (DIV-0067, DIV-0068)

See §1. These are the only DIVs treated as real protocol-side divergences.

### 3e. Apex hypotheses

| ID | DIV | Lens | Gate 3 | Gate 4 | Note |
|---|---|---|---|---|---|
| H-0001 | DIV-0067 | state-machine | pending / not executed | needs-evidence, medium theoretical | Lens statement bound to `constructor(`; live claim is still L-CH-001 |
| H-0002 | DIV-0067 | trust-boundary | none | not classified | Constructor/trust-boundary noise on CfdEngine.sol:76 |
| H-0003 | DIV-0068 | dimensional-analysis | pending / not executed | needs-evidence, low theoretical | Lens bound to PlanLib:21; live claim is L-CH-002 |
| H-0004 | DIV-0047 | reverse-engineering | none | not classified | Opaque-logic template on executeClose; no executed evidence |

## 4. Slither leads (never became DIV-* inside apex)

Apex `targeted_static_sweep` admitted **0** detectors (ISS-0003). Classification vs the four gates: **killed before G1 by tooling**.
Independent `slither --json /tmp/slither-full.json` (same pin) is the source below.

OOS files in this table are contest-excluded lenses; they are listed so Phase 2 can mark them out of coverage rather than misses.

| Impact | Check | File:line | OOS? | Description (truncated) |
|---|---|---|---|---|
| High | `arbitrary-send-eth` | `packages/perps/src/PletherOracle.sol:1055` | no | PletherOracle._refundValue(address,uint256) (src/PletherOracle.sol#1055-1068) sends eth to arbitrary user Dangerous calls: - (ok,None) = refundRecipient.call{g… |
| High | `weak-prng` | `packages/perps/src/PletherOracle.sol:805` | no | PletherOracle._computeBasketPriceFromFeeds(IPletherOracle.PriceMode,PythStructs.PriceFeed[],uint256) (src/PletherOracle.sol#805-876) uses a weak PRNG: "epochSt… |
| High | `reentrancy-eth` | `packages/perps/src/PletherOracle.sol:245` | no | Reentrancy in PletherOracle.updateBatchOrderExecutionPrice(address,bytes[],IPletherOracle.OrderExecutionRequest,IPletherOracle.BatchOrderPriceCache) (src/Pleth… |
| High | `reentrancy-eth` | `packages/perps/src/PletherOracle.sol:545` | no | Reentrancy in PletherOracle._updateOrderExecutionPrice(address,bytes[],IPletherOracle.OrderExecutionRequest) (src/PletherOracle.sol#545-563): External calls: -… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLens.sol:136` | yes | SettlementMonitorLens.HOUSE_POOL (src/SettlementMonitorLens.sol#136) is never initialized. It is used in: - SettlementMonitorLens.getSettlementHealth() (src/Se… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLensSidecar.sol:49` | yes | SettlementMonitorLensSidecar.HOUSE_POOL (src/SettlementMonitorLensSidecar.sol#49) is never initialized. It is used in: - SettlementMonitorLensSidecar._buildSet… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLensSidecar.sol:53` | yes | SettlementMonitorLensSidecar.SENIOR_VAULT (src/SettlementMonitorLensSidecar.sol#53) is never initialized. It is used in: - SettlementMonitorLensSidecar._popula… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLensSidecar.sol:52` | yes | SettlementMonitorLensSidecar.TERMINAL_NAV_BOOK (src/SettlementMonitorLensSidecar.sol#52) is never initialized. It is used in: - SettlementMonitorLensSidecar._p… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLens.sol:141` | yes | SettlementMonitorLens.JUNIOR_VAULT (src/SettlementMonitorLens.sol#141) is never initialized. It is used in: - SettlementMonitorLens._buildSettlementStatus(uint… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLensSidecar.sol:57` | yes | SettlementMonitorLensSidecar._BOUND_PLANNER_CODEHASH (src/SettlementMonitorLensSidecar.sol#57) is never initialized. It is used in: - SettlementMonitorLensSide… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLensSidecar.sol:55` | yes | SettlementMonitorLensSidecar.settlementToken (src/SettlementMonitorLensSidecar.sol#55) is never initialized. It is used in: - SettlementMonitorLensSidecar._rea… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLens.sol:140` | yes | SettlementMonitorLens.SENIOR_VAULT (src/SettlementMonitorLens.sol#140) is never initialized. It is used in: - SettlementMonitorLens._buildSettlementStatus(uint… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLensSidecar.sol:56` | yes | SettlementMonitorLensSidecar._BOUND_PLANNER (src/SettlementMonitorLensSidecar.sol#56) is never initialized. It is used in: - SettlementMonitorLensSidecar._plan… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLens.sol:143` | yes | SettlementMonitorLens.SIDECAR (src/SettlementMonitorLens.sol#143) is never initialized. It is used in: - SettlementMonitorLens.getSettlementStatus(uint256) (sr… |
| High | `uninitialized-state` | `packages/perps/src/SettlementMonitorLensSidecar.sol:54` | yes | SettlementMonitorLensSidecar.JUNIOR_VAULT (src/SettlementMonitorLensSidecar.sol#54) is never initialized. It is used in: - SettlementMonitorLensSidecar._popula… |
| Medium | `incorrect-equality` | `packages/perps/src/PletherOracle.sol:397` | no | PletherOracle._claimEthRefund(address) (src/PletherOracle.sol#397-412) uses a dangerous strict equality: - amount == 0 (src/PletherOracle.sol#404) |
| Medium | `incorrect-equality` | `packages/perps/src/PletherOracle.sol:1039` | no | PletherOracle._refundExcess(address,uint256) (src/PletherOracle.sol#1039-1053) uses a dangerous strict equality: - refund == 0 (src/PletherOracle.sol#1044) |
| Medium | `incorrect-equality` | `packages/perps/src/CfdClosePreview.sol:167` | yes | CfdClosePreview._validateRouterCommit(CfdEnginePlanTypes.RawSnapshot,CfdTypes.Order,address) (src/CfdClosePreview.sol#167-194) uses a dangerous strict equality… |
| Medium | `incorrect-equality` | `packages/perps/src/PletherOracle.sol:925` | no | PletherOracle._orderExecutionPrice(IPletherOracle.OrderExecutionRequest,uint256,uint256,bool) (src/PletherOracle.sol#925-941) uses a dangerous strict equality:… |
| Medium | `incorrect-equality` | `packages/perps/src/PletherOracle.sol:805` | no | PletherOracle._computeBasketPriceFromFeeds(IPletherOracle.PriceMode,PythStructs.PriceFeed[],uint256) (src/PletherOracle.sol#805-876) uses a dangerous strict eq… |
| Medium | `incorrect-equality` | `packages/perps/src/PletherOracle.sol:749` | no | PletherOracle._resolveCurrentBasket(bytes[],IPletherOracle.PriceMode,IPletherOracle.PolicySnapshot) (src/PletherOracle.sol#749-801) uses a dangerous strict equ… |
| Medium | `incorrect-equality` | `packages/perps/src/PletherOracle.sol:905` | no | PletherOracle._adverseOrderPrice(IPletherOracle.OrderExecutionRequest,uint256,uint256) (src/PletherOracle.sol#905-923) uses a dangerous strict equality: - shif… |
| Medium | `incorrect-equality` | `packages/perps/src/PletherOracle.sol:943` | no | PletherOracle._adverseLiquidationPrice(address,uint256,uint256) (src/PletherOracle.sol#943-958) uses a dangerous strict equality: - shift == 0 (src/PletherOrac… |
| Medium | `incorrect-equality` | `packages/perps/src/PletherOracle.sol:1021` | no | PletherOracle._normalizePythPrice(int64,int32) (src/PletherOracle.sol#1021-1037) uses a dangerous strict equality: - expo == - 8 (src/PletherOracle.sol#1030) |
| Medium | `incorrect-equality` | `packages/perps/src/PletherOracle.sol:878` | no | PletherOracle._snapshotFromBasket(PletherOracle.BasketPrice,IPletherOracle.PolicySnapshot,bool) (src/PletherOracle.sol#878-903) uses a dangerous strict equalit… |
| Medium | `pyth-unchecked-confidence` | `packages/perps/src/PletherOracle.sol:645` | no | Pyth price conf field is not checked in PletherOracle._requireStoredFeedCoverage(bytes32,uint256) (src/PletherOracle.sol#645-653) - storedPublishTime = pyth.ge… |
| Medium | `pyth-unchecked-publishtime` | `packages/perps/src/PletherOracle.sol:645` | no | Pyth price publishTime field is not checked in PletherOracle._requireStoredFeedCoverage(bytes32,uint256) (src/PletherOracle.sol#645-653) - storedPublishTime = … |
| Medium | `uninitialized-local` | `packages/perps/src/CfdOrderPolicyEvaluator.sol:98` | no | CfdOrderPolicyEvaluator.assessOrder(address,CfdTypes.Order,address,uint256,uint256,OrderV3Types.ExecutionBounds,uint256).context (src/CfdOrderPolicyEvaluator.s… |
| Medium | `uninitialized-local` | `packages/perps/src/TerminalNavBookV2.sol:512` | no | TerminalNavBookV2._replaceCurve(ITerminalNavBookV2.CurveRecord,ITerminalNavBookV2.CurveRecord).oldPrefix (src/TerminalNavBookV2.sol#512) is a local variable ne… |
| Medium | `uninitialized-local` | `packages/perps/src/OrderLifecycleBook.sol:704` | no | OrderLifecycleBook._validateBountyDisposition(OrderV3Types.OrderReceipt).forfeited (src/OrderLifecycleBook.sol#704) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/OrderLifecycleBook.sol:706` | no | OrderLifecycleBook._validateBountyDisposition(OrderV3Types.OrderReceipt).disposition (src/OrderLifecycleBook.sol#706) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/PletherOracle.sol:816` | no | PletherOracle._computeBasketPriceFromFeeds(IPletherOracle.PriceMode,PythStructs.PriceFeed[],uint256).maxPublishTime (src/PletherOracle.sol#816) is a local vari… |
| Medium | `uninitialized-local` | `packages/perps/src/OrderRecoverySidecar.sol:279` | no | OrderRecoverySidecar._validateSettledTerminalInput(IOrderRouterExecutionHost,OrderV3Types.PendingIntent,IOrderRouterExecutionHost.SettledTerminalInput).recipie… |
| Medium | `uninitialized-local` | `packages/perps/src/PletherOracle.sol:143` | no | PletherOracle.constructor(address,address,address,bytes32[],uint256[],uint256[],bool[]).totalWeight (src/PletherOracle.sol#143) is a local variable never initi… |
| Medium | `uninitialized-local` | `packages/perps/src/SettlementMonitorLens.sol:1191` | yes | SettlementMonitorLens._populateCommonDepositDeferrals(SettlementMonitorViewTypes.SettlementStatus,SettlementMonitorLens.StatusReadValidity).common (src/Settlem… |
| Medium | `uninitialized-local` | `packages/perps/src/CfdEngineLens.sol:542` | no | CfdEngineLens._findLiquidationPrice(CfdTypes.Position,uint256,uint256,uint256,uint256).low (src/CfdEngineLens.sol#542) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/OrderLifecycleBook.sol:703` | no | OrderLifecycleBook._validateBountyDisposition(OrderV3Types.OrderReceipt).refunded (src/OrderLifecycleBook.sol#703) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/TerminalNavBookV2.sol:329` | no | TerminalNavBookV2._terminalLpPriceDeltaAssetAtoms(uint32).prefix (src/TerminalNavBookV2.sol#329) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/OrderRouterExecutionSidecar.sol:242` | no | OrderRouterExecutionSidecar.executeOrderBatch(uint64,bytes[]).state (src/OrderRouterExecutionSidecar.sol#242) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/CfdEngineLens.sol:563` | no | CfdEngineLens._findLiquidationPrice(CfdTypes.Position,uint256,uint256,uint256,uint256).lo (src/CfdEngineLens.sol#563) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/OrderRecoverySidecar.sol:278` | no | OrderRecoverySidecar._validateSettledTerminalInput(IOrderRouterExecutionHost,OrderV3Types.PendingIntent,IOrderRouterExecutionHost.SettledTerminalInput).disposi… |
| Medium | `uninitialized-local` | `packages/perps/src/OrderRouterExecutionSidecar.sol:479` | no | OrderRouterExecutionSidecar._executePrepared(IOrderRouterExecutionHost,IOrderLifecycleBook,CfdTypes.Order,OrderV3Types.PendingIntent,IOrderRouterExecutionHost.… |
| Medium | `uninitialized-local` | `packages/perps/src/CfdEngineLens.sol:462` | no | CfdEngineLens._frozenSpreadPaidAssets(CfdEnginePlanTypes.CloseDelta).effectiveSpreadAssets (src/CfdEngineLens.sol#462) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/SettlementMonitorLens.sol:820` | yes | SettlementMonitorLens._validateQueueEndpoints(SettlementMonitorViewTypes.TrancheQueueStatus,address,uint256,bool,bool,bool,bool).redeemValid (src/SettlementMon… |
| Medium | `uninitialized-local` | `packages/perps/src/SettlementMonitorLens.sol:810` | yes | SettlementMonitorLens._validateQueueEndpoints(SettlementMonitorViewTypes.TrancheQueueStatus,address,uint256,bool,bool,bool,bool).depositValid (src/SettlementMo… |
| Medium | `uninitialized-local` | `packages/perps/src/TerminalNavBookV2.sol:537` | no | TerminalNavBookV2._applyEvent(uint32,ITerminalNavBookV2.Coeff,bool).prefix (src/TerminalNavBookV2.sol#537) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/OrderLifecycleBook.sol:702` | no | OrderLifecycleBook._validateBountyDisposition(OrderV3Types.OrderReceipt).paid (src/OrderLifecycleBook.sol#702) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/SettlementMonitorLens.sol:314` | yes | SettlementMonitorLens._buildSettlementStatus(uint256).validity (src/SettlementMonitorLens.sol#314) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/PletherOracle.sol:261` | no | PletherOracle.updateBatchOrderExecutionPrice(address,bytes[],IPletherOracle.OrderExecutionRequest,IPletherOracle.BatchOrderPriceCache).reusedBasket (src/Plethe… |
| Medium | `uninitialized-local` | `packages/perps/src/SettlementMonitorLens.sol:488` | yes | SettlementMonitorLens._buildTrancheQueueStatus(address,uint256,uint256,bool).failedReadMask (src/SettlementMonitorLens.sol#488) is a local variable never initi… |
| Medium | `uninitialized-local` | `packages/perps/src/TerminalNavBookV2.sol:513` | no | TerminalNavBookV2._replaceCurve(ITerminalNavBookV2.CurveRecord,ITerminalNavBookV2.CurveRecord).nextPrefix (src/TerminalNavBookV2.sol#513) is a local variable n… |
| Medium | `uninitialized-local` | `packages/perps/src/OrderLifecycleBook.sol:705` | no | OrderLifecycleBook._validateBountyDisposition(OrderV3Types.OrderReceipt).recipient (src/OrderLifecycleBook.sol#705) is a local variable never initialized |
| Medium | `uninitialized-local` | `packages/perps/src/CfdEngineSettlementSidecar.sol:733` | no | CfdEngineSettlementSidecar._recoveredFrozenSpreadAssets(CfdEnginePlanTypes.CloseDelta).effectiveSpreadAssets (src/CfdEngineSettlementSidecar.sol#733) is a loca… |
| Medium | `uninitialized-local` | `packages/perps/src/router/OrderLiquidationBatchLogic.sol:234` | no | OrderLiquidationBatchLogic._commitOrder(IOrderLiquidationBatchHost,address,OrderV3Types.OrderRequest,bool).executionBountyAssets (src/router/OrderLiquidationBa… |

In-scope High remaining after OOS-file filter: `PletherOracle` `arbitrary-send-eth`, `weak-prng`, two `reentrancy-eth`. These were **never generated** as apex DIVs. Confirmation specs are in `POC-QUEUE.md` (optional).

## 5. What was never generated

Anything not in this ledger was not a campaign lead. Phase 2 will classify the 69 public reports against this set (found / killed before validation / killed after validation / never generated / out of coverage / tooling failure / budget cutoff). That work starts only after this directory is committed.

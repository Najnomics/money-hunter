# #99855 [CRITICAL]

Source: https://reports.immunefi.com/plether/99855-sc-critical-gross-pending-trading-revenue-is-never-netted-against-trader-payouts-letting-junior-lps-withdraw-quarantined-unassignedassets

Brief/Intro
When both stored tranche principals are zero, HousePool records every trading receipt in pendingTradingRevenueAssets . Trader payouts reduce pool cash but never reduce that bucket. At the next reconciliation, planReconcile() reserves the whole gross bucket from distributable NAV before it caps unassignedAssets . The ownerless reserve therefore absorbs the payouts, and the gross bucket is credited to the tranches.
A Junior holder can exploit this with hedged trades. A LONG and an equal SHORT are opened and closed together. The losing leg's payment enters the pending bucket. The winning leg's equal payout is charged against the reserve. Pool cash barely moves, but the reserve turns into withdrawable Junior principal.
In the PoC, 10 hedged cycles raise pool cash by only 6,967 USDG but grow pending revenue to 161,039 USDG . One permissionless settlement then writes the reserve down by 154,071 USDG . A holder of 50% of Junior shares, who had deposited 5,000 USDG, withdraws 75,519 USDG . All positions are flat at the settlement checkpoint, and no mark-to-market value is involved.
Vulnerability Details
Reviewed revision: a82d4fefb02768e5b3bddcc97dee371eee24fea8 . Paths are relative to packages/perps/src .
1. Revenue is queued gross while both principals are zero
HousePool.recordClaimantInflow() adds cash and queues the full amount whenever both stored principals are zero:
if (cashMode = = IHousePool.ClaimantInflowCashMode.CashArrived) {
accountedAssets + = amount;
}
if (kind = = IHousePool.ClaimantInflowKind.Recapitalization) {
_recordPendingClaimantInflow(kind, amount);
} else if (seniorPrincipal + juniorPrincipal = = 0 ) {
_recordPendingClaimantInflow(kind, amount);
}
A losing close is one such inflow. CfdEngineSettlementSidecar.sol:604-612 records the consumed price-loss pledge plus collected action charges as Revenue / CashArrived . Positive opening VPI and collected carry reach the same bucket.
2. Trader payouts never retire the bucket
HousePool.payOut() only reduces accounted cash and transfers tokens:
accountedAssets - = amount;
settlementToken.safeTransfer(recipient, amount);
The only live decrement of the bucket is its consumption during reconciliation ( HousePool.sol:1787-1792 ). Between two reconciliations, the bucket is therefore the sum of all receipts , while pool cash reflects receipts minus payouts.
3. Reconciliation reserves the gross bucket ahead of the ownerless reserve
_reconcile() caps the bucket only against total distributable NAV ( HousePool.sol:1829-1834 ):
return HousePoolPendingPreviewLib.capClaimantBuckets(claimantBuckets, reconcileSnapshot.distributable);
HousePoolReconcilePlanLib.planReconcile() then subtracts the bucket first and caps unassignedAssets to what is left:
if (pendingBucketAssets > 0 ) {
snapshot.distributable =
snapshot.distributable > pendingBucketAssets ? snapshot.distributable - pendingBucketAssets : 0 ;
}
plan.state.unassignedAssets =
state.unassignedAssets > snapshot.distributable ? snapshot.distributable : state.unassignedAssets;
_reconcile() stores the reduced reserve, then applies the bucket through applyRevenueIntent() . That restores Senior up to its high-water mark and credits the rest to juniorPrincipal . Nothing records the reserve shortfall, so it is never restored.
With reserve U , gross bucket R and payouts X since the principals were wiped (flat pool, R <= distributable ):
pool cash after trading = U + R - X
reserve after reconciliation = min(U, U + R - X - R) = U - X
tranche credit = R
The payouts are charged to the ownerless reserve, and the gross receipts go to LPs. A correct net ledger gives unassigned = U and tranche credit = R - X .
4. Why this breaks the intended ownership rules
- INTERNAL_ARCHITECTURE_MAP.md:75 says unassigned assets "Require explicit assignment; cannot silently become windfall LP ownership."
- ACCOUNTING_SPEC.md:650 says only value with no safe claimant path belongs in unassignedAssets . Here the reserve shrinks while pool cash rises .
- For ordinary principal, losses hit Junior, then Senior, and only then the reserve. Pending revenue is also claimant-owned value, but it is reserved ahead of the ownerless reserve. Losses that follow it therefore skip the LP-owned bucket and land on unassignedAssets .
- The project's reference model ( PerpWaterfallReferenceInvariant.t.sol ) derives ownership from a net cash ledger. Its handler reconciles after every round trip, so the pending bucket never spans more than one trade. On the PoC's sequence the reference model would leave the reserve untouched, because cash ends above U .
5. Reachability
Every step is either a documented trusted action or a permissionless public action:
- A recap surplus exists. CfdEngine.recapitalizePool() restores Senior to its high-water mark and parks the excess in unassignedAssets . The project's own test test_Reachability_RecapitalizationRestoresSeniorAndReservesSurplusBeforeNewRevenue asserts that this surplus "remains reserved through later trading revenue". The MED-26 response confirms that trading continues while post-activation ownerless value exists.
- The tranches are wiped by a realized loss. After a recovery recap the tranches are small compared with the reserve. In the PoC, an ordinary 6% trader win on a 400k LONG exceeds the 20k of total principal. Any settlement with a matured request persists the wipe. A full-balance Junior redemption is refunded at zero value, and that counts as progress. Share supplies survive.
- The attacker runs hedged pairs while principals are zero. Each cycle opens a LONG and an equal SHORT and closes both after a price move. The losing leg's payment enters the bucket and the winning leg is paid from pool cash. The trader side nets to zero, minus fees and VPI. The order of the two closes does not matter.
- The attacker redeems pre-existing Junior shares. The request matures one LP epoch later, and anyone can call OrderRouter.settleLpEpoch() . The settlement persists the write-down and funds the redemption in the same transaction.
If a third party settles during step 3, the diversion accumulated so far is locked into tranche principal at that point. It is not reversed. The attacker needs price movement but not price control. Each cycle diverts roughly size × |move| plus positive VPI and costs about 16 bps of notional in execution fees plus net VPI. In the PoC, each cycle costs the traders about 931 USDG and diverts about 15,400 USDG.
6. Relation to known and other issues
- MED-26 (acknowledged). It concerns activating trading against ownerless assets, and trader PnL consuming them. Here the traders lose money in aggregate (9,311 USDG). The reserve goes to LP holders through the gross/net ledger mismatch, not to traders.
- SC-L1 / MED-12 (fixed). Those fixes cap pending buckets at distributable NAV and keep partial-settlement residuals reserved. In the PoC the whole bucket is settleable and no residual remains. The defect is that the bucket itself is overstated.
- MED-6 (fixed). That fix caps protocol-fee top-ups by the pending and unassigned reserves, and this report does not depend on top-ups. Ordinary trader payouts keep their documented priority over those reserves, and this report does not ask for that to change.
- MED-1 (fixed). That issue concerns stale-mark consumption of buckets. Every reconciliation here uses a fresh mark.
Impact Details
Selected impact: Critical, direct theft of funds.
USDG reserved as ownerless recapitalization capital is paid out to Junior LPs who have no claim to it. In the PoC:
Quantity USDG Reserve before trading 976,244 Net pool cash change over 10 hedged cycles +6,967 pendingTradingRevenueAssets before settlement 161,039 Reserve after one settlement 822,173 Reserve written down 154,071 Senior restored to its high-water mark 10,000 Credited to Junior 151,038 Attacker payout (50% of Junior, 5,000 deposited) 75,519 Hedge traders' aggregate cost 9,311
The attacker nets about 61,000 USDG after its deposit and trading costs. The other Junior holders receive the remaining 75,519 USDG of the diverted reserve.
The loss is permanent. No code path restores the reserve. When governance later calls assignUnassignedAssets() , it reconciles first and can assign only the reduced balance. The amount at risk grows with the number of cycles completed before any settlement, up to all of unassignedAssets .
Feasibility factors are: a recap surplus coexisting with wiped principals; price moves large enough for each cycle to cover its fees; and the owner not assigning the reserve first. Under the program's Feasibility Limitations, these affect the reward amount, not the impact or severity. The only privileged step is the documented recapitalizePool() .
Side effect, not claimed separately: when the gross bucket exceeds distributable NAV, the excess remains as a residual reservation with no cash behind it. It keeps deposit activation deferred.
Recommendation
Make pending revenue absorb losses before the ownerless reserve does, as ordinary tranche principal already does. Either of these works:
- Cap revenue after the reserve. In _settleablePendingClaimantBuckets() / planReconcile() , cap unassignedAssets against distributable NAV first. Then cap the revenue bucket against distributable - unassignedAssets , and write off any revenue in excess of that, since its cash has already left the pool.
- Net payouts against the bucket. While the bucket is nonzero and both principals are zero, reduce pendingTradingRevenueAssets by trader payouts and rebates, or record the pool cash at the time revenue first queues and cap the settleable revenue at the net increase since then.
Apply the same change to _previewPendingAccountingState() so that previews, cancellation predicates and live settlement stay consistent.
Proof of Concept
Proof of Concept
Save as test/poc/UnnettedPendingRevenueReserveDiversion.t.sol and run:
forge test --match-path test /poc/UnnettedPendingRevenueReserveDiversion.t.sol -vv
The PoC uses the in-repo BasePerpTest harness with the release risk parameters from packages/perps/DEPLOYMENT.md (1% VPI factor, 40% skew limit) and the release Senior limits (40M USDG / 80%). It does not modify any in-scope contract. All protocol actions go through public entry points ( requestRedeem , recapitalizePool , router.commitOrder / executeOrder , router.settleLpEpoch , claimRedeem ).
Steps
- Fund Junior (1k seed, attacker 5k, incumbent 4k, Carol 1k) and Senior (1k seed, 9k LP).
- The owner recapitalizes 980,000 USDG. One settlement parks the full amount in unassignedAssets .
- A trader opens a 400k LONG at $1.00 and closes it at $0.94. The realized gain exceeds total LP principal. The incumbent's full-balance Junior redemption is refunded at zero value, which persists the wipe. Both principals are 0 and share supplies survive.
- Two hedge traders run 10 cycles: each opens a 300k LONG and a 300k SHORT, then closes both after the price alternates between $1.00 and $0.95. No LP settlement runs in between.
- The attacker requests redemption of all its Junior shares. After one epoch, a permissionless router.settleLpEpoch() reconciles and funds it.
Output
[PASS] test_Poc_GrossPendingRevenueDivertsUnassignedToJunior()
unassigned after wipe: 976244094392
pool cash after wipe: 976244094392
senior HWM: 10000219202
pool cash after wash cycles: 983211433967
pending trading revenue: 161038723373
stored unassigned (unchanged until reconcile): 976244094392
aggregate hedge trader cost: 9311339575
unassigned after settlement: 822172710594
reserve write-down: 154071383798
senior principal after: 10000219202
junior principal after: 75519229105
pending revenue after: 0
attacker claimable shares: 5000045660416
attacker USDG payout (5k historical deposit): 75519275066
Code
// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.8.35;
import { BasePerpTest } from "../../packages/perps/test/perps/BasePerpTest.sol" ;
import { CfdTypes } from "@plether/perps/CfdTypes.sol" ;
/// @notice Verification PoC: wit

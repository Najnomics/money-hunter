# #97591 [CRITICAL]

Source: https://reports.immunefi.com/plether/97591-sc-critical-housepool-prices-junior-entry-and-exit-with-open-positions-refundable-vpi-in-nav-so-a-trading-lp-takes-incumbent-junior-principal-each-cycle

Description
Summary
HousePool prices Junior deposits and redemptions from a NAV that contains every open position's signed lifetime VPI. A skew-increasing open's charge is booked as pool revenue, and a skew-reducing open's rebate leaves pool cash, when paid. When the same position closes, a fresh VPI delta can return all of it. The lifetime clamp caps a charge's refund at the amount paid and makes a rebate's clawback at least its full amount. An address that is both Junior LP and trader enters while that term is low, exits while it is high, then closes. Junior LPs who stay, or who deposit while that term is high, pay the difference.
- Impact: Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield
- Severity: Critical
- Attacker needs: no role; 1.4M to 3M USDG of Junior deposits plus 150k to 400k of trading margin in the tests; one address, or two for the largest form
- Funds at risk: incumbent Junior principal. Against a 1M Junior tranche the largest test costs the incumbent 30,356.96 USDG (3.04%) in 15 hours and nets the attacker 23,926.19; the simplest costs 708.65 per 3-hour cycle
- Reproduce: forge test --match-path test/perps/JuniorNavSignedVpi.t.sol -vv (from packages/perps , audit repository commit a82d4fefb02768e5b3bddcc97dee371eee24fea8)
Affected assets
Contract (all in packages/perps/src ) Address (Arbitrum Sepolia v2.0.0) HousePool 0xeb5604c393843b2f3c347ec24fa9ddad6ab2131e CfdEngineProtocolLens 0x82fc00d77e86c52e2480459d07ad6220f1106413 CfdEngineSettlementSidecar 0xd3ede337e042d5aa6ba68e03d0c885b3d4a062dc CfdEngine 0xca18a6783d7542f9d2f28f4f259772b74c4d6baa TrancheVault (Junior) 0x4a8b67184a1e3224c11a191cc69f22c50eef734e
Source: the audit repository at commit a82d4fefb02768e5b3bddcc97dee371eee24fea8, whose packages/perps/src equals that of the v2.0.0 release (source commit 1209ca8a):
https://github.com/immunefi-team/audit-comp-plether/tree/a82d4fefb02768e5b3bddcc97dee371eee24fea8
The runtime code of each address above matches the release manifest's code hash, and the pool held 999,320.61 USDG Junior and 1,000,681.39 USDG Senior with no open positions at block 324,707,355. The PoC starts from about that state.
Preconditions
- Attacker: no role. One address deposits into the Junior vault and trades through the Router. The depth-amplified form also uses a second account for the opposite position, because an account cannot hold both sides ( CfdEnginePlanLib.sol:313-316 ); no per-identity limit is involved. The PoC holds the oracle price constant, at a 1 bp confidence. From the linear payoff, a driftless price adds variance, not expected loss, to the open position.
- Victim: holds Junior shares.
- External: no other trader, except ordinary skew for the entry discount.
- Program terms: "Impacts requiring basic economic and governance attacks (e.g. 51% attack)" and "Impacts from Sybil attacks" are excluded; the Severity section answers both.
Root cause
- A skew-increasing open's VPI is credited to the pool as revenue as soon as it is paid. packages/perps/src/CfdEngineSettlementSidecar.sol:454-464 :
if (delta.tradeCostAssets > 0 ) {
uint256 poolCashInflowAssets = uint256 (delta.tradeCostAssets) - protocolFeeCreditedAssets;
if (poolCashInflowAssets > 0 ) {
IHousePool(host.pool())
.recordClaimantInflow(
poolCashInflowAssets,
IHousePool.ClaimantInflowKind.Revenue,
IHousePool.ClaimantInflowCashMode.CashArrived
);
}
}
-
A skew-reducing open's rebate is priced at trade-time depth and paid out of pool cash at once ( packages/perps/src/libraries/CfdEnginePlanLib.sol:333 , packages/perps/src/CfdEngineSettlementSidecar.sol:442-444 ), and the same amount is locked as the trader's VPI reserve ( CfdEngineSettlementSidecar.sol:466-477 ).
-
When the same position closes, a fresh VPI delta at current skew and depth can return all of the VPI. The lifetime clamp keeps lifetime VPI at zero or above, so a refund cannot exceed the prepaid charge. A close that restores skew claws the rebate back from the reserve, at least in full ( CfdEnginePlanLib.sol:1052-1056 ; liquidation CfdEnginePlanLib.sol:1554-1571 ). packages/perps/src/libraries/CloseAccountingLib.sol:112-118 :
// Clamp so lifetime VPI (accrued + delta) never goes negative. Prevents LP sandwich attacks
// where an attacker opens at high depth, reduces pool depth, then closes to extract a
// net-negative lifetime VPI rebate. This rule is identical in live and oracle-frozen markets; frozen-market
// stale-price risk is priced separately through frozenSpreadAssets.
if (state.proportionalAccrualAssets + state.vpiDeltaAssets < 0 ) {
state.vpiDeltaAssets = - state.proportionalAccrualAssets;
}
- LP entry and exit share one NAV: physical assets, minus trader claims, plus the terminal price delta. Nothing in it nets the open positions' vpiAccrued . packages/perps/src/CfdEngineProtocolLens.sol:70 passes the price delta through, and packages/perps/src/libraries/HousePoolAccountingLib.sol:63-71 builds the NAV from it:
uint256 terminalAssets = engineSnapshot.physicalAssets;
uint256 terminalLiabilities = engineSnapshot.traderClaimBalanceAssets;
int256 terminalDelta = engineSnapshot.terminalLpPriceDeltaAssets;
if (terminalDelta > = 0 ) {
terminalAssets + = uint256 (terminalDelta);
} else {
// This form also handles `type(int256).min` without negating it directly.
terminalLiabilities + = uint256 ( - (terminalDelta + 1 )) + 1 ;
}
The broken rule: Junior NAV counts each open position's vpiAccrued as final, although the close can return all of it, and Junior shares are minted and burned at that NAV. From the deposit sizes and the curve, five attack tests close at the clamp, which returns exactly vpiAccrued ; in test_attack_exitPremiumAtUnchangedDepth the curve returns almost all of it. The clamp itself works as designed and stops rebate-only round trips; the gap is that LP pricing does not wait for the close it settles.
The project's symmetric-NAV rule, which paid VPI bypasses, reads: "new LPs receive the same marked-liability discount borne by existing LPs and do not inherit old trader obligations at a higher deposit NAV" ( packages/perps/SECURITY.md:859-860 ).
Attack path
Depth-amplified rebate (the largest form, test_attack_depthAmplifiedRebate ; at the size bound, test_attack_depthAmplifiedRebateAtBound ):
- The attacker deposits 3M USDG into Junior. Depth is 5M, so the 40% skew cap allows its 1.9M long, which pays a 3,609.82 charge.
- The attacker redeems. Depth falls back to about 2M, and the long stays open.
- In each later window the attacker's second account opens a 1.9M short. At the small depth it is paid a rebate from pool cash (9,021.47 in the first), so Junior NAV drops.
- The attacker's deposit activates at that lowered NAV. The short then closes, and the lifetime clamp makes it repay the whole rebate. The attacker redeems once that repayment has raised NAV again, holding about 75% of Junior.
- After the last window the long closes.
Exit premium (no other trader needed):
- The attacker requests a Junior deposit of 1.4M USDG. It activates at the next LP epoch with no open positions.
- The attacker opens a 1.2M long, 35% of depth. It prepays 2,117.54 USDG of VPI, which is booked as pool revenue.
- After the one-hour deposit cooldown the attacker requests redemption. It settles in full at the next epoch; a minute before it, Junior NAV per share is 0.999334 instead of 0.998440 in the control.
- The attacker closes the long. The clamp refunds the VPI from pool cash, which the remaining Junior LPs now carry.
Entry discount (an ordinary trader holds an 800k long):
- The attacker requests a Junior deposit of 3M USDG.
- Two minutes before the epoch boundary the attacker opens an 800k short and is paid a 1,598.80 USDG rebate from pool cash. Junior NAV per share falls from 1.000066 (control) to 0.998489, and the deposit activates at that lowered NAV.
- The attacker closes the short (the rebate is clawed back from its reserve) and redeems after the cooldown.
Impact
USDG, attack minus a control run from the same state with the same LP legs but no trades:
Test Attacker Incumbent Junior LP Window test_attack_depthAmplifiedRebate +11,523.68 -15,324.27 three windows, 32,407 s test_attack_depthAmplifiedRebateAtBound (size 1,965,300) +23,926.19 -30,356.96 five windows, 54,007 s test_attack_prepaidVpiExitPremium +228.45 -708.65 one cycle, 10,807 s test_attack_rebateEntryDiscountAgainstOrdinarySkew +533.87 -1,174.07 one cycle, 10,793 s test_attack_repeatedCycles (exit premium x4) +917.61 -2,838.37 43,207 s test_attack_exitPremiumAtUnchangedDepth +228.11 +226.49; the ordinary depositor -934.81 one cycle, 10,807 s
test_negative_tradingLegAloneLoses : an 800k open and close at the skew cap, with no LP leg, costs the attacker 684.14 USDG, so the profit comes from LP pricing, not from the trade's own VPI round trip. test_negative_vpiNeutralNavRemovesTheGain installs an equivalent of the recommended NAV term: the exit premium then costs the attacker 1,017.44, the entry discount 678.91 and the depth-amplified rebate 4,825.73 (absolute nets); the incumbent gains where it is measured.
In five of the six attack tests incumbent Junior LPs end below their starting principal, and the attacker ends with more than it put in.
Severity
The PoC shows the program's row "Direct theft of any user funds, whether at-rest or in-motion, other than unclaimed yield". The incumbent's loss is principal: its value falls 16.74 in the control and 725.39 with the attack. Of the 708.65 difference, about 228 goes to the attacker, 480 to the treasury as the open's execution fee and 0.20 to the keeper.
Each cycle needs one LP epoch to enter and one to exit and reuses the same capital; I found no cap on the number of cycles in the code ( test_attack_repeatedCycles runs four).
I found no project document that accepts this for VPI. For carry one does: "This intentionally allows a trader and incoming LP to time collection after LP activation" ( packages/perps/ACCOUNTING_SPEC.md:737 ). For rebates, the reserve rules point the other way.
The reserve exclusion exists "so LPs cannot withdraw it as marked equity before the matching position obligation settles" ( packages/perps/WHITEPAPER.md:887-888 ). Keeping anticipated VPI out of NAV ( packages/perps/SECURITY.md:872 ) stops an unpaid clawback from inflating NAV. The gap is paid VPI: unlike collected carry, it is not final until the close, yet NAV counts it at once.
The project's scan report ( audits/scan-plether-fi-plether-core-d4541b49.md ) lists "Temporary pool-liquidity reduction can amplify a skew-reducing close rebate" (informational). That item's harm is a close rebate above the unmanipulated curve, capped at the accrual. Here the harm remains without it: test_attack_exitPremiumAtUnchangedDepth keeps depth unchanged (3.4M at the open and at the close). The attacker still gains 228.11 against the control, so the loss comes from LP pricing, not from depth at close. In the depth-amplified form the smaller depth enlarges an open rebate, which the short repays in full at its close. No trading leg keeps a net VPI rebate, as VpiRoundTripAccounting.t.sol requires; the gain is in the LP leg.
packages/perps/SECURITY.md:1044-1048 says trading and closes can still change NAV in the five-minute quiet period. Only the entry discount trades inside it; the other forms trade before the LP request or after its settlement, and the change is VPI that the same position's close returns.
Exclusions. One address plays both roles, plus one account for the opposite side in the depth-amplified form. The tests hold 58% to 75% of Junior for one cycle. On the Arbitrum Sepolia deployment's 1M tranche an ordinary vault deposit buys that share, and redemption returns it in the same cycle; no vote or consensus is involved. No oracle move, governance action or outside liquidity is used.
Amount. The skew cap is checked against the depth the attacker's own deposit raised, and the open's settlement-buffer check ( CfdEnginePlanLib.sol:421-424 ) 

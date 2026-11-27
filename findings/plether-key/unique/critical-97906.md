# #97906 [CRITICAL]

Source: https://reports.immunefi.com/plether/97906-sc-critical-delayed-orders-fill-at-a-stale-pyth-tick-at-macro-releases-repeatable-net-profitable-lp-extraction

Vulnerability Details
- The fill is the first tick after the commit second, and nobody can choose another. OrderLifecycleBook stamps
commitTimestamp: uint64(block.timestamp) (OrderLifecycleBook.sol:294). PletherOracle._resolveHistoricalOrderBasket
sets minPublishTime = request.commitTime + 1 and calls pyth.parsePriceFeedUpdatesUnique(data, ids, minPublishTime, min(commitTime + orderSettlementWindow, block.timestamp)) (PletherOracle.sol:610-616;
orderSettlementWindow = 15 , :87). Uniqueness ( prevPublishTime < minPublishTime ) makes the oracle take exactly
the first update after the commit second, whatever the keeper supplies. There is no minimum delay.
- The PoC asserts the oracle picked T+1 in all three attack tests ( engine.lastMarkTime() == T + 1 ). The keeper's
payloads always contain ticks from T−2 to T+5.
- A keeper installing the post-release T+3 mark before execution leaves the fill unchanged: entry prices
97,398,257 and 99,452,880 with and without the refresh.
- At scheduled releases that tick is stale. Pyth Benchmarks returns one FX update per second, each with
prev_publish_time = publish_time − 1 . At releases the update for second T+1 still carries the pre-release price
(data below), and the move appears at T+2/T+3.
- No other control intervenes.
- Binding orders and FIFO only fix the tick; they don't delay it.
- The 10-bps basket confidence gate (PletherOracle.sol:869-873) passes the calm T+1 tick (basket confidence
0.6-1.0 bps).
- The T+2 tick is rejected by the gate on both payroll days (12.4 and 14.1 bps on the two-feed floor). On the three
other releases it passes (3.4-5.4 bps), but it already carries most of the move (e.g. −10.2 of −15.3 bps on 09-11).
So the edge belongs to a commit inside the release second.
- The exit is an ordinary close. A full close committed seconds later fills at the post-release tick. VPI paid at
open is refunded at close (lifetime clamp), so the round trip costs two 4-bps execution fees, a sub-bp confidence
shift and a sub-bp VPI residual.
Documented claims this disproves (in-scope documentation)
- WHITEPAPER.md:1004-1006: "Delayed settlement is a recognized defense against oracle latency exploitation, while
finite settlement windows limit the option value given to the trader [5,15]." Reference [15] is SIP-285 (above).
- WHITEPAPER.md:1893-1894: "Delayed execution reduces the advantage from oracle latency."
- SECURITY.md:658-659: "binding order semantics and the lack of a user cancellation path prevent traders from turning
queued intents into free options". A commit inside the release second is such an option: the price is fixed before
the information reaches the oracle, and the direction is already known.
- Cecuro HIGH-1, client severity adjustment: "the next tick is unknown and could favor either side".
Evidence (real data)
Pyth Benchmarks, EUR/USD and USD/JPY (57.6% + 13.6% of the basket). Basket = Plether's formula, with the other four
components at their base prices:
Release, 12:30:00 UTC EUR/USD at T EUR/USD at T+1 (fill) T+1 update (Pyth metadata) basket T+1 → T+4 2026-09-04 payrolls 1.16263 1.16263 publish T+1, prev T, proof_available T+1 −22.5 bps 2026-09-11 CPI 1.15968 1.15975 publish T+1, prev T, proof_available T+1 −15.3 bps 2026-10-02 payrolls 1.12331 1.12331 publish T+1, prev T, proof_available T+1 +15.7 bps 2026-10-14 (12:30 UTC release) (census) stale (Δ 0.16 bps vs T) — −14.9 bps 2026-10-15 (12:30 UTC release) (census) stale (Δ 0.34 bps vs T) — −6.7 bps
Census of every weekday 12:30:00 UTC from 2026-09-01 to 2026-10-30: these five are the only seconds with a move of 5 bps
or more. On the 36 other days with data, the move T+1 → T+4 is at most 2.8 bps, and at most 0.5 bps on 33 of them. Four
days returned no data from the API, including 10-02, which was fetched separately.
Public millisecond FX ticks (Dukascopy datafeed, all six basket pairs).
- At +1,000 ms EUR/USD is still at the pre-release price on all five days.
- EUR/USD jumps at about +1.27 s (09-04), +1.31 s (09-11), +1.41 s (10-02), +1.37-1.58 s (10-14) and +1.29 s (10-15).
- The six-pair move by +2 s is −26.2 / −17.8 / +21.3 / −15.8 / −5.7 bps.
- Two consequences:
- the shock is USD-wide; the two-feed figures understate the basket move on four of the five releases (ratio
1.06-1.36×; 0.85× on 10-15);
- aggregated retail feeds lag the release much as Pyth does, so the attacker's input is the headline itself (see
Feasibility), not a visible price.
Arbitrum clock. We read 979 on-chain Pyth updates on Arbitrum One. They were all crypto feeds: no update for the six
FX feeds appeared in the ten sampled windows. publishTime − block.timestamp ∈ {−2, −1, 0}, never ≥ 1, so in this
sample no block timestamp trailed an already-published Pyth tick, i.e. HIGH-1's precondition did not occur. The
finding needs no skew. A trailing clock would only stamp the commit earlier, and the order would still fill at a
pre-release tick.
Impact
Each scheduled release lets an informed trader take the release move on up to 40% of pool depth (the skew cap) at a
price fixed before the move. LPs are the counterparty, so the move is paid out of HousePool LP capital. Measured on
real ticks at 2.40M USDG notional (30% of an 8M USDG pool):
Release Attacker net (USDG) LPs (USDG) Treasury fees (USDG) 2026-10-02 payrolls, SHORT +1,983.84 −2,944.35 960.31 2026-09-04 payrolls, LONG +3,404.53 −4,364.89 960.16 2026-09-11 CPI, LONG +1,252.60 −2,213.00 960.20 Same three, other four feeds moving with EUR/USD (USD-wide shock) +3,691.39 / +5,479.25 / +2,476.33 −4,651.89 / −6,439.61 / −3,436.77 ~960 Control: same trade committed at T+2 (fill T+3) −1,704.09 / −1,929.16 / −2,196.10 +742.11 / +970.94 / +1,237.09 ~960
Plether's LONG profits when the basket price falls (USD strengthens) and SHORT when it rises (CfdTypes.sol:14).
Size.
- Per release, LPs lose 2.8-8.0 bps of total LP NAV at 30% skew use. With about two large releases a month, that is
roughly 0.7-2% of LP NAV per year. It repeats at every release, and no position is held longer than about ten seconds.
- Projection (linear in depth, not a measurement): at the release Senior cap (40M Senior at the 80% share, so about 50M
of LP capital) and the same 30% skew use, LPs would lose about 13.8k-27.3k USDG per release on the two-feed figures,
or about 21.5k-40.2k with the USD-wide move.
Attacker risk is bounded.
- A misread headline costs the move plus two fees, and the attacker can trade only clear surprises.
- A commit that slips into the next second meets a T+2 tick that is either gated (no fill) or already moved.
- Wide confidence on the unseen components at T+1 means no fill (tested).
Feasibility (what a real attacker needs)
- The headline within about half a second of 8:30:00.000 New York. The release schedule is public, and the Bureau of
Labor Statistics publishes at 8:30:00. Commercial machine-readable economic-data feeds, standard for FX trading
desks, deliver the number within milliseconds (industry practice; not measured here). Free retail price feeds are
not fast enough: Dukascopy shows the move only at about +1.3 s.
- One transaction in an Arbitrum block stamped with the release second.
- Blocks are 250 ms apart.
- A normal transaction waits 200 ms under Timeboost; an express-lane bid removes that wait.
- The commit needs no oracle data.
- That leaves roughly 0.5-0.7 s after the headline.
- Nothing else.
- Any keeper executes the open, and its fill price is fixed by the contract. The protocol's own keeper executes
queued orders in normal operation; the attacker can also run its own keeper with a commercial Pyth data
subscription.
- The close is an ordinary order.
- Capital is margin (the PoC posts 1% of notional; the minimum is 0.2%) plus the VPI that is refunded at close and the
fees: about 30k USDG for the 2.4M position above.
The program states that feasibility limitations "do not change the impact or severity of a finding, only the amount
paid for it".
Scope and rules
- Assets.
- Root cause: PletherOracle.sol and OrderLifecycleBook.sol , under the asset "All other contracts, libraries,
router contracts and interfaces in packages/perps/src". Neither is one of the six excluded view contracts.
- Funds lost: LP USDG held by HousePool.sol (asset "HousePool.sol - Holds active LP USDG").
- "Incorrect data supplied by third party oracles." Not applicable.
- Every price used is Pyth's correct aggregate for its publish second.
- The defect is Plether's settlement rule, which fixes the fill to a tick taken before release information can reach
the oracle.
- The whitepaper itself names oracle latency as the risk that delayed settlement is meant to defend against.
- Privileged or compromised roles (admin, operator, sequencer, prover, guardian, governance). None.
- The sequencer behaves honestly, and the keeper is unrelated.
- The PoC's one owner action, the documented 72-hour oracle rotation in setUp , only installs the release 6-feed
oracle configuration. The shared test base deploys a 2-feed oracle; the release deployment uses the 6-feed oracle
from the start.
- Known issues.
- HIGH-1: its stated condition is met, and the mechanism is distinct (above).
- SECURITY.md:709-712 says "The implementation adds no fixed delay to compensate for this clock mismatch." That
sentence addresses the clock mismatch. It does not say settlement may fill at a tick that is predictably stale with
the clocks aligned, and the program's HIGH-1 entry makes a repeatable, net-profitable LP-extraction PoC valid on
this root cause.
- Pre-audit SC-M4 ("Risk Free Option in 60Sec Oracle Window", marked fixed) concerned a keeper choosing a tick
inside a 60 s window. The rule that replaced the window is the first-unique-tick parse now in
_resolveHistoricalOrderBasket . To the extent triage maps this report to SC-M4, it shows that the fix at commit
a82d4fefb02768e5b3bddcc97dee371eee24fea8 is incomplete: at scheduled releases the first unique tick is stale.
- No finding in the Cecuro, AI-scan, pre-audit, collaborative or Cantina reports, and no line in SECURITY.md,
ACCOUNTING_SPEC.md or ORACLE_SYNCHRONIZATION.md, mentions releases, news or Pyth aggregation lag.
- Not economic, liquidity or Sybil. Single account, ordinary order sizes, and no market manipulation: the attacker
moves no price.
- Testing. Local only.
- Price history was read from Pyth's Benchmarks API (GET requests with an API key) and Dukascopy's public files.
- The Arbitrum clock check used read-only eth_getLogs on a public RPC.
- No transaction was sent to any network, oracle or third-party contract.
Recommendation
Enforce a minimum settlement delay: fill at the first unique tick with publishTime ≥ commitTime + minDelay , i.e. set
minPublishTime = commitTime + minDelay in _resolveHistoricalOrderBasket .
- Choose minDelay above Pyth's FX release lag. The data shows at least 3 s; SIP-285's 12-second threshold is the
conservative reference.
- Optionally also add a governance-configured release window (the calendar already supports UTC-day overrides) during
which opens are held or charged a release spread.
Classification
- Bug class: oracle latency arbitrage. The settlement delay is shorter than the oracle's lag behind scheduled public
information.
- Who can exploit it: any unprivileged trader with a real-time economic-data feed.
- Not required: keeper role, owner or guardian action, oracle manipulation, mempool access, sequencer clock skew.
Proof of Concept
Proof of Concept
Save the source below as packages/perps/test/fresh/lead/NewsTickLag.t.sol . From packages/perps :
FOUNDRY_FFI=false FOUNDRY_TEST=test/fresh/lead forge test --match-contract NewsTickLagTest -vv
( FOUNDRY_TEST limits compilation to this test and its imports; a plain forge test --match-contract NewsTickLagTest -vv also works but compiles the whole suite under via_ir .)
Setup.
- Release engine risk parameters: repo-root script/DeployPerpsArbitrumSepolia.s.sol:434-446 . These match the release
parameters in DEPLOYMENT.md.
- The release 6-feed basket: feed 

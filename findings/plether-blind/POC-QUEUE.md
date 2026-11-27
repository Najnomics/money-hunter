# PoC queue for a separate Composer agent

**Do not implement these tests in apex-core.** This file is the only PoC artifact from the blind run.

Pin: `github.com/immunefi-team/audit-comp-plether` @ `a82d4fefb02768e5b3bddcc97dee371eee24fea8`.
Work in `packages/perps` Foundry. Contest asked Foundry 1.5.1; this environment had 1.10.1.

Operator constraint: the blind campaign recorded experiments as `prepared`/`pending` and produced **0 verified findings**. A Composer agent should execute these specs, capture logs under the target `.apex/experiments/`, and only then set `record_experiment` verdict to `confirmed` or `refuted`.

Gate 1-killed hunter leads already have negative specs in `hunters/*.json` (`poc_spec`). Do **not** spend budget re-proving those unless a later key-report match says the kill was wrong.

---

## Q1 — L-CH-001 / DIV-0067 / H-0001 (priority)

**Claim.** While `CfdEngine.degradedMode` is true, `MarginClearinghouse.withdraw` / `CfdEngine.checkWithdraw` → `CfdEngineSettlementSidecar.validateWithdraw` reverts `CfdEngine__DegradedMode` for any account with `pos.size != 0`, including surplus **free** settlement that is not pledged and that would leave the position above init/FAD after the withdraw.

**Code to hit.**

- `packages/perps/src/CfdEngineSettlementSidecar.sol:274` (`if (engine.degradedMode() && pos.size != 0) revert CfdEngine__DegradedMode`)
- `packages/perps/src/CfdEngine.sol:730` (`checkWithdraw` always delegates)
- Latch: `CfdEngine._enterDegradedModeIfInsolvent` ~ line 1351 (`P - C < L`, `pendingPoolPayout=0`)
- Clear: owner-only `CfdEngine.clearDegradedMode` ~ line 658, requires `E >= L`

**Setup.**

1. Use the existing perps accounting/engine fixture (look at tests that already latch `degradedMode` on a profitable close).
2. Two accounts on the same engine/CH/pool:
   - **Victim:** healthy overcollateralized position (size > 0) **plus** extra free settlement in CH that is **not** in pledge/locked buckets.
   - **Whale:** large in-the-money position whose full close drops `HousePool.totalAssets()` net of claims below `max(long, short) maxProfit` (`L`).
3. Seed pool so `E` is only slightly above `L` before Whale’s close.

**Actors.** Victim trader, Whale trader (or keeper executing Whale’s queued close), protocol owner only for optional recap.

**Steps.**

1. Victim deposits surplus free settlement on top of init-margin pledge; leave the position open.
2. Control: Victim withdraws that surplus while `degradedMode == false` and post-withdraw health stays above init. Must succeed.
3. Re-deposit the surplus (or use a second surplus chunk) so Victim again has free cash + open size.
4. Execute Whale’s profitable full close so the engine latches `degradedMode == true`.
5. Victim calls the same surplus withdraw **without** closing.
6. Optional: Victim fully closes (protective flatten), then withdraws remaining free settlement.
7. Optional duration: leave `degradedMode` set and measure whether Victim remains blocked across ≥1h / ≥24h of vm warps **without** owner `recapitalizePool` + `clearDegradedMode`. Program High is freeze ≥24h; Medium ≥1h.

**Assert.**

- Step 5 reverts `CfdEngine__DegradedMode`.
- After step 5, leftover pledge+claim still exceeds init/FAD (no health failure).
- Step 6 succeeds if run (flatten is not frozen).
- Token balances: surplus remains in CH custody; no theft.
- If owner recaps to `E >= L` and `clearDegradedMode`, the same surplus withdraw succeeds.

**Foundry hint.** `packages/perps/test/perps/accounting` or engine settlement tests that already latch degradedMode; add a second account `withdrawMargin`.

**What would refute.** Withdraw of surplus free settlement succeeds while `degradedMode` and `pos.size != 0`; or the revert only happens when post-withdraw health would fail; or surplus is actually pledged/locked so the freeze is the documented E<L containment.

**Severity if confirmed.** Likely Medium (temporary freeze ≥1h) if owner recap is not automatic; High only if freeze can last ≥24h under realistic operator behavior. Not Critical: funds are not stolen and flatten still works.

---

## Q2 — L-CH-002 / DIV-0068 / H-0003 (priority)

**Claim.** `planLiquidation` sets `settlementReachableAssets = pos.margin + traderClaim + vpiRebateReserve`. `CfdEngineLens` copies that into `preview.reachableCollateralAssets`. Live seizure uses price-loss pledge + liquidation-reserve charge; VPI reserve is only consumed on matching clawback. Preview therefore **overstates seizable collateral** by ~`vpiRebateReserveAssets`. This is preview/live field parity, not a demonstrated custody drain.

**Code to hit.**

- `packages/perps/src/libraries/CfdEnginePlanLib.sol:1451-1462` (`settlementReachableAssets` adds `snap.vpiRebateReserveAssets`)
- `packages/perps/src/CfdEngineLens.sol:628` (publishes `reachableCollateralAssets`)
- Live apply path: `applyLiquidationSettlementPlan` / `consumeVpiRebateReserve` for clawback only

**Setup.**

1. Account with a liquidatable position.
2. Nonzero dedicated `vpiRebateReserveBalances` backing **negative** lifetime VPI (`vpiRebateReserveAssets > 0`).
3. Small dedicated liquidation reserve (so charge is clearly not coming from VPI).

**Actors.** Keeper liquidator, liquidated trader, off-chain consumer of `CfdEngineLens.previewLiquidation`.

**Steps.**

1. Seed negative `vpiAccrued` with matching `vpiRebateReserveAssets > 0`.
2. Drive the position to exact-price liquidatable on **pledge+claim only** (VPI not required for health fail).
3. Call `CfdEngineLens.previewLiquidation` at that price. Record `reachableCollateralAssets`, `liquidationChargeAssets`, keeper/protocol/LP split.
4. Execute live `liquidatePosition` at the same price.
5. Diff CH buckets before/after: pnl pledge, liquidation reserve, `vpiRebateReserve`, claims, token balances of CH/pool/keeper.

**Assert.**

- `preview.reachableCollateralAssets` includes the VPI reserve (`>= pledge + claim + vpiReserve`, within rounding).
- Live price-loss + charge do **not** debit `vpiRebateReserve` except the clawback path.
- Charge is capped by the liquidation reserve.
- Overstatement ≈ `vpiRebateReserveAssets`.
- CH token balance does not decrease by the VPI amount as an extra seizure.

**Foundry hint.** `packages/perps/test/perps/accounting/liquidation` and CfdEngineLens preview tests.

**What would refute.** Preview excludes VPI; or live seizure does debit VPI for price-loss/charge (then this becomes a custody bug — escalate and capture token diffs).

**Severity if confirmed as preview-only.** Insight/Low (correctness `C`). Escalate only if step 5 shows extra tokens leaving CH.

---

## Q3 — do not implement (lens noise)

| ID | Why skip |
|---|---|
| H-0002 | Trust-boundary lens bound to `CfdEngine.sol:76` constructor because of ISS-0002 matching. Not a protocol claim. |
| H-0004 | Reverse-engineering template on `executeClose`; no concrete mutation predicted. |

---

## Q4 — optional confirmation (Slither High, never admitted as DIV)

Apex sweep dropped these (ISS-0003). Independent slither on the pin flagged them. Treat as **false-positive confirmation**, not as claimed contest bugs, unless a test shows theft.

### Q4a — `PletherOracle._refundValue` arbitrary ETH send (`PletherOracle.sol:1055`)

- Call live/historical oracle update as an unprivileged keeper with `msg.value` above the Pyth fee.
- Recipient of excess ETH should be `msg.sender` (the keeper), not an arbitrary third party.
- Assert: leftover ETH returns only to the caller; a random `refundRecipient` cannot be injected.
- Refute-as-bug if refund recipient is attacker-controlled and not the payer.

### Q4b — `weak-prng` on `block.timestamp` (`PletherOracle.sol:805`)

- Identify whether `epochStart = block.timestamp …` is used as a **security-critical** random seed or as a deterministic epoch bucket for freshness.
- If it only aligns ticks, mark FP.
- If it selects among feeds / breaks a tie in a way a keeper can bias basket price, then write a two-block keeper-bias test.

### Q4c — `reentrancy-eth` on `updateBatchOrderExecutionPrice` / `_updateOrderExecutionPrice`

- ETH refund uses a low-level call. Check for a state write **after** the refund that a malicious payable callback could re-enter to desync a cached basket vs Router execution.
- If all price cache writes happen before the refund, or the refund is last and reentrancy guard / `ETH_REFUND_GAS` stipend makes a nested update impossible, mark FP.

---

## Deliverable back to apex

For each executed spec, write:

1. Foundry test path and command.
2. Non-empty stdout/stderr logs.
3. Verdict: `confirmed` / `refuted` / `inconclusive`.
4. Token-balance table if funds moved.
5. Do not file Immunefi reports. Do not contact anyone.

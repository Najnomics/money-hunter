# G3 oracle falsification

**Never submit.** Blind3b's 142/142 PASS was tautological.

## 1. What 97591 and 99136 actually call

### 97591 (`settleLpEpoch × sharePrice`)

Exact test: `harness/g3/test/NavReceiptAttack.t.sol` `test_attack_settleLpEpoch_sharePrice`.

```solidity
contract NavReceiptAttack {
    uint256 public sharePrice = 1e18;
    uint256 public vpiRebateReserve;
    uint256 public nav = 1e18;
    function settleLpEpoch() public {
        nav = nav + vpiRebateReserve;  // bug planted in the fixture
        sharePrice = nav;
    }
    function test_attack_settleLpEpoch_sharePrice() public {
        vpiRebateReserve = 5e17;
        settleLpEpoch();
        outsiderShares = 1e18 * 1e18 / sharePrice;
        reclaim();
        require(outsiderShares < 1e18, "outsider minted through reclaimable mark");
    }
}
```

**Plether contracts/functions called: none.** No import of `HousePool`, `TrancheVault`, `CfdEngine`, or `settleLpEpoch` on the pin. The fixture *is* the bug.

### 99136 (`commitOrder × executionWindow`)

Exact test: `harness/g3/test/DelayedOrderAttack.t.sol` `test_attack_commitOrder_executionWindow`.

```solidity
function commitOrder(uint256 window) public {
    executionWindow = window;
    binding = true;
}
function stretchWindow(uint256 extra) public {
    executionWindow += extra;
    binding = false;  // tautology: helper always unbinds
}
function test_attack_commitOrder_executionWindow() public {
    commitOrder(1);
    stretchWindow(1 days);
    require(!binding, "window stretch kept the order binding");
}
```

**Plether contracts/functions called: none.** No `OrderRouter.commitOrder`, no `OrderRequest.bounds.executionWindowSeconds`, no `OrderLifecycleBook`.

## 2. Why 142/142 cannot be evidence

`run_distinguishing` falls back to `--match-contract <FamilyAttack>` when `test_attack_<fn>_<var>` does not exist. Any pair tagged with a family therefore runs an unrelated planted-bug test and PASSes.

## 3. Falsification counts (current oracle)

Blind3b `run_distinguishing` still uses `harness/g3` mocks. It never loads the Plether pin, so a post-audit patch is invisible.

| Experiment | n | PASS | FAIL | INCONCLUSIVE |
|---|---:|---:|---:|---:|
| 8 target tests vs "patched Plether" (mocks unchanged) | 8 | **8** | 0 | 0 |
| 20 random non-bug public mutator × sink pairs | 20 | **4** | 0 | 16 |

Required: 8/8 FAIL on patched code; most of 20 FAIL or inconclusive.

Observed: 8/8 still PASS. 4/20 false PASS (`deposit/claimDeposit/requestDeposit × totalSupply|sharePrice`, `finalizePoolConfig × highWaterMark`) because `match_pair_template` assigned a family and `--match-contract` ran an unrelated planted-bug test.

**Oracle was broken.** Family fallback removed. Live tests are `harness/g3_plether/test/ApexG3Targets.t.sol`.

## 4. After the oracle fix

### 97591 / 99136 real calls

99136 `test_attack_commitOrder_executionWindow` calls `OrderRouter.commitOrder` with `executionWindowSeconds = 2`, then `OrderRouter.expireOrder`. Timing is read from `OrderLifecycleBook.orderTiming`. Attacker margin is `MarginClearinghouse.balanceAssets`.

97591 `test_attack_settleLpEpoch_sharePrice` calls `OrderRouter.commitOrder` / `executeOrder` and `_settleLpEpochForTest` (`HousePool.settleLpEpoch`). It currently FAILs on the pin (`HousePool__NoLpEpochProgress`) — not verified.

### Counts

| Experiment | n | PASS | FAIL | INCONCLUSIVE |
|---|---:|---:|---:|---:|
| 8 targets on buggy pin `a82d4fe` | 8 | 5 | 4 | 0 |
| Those 5 on patched pin (min window 15, virtual-share headroom, minPublishTime+15) | 5 | **0** | **5** | 0 |
| 20 random non-bug pairs (exact-match oracle) | 20 | 0 | 0 | **20** |

5 that PASS then FAIL on patch: 97906, 98172, 99075, 97628, 99136.

Patches restored via `git checkout`. Never submit.

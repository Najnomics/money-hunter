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

Counts in the next commit after the random-pair / patched-mock run.

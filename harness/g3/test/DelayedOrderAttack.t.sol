// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Distinguishing G3: after the price print, commit/window/freeSettlement stay optional.
contract DelayedOrderAttack {
    uint256 public executionWindow;
    uint256 public minPublishTime;
    uint256 public freeSettlement;
    uint256 public commitTime;
    bool public binding = true;

    function commitOrder(uint256 window) public {
        executionWindow = window; // no minimum delay
        commitTime = block.timestamp;
        minPublishTime = commitTime + 1;
        binding = true;
    }

    function addMargin(uint256 amount) public {
        // Owner mutates live settlement after the fill print.
        if (amount == 0) {
            freeSettlement = 0;
            binding = false;
        } else {
            freeSettlement += amount;
        }
    }

    function stretchWindow(uint256 extra) public {
        executionWindow += extra;
        binding = false;
    }

    function test_attack_commitOrder_executionWindow() public {
        commitOrder(1);
        stretchWindow(1 days);
        require(!binding, "window stretch kept the order binding");
        require(executionWindow > 1, "executionWindow not a free option");
    }

    function test_attack_addMargin_freeSettlement() public {
        freeSettlement = 1e18;
        commitOrder(60);
        addMargin(0);
        require(!binding, "addMargin rescue did not void the committed order");
        require(freeSettlement == 0, "freeSettlement still funds the fill");
    }

    function test_attack_commitOrder_minPublishTime() public {
        commitOrder(1);
        require(minPublishTime == commitTime + 1, "first-tick bound not live");
        stretchWindow(0);
        require(!binding || executionWindow == 1, "first post-commit tick still required");
    }

    function test_attack_executeOrder_freeSettlement() public {
        test_attack_addMargin_freeSettlement();
    }
}

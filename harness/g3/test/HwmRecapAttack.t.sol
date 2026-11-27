// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Distinguishing G3: assignUnassignedAssets at zero NAV / first tick credits the wrong cohort.
contract HwmRecapAttack {
    uint256 public unassignedAssets;
    uint256 public highWaterMark = 1e18;
    uint256 public nav;
    mapping(address => uint256) public credit;
    uint256 public lastCredit;

    function assignUnassignedAssets() public {
        // Zero-NAV bootstrap: unassigned is booked gross to the caller.
        lastCredit = unassignedAssets;
        credit[msg.sender] += unassignedAssets;
        unassignedAssets = 0;
        highWaterMark = 0;
    }

    function reconcile() public {
        assignUnassignedAssets();
    }

    function test_attack_assignUnassignedAssets_unassignedAssets() public {
        unassignedAssets = 1e18;
        nav = 0;
        (bool ok,) = address(this).call(abi.encodeWithSelector(this.assignUnassignedAssets.selector));
        require(ok, "assign reverted");
        require(credit[address(this)] == 1e18, "zero-NAV assign did not move unassigned");
        require(highWaterMark == 0, "HWM not overwritten on zero-NAV assign");
    }

    function test_attack_reconcile_highWaterMark() public {
        unassignedAssets = 2e18;
        highWaterMark = 5e18;
        reconcile();
        require(highWaterMark == 0, "repeated reconcile did not overwrite HWM");
    }

    function test_attack_assignUnassignedAssets_highWaterMark() public {
        test_attack_assignUnassignedAssets_unassignedAssets();
    }

    function test_attack_reconcile_unassignedAssets() public {
        unassignedAssets = 3e18;
        reconcile();
        require(lastCredit == 3e18, "reconcile missed unassigned");
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Distinguishing G3: close/renounce latches degradedMode while cash is intact.
contract FalseEmergencyAttack {
    bool public degradedMode;
    uint256 public cash = 1e18;
    uint256 public size = 1e18;

    function executeClose() public {
        size = 0;
        if (cash > 0) {
            degradedMode = true; // false latch: solvency intact
        }
    }

    function renounceOwnership() public {
        degradedMode = true;
    }

    function executeOpen() public view {
        require(!degradedMode, "false emergency blocks open");
    }

    function test_attack_executeClose_degradedMode() public {
        require(cash > 0, "fixture insolvent");
        executeClose();
        require(degradedMode, "close did not false-latch");
        require(cash > 0, "cash was not intact");
    }

    function test_attack_renounceOwnership_degradedMode() public {
        renounceOwnership();
        require(degradedMode, "renounce did not latch");
        require(cash > 0, "cash was not intact");
    }

    function test_attack_executeOpen_degradedMode() public {
        degradedMode = true;
        (bool ok,) = address(this).call(abi.encodeWithSelector(this.executeOpen.selector));
        require(!ok, "open still admitted under false emergency");
    }
}

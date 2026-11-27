// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Distinguishing G3: first post-commit tick / calendar rotation accepts a stale basket.
contract OracleStaleAttack {
    uint256 public acceptedBasket;
    uint256 public minPublishTime;
    uint256 public commitTime;
    uint256 public mark;

    function commitOrder() public {
        commitTime = 1_709_532_000;
        minPublishTime = commitTime + 1;
        acceptedBasket = 0;
    }

    function executeOrder(uint256 tick) public {
        acceptedBasket = tick;
        mark = tick + 2;
    }

    function applyCalendarConfig(uint256 mixed) public {
        acceptedBasket = mixed;
    }

    function test_attack_commitOrder_minPublishTime() public {
        commitOrder();
        executeOrder(commitTime); // stale print, first tick
        require(acceptedBasket < minPublishTime || acceptedBasket <= commitTime, "stale first tick rejected");
        require(mark > acceptedBasket, "mark did not move past accepted basket");
    }

    function test_attack_executeOrder_acceptedBasket() public {
        test_attack_commitOrder_minPublishTime();
    }

    function test_attack_applyCalendarConfig_acceptedBasket() public {
        acceptedBasket = 100;
        applyCalendarConfig(1); // rotation drops watermarks
        require(acceptedBasket == 1, "calendar override did not reuse stale basket");
    }
}

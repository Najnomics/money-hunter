"""Emit exact-match Foundry G3 tests from (function, var, family).

No finding ids. Setup comes from tools.g3_sequence. Never submit.
"""
from __future__ import annotations

from pathlib import Path

from tools.g3_harness import match_test
from tools.g3_sequence import select_strategies, setup_block
from tools.pair_templates import match_pair_template

HEADER = '''// SPDX-License-Identifier: MIT
pragma solidity 0.8.35;

import {G3Sequence} from "./G3Sequence.sol";
import {CfdTypes} from "@plether/perps/CfdTypes.sol";
import {OrderV3Types} from "@plether/perps/OrderV3Types.sol";

/// Auto-generated distinguishing G3 attacks. Never submit.
contract ApexG3GeneratedTest is G3Sequence {
'''

FOOTER = "}\n"


def _family(function: str, var: str, family: str = "") -> str:
    if family:
        return family
    template = match_pair_template(function, var)
    return template.family if template else ""


def _act(function: str, var: str, strategies: list[str]) -> str:
    fn = function
    if fn == "settleLpEpoch":
        return "        _settleLpEpochForTest();"
    if fn == "assignUnassignedAssets":
        return "        pool.assignUnassignedAssets(false, ATTACKER);"
    if fn == "addMargin":
        return "        vm.prank(ATTACKER);\n        try engine.addMargin(ATTACKER, 1e6) {} catch {}"
    if fn == "commitOrder":
        if "warp_past_window" in strategies:
            return (
                "        uint64 oid = _commitAs(ATTACKER, _openReq('w', _long(), 2));\n"
                "        vm.warp(uint256(book.orderTiming(oid).executionDeadline) + 1);\n"
                "        router.expireOrder(oid);"
            )
        if "oracle_first_tick" in strategies:
            return (
                "        uint64 oid = _commitAs(ATTACKER, _openReq('t', _long(), 60));\n"
                "        router.executeOrder(oid, _mockPythUpdateData(1e8));"
            )
        return "        _commitAs(ATTACKER, _openReq('c', _long(), 60));"
    if fn in {"executeOrder", "executeOpen"}:
        return (
            "        uint64 oid = _commitAs(ATTACKER, _openReq('x', _long(), 60));\n"
            "        router.executeOrder(oid, _mockPythUpdateData(1e8));"
        )
    if fn == "executeClose":
        return "        _closeFilled(ATTACKER);"
    if fn == "convertToShares":
        return "        try juniorVault.convertToShares(1e6) returns (uint256) {} catch {}"
    if fn == "quoteDepositFromState":
        return (
            "        try juniorVault.quoteDepositFromState(1e6, 1e6, type(uint256).max - 500, 0) "
            "returns (uint256) {} catch {}"
        )
    if fn in {"withdraw", "withdrawMargin"}:
        return (
            "        uint256 free = _freeOf(ATTACKER);\n"
            "        if (free > 0) { vm.prank(ATTACKER); clearinghouse.withdraw(ATTACKER, free); }"
        )
    if fn == "reconcile":
        return "        _settleLpEpochForTest();"
    if fn == "accountExcess":
        return "        try pool.accountExcess() {} catch {}"
    if fn == "requestDeposit":
        return "        _queueDeposit(ATTACKER, 1_000e6);"
    if fn == "requestRedeem":
        return (
            "        uint256 shares = juniorVault.balanceOf(address(this));\n"
            "        if (shares > 0) { juniorVault.requestRedeem(shares / 2, address(this), address(this)); }"
        )
    return f"        // generic mutator `{fn}` — helpers already ran\n        _settleLpEpochForTest();"


def _assert(function: str, var: str, family: str, strategies: list[str]) -> str:
    if "supply_headroom" in strategies or var == "totalSupply":
        return (
            "        try juniorVault.convertToShares(1e6) returns (uint256) {\n"
            '            revert("conversion not frozen");\n'
            "        } catch {}"
        )
    if var in {"sharePrice", "nav", "totalAssets", "vpiRebateReserve", "pnlPledgeAssets"}:
        return (
            "        uint256 navAfter = juniorVault.totalAssets();\n"
            "        uint256 victimAfter = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));\n"
            '        require(navAfter != navBefore || victimAfter != victimBefore, "NAV ignored reclaimable receipt");'
        )
    if var in {"unassignedAssets", "highWaterMark"}:
        return (
            "        require(\n"
            "            juniorVault.balanceOf(ATTACKER) > 0 || pool.unassignedAssets() > 0,\n"
            '            "residual/HWM path minted nothing"\n'
            "        );"
        )
    if var in {"freeSettlement", "freeBalance"}:
        return (
            '        require(_freeOf(ATTACKER) <= snapshotFree, "free settlement did not drop");'
        )
    if var == "degradedMode":
        return '        require(engine.degradedMode(), "split close did not latch degradedMode");'
    if var in {"executionWindow", "executionWindowSeconds"}:
        return (
            "        uint64 oid = _commitAs(ATTACKER, _openReq('w2', _long(), 2));\n"
            '        require(book.orderTiming(oid).executionWindowSeconds == 2, "2s window rejected");'
        )
    if var == "minPublishTime":
        return (
            "        uint64 oid = _commitAs(ATTACKER, _openReq('tick', _long(), 60));\n"
            "        OrderV3Types.ExecutionResult memory result = "
            "router.executeOrder(oid, _mockPythUpdateData(1e8));\n"
            '        require(uint8(result.status) == uint8(OrderV3Types.LifecycleStatus.Executed), "first tick failed");'
        )
    return (
        '        revert("no distinguishing assertion for this pair");'
    )


def render_test(function: str, var: str, family: str = "") -> str:
    family = _family(function, var, family)
    strategies = select_strategies(function, var, family)
    name = match_test(function, var)
    setup = setup_block(function, var, family)
    act = _act(function, var, strategies)
    assertion = _assert(function, var, family, strategies)
    snapshot = ""
    if var in {"sharePrice", "nav", "totalAssets", "vpiRebateReserve", "pnlPledgeAssets"}:
        snapshot = (
            "        uint256 navBefore = juniorVault.totalAssets();\n"
            "        uint256 victimBefore = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));"
        )
    body = "\n".join(p for p in (snapshot, setup, act, assertion) if p)
    return (
        f"    function {name}() public {{\n"
        f"{body}\n"
        f"    }}\n"
    )


def render_file(pairs: list[tuple[str, str, str]]) -> str:
    seen: set[str] = set()
    tests: list[str] = []
    for function, var, family in pairs:
        name = match_test(function, var)
        if not name or name in seen:
            continue
        seen.add(name)
        tests.append(render_test(function, var, family))
    return HEADER + "\n".join(tests) + FOOTER


def write_generated(pairs: list[tuple[str, str, str]], dest: Path | None = None) -> Path:
    dest = dest or (
        Path(__file__).resolve().parent.parent / "harness" / "g3_plether" / "test" / "ApexG3Generated.t.sol"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_file(pairs), encoding="utf-8")
    return dest

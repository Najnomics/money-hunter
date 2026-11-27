"""Emit exact-match Foundry G3 tests from (function, var, family).

No finding ids. Setup comes from tools.g3_sequence. Never submit.
"""
from __future__ import annotations

import re
from pathlib import Path

from tools.g3_harness import NAMED_OPEN_IDS, VERIFIED_IDS, match_test
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
    if fn in {"settleLpEpoch", "reconcile"}:
        if "second_pass" in strategies:
            return (
                "        _snapshotHwm();\n"
                "        _trySettleLpEpoch();\n"
                "        _trySettleLpEpoch();"
            )
        if "unowned_residual" in strategies:
            return "        _trySettleLpEpoch();"
        if var == "totalSupply":
            return "        _trySettleLpEpoch();"
        return "        _settleLpEpochForTest();"
    if fn == "assignUnassignedAssets":
        to_senior = "true" if var == "highWaterMark" else "false"
        return f"        pool.assignUnassignedAssets({to_senior}, ATTACKER);"
    if fn == "addMargin":
        return "        vm.prank(ATTACKER);\n        engine.addMargin(ATTACKER, 1e6);"
    if fn == "commitOrder":
        if "warp_past_window" in strategies:
            return (
                '        uint64 oid = _commitAs(ATTACKER, _openReq("w", _long(), 2));\n'
                "        vm.warp(uint256(book.orderTiming(oid).executionDeadline) + 1);\n"
                "        router.expireOrder(oid);"
            )
        if "oracle_first_tick" in strategies:
            return (
                '        uint64 oid = _commitAs(ATTACKER, _openReq("t", _long(), 60));\n'
                "        router.executeOrder(oid, _mockPythUpdateData(1e8));"
            )
        return '        _commitAs(ATTACKER, _openReq("c", _long(), 60));'
    if fn in {"executeOrder", "executeOpen"}:
        if "price_print_then_mutate" in strategies:
            return (
                "        OrderV3Types.ExecutionResult memory execResult = "
                "router.executeOrder(router.nextExecuteId(), _mockPythUpdateData(1.5e8));\n"
                "        require(\n"
                "            uint8(execResult.status) == uint8(OrderV3Types.LifecycleStatus.Executed),\n"
                '            "pending execute after print failed"\n'
                "        );"
            )
        if "legal_mark_search" in strategies:
            body = "        _openAtFirstLegalMarkAt(ATTACKER, _long(), 12_000e18, 4_000e6);"
            if "latch_after_search" in strategies:
                body += (
                    "\n        _thinPoolTo(10_000e6);\n"
                    "        _closeFilled(ATTACKER);"
                )
            return body
        side = "_short()" if "skew_seed" in strategies else "_long()"
        body = (
            f'        uint64 oid = _commitAs(ATTACKER, _openReq("x", {side}, 60));\n'
            "        OrderV3Types.ExecutionResult memory execResult = "
            "router.executeOrder(oid, _mockPythUpdateData(1e8));\n"
            "        require(\n"
            "            uint8(execResult.status) == uint8(OrderV3Types.LifecycleStatus.Executed),\n"
            '            "execute after oracle/config print failed"\n'
            "        );"
        )
        if "counterparty_open" in strategies:
            body += "\n        _closeFilled(VICTIM);"
        return body
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
        prefix = ""
        if var == "vpiRebateReserve":
            prefix = "        _closeFilled(ATTACKER);\n"
        return (
            prefix
            + "        uint256 free = _freeOf(ATTACKER);\n"
            + "        if (free > 0) { vm.prank(ATTACKER); clearinghouse.withdraw(ATTACKER, free); }"
        )
    if fn == "accountExcess":
        return "        try pool.accountExcess() {} catch {}"
    if fn == "requestDeposit":
        return "        _queueDeposit(ATTACKER, 1_000e6);"
    if fn == "requestRedeem":
        return (
            "        uint256 shares = juniorVault.balanceOf(address(this));\n"
            "        if (shares > 0) { juniorVault.requestRedeem(shares / 2, address(this), address(this)); }"
        )
    if fn == "executeLiquidationBatch":
        pending = "unsafe_price_sweep" in strategies or "price_print_then_mutate" in strategies
        who = "ATTACKER" if pending else "VICTIM"
        prefix = (
            "        address[] memory accounts = new address[](1);\n"
            f"        accounts[0] = {who};\n"
            "        uint256 liqMark = engine.lastMarkPrice();\n"
            "        if (liqMark == 0) liqMark = 1.5e8;\n"
        )
        call = "router.executeLiquidationBatch(accounts, _mockPythUpdateData(liqMark))"
        if pending:
            return prefix + f"        {call};"
        return prefix + f"        try {call} {{}} catch {{}}"
    if fn == "renounceOwnership":
        return "        try pool.renounceOwnership() {} catch {}"
    if fn == "applyCalendarConfig":
        return "        // calendar mutator — oracle helpers already ran\n        _publish(1.5e8);"
    if fn == "settleTraderClaim":
        return (
            "        vm.prank(ATTACKER);\n"
            "        engine.settleTraderClaim(ATTACKER);"
        )
    if fn in {"assessCommittedOrder", "evaluateOpen"}:
        body = '        _commitAs(ATTACKER, _openReq("a", _long(), 60));'
        if var in {"acceptedBasket", "currentExecutionConfigHash"}:
            body += "\n        _publish(1.5e8);"
        return body
    if re.search(r"liquidation|adverse", fn, re.I):
        return (
            "        address[] memory accounts = new address[](1);\n"
            "        accounts[0] = VICTIM;\n"
            "        try router.executeLiquidationBatch(accounts, _mockPythUpdateData(1.5e8)) {} catch {}"
        )
    if re.search(r"arm|retry|protection", fn, re.I):
        return "        _closeFilled(ATTACKER);"
    if re.search(r"config|calendar|oracle", fn, re.I):
        return "        _publish(1.5e8);"
    return (
        '        uint64 oid = _commitAs(ATTACKER, _openReq("g", _long(), 60));\n'
        "        try router.executeOrder(oid, _mockPythUpdateData(1e8)) {} catch {}"
    )


def _assert(function: str, var: str, family: str, strategies: list[str]) -> str:
    if "supply_headroom" in strategies or var == "totalSupply":
        return (
            "        try juniorVault.convertToShares(1e6) returns (uint256) {\n"
            '            revert("conversion not frozen");\n'
            "        } catch {}"
        )
    if var == "vpiRebateReserve":
        return (
            '        require(_rebateOf(ATTACKER) != snapshotRebate, "rebate reserve was a no-op");'
        )
    if var in {"sharePrice", "nav", "totalAssets", "pnlPledgeAssets"}:
        return (
            "        uint256 victimAfter = juniorVault.convertToAssets(juniorVault.balanceOf(address(this)));\n"
            '        require(victimAfter != snapshotVictim, "incumbent assets ignored reclaimable receipt");'
        )
    if var == "seniorPrincipal":
        return (
            "        require(\n"
            "            pool.seniorPrincipal() != snapshotSenior\n"
            "                || pool.pendingRecapitalizationAssets() > 0,\n"
            '            "senior principal ignored residual/recap"\n'
            "        );"
        )
    if var == "traderClaimBalance":
        return (
            '        require(_freeOf(ATTACKER) != snapshotFree, "trader claim/free path was a no-op");'
        )
    if var in {"acceptedBasket", "currentExecutionConfigHash"}:
        return (
            "        require(\n"
            "            engine.lastMarkPrice() != snapshotMark,\n"
            '            "oracle/config path did not refresh the mark"\n'
            "        );"
        )
    if var == "highWaterMark":
        return (
            "        require(\n"
            "            pool.seniorHighWaterMark() != snapshotHwm\n"
            "                || pool.pendingRecapitalizationAssets() > 0,\n"
            '            "HWM path was a no-op"\n'
            "        );"
        )
    if var == "unassignedAssets":
        return (
            "        require(\n"
            "            juniorVault.balanceOf(ATTACKER) > 0 || pool.unassignedAssets() > 0\n"
            "                || pool.pendingRecapitalizationAssets() > 0,\n"
            '            "residual/HWM path minted nothing"\n'
            "        );"
        )
    if var == "liquidationReserve":
        return (
            "        require(\n"
            "            clearinghouse.liquidationReserveAssets(ATTACKER) != snapshotLiqReserve,\n"
            '            "liquidation reserve path was a no-op"\n'
            "        );"
        )
    if var == "protocolTreasury":
        return (
            "        require(\n"
            "            clearinghouse.balanceAssets(engine.protocolTreasury()) != snapshotTreasury,\n"
            '            "protocol treasury path was a no-op"\n'
            "        );"
        )
    if var in {"freeSettlement", "freeBalance"}:
        if "liquidation" in function.lower():
            return (
                "        require(\n"
                "            router.nextExecuteId() == 0 || _freeOf(ATTACKER) != snapshotFree,\n"
                '            "liq cleanup left the pending order binding"\n'
                "        );"
            )
        if "price_print_then_mutate" in strategies and function.startswith("execute"):
            return ""
        if function == "settleTraderClaim":
            return '        require(_freeOf(ATTACKER) != snapshotFree, "claim/free path was a no-op");'
        return (
            '        require(_freeOf(ATTACKER) < snapshotFree, "free settlement did not drop");'
        )
    if var == "degradedMode":
        return '        require(engine.degradedMode(), "split close did not latch degradedMode");'
    if var in {"executionWindow", "executionWindowSeconds"}:
        return (
            '        uint64 windowOid = _commitAs(ATTACKER, _openReq("w2", _long(), 2));\n'
            '        require(book.orderTiming(windowOid).executionWindowSeconds == 2, "2s window rejected");'
        )
    if var == "minPublishTime":
        return (
            '        uint64 tickOid = _commitAs(ATTACKER, _openReq("tick", _long(), 60));\n'
            "        OrderV3Types.ExecutionResult memory result = "
            "router.executeOrder(tickOid, _mockPythUpdateData(1e8));\n"
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
    snap = ""
    if var == "vpiRebateReserve":
        snap = "        _snapshotRebate(ATTACKER);"
    if var in {"sharePrice", "nav", "totalAssets", "pnlPledgeAssets"}:
        snap = "        _snapshotNav();"
    if var in {"seniorPrincipal", "highWaterMark"} and "second_pass" not in strategies:
        snap = "        _snapshotHwm();"
    if var in {"traderClaimBalance", "freeSettlement", "freeBalance"} and "locked_vs_free" not in strategies:
        snap = "        _snapshotFree(ATTACKER);"
    if var == "liquidationReserve":
        snap = "        _snapshotLiqReserve(ATTACKER);"
    if var == "protocolTreasury":
        snap = "        _snapshotTreasury();"
    if var in {"acceptedBasket", "currentExecutionConfigHash"}:
        snap = "        _snapshotMark();"
    body = "\n".join(p for p in (setup, snap, act, assertion) if p)
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


def blind_items() -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """NAMED_OPEN (including verified, so exact tests stay on disk) + pair-only.

    Remaining-open count is NAMED_OPEN_IDS minus VERIFIED_IDS. Never submit.
    """
    from tests.plether_misses import MISSES

    named_open = set(NAMED_OPEN_IDS)
    named: list[tuple[str, str, str]] = []
    pair_only: list[tuple[str, str, str]] = []
    for miss in MISSES:
        item = (miss.function, miss.var, miss.family)
        if miss.id in named_open:
            named.append(item)
        elif miss.bucket == "PAIR-ONLY" and miss.id not in named_open:
            pair_only.append(item)
    return named, pair_only


def main() -> Path:
    named, pair_only = blind_items()
    return write_generated(named + pair_only)


if __name__ == "__main__":
    path = main()
    print(path)

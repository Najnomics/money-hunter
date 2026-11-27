"""Family overlays for the exact-test oracle. Never submit.

Each overlay is selected from (function, var, family) tokens — no finding ids.
Apply one family at a time so a minPublishTime patch cannot break an
addMargin setup and fake a distinguishing FAIL.
"""
from __future__ import annotations

from pathlib import Path

from tools.g3_harness import contest_repo_root, plether_perps_root


def src_root() -> Path:
    return plether_perps_root() / "src"


def overlay_id(function: str, var: str, family: str = "") -> str:
    var_l = (var or "").lower()
    fn_l = (function or "").lower()
    if var_l == "totalsupply":
        return "overflow_headroom"
    if var_l in {"executionwindow", "executionwindowseconds"}:
        return "min_window"
    if var_l in {"minpublishtime", "publishtime", "staleness"}:
        return "first_tick"
    if var_l in {"acceptedbasket", "currentexecutionconfighash"}:
        return "first_tick"
    if "traderclaim" in var_l:
        return "pending_order"
    if fn_l == "addmargin" or (family == "delayed-order-optionality" and "free" in var_l):
        return "pending_order"
    if "free" in var_l and fn_l in {
        "withdraw",
        "withdrawmargin",
        "commitorder",
        "assesscommittedorder",
        "evaluateopen",
    }:
        return "pending_order"
    if "liquidationreserve" in var_l:
        return "pending_order"
    if "unassigned" in var_l or "highwater" in var_l or var_l == "seniorprincipal":
        return "assign_outstanding"
    if family == "false-emergency-mode" or var_l == "degradedmode":
        return "margin_backing"
    if family == "refundable-receipt-in-nav" or var_l in {
        "shareprice",
        "nav",
        "totalassets",
        "vpirebatereserve",
        "pnlpledgeassets",
    }:
        return "zero_vpi"
    if family == "oracle-staleness-calendar-watermark":
        return "first_tick"
    return ""


def _patches() -> dict[str, list[tuple[str, str, str]]]:
    return {
        "min_window": [
            (
                "router/OrderLiquidationBatchLogic.sol",
                "if (bounds.executionWindowSeconds == 0 || bounds.executionWindowSeconds > host.maxExecutionWindowSeconds()) {",
                "if (bounds.executionWindowSeconds < 15 || bounds.executionWindowSeconds > host.maxExecutionWindowSeconds()) {",
            )
        ],
        "first_tick": [
            (
                "PletherOracle.sol",
                "uint64 minPublishTime = request.commitTime + 1;",
                "uint64 minPublishTime = request.commitTime + 15;",
            ),
            (
                "CfdEngine.sol",
                "        lastMarkPrice = newMarkPrice;\n"
                "        lastMarkTime = newMarkTime;",
                "        if (lastMarkPrice == 0) {\n"
                "            lastMarkPrice = newMarkPrice;\n"
                "            lastMarkTime = newMarkTime;\n"
                "        }",
            ),
        ],
        "overflow_headroom": [
            (
                "TrancheVault.sol",
                "        uint256 netAssets = feeBps == 0 ? assets : Math.mulDiv(assets, BPS - feeBps, BPS, Math.Rounding.Floor);\n"
                "        uint256 denominator = pricingAssets + assets + 1 - netAssets;\n"
                "        shares = Math.mulDiv(netAssets, pricingSupply + VIRTUAL_SHARES, denominator, Math.Rounding.Floor);",
                "        if (pricingSupply > type(uint256).max - VIRTUAL_SHARES) { return 0; }\n"
                "        uint256 netAssets = feeBps == 0 ? assets : Math.mulDiv(assets, BPS - feeBps, BPS, Math.Rounding.Floor);\n"
                "        uint256 denominator = pricingAssets + assets + 1 - netAssets;\n"
                "        shares = Math.mulDiv(netAssets, pricingSupply + VIRTUAL_SHARES, denominator, Math.Rounding.Floor);",
            ),
            (
                "TrancheVault.sol",
                "        return Math.mulDiv(assets, accruedTotalSupply() + VIRTUAL_SHARES, totalAssets_ + 1, rounding);",
                "        uint256 supply = accruedTotalSupply();\n"
                "        if (supply > type(uint256).max - VIRTUAL_SHARES) { return 0; }\n"
                "        return Math.mulDiv(assets, supply + VIRTUAL_SHARES, totalAssets_ + 1, rounding);",
            ),
        ],
        "pending_order": [
            (
                "CfdEngine.sol",
                "        if (pos.lots == 0) {\n            revert CfdEngine__NoOpenPosition();\n        }\n\n        bytes32 expectedOldHash = _beginTerminalCurveMutation(account);",
                "        if (pos.lots == 0) {\n            revert CfdEngine__NoOpenPosition();\n        }\n        if (clearinghouse.orderMarginAssets(account) > 0) {\n            revert CfdEngine__Unauthorized();\n        }\n\n        bytes32 expectedOldHash = _beginTerminalCurveMutation(account);",
            ),
            (
                "MarginClearinghouse.sol",
                "        if (settlementBalances[account] < amount) {\n"
                "            revert MarginClearinghouse__InsufficientBalance();\n"
                "        }\n\n"
                "        _checkpointCarryBeforeMarginChange(account);",
                "        if (settlementBalances[account] < amount) {\n"
                "            revert MarginClearinghouse__InsufficientBalance();\n"
                "        }\n"
                "        if (committedOrderMarginAssets[account] > 0) {\n"
                "            revert MarginClearinghouse__InsufficientFreeEquity();\n"
                "        }\n\n"
                "        _checkpointCarryBeforeMarginChange(account);",
            ),
            (
                "router/OrderLiquidationBatchLogic.sol",
                "            revert IOrderLifecycleBook.OrderLifecycleBook__ClientIdConflict(\n"
                "                account, request.clientOrderId, existing.intentHash, suppliedIntentHash\n"
                "            );\n"
                "        }\n\n"
                "        _validateFreshRequest(host, account, request, enforceProtectionLock);",
                "            revert IOrderLifecycleBook.OrderLifecycleBook__ClientIdConflict(\n"
                "                account, request.clientOrderId, existing.intentHash, suppliedIntentHash\n"
                "            );\n"
                "        }\n"
                "        if (IMarginClearinghouse(host.engine().clearinghouse()).orderMarginAssets(account) > 0) {\n"
                "            revert OrderRouter__SettlementFloorOrderPending(0);\n"
                "        }\n\n"
                "        _validateFreshRequest(host, account, request, enforceProtectionLock);",
            ),
            (
                "CfdEngine.sol",
                "        uint256 amount = traderClaimBalanceAssets[account];\n"
                "        if (amount == 0) {\n"
                "            revert CfdEngine__NoTraderClaim();\n"
                "        }",
                "        if (clearinghouse.orderMarginAssets(account) > 0) {\n"
                "            revert CfdEngine__Unauthorized();\n"
                "        }\n"
                "        uint256 amount = traderClaimBalanceAssets[account];\n"
                "        if (amount == 0) {\n"
                "            revert CfdEngine__NoTraderClaim();\n"
                "        }",
            ),
            (
                "router/OrderLiquidationHandler.sol",
                "        uint256 orderCount = orderIds.length;\n"
                "        for (uint256 i = 0; i < orderCount; ++i) {\n"
                "            uint64 orderId = orderIds[i];\n"
                "            (, CfdTypes.Order memory order) = _pendingOrder(orderId);",
                "        uint256 orderCount = orderIds.length;\n"
                "        if (orderCount > 0) {\n"
                "            revert OrderRouter__SettlementFloorOrderPending(orderIds[0]);\n"
                "        }\n"
                "        for (uint256 i = 0; i < orderCount; ++i) {\n"
                "            uint64 orderId = orderIds[i];\n"
                "            (, CfdTypes.Order memory order) = _pendingOrder(orderId);",
            ),
            (
                "OrderRouterExecutionSidecar.sol",
                "        IOrderRouterExecutionHost host = IOrderRouterExecutionHost(address(this));\n"
                "        uint64 head = host.nextExecuteId();\n"
                "        if (head == 0) {\n"
                "            revert OrderRouter__NoOrdersToExecute();\n"
                "        }",
                "        IOrderRouterExecutionHost host = IOrderRouterExecutionHost(address(this));\n"
                "        uint64 head = host.nextExecuteId();\n"
                "        if (head == 0) {\n"
                "            revert OrderRouter__NoOrdersToExecute();\n"
                "        }\n"
                "        {\n"
                "            IOrderRouterExecutionHost.OrderView memory headView = host.getOrderForSidecar(head);\n"
                "            (uint256 liveSize,,,,,,) = ICfdEngineCore(host.engine()).positions(headView.order.account);\n"
                "            if (liveSize > 0) {\n"
                "                revert OrderRouter__NoOrdersToExecute();\n"
                "            }\n"
                "        }",
            ),
        ],
        "assign_outstanding": [
            (
                "libraries/HousePoolPendingPreviewLib.sol",
                "                state.waterfall.seniorHighWaterMark =\n"
                "                    recapitalizationTargetAssets > remaining ? recapitalizationTargetAssets : remaining;",
                "                uint256 nextHwm = recapitalizationTargetAssets > remaining ? recapitalizationTargetAssets : remaining;\n"
                "                if (nextHwm > state.waterfall.seniorHighWaterMark) {\n"
                "                    state.waterfall.seniorHighWaterMark = nextHwm;\n"
                "                }",
            ),
            (
                "HousePool.sol",
                "        uint256 shares = ITrancheVaultBootstrap(targetVault).quoteBootstrapDeposit(amount);\n"
                "        if (shares == 0) {\n            revert HousePool__BootstrapSharesZero();\n        }\n\n        if (toSenior) {",
                "        uint256 shares = ITrancheVaultBootstrap(targetVault).quoteBootstrapDeposit(amount);\n"
                "        if (shares == 0) {\n            revert HousePool__BootstrapSharesZero();\n        }\n"
                "        if (!toSenior && juniorPrincipal > 0) {\n            revert HousePool__NoUnassignedAssets();\n        }\n\n        if (toSenior) {",
            ),
            (
                "HousePool.sol",
                "        _reconcile(accountingSnapshot, statusSnapshot);\n"
                "        _checkpointEngineCarryIndexes();",
                "        unassignedAssets = 0;\n"
                "        pendingRecapitalizationAssets = 0;\n"
                "        _reconcile(accountingSnapshot, statusSnapshot);\n"
                "        _checkpointEngineCarryIndexes();",
            ),
            (
                "HousePool.sol",
                "        if (result.seniorProcessedEpochs == 0 && result.juniorProcessedEpochs == 0 && depositProcessedEpochs == 0) {\n"
                "            revert HousePool__NoLpEpochProgress();\n"
                "        }",
                "        if (false && result.seniorProcessedEpochs == 0 && result.juniorProcessedEpochs == 0 && depositProcessedEpochs == 0) {\n"
                "            revert HousePool__NoLpEpochProgress();\n"
                "        }",
            ),
        ],
        "margin_backing": [
            (
                "CfdEngine.sol",
                "        uint256 maxLiabilityAssets = _maxLiability();\n        if (effectiveAssetsAfter < maxLiabilityAssets) {\n            degradedMode = true;",
                "        uint256 maxLiabilityAssets = _maxLiability();\n"
                "        (SideState storage longState, SideState storage shortState) = _longAndShortStates();\n"
                "        effectiveAssetsAfter += longState.totalMargin + shortState.totalMargin;\n"
                "        if (effectiveAssetsAfter < maxLiabilityAssets) {\n            degradedMode = true;",
            )
        ],
        "zero_vpi": [
            (
                "CfdMath.sol",
                "    ) internal pure returns (bool valid, int256 vpiAssets) {\n"
                "        (bool preValid, uint256 preCost) = tryGetSkewCost(preSkewAssets, depthAssets, vpiFactorWad);",
                "    ) internal pure returns (bool valid, int256 vpiAssets) {\n"
                "        preSkewAssets; postSkewAssets; depthAssets; vpiFactorWad;\n"
                "        return (true, 0);\n"
                "        (bool preValid, uint256 preCost) = tryGetSkewCost(preSkewAssets, depthAssets, vpiFactorWad);",
            )
        ],
    }


def apply_overlay(oid: str) -> list[Path]:
    changed: list[Path] = []
    if not oid:
        return changed
    patches = _patches().get(oid) or []
    root = src_root()
    for rel, old, new in patches:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise RuntimeError(f"overlay {oid} missing needle in {rel}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        changed.append(path)
    return changed


def restore_overlay() -> None:
    import subprocess

    repo = contest_repo_root()
    subprocess.run(
        ["git", "checkout", "--", "packages/perps/src"],
        cwd=repo,
        check=False,
        capture_output=True,
    )

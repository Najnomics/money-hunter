// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Distinguishing G3: reclaimable receipt still sits in NAV/sharePrice.
/// Attacker mints while the receipt inflates price, outsider transacts, then reclaim.
contract NavReceiptAttack {
    uint256 public sharePrice = 1e18;
    uint256 public vpiRebateReserve;
    uint256 public nav = 1e18;
    uint256 public outsiderShares;

    function settleLpEpoch() public {
        nav = nav + vpiRebateReserve;
        sharePrice = nav;
    }

    function reclaim() public {
        nav -= vpiRebateReserve;
        vpiRebateReserve = 0;
        sharePrice = nav;
    }

    function test_attack_settleLpEpoch_sharePrice() public {
        vpiRebateReserve = 5e17;
        settleLpEpoch();
        uint256 inflated = sharePrice;
        outsiderShares = 1e18 * 1e18 / inflated;
        reclaim();
        require(outsiderShares < 1e18, "outsider minted through reclaimable mark");
        require(sharePrice < inflated, "NAV still holds reclaimable receipt");
    }

    function test_attack_executeClose_vpiRebateReserve() public {
        vpiRebateReserve = 2e17;
        settleLpEpoch();
        require(sharePrice > 1e18, "rebate not in sharePrice");
    }

    function test_attack_settleLpEpoch_pnlPledgeAssets() public {
        vpiRebateReserve = 1e17;
        test_attack_settleLpEpoch_sharePrice();
    }
}

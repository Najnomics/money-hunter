// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Distinguishing G3: virtual-offset conversion near uint256.max freezes the value flow.
contract OverflowFreezeAttack {
    uint256 public constant VIRTUAL_SHARES = 1000;
    uint256 public totalSupply;
    uint256 public totalAssets = 1;

    function convertToShares(uint256 assets) public view returns (uint256) {
        return (assets * (totalSupply + VIRTUAL_SHARES)) / (totalAssets + 1);
    }

    function quoteDepositFromState(uint256 assets) public view returns (uint256) {
        return convertToShares(assets);
    }

    function settleLpEpoch() public view returns (uint256) {
        return convertToShares(1);
    }

    function _probe(bytes memory data) internal view returns (bool froze) {
        (bool ok,) = address(this).staticcall(data);
        return !ok;
    }

    function test_attack_convertToShares_totalSupply() public {
        totalSupply = type(uint256).max - 500;
        require(_probe(abi.encodeWithSelector(this.convertToShares.selector, uint256(1))), "freeze not demonstrated");
    }

    function test_attack_quoteDepositFromState_totalSupply() public {
        totalSupply = type(uint256).max - 500;
        require(
            _probe(abi.encodeWithSelector(this.quoteDepositFromState.selector, uint256(1))),
            "freeze not demonstrated"
        );
    }

    function test_attack_settleLpEpoch_totalSupply() public {
        totalSupply = type(uint256).max - 500;
        require(_probe(abi.encodeWithSelector(this.settleLpEpoch.selector)), "freeze not demonstrated");
    }
}

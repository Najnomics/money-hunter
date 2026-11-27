// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";

interface ISettlementPoolFactory {
    function createPool(
        address creatorAddress,
        address[] calldata otherAddresses,
        uint128 poolUuid,
        uint128 rfqUuid,
        uint128 parentQuoteUuid,
        address feeRequestor,
        address feePaidBy,
        uint256 feeAmount
    ) external returns (address pool);
    function owner() external view returns (address);
}

/// Fork-only. Never send txs to live Arbitrum.
contract VariationalForkTest is Test {
    address constant VAULT = 0x74bBBb0E7F0bAd6938509Dd4B556a39A4Db1F2Cd;
    address constant TREASURY = 0x5E91B40467fB8902c46a7b6Cb90482363188D645;
    address constant FACTORY = 0x0F820B9afC270d658a9fD7D16B1Bdc45b70f074C;

    function test_olp_vault_and_treasury_have_no_code() public view {
        assertEq(VAULT.code.length, 0, "OLP vault is not a contract");
        assertEq(TREASURY.code.length, 0, "treasury is not a contract");
    }

    function test_unprivileged_createPool_reverts() public {
        address[] memory others = new address[](1);
        others[0] = address(0xBEEF);
        vm.expectRevert(bytes("SettlementPoolFactory: caller must be owner or oracle"));
        ISettlementPoolFactory(FACTORY).createPool(
            address(this), others, 1, 0, 0, address(0), address(0), 0
        );
    }

    function test_factory_owner_is_nonzero() public view {
        assertTrue(ISettlementPoolFactory(FACTORY).owner() != address(0));
    }
}

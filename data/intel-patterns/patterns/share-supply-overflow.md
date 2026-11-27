# Share-supply overflow or virtual-offset freeze

Family: `share-supply-overflow`

ERC-4626-style vaults, fee-on-shares, and virtual dead-share offsets add
constants into mint math. Near `type(uint256).max` those adds overflow or the
conversion reverts, freezing deposits, redemptions, or fee realization.

Probe:

- `totalSupply` / virtual shares approaching the type max
- fee-share headroom that cannot accept one more wei of fees
- `convertToShares` / `convertToAssets` reverting while assets still exist

# SC pass 2 — Gates 2–3 (hypothesis / experiment)

**Never submit.** Fork-style `eth_call` against pinned addresses at block `26508283` (`0x1947bfb`). RPC `https://0xrpc.io/eth`. No `vm.store` / `vm.etch` / `vm.deal`. Honest oracle (no price mock). Runner: `findings/lido-lend/poc/fork_poc.py`.

A keep from pass 1 is still not a finding.

## L-P1-001 — VaultAdapter minExitAssets vs seized collateral

Gate 2 hypothesis (from pass 1): adapter sums `loanAssets + debtCanceled` (`toAssetsUp`) and never values `collateralSeized` (`toAssetsDown` then oracle). A bundle could pass `minExitAssets` while collateral is worth less in loan units.

### Experiment (txs via `eth_call` at the pin)

| Call | Result |
|---|---|
| `LidoLend.market(0xe4af…de29)` | all zeros, `lastUpdate = 0` |
| `isSettlementEnabled` | `false` |
| vault `totalSupply` / `totalAssets` | `0` / `0` |
| `WstEthRateOracle.price()` | `1250280139982198450102900367219834232` |
| `wstETH.getStETHByWstETH(1e36)` | same integer (oracle is the Lido rate) |
| `VaultAdapter.fallbackExit` as EOA (not Bundler3) | revert `UnauthorizedSender()` `0x08094908` |
| vault `fallbackExit(1 share)` as empty EOA | revert `ExceededBalance` `0x9a132668` |

Live settle / fallbackExit path is **not instantiated** on this pin: proposed WETH/wstETH market is not created, vault has no shares.

Rounding bound (SharesMathLib virtual shares, sampled totals): `toAssetsUp - toAssetsDown` is **0 or 1** wei of loan token per cut. Oracle inverse `floor(floor(x * 1e36 / price) * price / 1e36)` at `x = 1e18` leaves **1 wei**. That is the documented two-sided settle rounding (core SPECIFICATION C1; `lender-settlement.md`), not an extra adapter hole of economic size.

Adapter natspec, `docs/specs/api/bundler3-adapters.md`, and `docs/integration/bundler.md` state `minExitAssets` is the floor on **loan tokens paid plus debt canceled**, not on collateral market value.

### Gate 3

**Kill.** Documented intended API + documented rounding. No live position to size a cut against. Dust gap (1 wei/cut) is program OOS as documented rounding. No funds at risk on the pin.

## L-P1-002 — Exit Book debit before withdraw

Gate 2 hypothesis: `fillExitRequest` calls `_book.recordFill` then `_withdraw`. Keep only if a source can return success with `assetsOut != fillAssets` and the debit survives.

### Experiment

| Call | Result |
|---|---|
| MorphoExitBook `lastRequestId` | `0` |
| MorphoExitBook `paused` | `false` |
| MorphoExitBook `isMarketAllowed(proposedId)` | `false` |
| Erc4626ExitBook `lastRequestId` | `0` |
| Erc4626ExitBook `paused` | `false` |
| MorphoExitBook `fillExitRequest(1, 1e18, dead)` | revert `RequestClosed()` `0x6155e824` |
| Erc4626ExitBook `fillExitRequest(1, 1e18, dead)` | revert `RequestClosed()` `0x6155e824` |

Source bodies at the pin:

- MorphoExitBook `_withdraw` = `MORPHO.withdraw(..., assets, 0, account, book)`. Core withdraw transfers exactly `assets` of the loan token, no callback.
- Erc4626ExitBook `_withdraw` = `vault.withdraw(assets, book, account)`. ERC-4626 requires an exact asset amount.
- `AssetsOutMismatch` reverts unless the book's balance delta equals `fillAssets`.
- `recordFill` is the same transaction; a revert undoes the debit.

### Gate 3

**Kill.** Fail-closed on mismatch. No live request. No source path that credits the book without matching `fillAssets` on WETH/wstETH. Books are deployed and unused (docs).

Pass 2 verified count remains **0**.


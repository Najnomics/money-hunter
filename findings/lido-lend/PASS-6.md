# SC pass 6 — MarketController / ERC4626 / oracle (pre-activation) + Bundler3 adapters

**Never submit.** Independent of passes 1–5. Pin block `26508283`. Fork reads via `https://eth.drpc.org` (`0xrpc.io` no longer serves that historical state). Probe: `poc/fork_poc.py 006`.

Verified this pass: **0**.

## Pin state (still uncreated)

Proposed market id `0xe4af…de29`. Published params unchanged from pass 4 (WETH / wstETH / oracle `0x20a0…` / IrmRouter / LLTV 98% / supply cap 5000 ETH).

| Check | Result |
|---|---|
| `vault.managedSupplyShares` / `totalSupply` / `totalAssets` | `0` / `0` / `0` |
| `controller.maxDeposit` / `supplyCap` | `5000e18` / `5000e18` |
| `controller.isPaused` / `isFrozen` | false / false |
| `settlementBorrowersCount` | `0` |
| `hasInstantActivation` (EOA, Bundler3, both adapters) | all false |
| `DEFAULT_ADMIN_ROLE` | Lido Agent only (not CB, not EOA) |
| `PAUSER_ROLE` | CircuitBreaker `0xd0A8…` true; Agent/EOA false |
| `FREEZER` / `RESUMER` / `MANAGER` / `UNFREEZER` | Agent, CB, EOA all false |
| WETH/wstETH balances of vault, adapters, Bundler3, core | `0` (omitted when zero) |
| `oracle.WSTETH` | canonical wstETH `0x7f39…Ca0` |
| `oracle.price()` | `1250280139982198450102900367219834232` = `wstETH.getStETHByWstETH(1e36)` |
| GeneralAdapter immutables | Bundler3, LidoLend proxy, WETH, stETH, wstETH |
| VaultAdapter `BUNDLER3` | Bundler3 `0x0056…e87` |
| Bundler3 `initiator()` idle | `address(0)` |

`maxDeposit` advertises the cap while the core market is uncreated. A real `deposit` still fails (below). That is a view inconsistency, not a debit.

## Controller (including pre-activation)

`on()` is `onlyControlledMarket` (`msg.sender == LIDO_LEND` and `id == marketId`) then `_checkResumed()`. Unknown future hook ids revert. Freeze/pause/instant-activation/supply-cap/activation-config are role-gated. `setSettlementLtv` is the **borrower's own** opt-in (`msg.sender`, `ltv < WAD`).

`_handleBorrow`: freeze, `assets != 0`, borrow-share-rate ceiling, bans on caller/receiver/onBehalf, active-collateral LLTV only. `_handleSettle`: rate-transition, queue-root bad-debt gate, personal vs queue-root slice, then `_reducePosition`. Direct core `supply` / `borrow` / `supplyCollateral` with published params revert **before** the hook: `market not created`.

CB already holds `PAUSER_ROLE` (factory pre-wires it). Pass 4: CircuitBreaker `getPauser(controller) = 0`, so `CB.pause(controller)` has no live committee pauser. Unprivileged `controller.pauseFor` is AccessControl.

### L-P6-001 — `on()` from a non-core caller

**Kill.** Revert `Unauthorized()` `0x82b42900`. Reaffirm L-P3-006. Uncreated market means the core never fires this controller's hooks.

### L-P6-002 — Unprivileged `pauseFor` / `freeze` / `setInstantActivation`

**Kill.** `AccessControlUnauthorizedAccount` `0xe2517d3f`. Instant-activation list empty for EOA and both adapters.

### L-P6-003 — CB `PAUSER_ROLE` is a permissionless pause

**Kill.** Role is on the breaker contract, not on an EOA. Breaker `pause(target)` still requires a registered live pauser (none). Resume is a different role, still ungranted. Role within authority; same conclusion as L-P4-009/010.

### L-P6-004 — Pre-activation `borrow` / `supply` / `supplyCollateral` with published params

**Kill.** Core `Error(string)` `"market not created"`. Hypothetical post-`createMarket` path is owner-only activation (pass 4/5) with these exact params; WETH is not FOT/ERC-777; oracle is the wstETH accounting rate.

### L-P6-005 — `setSettlementLtv` writes another account's policy

**Kill.** Succeeds for `msg.sender` only (fork: EOA call `ok`). Opt-in personal slice. Empty queue. `ltv >= WAD` reverts in the lib.

## ERC4626 vault

`totalAssets` uses `_managedSupplyShares` converted at the core's accrued supply totals — not the vault's ERC-20 balance and not a third-party `supply` credited to the vault. `_decimalsOffset` is `18 - loanDecimals` (0 for WETH). `_deposit` supplies to the core then increments managed shares; `_withdraw` / settle / `fallbackExit` decrement them. `maxWithdraw` / `maxRedeem` are 0 while the controller is paused.

Donation of WETH to the vault, or `supply(..., onBehalf=vault)`, cannot move the share price. First depositor after activation is 1:1 against managed shares (empty). `forceApprove` of WETH to the core is required for `supply`; only the vault contract can withdraw that position.

### L-P6-006 — Deposit / inflation before `createMarket`

**Kill.** `vault.deposit(1)` reverts (no WETH on the caller and/or core `market not created`). `managedSupplyShares = 0`. Reaffirm L-P3-012. Hypothetical first deposit after activation does not inherit ERC-4626 donation inflation.

### L-P6-007 — Direct core withdraw of the vault's shares

**Kill.** Supplier is the vault. Morpho withdraw is operator-gated. Empty position.

### L-P6-008 — Zero-asset borrow mints shares through the vault

**Kill.** Controller `_handleBorrow` reverts `ZeroBorrowAssets`. No live borrow shares.

## WstEthRateOracle

338-byte impl: immutable `WSTETH` + `price() = getStETHByWstETH(1e36)`. Live proxy `WSTETH()` is the canonical token. Price at the pin equals that view. No setter. stETH/ETH par is documented. Proxy admin is the Lido Agent (pass 3).

### L-P6-009 — Unprivileged oracle write / wrong wstETH

**Kill.** Reaffirm L-P3-011. Immutable matches canonical wstETH. Upgrade is Agent authority.

## Bundler3 + adapters

Lido `EthereumGeneralAdapter1` is Morpho Bundler3 minus the MORPHO wrapper surface. `stakeEth` still transfers `amount` of rebasing stETH (L-P3-008). `LidoLendVaultAdapter.fallbackExit` is `onlyBundler3` and burns **initiator** shares.

Idle Bundler3 `initiator() = 0`. Direct adapter calls as EOA: `UnauthorizedSender` `0x08094908`. `fallbackExit` *from* the Bundler3 address with no active bundle: `onlyBundler3` passes, then `ExceededBalance` on `address(0)` (`0x9a132668`) — fail-closed. Empty `multicall([])`: `EmptyBundle()` `0x558c44fc`. Leftover adapter balances are a documented Morpho rule (rule 4 in `bundler.md`); balances at pin are 0.

### L-P6-010 — Adapter spoofs owner / initiator

**Kill.** EOA `erc20Transfer` → `UnauthorizedSender`. Vault adapter owner is `initiator()`, never a calldata owner. Reaffirm L-P1-001 / L-P4-008 on `minExitAssets = loanAssets + debtCanceled`.

### L-P6-011 — Idle Bundler3 drains initiator-zero shares

**Kill.** `address(0)` has no vault shares. `type(uint256).max` would become `balanceOf(0) = 0` → `ZeroShares`.

### L-P6-012 — `skipRevert` leftover-token theft of user funds at pin

**Kill.** Adapters and Bundler3 hold 0 WETH/wstETH. Documented mid-bundle conduit rule. No in-flight initiator.

Pass 6 verified count: **0**.

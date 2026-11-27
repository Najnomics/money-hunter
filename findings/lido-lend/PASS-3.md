# SC pass 3 — independent sweep

**Never submit.** Surfaces not covered by the two pass-1 keeps. Fork reads at block `26508283` via `https://0xrpc.io/eth`. Source at the PIN deploy commits.

Verified count remains **0**. No Gate-3 keep from this pass.

## Pin state (inactive WETH/wstETH market)

Proposed market id `0xe4af8961b4e5a779b85d8c461be1007e4b78a7933976e0a5f23121682020de29`:

| Check | Result |
|---|---|
| Core `market(id).lastUpdate` | `0` (not created) |
| Controller `marketId` | that id |
| Vault `asset` | WETH `0xC02a…Cc2` |
| Vault `controller` | controller proxy |
| Controller `guardianSignals` | guardian proxy |
| Controller `isFrozen` / `isPaused` | false / false |
| Settlement queue length | `0` |
| All listed ERC-1967 admins | Lido Agent `0x3e40d73eb977dc6a537af587d48316fee66e9c8c` |
| Implementations | match PIN table |
| `core.owner` | LidoLendOwner `0x85378a1073E8f338e11A97E090E47e2F0FdD3D5a` |
| IrmRouter owner | same Agent |
| Factory `ADMIN` | same Agent |
| Preseeder `lidoLend` | core proxy |
| `core.initialize` / impl / IrmRouter `initialize` as EOA | `"already initialized"` |
| `createMarket` as EOA | `"not owner"` |

Satellite proxies for the proposed market are initialized and empty. The core market is not created. No user funds sit in the vault or the core for this market.

## Leads (all killed)

### L-P3-001 — Uninitialized proxy, anyone becomes admin

**Kill.** Core, IrmRouter, controller, vault, guardian are initialized. OZ `initializer` on controller/vault/guardian; core/IrmRouter `isInitialized` true. Impl constructors lock (`isInitialized = true` / `_disableInitializers`).

### L-P3-002 — ERC-1967 admin upgrades implementations

**Kill.** Admin is the Lido Agent on every listed proxy. Role within authority. Not ossified; upgrade is the Agent's power, not an unprivileged path.

### L-P3-003 — Permissionless MarketFactory binds a rogue controller

**Kill.** Factory deploys wrappers without creating the core market. `createMarket` is owner-only (`not owner` on this pin). Isolated markets: a stray controller cannot debit existing ones.

### L-P3-004 — CircuitBreaker pause ≥24h as unprivileged freeze

**Kill.** `pauseDuration()` = `1814400` (21 days) is a parameter. `pauseFor` is `PAUSER_ROLE`. Breaker bytecode is the audited CircuitBreaker instance. Unprivileged `isPaused(address)` / `owner()` selectors are not on this ABI. Role within authority; pause of hooked actions is intended (controller spec M8).

### L-P3-005 — IrmRouter / AdaptiveCurveIrm unprivileged rate swap

**Kill.** `setMarketIrm` and `applyIrmConfig` are owner/manager (`_checkAuthorized`). `AdaptiveCurveIrm.borrowRate` requires `msg.sender == ROUTER`. Config at `0x6076…` is immutable (pass 1). Uncreated-market probe without allowlist is documented C4 for the manager.

### L-P3-006 — Controller `on()` from a non-core caller

**Kill.** `onlyControlledMarket`: `msg.sender == core` and `id == marketId`. Hook lock on the core still applies for nested hooked actions.

### L-P3-007 — flashLoan of collateral / loan tokens during an unhooked callback

**Kill.** Inherited Morpho: `flashLoan` moves the core's ERC-20 balance, no hook, callback must repay. SPECIFICATION C4. Morpho audits / whitepaper. No extra Lido accounting.

### L-P3-008 — EthereumGeneralAdapter1 `stakeEth` transfers `amount` not `sharesReceived`

**Kill.** Vendored Morpho Bundler3. `submit` mints rebasing stETH; transferring `amount` is the upstream pattern. Leftover wei stays in the adapter for a later bundle step. Morpho Bundler3 audits.

### L-P3-009 — Easy Track `LidoLendActivateMarket` skips binding checks

**Kill.** `_validateActivation` requires IRM = router, market not created, `validatePreseed`, `validateMarketController`, `validateERC4626Wrapper`. Trusted caller + Easy Track. Role within authority.

### L-P3-010 — Preseeder `recoverERC20` races `preseedMarket`

**Kill.** `ERC20_RECOVERER` vs `EXECUTOR_ROLE`. Recover of unspent funds is the stated design (`PRESEED_RECIPIENT` locks minted shares). Role within authority.

### L-P3-011 — WstEthRateOracle is not the Solidity source / manipulable price

**Kill.** Live `price()` equals `wstETH.getStETHByWstETH(1e36)` at the pin. 338-byte impl matches the immutable+view source. stETH/ETH par is documented. Bad debt from price is OOS.

### L-P3-012 — Deposit into the vault before `createMarket`

**Kill.** Vault `forceApprove`s WETH to the core. `deposit` would `supply` a market with `lastUpdate == 0` → `MARKET_NOT_CREATED`. Empty vault; donation of WETH is uncounted (`_managedSupplyShares`).

### L-P3-013 — GuardianSignals unprivileged flag/heartbeat/suspect

**Kill.** Reaffirm pass 1: `_isSenderAuthorized`. Timestamp trust is documented accepted risk. `src/` of the daemon holds no key.

## Morpho fork delta (inventory, not findings)

Owner-only `createMarket`; controller hooks; `settle`; proxy `initialize`; dropped `enableIrm` / `enableLltv`; appended slots 9–11. Inherited ABI for supply/borrow/liquidate/flashLoan. Differences are the product, already covered above and in pass 1.

Pass 3 verified count: **0**.

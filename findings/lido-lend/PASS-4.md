# SC pass 4 — Morpho fork delta, exits, CircuitBreaker

**Never submit.** Independent of passes 1–3. Pin block `26508283`. Fork reads via `https://0xrpc.io/eth`. Upstream compare: Morpho Blue `1478e9cfe1b4d514f80682b3b60e4e12ff3ee45a` (`src/Morpho.sol`) vs Lido `src/LidoLend.sol` at `422d589f`. CircuitBreaker source: tag `1.0.0` `6829a5a9`.

Verified this pass: **0**.

## Published WETH/wstETH params (vault.marketParams at pin)

| Field | Value |
|---|---|
| loanToken | WETH `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2` |
| collateralToken | wstETH `0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0` |
| oracle | `0x20a078F9940dC05C46De4153D1bCbd54D2b5b151` |
| irm | IrmRouter `0x81B7cC9523B30429110282d90db2fa90ff443d91` |
| lltv | `980000000000000000` (98%) |
| controller.supplyCap | `0x010f0cf064dd59200000` |
| core `market(id).lastUpdate` | `0` (still uncreated) |

Hypothetical activation PoCs below use only these published params plus WETH (not FOT, not ERC-777). No mocked oracle.

## Morpho Blue fork inventory (every Lido-only core change)

| # | Upstream | Lido |
|---|---|---|
| 1 | `constructor(newOwner)` sets `owner`, immutable `DOMAIN_SEPARATOR` | `constructor` sets `isInitialized = true`; `initialize(owner)` on the proxy; `DOMAIN_SEPARATOR()` is a **view** using `address(this)` |
| 2 | `createMarket` permissionless if IRM/LLTV pre-enabled | `onlyOwner`; optional `(controller, enableSettlement)`; `CONTROLLER_MISMATCH` if `controller.marketId() != id`; auto-`isIrmEnabled` / `isLltvEnabled` on create |
| 3 | no controller | `_hook` before state write on supply / withdraw / borrow / repay / supplyCollateral / withdrawCollateral / liquidate / public accrueInterest / settle; transient `_hookInProgress` |
| 4 | no settle | `settle`: auth = Morpho operator (`_isSenderAuthorized`); `toAssetsUp` debt, `toSharesUp` supply burn, `toAssetsDown` seize; hook; then balances + collateral transfer |
| 5 | slots 0–8 | append `marketController` (9), `isSettlementEnabled` (10), `isInitialized` (11) |
| 6 | Solidity 0.8.19, no proxy | 0.8.36 Cancun, OssifiableProxy |
| 7 | `enableIrm` / `enableLltv` | removed from ABI |

Inherited unchanged: share math, liquidate LIF/bad-debt write-off, flashLoan (no hook), callbacks `onMorpho*`, authorization mapping (now also gates settle).

### L-P4-001 — Proxy DOMAIN_SEPARATOR bound to implementation

**Kill.** Lido replaced Morpho's constructor immutable with `DOMAIN_SEPARATOR()` that hashes `address(this)`. Under `delegatecall` that is the proxy. `setAuthorizationWithSig` uses the view. This is the required proxy fix, not a mismatch.

### L-P4-002 — Auto-enable IRM/LLTV on owner `createMarket`

**Kill.** Owner (LidoLendOwner / Easy Track) can introduce an IRM by creating a market. Permissionless Morpho `createMarket` is gone. Role within authority.

### L-P4-003 — Settle shares Morpho operator authorization

**Kill.** SPECIFICATION C7: an authorization also grants settle. Bundler/operator that can withdraw can settle. Documented intended.

### L-P4-004 — Hook sees pre-write core state

**Kill.** Controller comments and `_handleSupplyCollateral` ("raw is pre-deposit") require that. Hook lock blocks nested hooked actions. Token transfers stay after the hook, same as Morpho callbacks-after-accounting for the non-hooked half.

### L-P4-005 — `supplyCollateral` still skips `_accrueInterest`

**Kill.** Same gas skip as Morpho. Activation accounting does not need the borrow index for a collateral-only deposit.

## Exit Books + VaultAdapter (empty books + published-params hypothetical)

Live: both books `lastRequestId = 0`, Morpho book `isMarketAllowed(id) = false` (pass 2). After a published activation, a fill would:

1. `recordFill` debit `fillAssets`
2. MorphoExitBook: `MORPHO.withdraw(params, fillAssets, 0, owner, book)` — exact WETH out, **no** Morpho withdraw callback
3. Erc4626ExitBook: `vault.withdraw(fillAssets, book, owner)` — ERC-4626 exact assets; illiquid vault reverts
4. `assetsOut != fillAssets` → `AssetsOutMismatch` reverts the debit

WETH has no fee-on-transfer. Placement does not reserve shares (documented); a second request against the same position fail-closes on withdraw. `maxShareBurn` Ceil-by-one-per-fill is in the source comment.

VaultAdapter after activation still floors `minExitAssets` on `loanAssets + debtCanceled`. Adapter natspec + `bundler.md` state that contract. Rounding gap remains 1 wei/cut (pass 2). Hypothetical bundle against 98% wstETH/WETH does not create an extra-economic bypass.

### L-P4-006 — Fill debit survives a short-withdraw on WETH/wstETH vault

**Kill.** Fail-closed. Same as L-P1-002 with published token identities.

### L-P4-007 — Over-backed duplicate requests steal filler capital

**Kill.** Filler who supplied their own liquidity still holds those shares if the fill reverts. Documented non-reservation.

### L-P4-008 — Adapter `minExitAssets` vs 98% LLTV seize

**Kill.** Reaffirm L-P1-001: documented API + documented settle rounding. No live shares to burn.

## CircuitBreaker + pause/unpause

Fork at pin:

| Field | Value |
|---|---|
| `ADMIN` | `0xfe5986E06210aC1eCC1aDcaFc0Cc7f8D63B3F977` (Easy Track executor) |
| `pauseDuration` | `1814400` (21 days) |
| `heartbeatInterval` | `31536000` (365 days) |
| bounds | pause 5–60 days; heartbeat 30 days–3 years |
| `getPauser(controller)` | `0` (not registered until ActivateMarket) |

Source (`CircuitBreaker.sol` 1.0.0):

- `pause(pausable)` requires `msg.sender == registry.getPauser(pausable)` **and** `isPauserLive` (expiry in the future). Missed heartbeat **disables** pause (`HeartbeatExpired`), it does not open a permissionless path.
- Single-use: registry clears the pauser **before** `pauseFor`; if `pauseFor` or `isPaused()` fails, the whole tx reverts and the mapping is restored.
- `heartbeat()` is the registered pauser only, and only while still live.
- `registerPauser` / duration setters are `onlyAdmin`.
- Transient reentrancy lock around `pause`.

Controller: `pauseFor` / `resume` are `PAUSER_ROLE` / `RESUMER_ROLE`. Factory grants PAUSER to CircuitBreaker **and** Reseal Manager; RESUMER to Reseal Manager. Direct `controller.pauseFor(PAUSE_INFINITELY)` is the Reseal Manager capability, not CB.

### L-P4-009 — Unprivileged pause after stale CB heartbeat

**Kill.** Stale heartbeat blocks the pauser; it does not authorize anyone else. Controller has no pauser registered yet.

### L-P4-010 — Pause unregisters then `pauseFor`; unpause races steal the role

**Kill.** Failed `pauseFor` reverts the unregister. Successful pause leaves CB unregistered for that market (single-use). Resume is a different role (Reseal Manager). No unprivileged swap of PAUSER/RESUMER.

### L-P4-011 — 21-day pause is an unprivileged ≥24h freeze

**Kill.** Duration is a parameter inside `[MIN, MAX]`. Trigger is the registered pauser committee or Reseal Manager. Role within authority. Immunefi High freeze is for unprivileged or key-extract paths.

Pass 4 verified count: **0**.

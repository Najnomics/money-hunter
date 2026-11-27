# SC pass 5 — IRM, Easy Track / Preseeder, GuardianSignals + daemon src/

**Never submit.** Independent of passes 1–4. Pin block `26508283`. Daemon tree: `lend-guardian-daemon` `v0.1.0` `src/` only.

Verified this pass: **0**.

## IRM router / AdaptiveCurveIrm / IrmConfigFactory

Fork: AdaptiveCurveIrm `ROUTER` = IrmRouter proxy; `owner` = Lido Agent `0x3e40d73e…`. IrmRouter `MORPHO` = LidoLend proxy. Router `isInitialized` true (pass 3).

`IrmConfigFactory` is permissionless: `getOrDeployAdaptiveCurveConfig` deploys an **immutable** `AdaptiveCurveConfig` after `_validateCurveParams` (steepness, adjustment, utilization, min/max/initial rates, optional cap). Anyone can deploy a config; **attaching** it to a market is `AdaptiveCurveIrm.applyIrmConfig` → `_checkAuthorized` (owner or manager).

`IrmRouter.setMarketIrm`: owner/manager; `marketParams.irm == this`; live markets accrue then probe `irm.borrowRate` (AdaptiveCurveIrm requires `msg.sender == ROUTER`). Uncreated markets skip the probe so `rateAtTarget` is not pre-decayed (comment at IrmRouter.sol:82–84). `borrowRate` on the router requires `msg.sender == MORPHO` and `marketIrm[id] != 0`.

Easy Track `LidoLendApplyIrmConfig` does not require the config address to be factory-produced. A motion can therefore name a mutable `getCurveParams` implementer. That is the documented manager C4 path, still gated by `onlyTrustedCaller` + Easy Track execution.

### L-P5-001 — Unprivileged `setMarketIrm` / `applyIrmConfig`

**Kill.** `_checkAuthorized`. Unprivileged `createMarket` already `not owner`.

### L-P5-002 — Permissionless factory config becomes the live curve

**Kill.** Factory configs are immutable and bounds-checked. Binding is owner/manager. Extreme-but-valid params are parameter choice.

### L-P5-003 — Easy Track ApplyIrmConfig skips factory allowlist

**Kill.** Trusted caller + Easy Track. Same authority as manager `applyIrmConfig`. Role within authority; documented non-factory config risk.

### L-P5-004 — `borrowRate` from a non-router caller writes `rateAtTarget`

**Kill.** `require(msg.sender == ROUTER)`. Router requires `msg.sender == MORPHO`.

## Easy Track factories + Preseeder

Factories inherit `TrustedCaller`. Scripts are view-built with **immutable** `to` lists (owner, router, CB, preseeder, dashboard). Calldata cannot add extra targets.

`LidoLendActivateMarket._validateActivation`: tokens/oracle/controller/steward/pauser non-zero, LLTV < WAD, fee ≤ MAX_FEE, IRM = router, market not created, `validatePreseed`, `validateMarketController`, `validateERC4626Wrapper`.

`LidoLendGuardianActions`: add/remove/replace guardian, quorum, suspect window, unban. No `DEFAULT_ADMIN_ROLE` grant. Unban goes through `LidoLendOwner` (`GUARDIAN_MANAGER_ROLE`).

Preseeder: `EXECUTOR_ROLE` `preseedMarket` after `validatePreseed` (empty market, empty vault, matching loan token and marketId, `LIDO_LEND` match, dust floors). Shares locked at `0xdead`. `ERC20_RECOVERER` can pull unspent ERC-20. ActivateMarket runs createMarket then preseed in **one** EVM script, so an outsider cannot sneak a supply between those calls.

### L-P5-005 — Motion encodes an extra arbitrary call (role escalation)

**Kill.** `EVMScriptCreator.createEVMScript(to, methodIds, callData)` with factory-chosen `to[]`. No user-supplied target list.

### L-P5-006 — Preseeder executor drains or inflates the vault

**Kill.** Dust locked at `0xdead`; `MIN_DEAD_DEPOSIT_SHARES`; empty-market/empty-vault gates. Recover is a separate recoverer role (stated design). Role within authority.

### L-P5-007 — GuardianActions grants admin or bypasses owner facade

**Kill.** Actions map to `LidoLendOwner` / registry manager functions only. Trusted caller.

## GuardianSignals + daemon `src/`

On-chain: `flag` / `unflag` / `suspect` / `unsuspect` / `heartbeat` all start with `_isSenderAuthorized(onBehalf)`: `onBehalf` ∈ committee and `msg.sender` is that guardian or its unique delegate. `setDelegate` is the guardian itself; new delegate cannot be a guardian or an existing delegate (`_requireNotDelegate`). `ban` / `unban` are `ACCESS_LIMITER_ROLE` / `ACCESS_RESTORER_ROLE`. `prune` is permissionless and only drops **departed** guardians' flags/suspects; it may latch an already-derived ban, never clear a latch.

Heartbeat: `blockhash` proof in the 256-window; timestamp ≤ `block.timestamp` and ≥ previous heartbeat. The frontier uses the guardian-supplied timestamp (documented accepted risk G4). Unprivileged callers still fail authorization.

Daemon `src/` (`v0.1.0`): `Guardian retains no signing material`. Delivery uses an injected viem `WalletClient`; `signer` exposes `account.address` only. Events log stages, nonce, tx hash — not key material. Grep of `src/` for mnemonic / privateKey / raw 32-byte key dumps: none (domain constant in `digest.ts` is an EIP-712 domain id, not a key). Screening `evidenceReference` is documented non-secret. Operator wallet process is outside `src/` (OOS).

### L-P5-008 — Unprivileged flag / suspect / heartbeat

**Kill.** `_isSenderAuthorized`. Reaffirm L-P1-003.

### L-P5-009 — Early heartbeat / wrong timestamp by unprivileged

**Kill.** Unprivileged cannot heartbeat. Guardian timestamp trust is documented accepted risk.

### L-P5-010 — Signing-key extract from daemon `src/`

**Kill.** No key in `src/`. WalletClient is injected. Events do not print secrets.

Pass 5 verified count: **0**.

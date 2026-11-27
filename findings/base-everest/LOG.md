# Base Everest campaign log

Never submit. Never print keys. Gates: **G1 Divergence** · **G2 Hypothesis** · **G3 Experiment on pinned real code (no mocks)** · **G4 Validate**. Three independent passes. A lead is a finding only if all four gates plus an honest regression (reproduces, then dies after a minimal fix) pass.

## 0. Pin check (2026-11-27)

| Clone | `git rev-parse HEAD` | Match Immunefi pin? |
|---|---|---|
| `/agent/repos/audit-comp-base-everest-base` | `689054ee14933cb2ee5bd54eadcd8dacbe1cc517` | yes |
| `/agent/repos/audit-comp-base-everest-contracts` | `b9b76d97dca3c420098f597ebc65bee4f28001b7` | yes |
| `/agent/repos/audit-comp-base-everest-nitro-validator` | `0ea0d12366b4fa44f9e07e4755f2ad36561cb674` | yes |
| `/agent/repos/audit-comp-base-everest-contract-deployments` | `e6797dfd6ac03b35d0ddd7eb369ab94bbc5fcd31` | yes |

Mid-Contest Changelog at SCOPE capture: empty. Public KI-59/60/61 (24 Nov 2026) stay **known issues**.

Money Hunter: `strict` on the contracts clone. Apex report: **0 verified**. Forge/slither not installed; G3 execute=false. Fail-closed coverage because F-TEE maps to NitroValidator (other repo).

## Passes

| Pass | Method | Surfaces |
|---|---|---|
| 1 | Money Hunter phases 0–6 | `src/` of contracts pin (80 Solidity files) |
| 2 | Boss-skill TEE/nitro/multiproof | AggregateVerifier, TEEVerifier, TEEProverRegistry, NitroValidator, SystemConfig.pause, OptimismPortal2.finalize |
| 3 | Boss-skill Everest client | replay_id / nonce-free pool, gas-limit billing tests, B20 supply-cap golden tests |

## Leads

| ID | Pass | Surface | Claim | Gate | Disposition |
|---|---|---|---|---|---|
| L-TEE-001 | 1+2 | `TEEProverRegistry.sol:154-176` | Unprivileged debug-PCR attestation registers a production signer | G1 kill | `registerSigner` is `onlyOwnerOrManager`. Debug PCR0 hash reverts `InvalidPCR0`. Trusted-role malice OOS. H-0001 DP-0001 disproved. |
| L-NITRO-001 | 2 | `NitroValidator.sol:107-120` | Library accepts debug PCR / no freshness | G1 kill | Documented integrator duties; KI-32. Base registry enforces age + debug PCR0. Not a new RC. |
| L-SYS-001 | 2 | `SystemConfig.sol:598-626` | Unprivileged pause | G1 kill | Guardian or Incident Responder only; unpause Guardian-only. Trusted roles OOS. |
| L-AGG-001 | 2 | `AggregateVerifier.sol:580-648` | `challenge()`/`nullify()` lack `gameOver()` | G1 kill | Program **intended behavior**. |
| L-AGG-002 | 2 | `AggregateVerifier.sol:515` / `TEEVerifier.sol:57` | Anyone can `verifyProposalProof` a forged TEE sig | G1 kill | Journal binds `TEE_IMAGE_HASH`+`CONFIG_HASH`; TEEVerifier requires registered signer + `isValidProposer` (owner-set) + image match. |
| L-PORTAL-001 | 2 | `OptimismPortal2.sol:461-486` | Failed target call still finalizes | G1 kill | Matches OP Stack; delegated-EOA failure reverts (rolls back). OP-matching behaviour OOS. `checkWithdrawal` requires `isGameClaimValid`. |
| L-ASR-001 | 2 | `AnchorStateRegistry.sol` | Unprivileged blacklist/retire | G1 kill | Guardian-gated in ASR (trusted). |
| L-KI-* | 1 | SCOPE known-issues table | Re-report KI-02..KI-61 | G1 kill | Public known issues / audits. |
| L-POOL-001 | 3 | `txpool` replay_id | Nonce-free twin after mine | G1 kill | KI-10 residual race. Tests in `pool.rs` cover mined replay_id eviction. |
| L-B20-001 | 3 | B20 precompile mint vs cap | Mint above cap | G1 kill | `golden_mint_reverts_over_supply_cap` on pin; no distinguishing bypass shown. |
| L-BILL-001 | 3 | `gas_limit_fee_billing.rs` | Unused gas refunded under Everest billing | G1 kill | Intended: receipts bill gas_limit (+ payer auth). Covered by in-tree test. |
| L-VAULT-* | 1 | Apex seed/never_generated H-0002+ | Share-price families on L2 proof contracts | G1 kill | Wrong protocol. Not Base NAV/vault. |
| L-DIV-0001 | 1 | unmapped F-TEE | NitroValidator not in contracts workspace | G1 keep as coverage gap | Workspace split, not a bug. Pass 2 closed the attestation path in the nitro pin. |

No lead reached G3 distinguishing execute=true on pinned code. **Verified findings: 0. No FINDING-*.md.**

## Strongest dropped lead

**L-TEE-001 / L-NITRO-001:** debug-mode AWS Nitro attestation (all-zero PCR) into the production signer set.

Why it looked live: NitroValidator explicitly does not enforce PCR/freshness (KI-32 text in-code). Registry comments say registration is PCR0-agnostic for pre-hardfork.

Why it died: `registerSigner` is privileged; debug PCR0 is a hard revert; TEEVerifier still checks `signerImageHash == AggregateVerifier.TEE_IMAGE_HASH` at proof time. Unprivileged path does not exist. G3 was not executed because G1 already killed reachability; forge was not installed.

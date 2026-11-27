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

Money Hunter: `strict` on the contracts clone. Apex report: **0 verified**. Fail-closed coverage because F-TEE maps to NitroValidator (other repo).

## 0b. Toolchains (G3 enablement)

See `findings/TOOLCHAINS.md`. Foundry forge 1.10.1 and SP1 cargo-prove `d83ed91` are installed. G3 execute is now possible. Prior G3 was prepare-only and is not evidence.

## Passes

| Pass | Method | Surfaces | G3 executed? |
|---|---|---|---|
| 1 | Forge on TEEProverRegistry | `registerSigner` unauthorized + debug PCR0 + owner happy path | yes, 3/3 PASS (attack fails) |
| 2 | Forge on pause/portal/games | SystemConfig pause fuzz; OptimismPortal2 finalize; Challenge; Nullify; TEEVerifier | yes, all matched tests PASS |
| 3 | Nitro forge + B20 cargo | `test_AttestationReplayHasNoOnChainProtection`; B20 `golden_mint_reverts_over_supply_cap` | yes; txpool rocksdb compile fail |

## Leads

| ID | Pass | Surface | Claim | Gate | Disposition |
|---|---|---|---|---|---|
| L-TEE-001 | 1+2 | `TEEProverRegistry.sol:154-176` | Unprivileged debug-PCR attestation registers a production signer | G3 kill | forge: unauthorized revert + `InvalidPCR0`. |
| L-NITRO-001 | 2 | `NitroValidator.sol:107-120` | Library accepts debug PCR / no freshness | G3 confirm KI-32 | `test_AttestationReplayHasNoOnChainProtection` PASS (documented). Registry still rejects debug PCR0. |
| L-SYS-001 | 2 | `SystemConfig.sol:598-626` | Unprivileged pause | G3 kill | `testFuzz_pause_notGuardianOrIncidentResponder_reverts` PASS. |
| L-AGG-001 | 2 | `AggregateVerifier.sol:580-648` | `challenge()`/`nullify()` lack `gameOver()` | G3 intended | Challenge 10 + Nullify 9 PASS as written (sequencing, not auth hole). |
| L-AGG-002 | 2 | `AggregateVerifier.sol:515` / `TEEVerifier.sol:57` | Anyone can `verifyProposalProof` a forged TEE sig | G3 kill | TEEVerifier: unregistered signer / invalid proposer / image mismatch FAIL verify. |
| L-PORTAL-001 | 2 | `OptimismPortal2.sol:461-486` | Failed target call still finalizes | G3 kill | `delegatedTargetFails_reverts` PASS; `targetFails_fails` PASS (OP-matching). |
| L-ASR-001 | 2 | `AnchorStateRegistry.sol` | Unprivileged blacklist/retire | G1 kill | Guardian-gated in ASR (trusted). |
| L-KI-* | 1 | SCOPE known-issues table | Re-report KI-02..KI-61 | G1 kill | Public known issues / audits. |
| L-POOL-001 | 3 | `txpool` replay_id | Nonce-free twin after mine | G1 kill | KI-10 residual race. Tests in `pool.rs` cover mined replay_id eviction. |
| L-B20-001 | 3 | B20 precompile mint vs cap | Mint above cap | G1 kill | `golden_mint_reverts_over_supply_cap` on pin; no distinguishing bypass shown. |
| L-BILL-001 | 3 | `gas_limit_fee_billing.rs` | Unused gas refunded under Everest billing | G1 kill | Intended: receipts bill gas_limit (+ payer auth). Covered by in-tree test. |
| L-VAULT-* | 1 | Apex seed/never_generated H-0002+ | Share-price families on L2 proof contracts | G1 kill | Wrong protocol. Not Base NAV/vault. |
| L-DIV-0001 | 1 | unmapped F-TEE | NitroValidator not in contracts workspace | G1 keep as coverage gap | Workspace split, not a bug. Pass 2 closed the attestation path in the nitro pin. |

G3 was executed 2026-11-27 after Foundry install. Commands and logs: `G3-EXECUTED.md`. No attack reproduced. **Verified findings: 0. No FINDING-*.md.**

## Strongest dropped lead (executed)

**L-TEE-001 / L-NITRO-001:** debug-mode AWS Nitro attestation (all-zero PCR) into the production signer set.

G3 outcome: `test_registerSigner_unauthorized_reverts` **PASS**; `test_registerSigner_debugModePCR0_reverts` **PASS** on pin `b9b76d97`. `test_AttestationReplayHasNoOnChainProtection` **PASS** on nitro pin `0ea0d123` (library has no freshness — KI-32). Integrator (registry) still rejects debug PCR0 and unprivileged callers. Not a finding.

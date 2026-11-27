# Base Everest pin

**Never submit.** Competition baseline is the Immunefi forks below, not `base/base` main.

Resolved 2026-11-27 UTC with `git ls-remote … HEAD` against the Immunefi competition remotes. All four HEADs match the SHAs named on the Immunefi resources page.

## Competition commits (source of truth)

| Asset | Remote | Tag / rev named on Immunefi | Full SHA (`HEAD`) |
|---|---|---|---|
| Offchain components | https://github.com/immunefi-team/audit-comp-base-everest-base | v1.6.0-rc.9 `689054ee` | `689054ee14933cb2ee5bd54eadcd8dacbe1cc517` |
| Implementation contracts | https://github.com/immunefi-team/audit-comp-base-everest-contracts | v8.5.0-rc.1 `b9b76d97` | `b9b76d97dca3c420098f597ebc65bee4f28001b7` |
| TEE attestation | https://github.com/immunefi-team/audit-comp-base-everest-nitro-validator | `0ea0d123` | `0ea0d12366b4fa44f9e07e4755f2ad36561cb674` |
| Deployment / upgrade scripts | https://github.com/immunefi-team/audit-comp-base-everest-contract-deployments | `e6797dfd` | `e6797dfd6ac03b35d0ddd7eb369ab94bbc5fcd31` |

Declared EL dependency (not a fifth Immunefi fork; recorded in the client pin):

| Dep | Remote | SHA |
|---|---|---|
| `base/reth` | https://github.com/base/reth | `2b20e42de9c42b51ea0fb56599fda3c2f22640ef` |

## Deployed addresses (pre-Everest Sepolia; fork-only)

See `SCOPE.md` tables. Snapshot: Ethereum Sepolia block 12,149,624 / Base Sepolia block 59,691,356 on 16 Nov 2026.

Primary L1 pins used in this campaign:

| Contract | Proxy / address |
|---|---|
| AggregateVerifier | `0x4234216f1648A8119c6E41e6C0C73956Ecc850Af` |
| OptimismPortal2 | `0x49f53e41452C74589E85cA1677426Ba426459e85` |
| SystemConfig | `0xf272670eb55e895584501d564AfEB048bEd26194` |
| NitroValidator | `0x16970101Ea32243cC80a2e0C91427e8bDA70F689` |
| ZkVerifier | `0xa738E13d97A3f10b307C2CD190edd3E227A72D68` |

Native Everest precompiles (devnet / client pin, not Sepolia): B20Factory `0xB20f…0000`, ActivationRegistry `0x8453…0001`, PolicyRegistry `0x8453…0002`, Nonce Manager `0x8130…aa01`, Transaction Context `0x8130…aa02`.

## Local clones

| Repo | Path | Expected `HEAD` |
|---|---|---|
| audit-comp-base-everest-base | `/agent/repos/audit-comp-base-everest-base` | `689054ee14933cb2ee5bd54eadcd8dacbe1cc517` |
| audit-comp-base-everest-contracts | `/agent/repos/audit-comp-base-everest-contracts` | `b9b76d97dca3c420098f597ebc65bee4f28001b7` |
| audit-comp-base-everest-nitro-validator | `/agent/repos/audit-comp-base-everest-nitro-validator` | `0ea0d12366b4fa44f9e07e4755f2ad36561cb674` |
| audit-comp-base-everest-contract-deployments | `/agent/repos/audit-comp-base-everest-contract-deployments` | `e6797dfd6ac03b35d0ddd7eb369ab94bbc5fcd31` |

Apex workspace for the Money Hunter case file: contracts clone (EVM profile, Foundry G3). Client clone is the offchain/DLT workspace. Do **not** re-pin to `base/base` main.

## Not the pin

- `base/base` main after v1.6.0-rc.9
- Public Base Sepolia / Base mainnet / Zeronet as live targets
- Mid-contest public fixes listed after their Immunefi changelog timestamp (KI-59/60/61 public on 24 Nov 2026 on `base/base` v1.5.7; competition commit may still contain the pre-fix code — treat as **public known issues**, not new findings)

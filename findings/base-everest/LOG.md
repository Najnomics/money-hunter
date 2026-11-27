# Base Everest campaign log

Never submit. Never print keys. Four gates: **G1 Divergence** · **G2 Hypothesis** · **G3 Experiment on pinned real code (no mocks)** · **G4 Validate**. Three independent passes. A lead is a finding only if all four gates plus an honest regression (reproduces, then dies after a minimal fix) pass.

## 0. Pin check (2026-11-27)

| Clone | `git rev-parse HEAD` | Match Immunefi pin? |
|---|---|---|
| `/agent/repos/audit-comp-base-everest-base` | `689054ee14933cb2ee5bd54eadcd8dacbe1cc517` | yes |
| `/agent/repos/audit-comp-base-everest-contracts` | `b9b76d97dca3c420098f597ebc65bee4f28001b7` | yes |
| `/agent/repos/audit-comp-base-everest-nitro-validator` | `0ea0d12366b4fa44f9e07e4755f2ad36561cb674` | yes |
| `/agent/repos/audit-comp-base-everest-contract-deployments` | `e6797dfd6ac03b35d0ddd7eb369ab94bbc5fcd31` | yes |

Mid-Contest Changelog at SCOPE capture: empty. Public KI-59/60/61 fixes on 24 Nov 2026 stay **known issues**, not candidates.

## Leads

| ID | Pass | Surface | Claim | Gate | Disposition |
|---|---|---|---|---|---|
| (filled as hunts run) | | | | | |

## Pipeline notes

- Apex workspace: `/agent/repos/audit-comp-base-everest-contracts` (EVM/Foundry).
- Client workspace: `/agent/repos/audit-comp-base-everest-base` (native/Rust).
- Nitro workspace: `/agent/repos/audit-comp-base-everest-nitro-validator`.

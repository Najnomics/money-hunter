# Base Everest — campaign summary

**Never submit.**

| Field | Result |
|---|---|
| Pin | `base` `689054ee14933cb2ee5bd54eadcd8dacbe1cc517`; `contracts` `b9b76d97dca3c420098f597ebc65bee4f28001b7`; `nitro-validator` `0ea0d12366b4fa44f9e07e4755f2ad36561cb674`; `contract-deployments` `e6797dfd6ac03b35d0ddd7eb369ab94bbc5fcd31` |
| Harness | `bin/money-hunter` policy `strict`, all four gates |
| Passes | 3 (pipeline on contracts; boss-skill TEE/nitro/multiproof; boss-skill client replay/B20/billing) |
| In-scope coverage | All four Immunefi assets listed in `SCOPE.md` were pinned and sampled. Contracts `src/` fully AST-mapped (541 surfaces). Nitro `src/` reviewed. Client sampled on replay_id, gas-limit billing, B20 cap — not every one of 135k nSLOC. |
| **Verified count** | **0** |
| Titles / severities | none |
| Strongest dropped lead | Debug-PCR Nitro attestation into production signer set — killed at G1 (`onlyOwnerOrManager` + debug PCR0 revert + proof-time image hash). See `LOG.md` L-TEE-001 / L-NITRO-001. |
| Apex | 94 DIV, 407 H-*, 65 prepared experiments, 1 disproved (H-0001), 0 verified. Coverage fail-closed (F-TEE NitroValidator lives in the other repo). |
| FINDING files | none (none passed G1–G4 + regression) |

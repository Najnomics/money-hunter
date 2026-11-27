# Base Everest — campaign summary

**Never submit.**

| Field | Result |
|---|---|
| Pin | `base` `689054ee14933cb2ee5bd54eadcd8dacbe1cc517`; `contracts` `b9b76d97dca3c420098f597ebc65bee4f28001b7`; `nitro-validator` `0ea0d12366b4fa44f9e07e4755f2ad36561cb674`; `contract-deployments` `e6797dfd6ac03b35d0ddd7eb369ab94bbc5fcd31` |
| Harness | `bin/money-hunter` policy `strict`, all four gates; G3 **executed** with forge 1.10.1 |
| Passes run | **3 executed** — (1) TEE registerSigner forge tests; (2) SystemConfig pause + Portal finalize + Challenge/Nullify/TEEVerifier; (3) Nitro replay/sig + B20 supply-cap cargo golden |
| In-scope coverage | All four Immunefi assets pinned. Contracts `src/` AST-mapped. Nitro tests run. Client B20 golden run. txpool replay_id test did not compile (rocksdb C++ headers). |
| **Verified count** | **0** |
| Titles / severities | none |
| Strongest dropped lead | L-TEE-001 debug-PCR signer registration — G3 **PASS as kill**: unauthorized + `InvalidPCR0`. See `G3-EXECUTED.md`. |
| FINDING files | none (none passed G1–G4 + regression that reproduces an attack) |

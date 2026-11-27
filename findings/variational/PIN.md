# Variational pin

**Never submit.** Live program: pin **deployed Arbitrum addresses**, not `main` of an unpublished Solidity repo.

Resolved 2026-11-27 UTC from Immunefi + docs.variational.io.

## Deployed addresses (Arbitrum One)

| Name | Address |
|---|---|
| Core OLP Vault | `0x74bbbb0e7f0bad6938509dd4b556a39a4db1f2cd` |
| Protocol Treasury | `0x5e91b40467fb8902c46a7b6cb90482363188d645` |
| Settlement Pool Factory | `0x0F820B9afC270d658a9fD7D16B1Bdc45b70f074C` |
| Oracle (docs only; not on Immunefi table) | `0x84BE56470d45b7f6629A66A219a38681F6BA6172` |

G3: local **fork** of Arbitrum at these addresses. Live `eth_send` is forbidden.

## Public git (off-chain SDK; archived)

| Remote | HEAD |
|---|---|
| https://github.com/variational-research/variational-sdk-python | `ce3bf96171b23dd9095354be530150c2b079917f` |

No public Solidity repository for the three contracts was found in the org listing. Sourcify v2 full-match for the OLP vault returned 404. Do not treat the Python SDK as the on-chain pin.

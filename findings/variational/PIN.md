# Variational pin

**Never submit.** Live program: pin **deployed Arbitrum addresses**, not `main` of an unpublished Solidity repo.

Resolved 2026-11-27 UTC from Immunefi + docs.variational.io.

## Deployed addresses (Arbitrum One)

| Name | Address |
|---|---|
| Core OLP Vault | `0x74bBBb0E7F0bAd6938509Dd4B556a39A4Db1F2Cd` (EOA, codesize 0 on fork) |
| Protocol Treasury | `0x5E91B40467fB8902c46a7b6Cb90482363188D645` (EOA, codesize 0 on fork) |
| Settlement Pool Factory | `0x0F820B9afC270d658a9fD7D16B1Bdc45b70f074C` (Sourcify exact_match) |
| Oracle (docs only; not on Immunefi table) | `0x84BE56470d45b7f6629A66A219a38681F6BA6172` (Sourcify exact_match) |

G3: local **fork** of Arbitrum at these addresses. Live `eth_send` is forbidden.

## Public git (off-chain SDK; archived)

| Remote | HEAD |
|---|---|
| https://github.com/variational-research/variational-sdk-python | `ce3bf96171b23dd9095354be530150c2b079917f` |

No public Solidity repository for the three Immunefi addresses was found in `org:variational-research`. Sourcify 404 on the OLP/treasury EOAs; exact_match on factory + oracle. Do not treat the Python SDK as the on-chain pin.

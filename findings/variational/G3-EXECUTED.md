# Variational — executed G3 (fork + Sourcify + local HMAC)

Never submit. Never send txs to Arbitrum or omni.variational.io.

Fork RPC (read-only): `https://arb1.arbitrum.io/rpc` at block ~528,139,968.

## Pass 1 — on-chain pin vs verified source

Sourcify v2:

| Address | Role | Sourcify | codesize (fork) |
|---|---|---|---|
| `0x74bBBb0E7F0bAd6938509Dd4B556a39A4Db1F2Cd` | Immunefi Core OLP Vault | 404 | **0** (EOA; ~73.37M USDC + 1.78 ETH) |
| `0x5E91B40467fB8902c46a7b6Cb90482363188D645` | Immunefi Treasury | 404 | **0** (EOA; ~14.41M USDC + 2.18 ETH) |
| `0x0F820B9afC270d658a9fD7D16B1Bdc45b70f074C` | Settlement Pool Factory | **exact_match** 2025-08-27 | 4695 |
| `0x84BE56470d45b7f6629A66A219a38681F6BA6172` | Oracle (docs, not Immunefi table) | **exact_match** | 18917 |

Arbiscan/Blockscout HTML APIs: Cloudflare 403. Sourcify supplied verified factory/pool. No public `org:variational-research` Solidity repo.

## Pass 2 — factory/pool on verified source + fork

Sources saved under `onchain/src/`. `createPool` requires `owner() || oracle`. Pool `withdrawUSDC` / `withdrawFees` are `onlyOracle`.

```
forge test --fork-url https://arb1.arbitrum.io/rpc -vv
```

in `findings/variational/g3-fork/`: **3 passed** — vault/treasury no code; unprivileged `createPool` reverts `caller must be owner or oracle`; factory owner nonzero.

## Pass 3 — HMAC (SDK, no live API)

`python3 findings/variational/g3-hmac/test_hmac.py` **PASS**: timestamp and body bound; wrong secret differs.

**Verified findings: 0.** OLP/treasury funds sit in EOAs (key-custody / operational), not unprivileged contract bugs. Factory/pool theft paths are owner/oracle-gated (trusted / PoI would still need oracle compromise).

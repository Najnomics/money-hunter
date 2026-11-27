# Variational campaign log

Never submit. Never live-test omni.variational.io or send Arbitrum txs. Four gates. Pin is **deployed addresses**.

## Pin (re-checked 2026-11-27 G3)

| Item | Value |
|---|---|
| Core OLP Vault | `0x74bBBb0E7F0bAd6938509Dd4B556a39A4Db1F2Cd` — **codesize 0**, ~73.37M USDC |
| Protocol Treasury | `0x5E91B40467fB8902c46a7b6Cb90482363188D645` — **codesize 0**, ~14.41M USDC |
| Settlement Pool Factory | `0x0F820B9afC270d658a9fD7D16B1Bdc45b70f074C` — Sourcify exact_match, `SettlementPoolFactory` |
| Oracle (docs) | `0x84BE56470d45b7f6629A66A219a38681F6BA6172` — Sourcify exact_match |
| SDK | `ce3bf96171b23dd9095354be530150c2b079917f` |

## Passes

| Pass | Method | G3 |
|---|---|---|
| 1 | Sourcify + fork `eth_getCode` / USDC `balanceOf` | vault/treasury EOA; factory verified |
| 2 | Fork forge tests on factory | unprivileged `createPool` reverts |
| 3 | Local HMAC + verified pool `onlyOracle` withdraw | HMAC bound; withdraws oracle-gated |

## Leads

| ID | Claim | Gate | Disposition |
|---|---|---|---|
| L-VAULT-SRC | Theft from OLP vault contract | G3 kill | Vault has no bytecode. Fork `test_olp_vault_and_treasury_have_no_code` PASS. Funds in EOA. |
| L-FACTORY | Unprivileged `createPool` / fee `transferFrom` | G3 kill | Reverts unless owner/oracle. Fork PASS. |
| L-POOL-WD | Unprivileged pool USDC withdraw | G1/G3 kill | `withdrawUSDC` / `withdrawFees` `onlyOracle` on verified source. |
| L-HMAC | Forge API HMAC | G3 kill | Local test: timestamp+body bound; wrong secret differs. Live API forbidden. |
| L-PERMIT | Unlimited permit drain | G1 kill | Helper; user supplies key. |
| L-ROUND | Client rounding extracts OLP | G1 kill | Client-side only. |
| L-WEB | XSS on omni | G1 kill | Live website testing prohibited. |

**Verified findings: 0. No FINDING-*.md.**

## Strongest dropped lead (executed)

**L-VAULT-SRC:** Immunefi names a Core OLP Vault address. Fork shows it is an **EOA** with large USDC, not a Solidity vault. There is no unprivileged contract entrypoint to test. Factory/pool (verified) keep `createPool` and withdrawals behind owner/oracle.

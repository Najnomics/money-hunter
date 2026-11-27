# Variational campaign log

Never submit. Never live-test omni.variational.io or Arbitrum. Four gates. Pin is **deployed addresses**.

## Pin

| Item | Value |
|---|---|
| Core OLP Vault | `0x74bbbb0e7f0bad6938509dd4b556a39a4db1f2cd` |
| Protocol Treasury | `0x5e91b40467fb8902c46a7b6cb90482363188d645` |
| Settlement Pool Factory | `0x0F820B9afC270d658a9fD7D16B1Bdc45b70f074C` |
| SDK (not the on-chain pin) | `ce3bf96171b23dd9095354be530150c2b079917f` |
| Sourcify vault | 404 |
| Public Solidity repo | none found in variational-research |

## Passes

| Pass | Method | Surfaces |
|---|---|---|
| 1 | Money Hunter `strict` on archived Python SDK | 5 DIV, 1 H-* disproved, 0 verified |
| 2 | Boss-skill SDK auth/permit/rounding | `auth.py` HMAC+timestamp; `permit.py` EIP-712; `rounding.py` HALF_UP |
| 3 | On-chain pin / docs quoting | Three Immunefi contracts + Omni URL + PoI; no bytecode source; live G3 forbidden |

## Leads

| ID | Claim | Gate | Disposition |
|---|---|---|---|
| L-VAULT-SRC | Theft from OLP vault | G3 not possible | No published implementation; Sourcify 404; Foundry/cast missing; live fork of mainnet txs forbidden. Not a finding. |
| L-HMAC | Forge API HMAC | G1 kill / G4 DP-0001 | MAC includes `key\|timestamp\|method\|path\|body`. Forgery needs secret. Replay window needs live API (forbidden). |
| L-PERMIT | Unlimited permit drain | G1 kill | `sign_and_submit_unlimited` is an explicit helper; user supplies key. Not unprivileged theft. |
| L-ROUND | Client rounding extracts OLP | G1 kill | Client-side `ROUND_HALF_UP` only; server quoting is the in-scope economic logic and was not live-tested. |
| L-WEB | XSS/subdomain on omni | G1 kill | Live website testing against production is prohibited. Theoretical web OOS. |
| L-ORACLE | Docs oracle address | G1 | Not on Immunefi assets table unless Crit theft via PoI; no source. |

**Verified findings: 0. No FINDING-*.md.**

## Strongest dropped lead

**L-VAULT-SRC / quoting-economic Crit:** the program’s highest-paid impact is OLP/treasury extraction, but the in-scope contracts have no public source and G3 on a mainnet fork was not available without live-network tooling. That is an incomplete hunt on the vault bytecode, not a claim the vault is clean.

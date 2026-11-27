# Variational — public Immunefi scope

Sources (public pages only; **never submit; never contact anyone**):

- https://immunefi.com/bug-bounty/variational/information/
- https://immunefi.com/bug-bounty/variational/scope/
- https://docs.variational.io/technical-documentation/mainnet-contracts
- https://docs.variational.io/technical-documentation/security-and-audits
- https://docs.variational.io/technical-documentation/bug-bounties

Captured 2026-11-27 UTC.

## Program

| Field | Value |
|---|---|
| Program | Variational (Omni perps) |
| Live since | 16 Mar 2026; last updated 24 Nov 2026 |
| Max bounty | $100,000 (SC Crit 10% FAR, min $10k) |
| Chain | Arbitrum; payouts USDC |
| Policy | Primacy of Rules, plus Primacy of Impact for **SC Crit direct theft of funds** and **Web Crit direct theft of funds** |
| PoC | Required |
| KYC | Required |
| Publication | Category 3 |
| Testing | Local forks only. **No** mainnet/public-testnet testing, **no** live omni.variational.io exploitation |
| Harness | Money Hunter `strict` + four gates |

## Assets in scope (entire list)

| Kind | Name | Target |
|---|---|---|
| Contract | Core OLP Vault | `0x74bbbb0e7f0bad6938509dd4b556a39a4db1f2cd` (Arbitrum) |
| Contract | Variational Protocol Treasury | `0x5e91b40467fb8902c46a7b6cb90482363188d645` |
| Contract | Settlement Pool Factory | `0x0F820B9afC270d658a9fD7D16B1Bdc45b70f074C` |
| Website | Omni app | https://omni.variational.io/ |
| Placeholder | Primacy of Impact | (SC Crit theft) |
| Placeholder | Primacy of Impact | (Web Crit theft) |

Docs also list Oracle `0x84BE56470d45b7f6629A66A219a38681F6BA6172`. That address is **not** on the Immunefi assets table; it is only in-scope via Primacy of Impact if a **Critical direct theft** is demonstrated.

## Severity table

**Smart Contract — Critical** (PoI for direct theft)

- Quoting and economic logic: exploitable flaws in Variational-operated quoting, pricing, execution, margin, liquidation, funding, accounting, or settlement (off-chain services, APIs, web, contracts) enabling unauthorized extraction/loss of user, OLP, or treasury funds, or protocol insolvency
- Direct theft of any user funds at-rest or in-motion other than unclaimed yield
- Permanent freezing of funds
- Protocol insolvency

**Website & Application — Critical**

- Execute arbitrary system commands
- Retrieve sensitive data/files from a running server (`/etc/shadow`, DB passwords, blockchain keys)
- Taking down the application/website
- Taking/modifying authenticated actions on behalf of other users without their interaction (registration, comments, voting, trades, withdrawals, …)
- Subdomain takeover with already-connected wallet interaction
- Direct theft of user funds
- Malicious interactions with an already-connected wallet (tx args, contract substitution, malicious txs)
- Injection of malicious HTML or XSS through metadata

**Rewards (information page)**

| Track | Crit | High | Medium | Low |
|---|---|---|---|---|
| Smart Contract | $10k–$100k (10% FAR, PoI theft) | $3.5k–$25k (unclaimed yield/temp freeze rules) | $3,500 flat | — |
| Websites | $10k–$50k (PoI theft / key leak) else Crit flat $10k | $10,000 flat | $2,000 | $1,000 |

Repeatable-attack and pause/upgrade limitations apply as on the information page.

## Out of scope

**Websites (program list):** theoretical without PoC; physical/local-network; reflected plaintext injection (HTML/JS and persistent plaintext still in); self-XSS; captcha OCR without impact; CSRF without state impact; missing headers/cookie flags without impact; non-confidential SSR; user enumeration; un-prompted in-app actions; SSL best practices; DDoS-only; UX without material disruption; browser/plugin defects; non-sensitive API keys; browser-bug exploits; SPF/DMARC; scanner dumps; NFT rendering.

**Default SC:** third-party oracle incorrect data (manipulation/flashloans remain valid); 51%; liquidity; Sybil; centralization.

**Default all:** already-exploited damage; leaked keys; privileged addresses without extra privilege; external depeg not caused by code; GitHub secrets without production proof; best practices; feature requests; test/config files; phishing.

**Operator:** no live mainnet testing; no contact; no submit.

## Known issues

- Unfixed items in Spearbit (Mar 2025) and Zellic (Dec 2024) audits at https://docs.variational.io/technical-documentation/security-and-audits
- No public KI table on the Immunefi page beyond default + those audits

## Source

Immunefi points at https://github.com/variational-research. Public org listing at capture showed **variational-sdk-python** (archived). On-chain implementations were **not** published as a public Solidity repo. Pin is therefore **deployed addresses**, not a git SHA. Sourcify full-match 404 for the OLP vault at capture. G3 requires a local fork of Arbitrum state of those addresses, no mocks.

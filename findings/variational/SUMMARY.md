# Variational — campaign summary

**Never submit.**

| Field | Result |
|---|---|
| Pin | Arbitrum addresses in `PIN.md`; factory Sourcify exact-match 2025-08-27; SDK `ce3bf961` |
| Harness | four gates; G3 **executed on a local Arbitrum fork** (no live txs) |
| Passes run | **3 executed** — (1) Sourcify + fork codesize/USDC; (2) factory `createPool` fork revert + verified pool `onlyOracle` withdraw; (3) local HMAC unit test |
| **Verified count** | **0** |
| Titles / severities | none |
| Strongest dropped lead | L-VAULT-SRC: Immunefi “Core OLP Vault” has **no code** (EOA holding ~73M USDC). Fork test `test_olp_vault_and_treasury_have_no_code` **PASS**. Not a contract theft RC; custody of the EOA is out of unprivileged SC scope. |
| FINDING files | none |

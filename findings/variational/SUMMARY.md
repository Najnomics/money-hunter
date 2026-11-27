# Variational — campaign summary

**Never submit.**

| Field | Result |
|---|---|
| Pin | Arbitrum `0x74bbbb…f2cd` (OLP), `0x5e91b4…d645` (treasury), `0x0F820B…074C` (factory). SDK HEAD `ce3bf961` is **not** the contract pin. |
| Harness | `bin/money-hunter` `strict` + four gates |
| Passes | 3 (SDK pipeline; HMAC/permit/rounding; deployed-address/docs without live testing) |
| In-scope list | All Immunefi table rows covered at pin/docs level. Vault/treasury/factory **bytecode not sourced**. Omni not live-tested. |
| **Verified count** | **0** |
| Titles / severities | none |
| Strongest dropped lead | OLP vault theft / quoting logic — blocked before G3 by missing public source and no-live-test rule |
| FINDING files | none |
| Apex (SDK workspace) | 5 DIV, 1 H-* disproved, 0 verified |

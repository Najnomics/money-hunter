# Lido Lend campaign scope

Pin: [PIN.md](PIN.md). Bytecode at mainnet block `26508283`. Source clones at deploy/release SHAs, not repo HEAD.

## In scope (this campaign)

- Deployed contracts listed on https://docs.lido.fi/lend/deployed-contracts/ (runtime bytecode).
- Source used only to read the pin: `lend` `422d589`, `lend-irm` `566d31f`, `lend-markets` `9c0ba34`, `lend-guardian-daemon` `v0.1.0` `src/`, Easy Track factories `4caa911`.
- Web: https://lend.lido.fi

## Impacts (program)

SC Crit: theft of user funds (excluding unclaimed yield), permanent freeze, insolvency, theft/freeze of protocol fees.  
SC High: theft/freeze of unclaimed yield, temporary freeze ≥24h, extract guardian signing key (unprivileged), acquire a role without grant.  
SC Med: block stuffing, griefing.  
SC Low: fails promised returns with no value loss.

Web Crit/High/Med/Low as given in the operator brief.

## Out of scope / known (not reported)

Deployed bytecode not repo HEAD; releases not develop; Morpho and Lido Lend audits; Morpho whitepaper; documented intended/accepted risks; expected tests; GitHub issues with the same root cause; guardian files outside `src/`; most guardian impacts except early heartbeat, wrong/missing flag, suspect by unprivileged, or key extract; documented rounding; bad debt from price; role used within its authority; parameter choices; third-party screening; normal frontrun.

## PoC rules

Fork of the pinned deployed contracts only. Transactions only. Funds-at-risk calculation required. Attack window 1h if a pause is involved. Never submit. Never print secrets.

## Harness

Money Hunter (this repo) plus Najnomics/boss-skill `audit-map-hunter`. Four gates: divergence, hypothesis, experiment, validate. Three SC passes, then web.

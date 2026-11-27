# Plether contest scope (blind, no finding bodies)

Sources used (contest pages and in-repo docs only; **reports.immunefi.com finding bodies were not read**):

- https://immunefi.com/audit-competition/plether/scope/
- https://immunefi.com/audit-competition/plether/information/
- https://immunefi.com/audit-competition/plether/resources/
- https://github.com/immunefi-team/audit-comp-plether
- Target pin: `packages/perps/SECURITY.md`, `ACCOUNTING_SPEC.md`, `CANONICAL_ENTRYPOINTS.md`, `INTERNAL_ARCHITECTURE_MAP.md`, `DEPLOYMENT.md`

## Pin

| Field | Value |
|---|---|
| Contest | Immunefi Plether Perps audit competition |
| Repo | https://github.com/immunefi-team/audit-comp-plether |
| Commit | `a82d4fefb02768e5b3bddcc97dee371eee24fea8` |
| Local clone | `/agent/repos/audit-comp-plether` |
| Campaign policy | `strict` |
| TargetProfile | `evm` |
| Apex workspace | `/agent/repos/audit-comp-plether/.apex/` |

`git rev-parse HEAD` and `git log -1 --oneline` at campaign start: `a82d4fe`.

## In scope

All Solidity under `packages/perps/src` **except** the six view-only contracts listed below.

**Explicitly in scope (called out on the contest page):**

- `CfdEngineLens.sol`
- `CfdEngineProtocolLens.sol`

Import-use of `packages/shared` (`DecimalConstants`, `IPyth`) is in-scope as used by perps; bugs **inside** `packages/shared` are not.

## Out of scope (contest)

View-only / lens files excluded on the program page:

- `packages/perps/src/CfdEngineAccountLens.sol`
- `packages/perps/src/PerpsPublicLens.sol`
- `packages/perps/src/CfdClosePreview.sol`
- `packages/perps/src/SettlementMonitorLens.sol`
- `packages/perps/src/SettlementMonitorLensSidecar.sol`
- `packages/perps/src/CfdEngineOpenQuoter.sol`

Also OOS: `packages/shared`, `packages/spot`, `packages/options`, `packages/perps-aa`, `packages/perps-aa-client`, tests/scripts/docs, `integration/`, keepers, oracle worker, gas sponsor/paymaster, bundler, frontend (`plether-app`), Across bridge route, theoretical no-PoC observations, leaked keys, privileged-role malice, 51%/Sybil/depeg-without-code-bug, centralization-as-finding, mainnet testing, DoS of project assets, third-party oracle incorrect data (oracle *manipulation/flashloans remain valid*), inactive feature flags/networks.

## Known issues (scope exclusions, not contest finding bodies)

Program page lists prior Cecuro items as known: MED-7, MED-13, MED-16, LOW-57, MED-22, MED-24, MED-29, MED-30; HIGH-1 Arbitrum/Pyth clock alignment unless net-profitable extraction beyond the limitation; `SECURITY.md` Known Limitations; previous audit reports including acknowledged sections.

This campaign treated those titles as **out-of-scope exclusions**. The bodies of the 69 Immunefi reports were not opened.

## Severity (program)

| Severity | Program definition used |
|---|---|
| Critical | Direct theft of user funds other than unclaimed yield; permanent freeze of funds; protocol insolvency |
| High | Permanent freeze of unclaimed yield; temporary freeze ≥24h; theft of unclaimed yield |
| Medium | Theft of gas; lack of token funds; block stuffing; griefing; unbounded gas; temporary freeze ≥1h |
| Low / Insight | Defense-in-depth; not a paid bug unless Insight terms apply |

Release params used when judging freeze/theft (`DEPLOYMENT.md`): MM 0.1%, IM 0.2%, frozen-market margin 3%, exec fee 0.04%, frozen-close spread 0.50%, Senior cap 40M USDG and 80% of pool.

## Program constraints that bound this run

- PoC required by the program. Operator instruction for **this** agent: do **not** write or execute PoCs; queue precise specs in `POC-QUEUE.md` for a separate Composer agent.
- Keepers are untrusted. Contracts are non-upgradeable.
- Apex Gate 3 still requires executed evidence to promote a verified finding. With execute=false, verified count is defined to be 0.

## Campaign result (honest)

`.apex/06_final_report.md` summary: **0 verified findings**, 4 unverified candidates, 68 divergences, 3 pipeline issues.

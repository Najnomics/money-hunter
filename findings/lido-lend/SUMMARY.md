# Lido Lend campaign summary

**Never submit.** Immunefi Lido Lend, bytecode pin, four gates. Harness: Money Hunter + audit-map-hunter.

## Verified findings

**0.** No `FINDING-*.md` / `FINDING-*.txt` written (verified-only rule).

## Pin SHAs

Bytecode snapshot: mainnet block **26508283** (`eth_getCode` keccak table in [PIN.md](PIN.md)).

| Repo | Deploy / tag used |
|---|---|
| lidofinance/lend | deploy `422d589f9d098124249b54b55306884165833207` (v1.0.0 / audit `4d55f1dd…`) |
| lidofinance/lend-irm | deploy `566d31f7dfdf83d07a6593f641f7474c263a7f89` (v1.0.1 / audit `97af4c39…`) |
| lidofinance/lend-markets | deploy `9c0ba34580ab5cff4354be8cb701419fb02b65d5` (audit `23416c43…`; HEAD `cfc464c` not hunted) |
| lidofinance/lend-guardian-daemon | tag `v0.1.0` `846f197cd33c7bb3a05facf44db50a45eb27cca4` (`src/` only) |
| lidofinance/easy-track | `4caa9117435631ef352d263c901fa9e26cfccfb4` |
| lidofinance/circuit-breaker | tag `1.0.0` `6829a5a962ece56564bd9d72d01c29cabf157579` |

## Pass ledger

| Pass | Artifact | Keep | Kill | Verified |
|---|---|---:|---:|---:|
| 1 Gate 1 | [PASS-1.md](PASS-1.md), [hunters/pass1.json](hunters/pass1.json) | 2 | 14 | 0 |
| 2 Gates 2–3 | [PASS-2.md](PASS-2.md), [poc/fork_poc.py](poc/fork_poc.py) | 0 | 2 (L-P1-001, L-P1-002) | 0 |
| 3 | [PASS-3.md](PASS-3.md), [hunters/pass3.json](hunters/pass3.json) | 0 | 13 | 0 |
| 4 | [PASS-4.md](PASS-4.md) | 0 | 11 | 0 |
| 5 | [PASS-5.md](PASS-5.md) | 0 | 10 | 0 |
| 6 | [PASS-6.md](PASS-6.md), [poc/fork_poc.py](poc/fork_poc.py) (`006`) | 0 | 12 | 0 |
| Web | [WEB.md](WEB.md) | 0 | n/a | 0 |

L-P1-001: adapter `minExitAssets` is the documented loan+debtCanceled floor; live market `lastUpdate=0`; rounding gap 1 wei. Kill.

L-P1-002: both exit books `lastRequestId=0`; `fillExitRequest` reverts `RequestClosed`; debit-before-withdraw fail-closed. Kill.

Proposed WETH/wstETH satellite proxies are initialized, empty, and admin'd by Lido Agent `0x3e40d73e…`. Core market not created. `lend.lido.fi` is a noindex static page with no wallet.

Passes 4–6 (SC only, skip web): Morpho fork delta, empty exit books, CircuitBreaker pause bounds, IRM/Easy Track/Preseeder, GuardianSignals + daemon `src/`, controller/vault/oracle pre-activation, Bundler3 adapters. All additional leads killed. Still **0** verified. No Immunefi submission.

## Paths

```
findings/lido-lend/PIN.md
findings/lido-lend/SCOPE.md
findings/lido-lend/PASS-1.md
findings/lido-lend/PASS-2.md
findings/lido-lend/PASS-3.md
findings/lido-lend/PASS-4.md
findings/lido-lend/PASS-5.md
findings/lido-lend/PASS-6.md
findings/lido-lend/WEB.md
findings/lido-lend/SUMMARY.md
findings/lido-lend/poc/fork_poc.py
findings/lido-lend/hunters/pass1.json
findings/lido-lend/hunters/pass3.json
```

Branch: `cursor/lido-lend-audit`. No Immunefi submission.

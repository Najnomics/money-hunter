# SC pass 1 — Gate 1 (divergence)

**Never submit.** Neutral map of what was opened against the pin in [PIN.md](PIN.md). A keep is not a finding.

Clones (detached):

| Tree | SHA |
|---|---|
| `/agent/repos/lido-lend` | `422d589f9d098124249b54b55306884165833207` |
| `/agent/repos/lido-lend-irm` | `566d31f7dfdf83d07a6593f641f7474c263a7f89` |
| `/agent/repos/lido-lend-markets` | `9c0ba34580ab5cff4354be8cb701419fb02b65d5` |
| `/agent/repos/lido-lend-guardian-daemon` | `846f197cd33c7bb3a05facf44db50a45eb27cca4` (`v0.1.0`, `src/` only) |
| `/agent/repos/lido-easy-track` | `4caa9117435631ef352d263c901fa9e26cfccfb4` |

Docs read before bodies: `lend` SPECIFICATION/FORK_NOTES/SECURITY; `lend-markets` architecture, roles, guardian-signals, lender-settlement.

## Subsystems opened

Core `settle` and `_hook`; `GuardianSignals` auth, heartbeat, flag, suspect, prune; `LidoLendMarketController.on` / `_handleSettle` / supply cap; `LidoLendERC4626` managed shares and exits; `IrmRouter.setMarketIrm`; `AdaptiveCurveConfig` immutables; `WstEthRateOracle`; Bundler3 adapters; Exit Book fill; guardian-daemon `src/` signing path.

## Gate 1 summary

| | Count |
|---|---:|
| Leads | 16 |
| Keep (pass 2) | 2 |
| Kill | 14 |

Keeps are in [hunters/pass1.json](hunters/pass1.json): vault-adapter slippage uses up-rounded debt cancellation; Exit Book fill records the debit before the source withdraw (needs a distinguishing revert path).

No Gate 3 experiment this pass. Verified count remains 0.

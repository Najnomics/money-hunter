# Past-audit index (dedupe set) — from docs.lido.fi/lend/audits (fetched 2026-11-27)

Program rule: past audit findings are out of scope (same-root-cause dedupe).

| Audit | Date | Object (commit) | Result |
|---|---|---|---|
| Cyfrin | 2026-10-26 | lend 4d55f1d + lend-irm 97af4c3 + lend-markets 23416c4, 53 files | 62 findings: 0 crit, 0 high, 8 med, 27 low, 21 info, 6 gas; 30 resolved / 1 partial / 31 acknowledged |
| MixBytes | 2026-11-09 | lend-guardian-daemon SDK b566e01 | 16 findings: 1 high, 8 med, 7 low |
| Cyfrin + MixBytes | 2026-05-01 | CircuitBreaker b4b2fbc | details not listed |
| Cyfrin | 2026-04-06 | CircuitBreaker formal verification | details not listed |
| Spearbit / Cantina / OZ | 2025-01..02 | Bundler3 (Morpho upstream) | upstream |
| MixBytes | 2026-11-16 | Easy Track factories + LidoLendPreseeder 4caa911 | 11 low: 1 fixed, 10 acknowledged |
| Cyfrin | 2026-11-16 | Deployment verification: runtime bytecode, constructor args, immutables, proxy checks, WETH/wstETH wiring (lend-markets 9c0ba34) | verification report |

Dedupe consequence: the 8 Cyfrin mediums are the most likely collision class for
pass-2 hypotheses. The full Cyfrin report was not locally available at campaign
start; candidates must carry a `why_not_known_issue` field and state why the
finding survives the 0-crit/0-high audit outcome (post-audit commits are within
the pinned audit set, so a missed crit/high is possible but must be argued
against audit coverage, not assumed).

Frontier intel (2026-11-27):
- Lido bug bounty: 43 reports, >$395k paid lifetime (docs.lido.fi/security/bugbounty).
- Immunefi 2026 lending research: 33+ lending/CDP hacks in 2026, median loss
  $756k; >1yr-old protocols most hit — supports focusing on settled accounting
  surfaces rather than fresh-deploy plumbing.
- No public contest results for Lido Lend itself.

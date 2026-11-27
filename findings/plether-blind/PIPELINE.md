# Blind pipeline log

Ran apex-core 1.1.0 grouped CLI (`python main.py <phase> <group> --action …`) plus boss-skill-style subsystem hunts against pin `a82d4fe`.

## Apex phases

| Phase | Tools run | Outcome |
|---|---|---|
| 0 Ground | scope, rules, boundaries, environment | Bound `packages/perps/src`, strict policy, 20 rules. Environment initially `ready=false` (forge/slither missing); later installed Foundry 1.10.1 and slither-analyzer in venv. |
| 1 Research | docs, audits, intel, cves | 14 docs / 723 claims. Past-audit ingest saw markdown only (PDF reports not parsed). Intel corpus missing → 0 hits. |
| 2 Model | flows, invariants, vocab, sinks, skeleton, prediction | 14 flows / 8 critical, 18 invariants, 18 vocab, 6 sinks, 8 predictions. **All 8 blind skeletons started at OOS `CfdClosePreview.sol`** because `make_blind_skeleton` failed to match `Name.fn(types)` and fell back to the first 80 surfaces. |
| 3 Divergence | ast, sweep, inventory, prediction_diff | 50 `undocumented_entrypoint` (cap), 8 `unmapped_critical_flow` (0 critical flows mapped — last-token AST matcher uses argument types). Slither sweep: rc 255 + 2MB stdout cap → **0 detectors admitted**. Independent slither file dump: 188 detectors. Two later `prediction_design_wrong` DIVs for live hunter leads. |
| 4 Specialists | state, trust, dimensional, reverse, assumptions, battery | 4 hypotheses. Lenses bound to **constructors** (same matching bug). 5 assumptions. Vault battery recorded L-LP-001 as not_triggered (already Gate 1 killed). |
| 5 Experiment | sandbox, test, record | Sandbox written. Invariant tests **prepared, not executed** (`execute=false`). Experiments E-0001..E-0004 verdict `pending`. |
| 6 Validate | disprove, classify, coverage, citations, draft, generate, close | H-0001/H-0003: Gate 4 `needs-evidence`. Coverage 57% (8/14 flows). Citations invalid=0. Report: 0 verified. Session paused. |

Pipeline self-reports: ISS-0001 missing tools, ISS-0002 skeleton/AST matching, ISS-0003 slither drop.

## Boss-skill hunts

Manual audit-map-hunter passes on three subsystems (JSON under `hunters/`):

| Subsystem | Leads | Gate 1 keep | Gate 1 kill |
|---|---:|---:|---:|
| Clearinghouse / engine settlement | 14 | 2 (L-CH-001, L-CH-002) | 12 |
| Orders / oracle / protection | 18 | 0 | 18 |
| HousePool / TrancheVault | 13 | 0 | 13 |
| **Total** | **45** | **2** | **43** |

Live leads were fed back as `prediction_diff` design-wrong (DIV-0067, DIV-0068) so they exist inside the apex case file, not only in hunter JSON.

## Four gates (this campaign)

1. **Divergence** — model vs code (DIV-*). Apex produced 66 matching-noise DIVs + 2 design-wrong. Hunters produced 45 leads judged keep/kill against source.
2. **Hypothesis** — specialist lens must attach to a DIV (H-*). Only 4 hypotheses; two are constructor-bound noise.
3. **Experiment** — executed test/fuzz/PoC. Operator override: none executed. All experiments `pending`/`prepared`.
4. **Validate** — adversarial disprove + citations + classify. Live hyps `needs-evidence`; unverified reachability.

No finding was promoted. That matches “harness found 0 issues” and is **not** a claim that the protocol has 0 issues.

# Pipeline issues recorded in the campaign (`ISS-*`)

These are apex-core defects / environment gaps, not Plether bugs.

## ISS-0001 — missing tools (blocker)

Foundry, Slither, Semgrep, and the bugbounty-intel corpus were absent at `assess_environment`. Contest PoCs require Foundry. EVM adapter static tools are slither and semgrep. Workaround: installed Foundry and slither later in the run; Semgrep and intel corpus stayed missing. Expected effect: Phase 3 static recall and Phase 5 executed evidence collapse.

## ISS-0002 — skeleton / AST entry matching (high)

`make_blind_skeleton` and `ast_divergence_mapper` token-match the **last** identifier of `flow.entry` after splitting on `[(:]`. For `MarginClearinghouse.depositFor(address,uint256)` the last token is `uint256`, so no surface matches. Skeleton then falls back to the first 80 surfaces (alphabetically `CfdClosePreview.sol`, out of scope). AST emits `unmapped_critical_flow` for every critical flow and fills the rest of the budget with `undocumented_entrypoint` (cap 50).

Requested change: match `Contract.function` (strip types), not the last parenthesis token.

## ISS-0003 — Slither stdout cap / rc 255 (blocker)

`targeted_static_sweep` ran slither on `packages/perps`. Independent rerun wrote 188 detectors (including 4 in-scope High on `PletherOracle.sol`). Apex logged the run as error rc=255, findings_total=0.

Causes:

1. `fsutil.run_command` truncates stdout at 2_000_000 bytes; slither `--json -` exceeded that; `json.loads` failed; parser returned `[]`.
2. Slither exits 255 when detectors fire; sweep treats only rc 0 and 1 as `ran`.

Requested change: write analyser JSON to a file and parse the file; treat slither 255 as success-with-findings; do not cap below typical slither JSON size.

## Additional defects observed, not yet ISS-* in `.apex`

- PDF past-audit files are not parsed by `review_past_audits` (markdown-only), so known-issue indexing from attached PDFs is empty.
- `undocumented_entrypoint` cap of 50 hides remaining public ABI.
- Phase 4 lenses reuse the same broken surface matcher and bind to `constructor(`.
- Gate 3 cannot be satisfied under an operator “do not write PoCs” constraint; the pipeline then **cannot** emit verified findings even for live code leads.

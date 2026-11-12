# Apex Core

Universal, domain-agnostic security-campaign pipeline exposed as a **Model
Context Protocol (MCP) server** with a first-class **CLI fallback**. One core,
pluggable `TargetProfile` adapters, strict phase gates, and JSON artifacts in
the target workspace.

Works with Cursor, Claude Desktop, Copilot, Kilocode, or any harness that can
run a command.

## Why

Naive pipelines jump from a mental model straight to blind scanning. Apex Core
forces the opposite: build an intent model, open the code, **map every
divergence**, then dispatch a specialist lens per divergence and verify the
hypothesis in a sandbox. Findings are compiled only from surviving, executed
evidence.

```
0 Ground -> 1 Research -> 2 Model -> 3 Divergence -> 4 Specialists -> 5 Experiment -> 6 Validate
```

Every phase writes one artifact; a tool in phase N refuses to run until phases
0..N-1 are complete. `TargetProfile` (`web2_api`, `evm`, `svm`, `move`,
`native_binary`, `hybrid`) routes parsing, static tools, and sandbox templates
without changing the workflow.

## Layout

```
apex-core/
├── main.py                 # MCP server + CLI entry point
├── state_manager.py        # .apex/ artifacts, TargetProfile, phase gates
├── registry.py             # plugin auto-discovery
├── runtime.py              # ToolSpec / ToolContext / ToolError
├── fsutil.py               # safe file + process helpers
├── adapters/               # web2, evm, svm, move, native, generic_ast
├── tools/
│   ├── phase0_ground.py
│   ├── phase1_research.py
│   ├── phase2_model.py
│   ├── phase3_divergence.py
│   ├── phase4_specialists.py
│   ├── phase5_sandbox.py
│   └── phase6_validate.py
├── schemas/                # Pydantic input/output models
├── SYSTEM_PROMPT.md        # universal harness instructions
└── requirements.txt
```

## Install

```bash
cd apex-core
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py --list
```

`tree-sitter-language-pack` is optional; without it, Phase 3 uses
language-specific regex extraction and records `method: "regex"`.

## Quick start (CLI)

Run from the **target workspace** so `.apex/` lands in the target:

```bash
CORE=/path/to/apex-core/main.py

# Phase 0
python "$CORE" 0 parse_scope --repos . --endpoints https://api.example.com
python "$CORE" 0 set_rules --policy-files SECURITY.md --invariants "totalSupply is conserved"
python "$CORE" 0 lock_boundaries --out-of-scope admin.example.com --non-destructive true

# Phase 1
python "$CORE" 1 ingest_docs --paths docs README.md
python "$CORE" 1 review_past_audits --paths audits
python "$CORE" 1 check_intel --keywords "ssrf,graphql,jwt"

# Phase 2
python "$CORE" 2 map_state_flows --args-file flows.json
python "$CORE" 2 define_invariants --args-file invariants.json

# Phase 3
python "$CORE" 3 ast_divergence_mapper
python "$CORE" 3 targeted_static_sweep --semgrep-config ./semgrep-rules.yml

# Phase 4 (requires a DIV-* id from Phase 3)
python "$CORE" 4 dimensional_checker --divergence-id DIV-0001
python "$CORE" 4 trust_boundary_prober --divergence-id DIV-0002 --focus "bearer token scope"

# Phase 5
python "$CORE" 5 sandbox_forge --service api
python "$CORE" 5 invariant_tester --hypothesis-id H-0001 --test-code "$(cat test.py)" --execute true --command "pytest -q"
python "$CORE" 5 record_experiment --hypothesis-id H-0001 --verdict confirmed \
  --command "pytest -q tests/test_fee.py" --output-path .apex/experiments/fee.log

# Phase 6
python "$CORE" 6 disprove_finding --hypothesis-id H-0001 --json '{"checks":[...]}'
python "$CORE" 6 generate_report

python "$CORE" --status
```

List tools: `python "$CORE" --list`.

### Argument forms

```bash
--repos src contracts          # space-separated list values
--repos src,contracts          # comma-separated
--repos '["src","contracts"]'  # JSON
--json '{"divergence_id":"DIV-0001"}'
--args-file args.json
```

Output is always structured JSON on stdout: `{"ok": true, "phase": 3, ...}` or
`{"ok": false, "error": {...}}`. Exit code is `2` for gate/tool/input errors.

## Cursor (MCP)

Create `.cursor/mcp.json` in the project, or add to the user-level config:

```json
{
  "mcpServers": {
    "apex-core": {
      "command": "python3",
      "args": [
        "/ABS/PATH/apex-core/main.py",
        "--mcp",
        "--workspace",
        "/ABS/PATH/TARGET"
      ],
      "env": {
        "APEX_INTEL_CORPUS": "/ABS/PATH/bugbounty-intel"
      }
    }
  }
}
```

Cursor then exposes the grouped tools `phase0_ground` … `phase6_report`.
Legacy names such as `phase0_parse_scope` require `APEX_TOOLSET=full`. Point
`--workspace` at the audit target, not at `apex-core`.

## Claude Desktop (MCP)

`claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "apex-core": {
      "command": "python3",
      "args": [
        "/ABS/PATH/apex-core/main.py",
        "--mcp",
        "--workspace",
        "/ABS/PATH/TARGET"
      ]
    }
  }
}
```

If your Python lives in a virtualenv, use its absolute interpreter path
(`.../apex-core/.venv/bin/python`) instead of `python3`.

## Copilot / Kilocode / any CLI harness

No MCP required. Give the agent `SYSTEM_PROMPT.md` and let it shell out:

```bash
python /ABS/PATH/apex-core/main.py 0 parse_scope --workspace /ABS/PATH/TARGET --repos .
python /ABS/PATH/apex-core/main.py --status --workspace /ABS/PATH/TARGET
```

Parse the JSON response; do not scrape stdout text.

## State & gates

```
.apex/
  config.json               TargetProfile + timestamps
  00_ground_zero.json       scope | rules | boundaries
  01_research.json          docs | audits | intel | cves
  02_mental_model.json      flows | invariants
  03_divergences.json       ast_map | static_sweep  (DIV-* ids)
  04_hypotheses.json        dimensional | reverse_engineer | state_machine | trust_boundary  (H-* ids)
  05_experiments.json       sandbox | experiments[]  (E-* ids)
  06_final_report.md        report markdown
  06_report_meta.json       report summary
  experiments/              generated tests + logs
  sandbox/                  provisioned harnesses
  tool-runs.jsonl           append-only tool audit log
  plugins/                  optional workspace extensions
```

Gate rules:

| Phase | Requires |
|---|---|
| 1 | scope + rules + boundaries |
| 2 | docs + audits + intel |
| 3 | flows + invariants |
| 4 | ast_map + static_sweep |
| 5 | at least one lens section with a hypothesis |
| 6 | sandbox + at least one experiment |

Phase 4 also validates that `divergence_id` exists in Phase 3; Phase 5
validates `hypothesis_id`; Phase 6 validates `hypothesis_id`.

## Adding a tool

Core plugin (`tools/phase4_specialists.py` style):

```python
from runtime import ToolSpec, tool
from schemas.common import ApexModel

class MyInput(ApexModel):
    divergence_id: str

class MyOutput(ApexModel):
    ok: bool = True

@tool(
    name="my_lens",
    phase=4,
    section="my_lens",
    summary="What this lens checks.",
    input_model=MyInput,
    output_model=MyOutput,
    write_mode="section",
)
def my_lens(ctx, inp):
    return MyOutput()
```

Drop a file under `apex-core/tools/phase4_my_lens.py`, or under
`<target>/.apex/plugins/my_lens.py` (no restart of the core code needed). The
registry auto-discovers modules exposing `TOOLS` and applies gates/schemas.
Duplicate `(phase, name)` pairs are rejected.

## Safety

- Static tools are read-only and time-limited.
- `invariant_tester` never executes unless `execute=true` and a `command` is
  supplied.
- Sandbox templates default to no network, dropped capabilities, and local
  runtimes (Docker/Foundry/Anchor/Move/process).
- The report never upgrades a candidate to a finding without an executed
  experiment and adversarial checks.

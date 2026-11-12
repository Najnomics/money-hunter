# Apex Core

**A disciplined audit campaign manager for AI agents.**

Apex Core gives an agent a clear process for security work: understand the
target, write down what should happen, compare it with the code, test the
differences, and report only what survives. It runs as an **MCP server** or as a
**normal command line tool**, so it works with Cursor, Claude Desktop, Copilot,
Kilocode, or a custom harness.

It is domain-agnostic: web APIs, EVM, Solana, Move, native binaries, or a mix.

## The idea in one picture

```
Ground -> Research -> Model -> Compare -> Analyze -> Test -> Report
```

Each step writes a file in the target’s `.apex/` folder. A step cannot start
until the previous checklist is complete. That is what stops the agent from
jumping straight to “findings.”

## Install

```bash
cd apex-core
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --list
```

`tree-sitter-language-pack` is optional. Without it, Phase 3 falls back to
pattern extraction and records that honestly.

### One-click setup

```bash
# Cursor, one project, with the shared intel corpus
./scripts/setup.sh --intel --client cursor --target /absolute/path/to/target

# Claude Desktop, global one-time server
./scripts/setup.sh --intel --client claude
```

The script creates the venv, installs dependencies, syncs the intel corpus,
writes the MCP config, and sets the policy. `--force` replaces an existing
`apex-core` entry.

### Intel corpus: linked, not vendored

`bugbounty-intel` is deliberately **not** committed here. It changes too often.
Clone/update it into a shared cache:

```bash
./scripts/sync-intel.sh            # ~/.apex/intel/bugbounty-intel
```

`check_intel` automatically finds that path and reports the corpus git revision
and commit date. Override with `APEX_INTEL_CORPUS` or `APEX_INTEL_REPO`.

## Quick start

Run against a target folder:

```bash
CORE=/absolute/path/to/apex-core/main.py
TARGET=/absolute/path/to/target

# Choose how strict the campaign should be (light | standard | strict)
python "$CORE" --policy standard --workspace "$TARGET"

# Phase 0 — what are we allowed to touch?
python "$CORE" 0 parse_scope --workspace "$TARGET" --repos .
python "$CORE" 0 set_rules --workspace "$TARGET" --policy-files SECURITY.md
python "$CORE" 0 lock_boundaries --workspace "$TARGET" --out-of-scope "prod.example.com"

# Phase 1 — what is it supposed to do?
python "$CORE" 1 ingest_docs --workspace "$TARGET" --paths docs README.md
python "$CORE" 1 review_past_audits --workspace "$TARGET" --paths audits
python "$CORE" 1 check_intel --workspace "$TARGET" --keywords "ssrf,graphql,jwt"

# Phase 2 — build the model before reading code
python "$CORE" 2 map_state_flows --workspace "$TARGET" --args-file flows.json
python "$CORE" 2 define_invariants --workspace "$TARGET" --args-file invariants.json

# Phase 3 — where does reality differ?
python "$CORE" 3 ast_divergence_mapper --workspace "$TARGET"
python "$CORE" 3 targeted_static_sweep --workspace "$TARGET"

# Phase 4 — analyze each divergence (needs a DIV-* id)
python "$CORE" 4 dimensional_checker --workspace "$TARGET" --divergence-id DIV-0001

# Phase 5 — test it in a sandbox
python "$CORE" 5 sandbox_forge --workspace "$TARGET" --service api
python "$CORE" 5 invariant_tester --workspace "$TARGET" --hypothesis-id H-0001

# Phase 6 — try to disprove it, measure coverage, report
python "$CORE" 6 disprove_finding --workspace "$TARGET" --hypothesis-id H-0001
python "$CORE" 6 verify_citations --workspace "$TARGET"
python "$CORE" 6 coverage_check --workspace "$TARGET"
python "$CORE" 6 generate_report --workspace "$TARGET"

python "$CORE" --status --workspace "$TARGET"
```

Output is always JSON:

```json
{"ok": true, "phase": 3, "tool": "ast_divergence_mapper", "artifact": ".apex/03_divergences.json"}
```

An error looks like:

```json
{"ok": false, "error": {"type": "phase_gate", "phase": 2, "missing": ["section:invariants"]}}
```

Exit code is `2` for gate, input, or tool errors.

## The strictness dial

| Policy | What it adds |
|---|---|
| `light` | The original seven phases. Fastest. |
| `standard` | Citation checking + coverage measurement before the report. |
| `strict` | State vocabulary, impact sinks, assumptions, and blind predictions for critical flows. |

Set it once:

```bash
python main.py --policy strict --workspace /path/to/target
```

You can change it later. The policy is stored in `.apex/config.json`.

## Connect it to Cursor

**One-time global setup (recommended):** configure the server once, then pass
the target workspace in each tool call. One server can serve every project.

```json
{
  "mcpServers": {
    "apex-core": {
      "command": "/ABS/PATH/apex-core/bin/apex",
      "args": ["--mcp"],
      "env": {
        "APEX_INTEL_CORPUS": "/home/you/.apex/intel/bugbounty-intel"
      }
    }
  }
}
```

The agent then calls tools with `"workspace": "/ABS/PATH/TARGET"` alongside
the normal arguments. Each target gets its own `.apex/` case file.

If you prefer a fixed default, add `--workspace /ABS/PATH/TARGET` to the args
and omit `workspace` from calls.

## Connect it to Claude Desktop

Edit `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "apex-core": {
      "command": "/ABS/PATH/apex-core/bin/apex",
      "args": ["--mcp"],
      "env": {
        "APEX_INTEL_CORPUS": "/home/you/.apex/intel/bugbounty-intel"
      }
    }
  }
}
```

This is also one-time. The agent supplies the target workspace per call.
`bin/apex` already prefers the project virtualenv, so no Python path is needed.

## Use it from Copilot, Kilocode, or any CLI agent

No MCP needed. Give the agent `SYSTEM_PROMPT.md` and let it call:

```bash
python /ABS/PATH/apex-core/main.py 0 parse_scope --workspace /ABS/PATH/TARGET --repos .
python /ABS/PATH/apex-core/main.py --status --workspace /ABS/PATH/TARGET
```

Read the JSON response; do not scrape console text.

## What the agent is not allowed to do

- Skip a phase.
- Analyze a divergence that does not exist.
- Test a hypothesis that does not exist.
- Mark a finding “confirmed” without captured evidence.
- Call a finding “critical” without human approval.
- Claim coverage without a coverage ledger.
- Turn a scanner hit into a finding by itself.

## Team onboarding

New to the tool? Read [How team members use Apex Core](docs/ONBOARDING.md) for
the exact clone → install → MCP/CLI setup, target workspace rules, and the
pipeline feedback mechanism.

## Learn more

- [Plain-English overview](docs/OVERVIEW.md) — start here if you are not technical
- [The seven phases](docs/PHASES.md) — what each stage does
- [State and gates](docs/STATE_AND_GATES.md) — the case file and checklists
- [The coverage loop](docs/COVERAGE_LOOP.md) — how second passes work
- [Tool reference](docs/TOOLS.md) — every tool in one table
- [Extending](docs/EXTENDING.md) — add an adapter or a tool
- [Publishing](docs/PUBLISHING.md) — push the repo and keep the intel corpus linked
- [Technical architecture](docs/ARCHITECTURE.md) — the original deep dive

## Safety

- Static tools are read-only and time-limited.
- `invariant_tester` only executes when `execute=true` and a command is supplied.
- Sandbox templates disable networking and drop capabilities by default.
- The report never upgrades a candidate to a finding without an executed
  experiment and adversarial checks.
- The user owns submission. The agent never submits, emails, or discloses.

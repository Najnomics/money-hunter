# How team members use Apex Core

This guide is for someone who wants to run an audit with an AI agent. You do
**not** need to be a Python developer, but you do need to copy a few paths
correctly.

## What you need

- Python 3.10 or newer
- Git (or a copy of the `apex-core` folder)
- A target codebase, service, or binary folder
- An agent that supports MCP (Cursor, Claude Desktop) **or** a CLI agent
  (Copilot, Kilocode, custom)

## Step 1 — Get the core and install it

```bash
git clone <your-repo-url>
cd apex-core
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --list
```

You should see roughly 37 tools grouped by phase. If the list is empty, the
install failed.

> `apex-core` is the **tool**. The target is the **thing you audit**. They are
> different folders. Never point `--workspace` at `apex-core` itself.

## Step 2 — Pick a target workspace

The target workspace is the folder that contains the code or artifacts you are
allowed to audit. Apex Core will create a `.apex/` folder **inside that target**.

```bash
TARGET=/absolute/path/to/your/target
CORE=/absolute/path/to/apex-core/main.py

python "$CORE" --policy standard --workspace "$TARGET"
```

`--workspace` must be an absolute path in MCP configs. Relative paths are
resolved from wherever the server happens to start, which is confusing.

## Step 3 — Choose how the agent connects

### Option A: MCP (Cursor or Claude Desktop)

Add the server to the client’s config.

**Cursor** — `.cursor/mcp.json` in the project, or the user-level MCP config:

```json
{
  "mcpServers": {
    "apex-core": {
      "command": "/absolute/path/to/apex-core/.venv/bin/python",
      "args": [
        "/absolute/path/to/apex-core/main.py",
        "--mcp",
        "--workspace",
        "/absolute/path/to/your/target"
      ],
      "env": {
        "APEX_INTEL_CORPUS": "/absolute/path/to/bugbounty-intel"
      }
    }
  }
}
```

**Claude Desktop** — `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Use the same `mcpServers` block.

Then:

1. Restart the client.
2. Ask it to list MCP tools. You should see `phase0_parse_scope` through
   `phase6_generate_report`.
3. Run `phase0_parse_scope` first. If it returns a phase-gate error, stop and
   run the missing earlier tool.

**One target per server entry.** If you audit three targets, create three
entries (`apex-core-target-a`, `apex-core-target-b`, …) with different
`--workspace` values. The tools and the case files stay separate.

### Option B: CLI (Copilot, Kilocode, custom agent)

No MCP configuration. Give the agent two things:

1. `SYSTEM_PROMPT.md` from this folder.
2. The command pattern and the absolute paths:

```bash
CORE=/absolute/path/to/apex-core/main.py
TARGET=/absolute/path/to/your/target

python "$CORE" --status --workspace "$TARGET"
python "$CORE" 0 parse_scope --workspace "$TARGET" --repos .
```

Tell the agent:

> Use Apex Core through `python "$CORE" <phase> <tool> --workspace "$TARGET"`.
> Read the JSON response. Do not skip a phase. If a gate blocks you, run the
> missing tool. If a tool is missing or confusing, call `report_issue`.

The agent should parse JSON, not scrape console text.

## Step 4 — Set the strictness

```bash
python "$CORE" --policy light   --workspace "$TARGET"   # fastest
python "$CORE" --policy standard --workspace "$TARGET"  # recommended
python "$CORE" --policy strict  --workspace "$TARGET"   # serious contests
```

`standard` requires citation and coverage checks before the report. `strict`
also requires environment readiness, state vocabulary, sinks, assumptions, and
blind predictions for critical flows.

## Step 5 — Run the campaign

The agent follows the seven phases. You can watch progress with:

```bash
python "$CORE" --status --workspace "$TARGET"
```

At the end, read:

- `.apex/06_final_report.md` — the report
- `.apex/06_report_meta.json` — coverage, citations, classifications, issues
- `.apex/death-note.md` and `.apex/backlog.md` — resume notes if the session
  stopped early

## Step 6 — Report pipeline problems

The agent can call `report_issue` **at any phase**, even when a gate is
blocking it.

```bash
python "$CORE" 6 report_issue --workspace "$TARGET" \
  --kind missing_tool \
  --title "Semgrep is not installed" \
  --description "The static sweep cannot run Semgrep rules in this sandbox." \
  --tool targeted_static_sweep \
  --phase-attempted 3 \
  --severity blocker \
  --requested-change "Install semgrep in the sandbox image" \
  --workaround "Bandit only"
```

Kinds:

| Kind | Use it for |
|---|---|
| `tool_friction` | The tool exists but is confusing, slow, or produces noisy output |
| `missing_tool` | A specific analyser, fuzzer, or runtime is not installed |
| `missing_capability` | The pipeline cannot express what the target needs |
| `bug` | A tool behaved incorrectly |
| `doc_gap` | The instructions or schema were unclear |
| `environment` | Sandbox, network, Docker, or fixture problem |

Issues are stored in `.apex/06_report_meta.json` under `issues` and appear in
the final report under **Agent feedback & missing tools**.

## Step 7 — Update the core

```bash
cd apex-core
git pull
source .venv/bin/activate
pip install -r requirements.txt
python main.py --list
```

Campaign state is in the target’s `.apex/`, not in `apex-core`, so updating the
core does not delete a campaign. Re-run `--status` after an update.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: mcp` | Dependencies not installed in the interpreter the client uses | Install into the same venv and use its absolute Python path in the MCP config |
| `phase_gate` error | Tools were called out of order | Run the missing earlier tool; do not edit JSON |
| Tools list is empty in Cursor | `--workspace` or `command` path is wrong | Use absolute paths, restart the client |
| Report blocked on `coverage` / `citations` | `standard` policy is on | Run `coverage_check` and `verify_citations`, or switch to `light` |
| `strict` blocks Phase 3 | Critical flow has no blind prediction | Run `record_prediction` for each critical flow |
| Static tool says `unavailable` | Binary not on PATH | Install it, or record a `missing_tool` issue |
| Experiments do nothing | `invariant_tester` is dry by default | Pass `--execute true` and a `--command` |
| Agent edited `.apex` by hand | Gate confusion | Regenerate with tools; hand edits defeat the audit trail |

## Team rules

- One `.apex/` per target. Do not reuse a campaign folder across targets.
- Treat `.apex/` as confidential; it contains exploit reasoning and evidence.
- Do not commit `.apex/` to a public repository.
- The agent never submits findings. A human reviews and submits.
- Run experiments locally, in a fork, or in a devnet only.
- If a tool is missing, report it. Silent workarounds are how audits become
  fiction.

# Apex Core in plain English

Apex Core is a **campaign manager for security audits**. It does not “find
bugs” by itself. It gives an AI agent a disciplined process, a place to write
down evidence, and a set of checks that stop it from claiming more than it can
prove.

Think of it like a criminal investigation:

| Investigation idea | Apex Core equivalent |
|---|---|
| Case file | The `.apex/` folder inside the target project |
| Investigation stages | Phases 0 to 6 |
| Checklist before moving on | A **phase gate** |
| Specialist investigator | A **tool** |
| Written evidence | JSON/Markdown **artifacts** |
| Translator for a type of target | A **TargetProfile adapter** |
| Second pass over overlooked areas | A **coverage round** |
| Case-closed review | Phase 6 report |

## The one-sentence version

> Understand the target, write down what should happen, compare it with what
> actually happens, test the differences, and only report what survives.

## Why the order matters

Many automated audits jump from “read some code” to “run a scanner” to “write a
finding.” That creates confident nonsense. Apex Core forces this order:

1. **Agree on the rules** — what is in scope, what is forbidden, what the system
   promises.
2. **Read the documentation first** — understand intent before implementation.
3. **Build a model** — flows, actors, state, invariants.
4. **Open the code and find divergences** — where the model and reality differ.
5. **Analyze each divergence with the right specialist lens** — math, state,
   trust, or reverse engineering.
6. **Run an experiment** — a hypothesis without executed evidence is only a
   candidate.
7. **Try to disprove it** — then report only what survived.

## The most important idea: evidence labels

Every claim must say how it is known:

- `[FACT]` — confirmed by the user or a map
- `[OBSERVED]` — seen directly in a probe or output
- `[SEARCHED]` — found in docs, advisories, or the intel corpus
- `[FUZZED]` — produced by an experiment you ran
- `[CODE]` — quoted from `file:line`
- `[DEDUCED]` — logically inferred from labeled facts
- `[ASSUMED]` — a guess; guesses lower confidence

An unlabeled sentence is not a finding. Two `[ASSUMED]` links in a chain make it
theoretical.

## The strictness dial

A campaign can run at three levels:

| Policy | What it means in plain language |
|---|---|
| `light` | The original seven-phase flow. Fast, fewer final checks. |
| `standard` | Also checks citations and measures coverage before the report. |
| `strict` | Also requires state vocabulary, impact sinks, assumptions, and blind predictions for critical flows. |

Set it once per campaign:

```bash
python main.py --policy standard --workspace /path/to/target
```

## The coverage loop

The first report is not automatically the end. Phase 6 produces a **coverage
ledger**: what was modeled, what was mapped, what is still open. If high-value
gaps remain, the agent can open a **round**, fix only those gaps, and regenerate
the report.

That loop is deliberately bounded:

- a few gaps per round, not the whole repo
- a few rounds, not forever
- if a round produces no new evidence, it is marked **stalled**
- “covered” means every in-scope entry has a disposition, not that every file
  was read

See [COVERAGE_LOOP.md](COVERAGE_LOOP.md).

## What the agent is not allowed to do

- Skip a phase.
- Analyze a divergence that does not exist.
- Test a hypothesis that does not exist.
- Mark a finding “confirmed” without a captured experiment.
- Call a finding “critical” without human approval.
- Claim coverage without a coverage ledger.
- Treat a scanner output as a finding.

## Where to look next

- [PHASES.md](PHASES.md) — what each phase does
- [STATE_AND_GATES.md](STATE_AND_GATES.md) — the case file and checklists
- [COVERAGE_LOOP.md](COVERAGE_LOOP.md) — the second-pass loop
- [TOOLS.md](TOOLS.md) — every tool in one table
- [EXTENDING.md](EXTENDING.md) — adding a new adapter or tool

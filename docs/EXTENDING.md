# Extending Money Hunter

There are two ways to add capability without editing the core workflow.

## 1. Add a target adapter

An adapter teaches the pipeline about one kind of target. It answers three
questions:

1. What file types identify this target?
2. How do I extract entry points from those files?
3. Which static tools and sandbox template fit this target?

Adapters live in `adapters/`. A minimal adapter:

```python
from adapters.base import Adapter
from schemas.common import TargetProfile

ADAPTER = Adapter(
    profile=TargetProfile.WEB2_API,
    name="web2_api",
    kind="service",
    extensions=(".py", ".go"),
    languages=("python", "go"),
    surface_patterns=(("route", r"@app\\.get\\(['\"]([^'\"]+)"),),
    static_tools=(),
    sandbox_kind="docker-service",
)
```

Register it in `adapters/__init__.py`. Keep domain knowledge here, not in phase
tools. That is what lets the same Phase 3 tool work on EVM, Solana, web
services, and native binaries.

## 2. Add a tool

A tool is a typed function with a phase, a section, and a handler.

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
    summary="What this lens checks, in one sentence.",
    input_model=MyInput,
    output_model=MyOutput,
    write_mode="section",
)
def my_lens(ctx, inp):
    # ctx.state gives access to artifacts and the gate policy.
    # ctx.adapter knows the TargetProfile.
    return MyOutput()

TOOLS = [my_lens]
```

Place it in:

- `tools/phase4_my_lens.py`, or
- `<target>/.apex/plugins/my_lens.py`

The registry discovers it on the next invocation. It automatically gets:

- phase gates
- Pydantic input/output validation
- MCP registration
- CLI registration
- the append/merge persistence rules

Duplicate `(phase, name)` pairs are rejected.

## Write modes

| Mode | Meaning |
|---|---|
| `section` | Store the output under the tool’s section. Repeatable sections merge by id. |
| `append` | Append `items` or `hypotheses` to a list section. |
| `report` | Write Markdown and store the remaining output as report metadata. |

## Rules of thumb

- Keep domain assumptions in adapters, not tools.
- Return structured data, not prose blobs.
- Require an id when a tool depends on earlier work.
- Never invent a tool result when a binary is missing; record `unavailable`.
- Add comments for the non-technical reader: explain *why*, not just *what*.

## What not to add

- A tool that silently shells out to a live target.
- A tool that upgrades a candidate to a finding.
- A domain-specific parser inside a phase tool.
- A hardcoded chain name, framework name, or file layout in the core.

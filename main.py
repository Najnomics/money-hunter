#!/usr/bin/env python3
"""Apex Core — dual MCP server and CLI entry point.

In plain English: this is the single front door.  It can run as an MCP server
for Cursor/Claude, or as a normal command for Copilot/Kilocode.  Both modes use
the same registry, the same phase gates, and the same JSON artifacts.

CLI:
    python main.py 0 parse_scope --workspace /target --repos .
    python main.py phase3 ast_divergence_mapper --workspace /target
    python main.py 4 dimensional_checker --divergence-id DIV-0001 --workspace /target
    python main.py --list
    python main.py --status --workspace /target

MCP:
    python main.py --mcp --workspace /target
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, get_args, get_origin

# Make sibling modules importable regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from adapters import get_adapter  # noqa: E402
from registry import PluginRegistry  # noqa: E402
from runtime import SessionState, ToolContext, ToolError, ToolSpec  # noqa: E402
from state_manager import ArtifactError, GateError, StateError, StateManager  # noqa: E402

VERSION = "1.0.4"


# --------------------------------------------------------------------- input
def _normalize_phase(value: str) -> int:
    match = re.fullmatch(r"(?:phase)?0*(\d)", value.strip().lower())
    if not match or int(match.group(1)) > 6:
        raise ValueError(f"invalid phase {value!r}; expected 0..6 or phase0..phase6")
    return int(match.group(1))


def _parse_flags(rest: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    index = 0
    while index < len(rest):
        token = rest[index]
        if not token.startswith("--"):
            raise ValueError(f"unexpected argument {token!r}; use --key value or --args JSON")
        key = token[2:]
        if "=" in key:
            key, value = key.split("=", 1)
        elif index + 1 < len(rest) and not rest[index + 1].startswith("--"):
            collected: list[str] = []
            while index + 1 < len(rest) and not rest[index + 1].startswith("--"):
                collected.append(rest[index + 1])
                index += 1
            value = collected[0] if len(collected) == 1 else collected
        else:
            value = "true"
        key = key.replace("-", "_")
        if key in values:
            previous = values[key]
            previous_list = previous if isinstance(previous, list) else [previous]
            next_list = value if isinstance(value, list) else [value]
            values[key] = previous_list + next_list
        else:
            values[key] = value
        index += 1
    return values


def _unwrap_annotation(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is not None and str(origin).endswith("Union"):
        args_list = [a for a in get_args(annotation) if a is not type(None)]
        if args_list:
            return args_list[0]
    # PEP 604 unions (X | None) arrive as types.UnionType
    if type(annotation).__name__ == "UnionType":
        args_list = [a for a in get_args(annotation) if a is not type(None)]
        if args_list:
            return args_list[0]
    return annotation


def _coerce(value: Any, annotation: Any) -> Any:
    annotation = _unwrap_annotation(annotation)
    origin = get_origin(annotation)

    if origin is list:
        (inner,) = get_args(annotation) or (str,)
        raw_values = value if isinstance(value, list) else [value]
        items: list[Any] = []
        for raw in raw_values:
            if isinstance(raw, str):
                stripped = raw.strip()
                if stripped.startswith("["):
                    try:
                        parsed = json.loads(stripped)
                        if isinstance(parsed, list):
                            items.extend(parsed)
                            continue
                    except json.JSONDecodeError:
                        pass
                if "," in stripped:
                    items.extend(part.strip() for part in stripped.split(",") if part.strip())
                elif stripped:
                    items.append(stripped)
            else:
                items.append(raw)
        return [_coerce(item, inner) for item in items]

    if origin is dict:
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    if isinstance(value, list) and len(value) == 1:
        value = value[0]

    if annotation is bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}
    if annotation is int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    if annotation is float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    if annotation is str:
        return str(value)
    return value


def _extract_global_flags(rest: list[str], args: argparse.Namespace) -> list[str]:
    """Pull global flags that argparse's REMAINDER left after positionals."""
    value_flags = {
        "--workspace": "workspace",
        "--state-dir": "state_dir",
        "--args-file": "args_file",
        "--json": "json",
        "--policy": "policy",
    }
    remaining: list[str] = []
    index = 0
    while index < len(rest):
        token = rest[index]
        key, _, inline = token.partition("=")
        if key in value_flags:
            if inline:
                value = inline
            elif index + 1 < len(rest) and not rest[index + 1].startswith("--"):
                value = rest[index + 1]
                index += 1
            else:
                value = ""
            setattr(args, value_flags[key], value)
        elif token == "--pretty":
            args.pretty = True
        else:
            remaining.append(token)
        index += 1
    return remaining


def build_raw_args(flags: dict[str, Any], spec: ToolSpec) -> dict[str, Any]:
    fields = spec.input_model.model_fields
    accepted: set[str] = set(fields)
    unknown = [key for key in flags if key not in accepted]
    if unknown:
        raise ToolError(
            f"unknown argument(s) for {spec.name}: {', '.join(unknown)}",
            details={"accepted": sorted(accepted)},
        )
    return {key: _coerce(value, fields[key].annotation) for key, value in flags.items()}


# ----------------------------------------------------------------- execution
def execute_tool(
    spec: ToolSpec,
    raw: dict[str, Any],
    state: StateManager,
    workspace: Path,
    session: SessionState | None = None,
) -> dict[str, Any]:
    # Resolution order: explicit per-call workspace, then the target bound by
    # start_campaign, then the server/CLI default.  The middle step is what
    # makes "use apex-core on /target" a once-per-session action.
    requested_workspace = raw.get("workspace")
    if requested_workspace:
        call_workspace = Path(str(requested_workspace)).expanduser().resolve()
    elif session is not None and session.workspace is not None:
        call_workspace = session.workspace
    else:
        call_workspace = workspace
    call_state = (
        state
        if call_workspace == state.workspace
        else StateManager(call_workspace, state_dir=state.state_dir_name)
    )

    # Meta tools such as report_issue are deliberately callable even when a
    # phase gate is blocking the campaign, so the agent can report the block.
    if not spec.always_available:
        call_state.require_gate(spec.phase)

    try:
        payload_in = spec.input_model.model_validate(raw)
    except Exception as exc:
        raise ToolError(f"invalid input for {spec.name}: {exc}", details=getattr(exc, "errors", lambda: None)()) from exc

    ctx = ToolContext(
        workspace=call_workspace,
        state=call_state,
        adapter=get_adapter(call_state.target_profile),
        session=session,
    )
    try:
        result = spec.handler(ctx, payload_in)
    except ToolError:
        raise
    except Exception as exc:
        raise ToolError(f"{spec.name} failed: {exc}") from exc

    try:
        data = spec.output_model.model_validate(result).model_dump(mode="json")
    except Exception as exc:
        raise ToolError(f"{spec.name} produced invalid output: {exc}") from exc

    if spec.write_mode == "section":
        call_state.write_section(spec.phase, spec.section, data, spec.name)
    elif spec.write_mode == "append":
        items = data.get("items") if isinstance(data, dict) else None
        if items is None and isinstance(data, dict):
            items = data.get("hypotheses")
        if not isinstance(items, list):
            raise ToolError(f"{spec.name}: append output must contain an `items` list")
        call_state.append_items(spec.phase, spec.section, items, spec.name)
    elif spec.write_mode == "report":
        markdown = data.pop("markdown", "")
        if not markdown:
            raise ToolError(f"{spec.name}: report output is empty")
        call_state.write_report(markdown)
        data["report_path"] = call_state.artifact_relpath(6)
        call_state.write_section(6, "report", data, spec.name)
    elif spec.write_mode == "none":
        pass  # meta tool; it updates config/session only
    else:  # pragma: no cover - validated by ToolSpec
        raise ToolError(f"{spec.name}: invalid write mode {spec.write_mode}")

    if spec.phase == 0 and isinstance(data.get("target_profile"), str):
        call_state.update_config(target_profile=data["target_profile"])

    return {
        "ok": True,
        "phase": spec.phase,
        "tool": spec.name,
        "section": spec.section,
        "workspace": str(call_workspace),
        "artifact": (
            ".apex/config.json"
            if spec.write_mode == "none"
            else call_state.meta_relpath(spec.phase)
            if spec.always_available
            else call_state.artifact_relpath(spec.phase)
        ),
        "gate": call_state.gate_status(spec.phase),
        "data": data,
    }


def error_payload(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, GateError):
        return {
            "ok": False,
            "error": {"type": "phase_gate", "message": str(exc), "phase": exc.phase, "missing": exc.missing},
        }
    if isinstance(exc, ToolError):
        return {"ok": False, "error": {"type": "tool_error", "message": exc.message, "details": exc.details}}
    if isinstance(exc, ArtifactError):
        return {"ok": False, "error": {"type": "artifact_error", "message": str(exc)}}
    if isinstance(exc, StateError):
        return {"ok": False, "error": {"type": "state_error", "message": str(exc)}}
    return {"ok": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}


# ---------------------------------------------------------------------- MCP
def run_mcp(registry: PluginRegistry, state: StateManager, workspace: Path) -> int:
    try:
        import mcp.types as types
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
    except ImportError:
        print(
            "MCP SDK not installed. Run `pip install -r requirements.txt` or use CLI mode.",
            file=sys.stderr,
        )
        return 3

    import asyncio

    server = Server("apex-core")
    session = SessionState()

    def tool_defs() -> list[Any]:
        tools: list[Any] = []
        for spec in registry.all():
            availability = (
                "Available at any phase (meta tool)."
                if spec.always_available
                else f"Requires: phases 0..{spec.phase - 1} complete."
            )
            description = (
                f"[Phase {spec.phase}] {spec.summary}\n"
                f"Writes: .apex/{spec.section} (phase {spec.phase} artifact).\n"
                f"{availability}"
            )
            tools.append(
                types.Tool(
                    name=spec.qualified_name,
                    description=description,
                    inputSchema=spec.input_model.model_json_schema(),
                )
            )
        return tools

    def call_payload(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        spec = registry.by_qualified(name)
        if spec is None:
            return {
                "ok": False,
                "error": {
                    "type": "unknown_tool",
                    "message": f"unknown tool {name}",
                    "available": [s.qualified_name for s in registry.all()],
                },
            }
        try:
            return execute_tool(spec, arguments or {}, state, workspace, session)
        except BaseException as exc:  # noqa: BLE001 - return structured MCP error
            return error_payload(exc)

    if hasattr(server, "list_tools"):
        # MCP SDK 1.x decorator API
        @server.list_tools()
        async def list_tools() -> list[Any]:
            return tool_defs()

        @server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[Any]:
            payload = call_payload(name, arguments)
            return [types.TextContent(type="text", text=json.dumps(payload, indent=2, default=str))]
    else:
        # MCP SDK 2.x request-handler API
        async def on_list_tools(ctx: Any, params: Any) -> Any:
            return types.ListToolsResult(tools=tool_defs())

        async def on_call_tool(ctx: Any, params: Any) -> Any:
            name = getattr(params, "name", "")
            arguments = getattr(params, "arguments", None) or {}
            payload = call_payload(name, arguments)
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=json.dumps(payload, indent=2, default=str))],
                isError=not payload.get("ok", False),
            )

        server.add_request_handler("tools/list", types.PaginatedRequestParams, on_list_tools)
        server.add_request_handler("tools/call", types.CallToolRequestParams, on_call_tool)

    async def _serve() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(_serve())
    return 0


# ---------------------------------------------------------------------- CLI
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apex-core",
        description="Adaptive security-campaign pipeline: MCP server + CLI.",
    )
    parser.add_argument("--mcp", action="store_true", help="Run as an MCP stdio server.")
    parser.add_argument("--workspace", default=".", help="Target workspace containing .apex/ (default: cwd).")
    parser.add_argument("--state-dir", default=None, help="Override state directory name (default: .apex).")
    parser.add_argument("--list", action="store_true", dest="list_tools", help="List registered tools by phase.")
    parser.add_argument("--status", action="store_true", help="Print campaign gate status as JSON.")
    parser.add_argument(
        "--policy",
        default=None,
        choices=["light", "standard", "strict"],
        help="Gate strictness. light = original flow; standard adds coverage/citations; strict adds assumptions/vocab/predictions.",
    )
    parser.add_argument("--json", default=None, help="JSON object of tool arguments.")
    parser.add_argument("--args-file", default=None, help="Path to a JSON file of tool arguments.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--version", action="version", version=f"apex-core {VERSION}")
    parser.add_argument("phase", nargs="?", help="Phase 0..6 (or phase0..phase6).")
    parser.add_argument("tool", nargs="?", help="Tool name, e.g. parse_scope.")
    parser.add_argument("rest", nargs=argparse.REMAINDER, help="Tool flags: --key value ...")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.rest = _extract_global_flags(list(args.rest), args)
    workspace = Path(args.workspace).expanduser().resolve()
    state = StateManager(workspace, state_dir=args.state_dir or ".apex")
    policy_was_set = bool(args.policy)
    if args.policy:
        state.set_gate_policy(args.policy)

    registry = PluginRegistry(
        extra_paths=[workspace / ".apex" / "plugins"] if (workspace / ".apex" / "plugins").is_dir() else []
    ).discover()
    for warning in registry.errors:
        print(f"[apex-core] plugin warning: {warning}", file=sys.stderr)

    if args.list_tools:
        rows = registry.describe()
        for phase in range(0, 7):
            phase_tools = [r for r in rows if r["phase"] == phase]
            if not phase_tools:
                continue
            print(f"\nPhase {phase}")
            for row in phase_tools:
                marker = " [any phase]" if row.get("always_available") else ""
                print(f"  {row['name']:<26} -> section {row['section']:<18} {row['summary']}{marker}")
        print(f"\n{len(rows)} tool(s) registered. {len(registry.errors)} plugin warning(s).")
        return 0

    if args.status:
        print(json.dumps(state.snapshot(), indent=2, default=str))
        return 0

    if args.mcp:
        return run_mcp(registry, state, workspace)

    if not args.phase or not args.tool:
        if policy_was_set:
            print(json.dumps({"ok": True, "gate_policy": state.gate_policy}, indent=2))
            return 0
        parser.print_help()
        return 2

    try:
        phase = _normalize_phase(args.phase)
    except ValueError as exc:
        print(json.dumps(error_payload(ToolError(str(exc))), indent=2))
        return 2

    tool_name = args.tool
    qualified = tool_name if tool_name.startswith("phase") else None
    spec = registry.by_qualified(qualified) if qualified else registry.find(phase, tool_name)
    if spec is None and qualified:
        spec = registry.find(phase, qualified.split("_", 1)[-1])
    if spec is None:
        available = [s.name for s in registry.by_phase(phase)]
        payload = error_payload(
            ToolError(
                f"unknown tool {tool_name!r} for phase {phase}",
                details={"available": available},
            )
        )
        print(json.dumps(payload, indent=2))
        return 2

    raw: dict[str, Any] = {}
    if args.args_file:
        raw.update(json.loads(Path(args.args_file).expanduser().read_text(encoding="utf-8")))
    if args.json:
        raw.update(json.loads(args.json))
    try:
        raw.update(build_raw_args(_parse_flags(list(args.rest)), spec))
    except (ValueError, ToolError) as exc:
        payload = error_payload(exc if isinstance(exc, ToolError) else ToolError(str(exc)))
        print(json.dumps(payload, indent=2))
        return 2

    try:
        payload = execute_tool(spec, raw, state, workspace)
    except BaseException as exc:  # noqa: BLE001 - CLI contract is structured JSON
        print(json.dumps(error_payload(exc), indent=2 if args.pretty else None, default=str))
        return 2

    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

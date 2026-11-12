"""Shared runtime types for Apex Core tools.

A tool is a ``ToolSpec``: a typed input model, a typed output model, a phase,
a persistence target, and a handler. Handlers never touch the filesystem
layout of ``.apex/`` directly; they receive a ``ToolContext`` whose
``state`` object owns persistence and gate enforcement.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Type

from pydantic import BaseModel

TOOL_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
WRITE_MODES = {"section", "append", "report", "none", "dispatch"}


class ToolError(Exception):
    """A user-actionable tool failure (bad input, missing artifact, etc.)."""

    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.message = message
        self.details = details


@dataclass
class DispatchResult:
    """Returned by a grouped phase tool to hand off to a concrete child tool."""

    spec: "ToolSpec"
    result: Any


@dataclass
class SessionState:
    """Small amount of state that lives for one MCP server process.

    `start_campaign` writes the chosen target here, so later tool calls do not
    need to repeat the workspace.  It is intentionally not persisted: a new
    server process must bind again.
    """

    workspace: Path | None = None
    policy_hint: str | None = None


@dataclass
class ToolContext:
    workspace: Path
    state: Any
    adapter: Any
    session: Any = None

    def resolve(self, path: str | Path) -> Path:
        p = Path(path).expanduser()
        return p if p.is_absolute() else (self.workspace / p)

    def rel(self, path: str | Path) -> str:
        from fsutil import rel_to

        p = Path(path)
        return rel_to(p, self.workspace)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    phase: int
    section: str
    summary: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    handler: Callable[[ToolContext, Any], Any]
    write_mode: str = "section"  # section | append | report
    always_available: bool = False  # meta tools such as report_issue skip phase gates
    plugin: str = "core"
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def qualified_name(self) -> str:
        return f"phase{self.phase}_{self.name}"

    def validate(self) -> None:
        if not TOOL_NAME_RE.match(self.name):
            raise ValueError(f"invalid tool name {self.name!r}")
        if not 0 <= self.phase <= 6:
            raise ValueError(f"tool {self.name}: phase must be 0..6")
        if self.write_mode not in WRITE_MODES:
            raise ValueError(f"tool {self.name}: invalid write_mode {self.write_mode!r}")
        if not (isinstance(self.input_model, type) and issubclass(self.input_model, BaseModel)):
            raise ValueError(f"tool {self.name}: input_model must be a pydantic BaseModel")
        if not (isinstance(self.output_model, type) and issubclass(self.output_model, BaseModel)):
            raise ValueError(f"tool {self.name}: output_model must be a pydantic BaseModel")
        if not callable(self.handler):
            raise ValueError(f"tool {self.name}: handler is not callable")
        if not self.section:
            raise ValueError(f"tool {self.name}: section is required")


def tool(
    *,
    name: str,
    phase: int,
    section: str,
    summary: str,
    input_model: Type[BaseModel],
    output_model: Type[BaseModel],
    write_mode: str = "section",
    always_available: bool = False,
    tags: tuple[str, ...] = (),
) -> Callable[[Callable[[ToolContext, Any], Any]], ToolSpec]:
    """Decorator used by phase modules to declare a tool."""

    def wrap(handler: Callable[[ToolContext, Any], Any]) -> ToolSpec:
        spec = ToolSpec(
            name=name,
            phase=phase,
            section=section,
            summary=summary,
            input_model=input_model,
            output_model=output_model,
            handler=handler,
            write_mode=write_mode,
            always_available=always_available,
            tags=tags,
        )
        spec.validate()
        return spec

    return wrap

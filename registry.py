"""Plugin discovery and tool registry.

In plain English: this is the front desk.  It finds every tool module, checks
that its name and phase are valid, and builds the list that MCP clients and the
CLI can see.  New tools can be dropped into ``tools/`` or a target's
``.apex/plugins/`` folder without editing the front desk.

Original details:

Core tools live in ``tools/phase*_*.py`` and expose a module-level ``TOOLS``
list of :class:`runtime.ToolSpec` objects.

Drop-in extension:
  * add a ``tools/phase<N>_<name>.py`` module, or
  * put a ``*.py`` file under ``.apex/plugins/`` in the target workspace, or
  * append a directory to ``APEX_PLUGIN_PATHS``.

Each module only needs ``TOOLS = [ToolSpec, ...]``. New tools are registered
on the next invocation; no central edit is required.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import pkgutil
import re
import sys
from pathlib import Path
from typing import Iterable, Optional

from runtime import ToolSpec

TOOL_FILE_RE = re.compile(r"^phase\d+_.*\.py$")


class RegistryError(Exception):
    pass


class PluginRegistry:
    def __init__(self, extra_paths: Optional[Iterable[str | Path]] = None):
        self._tools: dict[tuple[int, str], ToolSpec] = {}
        self._qualified: dict[str, ToolSpec] = {}
        self.loaded_modules: list[str] = []
        self.errors: list[str] = []
        self._extra_paths = [Path(p).expanduser() for p in (extra_paths or [])]
        env_paths = os.environ.get("APEX_PLUGIN_PATHS", "")
        self._extra_paths.extend(Path(p) for p in env_paths.split(os.pathsep) if p.strip())

    # ------------------------------------------------------------------ add
    def add(self, spec: ToolSpec) -> None:
        spec.validate()
        key = (spec.phase, spec.name)
        if key in self._tools:
            raise RegistryError(
                f"duplicate tool phase {spec.phase} / {spec.name} "
                f"(already from {self._tools[key].plugin})"
            )
        if spec.qualified_name in self._qualified:
            raise RegistryError(f"duplicate qualified tool {spec.qualified_name}")
        self._tools[key] = spec
        self._qualified[spec.qualified_name] = spec

    # -------------------------------------------------------------- discover
    def discover(self) -> "PluginRegistry":
        self._discover_core()
        for directory in self._extra_paths:
            self._discover_directory(directory)
        return self

    def _discover_core(self) -> None:
        try:
            import tools as tools_pkg
        except Exception as exc:  # pragma: no cover - import failure is fatal
            raise RegistryError(f"cannot import tools package: {exc}") from exc

        for info in pkgutil.iter_modules(tools_pkg.__path__, prefix="tools."):
            name = info.name.split(".")[-1]
            if not name.startswith("phase") or name.startswith("_"):
                continue
            try:
                module = importlib.import_module(info.name)
            except Exception as exc:
                self.errors.append(f"{info.name}: import failed: {exc}")
                continue
            self._collect_module(module, f"core:{info.name}")

    def _discover_directory(self, directory: Path) -> None:
        if not directory.is_dir():
            self.errors.append(f"plugin path does not exist: {directory}")
            return
        for path in sorted(directory.glob("*.py")):
            if path.name.startswith("_"):
                continue
            mod_name = f"apex_plugin_{abs(hash(str(path.resolve())))}_{path.stem}"
            try:
                spec = importlib.util.spec_from_file_location(mod_name, path)
                if spec is None or spec.loader is None:
                    raise ImportError("cannot create module spec")
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                spec.loader.exec_module(module)
            except Exception as exc:
                self.errors.append(f"{path}: import failed: {exc}")
                continue
            self._collect_module(module, f"plugin:{path}")

    def _collect_module(self, module, origin: str) -> None:
        specs = getattr(module, "TOOLS", None)
        if specs is None:
            return
        if not isinstance(specs, (list, tuple)):
            self.errors.append(f"{origin}: TOOLS must be a list")
            return
        for spec in specs:
            if not isinstance(spec, ToolSpec):
                self.errors.append(f"{origin}: TOOLS contains a non-ToolSpec value")
                continue
            if spec.plugin == "core":
                object.__setattr__(spec, "plugin", origin)
            try:
                self.add(spec)
            except RegistryError as exc:
                self.errors.append(f"{origin}: {exc}")
        self.loaded_modules.append(origin)

    # --------------------------------------------------------------- lookup
    def all(self) -> list[ToolSpec]:
        return sorted(self._tools.values(), key=lambda s: (s.phase, s.name))

    def by_phase(self, phase: int) -> list[ToolSpec]:
        return [s for s in self.all() if s.phase == phase]

    def find(self, phase: int, name: str) -> Optional[ToolSpec]:
        return self._tools.get((phase, name))

    def by_qualified(self, qualified: str) -> Optional[ToolSpec]:
        return self._qualified.get(qualified)

    def __len__(self) -> int:
        return len(self._tools)

    def describe(self) -> list[dict]:
        return [
            {
                "phase": s.phase,
                "name": s.name,
                "qualified": s.qualified_name,
                "section": s.section,
                "write_mode": s.write_mode,
                "always_available": s.always_available,
                "summary": s.summary,
                "plugin": s.plugin,
            }
            for s in self.all()
        ]

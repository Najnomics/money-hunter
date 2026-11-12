"""Adapter contracts.

An adapter is the only place that knows how one kind of target is parsed,
which static analysers are appropriate, and what a local sandbox looks like.
Think of it as a translator: Phase 3 always asks "what are the entry points?",
and the adapter answers in the language of web APIs, EVM, Solana, Move, or a
native binary.  Phase tools never hardcode a domain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from schemas.common import TargetProfile


@dataclass(frozen=True)
class SurfaceHit:
    file: str
    line: int
    name: str
    kind: str = "function"
    language: str = "unknown"
    entry: bool = False
    extractor: str = "regex"


@dataclass(frozen=True)
class StaticTool:
    name: str
    binary: str
    args: tuple[str, ...] = ()
    extensions: tuple[str, ...] = ()
    requires_config: bool = False
    single_target: bool = False
    cwd_target: bool = False


@dataclass
class Adapter:
    profile: TargetProfile
    name: str
    kind: str
    extensions: tuple[str, ...]
    languages: tuple[str, ...]
    surface_patterns: tuple[tuple[str, str], ...] = ()
    static_tools: tuple[StaticTool, ...] = ()
    sandbox_kind: str = "generic"

    # -- detection ---------------------------------------------------------
    def score(self, files: Sequence[Path], manifest_text: str = "") -> int:
        lowered = manifest_text.lower()
        score = sum(2 for f in files if f.suffix.lower() in self.extensions)
        if self.name == "web2_api":
            for marker in ("openapi", "swagger", "fastapi", "django", "flask", "express", "spring"):
                if marker in lowered:
                    score += 3
        elif self.name == "svm":
            for marker in ("anchor-lang", "anchor-spl", "solana-program", "cargo.toml"):
                if marker in lowered:
                    score += 3
        elif self.name == "evm":
            for marker in ("foundry", "hardhat", "solidity", "openzeppelin"):
                if marker in lowered:
                    score += 3
        elif self.name == "move":
            for marker in ("move.toml", "aptos", "sui::"):
                if marker in lowered:
                    score += 3
        elif self.name == "native_binary":
            for marker in ("cmakelists", "makefile", "gcc", "clang"):
                if marker in lowered:
                    score += 2
        return score

    # -- surfaces ----------------------------------------------------------
    def surfaces(self, files: Sequence[Path], root: Path, max_surfaces: int = 3000):
        from adapters.generic_ast import extract_surfaces

        return extract_surfaces(
            files,
            root,
            patterns=self.surface_patterns,
            extensions=self.extensions,
            max_surfaces=max_surfaces,
        )

    # -- sandbox -----------------------------------------------------------
    def sandbox_files(self, service: str) -> dict[str, str]:
        return {
            "README.md": (
                f"# Sandbox: {service}\n\n"
                f"Profile `{self.profile.value}` has no dedicated template yet.\n"
                "Run experiments locally only. Never point this at production.\n"
            ),
            "run.sh": "#!/usr/bin/env bash\nset -euo pipefail\necho 'configure sandbox'\n",
        }

    def sandbox_instructions(self) -> str:
        return (
            "Generic sandbox. Run only local, isolated experiments. "
            "Pin dependencies and capture stdout/stderr under .apex/experiments/."
        )

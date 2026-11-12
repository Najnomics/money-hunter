"""Adapter registry and TargetProfile detection."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from adapters.base import Adapter, StaticTool, SurfaceHit
from adapters import evm, move, native, svm, web2
from fsutil import read_text
from schemas.common import TargetProfile

# A hybrid target uses the union of the domain adapters' extraction patterns
# and tools; the generic adapter below provides that union.
HYBRID = Adapter(
    profile=TargetProfile.HYBRID,
    name="hybrid",
    kind="mixed",
    extensions=tuple({*web2.ADAPTER.extensions, *evm.ADAPTER.extensions, *svm.ADAPTER.extensions, *move.ADAPTER.extensions, *native.ADAPTER.extensions}),
    languages=tuple(sorted({*web2.ADAPTER.languages, *evm.ADAPTER.languages, *svm.ADAPTER.languages, *move.ADAPTER.languages, *native.ADAPTER.languages})),
    surface_patterns=tuple({*web2.ADAPTER.surface_patterns, *evm.ADAPTER.surface_patterns, *svm.ADAPTER.surface_patterns, *move.ADAPTER.surface_patterns, *native.ADAPTER.surface_patterns}),
    static_tools=(
        web2.ADAPTER.static_tools[1],  # bandit
        evm.ADAPTER.static_tools[0],   # slither
    ),
    sandbox_kind="hybrid",
)

GENERIC = Adapter(
    profile=TargetProfile.UNKNOWN,
    name="generic",
    kind="unknown",
    extensions=tuple(),
    languages=tuple(),
    surface_patterns=(),
    static_tools=(
        web2.ADAPTER.static_tools[1],  # bandit
    ),
    sandbox_kind="generic",
)

ALL_ADAPTERS: tuple[Adapter, ...] = (
    web2.ADAPTER,
    evm.ADAPTER,
    svm.ADAPTER,
    move.ADAPTER,
    native.ADAPTER,
)

_BY_PROFILE: dict[str, Adapter] = {
    TargetProfile.WEB2_API.value: web2.ADAPTER,
    TargetProfile.EVM.value: evm.ADAPTER,
    TargetProfile.SVM.value: svm.ADAPTER,
    TargetProfile.MOVE.value: move.ADAPTER,
    TargetProfile.NATIVE_BINARY.value: native.ADAPTER,
    TargetProfile.HYBRID.value: HYBRID,
    TargetProfile.UNKNOWN.value: GENERIC,
}

MANIFEST_NAMES = {
    "cargo.toml", "anchor.toml", "package.json", "go.mod", "pyproject.toml",
    "requirements.txt", "pom.xml", "build.gradle", "build.gradle.kts",
    "foundry.toml", "hardhat.config.js", "hardhat.config.ts", "move.toml",
    "cmakelists.txt", "makefile", "dockerfile", "docker-compose.yml",
    "compose.yml", "openapi.yaml", "openapi.yml", "swagger.yaml", "swagger.json",
    "mix.exs", "gemfile", "composer.json",
}


def get_adapter(profile: str | TargetProfile | None) -> Adapter:
    if isinstance(profile, TargetProfile):
        key = profile.value
    else:
        key = str(profile or TargetProfile.UNKNOWN.value)
    return _BY_PROFILE.get(key, GENERIC)


def manifest_files(files: Iterable[Path]) -> list[Path]:
    return [f for f in files if f.name.lower() in MANIFEST_NAMES]


def detect_profile(root: Path, files: Sequence[Path]) -> tuple[TargetProfile, dict[str, int]]:
    """Score each adapter against the file set and manifest text."""
    manifest_paths = manifest_files(files)
    manifest_text = "\n".join(read_text(p, max_bytes=200_000) for p in manifest_paths[:40])
    binary_like = 0
    for f in files[:2000]:
        try:
            with f.open("rb") as fh:
                head = fh.read(4)
            if head.startswith(b"\x7fELF") or head.startswith(b"MZ"):
                binary_like += 1
        except OSError:
            continue

    scores: dict[str, int] = {}
    for adapter in ALL_ADAPTERS:
        score = adapter.score(files, manifest_text)
        if adapter.profile == TargetProfile.NATIVE_BINARY:
            score += binary_like * 5
        scores[adapter.profile.value] = score

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    positive = [(name, score) for name, score in ranked if score > 0]
    if not positive:
        return TargetProfile.UNKNOWN, scores
    if len(positive) >= 2 and positive[0][1] > 0 and positive[1][1] >= max(3, positive[0][1] // 2):
        return TargetProfile.HYBRID, scores
    return TargetProfile(positive[0][0]), scores

"""Native binary / C / C++ adapter."""
from __future__ import annotations

from adapters.base import Adapter, StaticTool
from schemas.common import TargetProfile

SURFACE_PATTERNS = (
    ("function", r"^(?:static\s+|inline\s+|extern\s+)*[A-Za-z_][\w\s\*]*\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*\{"),
    ("function", r"\b(?:void|int|char|size_t|long|short)\s+([A-Za-z_]\w*)\s*\("),
)

ADAPTER = Adapter(
    profile=TargetProfile.NATIVE_BINARY,
    name="native_binary",
    kind="binaries",
    extensions=(".c", ".h", ".cc", ".cpp", ".hpp"),
    languages=("c", "cpp"),
    surface_patterns=SURFACE_PATTERNS,
    static_tools=(
        StaticTool(
            name="cppcheck",
            binary="cppcheck",
            args=("--enable=warning,style,performance,portability", "--xml", "--xml-version=2", "{paths}"),
        ),
        StaticTool(
            name="flawfinder",
            binary="flawfinder",
            args=("--csv", "{paths}"),
        ),
    ),
    sandbox_kind="process",
)


def sandbox_files(service: str) -> dict[str, str]:
    return {
        "Dockerfile": (
            "FROM ubuntu:24.04\n"
            "RUN apt-get update && apt-get install -y --no-install-recommends gdb strace ltrace ca-certificates \\\n"
            "    && rm -rf /var/lib/apt/lists/*\n"
            "WORKDIR /work\n"
            "COPY . /work\n"
            "CMD [\"/bin/bash\"]\n"
        ),
        "run.sh": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "BIN=\"${1:-./target}\"\n"
            "timeout 60 \"$BIN\" --help || true\n"
        ),
        "README.md": (
            f"# {service} — process sandbox\n\n"
            "```bash\ndocker build -t " + service + "-sandbox .\n"
            "docker run --rm -it --network=none --cap-drop=ALL --security-opt=no-new-privileges " + service + "-sandbox\n```\n\n"
            "Attach gdb/strace. Never execute an unknown sample outside this container.\n"
        ),
    }


ADAPTER.sandbox_files = sandbox_files  # type: ignore[method-assign]
ADAPTER.sandbox_instructions = (  # type: ignore[method-assign]
    lambda: "Isolated process container. No network, dropped capabilities, 60s timeout. "
    "Use gdb/strace for reverse engineering."
)

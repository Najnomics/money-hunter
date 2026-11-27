"""EVM / Solidity adapter."""
from __future__ import annotations

from adapters.base import Adapter, StaticTool
from schemas.common import TargetProfile

SURFACE_PATTERNS = (
    ("function", r"\bfunction\s+([A-Za-z_]\w*)\s*\("),
    ("modifier", r"\bmodifier\s+([A-Za-z_]\w*)"),
    ("function", r"\b(?:receive|fallback)\s*\(\s*\)"),
    ("function", r"\bconstructor\s*\("),
    ("function", r"\b(?:public|external|internal|private)\s+([A-Za-z_]\w*)\s*\("),
)

ADAPTER = Adapter(
    profile=TargetProfile.EVM,
    name="evm",
    kind="contracts",
    extensions=(".sol", ".vy"),
    languages=("solidity", "vyper"),
    surface_patterns=SURFACE_PATTERNS,
    static_tools=(
        StaticTool(
            name="slither",
            binary="slither",
            args=("{paths}", "--json", "{json_out}"),
            single_target=True,
        ),
        StaticTool(
            name="semgrep",
            binary="semgrep",
            args=("--json", "--quiet", "--metrics", "off", "--config", "{config}", "{paths}"),
            requires_config=True,
        ),
    ),
    sandbox_kind="foundry",
)


def sandbox_files(service: str) -> dict[str, str]:
    return {
        "foundry.toml": (
            "[profile.default]\n"
            "src = \"src\"\n"
            "test = \"test\"\n"
            "out = \"out\"\n"
            "libs = [\"lib\"]\n"
            "optimizer = true\n"
            "optimizer_runs = 200\n"
        ),
        "test/InvariantSandbox.t.sol": (
            "// SPDX-License-Identifier: MIT\n"
            "pragma solidity ^0.8.24;\n\n"
            "import \"forge-std/Test.sol\";\n\n"
            "contract InvariantSandbox is Test {\n"
            "    function setUp() public {}\n\n"
            "    function test_placeholder() public {\n"
            "        assertTrue(true);\n"
            "    }\n"
            "}\n"
        ),
        "README.md": (
            f"# {service} — Foundry sandbox\n\n"
            "Put fork target sources under `src/`, fixtures under `test/`, then:\n\n"
            "```bash\nforge test -vvv\n```\n\n"
            "Use `--fork-url $LOCAL_RPC` against a local/anvil fork only. Never a live RPC.\n"
        ),
    }


ADAPTER.sandbox_files = sandbox_files  # type: ignore[method-assign]
ADAPTER.sandbox_instructions = (  # type: ignore[method-assign]
    lambda: "Foundry sandbox. Run against anvil or a local fork; treat all fork URLs as "
    "read-only unless the campaign boundaries say otherwise."
)

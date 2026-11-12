"""Solana / SVM adapter."""
from __future__ import annotations

from adapters.base import Adapter, StaticTool
from schemas.common import TargetProfile

SURFACE_PATTERNS = (
    ("function", r"\bpub\s+fn\s+([A-Za-z_]\w*)\s*\("),
    ("function", r"\bfn\s+([A-Za-z_]\w*)\s*\("),
    ("instructions", r"#\[(?:instruction|program)\][\s\S]{0,120}?fn\s+([A-Za-z_]\w*)"),
)

ADAPTER = Adapter(
    profile=TargetProfile.SVM,
    name="svm",
    kind="programs",
    extensions=(".rs",),
    languages=("rust",),
    surface_patterns=SURFACE_PATTERNS,
    static_tools=(
        StaticTool(
            name="clippy",
            binary="cargo",
            args=("clippy", "--message-format=json", "--", "-W", "clippy::all"),
            cwd_target=True,
        ),
        StaticTool(
            name="semgrep",
            binary="semgrep",
            args=("--json", "--quiet", "--metrics", "off", "--config", "{config}", "{paths}"),
            requires_config=True,
        ),
    ),
    sandbox_kind="anchor",
)


def sandbox_files(service: str) -> dict[str, str]:
    return {
        "Anchor.toml": (
            "[features]\n"
            "resolution = true\n"
            "skip-lint = false\n\n"
            "[programs.localnet]\n"
            f"{service} = \"Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS\"\n\n"
            "[provider]\n"
            "cluster = \"Localnet\"\n"
        ),
        "tests/invariant_test.rs": (
            "// Property test scaffold. Uses localnet only.\n"
            "#[test]\n"
            "fn placeholder_invariant() {\n"
            "    assert!(true);\n"
            "}\n"
        ),
        "README.md": (
            f"# {service} — Anchor sandbox\n\n"
            "```bash\nanchor build\nanchor test --skip-local-validator  # local validator only\n```\n\n"
            "Never submit transactions to mainnet or a public devnet from this harness.\n"
        ),
    }


ADAPTER.sandbox_files = sandbox_files  # type: ignore[method-assign]
ADAPTER.sandbox_instructions = (  # type: ignore[method-assign]
    lambda: "Anchor local-validator sandbox. Build with `anchor build`; run tests against a "
    "local validator and capture transaction logs."
)

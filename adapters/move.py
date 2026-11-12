"""Move (Aptos/Sui) adapter."""
from __future__ import annotations

from adapters.base import Adapter, StaticTool
from schemas.common import TargetProfile

SURFACE_PATTERNS = (
    ("entry", r"\b(?:public\s+)?entry\s+fun\s+([A-Za-z_]\w*)\s*[<(]"),
    ("function", r"\bpublic\s+fun\s+([A-Za-z_]\w*)\s*[<(]"),
    ("function", r"\bfun\s+([A-Za-z_]\w*)\s*[<(]"),
)

ADAPTER = Adapter(
    profile=TargetProfile.MOVE,
    name="move",
    kind="modules",
    extensions=(".move",),
    languages=("move",),
    surface_patterns=SURFACE_PATTERNS,
    static_tools=(
        StaticTool(
            name="move-prove",
            binary="aptos",
            args=("move", "prove", "--named-addresses", "{addresses}"),
            cwd_target=True,
        ),
        StaticTool(
            name="sui-move-test",
            binary="sui",
            args=("move", "test", "--skip-fetch-latest-git-deps"),
            cwd_target=True,
        ),
    ),
    sandbox_kind="move",
)


def sandbox_files(service: str) -> dict[str, str]:
    return {
        "Move.toml": (
            "[package]\n"
            f"name = \"{service}\"\n"
            "version = \"0.0.1\"\n\n"
            "[dependencies]\n"
            "AptosFramework = { git = \"https://github.com/aptos-labs/aptos-core.git\", subdir = \"aptos-move/framework/aptos-framework\", rev = \"main\" }\n"
        ),
        "sources/invariant_test.move": (
            "module 0x1::invariant_test {\n"
            "    #[test]\n"
            "    fun placeholder_invariant() {\n"
            "        assert!(true, 0);\n"
            "    }\n"
            "}\n"
        ),
        "README.md": (
            f"# {service} — Move sandbox\n\n"
            "```bash\naptos move test\n# or\nsui move test\n```\n\n"
            "Run against a local network only; never publish from this harness.\n"
        ),
    }


ADAPTER.sandbox_files = sandbox_files  # type: ignore[method-assign]
ADAPTER.sandbox_instructions = (  # type: ignore[method-assign]
    lambda: "Move test sandbox. Use `aptos move test`/`sui move test` and the prover where "
    "the invariant is mathematical."
)

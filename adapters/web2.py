"""Web2 API / backend adapter."""
from __future__ import annotations

from adapters.base import Adapter, StaticTool
from schemas.common import TargetProfile

SURFACE_PATTERNS = (
    ("route", r"@(?:app|router|bp|blueprint)\.(?:get|post|put|patch|delete|route)\(\s*['\"]([^'\"]+)"),
    ("route", r"\b(?:app|router)\.(?:get|post|put|patch|delete|all)\(\s*['\"]([^'\"]+)"),
    ("route", r"@(?:Get|Post|Put|Patch|Delete|Request)Mapping\(\s*['\"]?([^'\"\)]+)"),
    ("function", r"\bfunc\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\("),
    ("function", r"\basync\s+def\s+([A-Za-z_]\w*)\s*\("),
    ("function", r"\bdef\s+([A-Za-z_]\w*)\s*\("),
    ("function", r"\b(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\], ?]+\s+([A-Za-z_]\w*)\s*\("),
    ("handler", r"\b(?:HandleFunc|Handle)\(\s*['\"]([^'\"]+)"),
)

ADAPTER = Adapter(
    profile=TargetProfile.WEB2_API,
    name="web2_api",
    kind="service",
    extensions=(
        ".py", ".go", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt",
        ".rb", ".php", ".cs",
    ),
    languages=("python", "go", "typescript", "javascript", "java", "kotlin", "ruby", "php", "csharp"),
    surface_patterns=SURFACE_PATTERNS,
    static_tools=(
        StaticTool(
            name="semgrep",
            binary="semgrep",
            args=("--json", "--quiet", "--metrics", "off", "--config", "{config}", "{paths}"),
            requires_config=True,
        ),
        StaticTool(
            name="bandit",
            binary="bandit",
            args=("-r", "-f", "json", "--exit-zero", "{paths}"),
            extensions=(".py",),
        ),
    ),
    sandbox_kind="docker-service",
)


def sandbox_files(service: str) -> dict[str, str]:
    return {
        "Dockerfile": (
            "FROM python:3.12-slim\n"
            "WORKDIR /app\n"
            "COPY . /app\n"
            "RUN pip install --no-cache-dir -r requirements.txt || true\n"
            "RUN pip install --no-cache-dir pytest hypothesis requests\n"
            "CMD [\"python\", \"-m\", \"pytest\", \"-q\"]\n"
        ),
        "docker-compose.yml": (
            "services:\n"
            f"  {service}:\n"
            "    build: .\n"
            "    network_mode: none\n"
            "    read_only: true\n"
            "    tmpfs: [/tmp]\n"
            "    cap_drop: [ALL]\n"
            "    security_opt: [no-new-privileges:true]\n"
            "    mem_limit: 512m\n"
            "    pids_limit: 256\n"
        ),
        "tests/test_invariant.py": (
            "import pytest\n\n"
            "def test_placeholder_invariant():\n"
            "    # Replace with a property from .apex/02_mental_model.json.\n"
            "    assert True\n"
        ),
        "README.md": (
            f"# {service} — Web2 sandbox\n\n"
            "Copy the target fixture into this directory, then:\n\n"
            "```bash\ndocker compose run --rm " + service + " python -m pytest -q\n```\n\n"
            "Network is disabled. Bind fixtures locally; never point at production.\n"
        ),
    }


ADAPTER.sandbox_files = sandbox_files  # type: ignore[method-assign]
ADAPTER.sandbox_instructions = (  # type: ignore[method-assign]
    lambda: "Docker service sandbox with networking disabled. Use pytest/hypothesis "
    "against the specific invariant and capture logs under .apex/experiments/."
)

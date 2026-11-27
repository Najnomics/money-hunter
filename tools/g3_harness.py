"""Local Foundry distinguishing-attack harness (protocol-agnostic family fixtures).

Gate 3 execute=true runs these tests with forge. A passing attack is evidence
that the family's distinguishing prediction holds; it is not an Immunefi
submission.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from fsutil import run_command

PAIR_MARK = "pair:"
# Immunefi Plether freeze (information/scope/resources pages). Never use
# Plether-Fi/plether-core master for recall scoring.
CONTEST_PIN = "a82d4fefb02768e5b3bddcc97dee371eee24fea8"
FAMILY_CONTRACT: dict[str, str] = {
    "refundable-receipt-in-nav": "NavReceiptAttack",
    "share-supply-overflow": "OverflowFreezeAttack",
    "hwm-recap-accounting": "HwmRecapAttack",
    "delayed-order-optionality": "DelayedOrderAttack",
    "oracle-staleness-calendar-watermark": "OracleStaleAttack",
    "false-emergency-mode": "FalseEmergencyAttack",
}

# Blind3 NAMED_OPEN (20 former kills + 17 newly named pairs + 99136).
NAMED_OPEN_IDS: tuple[str, ...] = (
    "97591", "97906", "98172", "99075", "98209", "98854",
    "97628", "97590", "97760", "97844", "97968", "99735",
    "97603", "97848", "98994", "99501",
    "97715", "97733", "98961", "99392",
    "97677", "97858", "98035", "98941", "99536", "99589", "99855",
    "97903", "97605", "97748", "99795",
    "97622", "97893", "98039", "99470", "99602", "99933",
    "99136",
)

# Honest SCORE-B: exact test PASSed on a82d4fe and FAILed on the local patch.
VERIFIED_IDS: frozenset[str] = frozenset(
    {
        "97906", "98172", "99075", "97628", "99136",
        "97591", "98209", "98854", "97590",
        "97677", "97715", "98961", "99470",
    }
)


def harness_root() -> Path:
    return Path(__file__).resolve().parent.parent / "harness" / "g3"


def contest_repo_root(perps: Path | None = None) -> Path:
    perps = perps or plether_perps_root()
    if perps.name == "perps":
        return perps.parents[1]
    return perps


def pinned_head(repo: Path | None = None) -> str:
    import subprocess

    repo = repo or contest_repo_root()
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.stdout or "").strip()


def require_contest_pin(repo: Path | None = None) -> str:
    head = pinned_head(repo)
    if head != CONTEST_PIN:
        raise RuntimeError(
            f"Plether HEAD {head or '(missing)'} is not contest pin {CONTEST_PIN}. "
            "Do not score against Plether-Fi main. See findings/plether-blind3/PIN.md."
        )
    return head


def plether_perps_root() -> Path:
    override = os.environ.get("APEX_PLETHER_PERPS")
    if override:
        return Path(override)
    return Path("/agent/repos/audit-comp-plether/packages/perps")


def sync_plether_tests() -> Path:
    src = Path(__file__).resolve().parent.parent / "harness" / "g3_plether" / "test"
    dest = plether_perps_root() / "test" / "apex_g3"
    dest.mkdir(parents=True, exist_ok=True)
    if src.exists():
        for path in src.glob("*.sol"):
            (dest / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def forge_bin() -> str:
    found = shutil.which("forge")
    if found:
        return found
    home = Path.home() / ".foundry" / "bin" / "forge"
    if home.exists():
        return str(home)
    raise FileNotFoundError("forge not found on PATH or ~/.foundry/bin")


def parse_pair(blob: str) -> tuple[str, str]:
    match = re.search(rf"{re.escape(PAIR_MARK)}([A-Za-z_]\w*)::([A-Za-z_]\w*)", blob or "")
    if match:
        return match.group(1), match.group(2)
    return "", ""


def contract_for(family: str, function: str = "", var: str = "") -> str:
    if family in FAMILY_CONTRACT:
        return FAMILY_CONTRACT[family]
    from tools.pair_templates import match_pair_template

    template = match_pair_template(function, var) if function and var else None
    if template and template.family in FAMILY_CONTRACT:
        return FAMILY_CONTRACT[template.family]
    return ""


def match_test(function: str, var: str) -> str:
    fn = re.sub(r"[^A-Za-z0-9]+", "_", function or "").strip("_")
    sink = re.sub(r"[^A-Za-z0-9]+", "_", var or "").strip("_")
    if fn and sink:
        return f"test_attack_{fn}_{sink}"
    return ""


def run_distinguishing(
    *,
    family: str,
    function: str,
    var: str,
    timeout_seconds: int = 120,
) -> dict:
    """Run the exact test_attack_<fn>_<var> against real Plether. No family fallback."""
    del family  # family must not select an unrelated planted-bug contract
    test_name = match_test(function, var)
    empty = {
        "ok": False,
        "returncode": 2,
        "stdout": "",
        "stderr": "",
        "command": "",
        "contract": "ApexG3TargetsTest",
        "timed_out": False,
        "inconclusive": True,
    }
    if not test_name:
        empty["stderr"] = f"no exact test for {function}::{var}"
        return empty
    sources = Path(__file__).resolve().parent.parent / "harness" / "g3_plether" / "test"
    if sources.exists() and not any(
        f"function {test_name}(" in p.read_text(encoding="utf-8") for p in sources.glob("*.t.sol")
    ):
        empty["stderr"] = f"no exact test source for {test_name}"
        return empty
    root = plether_perps_root()
    if not (root / "foundry.toml").exists():
        empty["stderr"] = f"plether perps root missing: {root}"
        return empty
    try:
        require_contest_pin(contest_repo_root(root))
    except RuntimeError as exc:
        empty["stderr"] = str(exc)
        return empty
    sync_plether_tests()
    forge = forge_bin()
    env = os.environ.copy()
    env["PATH"] = str(Path(forge).parent) + os.pathsep + env.get("PATH", "")
    command = [
        forge,
        "test",
        "--root",
        str(root),
        "--match-path",
        "test/apex_g3/*",
        "--match-test",
        f"^{test_name}$",
        "-vv",
    ]
    result = run_command(command, cwd=root, timeout_seconds=timeout_seconds, env=env)
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    blob = stdout + stderr
    no_match = "No tests match" in blob or "0 tests" in blob and "passed" in blob and "[PASS]" not in blob
    if no_match or "[PASS]" not in stdout and "[FAIL" not in stdout:
        return {
            "ok": False,
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr or f"no exact test {test_name}",
            "command": " ".join(command),
            "contract": "ApexG3TargetsTest",
            "timed_out": result.timed_out,
            "inconclusive": True,
        }
    passed = result.returncode == 0 and "[FAIL" not in stdout
    return {
        "ok": passed and not result.timed_out,
        "returncode": result.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "command": " ".join(command),
        "contract": "ApexG3TargetsTest",
        "timed_out": result.timed_out,
        "inconclusive": False,
    }

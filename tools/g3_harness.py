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


def harness_root() -> Path:
    return Path(__file__).resolve().parent.parent / "harness" / "g3"


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
    """Run the family Foundry attack. Prefer an exact test_attack_fn_var match."""
    root = harness_root()
    contract = contract_for(family, function, var)
    if not contract:
        return {
            "ok": False,
            "returncode": 2,
            "stdout": "",
            "stderr": f"no family fixture for family={family} {function}::{var}",
            "command": "",
            "contract": "",
        }
    forge = forge_bin()
    env = os.environ.copy()
    env["PATH"] = str(Path(forge).parent) + os.pathsep + env.get("PATH", "")
    test_name = match_test(function, var)
    command = [forge, "test", "--root", str(root), "--match-contract", contract, "-vv"]
    if test_name:
        command.extend(["--match-test", test_name])
    result = run_command(command, cwd=root, timeout_seconds=timeout_seconds, env=env)
    stdout = result.stdout or ""
    no_match = "No tests match" in (result.stderr or "") or "No tests match" in stdout
    if no_match and test_name:
        command = [forge, "test", "--root", str(root), "--match-contract", contract, "-vv"]
        result = run_command(command, cwd=root, timeout_seconds=timeout_seconds, env=env)
        stdout = result.stdout or ""
    passed = result.returncode == 0 and "fail" not in stdout.lower().split("Suite result:")[-1]
    if result.returncode == 0 and "[FAIL" not in stdout:
        passed = True
    return {
        "ok": passed and not result.timed_out,
        "returncode": result.returncode,
        "stdout": stdout,
        "stderr": result.stderr or "",
        "command": " ".join(command),
        "contract": contract,
        "timed_out": result.timed_out,
    }

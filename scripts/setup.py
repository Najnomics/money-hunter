#!/usr/bin/env python3
"""One-click setup for Apex Core.

What it does, in plain English:
  1. Creates a private Python environment for the tool.
  2. Installs the dependencies.
  3. Optionally clones/updates the shared intel corpus (never vendored).
  4. Writes MCP config so Cursor/Claude can see the tools.
  5. Sets the campaign strictness for a target, if one is supplied.

The MCP server can be configured once, globally.  If `--target` is omitted,
the config has no fixed workspace and the agent passes `workspace` with each
tool call.  If `--target` is supplied, that target becomes the default.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
SERVER_NAME = "apex-core"


def run(args: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=str(cwd or CORE), check=True)


def venv_python() -> Path:
    if platform.system() == "Windows":
        return CORE / ".venv" / "Scripts" / "python.exe"
    return CORE / ".venv" / "bin" / "python"


def install_deps(skip: bool) -> Path:
    python = venv_python()
    if not skip and not python.exists():
        run([sys.executable, "-m", "venv", str(CORE / ".venv")])
    if not skip:
        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(python), "-m", "pip", "install", "-r", str(CORE / "requirements.txt")])
    if python.exists():
        return python
    return Path(sys.executable)


def sync_intel(repo: str) -> Path:
    dest = Path(os.environ.get("APEX_INTEL_CORPUS", Path.home() / ".apex" / "intel" / "bugbounty-intel")).expanduser()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if (dest / ".git").is_dir():
        run(["git", "-C", str(dest), "fetch", "--prune", "origin"])
        run(["git", "-C", str(dest), "pull", "--ff-only"])
    else:
        run(["git", "clone", "--depth", "1", repo, str(dest)])
    return dest


def mcp_server(python: Path, target: Path | None, intel: Path | None) -> dict:
    args = [str(CORE / "main.py"), "--mcp"]
    if target is not None:
        args.extend(["--workspace", str(target)])
    server: dict = {"command": str(python), "args": args}
    if intel is not None:
        server["env"] = {"APEX_INTEL_CORPUS": str(intel)}
    return server


def merge_config(path: Path, server: dict, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            backup = path.with_suffix(".json.bak")
            shutil.copyfile(path, backup)
            print(f"Could not parse {path}; backed it up to {backup}")
            existing = {}
    servers = existing.setdefault("mcpServers", {})
    if SERVER_NAME in servers and not force:
        print(f"{path}: '{SERVER_NAME}' already exists; leaving it unchanged (use --force to replace).")
        return
    servers[SERVER_NAME] = server
    path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def claude_config_path() -> Path:
    home = Path.home()
    system = platform.system()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        return appdata / "Claude" / "claude_desktop_config.json"
    return home / ".config" / "Claude" / "claude_desktop_config.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up Apex Core and MCP clients.")
    parser.add_argument("--target", help="Target workspace. Omit for a global, per-call-workspace server.")
    parser.add_argument("--client", choices=["cursor", "claude", "both", "none"], default="none")
    parser.add_argument("--policy", choices=["light", "standard", "strict"], default="standard")
    parser.add_argument("--intel", action="store_true", help="Clone/update the shared intel corpus.")
    parser.add_argument("--intel-repo", default=os.environ.get("APEX_INTEL_REPO", "git@github.com:Najnomics/bugbounty-intel.git"))
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--force", action="store_true", help="Replace an existing MCP server entry.")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve() if args.target else None
    if target is not None and not target.is_dir():
        parser.error(f"target is not a directory: {target}")

    python = install_deps(args.skip_install)
    intel = sync_intel(args.intel_repo) if args.intel else (
        Path.home() / ".apex" / "intel" / "bugbounty-intel"
        if (Path.home() / ".apex" / "intel" / "bugbounty-intel" / "INDEX.md").exists()
        else None
    )
    server = mcp_server(python, target, intel)

    if target is not None:
        run([str(python), str(CORE / "main.py"), "--policy", args.policy, "--workspace", str(target)])

    if args.client in {"cursor", "both"}:
        if target is None:
            print("Cursor project config needs --target. Printing the snippet instead:")
            print(json.dumps({"mcpServers": {SERVER_NAME: server}}, indent=2))
        else:
            merge_config(target / ".cursor" / "mcp.json", server, args.force)

    if args.client in {"claude", "both"}:
        merge_config(claude_config_path(), server, args.force)

    if args.client == "none":
        print(json.dumps({"mcpServers": {SERVER_NAME: server}}, indent=2))

    print("\nDone.")
    if target is None:
        print("Global server: the agent must pass `workspace` in each tool call.")
    else:
        print(f"Default workspace: {target}")
    print("Restart the client, then call phase0_parse_scope.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

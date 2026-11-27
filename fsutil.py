"""Small, dependency-free filesystem and process helpers.

Everything here is read-only by default. The only process execution helper is
``run_command``, which is used by the static-sweep and experiment tools and is
always invoked with an explicit timeout.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".apex",
    ".belzeebub",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "target",
    "dist",
    "build",
    "out",
    "cache",
    ".idea",
    ".vscode",
    ".next",
    "coverage",
}

TEXT_SUFFIXES = {
    ".md", ".txt", ".rst", ".adoc", ".json", ".jsonl", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".py", ".go", ".rs", ".sol", ".vy", ".move",
    ".cairo", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".cs", ".rb",
    ".php", ".swift", ".dart", ".c", ".h", ".cc", ".cpp", ".hpp", ".sh",
    ".graphql", ".gql", ".proto", ".html", ".sql", ".xml", ".lock",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def walk_files(
    paths: Iterable[str | Path],
    max_files: int = 5000,
    exts: Iterable[str] | None = None,
    include_hidden: bool = False,
) -> list[Path]:
    """Deterministically walk files, pruning vendor/build/VCS directories."""
    allowed = {e.lower() for e in exts} if exts else None
    out: list[Path] = []
    seen: set[str] = set()

    for raw in paths:
        p = Path(raw).expanduser()
        if not p.exists():
            continue
        if p.is_file():
            if allowed and p.suffix.lower() not in allowed:
                continue
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                out.append(p)
            continue

        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = [
                d for d in sorted(dirnames)
                if d not in EXCLUDED_DIRS and (include_hidden or not d.startswith("."))
            ]
            for name in sorted(filenames):
                f = Path(dirpath) / name
                if allowed and f.suffix.lower() not in allowed:
                    continue
                key = str(f.resolve())
                if key in seen:
                    continue
                seen.add(key)
                out.append(f)
                if len(out) >= max_files:
                    return out
    return out


def is_binary(path: Path, sample: int = 8192) -> bool:
    try:
        with path.open("rb") as fh:
            chunk = fh.read(sample)
    except OSError:
        return True
    if b"\x00" in chunk:
        return True
    if chunk.startswith(b"\x7fELF") or chunk.startswith(b"MZ"):
        return True
    return False


def read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        data = path.read_bytes()
        raw = data if max_bytes <= 0 else data[:max_bytes]
    except OSError:
        return ""
    if b"\x00" in raw[:8192]:
        return ""
    return raw.decode("utf-8", errors="replace")


def read_lines(path: Path, max_bytes: int = 2_000_000) -> list[str]:
    return read_text(path, max_bytes).splitlines()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


def rel_to(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except (ValueError, OSError):
        try:
            return os.path.relpath(str(path), str(root))
        except ValueError:
            return str(path)


def write_text_atomic(path: Path, text: str) -> None:
    """Write a complete file atomically.

    A unique temp name prevents two concurrent tool calls from writing into the
    same temporary file.  JSON files are re-parsed before the rename, so a
    malformed section can never replace a good artifact.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".json":
        json.loads(text)  # fail before touching the old file
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_seconds: float


def run_command(
    args: Sequence[str],
    cwd: Path | str,
    timeout_seconds: int = 120,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """Run a command with a hard timeout and captured output.

    Output is capped so a runaway linter cannot exhaust agent context.
    """
    started = time.monotonic()
    run_env = os.environ.copy()
    run_env.setdefault("NO_COLOR", "1")
    run_env.setdefault("CI", "1")
    if env:
        run_env.update(env)
    try:
        completed = subprocess.run(
            list(args),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout_seconds,
            env=run_env,
            check=False,
        )
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout[:2_000_000],
            stderr=completed.stderr[:2_000_000],
            timed_out=False,
            duration_seconds=round(time.monotonic() - started, 2),
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            returncode=124,
            stdout=(exc.stdout or "")[:2_000_000] if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "")[:2_000_000] if isinstance(exc.stderr, str) else "",
            timed_out=True,
            duration_seconds=round(time.monotonic() - started, 2),
        )
    except OSError as exc:
        return CommandResult(
            returncode=127,
            stdout="",
            stderr=str(exc),
            timed_out=False,
            duration_seconds=round(time.monotonic() - started, 2),
        )

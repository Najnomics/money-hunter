"""Best-effort PDF text extraction with no required dependency.

Prefers ``pdftotext`` or ``pypdf`` when present, then falls back to inflating
PDF streams and collecting literal strings. Good enough to index past-audit
PDFs into the known-issue / hypothesis seed path.
"""
from __future__ import annotations

import re
import shutil
import zlib
from pathlib import Path

from fsutil import run_command

_STREAM_RE = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)
_LITERAL_RE = re.compile(rb"\((?:\\.|[^\\)])*\)")
_TJ_RE = re.compile(rb"\[(.*?)\]\s*TJ", re.DOTALL)


def extract_pdf_text(path: Path, max_chars: int = 400_000) -> str:
    """Return extracted text, or empty string if the file is not a readable PDF."""
    path = Path(path)
    if path.suffix.lower() != ".pdf" or not path.is_file():
        return ""
    for extractor in (_pdftotext, _pypdf, _raw_pdf_strings):
        try:
            text = extractor(path)
        except Exception:
            continue
        text = _clean(text)
        if text.strip():
            return text[:max_chars]
    return ""


def _clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pdftotext(path: Path) -> str:
    binary = shutil.which("pdftotext")
    if not binary:
        return ""
    result = run_command([binary, "-layout", "-q", str(path), "-"], timeout_seconds=30)
    if result.returncode != 0:
        return ""
    return result.stdout or ""


def _pypdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return ""
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages[:80]:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _raw_pdf_strings(path: Path) -> str:
    data = path.read_bytes()[:8_000_000]
    chunks: list[bytes] = [data]
    for match in _STREAM_RE.finditer(data):
        payload = match.group(1)
        for decoder in (_identity, _zlib, _zlib_raw):
            try:
                decoded = decoder(payload)
            except Exception:
                continue
            if decoded:
                chunks.append(decoded)
                break
    texts: list[str] = []
    for chunk in chunks:
        texts.extend(_literals(chunk))
        for tj in _TJ_RE.finditer(chunk):
            texts.extend(_literals(tj.group(1)))
    return "\n".join(t for t in texts if t.strip())


def _identity(payload: bytes) -> bytes:
    return payload


def _zlib(payload: bytes) -> bytes:
    return zlib.decompress(payload)


def _zlib_raw(payload: bytes) -> bytes:
    return zlib.decompress(payload, wbits=-15)


def _literals(chunk: bytes) -> list[str]:
    out: list[str] = []
    for match in _LITERAL_RE.finditer(chunk):
        raw = match.group(0)[1:-1]
        raw = (
            raw.replace(b"\\n", b"\n")
            .replace(b"\\r", b"\r")
            .replace(b"\\t", b"\t")
            .replace(b"\\(", b"(")
            .replace(b"\\)", b")")
            .replace(b"\\\\", b"\\")
        )
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")
        if any(ch.isalpha() for ch in text) and len(text.strip()) >= 3:
            out.append(text)
    return out

"""Phase 1 — Research: docs, historical audits, disclosed intel, CVE hook.

In plain English: read what the project says it does before reading what the
code actually does.  This is also where past audits and known issues are
indexed, so the agent does not rediscover them as new findings.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from fsutil import now_iso, read_text, rel_to, run_command, sha1_text, walk_files
from runtime import ToolContext, ToolSpec, tool
from tools.pdftext import extract_pdf_text
from tools.protocol_families import default_family_keywords
from schemas.phase1 import (
    Advisory,
    Ambiguity,
    CheckIntelInput,
    CheckIntelOutput,
    CVEsInput,
    CVEsOutput,
    DocClaim,
    DocSource,
    IngestDocsInput,
    IngestDocsOutput,
    IntelMatch,
    PackageRef,
    PastFinding,
    ReviewAuditsInput,
    ReviewAuditsOutput,
)
from tools._shared import default_existing

DOC_EXTS = {".md", ".txt", ".rst", ".adoc", ".json", ".yaml", ".yml", ".graphql", ".gql", ".proto"}
AUDIT_EXTS = {".md", ".txt", ".json", ".jsonl", ".rst", ".pdf"}
MODAL_RE = re.compile(r"\b(should|must|shall|never|always|only|required|forbidden|may)\b", re.I)
AMBIGUITY_RE = re.compile(
    r"\b(todo|tbd|to be determined|not specified|implementation[- ]defined|unspecified|"
    r"ambiguous|left to the implementation|assume[d]?\b|out of scope)\b",
    re.I,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.{3,200})$")
FINDING_RE = re.compile(
    r"(finding|vulnerab|exploit|issue|risk|\[[A-Z]{1,2}-\d+\]|\b(critical|high|medium|low)\b)",
    re.I,
)
SEVERITY_RE = re.compile(r"\b(critical|high|medium|low|informational|info)\b", re.I)
ACK_RE = re.compile(r"\b(acknowledged|won'?t fix|wontfix|known issue|by design|out of scope)\b", re.I)


@tool(
    name="ingest_docs",
    phase=1,
    section="docs",
    summary="Read specs/READMEs/API schemas and extract stated claims plus ambiguity/silence.",
    input_model=IngestDocsInput,
    output_model=IngestDocsOutput,
    tags=("docs", "intent"),
)
def ingest_docs(ctx: ToolContext, inp: IngestDocsInput) -> IngestDocsOutput:
    paths = inp.paths or default_existing(
        ctx, ["docs", "doc", "README.md", "readme.md", "SPEC.md", "spec", "whitepaper.md", "api"]
    )
    files = walk_files([ctx.resolve(p) for p in paths], max_files=inp.max_files, exts=DOC_EXTS)

    sources: list[DocSource] = []
    claims: list[DocClaim] = []
    ambiguities: list[Ambiguity] = []
    api_schemas: list[str] = []
    notes: list[str] = []

    for path in files:
        text = read_text(path)
        if not text:
            continue
        rel = rel_to(path, ctx.workspace)
        line_count = text.count("\n") + 1
        sources.append(DocSource(path=rel, bytes=len(text.encode("utf-8")), lines=line_count))
        lowered = path.name.lower()
        if any(token in lowered for token in ("openapi", "swagger", "graphql", "schema", ".proto", ".gql")):
            api_schemas.append(rel)

        for idx, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if 20 <= len(stripped) <= 400:
                match = MODAL_RE.search(stripped)
                if match and len(claims) < inp.max_claims:
                    claims.append(
                        DocClaim(text=stripped[:400], modal=match.group(1).lower(), path=rel, line=idx)
                    )
                ambiguity = AMBIGUITY_RE.search(stripped)
                if ambiguity and len(ambiguities) < 300:
                    ambiguities.append(
                        Ambiguity(topic=stripped[:120], reason=ambiguity.group(1), path=rel, line=idx)
                    )

    if not files:
        notes.append("No documentation files found. Read official docs manually and rerun with --paths.")
    summary = (
        f"Read {len(sources)} doc source(s); extracted {len(claims)} stated claims, "
        f"{len(ambiguities)} ambiguity/silence markers, {len(api_schemas)} API schema(s)."
    )
    return IngestDocsOutput(
        sources=sources,
        claims=claims,
        ambiguities=ambiguities,
        api_schemas=sorted(set(api_schemas)),
        summary=summary,
        notes=notes,
    )


@tool(
    name="review_past_audits",
    phase=1,
    section="audits",
    summary="Index past audits/post-mortems and known issues to prevent duplicate findings.",
    input_model=ReviewAuditsInput,
    output_model=ReviewAuditsOutput,
    tags=("dedupe", "intel"),
)
def review_past_audits(ctx: ToolContext, inp: ReviewAuditsInput) -> ReviewAuditsOutput:
    paths = inp.paths or default_existing(
        ctx, ["audits", "audit", "docs/audits", "security", "postmortems", "post-mortems", "reports"]
    )
    files = walk_files([ctx.resolve(p) for p in paths], max_files=inp.max_files, exts=AUDIT_EXTS)

    findings: list[PastFinding] = []
    known_issues: list[str] = []
    sources: list[str] = []
    dedupe: dict[str, list[str]] = {}

    pdfs_read = 0
    for path in files:
        if path.suffix.lower() == ".pdf":
            text = extract_pdf_text(path)
            if text:
                pdfs_read += 1
        else:
            text = read_text(path)
        if not text:
            continue
        rel = rel_to(path, ctx.workspace)
        sources.append(rel)
        content = text.splitlines()
        for idx, line in enumerate(content, start=1):
            stripped = line.strip()
            if ACK_RE.search(stripped) and 10 <= len(stripped) <= 300:
                known_issues.append(f"{rel}:{idx}: {stripped[:300]}")
            heading = HEADING_RE.match(stripped)
            title = heading.group(2).strip() if heading else ""
            if not title:
                bracket = re.search(r"\[([A-Z]{1,2}-\d+)\]\s*(.+)", stripped)
                if bracket:
                    title = bracket.group(2).strip()
            if not title and FINDING_RE.search(stripped) and 20 <= len(stripped) <= 240:
                title = stripped.lstrip("-* ").strip()
            if not title or not FINDING_RE.search(title):
                continue
            if title.lower().strip("#: ") in {
                "findings", "summary", "introduction", "overview", "appendix",
                "methodology", "scope", "conclusion", "recommendations",
            }:
                continue
            severity_match = SEVERITY_RE.search(title)
            if not severity_match:
                for follow in content[idx: idx + 3]:
                    severity_match = SEVERITY_RE.search(follow)
                    if severity_match:
                        break
            excerpt_lines = []
            for follow in content[idx: idx + 6]:
                follow_s = follow.strip()
                if follow_s and follow_s != stripped:
                    excerpt_lines.append(follow_s)
                if len(" ".join(excerpt_lines)) >= 280:
                    break
            key = sha1_text(re.sub(r"\W+", " ", title.lower()).strip())[:12]
            finding = PastFinding(
                id=f"AF-{len(findings) + 1:04d}",
                title=title[:240],
                severity=severity_match.group(1).lower() if severity_match else None,
                source=rel,
                line=idx,
                dedupe_key=key,
                acknowledged=bool(ACK_RE.search(stripped)),
                excerpt=" ".join(excerpt_lines)[:400],
            )
            findings.append(finding)
            dedupe.setdefault(key, []).append(rel)

    notes: list[str] = []
    if pdfs_read:
        notes.append(f"Extracted text from {pdfs_read} PDF audit report(s).")
    if not sources:
        notes.append("No audit reports found. Known-issue dedupe is empty — record the attempt in notes.")
    return ReviewAuditsOutput(
        sources=sources,
        past_findings=findings[:1000],
        known_issues=known_issues[:300],
        dedupe_index=dedupe,
        notes=notes,
    )


def _bundled_intel_root() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "intel-patterns"


def _find_corpus(ctx: ToolContext, explicit: str | None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(ctx.resolve(explicit))
    env = os.environ.get("APEX_INTEL_CORPUS")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.extend(
        [
            # Shared, auto-updated clone used by the team setup script.
            Path.home() / ".apex" / "intel" / "bugbounty-intel",
            Path.home() / ".apex" / "bugbounty-intel",
            ctx.workspace / "bugbounty-intel",
            ctx.workspace.parent / "bugbounty-intel",
            Path(__file__).resolve().parents[2] / "bugbounty-intel",
        ]
    )
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "INDEX.md").exists():
            return candidate.resolve()
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def _scan_intel_root(root: Path, keywords: list[str], kinds: list[str], source_kind_default: str) -> tuple[list[IntelMatch], list[str], int]:
    roots = [root / "posts", root / "writeups", root / "projects", root / "researchers", root / "patterns"]
    if kinds:
        roots = [root / kind for kind in kinds if (root / kind).is_dir()]
    files = walk_files([r for r in roots if r.exists()], max_files=5000, exts={".md", ".jsonl", ".txt"})
    for extra in ("techniques.md", "INDEX.md"):
        candidate = root / extra
        if candidate.exists():
            files.append(candidate)

    matches: list[IntelMatch] = []
    for path in files:
        text = read_text(path)
        if not text:
            continue
        lowered = text.lower()
        if keywords and not any(k in lowered for k in keywords):
            continue
        first_heading = next((l.strip("# ").strip() for l in text.splitlines() if l.startswith("#")), path.stem)
        score = 0.0
        for keyword in keywords:
            count = lowered.count(keyword)
            if count:
                score += count + (5 if keyword in first_heading.lower() else 0)
        first = min((lowered.find(k) for k in keywords if k in lowered), default=0) if keywords else 0
        snippet = text[max(0, first - 160): first + 420].replace("\n", " ").strip()
        kind = source_kind_default
        rel = rel_to(path, root)
        if rel.startswith("writeups"):
            kind = "writeup"
        elif rel.startswith("projects"):
            kind = "advisory-index"
        elif rel.startswith("researchers"):
            kind = "profile"
        elif rel.startswith("patterns") or "intel-patterns" in str(root):
            kind = "technique"
        matches.append(
            IntelMatch(path=f"{rel}", title=first_heading[:200], snippet=snippet[:600], score=round(score, 2), source_kind=kind)
        )

    techniques: list[str] = []
    techniques_file = root / "techniques.md"
    if techniques_file.exists():
        for line in read_text(techniques_file).splitlines():
            if (not keywords or any(k in line.lower() for k in keywords)) and len(line.strip()) > 10:
                techniques.append(line.strip()[:300])
    return matches, techniques, len(files)


@tool(
    name="check_intel",
    phase=1,
    section="intel",
    summary="Query bundled intel-patterns plus optional bugbounty-intel for comparable bug patterns.",
    input_model=CheckIntelInput,
    output_model=CheckIntelOutput,
    tags=("intel", "corpus"),
)
def check_intel(ctx: ToolContext, inp: CheckIntelInput) -> CheckIntelOutput:
    family_keywords = [k.lower() for k in default_family_keywords()]
    keywords = [k.lower() for k in inp.keywords if k.strip()]
    if not keywords:
        keywords = list(family_keywords)

    matches: list[IntelMatch] = []
    techniques: list[str] = []
    files_scanned = 0
    notes: list[str] = []

    bundled = _bundled_intel_root()
    if bundled.is_dir():
        bundled_matches, bundled_tech, n_files = _scan_intel_root(bundled, keywords, inp.kinds, "technique")
        matches.extend(bundled_matches)
        techniques.extend(bundled_tech)
        files_scanned += n_files
        notes.append(f"Scanned bundled intel-patterns at {bundled} ({n_files} files).")
    else:
        notes.append("Bundled intel-patterns directory is missing from this checkout.")

    corpus = _find_corpus(ctx, inp.corpus_path)
    if corpus is not None and corpus.resolve() != bundled.resolve():
        corpus_matches, corpus_tech, n_files = _scan_intel_root(corpus, keywords, inp.kinds, "post")
        matches.extend(corpus_matches)
        techniques.extend(corpus_tech)
        files_scanned += n_files
        revision = run_command(
            ["git", "-C", str(corpus), "rev-parse", "--short", "HEAD"],
            cwd=corpus,
            timeout_seconds=5,
        )
        if revision.returncode == 0 and revision.stdout.strip():
            committed = run_command(
                ["git", "-C", str(corpus), "log", "-1", "--format=%cs"],
                cwd=corpus,
                timeout_seconds=5,
            )
            date = committed.stdout.strip() if committed.returncode == 0 else "unknown"
            notes.append(
                f"External corpus {corpus} revision {revision.stdout.strip()} (committed {date}). "
                "Run scripts/sync-intel.sh to update."
            )
        else:
            notes.append(f"Scanned external corpus at {corpus}; not a git checkout.")
    else:
        notes.append(
            "Full bugbounty-intel corpus not found. Bundled protocol-family cards still ran. "
            "Set --corpus-path or APEX_INTEL_CORPUS for the larger archive."
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    # Deduplicate technique lines while preserving order.
    seen_tech: set[str] = set()
    unique_tech: list[str] = []
    for line in techniques:
        if line not in seen_tech:
            seen_tech.add(line)
            unique_tech.append(line)

    notes.insert(0, f"Scanned {files_scanned} intel file(s) at {now_iso()}.")
    return CheckIntelOutput(
        corpus_path=str(corpus or bundled),
        queries=inp.keywords or keywords,
        matches=matches[: inp.max_results],
        techniques=unique_tech[:50],
        found=len(matches),
        notes=notes,
    )


def _local_advisories(index: Path, packages: list[PackageRef], limit: int) -> list[Advisory]:
    files = walk_files([index], max_files=1500, exts={".md", ".txt", ".json"})
    advisories: list[Advisory] = []
    for package in packages:
        needle = package.name.lower()
        for path in files:
            text = read_text(path, max_bytes=400_000)
            if needle not in text.lower():
                continue
            rel = rel_to(path, index)
            for idx, line in enumerate(text.splitlines(), start=1):
                if needle in line.lower():
                    advisories.append(
                        Advisory(
                            id=f"LOCAL-{len(advisories) + 1:04d}",
                            summary=line.strip()[:300],
                            package=package.name,
                            version=package.version,
                            source=f"{rel}:{idx}",
                        )
                    )
                    break
            if len(advisories) >= limit:
                return advisories
    return advisories


def _osv_query(package: PackageRef, timeout: int = 15) -> tuple[list[Advisory], str | None]:
    if not package.ecosystem:
        return [], "ecosystem required for OSV query"
    body: dict = {"package": {"name": package.name, "ecosystem": package.ecosystem}}
    if package.version:
        body["version"] = package.version
    request = urllib.request.Request(
        "https://api.osv.dev/v1/query",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return [], f"OSV query failed for {package.name}: {exc}"
    advisories = []
    for vuln in payload.get("vulns", [])[:50]:
        advisories.append(
            Advisory(
                id=vuln.get("id", "UNKNOWN"),
                summary=(vuln.get("summary") or vuln.get("details", ""))[:300],
                package=package.name,
                version=package.version,
                source="osv",
                aliases=list(vuln.get("aliases", [])),
            )
        )
    return advisories, None


@tool(
    name="cves_intel",
    phase=1,
    section="cves",
    summary="Extension hook: query OSV (opt-in) or local advisory indexes for dependency CVEs.",
    input_model=CVEsInput,
    output_model=CVEsOutput,
    tags=("extension", "cves", "supply-chain"),
)
def cves_intel(ctx: ToolContext, inp: CVEsInput) -> CVEsOutput:
    advisories: list[Advisory] = []
    errors: list[str] = []
    network_used = False

    index = ctx.resolve(inp.local_index) if inp.local_index else None
    if index is None:
        corpus = _find_corpus(ctx, None)
        if corpus and (corpus / "projects").is_dir():
            index = corpus / "projects"
    if index and index.exists() and inp.packages:
        advisories.extend(_local_advisories(index, inp.packages, limit=200))

    if inp.allow_network:
        for package in inp.packages:
            found, error = _osv_query(package)
            network_used = True
            advisories.extend(found)
            if error:
                errors.append(error)

    notes = []
    if not inp.packages:
        notes.append("No packages supplied; nothing to query.")
    if not inp.allow_network:
        notes.append("Network disabled by default. Pass --allow-network true to query OSV.")

    return CVEsOutput(
        packages=inp.packages,
        advisories=advisories[:300],
        source="osv+local" if network_used else "local",
        network_used=network_used,
        errors=errors,
        notes=notes,
    )


TOOLS: list[ToolSpec] = [ingest_docs, review_past_audits, check_intel, cves_intel]  # type: ignore[list-item]

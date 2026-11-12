"""Phase 1 — Research: docs, past audits, intel, CVE hook."""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from schemas.common import ApexModel


class DocSource(ApexModel):
    path: str
    bytes: int = 0
    lines: int = 0
    kind: str = "doc"


class DocClaim(ApexModel):
    text: str
    modal: Optional[str] = None
    path: Optional[str] = None
    line: Optional[int] = None


class Ambiguity(ApexModel):
    topic: str
    reason: str
    path: Optional[str] = None
    line: Optional[int] = None


class IngestDocsInput(ApexModel):
    paths: list[str] = Field(default_factory=list, description="Docs directories/files. Empty = common doc locations.")
    include_globs: list[str] = Field(default_factory=list, description="Unused placeholder for future glob support.")
    max_files: int = Field(300, ge=1, le=5000)
    max_claims: int = Field(500, ge=1, le=5000)


class IngestDocsOutput(ApexModel):
    sources: list[DocSource] = Field(default_factory=list)
    claims: list[DocClaim] = Field(default_factory=list)
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    api_schemas: list[str] = Field(default_factory=list)
    summary: str = ""
    notes: list[str] = Field(default_factory=list)


class PastFinding(ApexModel):
    id: str
    title: str
    severity: Optional[str] = None
    source: str
    line: Optional[int] = None
    dedupe_key: str
    acknowledged: bool = False


class ReviewAuditsInput(ApexModel):
    paths: list[str] = Field(default_factory=list, description="Audit reports / post-mortems directories.")
    max_files: int = Field(200, ge=1, le=2000)


class ReviewAuditsOutput(ApexModel):
    sources: list[str] = Field(default_factory=list)
    past_findings: list[PastFinding] = Field(default_factory=list)
    known_issues: list[str] = Field(default_factory=list)
    dedupe_index: dict[str, list[str]] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class IntelMatch(ApexModel):
    path: str
    title: str
    snippet: str
    score: float
    source_kind: str = "post"


class CheckIntelInput(ApexModel):
    keywords: list[str] = Field(..., min_length=1, description="Architecture / bug-class / framework keywords.")
    corpus_path: Optional[str] = Field(None, description="bugbounty-intel root. Auto-detected when omitted.")
    max_results: int = Field(20, ge=1, le=200)
    kinds: list[str] = Field(default_factory=list, description="Restrict to posts/writeups/projects/techniques.")


class CheckIntelOutput(ApexModel):
    corpus_path: Optional[str] = None
    queries: list[str] = Field(default_factory=list)
    matches: list[IntelMatch] = Field(default_factory=list)
    techniques: list[str] = Field(default_factory=list)
    found: int = 0
    notes: list[str] = Field(default_factory=list)


class PackageRef(ApexModel):
    name: str
    version: Optional[str] = None
    ecosystem: Optional[str] = None


class Advisory(ApexModel):
    id: str
    summary: str = ""
    package: Optional[str] = None
    version: Optional[str] = None
    source: str = "local"
    aliases: list[str] = Field(default_factory=list)


class CVEsInput(ApexModel):
    packages: list[PackageRef] = Field(default_factory=list)
    allow_network: bool = Field(False, description="Permit OSV API lookup. Off by default.")
    local_index: Optional[str] = Field(None, description="Local advisory index root (bugbounty-intel/projects).")


class CVEsOutput(ApexModel):
    packages: list[PackageRef] = Field(default_factory=list)
    advisories: list[Advisory] = Field(default_factory=list)
    source: str = "local"
    network_used: bool = False
    errors: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

"""Phase 3 — Verify Divergence: model vs implementation."""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from schemas.common import ApexModel, Confidence


class Surface(ApexModel):
    file: str
    line: int
    name: str
    kind: str = "function"
    language: str = "unknown"
    entry: bool = False
    extractor: str = "regex"


class Divergence(ApexModel):
    id: str
    kind: str
    expected: str
    observed: str
    flow_id: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None
    confidence: Confidence = Confidence.LOW
    status: str = "candidate"
    source_tool: str = ""
    evidence: list[str] = Field(default_factory=list)


class ASTMapInput(ApexModel):
    paths: list[str] = Field(default_factory=list, description="Source paths to map. Empty = scope repos / workspace.")
    languages: list[str] = Field(default_factory=list)
    model_flows: list[str] = Field(default_factory=list, description="Optional flow-id filter.")
    max_files: int = Field(5000, ge=1, le=50000)


class ASTMapOutput(ApexModel):
    surfaces: list[Surface] = Field(default_factory=list)
    mapped_flows: dict[str, list[str]] = Field(default_factory=dict)
    divergences: list[Divergence] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    method: str = "regex"
    files_scanned: int = 0
    notes: list[str] = Field(default_factory=list)


class ToolRun(ApexModel):
    tool: str
    status: str
    command: list[str] = Field(default_factory=list)
    returncode: Optional[int] = None
    findings: int = 0
    log_path: Optional[str] = None
    reason: Optional[str] = None


class StaticSweepInput(ApexModel):
    paths: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list, description="Subset of adapter tools. Empty = all applicable.")
    timeout_seconds: int = Field(300, ge=10, le=3600)
    semgrep_config: Optional[str] = Field(None, description="Local Semgrep config or registry pack. Required to run Semgrep.")
    max_findings: int = Field(200, ge=1, le=5000)


class StaticSweepOutput(ApexModel):
    runs: list[ToolRun] = Field(default_factory=list)
    divergences: list[Divergence] = Field(default_factory=list)
    findings_total: int = 0
    notes: list[str] = Field(default_factory=list)


class PredictionDiffInput(ApexModel):
    flow_id: str
    verdict: str = Field(
        ...,
        description="model-wrong | design-wrong | design-choice. design-wrong becomes a high-priority divergence.",
    )
    expected: str
    observed: str
    why: str = ""
    file: Optional[str] = None
    line: Optional[int] = None
    confidence: Confidence = Confidence.MEDIUM


class PredictionDiffOutput(ApexModel):
    flow_id: str
    verdict: str
    divergences: list[Divergence] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class InventoryInput(ApexModel):
    rule_name: str = Field(..., description="Stable name, e.g. balance-of-self.")
    pattern: str = Field(..., description="Regular expression to search for.")
    paths: list[str] = Field(default_factory=list)
    extensions: list[str] = Field(default_factory=list)
    case_sensitive: bool = True
    max_files: int = Field(5000, ge=1, le=50000)


class InventoryHit(ApexModel):
    file: str
    line: int
    expression: str


class InventoryResult(ApexModel):
    rule: str
    total: int = 0
    new: int = 0
    removed: int = 0
    moved: int = 0
    unchanged: int = 0
    baseline_path: Optional[str] = None
    hits: list[InventoryHit] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class InventoryBatch(ApexModel):
    items: list[InventoryResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

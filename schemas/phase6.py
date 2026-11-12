"""Phase 6 — Validate & Report."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field

from schemas.common import ApexModel, Impact, Reachability, Trigger


class CheckResult(str, Enum):
    BLOCKS = "blocks"
    ALLOWS = "allows"
    UNKNOWN = "unknown"


class DisproofCheck(ApexModel):
    name: str
    question: str
    result: CheckResult = CheckResult.UNKNOWN
    evidence: str = ""


class DisproveInput(ApexModel):
    hypothesis_id: str = Field(..., description="Required. A valid H-* id from Phase 4.")
    checks: list[DisproofCheck] = Field(default_factory=list)
    notes: Optional[str] = None


class Disproof(ApexModel):
    id: str
    hypothesis_id: str
    verdict: str
    blocking_checks: list[str] = Field(default_factory=list)
    allowing_checks: list[str] = Field(default_factory=list)
    unknown_checks: list[str] = Field(default_factory=list)
    rationale: str = ""


class DisproofBatch(ApexModel):
    items: list[Disproof] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ReportInput(ApexModel):
    title: Optional[str] = None
    author: Optional[str] = None
    include_theoretical: bool = Field(False, description="Include hypotheses that were not verified.")
    mirror_earned: Optional[str] = Field(None, description="What was actually proved.")
    mirror_faked: Optional[str] = Field(None, description="Where the analysis hand-waved.")
    mirror_next: Optional[str] = Field(None, description="One concrete fix for the next run.")
    mirror_brag_or_regret: Optional[str] = None


class ReportOutput(ApexModel):
    markdown: str
    summary: dict[str, int] = Field(default_factory=dict)
    report_path: Optional[str] = None


class CitationCheckInput(ApexModel):
    phases: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])
    include_markdown: bool = False


class CitationIssue(ApexModel):
    cite: str
    reason: str


class CitationCheckOutput(ApexModel):
    checked: int = 0
    valid: int = 0
    invalid: int = 0
    details: list[CitationIssue] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ClassificationInput(ApexModel):
    hypothesis_id: str
    impact: Impact
    trigger: Trigger
    reachability: Reachability = Reachability.UNVERIFIED
    human_approved: bool = False
    reason: str = ""
    poc: str = ""


class Classification(ApexModel):
    id: str
    hypothesis_id: str
    impact: str
    trigger: str
    reachability: str
    severity: str
    proof_tier: str
    human_approved: bool = False
    requires_approval: bool = False
    reason: str = ""
    poc: str = ""


class ClassificationBatch(ApexModel):
    items: list[Classification] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class GapRef(ApexModel):
    id: str
    type: str = Field(..., description="docs | model | surface | hypothesis | disproof | sink")
    description: str
    next_phase: int = 3
    next_tool: str = ""
    flow_id: Optional[str] = None
    file: Optional[str] = None
    sink: Optional[str] = None
    ev_rank: int = 0


class CoverageInput(ApexModel):
    include_excluded: bool = True
    max_gaps: int = Field(50, ge=1, le=1000)


class CoverageOutput(ApexModel):
    summary: dict[str, int] = Field(default_factory=dict)
    ratio: float = 0.0
    confidence: str = "lower-bound"
    gaps: list[GapRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class StartRoundInput(ApexModel):
    gaps: list[GapRef] = Field(default_factory=list)
    max_gaps: int = Field(3, ge=1, le=20)
    notes: Optional[str] = None


class RoundRecord(ApexModel):
    round: int
    status: str = "open"
    gaps_selected: list[GapRef] = Field(default_factory=list)
    started_at: str = ""
    closed_at: Optional[str] = None
    outcome: Optional[str] = None
    tools_run: list[str] = Field(default_factory=list)
    new_divergences: int = 0
    new_hypotheses: int = 0
    new_experiments: int = 0
    closed_gaps: int = 0
    remaining_gaps: list[GapRef] = Field(default_factory=list)
    stop_reason: Optional[str] = None
    notes: list[str] = Field(default_factory=list)


class CloseRoundInput(ApexModel):
    round: int
    outcome: str = Field("progress", description="progress | stalled | exhausted")
    tools_run: list[str] = Field(default_factory=list)
    new_divergences: int = 0
    new_hypotheses: int = 0
    new_experiments: int = 0
    closed_gaps: int = 0
    remaining_gaps: list[GapRef] = Field(default_factory=list)
    stop_reason: Optional[str] = None
    notes: Optional[str] = None


class CloseSessionInput(ApexModel):
    status: str = Field("paused", description="paused | stalled | completed")
    resume_state: str
    backlog: list[str] = Field(default_factory=list)
    lessons: list[str] = Field(default_factory=list)
    remaining_gaps: list[GapRef] = Field(default_factory=list)


class CloseSessionOutput(ApexModel):
    death_note_path: str
    backlog_path: str
    status: str


class IssueInput(ApexModel):
    """Feedback from the agent about the pipeline itself.

    Examples: a tool was confusing, a needed analyser was not installed, a
    schema field did not fit, or a phase gate blocked a legitimate workflow.
    """

    kind: str = Field(
        "tool_friction",
        description="tool_friction | missing_tool | missing_capability | bug | doc_gap | environment",
    )
    title: str
    description: str
    tool: Optional[str] = None
    phase_attempted: Optional[int] = None
    severity: str = Field("medium", description="low | medium | high | blocker")
    attempted: Optional[str] = None
    workaround: Optional[str] = None
    requested_change: Optional[str] = None
    evidence: list[str] = Field(default_factory=list)
    reporter: str = "agent"


class IssueEntry(IssueInput):
    id: str
    created_at: str = ""


class IssueBatch(ApexModel):
    items: list[IssueEntry] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

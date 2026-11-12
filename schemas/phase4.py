"""Phase 4 — Specialist Analysis: divergence-anchored hypotheses."""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from schemas.common import ApexModel, Confidence


class HypothesisInput(ApexModel):
    divergence_id: str = Field(..., description="Required. A valid DIV-* id from Phase 3.")
    focus: Optional[str] = Field(None, description="What to examine. Supplied by the analyst when no code hit is obvious.")
    files: list[str] = Field(default_factory=list)
    hint: Optional[str] = None


class DimensionalInput(HypothesisInput):
    metric_hints: list[str] = Field(default_factory=list)


class ReverseInput(HypothesisInput):
    artifact_paths: list[str] = Field(default_factory=list)


class StateMachineInput(HypothesisInput):
    target_states: list[str] = Field(default_factory=list)


class TrustBoundaryInput(HypothesisInput):
    boundaries: list[str] = Field(default_factory=list)


class Hypothesis(ApexModel):
    id: str
    divergence_id: str
    lens: str
    statement: str
    falsifiable_prediction: str
    sink: str = ""
    title: Optional[str] = Field(None, description="Non-technical report title.")
    summary: Optional[str] = Field(None, description="One non-technical sentence for the report.")
    impact_statement: Optional[str] = Field(None, description="One non-technical impact sentence.")
    remediation: Optional[str] = Field(None, description="Recommended fix, in plain language.")
    preconditions: list[str] = Field(default_factory=list)
    experiment_plan: str = ""
    confidence: Confidence = Confidence.LOW
    status: str = "open"
    trusted_actor: bool = Field(False, description="True if the path needs an admin/keeper/operator action.")
    evidence: list[str] = Field(default_factory=list)


class HypothesisBatch(ApexModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class Assumption(ApexModel):
    """A load-bearing belief the code silently makes."""

    id: str
    assumption_class: str = Field(
        ...,
        description="TRUST | ACCOUNTING | ORDER_TIMING | ECONOMIC | ORACLE_DATA | "
        "PRIVACY | LIVENESS | IDENTITY | UPGRADE | SPEC",
    )
    statement: str
    where: Optional[str] = None
    violator: str = ""
    primitive: str = ""
    cost: str = ""
    status: str = "OPEN"
    trusted_actor: bool = False
    docs_claim: Optional[str] = None


class AssumptionInput(ApexModel):
    assumptions: list[Assumption] = Field(default_factory=list)
    notes: Optional[str] = None


class AssumptionBatch(ApexModel):
    items: list[Assumption] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BatteryCheck(ApexModel):
    name: str
    outcome: str = Field("inconclusive", description="fired | not_triggered | inconclusive")
    evidence: str = ""
    note: str = ""


class BatteryInput(ApexModel):
    battery: str = Field(..., description="vault | lifecycle | boundary")
    trigger: str
    checks: list[BatteryCheck] = Field(default_factory=list)
    notes: Optional[str] = None


class BatteryResult(ApexModel):
    id: str
    battery: str
    trigger: str
    outcome: str
    checks: list[BatteryCheck] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BatteryBatch(ApexModel):
    items: list[BatteryResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ChainNode(ApexModel):
    hypothesis_id: str
    pre_fact: str = Field(..., description="state_variable:condition")
    post_fact: str = Field(..., description="state_variable:condition")
    satisfies: list[str] = Field(default_factory=list)


class ChainEdge(ApexModel):
    source: str = Field(..., description="hypothesis id that produces the state")
    target: str = Field(..., description="hypothesis id that consumes the state")
    via: str = Field(..., description="the target's pre_fact that the source satisfies")
    falsifier: str = Field(..., description="what would break the state hand-off")
    cite: str = Field(..., description="path:line where the falsifier lives")
    satisfies_cite: str = Field(..., description="path:line where target reads the state")


class ChainSpec(ApexModel):
    id: str
    order: list[str] = Field(default_factory=list)
    edges: list[ChainEdge] = Field(default_factory=list)
    sink_id: str


class ChainInput(ApexModel):
    nodes: list[ChainNode] = Field(default_factory=list)
    chains: list[ChainSpec] = Field(default_factory=list)
    notes: Optional[str] = None


class ChainBatch(ApexModel):
    items: list[ChainSpec] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

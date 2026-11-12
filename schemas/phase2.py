"""Phase 2 — Model: actors, flows, state, invariants."""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from schemas.common import ApexModel


class Actor(ApexModel):
    id: str
    name: str
    privileges: list[str] = Field(default_factory=list)


class Flow(ApexModel):
    id: str
    name: str
    actor: str
    entry: str = Field(..., description="Expected entrypoint: route, function signature, RPC, message, or binary path.")
    description: str = ""
    states: list[str] = Field(default_factory=list)
    transitions: list[str] = Field(default_factory=list)
    value_sinks: list[str] = Field(default_factory=list)
    trust_boundaries: list[str] = Field(default_factory=list)
    critical: bool = False


class MapFlowsInput(ApexModel):
    actors: list[Actor] = Field(default_factory=list)
    flows: list[Flow] = Field(default_factory=list)
    state_variables: list[str] = Field(default_factory=list)
    entrypoints: list[str] = Field(default_factory=list)


class MapFlowsOutput(ApexModel):
    actors: list[Actor] = Field(default_factory=list)
    flows: list[Flow] = Field(default_factory=list)
    state_variables: list[str] = Field(default_factory=list)
    entrypoints: list[str] = Field(default_factory=list)
    critical_flows: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class Invariant(ApexModel):
    id: str
    statement: str
    category: str = Field("security", description="math | economic | authorization | state | security")
    source: Optional[str] = None
    applies_to: list[str] = Field(default_factory=list)
    falsifiable: bool = True


class DefineInvariantsInput(ApexModel):
    invariants: list[Invariant] = Field(default_factory=list)
    source_notes: Optional[str] = None


class DefineInvariantsOutput(ApexModel):
    invariants: list[Invariant] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StateVariable(ApexModel):
    """Something the system remembers between steps."""

    var: str = Field(..., description="Code identifier, e.g. orders.total")
    file: Optional[str] = Field(None, description="path:line where it lives")
    kind: str = "mutable"
    note: Optional[str] = None


class StateVocabInput(ApexModel):
    states: list[StateVariable] = Field(default_factory=list)
    notes: Optional[str] = None


class StateVocabOutput(ApexModel):
    states: list[StateVariable] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SinkDef(ApexModel):
    """Where an attacker wants to end up."""

    id: str
    var: Optional[str] = None
    vars: list[str] = Field(default_factory=list)
    expr: Optional[str] = Field(None, description="Required when vars has more than one entry.")
    note: Optional[str] = None


class SinksInput(ApexModel):
    sinks: list[SinkDef] = Field(default_factory=list)
    notes: Optional[str] = None


class SinksOutput(ApexModel):
    sinks: list[SinkDef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SkeletonInput(ApexModel):
    flow_id: str
    paths: list[str] = Field(default_factory=list)
    max_surfaces: int = Field(300, ge=1, le=3000)


class Signature(ApexModel):
    file: str
    line: int
    name: str
    language: str = "unknown"


class SkeletonOutput(ApexModel):
    flow_id: str
    skeleton_path: str
    signatures: list[Signature] = Field(default_factory=list)
    note: str = (
        "Skeleton only. Bodies are omitted on purpose; write the prediction before reading implementation."
    )


class PredictionInput(ApexModel):
    flow_id: str
    provenance: str = Field(..., description="What had been read when this prediction was written.")
    expected: str = Field(..., description="What this flow is supposed to do, in plain English.")
    inputs: str = Field("", description="Expected inputs and validations.")
    state_changes: str = Field("", description="Expected state writes and reads.")
    failure_behavior: str = Field("", description="Expected behaviour when a check fails.")
    surprises: list[str] = Field(..., min_length=2, description="At least two things that would prove me wrong.")
    boundary_semantics: str = Field(
        ..., description="Inclusive or exclusive at snapshot/window boundaries, and what happens on the boundary."
    )
    skeleton_path: Optional[str] = None


class PredictionRecord(PredictionInput):
    created_at: str = ""
    prediction_path: Optional[str] = None


class PredictionOutput(ApexModel):
    flow_id: str
    prediction_path: str
    prediction: PredictionRecord

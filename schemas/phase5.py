"""Phase 5 — Experiment: sandbox provisioning and invariant testing."""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from schemas.common import ApexModel


class SandboxInput(ApexModel):
    service: str = Field("target", description="Sandbox name / service under test.")
    out_dir: Optional[str] = Field(None, description="Override output dir. Default .apex/sandbox/<service>.")
    base_image: Optional[str] = None
    ports: list[str] = Field(default_factory=list)


class SandboxOutput(ApexModel):
    directory: str
    files: list[str] = Field(default_factory=list)
    profile: str = "unknown"
    kind: str = "generic"
    instructions: str = ""
    notes: list[str] = Field(default_factory=list)


class Experiment(ApexModel):
    id: str
    hypothesis_id: str
    kind: str = "invariant_test"
    status: str = "prepared"
    command: Optional[str] = None
    artifact: Optional[str] = None
    returncode: Optional[int] = None
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    observation: str = ""
    verdict: str = "pending"
    experiment_class: str = Field(
        "unknown",
        description="distinguishing | happy-path | code-fact | unknown. Only distinguishing can confirm or refute.",
    )


class ExperimentBatch(ApexModel):
    items: list[Experiment] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class InvariantTestInput(ApexModel):
    hypothesis_id: str = Field(..., description="Required. A valid H-* id from Phase 4.")
    test_code: Optional[str] = Field(None, description="Test source to write into the sandbox.")
    command: Optional[str] = Field(None, description="Command to run when execute=true.")
    execute: bool = Field(False, description="Actually run the command. Default false (dry-run).")
    timeout_seconds: int = Field(120, ge=5, le=3600)
    name: str = "invariant_test"
    experiment_class: str = Field(
        "distinguishing",
        description="Must be distinguishing for a G3 pass/kill. Happy-path and code-fact are not evidence.",
    )


class RecordExperimentInput(ApexModel):
    hypothesis_id: str
    command: str
    observation: str = ""
    verdict: str = "pending"
    output_path: Optional[str] = None
    experiment_class: str = Field(
        "",
        description="distinguishing | happy-path | code-fact | unknown. Confirmed/refuted require distinguishing.",
    )


class CartesianQueueInput(ApexModel):
    max_queue: int = Field(8, ge=1, le=50, description="How many top-ranked public pairs to materialize.")
    execute: bool = Field(
        False,
        description="Queue never executes. Distinguishing attacks are recorded separately.",
    )

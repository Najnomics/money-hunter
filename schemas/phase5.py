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


class RecordExperimentInput(ApexModel):
    hypothesis_id: str
    command: str
    observation: str = ""
    verdict: str = "pending"
    output_path: Optional[str] = None

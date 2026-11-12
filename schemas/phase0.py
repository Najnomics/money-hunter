"""Phase 0 — Ground Zero: scope, rules, boundaries."""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from schemas.common import ApexModel, TargetProfile


class ScopeInput(ApexModel):
    repos: list[str] = Field(default_factory=list, description="Repository / source directories to include in scope.")
    endpoints: list[str] = Field(default_factory=list, description="Service endpoints / hosts / base URLs.")
    addresses: list[str] = Field(default_factory=list, description="On-chain program/contract addresses or deployment IDs.")
    binaries: list[str] = Field(default_factory=list, description="Compiled artifacts (ELF, wasm, bytecode files).")
    profile: TargetProfile = Field(TargetProfile.UNKNOWN, description="TargetProfile; 'unknown' auto-detects.")
    notes: Optional[str] = None
    max_files: int = Field(5000, ge=1, le=100000)


class Component(ApexModel):
    name: str
    kind: str = "repo"
    paths: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    manifests: list[str] = Field(default_factory=list)


class ScopeOutput(ApexModel):
    target_profile: TargetProfile
    components: list[Component] = Field(default_factory=list)
    allowlist: list[str] = Field(default_factory=list)
    detected_languages: dict[str, int] = Field(default_factory=dict)
    manifests: list[str] = Field(default_factory=list)
    file_count: int = 0
    profile_scores: dict[str, int] = Field(default_factory=dict)
    notes: Optional[str] = None


class InvariantRule(ApexModel):
    id: str
    statement: str
    category: str = "security"
    source: Optional[str] = None


class RulesInput(ApexModel):
    invariants: list[str] = Field(default_factory=list, description="Stated system invariants / guarantees.")
    policy_files: list[str] = Field(default_factory=list, description="Files containing policy, bounty, or severity rules.")
    bounty_url: Optional[str] = None
    severity_scale: dict[str, str] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)


class RulesOutput(ApexModel):
    invariants: list[InvariantRule] = Field(default_factory=list)
    policy: Optional[str] = None
    bounty: Optional[str] = None
    severity_scale: dict[str, str] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    extracted_claims: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BoundariesInput(ApexModel):
    out_of_scope: list[str] = Field(default_factory=list)
    rate_limits: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    non_destructive: bool = True
    allowed_environments: list[str] = Field(default_factory=lambda: ["local", "fork", "devnet", "sandbox"])
    notes: Optional[str] = None


class BoundariesOutput(ApexModel):
    out_of_scope: list[str] = Field(default_factory=list)
    rate_limits: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    non_destructive: bool = True
    allowed_environments: list[str] = Field(default_factory=list)
    hard_rules: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class EnvironmentCheck(ApexModel):
    """One readiness check: identity, tool, or fixture."""

    name: str
    kind: str = Field("tool", description="identity | tool | fixture")
    command: Optional[str] = None
    passed: bool = False
    evidence: str = ""


class EnvironmentInput(ApexModel):
    checks: list[EnvironmentCheck] = Field(default_factory=list)
    offline_limits: list[str] = Field(default_factory=list)
    reset_command: Optional[str] = None
    notes: Optional[str] = None


class EnvironmentOutput(ApexModel):
    ready: bool = False
    checks: list[EnvironmentCheck] = Field(default_factory=list)
    offline_limits: list[str] = Field(default_factory=list)
    reset_command: Optional[str] = None
    summary: str = ""
    notes: list[str] = Field(default_factory=list)

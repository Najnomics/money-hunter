"""Shared enums and base model configuration."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TargetProfile(str, Enum):
    UNKNOWN = "unknown"
    WEB2_API = "web2_api"
    EVM = "evm"
    SVM = "svm"
    MOVE = "move"
    NATIVE_BINARY = "native_binary"
    HYBRID = "hybrid"


class EvidenceLabel(str, Enum):
    FACT = "[FACT]"
    OBSERVED = "[OBSERVED]"
    SEARCHED = "[SEARCHED]"
    FUZZED = "[FUZZED]"
    CODE = "[CODE]"
    DEDUCED = "[DEDUCED]"
    ASSUMED = "[ASSUMED]"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Impact(str, Enum):
    """What the target loses if the bug is real."""

    TAKE = "T"                 # value/data can be taken or corrupted
    FREEZE_PERMANENT = "F+"    # permanent lock / unrecoverable state
    FREEZE_TEMPORARY = "F-"    # temporary freeze or degradation
    CORRECTNESS = "C"          # wrong answer, no direct loss


class Trigger(str, Enum):
    """Who can pull the trigger."""

    ANYONE = "A"               # anyone, any time
    CONDITIONAL = "K"          # anyone, but conditions must align
    ROLE_ACQUIRABLE = "R+"     # requires a role the attacker can obtain
    ROLE_NOT_ACQUIRABLE = "R-" # requires an unobtainable role


class Reachability(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


class ProofTier(str, Enum):
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    THEORETICAL = "theoretical"
    REJECTED = "rejected"


class GatePolicy(str, Enum):
    """How strict the campaign gates should be."""

    LIGHT = "light"        # the original seven-phase flow
    STANDARD = "standard"  # adds coverage + citation checks at the end
    STRICT = "strict"      # adds assumptions, vocab, sinks, predictions


class ApexModel(BaseModel):
    """Base model: tolerant to extra CLI keys, JSON-friendly enums."""

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    # Optional per-call target.  This is what lets one global MCP server serve
    # every project: the agent passes the target workspace alongside the tool
    # arguments instead of needing a new server entry per target.
    workspace: Optional[str] = Field(
        None,
        description="Target workspace for this call. Omit to use the server's --workspace default.",
    )

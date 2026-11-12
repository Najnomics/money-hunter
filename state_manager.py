"""Campaign state, phase gates, and artifact persistence.

The target workspace owns a ``.apex/`` directory. Every phase writes one
artifact (Phase 6 writes Markdown plus a metadata sidecar). A tool in phase N
may only run when phases 0..N-1 have complete artifacts.

Phase layout
------------
0  .apex/00_ground_zero.json      sections: scope, rules, boundaries
1  .apex/01_research.json         sections: docs, audits, intel, [cves]
2  .apex/02_mental_model.json     sections: flows, invariants
3  .apex/03_divergences.json      sections: ast_map, static_sweep
4  .apex/04_hypotheses.json       sections: dimensional, reverse_engineer,
                                            state_machine, trust_boundary
5  .apex/05_experiments.json      sections: sandbox, experiments[]
6  .apex/06_final_report.md       markdown + 06_report_meta.json
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from fsutil import now_iso, rel_to, write_text_atomic
from schemas.common import TargetProfile

SCHEMA_VERSION = "1.0"

PHASE_ARTIFACTS: dict[int, str] = {
    0: "00_ground_zero.json",
    1: "01_research.json",
    2: "02_mental_model.json",
    3: "03_divergences.json",
    4: "04_hypotheses.json",
    5: "05_experiments.json",
    6: "06_final_report.md",
}
PHASE6_META = "06_report_meta.json"


class StateError(Exception):
    """Base error for state / gate failures."""


class GateError(StateError):
    def __init__(self, phase: int, missing: list[str]):
        self.phase = phase
        self.missing = missing
        super().__init__(
            f"Phase {phase} is blocked: previous phase gate incomplete "
            f"({', '.join(missing) if missing else 'unknown'})"
        )


class ArtifactError(StateError):
    """An artifact exists but is malformed."""


@dataclass(frozen=True)
class GateSpec:
    required: tuple[str, ...] = ()
    required_any: tuple[str, ...] = ()
    require_file: bool = False


GATES: dict[int, GateSpec] = {
    0: GateSpec(required=("scope", "rules", "boundaries")),
    1: GateSpec(required=("docs", "audits", "intel")),
    2: GateSpec(required=("flows", "invariants")),
    3: GateSpec(required=("ast_map", "static_sweep")),
    4: GateSpec(required_any=("dimensional", "reverse_engineer", "state_machine", "trust_boundary")),
    5: GateSpec(required=("sandbox", "experiments")),
    6: GateSpec(required=("report",), require_file=True),
}


class StateManager:
    def __init__(self, workspace: Path | str, state_dir: str = ".apex"):
        self.workspace = Path(workspace).expanduser().resolve()
        self.state_dir_name = state_dir
        self.apex_dir = (self.workspace / state_dir).resolve()

    # ------------------------------------------------------------------ setup
    def ensure(self) -> Path:
        self.apex_dir.mkdir(parents=True, exist_ok=True)
        return self.apex_dir

    @property
    def config_path(self) -> Path:
        return self.apex_dir / "config.json"

    @property
    def tool_log_path(self) -> Path:
        return self.apex_dir / "tool-runs.jsonl"

    def artifact_path(self, phase: int) -> Path:
        if phase not in PHASE_ARTIFACTS:
            raise StateError(f"unknown phase {phase}")
        return self.apex_dir / PHASE_ARTIFACTS[phase]

    def _meta_path(self, phase: int) -> Path:
        return self.apex_dir / PHASE6_META if phase == 6 else self.artifact_path(phase)

    def artifact_relpath(self, phase: int) -> str:
        return rel_to(self.artifact_path(phase), self.workspace)

    def meta_relpath(self, phase: int) -> str:
        """Path to the JSON metadata file (for phase 6 this is not the Markdown report)."""
        return rel_to(self._meta_path(phase), self.workspace)

    # --------------------------------------------------------------- config
    def read_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def update_config(self, **values: Any) -> dict[str, Any]:
        self.ensure()
        cfg = self.read_config()
        cfg.update({k: v for k, v in values.items() if v is not None})
        cfg.setdefault("created_at", now_iso())
        cfg["updated_at"] = now_iso()
        write_text_atomic(self.config_path, json.dumps(cfg, indent=2, sort_keys=True))
        # Keep the phase-0 envelope's profile in sync.
        if "target_profile" in cfg:
            env = self._load_envelope(0, create=False)
            if env is not None:
                env["target_profile"] = cfg["target_profile"]
                env["updated_at"] = now_iso()
                self._save_envelope(0, env)
        return cfg

    @property
    def target_profile(self) -> TargetProfile:
        raw = self.read_config().get("target_profile")
        if not raw:
            env = self._load_envelope(0, create=False)
            raw = (env or {}).get("target_profile")
        try:
            return TargetProfile(raw or TargetProfile.UNKNOWN.value)
        except ValueError:
            return TargetProfile.UNKNOWN

    # Gates can be light/standard/strict.  The policy is stored in
    # .apex/config.json so every future tool call sees the same contract.
    @property
    def gate_policy(self) -> str:
        raw = str(self.read_config().get("gate_policy", "standard")).lower()
        return raw if raw in {"light", "standard", "strict"} else "standard"

    def set_gate_policy(self, policy: str) -> None:
        if policy not in {"light", "standard", "strict"}:
            raise StateError("gate policy must be light, standard, or strict")
        self.update_config(gate_policy=policy)

    # ------------------------------------------------------------ envelopes
    def _new_envelope(self, phase: int) -> dict[str, Any]:
        ts = now_iso()
        return {
            "schema_version": SCHEMA_VERSION,
            "phase": phase,
            "artifact": PHASE_ARTIFACTS[phase],
            "target_profile": self.target_profile.value,
            "created_at": ts,
            "updated_at": ts,
            "status": "in_progress",
            "sections": {},
            "tool_runs": [],
        }

    def _load_envelope(self, phase: int, create: bool = True) -> Optional[dict[str, Any]]:
        path = self._meta_path(phase)
        if not path.exists():
            return self._new_envelope(phase) if create else None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ArtifactError(f"{path.name} is not valid JSON: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("sections"), dict):
            raise ArtifactError(f"{path.name} is not an Apex artifact envelope")
        data.setdefault("schema_version", SCHEMA_VERSION)
        data.setdefault("phase", phase)
        data.setdefault("tool_runs", [])
        return data

    def _save_envelope(self, phase: int, envelope: dict[str, Any]) -> Path:
        self.ensure()
        envelope["updated_at"] = now_iso()
        envelope["target_profile"] = self.target_profile.value
        envelope["status"] = "in_progress"
        path = self._meta_path(phase)
        write_text_atomic(path, json.dumps(envelope, indent=2, sort_keys=True))
        # Recompute against the artifact now on disk so the stored status is accurate.
        status = "complete" if self._gate_ok(phase) else "in_progress"
        if envelope.get("status") != status:
            envelope["status"] = status
            write_text_atomic(path, json.dumps(envelope, indent=2, sort_keys=True))
        return path

    # --------------------------------------------------------------- reading
    def load(self, phase: int) -> Optional[dict[str, Any]]:
        return self._load_envelope(phase, create=False)

    def sections(self, phase: int) -> dict[str, Any]:
        env = self._load_envelope(phase, create=False)
        return (env or {}).get("sections", {}) or {}

    def section(self, phase: int, name: str) -> Any:
        return self.sections(phase).get(name)

    # --------------------------------------------------------------- writing
    @staticmethod
    def _merge_payload(phase: int, section: str, previous: Any, payload: Any) -> Any:
        """Merge repeatable sections instead of silently replacing old work."""
        if (
            phase == 2
            and section in {"predictions", "skeletons"}
            and isinstance(payload, dict)
            and isinstance(payload.get("flow_id"), str)
        ):
            base = previous if isinstance(previous, dict) else {}
            return {**base, payload["flow_id"]: payload}
        if not isinstance(previous, dict) or not isinstance(payload, dict):
            return payload
        merged = dict(payload)
        merge_lists = {
            (3, "prediction_diff"): ("divergences",),
            (4, "dimensional"): ("hypotheses",),
            (4, "reverse_engineer"): ("hypotheses",),
            (4, "state_machine"): ("hypotheses",),
            (4, "trust_boundary"): ("hypotheses",),
        }.get((phase, section), ())
        for key in merge_lists:
            old_items = previous.get(key)
            new_items = payload.get(key)
            if isinstance(old_items, list) and isinstance(new_items, list):
                by_id: dict[str, Any] = {}
                for item in old_items + new_items:
                    if isinstance(item, dict):
                        by_id[str(item.get("id") or len(by_id))] = item
                    else:
                        by_id[str(len(by_id))] = item
                merged[key] = list(by_id.values())
        if phase == 2 and section in {"predictions", "skeletons"}:
            # These sections are keyed by flow id, not by section name.
            if isinstance(payload.get("flow_id"), str):
                return {**previous, payload["flow_id"]: payload}
            return {**previous, **payload}
        return merged

    def write_section(
        self,
        phase: int,
        section: str,
        payload: Any,
        tool: str = "",
    ) -> Path:
        env = self._load_envelope(phase, create=True)
        assert env is not None
        previous = env["sections"].get(section)
        payload = self._merge_payload(phase, section, previous, payload)
        env["sections"][section] = payload
        if tool:
            env["tool_runs"].append({"tool": tool, "at": now_iso(), "section": section})
            env["tool_runs"] = env["tool_runs"][-100:]
        path = self._save_envelope(phase, env)
        self._log_tool(tool, phase, section, "ok")
        return path

    def append_items(
        self,
        phase: int,
        section: str,
        items: Iterable[dict[str, Any]],
        tool: str = "",
    ) -> Path:
        env = self._load_envelope(phase, create=True)
        assert env is not None
        existing = env["sections"].get(section)
        if existing is None:
            existing = []
        if not isinstance(existing, list):
            raise ArtifactError(f"section {section!r} in phase {phase} is not a list")
        known_ids = {item.get("id") for item in existing if isinstance(item, dict)}
        for item in items:
            if not isinstance(item, dict):
                raise ArtifactError("append_items expects dictionaries")
            item_id = item.get("id")
            if item_id and item_id in known_ids:
                raise ArtifactError(f"duplicate id {item_id!r} in section {section!r}")
            existing.append(item)
            if item_id:
                known_ids.add(item_id)
        env["sections"][section] = existing
        if tool:
            env["tool_runs"].append({"tool": tool, "at": now_iso(), "section": section})
            env["tool_runs"] = env["tool_runs"][-100:]
        path = self._save_envelope(phase, env)
        self._log_tool(tool, phase, section, "ok")
        return path

    def write_report(self, markdown: str) -> Path:
        self.ensure()
        path = self.artifact_path(6)
        write_text_atomic(path, markdown)
        return path

    def read_report(self) -> str:
        path = self.artifact_path(6)
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _log_tool(self, tool: str, phase: int, section: str, outcome: str) -> None:
        if not tool:
            return
        self.ensure()
        row = {
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "tool": tool,
            "phase": phase,
            "section": section,
            "outcome": outcome,
        }
        with self.tool_log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")

    # ----------------------------------------------------------------- gates
    def _gate_ok(self, phase: int) -> bool:
        return self.gate_status(phase)["ok"]

    def gate_status(self, phase: int) -> dict[str, Any]:
        if phase not in GATES:
            return {"phase": phase, "ok": False, "missing": ["unknown phase"]}
        spec = GATES[phase]
        missing: list[str] = []

        if spec.require_file and not self.artifact_path(phase).exists():
            missing.append(PHASE_ARTIFACTS[phase])

        sections = self.sections(phase)
        for name in spec.required:
            value = sections.get(name)
            if value in (None, {}, [], ""):
                missing.append(f"section:{name}")

        if spec.required_any:
            present = [n for n in spec.required_any if sections.get(n) not in (None, {}, [])]
            if not present:
                missing.append("one-of:" + ",".join(spec.required_any))

        # Phase-specific completeness: a section existing is not enough.
        if phase == 4:
            if not self.collect(4, "hypotheses"):
                missing.append("hypotheses:non-empty")
        if phase == 5:
            if not self.collect(5, "experiments"):
                missing.append("experiments:non-empty")

        self._policy_extra(phase, sections, missing)
        return {"phase": phase, "ok": not missing, "missing": missing}

    def _policy_extra(self, phase: int, sections: dict[str, Any], missing: list[str]) -> None:
        """Add the checks that depend on the light/standard/strict policy."""
        rank = {"light": 0, "standard": 1, "strict": 2}[self.gate_policy]

        def need(section: str, label: str | None = None) -> None:
            if sections.get(section) in (None, {}, [], ""):
                missing.append(label or f"section:{section}")

        if rank >= 1 and phase == 6:
            need("coverage")
            need("citations")
            citations = sections.get("citations") or {}
            if isinstance(citations, dict) and int(citations.get("invalid", 0)) > 0:
                missing.append(f"citations:invalid={citations['invalid']}")

        if rank >= 2:
            if phase == 0:
                need("environment")
            if phase == 2:
                need("state_vocab")
                need("sinks")
            if phase == 3:
                flows = (self.section(2, "flows") or {}).get("flows", [])
                predictions = self.section(2, "predictions") or {}
                unplanned = [
                    flow.get("id") for flow in flows
                    if flow.get("critical") and flow.get("id") not in predictions
                ]
                if unplanned:
                    missing.append("predictions:missing=" + ",".join(map(str, unplanned)))
            if phase == 4:
                need("assumptions")
                assumptions = self.collect(4, "assumptions")
                if len(assumptions) < 4:
                    missing.append("assumptions:min=4")
            if phase == 6:
                confirmed = [
                    exp for exp in self.collect(5, "experiments")
                    if exp.get("status") == "ran" and exp.get("verdict") == "confirmed"
                ]
                classifications = self.collect(6, "classifications")
                classified = {
                    str(row.get("hypothesis_id")) for row in classifications
                    if isinstance(row, dict)
                }
                unclassified = sorted({
                    str(exp.get("hypothesis_id")) for exp in confirmed
                } - classified)
                if unclassified:
                    missing.append("classifications:missing=" + ",".join(unclassified))

    def require_gate(self, phase: int) -> None:
        """Raise GateError unless every earlier phase gate is complete."""
        if phase == 0:
            return
        for prior in range(0, phase):
            status = self.gate_status(prior)
            if not status["ok"]:
                raise GateError(prior, status["missing"])

    def phase_states(self) -> list[dict[str, Any]]:
        return [self.gate_status(p) for p in range(0, 7)]

    # ------------------------------------------------------------- id lookup
    @staticmethod
    def _walk(obj: Any):
        if isinstance(obj, dict):
            yield obj
            for value in obj.values():
                yield from StateManager._walk(value)
        elif isinstance(obj, list):
            for value in obj:
                yield from StateManager._walk(value)

    def find_id(self, phase: int, obj_id: str) -> Optional[dict[str, Any]]:
        for obj in self._walk(self.sections(phase)):
            if obj.get("id") == obj_id:
                return obj
        return None

    def find_divergence(self, divergence_id: str) -> Optional[dict[str, Any]]:
        return self.find_id(3, divergence_id)

    def find_hypothesis(self, hypothesis_id: str) -> Optional[dict[str, Any]]:
        return self.find_id(4, hypothesis_id)

    def collect(self, phase: int, key: str) -> list[dict[str, Any]]:
        """Collect every list found under ``key`` anywhere in a phase artifact."""
        results: list[dict[str, Any]] = []
        seen: set[str] = set()

        def walk(obj: Any):
            if isinstance(obj, dict):
                for k, value in obj.items():
                    if k == key and isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                marker = json.dumps(item, sort_keys=True, default=str)
                                if marker not in seen:
                                    seen.add(marker)
                                    results.append(item)
                    else:
                        walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)

        walk(self.sections(phase))
        return results

    def divergences(self) -> list[dict[str, Any]]:
        return self.collect(3, "divergences")

    def hypotheses(self) -> list[dict[str, Any]]:
        return self.collect(4, "hypotheses")

    def experiments(self) -> list[dict[str, Any]]:
        return self.collect(5, "experiments")

    def disproofs(self) -> list[dict[str, Any]]:
        return self.collect(6, "disproofs")

    # ----------------------------------------------------------------- rounds
    @property
    def rounds_dir(self) -> Path:
        return self.apex_dir / "rounds"

    def round_records(self) -> list[dict[str, Any]]:
        if not self.rounds_dir.is_dir():
            return []
        records: list[dict[str, Any]] = []
        for path in sorted(self.rounds_dir.glob("round-*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                records.append(data)
        return records

    def next_round_number(self) -> int:
        highest = 0
        for record in self.round_records():
            try:
                highest = max(highest, int(record.get("round", 0)))
            except (TypeError, ValueError):
                pass
        return highest + 1

    def write_round(self, record: dict[str, Any]) -> Path:
        self.rounds_dir.mkdir(parents=True, exist_ok=True)
        number = int(record["round"])
        path = self.rounds_dir / f"round-{number}.json"
        write_text_atomic(path, json.dumps(record, indent=2, sort_keys=True))
        return path

    # ---------------------------------------------------------------- status
    def snapshot(self) -> dict[str, Any]:
        return {
            "workspace": str(self.workspace),
            "apex_dir": str(self.apex_dir),
            "target_profile": self.target_profile.value,
            "gate_policy": self.gate_policy,
            "rounds": len(self.round_records()),
            "phases": self.phase_states(),
            "counts": {
                "divergences": len(self.divergences()),
                "hypotheses": len(self.hypotheses()),
                "experiments": len(self.experiments()),
                "disproofs": len(self.disproofs()),
                "assumptions": len(self.collect(4, "assumptions")),
                "chains": len(self.collect(4, "chains")),
            },
        }

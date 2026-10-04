from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class Quality(StrEnum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTING = "CONFLICTING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class QualityState(Contract):
    accuracy: Quality
    completeness: Quality
    freshness: Quality


class Observation(Contract):
    observation_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    field_key: str = Field(min_length=1)
    value: str | bool | int | float | None
    kind: Literal["OBSERVED", "DERIVED", "INFERRED", "MANUAL"]
    event_time_ms: int = Field(ge=0, strict=True)
    received_at: datetime
    game_clock_basis: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    source_location: str = Field(min_length=1)
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    lineage_ids: tuple[str, ...]
    independent_group_id: str = Field(min_length=1)
    perspective: Literal["PLAYER", "OBSERVER", "UNKNOWN"]
    visibility_at_event: Literal["KNOWN", "UNKNOWN", "NOT_VISIBLE"]
    patch: str = Field(min_length=1)
    quality_state: QualityState
    validity: Literal["AT_EVENT", "HISTORICAL_FACT"]
    formula: str | None = None
    formula_version: str | None = None
    hypothesis: str | None = None
    conditions: tuple[str, ...] = ()
    counterevidence: tuple[str, ...] = ()
    author: str | None = None
    missing_reason: str | None = None

    @field_validator("received_at")
    @classmethod
    def aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("received_at must include timezone")
        return value

    @field_validator("value")
    @classmethod
    def finite(cls, value):
        import math
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite value")
        return value

    @model_validator(mode="after")
    def provenance(self):
        if self.kind == "DERIVED" and not (self.lineage_ids and self.formula and self.formula_version):
            raise ValueError("derived observation requires lineage and formula version")
        if self.kind == "INFERRED" and not self.hypothesis:
            raise ValueError("inference requires hypothesis")
        if self.kind == "MANUAL" and not self.author:
            raise ValueError("manual observation requires author")
        if self.value is None and not self.missing_reason:
            raise ValueError("null requires missing_reason")
        if self.validity == "HISTORICAL_FACT" and not self.field_key.endswith((".last_seen", ".cast_event", ".event")):
            raise ValueError("historical fact must use explicit event/last_seen field")
        if self.observation_id in self.lineage_ids:
            raise ValueError("self lineage")
        return self

    @property
    def key(self):
        return f"{self.entity_id}:{self.field_key}"


class SnapshotRequest(Contract):
    session_id: str = Field(min_length=1)
    patch: str = Field(min_length=1)
    as_of_event_time_ms: int = Field(ge=0, strict=True)
    knowledge_cutoff: datetime
    game_clock_basis: str = Field(min_length=1)
    view: Literal["PLAYER_REVIEW", "RECEIVED_AS_OF"]
    required_keys: tuple[str, ...]
    revision_parent: str | None = None

    @field_validator("knowledge_cutoff")
    @classmethod
    def aware(cls, value):
        return Observation.aware(value)


class FieldState(Contract):
    key: str
    value: str | bool | int | float | None
    state: Literal["KNOWN", "UNKNOWN", "CONDITIONAL", "CONFLICTING", "STALE"]
    evidence_refs: tuple[str, ...]
    reasons: tuple[str, ...]
    independent_groups: tuple[str, ...]


class Snapshot(Contract):
    snapshot_id: str
    request: SnapshotRequest
    schema_version: Literal["r3.v1"] = "r3.v1"
    reducer_version: Literal["r3.v1"] = "r3.v1"
    fields: tuple[FieldState, ...]
    observation_hashes: tuple[tuple[str, str], ...]
    excluded: tuple[tuple[str, str], ...]
    conflict_ids: tuple[str, ...]

    def field(self, key):
        return next((f for f in self.fields if f.key == key), None)

    @property
    def known_refs(self):
        return frozenset(ref for f in self.fields if f.state == "KNOWN" for ref in f.evidence_refs)


class Scenario(Contract):
    scenario_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    support_refs: tuple[str, ...]
    conditions: tuple[str, ...]


class Action(Contract):
    action_id: str = Field(min_length=1)
    action_type: Literal["THREAT", "SINGLE_HIT", "SHORT_TRADE", "EXTENDED_TRADE", "ALL_IN", "CHASE", "CONCEDE_RESOURCE", "HOLD_PRESSURE", "FREEZE", "SLOW_PUSH", "CRASH", "CLAIM_SPACE", "CLAIM_RESOURCE", "WAIT", "PROBE", "DISENGAGE", "FULL_COMMIT", "LIMITED_SUPPORT", "EXIT_COVER", "CROSS_MAP_TRADE", "RECALL", "ROAM", "AMBUSH"]
    feasibility: Literal["POSSIBLE", "IMPOSSIBLE", "UNKNOWN"]
    feasibility_refs: tuple[str, ...]
    required_keys: tuple[str, ...]
    target: str = Field(min_length=1)
    path: str = Field(min_length=1)
    entry_condition: str = Field(min_length=1)
    resource_budget: str = Field(min_length=1)
    exit_condition: str = Field(min_length=1)
    abort_conditions: tuple[str, ...] = Field(min_length=1)
    postcondition: str = Field(min_length=1)
    deadline_event: str = Field(min_length=1)


class Assessment(Contract):
    action_id: str
    scenario_id: str
    assessment: Literal["FAVORABLE", "UNFAVORABLE", "CONTESTED", "UNDETERMINED"]
    rationale: str = Field(min_length=1)
    evidence_refs: tuple[str, ...]
    knowledge_status: Literal["REVIEWED", "EXPLORATORY"]
    patch: str
    knowledge_ref: str = Field(min_length=1)


DIMENSIONS = ("survival_exposure", "resources", "growth", "position_wave", "time_objectives", "options")


class DimensionRelation(Contract):
    dimension: Literal["survival_exposure", "resources", "growth", "position_wave", "time_objectives", "options"]
    relation: Literal["BETTER", "SAME", "WORSE", "UNKNOWN"]
    rationale: str = Field(min_length=1)
    evidence_refs: tuple[str, ...]


class Comparison(Contract):
    left_action_id: str
    right_action_id: str
    scenario_id: str
    dimensions: tuple[DimensionRelation, ...]

    @model_validator(mode="after")
    def complete_dimensions(self):
        if sorted(x.dimension for x in self.dimensions) != sorted(DIMENSIONS):
            raise ValueError("exactly six distinct comparison dimensions required")
        if self.left_action_id == self.right_action_id:
            raise ValueError("self comparison")
        return self


class InformationRequest(Contract):
    field_key: str
    action_ids: tuple[str, ...]
    changes_conclusion: bool
    minimum_observation: str = Field(min_length=1)
    available_before_deadline: Literal["YES", "NO", "UNKNOWN"]
    waiting_cost: str = Field(min_length=1)


class ReviewInput(Contract):
    schema_version: Literal["r3.v1"]
    evidence_kind: Literal["SYNTHETIC"]
    mode: Literal["TEST", "PRE_GAME", "POST_GAME", "LIVE_STATIC"]
    objective: str = Field(min_length=1)
    scope_reason: str = Field(min_length=1)
    snapshot_request: SnapshotRequest
    observations: tuple[Observation, ...]
    scenarios: tuple[Scenario, ...] = Field(min_length=1)
    actions: tuple[Action, ...] = Field(min_length=1)
    assessments: tuple[Assessment, ...]
    comparisons: tuple[Comparison, ...]
    information_requests: tuple[InformationRequest, ...] = ()
    occurred_events: tuple[str, ...] = ()
    intended_plan: str | None = None
    outcome_note: str | None = None

    @model_validator(mode="after")
    def links(self):
        aids=[a.action_id for a in self.actions]; sids=[s.scenario_id for s in self.scenarios]
        if len(set(aids)) != len(aids) or len(set(sids)) != len(sids):
            raise ValueError("duplicate action/scenario ID")
        keys=[]
        for a in self.assessments:
            if a.action_id not in aids or a.scenario_id not in sids:
                raise ValueError("dangling assessment")
            keys.append((a.action_id,a.scenario_id))
        if len(set(keys)) != len(keys): raise ValueError("duplicate assessment")
        keys=[]
        for c in self.comparisons:
            if c.left_action_id not in aids or c.right_action_id not in aids or c.scenario_id not in sids:
                raise ValueError("dangling comparison")
            keys.append((tuple(sorted((c.left_action_id,c.right_action_id))),c.scenario_id))
        if len(set(keys)) != len(keys): raise ValueError("duplicate or contradictory pair comparison")
        for q in self.information_requests:
            if not set(q.action_ids).issubset(aids): raise ValueError("dangling information request")
        if any(o.session_id != self.snapshot_request.session_id for o in self.observations):
            raise ValueError("mixed session observation batch")
        return self

"""Pure immutable snapshots. No TTL guesses or promotion of inferred observations."""
from collections import defaultdict
import hashlib
import json

from .models import Observation, SnapshotRequest, Snapshot, FieldState


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def reduce_snapshot(observations: tuple[Observation,...], request: SnapshotRequest) -> Snapshot:
    # knowledge_cutoff is analysis intake cutoff in PLAYER_REVIEW, historical reception
    # cutoff in RECEIVED_AS_OF. Event cutoff and player visibility apply in both views.
    by_id=defaultdict(dict); excluded=[]
    for o in observations:
        if o.session_id != request.session_id:
            raise ValueError("cross-session observation")
        if o.received_at > request.knowledge_cutoff:
            excluded.append((o.observation_id,"AFTER_KNOWLEDGE_CUTOFF")); continue
        if o.event_time_ms > request.as_of_event_time_ms:
            excluded.append((o.observation_id,"FUTURE_EVENT")); continue
        by_id[o.observation_id][digest(o.model_dump(mode="json"))]=o
    collisions={oid for oid,variants in by_id.items() if len(variants)>1}
    selected={oid:next(iter(variants.values())) for oid,variants in by_id.items() if oid not in collisions}

    def status(oid,chain=()):
        if oid in chain: return "CONFLICTING",("CYCLIC_LINEAGE",)
        if oid in collisions: return "CONFLICTING",("ID_PAYLOAD_COLLISION",)
        o=selected.get(oid)
        if o is None: return "UNKNOWN",("MISSING_LINEAGE",)
        if o.patch != request.patch: return "UNKNOWN",("PATCH_MISMATCH",)
        if o.game_clock_basis != request.game_clock_basis: return "UNKNOWN",("CLOCK_UNALIGNED",)
        if o.perspective != "PLAYER" or o.visibility_at_event != "KNOWN":
            return "UNKNOWN",("NOT_PLAYER_KNOWN",)
        # A derived field must not launder one side of an unresolved source conflict.
        for other_id, variants in by_id.items():
            eligible=[other for other in variants.values() if other.key==o.key
                      and other.patch==o.patch and other.game_clock_basis==o.game_clock_basis
                      and other.perspective=='PLAYER' and other.visibility_at_event=='KNOWN']
            if eligible and other_id in collisions:
                return "CONFLICTING",("SOURCE_FIELD_ID_COLLISION",)
            if any(other.event_time_ms==o.event_time_ms and canonical(other.value)!=canonical(o.value) for other in eligible):
                return "CONFLICTING",("SOURCE_FIELD_VALUE_CONFLICT",)
        if o.value is None: return "UNKNOWN",(o.missing_reason or "MISSING_VALUE",)
        if "CONFLICTING" in o.quality_state.model_dump().values(): return "CONFLICTING",("SOURCE_QUALITY_CONFLICT",)
        if o.validity=="AT_EVENT" and o.event_time_ms != request.as_of_event_time_ms:
            return "STALE",("CURRENT_VALIDITY_NOT_ESTABLISHED",)
        if o.kind in ("MANUAL","INFERRED"): return "CONDITIONAL",(o.kind+"_NOT_FACT",)
        if any(v != "VERIFIED" for v in o.quality_state.model_dump().values()):
            return "CONDITIONAL",("SOURCE_QUALITY_UNVERIFIED",)
        for ref in o.lineage_ids:
            parent=selected.get(ref)
            if parent is not None and parent.event_time_ms>o.event_time_ms:
                return "CONDITIONAL",("FUTURE_LINEAGE",ref)
            st,reasons=status(ref,chain+(oid,))
            if st!="KNOWN": return "CONDITIONAL",("LINEAGE_NOT_KNOWN",ref,*reasons)
        return "KNOWN",()

    groups=defaultdict(list)
    for o in selected.values():
        # Hidden and incompatible data are archived as excluded; they cannot supersede
        # an older player-known observation simply because their event timestamp is newer.
        if o.patch!=request.patch or o.game_clock_basis!=request.game_clock_basis or o.perspective!="PLAYER" or o.visibility_at_event!="KNOWN":
            excluded.append((o.observation_id,status(o.observation_id)[1][0])); continue
        groups[o.key].append(o)
    collision_keys=defaultdict(list)
    for oid in collisions:
        for o in by_id[oid].values(): collision_keys[o.key].append(oid)
    fields=[]
    for key in sorted(set(groups)|set(request.required_keys)|set(collision_keys)):
        if key in collision_keys:
            fields.append(FieldState(key=key,value=None,state="CONFLICTING",evidence_refs=tuple(sorted(set(collision_keys[key]))),reasons=("ID_PAYLOAD_COLLISION",),independent_groups=()))
            continue
        entries=groups.get(key,[])
        if not entries:
            fields.append(FieldState(key=key,value=None,state="UNKNOWN",evidence_refs=(),reasons=("NO_ELIGIBLE_OBSERVATION",),independent_groups=()))
            continue
        latest=max(o.event_time_ms for o in entries)
        current=sorted((o for o in entries if o.event_time_ms==latest),key=lambda o:o.observation_id)
        refs=tuple(o.observation_id for o in current)
        states=[status(o.observation_id) for o in current]
        values={canonical(o.value) for o in current}
        if len(values)>1 or any(st=="CONFLICTING" for st,_ in states): st="CONFLICTING"
        elif any(st=="UNKNOWN" for st,_ in states): st="UNKNOWN"
        elif any(st=="STALE" for st,_ in states): st="STALE"
        elif any(st=="CONDITIONAL" for st,_ in states): st="CONDITIONAL"
        else: st="KNOWN"
        reasons=sorted({reason for _,rs in states for reason in rs})
        if len(values)>1: reasons.append("SAME_TIME_VALUE_CONFLICT")
        fields.append(FieldState(key=key,value=current[0].value if st in ("KNOWN","CONDITIONAL") else None,state=st,evidence_refs=refs,reasons=tuple(reasons),independent_groups=tuple(sorted({o.independent_group_id for o in current}))))
    hashes=tuple(sorted((oid,h) for oid,vs in by_id.items() for h in vs))
    body=dict(request=request.model_dump(mode="json"),fields=[f.model_dump(mode="json") for f in fields],observation_hashes=hashes,excluded=sorted(set(excluded)),conflict_ids=sorted(collisions))
    return Snapshot(snapshot_id=digest(body),request=request,fields=tuple(fields),observation_hashes=hashes,excluded=tuple(sorted(set(excluded))),conflict_ids=tuple(sorted(collisions)))

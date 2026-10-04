"""Evidence gating and symbolic comparison; supplied annotations are not game simulation."""
from .models import ReviewInput, DIMENSIONS
from .state import reduce_snapshot, digest


class ModeBlocked(ValueError):
    pass


def run_review(case: ReviewInput, *, allow_synthetic: bool = False):
    # No sample-verified match-end adapter exists in R3. Manual flags must not
    # unlock real post-game analysis. TEST is explicit and never a production mode.
    if case.mode != "TEST" or not allow_synthetic or case.evidence_kind != "SYNTHETIC":
        raise ModeBlocked("R3_SYNTHETIC_ONLY: real modes require verified adapters and release gates")
    snapshot=reduce_snapshot(case.observations,case.snapshot_request)
    known=snapshot.known_refs
    supported=lambda refs: bool(refs) and set(refs).issubset(known)
    scenarios={s.scenario_id:s for s in case.scenarios}
    scope_supported=bool(case.scope_reason.strip()) and all(supported(s.support_refs) for s in case.scenarios)
    evaluations=[]
    for action in case.actions:
        missing=[key for key in action.required_keys if not snapshot.field(key) or snapshot.field(key).state!="KNOWN"]
        expired=action.deadline_event in case.occurred_events or bool(set(action.abort_conditions)&set(case.occurred_events))
        feasibility=action.feasibility if supported(action.feasibility_refs) else "UNKNOWN"
        rows=[]
        for sid in scenarios:
            a=next((a for a in case.assessments if a.action_id==action.action_id and a.scenario_id==sid),None)
            eligible=bool(a and supported(a.evidence_refs) and a.patch==case.snapshot_request.patch and a.knowledge_status=="REVIEWED" and supported(scenarios[sid].support_refs))
            rows.append(dict(scenario_id=sid,assessment=a.assessment if eligible and not missing and feasibility=="POSSIBLE" and not expired else "UNDETERMINED",rationale=a.rationale if a else "NO_ASSESSMENT",evidence_refs=list(a.evidence_refs) if a else [],annotation_status="ELIGIBLE_SYNTHETIC_ANNOTATION" if eligible else "UNVERIFIED_OR_MISSING",conditions=list(scenarios[sid].conditions)))
        answers={r['assessment'] for r in rows}
        if missing or feasibility!="POSSIBLE" or expired or not scope_supported or "UNDETERMINED" in answers:
            sufficient="INSUFFICIENT";assessment="UNDETERMINED"
        elif len(answers)>1:
            sufficient="CONDITIONAL";assessment="CONTESTED"
        else:
            sufficient="SUFFICIENT";assessment=next(iter(answers))
        evaluations.append(dict(action_id=action.action_id,action_type=action.action_type,feasibility=feasibility,sufficiency=sufficient,assessment=assessment,missing_fields=missing,expired=expired,scenario_assessments=rows,contract=action.model_dump(mode='json')))
    by_action={a['action_id']:a for a in evaluations}

    # Evaluate each direction against ALL supplied scenarios and six dimensions.
    # Relations are explicit synthetic expert annotations; no hidden weights.
    dominates=[]
    for left in by_action:
        for right in by_action:
            if left==right or not scope_supported: continue
            a,b=by_action[left],by_action[right]
            if any(x['feasibility']!="POSSIBLE" or x['expired'] or x['missing_fields'] or x['sufficiency']=='INSUFFICIENT' for x in (a,b)): continue
            strict=False; ok=True
            for sid in scenarios:
                c=next((c for c in case.comparisons if c.scenario_id==sid and {c.left_action_id,c.right_action_id}=={left,right}),None)
                if c is None: ok=False;break
                for d in c.dimensions:
                    rel=d.relation
                    if c.left_action_id!=left: rel={'BETTER':'WORSE','WORSE':'BETTER'}.get(rel,rel)
                    if not supported(d.evidence_refs) or rel in ('WORSE','UNKNOWN'): ok=False
                    strict |= rel=='BETTER'
            if ok and strict: dominates.append((left,right))
    # Each scenario/dimension is a partial order. SAME contributes two non-strict
    # edges, so A>B, B>C, A=C is a contradiction even without a strict-only cycle.
    order_conflicts=set()
    for sid in scenarios:
        for dimension in DIMENSIONS:
            edges=[]
            for c in case.comparisons:
                if c.scenario_id!=sid: continue
                d=next(d for d in c.dimensions if d.dimension==dimension)
                if not supported(d.evidence_refs): continue
                if d.relation in ('BETTER','SAME'):edges.append((c.left_action_id,c.right_action_id,d.relation=='BETTER'))
                if d.relation in ('WORSE','SAME'):edges.append((c.right_action_id,c.left_action_id,d.relation=='WORSE'))
            def strict_cycle(start,node,strict,seen):
                state=(node,strict)
                if state in seen:return False
                seen=seen|{state}
                for u,v,is_strict in edges:
                    if u!=node:continue
                    next_strict=strict or is_strict
                    if v==start and next_strict:return True
                    if strict_cycle(start,v,next_strict,seen):return True
                return False
            order_conflicts.update(a for a in by_action if strict_cycle(a,a,False,set()))
    # Inconsistent supplied pairwise rankings must not eliminate alternatives.
    def reachable(start,target,visited):
        if start in visited:return False
        visited=visited|{start}
        return any(v==target or reachable(v,target,visited) for u,v in dominates if u==start)
    cycles={node for node in by_action if reachable(node,node,set())}|order_conflicts
    if cycles: dominates=[]
    dominated={b for _,b in dominates}
    alternatives=[a['action_id'] for a in evaluations if a['feasibility']=='POSSIBLE' and not a['expired'] and a['action_id'] not in dominated]
    requests=[];deferred=[]
    for q in case.information_requests:
        relevant=[aid for aid in q.action_ids if q.field_key in by_action[aid]['missing_fields']]
        if q.changes_conclusion and relevant:
            active=[aid for aid in relevant if not by_action[aid]['expired'] and by_action[aid]['feasibility']!='IMPOSSIBLE']
            item=q.model_dump(mode='json')
            item['action_ids']=active
            item['inactive_action_ids']=[aid for aid in relevant if aid not in active]
            item['reason']='ACTIVE_BEFORE_DEADLINE' if active and q.available_before_deadline=='YES' else 'NO_ACTIVE_TARGET' if not active else 'OBSERVATION_NOT_TIMELY_OR_UNKNOWN'
            (requests if active and q.available_before_deadline=='YES' else deferred).append(item)
    return dict(schema_version='r3.v1',evidence_kind='SYNTHETIC',decision_id=digest(case.model_dump(mode='json')),mode='TEST',objective=case.objective,scope_reason=case.scope_reason,scope_limit='Only supplied scenarios; scope completeness and game annotations are not independently verified.',snapshot=snapshot.model_dump(mode='json'),evaluations=evaluations,dominance=[dict(better=a,worse=b) for a,b in dominates],comparison_conflicts=sorted(cycles),alternatives=alternatives,recommendation=None,information_requests=requests,deferred_information=deferred,intention=dict(state='PROVIDED' if case.intended_plan else 'UNKNOWN',text=case.intended_plan,execution_violation='NOT_EVALUATED'),outcome=dict(text=case.outcome_note,used_for_decision=False),limitations=['Offline synthetic contract execution only.','No damage, matchup, cooldown, win-probability or live game inference.','No production adapter, AI service, API or web UI enabled.'])

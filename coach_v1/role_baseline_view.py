"""Small plotting projection from already validated anonymous power/progress.

Catalog owns validation before calling this helper. Retained clustered spread
alone never invents a mean: exact same-role population means must agree.
"""
import math
from collections import defaultdict
from .power_stats import student_t_critical,POSITIONS
from .collection_progress import estimated_target

def role_baseline_curves_from_validated(data,progress):
    means=defaultdict(list)
    for cohort in data['cohorts']:
        if cohort['comparison']!='ROLE_POPULATION':continue
        for point in cohort['points']:
            if 'reference_mean' in point:
                means[(cohort['position'],cohort['metric'],point['minute'])].append((point['n'],point['reference_mean']))
    roles=[]
    limits=data['source']['precision_policy']['ci_width_limits'] or {}
    for position in POSITIONS:
        role=next(r for r in progress['roles'] if r['position']==position);curves=[]
        for curve in role['role_baseline'].get('curves',[]):
            points=[]
            for evidence in curve.get('precision_evidence',[]):
                minute=evidence['minute'];n=evidence['match_count'];sd=evidence['empirical_sd']
                rows=means.get((position,curve['metric'],minute),[])
                compatible=bool(rows) and all(count==n and abs(mean-rows[0][1])<1e-8 for count,mean in rows)
                mean=rows[0][1] if compatible else None
                target=estimated_target(n,sd,limits.get(curve['metric'])) if compatible else None
                half=student_t_critical(n-1)*sd/math.sqrt(n) if compatible and n>=2 and sd is not None else None
                status='READY' if target is not None and n>=target else ('ESTIMATED' if target is not None else 'UNKNOWN')
                points.append(dict(minute=minute,match_count=n,participant_count=2*n,mean=mean,
                    ci95=dict(low=mean-half if half is not None else None,high=mean+half if half is not None else None),
                    status=status,estimated_remaining_matches=max(0,target-n) if target is not None else None,
                    reason=None if status=='READY' else ('POPULATION_MEAN_UNAVAILABLE_OR_CONFLICTING' if not compatible else ('N_LT_2' if n<2 else 'CI_TOO_WIDE'))))
            curves.append(dict(metric=curve['metric'],units=curve['units'],points=points))
        roles.append(dict(position=position,status='READY' if any(p['status']=='READY' for c in curves for p in c['points']) else 'UNKNOWN',curves=curves))
    return dict(schema_version='pregame.role-baseline-curves.v1',roles=roles,
        source_digest=progress['power_dataset_sha256'],tier=data['source']['tier'],patch=data['source']['patch'],
        formula='POOLED_SAME_ROLE_MEAN_RATE_MATCH_CLUSTER_STUDENT_T95.v1',coaching_accuracy=None,
        limitations=['DESCRIPTIVE_NON_CAUSAL','INDEPENDENT_MATCH_CLUSTER_CI','SPARSE_TAIL_REMAINS_UNKNOWN'])

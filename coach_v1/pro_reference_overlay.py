"""Add selected-pro absolute reference curves without rewriting League deltas."""
from copy import deepcopy
from .pro_reference import validate_pro_reference


def attach_pro_reference(detail,data,test_mode=False):
    result=deepcopy(detail)
    reference=dict(status='UNKNOWN',reason='PRO_REFERENCE_NOT_COLLECTED',comparison_group='PRO_ROSTER',
        selection='USER_PRO_REFERENCE_ROSTER',tier='UNKNOWN',verification='USER_REPORT_NOT_NETWORK_VERIFIED',
        units='ABSOLUTE_RECORDED_RESOURCE_TOTALS',cohorts=[],limitations=[])
    result['pro_reference']=reference
    if data is None:return result
    d=validate_pro_reference(data)
    reference.update(roster_sha256=d['roster_sha256'],sample_kind=d['sample_kind'],limitations=deepcopy(d['limitations']))
    if d['sample_kind']=='SYNTHETIC' and not test_mode:
        reference['reason']='SYNTHETIC_REFERENCE_REQUIRES_TEST_MODE';return result
    for cohort in d['cohorts']:
        if (cohort['champion'],cohort['position'],cohort['patch'])!=(detail.get('champion'),detail.get('role'),detail.get('patch')):continue
        c=deepcopy(cohort);c['comparison_group']='PRO_ROSTER'
        c['personal_points']=[dict(minute=p['minute'],value=p.get(c['metric'])) for p in detail.get('resources',[])]
        reference['cohorts'].append(c)
    known=any(p['visible'] for c in reference['cohorts'] for p in c['points'])
    reference.update(status='KNOWN' if known else 'UNKNOWN',reason=None if known else 'NO_ELIGIBLE_SAME_CHAMPION_ROLE_PATCH_PRO_SAMPLE')
    return result

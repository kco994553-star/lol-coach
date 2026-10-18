"""User-approved Challenger policy and current official static patch metadata."""
from datetime import datetime,timezone
import re
from .power_stats import validate_power_dataset

FUTURE_STATISTICS_TIERS=('MASTER','GRANDMASTER','CHALLENGER')

def validate_new_statistics_tier(tier):
    """Current ranked seed eligibility, not every participant's historic rank."""
    if tier not in FUTURE_STATISTICS_TIERS:raise ValueError('MASTER_PLUS_REQUIRED')
    return tier


def resolve_patch(versions,*,explicit=None):
    if explicit:
        if not isinstance(explicit,str) or re.fullmatch(r'\d{1,3}\.\d{1,3}',explicit) is None:raise ValueError('INVALID_EXPLICIT_PATCH')
        return explicit
    if not isinstance(versions,list) or not versions or len(versions)>1000 or not isinstance(versions[0],str) or re.fullmatch(r'\d{1,3}\.\d{1,3}\.\d{1,4}',versions[0]) is None:
        raise ValueError('OFFICIAL_CURRENT_PATCH_UNKNOWN')
    return '.'.join(versions[0].split('.')[:2])


def key_enabled(policy,now,*,manual_confirmed=False):
    if manual_confirmed:return True
    def stamp(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
    return stamp(policy['key_renewed_at'])<=now<stamp(policy['key_valid_until'])


def auxiliary_needed(datasets,*,patch):
    for raw in datasets:
        d=validate_power_dataset(raw)
        if d['source']['sample_kind']!='REAL' or d['source']['tier']!='CHALLENGER' or d['source']['patch']!=patch:continue
        roles={c['position'] for c in d['cohorts']}
        if not {'TOP','JUNGLE','MID','BOTTOM','SUPPORT'}<=roles:return True
        for c in d['cohorts']:
            if any(not p['visible'] for p in c['points']):return True
    return False

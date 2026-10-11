"""Compare an explicit numerical speech criterion with one descriptive aggregate.

No prose becomes a radius, predicate, tactic, verified utterance, or approval.
The bridge validates expert artifacts; this independent consumer also validates
its narrow numerical criterion and movement dataset before comparison.
"""
from copy import deepcopy
import math
import re
from urllib.parse import urlsplit
from .movement import validate_movement_dataset, POSITIONS, STAGES, TIERS
from .state import canonical, digest

MEASUREMENT_KEYS={'kind','cohort_id','patch','tier','minute','operator','threshold',
    'criterion_source_url','rationale','origin'}
COMPARISON_LIMITATION='NUMERICAL_COMPARISON_NOT_TACTICAL_VALIDATION_OR_APPROVAL'
MAX_SOURCE_BYTES=32768
HASH=re.compile(r'[a-f0-9]{64}\Z')
PATCH=re.compile(r'[0-9]+\.[0-9]+\Z')
CHAMPION=re.compile(r'[A-Za-z][A-Za-z0-9]{0,99}\Z')


def _result(status,reason,statistic=None):
    return dict(status=status,reasons=[reason],statistic=statistic)


def _criterion(value):
    if not isinstance(value,dict) or set(value)!=MEASUREMENT_KEYS:return None
    c=deepcopy(value)
    if c['kind']!='MOVEMENT_MEAN_DISTANCE':return None
    if not isinstance(c['cohort_id'],str) or not HASH.fullmatch(c['cohort_id']):return None
    if not isinstance(c['patch'],str) or not PATCH.fullmatch(c['patch']) or c['tier'] not in TIERS:return None
    if type(c['minute']) is not int or c['minute']<0 or c['operator'] not in ('LE','GE'):return None
    if type(c['threshold']) not in (int,float):return None
    try:
        if not math.isfinite(c['threshold']) or c['threshold']<0:return None
    except OverflowError:return None
    if c['origin'] not in ('MANUAL','REVIEWED'):return None
    if not isinstance(c['rationale'],str) or not c['rationale'].strip() or len(c['rationale'])>500:return None
    url=c['criterion_source_url']
    if not isinstance(url,str) or not 9<=len(url)<=2000:return None
    try:
        parsed=urlsplit(url)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username is not None or parsed.password is not None:return None
        # Trigger validation of malformed numeric ports without ever echoing the URL.
        parsed.port
    except ValueError:return None
    return c


def compare_claim(claim,movement_data,test_mode=False):
    """Return {status,reasons,statistic}; caller criteria are never inferred.

    LE agrees only when CI high <= threshold, disagrees when CI low > threshold;
    GE agrees only when CI low >= threshold, disagrees when CI high < threshold.
    A visible interval crossing the criterion remains INSUFFICIENT with evidence.
    """
    if not isinstance(claim,dict):return _result('UNMEASURABLE','INVALID_CLAIM')
    if claim.get('measurable') is not True:return _result('UNMEASURABLE','CLAIM_NOT_MEASURABLE')
    if claim.get('measurement') is None:return _result('UNMEASURABLE','NO_EXPLICIT_NUMERICAL_CRITERION')
    criterion=_criterion(claim['measurement'])
    if criterion is None:return _result('UNMEASURABLE','INVALID_NUMERICAL_CRITERION')
    champion=claim.get('champion');position=claim.get('position');stage=claim.get('stage')
    if not isinstance(champion,str) or champion=='UNKNOWN' or not CHAMPION.fullmatch(champion) or position not in POSITIONS or stage not in STAGES:
        return _result('INSUFFICIENT','CLAIM_SCOPE_UNKNOWN')
    if movement_data is None:return _result('INSUFFICIENT','MOVEMENT_DATA_UNAVAILABLE')
    try:
        data=validate_movement_dataset(movement_data)
    except (ValueError,KeyError,TypeError,OverflowError,RecursionError):
        return _result('INSUFFICIENT','MOVEMENT_DATA_INVALID')
    source=data['source'];synthetic=source['sample_kind']=='SYNTHETIC'
    if synthetic and test_mode is not True:return _result('INSUFFICIENT','SYNTHETIC_DATA_NOT_REAL_EVIDENCE')
    if len(canonical(source).encode('utf-8'))>MAX_SOURCE_BYTES:return _result('INSUFFICIENT','SOURCE_METADATA_TOO_LARGE')
    cohort=next((co for co in data['cohorts'] if co['id']==criterion['cohort_id']),None)
    if cohort is None:return _result('INSUFFICIENT','COHORT_NOT_FOUND')
    if (cohort['champion'],cohort['position'],cohort['stage'])!=(champion,position,stage):
        return _result('INSUFFICIENT','CLAIM_COHORT_SCOPE_MISMATCH')
    if cohort['patch']!=criterion['patch'] or cohort['tier']!=criterion['tier']:
        return _result('INSUFFICIENT','CRITERION_COHORT_PATCH_TIER_MISMATCH')
    # The movement validator checks state semantics and requires VERIFIED lineage.
    # A null-stage minute candidate is never promoted using timestamp or speech.
    if not cohort['condition_signature'] or not any(s['verification']=='VERIFIED' for s in source.get('phase_annotation_sources',[])):
        return _result('INSUFFICIENT','VERIFIED_PHASE_SUPPORT_UNAVAILABLE')
    point=next((p for p in cohort['points'] if p['minute']==criterion['minute']),None)
    if point is None:return _result('INSUFFICIENT','MINUTE_NOT_FOUND')
    if point['n']<2 or not point['visible'] or point['ci95']['low'] is None or point['ci95']['high'] is None:
        return _result('INSUFFICIENT','PRECISION_INSUFFICIENT')
    limitations=list(dict.fromkeys([*source['limitations'],COMPARISON_LIMITATION]))
    if synthetic:limitations.append('SYNTHETIC_TEST_NOT_REAL_EVIDENCE')
    statistic=dict(dataset_sha256=digest(data),cohort_id=cohort['id'],champion=champion,
        position=position,stage=stage,patch=cohort['patch'],tier=cohort['tier'],minute=point['minute'],
        condition_signature=deepcopy(cohort['condition_signature']),source=deepcopy(source),
        formula=source['formula_version'],n=point['n'],mean_distance=point['mean_distance'],
        ci95=deepcopy(point['ci95']),criterion=criterion,limitations=limitations,
        evidence_kind='TEST' if synthetic else 'REAL_AGGREGATE')
    low=point['ci95']['low'];high=point['ci95']['high'];threshold=criterion['threshold']
    if criterion['operator']=='LE':agrees=high<=threshold;disagrees=low>threshold
    else:agrees=low>=threshold;disagrees=high<threshold
    if agrees:return _result('AGREES','NUMERICAL_CRITERION_SUPPORTED',statistic)
    if disagrees:return _result('DISAGREES','NUMERICAL_CRITERION_CONTRADICTED',statistic)
    return _result('INSUFFICIENT','CONFIDENCE_INTERVAL_CROSSES_THRESHOLD',statistic)

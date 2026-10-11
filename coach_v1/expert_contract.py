"""Bounded unverified source statements; no network, approval, or prose execution."""
from copy import deepcopy
from datetime import date,datetime
import json
import math
import re
from urllib.parse import urlsplit

MAX_BYTES=200_000
MAX_CLAIMS=100
REJECTION_REASONS=frozenset({'FAILED_FORMAT','INVALID_CLAIM','INVALID_TIMESTAMP',
    'OUT_OF_RANGE_TIMESTAMP','DUPLICATE_CLAIM','NO_ACCEPTED_CLAIMS'})
MODEL_FIELDS={'timestamp','paraphrase','champion','position','stage','conditions','context','measurable'}
CLAIM_FIELDS=MODEL_FIELDS|{'timestamp_seconds','patch_range','counterexamples','limitations','measurement','independent_group_id'}
POSITIONS=('TOP','JUNGLE','MID','BOTTOM','SUPPORT','UNKNOWN')
TIERS=('IRON','BRONZE','SILVER','GOLD','PLATINUM','EMERALD','DIAMOND','MASTER','GRANDMASTER','CHALLENGER')


def _require(condition):
    if not condition:raise ValueError('INVALID_EXPERT_ARTIFACT')


def _keys(value,fields):_require(type(value) is dict and set(value)==set(fields))


def _text(value,maximum):
    _require(type(value) is str and bool(value.strip()) and len(value)<=maximum)
    try:value.encode('utf-8')
    except UnicodeError:raise ValueError('INVALID_EXPERT_ARTIFACT') from None
    # Public artifacts cannot carry recognizable credential material.
    _require(not re.search(r'(?:RGAPI-[A-Za-z0-9-]{8,}|AIza[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,})',value))
    return value


def _integer(value,minimum=0,maximum=None):
    _require(type(value) is int and value>=minimum and (maximum is None or value<=maximum))


def _bounded(value):
    try:encoded=json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    except (TypeError,ValueError,UnicodeError,RecursionError):raise ValueError('INVALID_EXPERT_ARTIFACT') from None
    _require(len(encoded)<=MAX_BYTES)
    return encoded


def _strings(values,minimum,maximum,length):
    _require(type(values) is list and minimum<=len(values)<=maximum)
    for value in values:_text(value,length)


def _utc(value):
    _text(value,40)
    _require(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)',value) is not None)
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    _require(parsed.utcoffset().total_seconds()==0)


def _timestamp(value):
    _text(value,12)
    match=re.fullmatch(r'(\d{2,}):([0-5]\d)',value)
    _require(match is not None)
    return int(match[1])*60+int(match[2])


def _patch(value):
    _text(value,40)
    if value=='UNKNOWN':return
    _require(re.fullmatch(r'\d+\.\d+(?:-\d+\.\d+)?',value) is not None)
    endpoints=[tuple(map(int,p.split('.'))) for p in value.split('-')]
    _require(len(endpoints)==1 or endpoints[0]<=endpoints[1])


def _measurement(value):
    if value is None:return
    _keys(value,{'kind','cohort_id','patch','tier','minute','operator','threshold','criterion_source_url','rationale','origin'})
    _require(value['kind']=='MOVEMENT_MEAN_DISTANCE')
    _require(type(value['cohort_id']) is str and re.fullmatch('[a-f0-9]{64}',value['cohort_id']) is not None)
    _patch(value['patch']);_require(re.fullmatch(r'\d+\.\d+',value['patch']) is not None)
    _require(value['tier'] in TIERS);_integer(value['minute'])
    _require(value['operator'] in ('LE','GE') and value['origin'] in ('MANUAL','REVIEWED'))
    _require(type(value['threshold']) in (int,float) and math.isfinite(value['threshold']) and value['threshold']>=0)
    _text(value['criterion_source_url'],2000);url=urlsplit(value['criterion_source_url'])
    _require(url.scheme=='https' and url.hostname is not None and url.username is None and url.password is None)
    _text(value['rationale'],500)


def _model_claim(value,duration):
    _keys(value,MODEL_FIELDS)
    seconds=_timestamp(value['timestamp']);_require(seconds<duration)
    _text(value['paraphrase'],500);_text(value['champion'],40)
    _require(re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,39}',value['champion']) is not None)
    _require(value['position'] in POSITIONS and value['stage'] in ('EARLY','MID','LATE','UNKNOWN'))
    _strings(value['conditions'],0,10,200)
    _require(value['context'] in ('EXPLANATION','JOKE','EXAGGERATION_SUSPECTED','UNKNOWN'))
    _require(type(value['measurable']) is bool)
    return seconds


def validate_expert_artifact(value):
    """Validate and copy a public artifact; caller assertions remain assertions."""
    try:
        _bounded(value)
        _keys(value,{'schema_version','video','processing','claims','rejections','visual_verified','coaching_accuracy'})
        _require(value['schema_version']=='expert.claims.v1' and value['visual_verified'] is False and value['coaching_accuracy'] is None)
        video=value['video']
        _keys(video,{'id','url','title','channel_id','channel_name','speaker','speaker_verified','published_at','upload_date','duration_seconds','language'})
        _text(video['id'],11);_require(re.fullmatch(r'[A-Za-z0-9_-]{11}',video['id']) is not None)
        _require(video['url']=='https://www.youtube.com/watch?v='+video['id'])
        for field in ('title','channel_name','speaker'):_text(video[field],200)
        if video['channel_id'] is not None:
            _text(video['channel_id'],24);_require(re.fullmatch(r'UC[A-Za-z0-9_-]{22}',video['channel_id']) is not None)
        _require(type(video['speaker_verified']) is bool)
        _require(video['speaker_verified'] or video['speaker']=='UNKNOWN')
        if video['published_at'] is not None:_utc(video['published_at'])
        if video['upload_date'] is not None:
            _text(video['upload_date'],10);_require(date.fromisoformat(video['upload_date']).isoformat()==video['upload_date'])
        _integer(video['duration_seconds'],1,28800)
        _text(video['language'],40);_require(video['language']=='UNKNOWN' or re.fullmatch(r'[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8}){0,3}',video['language']) is not None)
        processing=value['processing']
        _keys(processing,{'method','model','processed_at','input_sha256'})
        _require(processing['method'] in ('MANUAL_SUMMARY','GEMINI_YOUTUBE'))
        _text(processing['model'],100);_require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,99}',processing['model']) is not None)
        if processing['method']=='MANUAL_SUMMARY':_require(processing['model']=='UNKNOWN')
        else:_require(video['speaker']=='UNKNOWN' and video['speaker_verified'] is False and video['channel_id'] is not None)
        _utc(processing['processed_at'])
        _require(type(processing['input_sha256']) is str and re.fullmatch('[a-f0-9]{64}',processing['input_sha256']) is not None)
        _require(type(value['claims']) is list and 1<=len(value['claims'])<=MAX_CLAIMS)
        seen=set()
        for claim in value['claims']:
            _keys(claim,CLAIM_FIELDS)
            seconds=_model_claim({key:claim[key] for key in MODEL_FIELDS},video['duration_seconds'])
            _integer(claim['timestamp_seconds']);_require(claim['timestamp_seconds']==seconds)
            _patch(claim['patch_range']);_strings(claim['counterexamples'],1,10,300);_strings(claim['limitations'],1,10,300)
            _measurement(claim['measurement'])
            _require(claim['independent_group_id']=='YOUTUBE:'+video['id'])
            identity=_bounded(claim);_require(identity not in seen);seen.add(identity)
        _require(type(value['rejections']) is list and len(value['rejections'])<=MAX_CLAIMS)
        for rejection in value['rejections']:
            _keys(rejection,{'index','reason'});_integer(rejection['index']);_require(rejection['reason'] in REJECTION_REASONS)
        return deepcopy(value)
    except (TypeError,KeyError,AttributeError,OverflowError,UnicodeError,RecursionError):
        raise ValueError('INVALID_EXPERT_ARTIFACT') from None


def normalize_gemini_claims(value,duration_seconds):
    """Convert strict model JSON into unverified summaries, with safe errors."""
    claims=[];rejections=[];seen=set()
    try:
        _integer(duration_seconds,1,28800);_bounded(value);_keys(value,{'claims'})
        _require(type(value['claims']) is list and len(value['claims'])<=MAX_CLAIMS)
    except (ValueError,TypeError,RecursionError):
        return [],[dict(index=0,reason='FAILED_FORMAT'),dict(index=0,reason='NO_ACCEPTED_CLAIMS')]
    for index,item in enumerate(value['claims']):
        try:seconds=_timestamp(item.get('timestamp') if type(item) is dict else None)
        except ValueError:
            rejections.append(dict(index=index,reason='INVALID_TIMESTAMP'));continue
        if seconds>=duration_seconds:
            rejections.append(dict(index=index,reason='OUT_OF_RANGE_TIMESTAMP'));continue
        try:
            _model_claim(item,duration_seconds)
            claim=dict(deepcopy(item),timestamp_seconds=seconds,patch_range='UNKNOWN',measurement=None,
                limitations=['AI_SUMMARY_NOT_FACT_CHECKED','VIDEO_CONTEXT_REQUIRES_USER_REVIEW'],
                counterexamples=['COUNTEREXAMPLE_NOT_ESTABLISHED'])
            identity=_bounded(claim)
        except (ValueError,TypeError,KeyError):
            rejections.append(dict(index=index,reason='INVALID_CLAIM'));continue
        if identity in seen:rejections.append(dict(index=index,reason='DUPLICATE_CLAIM'));continue
        seen.add(identity);claims.append(claim)
    if not claims:
        rejections=rejections[:MAX_CLAIMS-1]+[dict(index=0,reason='NO_ACCEPTED_CLAIMS')]
    return claims,rejections

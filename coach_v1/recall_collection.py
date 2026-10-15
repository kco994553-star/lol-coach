"""Trusted acquisition adapters; private raw records never become public receipts.

The old anonymous power/reference aggregates omitted health and cannot be used
as recall evidence. Only original Match-V5 match/timeline pairs are extracted.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile

from .postgame_match import PostgameStore
from .pro_reference_cases import validate_public_directory
from .recall_stats import extract_match, build_dataset, validate_dataset
from .riot_collector import RiotCollector

POPULATIONS=('PRO_REFERENCE','CHALLENGER')
MAX_PRIVATE_RECORDS=2000
MAX_COLLECTION_LIMITS=dict(max_requests=650,max_matches=300,max_pages=1,
                           max_players=40,max_retries=2,deadline_seconds=900)
REASONS={None,'MISSING_API_KEY','INVALID_API_KEY_SHAPE','DEADLINE_EXHAUSTED',
         'REQUEST_BUDGET_EXHAUSTED','NETWORK_FAILURE','MALFORMED_RESPONSE',
         'UNAUTHORIZED_OR_EXPIRED_OR_UNSUPPORTED_PATH','RATE_LIMIT_EXHAUSTED',
         'RIOT_SERVER_FAILURE','HTTP_FAILURE','UNSUPPORTED_LEAGUE_IDENTITY'}


def reuse_private_cache(private_directory):
    """Read existing validated roster-participant envelopes, never accounts/lookups.

    Existing PostgameStore owns the raw shape, source and filesystem checks.
    Missing/corrupt caches are errors; no empty-cache recreation or network fallback.
    """
    root=Path(private_directory)
    directory=root/'private'/'matches'
    if not directory.is_dir():raise ValueError('PRIVATE_RECALL_CACHE_REQUIRED')
    store=PostgameStore(directory)
    paths=sorted(directory.glob('*.json'))
    if len(paths)>MAX_PRIVATE_RECORDS:raise ValueError('PRIVATE_RECALL_CACHE_LIMIT')
    clusters={};selected={}
    for path in paths:
        envelope,_,mh=store._load(path.stem)
        # _load rejects synthetic storage outside explicit PostgameStore test mode.
        if envelope['source']!='REAL':raise ValueError('REAL_PRIVATE_CACHE_REQUIRED')
        extracted=extract_match(envelope['match'],envelope['timeline'],population='PRO_REFERENCE',
                                participant_ids=[envelope['participant_id']])
        if mh not in clusters:
            clusters[mh]={key:value for key,value in extracted.items() if key!='participants'}
            selected[mh]={}
        if clusters[mh]!={key:value for key,value in extracted.items() if key!='participants'}:
            raise ValueError('INCONSISTENT_PRIVATE_MATCH_OBSERVATIONS')
        pid=envelope['participant_id']
        if len(extracted['participants'])!=1:raise ValueError('INVALID_SELECTED_PARTICIPANT')
        participant=extracted['participants'][0]
        if pid in selected[mh] and selected[mh][pid]!=participant:
            raise ValueError('CONFLICTING_PRIVATE_MATCH_OBSERVATIONS')
        selected[mh][pid]=participant
    observations=[dict(cluster,participants=[selected[mh][pid] for pid in sorted(selected[mh])])
                  for mh,cluster in sorted(clusters.items())]
    receipt=dict(status='EXTRACTED' if observations else 'INSUFFICIENT_DATA',reason=None,
                 population='PRO_REFERENCE',request_count=0,retry_count=0,
                 reused_private_records=len(paths),reused_unique_matches=len(clusters),
                 observed_http_status=None,limits=None,
                 selection='RECORDED_USER_ROSTER_PARTICIPANTS_NO_NEW_ACCOUNT_LOOKUPS')
    return observations,receipt


class RecallCollector(RiotCollector):
    """Consume the collector's existing raw pair stream, without refetching.

    The superclass validates queue/map/mode/patch before requesting timelines.
    Override only its response hook: extraction is private, and retained output
    contains anonymous observations. Rate limits/auth stops remain superclass code.
    """
    def __init__(self,*args,**kwargs):
        for key,maximum in MAX_COLLECTION_LIMITS.items():
            value=kwargs.get(key,maximum)
            if type(value) is not int or value>(maximum) or value<(0 if key=='max_retries' else 1):
                raise ValueError('RECALL_COLLECTION_LIMIT_EXCEEDED')
            kwargs[key]=value
        super().__init__(*args,**kwargs)
        self._recall_observations=[];self._pending_match=None

    def _get(self,url,method,**kwargs):
        payload,raw=super()._get(url,method,**kwargs)
        if method=='MATCH_V5_MATCH':self._pending_match=payload
        elif method=='MATCH_V5_TIMELINE':
            match=self._pending_match;self._pending_match=None
            if match is not None and payload is not None:
                self._recall_observations.append(extract_match(match,payload,population='CHALLENGER'))
        return payload,raw

    def collect_recall(self,*,patch,start_time=None,end_time=None):
        if not isinstance(patch,str) or re.fullmatch(r'\d{1,3}\.\d{1,3}',patch) is None:
            raise ValueError('EXACT_OFFICIAL_PATCH_REQUIRED')
        self._recall_observations=[];self._pending_match=None
        try:
            aggregate=super().collect(tier='CHALLENGER',patch=patch,start_time=start_time,
                                      end_time=end_time,collect_items=False)
        finally:self._pending_match=None
        collection=aggregate['source']['collection'];reason=collection['reason']
        receipt=dict(status='BLOCKED_EXTERNAL' if aggregate['status']=='BLOCKED_EXTERNAL' else
                     ('EXTRACTED' if self._recall_observations else 'INSUFFICIENT_DATA'),
                     reason=reason if reason in REASONS else 'UNKNOWN_COLLECTION_REASON',
                     population='CHALLENGER',request_count=self.requests,retry_count=self.retries,
                     reused_private_records=0,reused_unique_matches=0,
                     observed_http_status=collection['status_code'],limits=self.limits.copy(),
                     selection='CURRENT_CHALLENGER_SEED_MATCHES_NOT_VERIFIED_ALL_PARTICIPANT_RANKS')
        return self._recall_observations,receipt


def export_recall(directory,private_directory,observations,receipt,*,retrieved_at=None):
    """Strict dataset validator and fixed receipt fields are the public boundary."""
    population=receipt['population']
    if population not in POPULATIONS:raise ValueError('INVALID_RECALL_POPULATION')
    public=validate_public_directory(directory,private_directory)
    data=validate_dataset(build_dataset(observations,population=population,
        retrieved_at=retrieved_at or datetime.now(timezone.utc).isoformat()))
    # Never project caller-supplied extra fields, arbitrary error text or paths.
    safe={key:receipt[key] for key in ('status','reason','population','request_count','retry_count',
          'reused_private_records','reused_unique_matches','observed_http_status','limits','selection')}
    if safe['status'] not in ('EXTRACTED','INSUFFICIENT_DATA','BLOCKED_EXTERNAL') or safe['reason'] not in REASONS|{'UNKNOWN_COLLECTION_REASON'}:
        raise ValueError('INVALID_RECALL_RECEIPT')
    for key in ('request_count','retry_count','reused_private_records','reused_unique_matches'):
        if type(safe[key]) is not int or not 0<=safe[key]<=2000:raise ValueError('INVALID_RECALL_RECEIPT')
    if safe['observed_http_status'] is not None and (type(safe['observed_http_status']) is not int or not 100<=safe['observed_http_status']<=599):
        raise ValueError('INVALID_RECALL_RECEIPT')
    expected_selection=('RECORDED_USER_ROSTER_PARTICIPANTS_NO_NEW_ACCOUNT_LOOKUPS' if population=='PRO_REFERENCE' else
                        'CURRENT_CHALLENGER_SEED_MATCHES_NOT_VERIFIED_ALL_PARTICIPANT_RANKS')
    if safe['selection']!=expected_selection:raise ValueError('INVALID_RECALL_RECEIPT')
    limits=safe['limits']
    if population=='PRO_REFERENCE':
        if limits is not None or safe['request_count']!=0 or safe['retry_count']!=0:raise ValueError('INVALID_RECALL_RECEIPT')
    elif not isinstance(limits,dict) or set(limits)!=set(MAX_COLLECTION_LIMITS) or any(
            type(limits[k]) is not int or not (0 if k=='max_retries' else 1)<=limits[k]<=maximum
            for k,maximum in MAX_COLLECTION_LIMITS.items()):
        raise ValueError('INVALID_RECALL_RECEIPT')
    safe.update(schema_version='recall.collection-receipt.v1',dataset_status='HAS_OBSERVATIONS' if data['samples']['matches'] else 'INSUFFICIENT_DATA',
                dataset_samples=data['samples'],
                privacy='ANONYMOUS_DERIVED_ONLY',coaching_accuracy=None,
                health_availability='ONLY_EXPLICIT_RECEIVED_RAW_FRAME_HEALTH_FIELDS',
                source_kind='REAL',threshold_policy='OPERATIONAL_ANALYSIS_RULES_NOT_GAMEPLAY_ADVICE')
    public.mkdir(parents=True,exist_ok=True)
    for name,value in [('recall-data.json',data),('collection-receipt.json',safe)]:
        dest=public/name
        if dest.is_symlink():raise ValueError('UNSAFE_RECALL_OUTPUT')
        fd,tmp=tempfile.mkstemp(prefix='.recall-',dir=public)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:
                json.dump(value,stream,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)
                stream.write('\n')
            os.replace(tmp,dest)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    return safe

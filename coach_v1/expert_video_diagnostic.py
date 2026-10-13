"""Explicit one-shot video argument diagnosis; not expert claim acquisition.

The authorized baseline copies the literal official YouTube URL example,
substituting only the explicitly selected known free model.
Each additive stage has its own full-duration durable reservation. No retries,
alternative models, raw outputs, automatic approval or automatic resumption.
"""
from copy import deepcopy
from datetime import datetime, timezone
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from .api_diagnostics import safe_http_error
from .expert_collector import (ExpertCollector, FALLBACK_MODEL, CAP, CHARGE_WINDOW,
    MAX_DISPATCH_DELAY, MAX_VIDEO_SECONDS, RESPONSE_SCHEMA, _External, _NoRedirect,
    _canonical, _digest, _id, _int, _json, _keys, _require, _sha,
    validate_config, validate_entitlement_proof, validate_ledger)
from .expert_front_diagnostics import _bounded_process

MODEL=FALLBACK_MODEL
OFFICIAL_VIDEO_ID='9hE5-98ZeCg'
OFFICIAL_VIDEO_URL='https://www.youtube.com/watch?v='+OFFICIAL_VIDEO_ID
ENDPOINT='https://generativelanguage.googleapis.com/v1beta/interactions'
AUTHORIZATION='USER_PRO_REFERENCE_RESUME_2026-10-13'
STAGES=('BASELINE','CLIPPING','RESPONSE_FORMAT')
MIN_STAGE_SPACING=15
MAX_RESPONSE_BYTES=2_000_000
MAX_SANITIZED_MESSAGE_BYTES=32_000_000
SOURCE_URLS=('https://ai.google.dev/gemini-api/docs/video-understanding',
    'https://ai.google.dev/gemini-api/docs/structured-output',
    'https://ai.google.dev/api/interactions-api',
    'https://ai.google.dev/static/api/interactions.openapi.json')
PLAN_SCHEMA='expert.video-diagnostic-plan.v1'
RESULT_SCHEMA='expert.video-diagnostic-result.v1'
VIDEO_FIELDS={'id','url','duration_seconds','public_confirmed','metadata_checked_at'}
ERROR_FIELDS={'schema_version','provider','http_status','error_code','error_status','error_message',
    'message_complete','source_run_id','source_artifact_id','source_path','source_sha256','provenance',
    'raw_error_body_retained','recorded_before_new_attempt','authorization'}
STAGE_RECEIPT_FIELDS={'stage','status','http_status','request_count','request_sha256','reservation_id','checked_at'}
PLAN_FIELDS={'schema_version','status','reason','stage','session_id','created_at','video','authorization',
    'prior_error_receipt','prior_error_sha256','ledger','prior_ledger_sha256','ledger_sha256','reservation_id',
    'stage_receipts','request_sha256','model','api_route'}
RESULT_FIELDS={'schema_version','status','reason','stage','session_id','model','api_route','video',
    'authorization','prior_error_receipt','prior_error_sha256','ledger','ledger_sha256','checked_at',
    'next_not_before','stage_receipts','request_count','error','localized_change','exact_invalid_field',
    'manual_summary_default','automatic_collection_paused','accepted_claims','coaching_accuracy'}
RESULT_REASONS={'RESERVATION_PERSISTENCE_NOT_CONFIRMED','DISPATCH_ALREADY_CLAIMED','PROVIDER_HTTP_FAILURE',
    'NETWORK_TIMEOUT','NETWORK_FAILURE','MALFORMED_OR_INCOMPLETE_RESPONSE','DOCUMENTED_PAID_ENTITLEMENT_REQUIRED',
    'FREE_PROJECT_OR_ENTITLEMENT_UNVERIFIED','KNOWN_PAID_PROJECT','MISSING_API_KEYS'}


def sanitize_complete_message(value,*,secrets=(),identifiers=()):
    """Redact in full; never take a substring of a provider message."""
    if not isinstance(value,str) or not value:return None
    variants=set()
    for secret in secrets:
        if isinstance(secret,str) and secret:
            for s in (secret,secret.strip()):
                if s:variants.update((s,urllib.parse.quote(s,safe=''),urllib.parse.quote_plus(s,safe='')))
    for secret in sorted(variants,key=len,reverse=True):value=value.replace(secret,'[REDACTED_KEY]')
    for identifier in sorted((s for s in identifiers if isinstance(s,str) and s),key=len,reverse=True):
        replacement='[REDACTED_URL]' if identifier.startswith(('https://','http://')) else '[REDACTED_IDENTIFIER]'
        for variant in (identifier,urllib.parse.quote(identifier,safe=''),urllib.parse.quote_plus(identifier)):
            value=value.replace(variant,replacement)
    value=re.sub(r'https?://[^\s<>"\']+','[REDACTED_URL]',value,flags=re.I)
    value=re.sub(r'RGAPI-[A-Za-z0-9_-]+|AIza[A-Za-z0-9_-]+','[REDACTED_KEY]',value)
    value=re.sub(r'(?i)\bauthorization\s*[:=]\s*["\']?(?:Bearer|Basic)\s+[^\s,"\';]+','[REDACTED_CREDENTIAL]',value)
    value=re.sub(r'(?i)\b(?:api[_ -]?key|x-goog-api-key|x-riot-token|authorization|key)\s*[:=]\s*["\']?[^\s,"\';]+','[REDACTED_CREDENTIAL]',value)
    value=re.sub(r'(?i)(["\']?\b(?:puuid|summoner[_ -]?(?:id|name)|account[_ -]?id|project[_ -]?(?:id|number)|gameName|tagLine|riot[_ -]?id)["\']?\s*[:=]\s*)(?:"[^"\n]*"|\'[^\'\n]*\'|[^\s,}\]<]+)',lambda m:m[1]+'"[REDACTED_IDENTIFIER]"',value)
    value=re.sub(r'\b(?:projects|users|accounts)/[^\s/"\']+','[REDACTED_RESOURCE]',value,flags=re.I)
    value=re.sub(r'[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}','[REDACTED_IDENTIFIER]',value)
    value=re.sub(r'[\w.\-]{1,64}#[\w.\-]{1,16}','[REDACTED_IDENTIFIER]',value)
    value=re.sub(r'[A-Za-z0-9_-]{40,}','[REDACTED_IDENTIFIER]',value)
    return re.sub(r'[\x00-\x1f\x7f]',' ',value)


def complete_error_receipt(http_status,body,*,source_run_id=None,source_artifact_id=None,secrets=(),identifiers=()):
    """Select the COMPLETE error.message; unreadable/oversize is unavailable.

    A bounded body is never mistaken for a complete message after truncation.
    The receipt keeps no body, raw-body hash, response details or output text.
    """
    message=None;safe=dict(http_status=http_status,error_code=None,error_status=None)
    try:
        if isinstance(body,(str,bytes)):
            _require(len(body)<=MAX_RESPONSE_BYTES);body=_json(body)
        _require(isinstance(body,dict) and len(_canonical(body).encode())<=MAX_RESPONSE_BYTES)
        error=body.get('error');_require(isinstance(error,dict))
        safe=safe_http_error('GEMINI',http_status,body,secrets=secrets)
        message=sanitize_complete_message(error.get('message'),secrets=secrets,identifiers=identifiers)
    except (ValueError,TypeError,UnicodeError,RecursionError,OverflowError):pass
    return dict(schema_version='expert.complete-error.v1',provider='GEMINI',
        http_status=safe.get('http_status'),error_code=safe.get('error_code'),error_status=safe.get('error_status'),
        error_message=message,message_complete=message is not None,
        source_run_id=source_run_id,source_artifact_id=source_artifact_id,source_path=None,source_sha256=None,
        provenance='COMPLETE_SANITIZED_ERROR_MESSAGE' if message is not None else 'ERROR_MESSAGE_UNAVAILABLE',
        raw_error_body_retained=False,recorded_before_new_attempt=True,authorization=AUTHORIZATION)


def validate_complete_error(receipt,*,prior=False):
    r=deepcopy(receipt);_keys(r,ERROR_FIELDS)
    _require(r['schema_version']=='expert.complete-error.v1' and r['provider']=='GEMINI')
    _require(r['http_status'] is None or type(r['http_status']) is int and 100<=r['http_status']<=599)
    for key in ('source_run_id','source_artifact_id'):_require(r[key] is None or _int(r[key],1))
    _require(r['source_sha256'] is None or _sha(r['source_sha256']))
    _require(r['source_path'] is None or isinstance(r['source_path'],str) and re.fullmatch(r'[A-Za-z0-9_./-]{1,300}',r['source_path']))
    _require(r['provenance'] in ('PRIOR_SAFE_DIAGNOSTIC_MESSAGE_SHORTER_THAN_512_CHAR_LIMIT_NO_TRUNCATION',
        'COMPLETE_SANITIZED_ERROR_MESSAGE','ERROR_MESSAGE_UNAVAILABLE'))
    _require(r['raw_error_body_retained'] is False and r['recorded_before_new_attempt'] is True)
    _require(r['authorization']==AUTHORIZATION and type(r['message_complete']) is bool)
    message=r['error_message']
    _require(message is None or isinstance(message,str) and len(message.encode())<=MAX_SANITIZED_MESSAGE_BYTES and sanitize_complete_message(message)==message)
    _require(r['message_complete']==(message is not None))
    _require(r['error_code'] is None or type(r['error_code']) is int and 0<=r['error_code']<=999 or
        isinstance(r['error_code'],str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}',r['error_code']))
    _require(r['error_status'] is None or isinstance(r['error_status'],str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}',r['error_status']))
    if prior:_require(r['message_complete'] and r['http_status']==400 and r['source_run_id'] is not None and r['source_artifact_id'] is not None)
    return r


def _video(value,now,*,fresh=True):
    v=deepcopy(value);_keys(v,VIDEO_FIELDS)
    _require(v['id']==OFFICIAL_VIDEO_ID and v['url']==OFFICIAL_VIDEO_URL)
    _require(_int(v['duration_seconds'],1) and v['duration_seconds']<=MAX_VIDEO_SECONDS)
    _require(v['public_confirmed'] is True and _int(v['metadata_checked_at']) and v['metadata_checked_at']<=now)
    if fresh:_require(now-v['metadata_checked_at']<=MAX_DISPATCH_DELAY)
    return v


def stage_body(stage,video):
    _require(stage in STAGES)
    _require(video['id']==OFFICIAL_VIDEO_ID and video['url']==OFFICIAL_VIDEO_URL)
    body=dict(model=MODEL,input=[dict(type='text',text='Please summarize the video in 3 sentences.'),
        dict(type='video',uri=OFFICIAL_VIDEO_URL)])
    if stage!='BASELINE':body['input'][1]['processing']=dict(type='static',start_offset='0s',
        end_offset=str(min(600,video['duration_seconds']))+'s')
    if stage=='RESPONSE_FORMAT':body['response_format']=dict(type='text',mime_type='application/json',schema=deepcopy(RESPONSE_SCHEMA))
    return body


def _reservation_payload(plan):
    return {key:plan[key] for key in ('stage','session_id','created_at','video','authorization','prior_error_sha256',
        'prior_ledger_sha256','stage_receipts','request_sha256','model','api_route')}


def validate_stage_result(value):
    r=deepcopy(value);_keys(r,RESULT_FIELDS)
    _require(r['schema_version']==RESULT_SCHEMA and r['stage'] in STAGES and r['status'] in ('READY','BLOCKED_EXTERNAL'))
    _require(r['model']==MODEL and r['api_route']=='INTERACTIONS' and r['authorization']==AUTHORIZATION)
    _require(_sha(r['session_id']) and _sha(r['prior_error_sha256']) and _int(r['checked_at']))
    _video(r['video'],r['checked_at'],fresh=False)
    validate_complete_error(r['prior_error_receipt'],prior=True)
    _require(_digest(r['prior_error_receipt'])==r['prior_error_sha256'])
    valid=validate_ledger(r['ledger'],r['checked_at']);_require(_digest(valid)==r['ledger_sha256'])
    rows=r['stage_receipts'];_require(isinstance(rows,list) and len(rows)==STAGES.index(r['stage'])+1)
    for i,row in enumerate(rows):
        _keys(row,STAGE_RECEIPT_FIELDS);_require(row['stage']==STAGES[i])
        _require(row['status'] in ('READY','BLOCKED_EXTERNAL'))
        if i<len(rows)-1:_require(row['status']=='READY')
        _require(type(row['request_count']) is int and row['request_count'] in (0,1))
        _require(row['http_status'] is None or type(row['http_status']) is int and 100<=row['http_status']<=599)
        _require(_sha(row['reservation_id']) and row['request_sha256']==_digest(stage_body(row['stage'],r['video'])))
        _require(_int(row['checked_at']) and row['checked_at']<=r['checked_at'])
        matches=[v for v in valid['reservations'] if v['reservation_id']==row['reservation_id']]
        _require(len(matches)==1 and matches[0]['video_id']==r['video']['id'] and matches[0]['seconds']==r['video']['duration_seconds'])
        if row['status']=='READY':_require(row['request_count']==1 and row['http_status']==200)
        if row['request_count']==0:_require(row['http_status'] is None)
    _require(type(r['request_count']) is int and r['request_count']==sum(row['request_count'] for row in rows) and r['request_count']<=3)
    _require(r['status']==rows[-1]['status'])
    _require(r['next_not_before']==r['checked_at']+MIN_STAGE_SPACING)
    _require(r['manual_summary_default'] is True and r['automatic_collection_paused'] is True)
    _require(r['accepted_claims']==0 and type(r['accepted_claims']) is int and r['coaching_accuracy'] is None and r['exact_invalid_field'] is None)
    _require(r['localized_change'] in (None,'VIDEO_PROCESSING','RESPONSE_FORMAT'))
    if r['error'] is not None:validate_complete_error(r['error'])
    if r['status']=='READY':_require(r['reason'] is None and r['error'] is None and r['localized_change'] is None)
    else:_require(r['reason'] in RESULT_REASONS)
    return r


def _video_transport(method,url,headers,body,timeout,max_bytes):
    _require(method=='POST' and url==ENDPOINT and timeout==600 and max_bytes==MAX_RESPONSE_BYTES)
    request=urllib.request.Request(url,data=_canonical(body).encode(),headers=headers,method=method)
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request,timeout=timeout) as response:
            return response.status,{},response.read(max_bytes+1)
    except urllib.error.HTTPError as error:
        try:return error.code,{},error.read(max_bytes+1)
        finally:error.close()


def _transport(method,url,headers,body,timeout,max_bytes):
    program=('import json,sys; from coach_v1.expert_video_diagnostic import _video_transport; '
        'a=json.load(sys.stdin); code,headers,body=_video_transport(**a); '
        'sys.stdout.buffer.write(str(code).encode()+b"\\n"+body)')
    code,wire=_bounded_process((sys.executable,'-c',program),_canonical(dict(method=method,url=url,headers=headers,
        body=body,timeout=timeout,max_bytes=max_bytes)).encode(),timeout,max_bytes+64)
    if code:raise OSError()
    literal,raw=wire.split(b'\n',1)
    return int(literal),{},raw


def _successful_output(response,stage,duration):
    _require(isinstance(response,dict) and response.get('status')=='completed' and not response.get('errors'))
    steps=response.get('steps');_require(isinstance(steps,list) and bool(steps))
    outputs=[s for s in steps if isinstance(s,dict) and s.get('type')=='model_output']
    _require(len(outputs)==1 and outputs[0] is steps[-1] and not outputs[0].get('error'))
    content=outputs[0].get('content');_require(isinstance(content,list) and bool(content))
    _require(all(isinstance(p,dict) and p.get('type')=='text' and isinstance(p.get('text'),str) for p in content))
    text=''.join(p['text'] for p in content);_require(bool(text.strip()))
    if stage=='RESPONSE_FORMAT':
        from .expert_contract import normalize_gemini_claims
        decoded=_json(text);_,rejected=normalize_gemini_claims(decoded,duration)
        _require(all(r['reason'] in ('NO_ACCEPTED_CLAIMS','DUPLICATE_CLAIM') for r in rejected))


class ExpertVideoDiagnostic:
    def __init__(self,*,gemini_api_key=None,youtube_api_key=None,policy,entitlement_proof,
                 transport=None,clock=None,claim_dispatch=None,source_run_id=None):
        self.clock=clock or time.time;self.transport=transport or _transport
        self.gemini_key=gemini_api_key;self.youtube_key=youtube_api_key
        self.proof=validate_entitlement_proof(entitlement_proof,MODEL)
        self.policy=deepcopy(policy);self.claim_dispatch=claim_dispatch;self.claimed=set();self.source_run_id=source_run_id
        self.metadata_collector=ExpertCollector(model=MODEL,gemini_api_key=gemini_api_key,youtube_api_key=youtube_api_key,
            policy=policy,clock=self.clock,max_requests=50-len(STAGES))

    def _gate(self):
        today=datetime.fromtimestamp(self.clock(),timezone.utc).date().isoformat()
        if self.proof['status']=='PAID_REQUIRED':raise _External('DOCUMENTED_PAID_ENTITLEMENT_REQUIRED')
        if self.proof['status']!='VERIFIED_FREE' or self.proof['checked_at']!=today:raise _External('FREE_PROJECT_OR_ENTITLEMENT_UNVERIFIED')
        self.metadata_collector._gate()

    def discover(self,config,ledger,prior_error_receipt):
        now=int(self.clock());valid=validate_ledger(ledger,now)
        receipt=dict(status='BLOCKED_EXTERNAL',reason=None,video=None,metadata_request_count=0)
        try:
            validate_complete_error(prior_error_receipt,prior=True);self._gate()
            validate_config(config)  # Retained CLI contract; channels never substitute the example.
            if OFFICIAL_VIDEO_ID in valid['processed_video_ids'] or any(r['video_id']==OFFICIAL_VIDEO_ID for r in valid['reservations']):
                raise _External('VIDEO_ALREADY_CHARGED')
            data=self.metadata_collector._youtube('videos',part='snippet,contentDetails,status',id=OFFICIAL_VIDEO_ID)
            items=data.get('items');_require(isinstance(items,list) and len(items)==1)
            item=items[0];_require(isinstance(item,dict) and item.get('id')==OFFICIAL_VIDEO_ID)
            status=item['status'];snippet=item['snippet']
            if status.get('privacyStatus')!='public' or status.get('uploadStatus')!='processed' or snippet.get('liveBroadcastContent','none')!='none':
                raise _External('OFFICIAL_EXAMPLE_NOT_PUBLIC_PROCESSED_VIDEO')
            duration=item['contentDetails']['duration'];_require(isinstance(duration,str))
            match=re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',duration);_require(match is not None)
            seconds=sum(int(x or 0)*scale for x,scale in zip(match.groups(),(3600,60,1)))
            selected=_video(dict(id=OFFICIAL_VIDEO_ID,url=OFFICIAL_VIDEO_URL,duration_seconds=seconds,
                public_confirmed=True,metadata_checked_at=int(self.clock())),int(self.clock()))
            receipt.update(status='SELECTED',video=selected)
        except _External as error:receipt['reason']=error.reason
        except (ValueError,TypeError,KeyError):receipt['reason']='PRIOR_COMPLETE_ERROR_OR_METADATA_UNAVAILABLE'
        receipt['metadata_request_count']=self.metadata_collector.request_count
        return receipt

    def prepare_stage(self,video,ledger,prior_error_receipt,*,authorization,previous_result=None,stage=None):
        now=int(self.clock());valid=validate_ledger(ledger,now)
        plan=dict(schema_version=PLAN_SCHEMA,status='BLOCKED_EXTERNAL',reason=None,stage=stage or 'BASELINE',session_id=None,
            created_at=now,video=None,authorization=AUTHORIZATION,prior_error_receipt=None,prior_error_sha256=None,
            ledger=valid,prior_ledger_sha256=_digest(valid),ledger_sha256=_digest(valid),reservation_id=None,
            stage_receipts=[],request_sha256=None,model=MODEL,api_route='INTERACTIONS')
        try:
            if authorization!=AUTHORIZATION:raise _External('DIAGNOSTIC_AUTHORIZATION_MISSING')
            prior=validate_complete_error(prior_error_receipt,prior=True);self._gate()
            v=_video(video,now,fresh=previous_result is None);rows=[]
            if previous_result is None:
                target='BASELINE'
                if v['id'] in valid['processed_video_ids'] or any(r['video_id']==v['id'] for r in valid['reservations']):raise _External('VIDEO_ALREADY_CHARGED')
                session=_digest(dict(video=v,prior_error_sha256=_digest(prior),authorization=AUTHORIZATION,prior_ledger_sha256=_digest(valid)))
            else:
                previous=validate_stage_result(previous_result)
                if previous['status']!='READY':raise _External('PREVIOUS_STAGE_FAILED')
                index=STAGES.index(previous['stage'])+1
                if index==len(STAGES):raise _External('ALL_AUTHORIZED_STAGES_FINISHED')
                target=STAGES[index];session=previous['session_id'];rows=previous['stage_receipts']
                _require(v==previous['video'] and valid==previous['ledger'] and _digest(prior)==previous['prior_error_sha256'])
                same=[r['reservation_id'] for r in valid['reservations'] if r['video_id']==v['id']]
                _require(set(same)=={r['reservation_id'] for r in rows} and v['id'] not in valid['processed_video_ids'])
                if now<previous['next_not_before']:raise _External('STAGE_RATE_WINDOW')
            _require(stage is None or stage==target)
            if sum(r['seconds'] for r in valid['reservations'] if r['reserved_at']>now-CHARGE_WINDOW)+v['duration_seconds']>CAP:raise _External('ROLLING_VIDEO_BUDGET_EXHAUSTED')
            plan.update(stage=target,session_id=session,video=v,prior_error_receipt=prior,prior_error_sha256=_digest(prior),
                stage_receipts=rows,request_sha256=_digest(stage_body(target,v)))
            reservation=_digest(_reservation_payload(plan))
            valid['reservations'].append(dict(video_id=v['id'],seconds=v['duration_seconds'],reserved_at=now,reservation_id=reservation))
            plan.update(status='RESERVED',reservation_id=reservation,ledger=validate_ledger(valid,now),ledger_sha256=_digest(valid))
        except _External as error:plan['reason']=error.reason
        except (ValueError,TypeError,KeyError):plan['reason']='INVALID_DIAGNOSTIC_STATE_OR_PRIOR_COMPLETE_ERROR'
        return plan

    def process_stage(self,plan,*,reservation_artifact_id=None):
        _keys(plan,PLAN_FIELDS);_require(plan['schema_version']==PLAN_SCHEMA and plan['status']=='RESERVED')
        now=int(self.clock());ledger=validate_ledger(plan['ledger'],now)
        _require(plan['model']==MODEL and plan['api_route']=='INTERACTIONS' and plan['authorization']==AUTHORIZATION)
        _require(plan['stage'] in STAGES and _sha(plan['session_id']) and _digest(ledger)==plan['ledger_sha256'])
        _require(_int(plan['created_at']) and 0<=now-plan['created_at']<=MAX_DISPATCH_DELAY)
        prior=validate_complete_error(plan['prior_error_receipt'],prior=True);_require(_digest(prior)==plan['prior_error_sha256'])
        v=_video(plan['video'],now,fresh=plan['stage']=='BASELINE');body=stage_body(plan['stage'],v)
        _require(_digest(body)==plan['request_sha256'] and _digest(_reservation_payload(plan))==plan['reservation_id'])
        current=[r for r in ledger['reservations'] if r['reservation_id']==plan['reservation_id']]
        _require(len(current)==1 and current[0]['video_id']==v['id'] and current[0]['seconds']==v['duration_seconds'] and current[0]['reserved_at']==plan['created_at'])
        old=deepcopy(ledger);old['reservations']=[r for r in old['reservations'] if r['reservation_id']!=plan['reservation_id']]
        _require(_digest(old)==plan['prior_ledger_sha256'])
        rows=deepcopy(plan['stage_receipts']);_require(len(rows)==STAGES.index(plan['stage']))
        for i,row in enumerate(rows):
            _keys(row,STAGE_RECEIPT_FIELDS);_require(row['stage']==STAGES[i] and row['status']=='READY' and row['http_status']==200 and row['request_count']==1)
        reason=None;status='BLOCKED_EXTERNAL';http_status=None;error=None;attempts=0
        try:
            self._gate()
            if not isinstance(reservation_artifact_id,str) or re.fullmatch(r'[1-9][0-9]*',reservation_artifact_id) is None:raise _External('RESERVATION_PERSISTENCE_NOT_CONFIRMED')
            if plan['reservation_id'] in self.claimed:raise _External('DISPATCH_ALREADY_CLAIMED')
            if self.claim_dispatch is not None:
                try:self.claim_dispatch(plan)
                except FileExistsError:raise _External('DISPATCH_ALREADY_CLAIMED') from None
            self.claimed.add(plan['reservation_id']);attempts=1
            http_status,_,raw=self.transport('POST',ENDPOINT,{'x-goog-api-key':self.gemini_key,'Content-Type':'application/json'},body,600,MAX_RESPONSE_BYTES)
            _require(type(http_status) is int and 100<=http_status<=599)
            if http_status!=200:
                error=complete_error_receipt(http_status,raw,source_run_id=self.source_run_id,
                    secrets=(self.gemini_key,self.youtube_key),identifiers=(v['id'],v['url']))
                raise _External('PROVIDER_HTTP_FAILURE')
            if isinstance(raw,dict):_require(len(_canonical(raw).encode())<=MAX_RESPONSE_BYTES);decoded=raw
            else:_require(isinstance(raw,(bytes,str)) and len(raw)<=MAX_RESPONSE_BYTES);decoded=_json(raw)
            _successful_output(decoded,plan['stage'],v['duration_seconds']);status='READY'
        except _External as e:reason=e.reason
        except TimeoutError:reason='NETWORK_TIMEOUT'
        except urllib.error.URLError as e:reason='NETWORK_TIMEOUT' if isinstance(e.reason,TimeoutError) else 'NETWORK_FAILURE'
        except (ValueError,TypeError,KeyError,UnicodeError,RecursionError,OverflowError):reason='MALFORMED_OR_INCOMPLETE_RESPONSE'
        except Exception:reason='NETWORK_FAILURE'
        checked=int(self.clock())
        rows.append(dict(stage=plan['stage'],status=status,http_status=http_status,request_count=attempts,
            request_sha256=plan['request_sha256'],reservation_id=plan['reservation_id'],checked_at=checked))
        result=dict(schema_version=RESULT_SCHEMA,status=status,reason=reason,stage=plan['stage'],session_id=plan['session_id'],model=MODEL,
            api_route='INTERACTIONS',video=v,authorization=AUTHORIZATION,prior_error_receipt=prior,prior_error_sha256=plan['prior_error_sha256'],
            ledger=ledger,ledger_sha256=_digest(ledger),checked_at=checked,next_not_before=checked+MIN_STAGE_SPACING,
            stage_receipts=rows,request_count=sum(r['request_count'] for r in rows),error=error,
            localized_change=('VIDEO_PROCESSING' if plan['stage']=='CLIPPING' else 'RESPONSE_FORMAT') if http_status==400 and rows[:-1] else None,
            exact_invalid_field=None,manual_summary_default=True,automatic_collection_paused=True,accepted_claims=0,coaching_accuracy=None)
        return validate_stage_result(result)

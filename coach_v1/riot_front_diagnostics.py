"""One curl and one Python GET; status comparison, never a causal UA claim.

Credentials enter curl through stdin configuration only. Body/header bytes are
bounded transient memory and are reduced to sanitized observations. The pair
intentionally finishes both clients after an auth failure; collection is gated
separately on both literal statuses200. request_count counts client attempts,
not proof that a network-failed attempt reached Riot.
"""
from copy import deepcopy
import json
import os
import re
import selectors
import subprocess
import time
from urllib.error import HTTPError
from urllib.request import Request,build_opener
from urllib.parse import quote,quote_plus

from .api_diagnostics import MAX_ERROR_BYTES,inspect_riot_key,safe_http_error
from .riot_collector import RIOT_USER_AGENT,_RejectRedirect

CHALLENGER_URL='https://kr.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5'
CURL_COMMAND=('curl','--disable','--config','-')
MAX_HEADER_BYTES=16384
MARKERS=('cf-ray','cf-cache-status','cf-mitigated','x-sucuri-block','x-sucuri-id','x-akamai-transformed')
OBSERVATION_FIELDS={'http_status','headers_content_type','headers_server','markers','is_json','body_prefix','error_message','reason'}
SHAPE_FIELDS={'raw_length','normalized_length','raw_has_prefix','normalized_has_prefix','has_outer_whitespace','contains_line_break','valid_shape'}
JSON_TOKEN=re.compile(r'(?<!\\)"(?:[^"\\]|\\.)*"|[{}\[\]:,]|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?|\b(?:true|false|null)\b')


def _require(condition):
    if not condition:raise ValueError('invalid Riot front receipt')


def _safe_text(value,maximum,secrets=()):
    if not isinstance(value,str):return None
    variants=set()
    for secret in secrets:
        if isinstance(secret,str) and secret:
            for candidate in (secret,secret.strip()):
                if candidate:variants.update((candidate,quote(candidate,safe=''),quote_plus(candidate,safe='')))
    for secret in sorted(variants,key=len,reverse=True):value=value.replace(secret,'[REDACTED_KEY]')
    # Redact identifiers before any truncation, including JSON and incomplete
    # JSON assignments. Broad token redaction favors privacy over completeness.
    value=re.sub(r'(?i)(["\']?\b(?:puuid|summoner[_ -]?(?:id|name)|account[_ -]?id|encrypted[_ -]?(?:summoner|account)[_ -]?id|riot[_ -]?id(?:GameName|Tagline)?|gameName|tagLine|id|name)["\']?\s*[:=]\s*)(?:"[^"\n]*"|\'[^\'\n]*\'|[^\s,}\]<]+)',
                 lambda m:m.group(1)+'"[REDACTED_IDENTIFIER]"',value)
    value=re.sub(r'[\w.\-]{1,64}#[\w.\-]{1,16}','[REDACTED_RIOT_ID]',value)
    value=re.sub(r'[A-Za-z0-9_-]{24,}','[REDACTED_IDENTIFIER]',value)
    selected=safe_http_error('RIOT',403,{'status':{'message':value}},secrets=secrets)['error_message']
    return selected[:maximum] if selected is not None else None


def _redact_json_strings(text,secrets=()):
    """Preserve original token order/whitespace; withhold unrelated values."""
    frames=[];parts=[];end=0
    for match in JSON_TOKEN.finditer(text):
        token=match.group();replacement=token
        if token.startswith('"'):
            try:value=json.loads(token)
            except ValueError:value=None
            is_key=text[match.end():].lstrip().startswith(':')
            if is_key:
                if frames:frames[-1]['key']=value
                sanitized=_safe_text(value,512,secrets)
                if sanitized!=value:replacement=json.dumps(sanitized,ensure_ascii=False)
            else:
                path=frames[-1]['path']+(frames[-1]['key'],) if frames and frames[-1]['kind']=='{' else ()
                if path==('status','message'):replacement=json.dumps(_safe_text(value,512,secrets),ensure_ascii=False)
                elif value not in ('[REDACTED_VALUE]','[REDACTED_IDENTIFIER]','[REDACTED_KEY]','[REDACTED_RIOT_ID]'):
                    replacement='"[REDACTED_VALUE]"'
                if frames:frames[-1]['key']=None
        elif token in ('{','['):
            path=frames[-1]['path']+(frames[-1]['key'],) if frames and frames[-1]['kind']=='{' else ('ARRAY',) if frames else ()
            if frames:frames[-1]['key']=None
            frames.append(dict(kind=token,path=path,key=None))
        elif token in ('}',']'):
            if frames:frames.pop()
        elif token==',' and frames:frames[-1]['key']=None
        elif token!=':':
            path=frames[-1]['path']+(frames[-1]['key'],) if frames and frames[-1]['kind']=='{' else ()
            if path!=('status','status_code') or not re.fullmatch(r'[1-5][0-9]{2}',token):
                replacement='"[REDACTED_VALUE]"'
            if frames:frames[-1]['key']=None
        parts.append(text[end:match.start()]);parts.append(replacement);end=match.end()
    parts.append(text[end:]);return ''.join(parts)


def safe_403_observation(headers,body,status=403,*,secrets=(),complete=True):
    """Safe observation for any response; exported for collector403 handling."""
    code=status if type(status) is int and 100<=status<=599 else None
    if code!=403:
        return dict(http_status=code,headers_content_type=None,headers_server=None,markers={name:False for name in MARKERS},
            is_json=None,body_prefix=None,error_message=None,reason='NETWORK_FAILURE' if code is None else None)
    h={key.lower():value for key,value in headers.items() if isinstance(key,str)} if isinstance(headers,dict) else {}
    text=None;is_json=None;selected_message=None
    if isinstance(body,(bytes,str)):
        raw=body.encode('utf-8') if isinstance(body,str) else body
        oversized=len(raw)>MAX_ERROR_BYTES
        text=raw[:MAX_ERROR_BYTES].decode('utf-8',errors='replace')
        if complete and not oversized:
            try:
                def reject(_):raise ValueError('nonfinite JSON')
                decoded=json.loads(raw,parse_constant=reject);is_json=True
                error=decoded.get('status') if isinstance(decoded,dict) else None
                if isinstance(error,dict):selected_message=_safe_text(error.get('message'),512,secrets)
                # Preserve the original JSON token sequence and whitespace.
                # Only actual status.message string values remain descriptive;
                # unrelated string values are replaced before prefix truncation.
                text=_redact_json_strings(text,secrets)
            except (ValueError,TypeError,UnicodeError,RecursionError,OverflowError):is_json=False
        if is_json is not True and text.lstrip().startswith(('{','[')):
            text=None
    prefix=text[:100] if is_json is True else _safe_text(text,100,secrets)
    return dict(http_status=code,headers_content_type=_safe_text(h.get('content-type'),128,secrets),
        headers_server=_safe_text(h.get('server'),128,secrets),markers={name:name in h for name in MARKERS},
        is_json=is_json,body_prefix=prefix,error_message=selected_message,
        reason='NETWORK_FAILURE' if code is None else None)


def _read_python_response(response,status,max_bytes):
    try:body=response.read(max_bytes+1)
    except (OSError,TimeoutError):return status,dict(response.headers),None,False
    return status,dict(response.headers),body[:max_bytes],len(body)<=max_bytes


def _python_transport(url,headers,timeout,max_bytes):
    try:
        with build_opener(_RejectRedirect()).open(Request(url,headers=headers),timeout=timeout) as response:
            return _read_python_response(response,response.status,max_bytes)
    except HTTPError as error:
        try:return _read_python_response(error,error.code,max_bytes)
        finally:error.close()


def _curl_config(url,headers,timeout):
    _require(url==CHALLENGER_URL and inspect_riot_key(headers.get('X-Riot-Token'))[0]==headers.get('X-Riot-Token'))
    _require(headers.get('User-Agent')==RIOT_USER_AGENT and type(timeout) is int and 1<=timeout<=60)
    return '\n'.join(('url = "'+url+'"','request = "GET"','header = "X-Riot-Token: '+headers['X-Riot-Token']+'"',
        'header = "Accept: application/json"','user-agent = "'+RIOT_USER_AGENT+'"','include',
        'silent','proto = "=https"','max-redirs = 0','max-time = '+str(timeout),
        'connect-timeout = '+str(timeout),'max-filesize = '+str(MAX_ERROR_BYTES),'output = "-"',
        'write-out = "\\nRIOT_CURL_HTTP_STATUS:%{http_code}\\n"'))+'\n'


def _parse_curl_output(wire,complete,max_bytes,*,status_hint=None):
    _require(isinstance(wire,bytes) and type(complete) is bool)
    rest=wire;status=None;headers={};header_bytes=0
    while rest.startswith(b'HTTP/'):
        boundary=rest.find(b'\r\n\r\n');separator=4
        if boundary<0:boundary=rest.find(b'\n\n');separator=2
        line=rest.split(b'\n',1)[0].rstrip(b'\r')
        match=re.fullmatch(rb'HTTP/[0-9.]+ ([1-5][0-9]{2})(?: .*|)',line)
        if match is None:return None,{},None,False
        status=int(match.group(1));proxy=b'connection established' in line.lower()
        if boundary<0 or header_bytes+boundary+separator>MAX_HEADER_BYTES:
            return (None if proxy or status<200 else status),{},None,False
        block=rest[:boundary];header_bytes+=boundary+separator;rest=rest[boundary+separator:]
        headers={}
        for header in block.splitlines()[1:]:
            if b':' in header:
                key,value=header.split(b':',1);headers[key.decode('ascii',errors='ignore').strip().lower()]=value.decode('utf-8',errors='replace').strip()
        if proxy or status<200:
            status=None;headers={}
            if not rest.startswith(b'HTTP/'):return None,{},None,False
            continue
        # Only CONNECT/informational blocks precede another HTTP header. A
        # final response body resembling HTTP cannot replace its literal code.
        break
    if status is None:return status_hint,{},None,False
    return status,headers,rest[:max_bytes],complete and len(rest)<=max_bytes


def _curl_transport(url,headers,timeout,max_bytes):
    configuration=_curl_config(url,headers,timeout).encode()
    process=subprocess.Popen(CURL_COMMAND,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    wire=bytearray();complete=True;maximum=max_bytes+MAX_HEADER_BYTES
    try:
        process.stdin.write(configuration);process.stdin.close()
        deadline=time.monotonic()+timeout+2
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout,selectors.EVENT_READ)
            while True:
                remaining=deadline-time.monotonic()
                if remaining<=0:complete=False;break
                if not selector.select(timeout=min(remaining,1)):continue
                chunk=os.read(process.stdout.fileno(),min(16384,maximum+1-len(wire)))
                if not chunk:break
                wire.extend(chunk)
                if len(wire)>maximum:complete=False;break
        if not complete:process.kill()
        code=process.wait(timeout=2)
        raw=bytes(wire);hint=None
        # curl emits its own final write-out even when max-filesize rejects a
        # response before include headers are written. Trust it only after EOF;
        # a killed/truncated response body cannot forge this trailer.
        if complete:
            trailer=re.search(rb'\nRIOT_CURL_HTTP_STATUS:([0-9]{3})\n$',raw)
            if trailer:
                literal=int(trailer.group(1));hint=literal if 100<=literal<=599 else None
                raw=raw[:trailer.start()]
        return _parse_curl_output(raw,complete and code==0,max_bytes,status_hint=hint)
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=2)
        process.stdout.close()
        if not process.stdin.closed:process.stdin.close()


def diagnose_riot_front(api_key=None,*,curl_transport=None,python_transport=None,timeout=20):
    _require(type(timeout) is int and 1<=timeout<=60)
    raw=api_key if api_key is not None else os.environ.get('RIOT_API_KEY')
    key,shape=inspect_riot_key(raw)
    observations={name:safe_403_observation({},None,None,complete=False) for name in ('curl','python')}
    if key is None:
        for observation in observations.values():observation['reason']=None
    if key is not None:
        headers={'Accept':'application/json','X-Riot-Token':key,'User-Agent':RIOT_USER_AGENT}
        for name,transport in (('curl',curl_transport or _curl_transport),('python',python_transport or _python_transport)):
            try:
                status,h,body,complete=transport(CHALLENGER_URL,deepcopy(headers),timeout,MAX_ERROR_BYTES)
                _require(type(complete) is bool)
                observations[name]=safe_403_observation(h,body,status,secrets=(raw,key),complete=complete)
            except (OSError,ValueError,TypeError,TimeoutError,subprocess.SubprocessError):pass
    statuses={name:observation['http_status'] for name,observation in observations.items()}
    ready=all(code==200 for code in statuses.values())
    reasons=[] if ready else ['MISSING_API_KEY' if shape['raw_length']==0 else 'INVALID_API_KEY_SHAPE'] if key is None else ['PAIRED_HTTP_NOT_BOTH_200']
    return validate_front_receipt(dict(schema_version='riot.front-diagnostics.v1',status='READY' if ready else 'BLOCKED_EXTERNAL',
        key_shape=shape,statuses=statuses,observations=observations,request_count=2 if key is not None else 0,reasons=reasons,coaching_accuracy=None))


def validate_front_receipt(value):
    try:return _validate_front_receipt(value)
    except (TypeError,KeyError,AttributeError,OverflowError):raise ValueError('invalid Riot front receipt') from None


def _validate_front_receipt(value):
    d=deepcopy(value)
    _require(isinstance(d,dict) and set(d)=={'schema_version','status','key_shape','statuses','observations','request_count','reasons','coaching_accuracy'})
    _require(d['schema_version']=='riot.front-diagnostics.v1' and d['status'] in ('READY','BLOCKED_EXTERNAL') and d['coaching_accuracy'] is None)
    shape=d['key_shape'];_require(isinstance(shape,dict) and set(shape)==SHAPE_FIELDS)
    _require(all(type(shape[k]) is int and shape[k]>=0 for k in ('raw_length','normalized_length')))
    _require(all(type(shape[k]) is bool for k in SHAPE_FIELDS-{'raw_length','normalized_length'}))
    _require(shape['raw_length']>=shape['normalized_length'] and (shape['raw_length']!=shape['normalized_length'])==shape['has_outer_whitespace'])
    _require(not shape['valid_shape'] or shape['normalized_length']==42 and shape['normalized_has_prefix'])
    _require(isinstance(d['statuses'],dict) and set(d['statuses'])=={'curl','python'})
    _require(isinstance(d['observations'],dict) and set(d['observations'])=={'curl','python'})
    for name in ('curl','python'):
        code=d['statuses'][name];_require(code is None or type(code) is int and 100<=code<=599)
        obs=d['observations'][name];_require(isinstance(obs,dict) and set(obs)==OBSERVATION_FIELDS)
        _require(obs['http_status']==code and (obs['is_json'] is None or type(obs['is_json']) is bool))
        _require(obs['reason']==('NETWORK_FAILURE' if code is None and shape['valid_shape'] else None))
        _require(isinstance(obs['markers'],dict) and set(obs['markers'])==set(MARKERS) and all(type(v) is bool for v in obs['markers'].values()))
        for field,maximum in (('headers_content_type',128),('headers_server',128),('body_prefix',100),('error_message',512)):
            text=obs[field]
            _require(text is None or isinstance(text,str) and len(text)<=maximum)
            if field!='body_prefix' or obs['is_json'] is not True:
                _require(text is None or _safe_text(text,maximum)==text)
        if obs['is_json'] is True:
            _require(obs['body_prefix'] is None or _redact_json_strings(obs['body_prefix'])==obs['body_prefix'])
        if code!=403:_require(obs['is_json'] is None and all(obs[k] is None for k in ('headers_content_type','headers_server','body_prefix','error_message')) and not any(obs['markers'].values()))
    _require(type(d['request_count']) is int and d['request_count']==(2 if shape['valid_shape'] else 0))
    if not shape['valid_shape']:_require(all(code is None for code in d['statuses'].values()))
    ready=all(code==200 for code in d['statuses'].values())
    _require(d['status']==('READY' if ready else 'BLOCKED_EXTERNAL'))
    expected=[] if ready else ['MISSING_API_KEY' if shape['raw_length']==0 else 'INVALID_API_KEY_SHAPE'] if not shape['valid_shape'] else ['PAIRED_HTTP_NOT_BOTH_200']
    _require(d['reasons']==expected)
    return d

"""One concurrent curl/Python text pair per pinned, freshly verified free model.

Only statuses and typed success receipts survive; credentials, raw model output,
stderr and key fingerprints never enter receipts. No video or quota mutation.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
import selectors
import subprocess
import sys
import time
import urllib.error

from .expert_collector import (MODEL, FALLBACK_MODEL, ALLOWED_MODELS, MAX_TEXT_TIMEOUT,
    MAX_DISPATCH_DELAY, _require, _canonical, _digest, _generated_text, _json,
    _valid_probe, validate_entitlement_proof, validate_ledger, ExpertCollector, _External)
from .expert_entitlement import verify_free_entitlement

CURL_COMMAND=('curl','--disable','--config','-')
MAX_BYTES=1000000
OBSERVATION_FIELDS={'http_status','reason','valid_response'}
TERMINAL_HTTP_STATUSES=(401,402,403,429)


def text_body():
    return dict(contents=[dict(role='user',parts=[dict(text='Reply with OK.')])],generationConfig=dict(candidateCount=1))


def model_url(model):
    _require(model in ALLOWED_MODELS)
    return 'https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent'


def curl_configuration(model,headers,body,timeout):
    _require(type(timeout) is int and 1<=timeout<=MAX_TEXT_TIMEOUT)
    key=headers.get('x-goog-api-key')
    _require(isinstance(key,str) and bool(key.strip()) and not any(ord(c)<32 for c in key))
    _require(body==text_body() and headers.get('Content-Type')=='application/json')
    def quoted(value):return json.dumps(value,ensure_ascii=True)
    return '\n'.join(('url = '+quoted(model_url(model)),'request = "POST"',
        'header = '+quoted('x-goog-api-key: '+key),'header = "Content-Type: application/json"',
        'data-binary = '+quoted(_canonical(body)),'silent','proto = "=https"','max-redirs = 0',
        'max-time = '+str(timeout),'connect-timeout = '+str(timeout),'max-filesize = '+str(MAX_BYTES),
        'output = "-"','write-out = "\\nEXPERT_HTTP_STATUS:%{http_code}\\n"'))+'\n'


def _bounded_process(command,configuration,timeout,maximum):
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    wire=bytearray();deadline=time.monotonic()+timeout
    try:
        process.stdin.write(configuration);process.stdin.close()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout,selectors.EVENT_READ)
            while True:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise TimeoutError()
                if not selector.select(timeout=min(remaining,1)):continue
                chunk=os.read(process.stdout.fileno(),min(16384,maximum+1-len(wire)))
                if not chunk:break
                wire.extend(chunk)
                if len(wire)>maximum:raise _External('RESPONSE_TOO_LARGE')
        code=process.wait(timeout=max(0.001,deadline-time.monotonic()))
        return code,bytes(wire)
    except subprocess.TimeoutExpired:raise TimeoutError() from None
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=2)
        process.stdout.close()
        if not process.stdin.closed:process.stdin.close()


def _curl_transport(method,url,headers,body,timeout,max_bytes):
    model=next((m for m in ALLOWED_MODELS if url==model_url(m)),None)
    _require(method=='POST' and model is not None and max_bytes==MAX_BYTES)
    code,raw=_bounded_process(CURL_COMMAND,curl_configuration(model,headers,body,timeout).encode(),timeout,max_bytes+64)
    if code==28:raise TimeoutError()
    if code==63:raise _External('RESPONSE_TOO_LARGE')
    if code:raise OSError()
    import re
    match=re.search(rb'\nEXPERT_HTTP_STATUS:([0-9]{3})\n$',raw)
    if match is None:raise OSError()
    return int(match[1]),{},raw[:match.start()]


def _python_transport(method,url,headers,body,timeout,max_bytes):
    # A child process makes120s a total wall bound, not a per-socket-read bound.
    # The child imports the same redirect-rejecting stdlib collector transport.
    program='''import json,sys,urllib.error
from coach_v1.expert_collector import _transport,_External
a=json.load(sys.stdin)
try:
    code,headers,body=_transport(**a)
    sys.stdout.buffer.write(str(code).encode()+b"\\n"+body)
except TimeoutError:
    sys.stdout.buffer.write(b"TIMEOUT\\n")
except urllib.error.URLError as error:
    sys.stdout.buffer.write(b"TIMEOUT\\n" if isinstance(error.reason,TimeoutError) else b"NETWORK\\n")
except _External:
    sys.stdout.buffer.write(b"TOO_LARGE\\n")
'''
    code,raw=_bounded_process((sys.executable,'-c',program),
        _canonical(dict(method=method,url=url,headers=headers,body=body,timeout=timeout,max_bytes=max_bytes)).encode(),timeout,max_bytes+64)
    if code:raise OSError()
    literal,body=raw.split(b'\n',1)
    if literal==b'TIMEOUT':raise TimeoutError()
    if literal==b'TOO_LARGE':raise _External('RESPONSE_TOO_LARGE')
    if literal==b'NETWORK':raise OSError()
    return int(literal),{},body


def _observe(transport,url,headers,body,timeout):
    observation=dict(http_status=None,reason=None,valid_response=False)
    try:
        code,_,raw=transport('POST',url,deepcopy(headers),deepcopy(body),timeout,MAX_BYTES)
        _require(type(code) is int and 100<=code<=599)
        observation['http_status']=code
        if code!=200:observation['reason']='PROVIDER_HTTP_FAILURE';return observation
        response=raw if isinstance(raw,dict) else _json(raw)
        _require(len(_canonical(response).encode())<=MAX_BYTES)
        _generated_text(response)
        observation['valid_response']=True
    except TimeoutError:observation['reason']='NETWORK_TIMEOUT'
    except urllib.error.URLError as error:
        observation['reason']='NETWORK_TIMEOUT' if isinstance(error.reason,TimeoutError) else 'NETWORK_FAILURE'
    except _External as error:observation['reason']=error.reason
    except (ValueError,TypeError,KeyError,UnicodeError,RecursionError,OverflowError):observation['reason']='MALFORMED_RESPONSE'
    except Exception:observation['reason']='NETWORK_FAILURE'
    return observation


def _attempt_reason(observations):
    if any(o['http_status'] in TERMINAL_HTTP_STATUSES for o in observations.values()):return 'PROVIDER_HTTP_FAILURE'
    if any(o['valid_response'] for o in observations.values()):return None
    if all(o['reason']=='NETWORK_TIMEOUT' for o in observations.values()):return 'PROVIDER_NETWORK_TIMEOUT'
    if any(o['reason']=='PROVIDER_HTTP_FAILURE' for o in observations.values()):return 'PROVIDER_HTTP_FAILURE'
    if any(o['reason']=='MALFORMED_RESPONSE' for o in observations.values()):return 'MALFORMED_RESPONSE'
    if any(o['reason']=='RESPONSE_TOO_LARGE' for o in observations.values()):return 'RESPONSE_TOO_LARGE'
    return 'NETWORK_FAILURE'


def run_front_diagnostics(*,youtube_api_key=None,gemini_api_key=None,policy_factory,
    entitlement_verifier=None,curl_transport=None,python_transport=None,clock=None,timeout=120,
    ledger_history='ABSENT',ledger=None,allow_fallback_once=False):
    _require(type(timeout) is int and 1<=timeout<=MAX_TEXT_TIMEOUT)
    _require(type(allow_fallback_once) is bool)
    _require(ledger_history in ('FOUND','ABSENT','UNKNOWN'))
    clock=clock or time.time
    verifier=entitlement_verifier or (lambda model:verify_free_entitlement(model=model))
    receipt=dict(schema_version='expert.front-diagnostics.v1',status='BLOCKED_EXTERNAL',reason=None,
        checked_at=int(clock()),timeout_seconds=timeout,request_count=0,selected_model=None,
        selected_text_probe=None,attempts=[],coaching_accuracy=None,allow_fallback_once=allow_fallback_once)
    for model in ALLOWED_MODELS if allow_fallback_once else (MODEL,):
        proof=validate_entitlement_proof(verifier(model),model)
        now=int(clock())
        observations={name:dict(http_status=None,reason=None,valid_response=False) for name in ('curl','python')}
        reason=None;requests=0
        try:
            _require(proof['checked_at']==datetime.fromtimestamp(now,timezone.utc).date().isoformat())
            if proof['status']=='PAID_REQUIRED':raise _External('DOCUMENTED_PAID_ENTITLEMENT_REQUIRED')
            _require(proof['status']=='VERIFIED_FREE')
            c=ExpertCollector(model=model,youtube_api_key=youtube_api_key,gemini_api_key=gemini_api_key,policy=policy_factory(proof))
            c._gate()
            if ledger_history=='UNKNOWN':raise _External('QUOTA_HISTORY_UNKNOWN')
            if ledger_history=='FOUND' and ledger is None:raise _External('QUOTA_HISTORY_UNKNOWN')
            if ledger is not None:
                try:validate_ledger(ledger,now)
                except (ValueError,TypeError,KeyError):raise _External('QUOTA_HISTORY_UNKNOWN') from None
            elif not c.policy['initial_zero_usage_confirmed']:raise _External('INITIAL_QUOTA_NOT_ATTESTED')
        except _External as error:reason=error.reason
        except ValueError:reason='FREE_PROJECT_OR_ENTITLEMENT_UNVERIFIED'
        if reason is None:
            body=text_body();headers={'x-goog-api-key':gemini_api_key,'Content-Type':'application/json'}
            # Both clients start before either is awaited; no503 retry here.
            with ThreadPoolExecutor(max_workers=2) as executor:
                pending={name:executor.submit(_observe,transport,model_url(model),headers,body,timeout)
                    for name,transport in [('curl',curl_transport or _curl_transport),('python',python_transport or _python_transport)]}
                observations={name:future.result() for name,future in pending.items()}
            requests=2;reason=_attempt_reason(observations)
        attempt=dict(model=model,proof=proof,request_sha256=_digest(text_body()),checked_at=int(clock()),
            statuses={name:o['http_status'] for name,o in observations.items()},observations=observations,
            request_count=requests,reason=reason)
        receipt['attempts'].append(attempt);receipt['request_count']+=requests;receipt['checked_at']=int(clock())
        receipt['reason']=reason
        if reason is None:
            receipt.update(status='READY',selected_model=model,selected_text_probe=dict(schema_version='expert.text-probe.v2',
                status='READY',reason=None,model=model,checked_at=receipt['checked_at'],http_status=200,
                input_kind='TEXT_ONLY',video_inputs=0,api_route='GENERATE_CONTENT',attempt_count=1,retry_count=0))
            break
        # No paid fallback or fallback when primary was never dispatched.
        if not requests or any(code in TERMINAL_HTTP_STATUSES for code in attempt['statuses'].values()):break
    return validate_front_receipt(receipt,now=int(clock()))


def validate_front_receipt(value,*,now):
    try:return _validate_front_receipt(value,now)
    except (KeyError,TypeError,AttributeError,OverflowError):raise ValueError('invalid expert front receipt') from None


def _validate_front_receipt(value,now):
    r=deepcopy(value)
    _require(isinstance(r,dict) and set(r)=={'schema_version','status','reason','checked_at','timeout_seconds','request_count',
        'selected_model','selected_text_probe','attempts','coaching_accuracy','allow_fallback_once'})
    _require(r['schema_version']=='expert.front-diagnostics.v1' and r['coaching_accuracy'] is None)
    _require(type(r['allow_fallback_once']) is bool)
    _require(type(r['checked_at']) is int and 0<=now-r['checked_at']<=MAX_DISPATCH_DELAY)
    _require(type(r['timeout_seconds']) is int and 1<=r['timeout_seconds']<=MAX_TEXT_TIMEOUT)
    _require(isinstance(r['attempts'],list) and 1<=len(r['attempts'])<=2)
    for i,a in enumerate(r['attempts']):
        _require(set(a)=={'model','proof','request_sha256','checked_at','statuses','observations','request_count','reason'})
        _require(a['model']==ALLOWED_MODELS[i] and a['request_sha256']==_digest(text_body()))
        p=validate_entitlement_proof(a['proof'],a['model'])
        _require(type(a['checked_at']) is int and 0<=r['checked_at']-a['checked_at']<=MAX_DISPATCH_DELAY)
        _require(set(a['statuses'])==set(a['observations'])=={'curl','python'})
        _require(type(a['request_count']) is int and a['request_count'] in (0,2))
        for name,o in a['observations'].items():
            _require(set(o)==OBSERVATION_FIELDS)
            code=o['http_status'];_require(code is None or type(code) is int and 100<=code<=599)
            _require(type(o['valid_response']) is bool and a['statuses'][name]==code)
            _require(o['reason'] in (None,'NETWORK_TIMEOUT','NETWORK_FAILURE','MALFORMED_RESPONSE','PROVIDER_HTTP_FAILURE','RESPONSE_TOO_LARGE'))
            _require(not o['valid_response'] or code==200 and o['reason'] is None)
            _require(code is None or code==200 or o['reason']=='PROVIDER_HTTP_FAILURE')
        if a['request_count']:
            _require(p['status']=='VERIFIED_FREE' and p['checked_at']==datetime.fromtimestamp(a['checked_at'],timezone.utc).date().isoformat())
            _require(a['reason']==_attempt_reason(a['observations']))
        else:
            _require(a['reason'] in ('FREE_PROJECT_OR_ENTITLEMENT_UNVERIFIED','DOCUMENTED_PAID_ENTITLEMENT_REQUIRED','KNOWN_PAID_PROJECT','MISSING_API_KEYS','QUOTA_HISTORY_UNKNOWN','INITIAL_QUOTA_NOT_ATTESTED'))
            _require(all(o==dict(http_status=None,reason=None,valid_response=False) for o in a['observations'].values()))
        if i:
            _require(r['allow_fallback_once'])
            primary=r['attempts'][0]
            _require(primary['reason'] is not None and primary['request_count']==2)
            _require(not any(code in TERMINAL_HTTP_STATUSES for code in primary['statuses'].values()))
    _require(type(r['request_count']) is int and r['request_count']==sum(a['request_count'] for a in r['attempts']))
    last=r['attempts'][-1];ready=last['reason'] is None
    _require(r['status']==('READY' if ready else 'BLOCKED_EXTERNAL') and r['reason']==last['reason'])
    if ready:
        _require(r['selected_model']==last['model'])
        _valid_probe(r['selected_text_probe'],now,last['model'])
        _require(r['selected_text_probe']['checked_at']==r['checked_at'] and r['selected_text_probe']['attempt_count']==1)
    else:_require(r['selected_model'] is None and r['selected_text_probe'] is None)
    return r

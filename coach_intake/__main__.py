"""No account/key/payment required. Captures remain local; no coaching activation."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import socket,ssl,urllib.error
from .io import SAMPLE_URL,CA_URL,GAME_URL,fetch,sha,write_new,write_json
from .audit import inspect
from .video import index_transcript

def stamp():return datetime.now(timezone.utc).isoformat()

def acquire(destination,kind,max_bytes,timeout):
    destination=Path(destination)
    # A fresh directory makes partial/failed runs visible and prevents overwrites.
    destination.mkdir(parents=True,exist_ok=False)
    status=dict(at_utc=stamp(),mode=kind,stage='START',coaching_enabled=False,passed=False)
    try:
        ca=None
        if kind=='local':
            status['stage']='CERTIFICATE_DOWNLOAD'
            cert=fetch(CA_URL,100000,timeout)
            ssl.create_default_context(cadata=cert.decode('ascii'))
            ca=destination/'riotgames.pem';write_new(ca,cert)
            status['certificate_sha256']=sha(cert);status['certificate_url']=CA_URL
        source=SAMPLE_URL if kind=='sample' else GAME_URL
        status['stage']='PAYLOAD_DOWNLOAD';raw=fetch(source,max_bytes,timeout,ca)
        received=stamp();write_new(destination/'raw.json',raw)
        status['stage']='PAYLOAD_AUDIT'
        declared='DOCUMENTATION_SAMPLE' if kind=='sample' else 'UNVERIFIED_LOCAL_CAPTURE'
        report=inspect(raw,declared,sha(raw))
        write_json(destination/'audit.json',report)
        write_json(destination/'receipt.json',dict(source_url=source,retrieved_at_utc=received,raw_sha256=sha(raw),bytes=len(raw),evidence_kind=declared,game_end_verified=False,coaching_enabled=False))
        status.update(stage='DONE',passed=True,acquisition_and_audit_only=True)
    except Exception as e:
        reason=e.reason if isinstance(e,urllib.error.URLError) else e
        if isinstance(reason,ssl.SSLCertVerificationError):code='TLS_VERIFICATION_FAILED'
        elif isinstance(reason,(ConnectionRefusedError,socket.timeout,TimeoutError)):code='ENDPOINT_UNAVAILABLE'
        elif isinstance(e,urllib.error.HTTPError):code='HTTP_'+str(e.code)
        else:code=type(e).__name__
        status.update(error_code=code,action='Check internet/certificate for CERTIFICATE_DOWNLOAD; start LoL on this PC for local PAYLOAD_DOWNLOAD. Never disable TLS verification.')
    write_json(destination/'status.json',status)
    return status

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for command in ('sample','local'):
        q=sub.add_parser(command);q.add_argument('--out',type=Path,required=True);q.add_argument('--max-bytes',type=int,required=True);q.add_argument('--timeout-seconds',type=float,required=True)
    q=sub.add_parser('inspect');q.add_argument('input',type=Path);q.add_argument('--out',type=Path,required=True);q.add_argument('--max-bytes',type=int,required=True)
    q=sub.add_parser('video');q.add_argument('input',type=Path);q.add_argument('--video-id',required=True);q.add_argument('--out',type=Path,required=True);q.add_argument('--max-bytes',type=int,required=True)
    a=p.parse_args()
    try:
        if a.command in ('inspect','video'):
            if a.max_bytes<=0:raise ValueError('INVALID_LIMIT')
            with a.input.open('rb') as f:raw=f.read(a.max_bytes+1)
            if len(raw)>a.max_bytes:raise ValueError('SIZE_LIMIT')
            write_json(a.out,inspect(raw) if a.command=='inspect' else index_transcript(raw,a.video_id));print('Diagnostic saved. Real-data coaching remains disabled.');return 0
        result=acquire(a.out,a.command,a.max_bytes,a.timeout_seconds)
        print(json.dumps(result,ensure_ascii=False));return 0 if result['passed'] else 1
    except Exception as e:print(json.dumps(dict(passed=False,error_code=type(e).__name__,coaching_enabled=False)));return 1
if __name__=='__main__':raise SystemExit(main())

"""One-shot private capture for offline adapter research; never produces advice."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import ssl
import urllib.request

ENDPOINT='https://127.0.0.1:2999/liveclientdata/allgamedata'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirect refused')

def envelope(raw, received_at):
    value=json.loads(raw,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    if not isinstance(value,dict):raise ValueError('Expected JSON object')
    return dict(format='lol-coach-raw-capture-v1',endpoint=ENDPOINT,received_at=received_at,
        raw_sha256=hashlib.sha256(raw).hexdigest(),raw_base64=base64.b64encode(raw).decode(),
        evidence_kind='UNVERIFIED_LOCAL_CAPTURE',game_end_verified=False,
        source_semantics_verified=False,coaching_enabled=False)

def capture(ca, destination, max_bytes, timeout):
    if max_bytes<=0 or not math.isfinite(timeout) or timeout<=0:raise ValueError('Positive explicit limits required')
    context=ssl.create_default_context(cafile=str(ca))
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=context),NoRedirect())
    with opener.open(urllib.request.Request(ENDPOINT,headers={'Accept':'application/json'}),timeout=timeout) as response:
        raw=response.read(max_bytes+1)
    if len(raw)>max_bytes:raise ValueError('Capture exceeds limit')
    data=envelope(raw,datetime.now(timezone.utc).isoformat())
    encoded=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
    # Exclusive creation prevents replacing earlier evidence. No upload or polling.
    fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'wb') as f:f.write(encoded);f.flush();os.fsync(f.fileno())
    except BaseException:
        Path(destination).unlink(missing_ok=True);raise
    return data['raw_sha256']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ca',type=Path,required=True,help='Official Riot root certificate file')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-bytes',type=int,required=True)
    p.add_argument('--timeout-seconds',type=float,required=True)
    a=p.parse_args()
    try:capture(a.ca,a.output,a.max_bytes,a.timeout_seconds)
    except Exception as e:p.exit(1,'Capture failed: '+type(e).__name__+'; no coaching activated.\n')
    print('Local unverified capture saved. No analysis or upload performed.')

if __name__=='__main__':main()

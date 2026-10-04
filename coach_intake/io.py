import hashlib,json,math,os,ssl,tempfile,urllib.request
from pathlib import Path

SAMPLE_URL='https://static.developer.riotgames.com/docs/lol/liveclientdata_sample.json'
CA_URL='https://static.developer.riotgames.com/docs/lol/riotgames.pem'
GAME_URL='https://127.0.0.1:2999/liveclientdata/allgamedata'

def strict_json(raw):
    def pairs(items):
        obj={}
        for k,v in items:
            if k in obj:raise ValueError('DUPLICATE_KEY')
            obj[k]=v
        return obj
    def number(s):
        x=float(s)
        if not math.isfinite(x):raise ValueError('NONFINITE_NUMBER')
        return x
    def bad(s):raise ValueError('NONFINITE_NUMBER')
    return json.loads(raw,object_pairs_hook=pairs,parse_float=number,parse_constant=bad)

def sha(raw):return hashlib.sha256(raw).hexdigest()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('REDIRECT_REFUSED')

def fetch(url,limit,timeout,ca=None):
    if url not in (SAMPLE_URL,CA_URL,GAME_URL):raise ValueError('URL_NOT_ALLOWED')
    if type(limit) is not int or limit<=0 or not math.isfinite(timeout) or timeout<=0:raise ValueError('INVALID_LIMIT')
    if url==GAME_URL and ca is None:raise ValueError('GAME_CA_REQUIRED')
    context=ssl.create_default_context(cafile=str(ca) if ca is not None else None)
    # No proxy prevents local/private game payload from leaving through a proxy.
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}) if url==GAME_URL else urllib.request.ProxyHandler(),urllib.request.HTTPSHandler(context=context),NoRedirect())
    with opener.open(url,timeout=timeout) as response:
        if response.status!=200:raise ValueError('HTTP_STATUS')
        raw=response.read(limit+1)
    if len(raw)>limit:raise ValueError('SIZE_LIMIT')
    return raw

def write_new(path,raw):
    """Publish a complete file exclusively; failed attempts leave no partial target."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.intake-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.link(temp,path)
    finally:Path(temp).unlink(missing_ok=True)

def write_json(path,obj):write_new(path,(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())

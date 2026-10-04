"""Loopback-only authenticated development workbench. No production game adapter."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import threading
from urllib.parse import urlsplit

from .storage import Store, ServiceError

ROOT=Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Limits:
    body_bytes: int
    observations: int
    actions: int
    scenarios: int
    comparisons: int
    pending_jobs: int

    def __post_init__(self):
        if any(type(v) is not int or v<=0 for v in vars(self).values()):
            raise ValueError('Explicit positive operational limits required')


def strict_json(raw):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('duplicate JSON key')
            result[k]=v
        return result
    def bad_constant(value):raise ValueError('nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad_constant)


class Workbench(ThreadingHTTPServer):
    daemon_threads=True

    def __init__(self, db, token: str, limits: Limits, port=0):
        if len(token)<32:raise ValueError('token must have at least 32 characters')
        lock_path=Path(str(Path(db).resolve())+'.lock')
        lock_path.parent.mkdir(parents=True,exist_ok=True)
        self.db_lock=lock_path.open('a+b')
        try:
            if __import__('os').name=='nt':
                import msvcrt
                self.db_lock.seek(0);self.db_lock.write(b'0');self.db_lock.flush();self.db_lock.seek(0)
                msvcrt.locking(self.db_lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.db_lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.db_lock.close();raise ValueError('Database already owned by another workbench') from None
        try:self.store=Store(db)
        except Exception:self.db_lock.close();raise
        self.token=token
        self.limits=limits
        self.worker=ThreadPoolExecutor(max_workers=1,thread_name_prefix='lol-review')
        self.pending=set()
        self.job_lock=threading.RLock()
        self.closing=False
        super().__init__(('127.0.0.1',port),Handler)
        self.allowed_hosts={f'127.0.0.1:{self.server_port}',f'localhost:{self.server_port}'}
        self.allowed_origins={f'http://{host}' for host in self.allowed_hosts}
        self.pump()

    def pump(self):
        if self.closing:return
        for jid in self.store.queued_job_ids():
            try:self.schedule(jid)
            except ServiceError:return

    def schedule(self,jid):
        with self.job_lock:
            if jid in self.pending:return
            if len(self.pending)>=self.limits.pending_jobs:
                raise ServiceError(503,'QUEUE_CAPACITY')
            self.pending.add(jid)
        def work():
            try:self.store.run_job(jid)
            finally:
                with self.job_lock:self.pending.discard(jid)
                self.pump()
        self.worker.submit(work)

    def server_close(self):
        self.closing=True
        super().server_close()
        self.worker.shutdown(wait=True,cancel_futures=False)
        self.db_lock.close()


class Handler(BaseHTTPRequestHandler):
    server_version='LoLCoachDev'
    # HTTP/1.0 closes each request: no ambiguous pipelined request bodies.
    def log_message(self,*args):pass

    def reply(self,status,payload,ctype='application/json; charset=utf-8'):
        body=payload if isinstance(payload,bytes) else json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def fail(self,status,code):
        self.reply(status,dict(error_code=code,message='요청을 처리하지 못했습니다. 입력·연결 상태를 확인하세요.',retryable=status==503,correlation_id=secrets.token_hex(8)))

    def preflight(self):
        if len(self.headers.get_all('Host',[]))!=1 or self.headers['Host'] not in self.server.allowed_hosts:
            raise ServiceError(403,'HOST_REJECTED')
        origins=self.headers.get_all('Origin',[])
        if len(origins)>1 or (origins and origins[0] not in self.server.allowed_origins):
            raise ServiceError(403,'ORIGIN_REJECTED')
        if self.headers.get('Sec-Fetch-Site')=='cross-site':raise ServiceError(403,'CROSS_SITE_REJECTED')

    def authorize(self):
        values=self.headers.get_all('Authorization',[])
        supplied=values[0] if len(values)==1 else ''
        if not hmac.compare_digest(supplied.encode(),('Bearer '+self.server.token).encode()):
            raise ServiceError(401,'AUTH_REQUIRED')

    def body(self):
        if self.headers.get('Transfer-Encoding'):raise ServiceError(400,'TRANSFER_ENCODING_REJECTED')
        lengths=self.headers.get_all('Content-Length',[])
        if len(lengths)!=1:raise ServiceError(411,'LENGTH_REQUIRED')
        if not re.fullmatch(r'\d+',lengths[0]):raise ServiceError(400,'INVALID_LENGTH')
        size=int(lengths[0])
        if size>self.server.limits.body_bytes:raise ServiceError(413,'BODY_TOO_LARGE')
        if self.headers.get_content_type()!='application/json':raise ServiceError(415,'JSON_REQUIRED')
        self.connection.settimeout(10)
        raw=self.rfile.read(size)
        if len(raw)!=size:raise ServiceError(400,'INCOMPLETE_BODY')
        obj=strict_json(raw.decode('utf-8'))
        if not isinstance(obj,dict):raise ServiceError(422,'OBJECT_REQUIRED')
        return obj

    def fields(self,obj,required,optional=()):
        if not set(required).issubset(obj) or set(obj)-set(required)-set(optional):raise ServiceError(422,'INVALID_FIELDS')

    def key(self):
        keys=self.headers.get_all('Idempotency-Key',[])
        if len(keys)!=1 or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',keys[0]):raise ServiceError(422,'IDEMPOTENCY_KEY_REQUIRED')
        return keys[0]

    def revision(self,value):
        if type(value) is not int or value<0:raise ServiceError(422,'INVALID_REVISION')
        return value

    def check_case_limits(self,case):
        if not isinstance(case,dict):raise ServiceError(422,'CASE_OBJECT_REQUIRED')
        for name in ('observations','actions','scenarios','comparisons'):
            items=case.get(name)
            if not isinstance(items,list) or len(items)>getattr(self.server.limits,name):raise ServiceError(413,'CASE_COMPLEXITY_LIMIT')

    def dispatch(self):
        self.preflight()
        path=urlsplit(self.path)
        if path.query or path.fragment:raise ServiceError(400,'QUERY_NOT_SUPPORTED')
        route=path.path
        assets={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/styles.css':('styles.css','text/css; charset=utf-8')}
        if self.command=='GET' and route in assets:
            filename,ctype=assets[route]
            return self.reply(200,(ROOT/'web_r4'/filename).read_bytes(),ctype)
        self.authorize()
        store=self.server.store
        prefix='/dev/v1'
        if self.command=='GET' and route==prefix+'/status':
            return self.reply(200,dict(version='R4',mode='SYNTHETIC_ONLY',real_data_enabled=False,limits=vars(self.server.limits)))
        examples={'insufficient-evidence':'정보 부족 확인','compare-wait-retreat':'대기와 후퇴 비교'}
        if self.command=='GET' and route==prefix+'/examples':
            return self.reply(200,[dict(id=k,title=v) for k,v in examples.items()])
        if self.command=='GET' and route.startswith(prefix+'/examples/'):
            name=route.removeprefix(prefix+'/examples/')
            if name not in examples:raise ServiceError(404,'NOT_FOUND')
            return self.reply(200,json.loads((ROOT/'examples/r3'/(name+'.json')).read_text()))
        if route==prefix+'/sessions':
            if self.command=='GET':return self.reply(200,store.list_sessions())
            if self.command=='POST':
                b=self.body();self.fields(b,('title','patch'),('mode',))
                return self.reply(201,store.create_session(b['title'],b['patch'],b.get('mode','TEST')))
        m=re.fullmatch(re.escape(prefix)+r'/sessions/([a-zA-Z0-9-]+)(/case|/reviews)?',route)
        if m:
            sid,suffix=m.groups()
            if not suffix:
                if self.command=='GET':return self.reply(200,store.get_session(sid))
                if self.command=='DELETE':return self.reply(200,store.delete_session(sid))
            if suffix=='/case':
                if self.command=='GET':return self.reply(200,store.get_case(sid))
                if self.command=='PUT':
                    b=self.body();self.fields(b,('case','expected_revision'));self.check_case_limits(b['case'])
                    return self.reply(200,store.put_case(sid,b['case'],self.revision(b['expected_revision']),self.key()))
            if suffix=='/reviews' and self.command=='GET':return self.reply(200,store.list_jobs(sid))
            if suffix=='/reviews' and self.command=='POST':
                b=self.body();self.fields(b,('expected_revision',))
                with self.server.job_lock:
                    if len(self.server.pending)>=self.server.limits.pending_jobs:raise ServiceError(503,'QUEUE_CAPACITY')
                    job=store.submit_review(sid,self.revision(b['expected_revision']),self.key())
                    if job['status']=='QUEUED':self.server.schedule(job['id'])
                return self.reply(202,job)
        m=re.fullmatch(re.escape(prefix)+r'/jobs/([a-zA-Z0-9-]+)(/cancel)?',route)
        if m:
            jid,suffix=m.groups()
            if not suffix and self.command=='GET':return self.reply(200,store.get_job(jid))
            if suffix=='/cancel' and self.command=='POST':
                self.fields(self.body(),());return self.reply(200,store.cancel_job(jid))
        m=re.fullmatch(re.escape(prefix)+r'/reviews/([a-zA-Z0-9-]+)',route)
        if m and self.command=='GET':return self.reply(200,store.get_review(m.group(1)))
        raise ServiceError(404,'NOT_FOUND')

    def handle_request(self):
        try:self.dispatch()
        except ServiceError as e:self.fail(e.status,e.code)
        except (ValueError,TypeError,KeyError,UnicodeError,RecursionError):self.fail(422,'INVALID_INPUT')
        except (TimeoutError,ConnectionError):self.close_connection=True
        except Exception:self.fail(500,'INTERNAL_ERROR')

    do_GET=handle_request
    do_POST=handle_request
    do_PUT=handle_request
    do_DELETE=handle_request


def main():
    parser=argparse.ArgumentParser(description='Local synthetic development workbench; not an in-game coach')
    parser.add_argument('--db',type=Path,required=True)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--token-file',type=Path,required=True)
    for flag in ('body-bytes','observations','actions','scenarios','comparisons','pending-jobs'):
        parser.add_argument('--max-'+flag,type=int,required=True)
    args=parser.parse_args()
    if args.token_file.exists():
        token=args.token_file.read_text().strip()
    else:
        args.token_file.parent.mkdir(parents=True,exist_ok=True)
        token=secrets.token_urlsafe(32)
        import os
        fd=os.open(args.token_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:f.write(token+'\n')
    limits=Limits(args.max_body_bytes,args.max_observations,args.max_actions,args.max_scenarios,args.max_comparisons,args.max_pending_jobs)
    server=Workbench(args.db,token,limits,args.port)
    print(f'개발용 합성 복기 화면: http://127.0.0.1:{server.server_port}',flush=True)
    print(f'접속키는 {args.token_file} 파일에서 확인하세요. 실제 경기 기능은 잠겨 있습니다.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()

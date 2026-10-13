#!/usr/bin/env python3
"""Disposable SYNTHETIC browser proof; private fixtures removed, no Riot/provider calls."""
import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
FILES=['coach_v1/postgame_match.py','coach_v1/personal_riot.py','coach_v1/pregame_server.py',
       'web_r4/postgame.html','web_r4/postgame.js','web_r4/postgame.css','web_r4/pro_reference_view.js','config/pro_reference_players.json','coach_v1/pro_reference.py','coach_v1/pro_reference_overlay.py',
       'tests_pregame/test_v20_postgame.py','tests_pregame/browser_postgame_v20.cjs','scripts/browser_postgame_v20.py']


def fixture():
    from tests_pregame.test_v20_postgame import body
    b=body();b['match']['info']['gameStartTimestamp']=100000
    a=dict(match_sha256=hashlib.sha256(b['match']['metadata']['matchId'].encode()).hexdigest(),timestamp_ms=60000,stage='EARLY',stage_conditions=[dict(field='LANING_ACTIVE',value=True)],source_sha256='a'*64,source_pointer='/synthetic/phase/0',verification='VERIFIED')
    b['phase_annotations']=[a];return b


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default='evidence/queue/postgame-v20-synthetic');args=p.parse_args(argv)
    output=(ROOT/args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}
    receipt=dict(schema_version='queue.v20.postgame-browser.v1',sample_kind='SYNTHETIC',real_matches=0,started_at=datetime.now(timezone.utc).isoformat(),source_sha256=hashes,privacy='DISPOSABLE_SYNTHETIC_RAW_ONLY',external_requests=0,approval_operations=0)
    server=None;thread=None
    with tempfile.TemporaryDirectory(prefix='postgame-v20-') as td:
        token=secrets.token_urlsafe(32);token_path=Path(td)/'token';token_path.write_text(token);token_path.chmod(0o600)
        try:
            from coach_v1.pregame_server import PregameWorkbench
            from coach_v1.server import Limits
            from coach_v1.postgame_match import PostgameStore
            from coach_v1.movement import build_movement_dataset
            from coach_v1.power_stats import build_power_dataset
            from coach_v1.pregame_v2 import evaluate_gameplan_v2
            from tests_pregame.test_contract import golden
            from tests_pregame.test_movement import source
            server=PregameWorkbench(Path(td)/'app.sqlite',token,Limits(12_000_000,1000,100,100,100,10));server.test_mode=True
            b=fixture();pairs=[];annotations=[]
            for n in (1,2):
                pair=copy.deepcopy(b);mid='KR_'+str(n);pair['match']['metadata']['matchId']=mid;pair['timeline']['metadata']['matchId']=mid;pair.pop('phase_annotations')
                pairs.append(pair);a=copy.deepcopy(b['phase_annotations'][0]);a['match_sha256']=hashlib.sha256(mid.encode()).hexdigest();annotations.append(a)
            server.power_data=build_power_dataset(pairs,source=source());server.movement_statistics=build_movement_dataset(pairs,source=source(),phase_annotations=annotations)
            store=PostgameStore(Path(td)/'private'/'postgame',test_mode=True);known=store.import_match(b)
            incomplete=copy.deepcopy(b);incomplete['match']['metadata']['matchId']='KR_999';incomplete['timeline']['metadata']['matchId']='KR_999';incomplete.pop('phase_annotations');del incomplete['timeline']['info']['frames'][1]['participantFrames']['2']['position'];missing=store.import_match(incomplete)
            draft=golden(patch='16.19');saved=server.pregame.save(draft,None,0,'synthetic-input');plan=server.pregame.save_plan(saved['session_id'],1,evaluate_gameplan_v2(draft,[]),'synthetic-plan')
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            imported=copy.deepcopy(b);imported['match']['metadata']['matchId']='KR_888';imported['timeline']['metadata']['matchId']='KR_888';imported.pop('phase_annotations')
            env=dict(os.environ,POSTGAME_BROWSER_URL='http://127.0.0.1:'+str(server.server_address[1])+'/postgame',POSTGAME_TOKEN_FILE=str(token_path),POSTGAME_OUTPUT=str(output),POSTGAME_FIXTURE=json.dumps(imported),POSTGAME_KNOWN_ID=known['id'],POSTGAME_MISSING_ID=missing['id'],POSTGAME_PLAN_ID=plan['id'],NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),CHROMIUM_EXECUTABLE=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
            child=subprocess.run(['node','tests_pregame/browser_postgame_v20.cjs'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
            for name,value in [('stdout',child.stdout),('stderr',child.stderr)]:
                (output/(name+'.log')).write_text(value.replace(token,'[REDACTED]'))
            receipt['exit_code']=child.returncode
            browser_receipt=output/'browser.json'
            receipt['browser']=json.loads(browser_receipt.read_text()) if browser_receipt.exists() else None
            receipt['passed']=child.returncode==0 and bool(receipt['browser']) and receipt['browser']['passed']
        except Exception as e:
            receipt['passed']=False;receipt['error']=str(e).replace(token,'[REDACTED]')
        finally:
            if server:
                if thread:server.shutdown()
                server.server_close()
    receipt['finished_at']=datetime.now(timezone.utc).isoformat();receipt['source_unchanged']=hashes=={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}
    receipt['passed']=receipt['passed'] and receipt['source_unchanged']
    receipt_text=json.dumps(receipt,indent=2,ensure_ascii=False)+'\n'
    (output/'receipt.json').write_text(receipt_text)
    (output/'runner.json').write_text(receipt_text)
    print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(output),sample_kind='SYNTHETIC',real_matches=0)));return 0 if receipt['passed'] else 1

if __name__=='__main__':raise SystemExit(main())

"""Isolated production browser proof. Accepts validated REAL public aggregates only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import selectors
import sqlite3
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
IDS = ['real-datasets', 'production-auth', 'manual-default-roles', 'saved-current-plan',
       'challenger-tier', 'source-bound-view', 'honest-precision-rendering',
       'point-hover-or-withheld', 'real-source-details', 'unknown-opponent-fallback',
       'explicit-missing-patch', 'no-synthetic-rendering', 'no-review-writes', 'clean-browser']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=Path('/workspace/lol-coach-v13'))
    p.add_argument('--power-data', type=Path, required=True)
    p.add_argument('--movement-data', type=Path)
    p.add_argument('--outcome-data', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); root = a.repo.resolve(); sys.path.insert(0, str(root))
    from coach_v1.power_stats import validate_power_dataset, select_power_view
    from coach_v1.movement import validate_movement_dataset
    from coach_v1.outcome_stats import validate_outcome_dataset
    from coach_v1.state import digest
    datasets = {}; bindings = {}
    for name, validator in [('power',validate_power_dataset),('movement',validate_movement_dataset),('outcome',validate_outcome_dataset)]:
        path = getattr(a, name+'_data')
        if path is None: continue
        path = path.resolve(); data = validator(json.loads(path.read_text()))
        if data['source']['sample_kind'] != 'REAL' or data['source']['tier'] != 'CHALLENGER':
            raise ValueError(name+': requires REAL CHALLENGER source')
        if data.get('samples',{}).get('synthetic_matches',0) != 0:
            raise ValueError(name+': synthetic sample prohibited')
        datasets[name] = data
        bindings[name] = dict(path=str(path), file_sha256=sha(path), dataset_digest=digest(data),
            schema_version=data['schema_version'], source=data['source'], samples=data.get('samples'),status=data.get('status'))
    power=datasets['power']
    if power['source']['precision_policy']['ci_width_limits'] is not None: raise ValueError('REAL verification forbids precision-width overrides')
    if power.get('samples',{}).get('real_matches',0) < 1: raise ValueError('No acquired real matches to verify')
    cohorts=[c for c in power['cohorts'] if c['metric']=='gold_delta' and c['patch'] and c['tier']=='CHALLENGER']
    if not cohorts: raise ValueError('No observed real cohort with exact patch and canonical position')
    cohorts.sort(key=lambda c:(c['comparison']=='MATCHUP',sum(q.get('visible') is True for q in c['points']),max((q['n'] for q in c['points']),default=0)), reverse=True)
    c=cohorts[0]; selection={k:c[k] for k in ['champion','position','patch','tier','opponent_champion']}
    expected={key:dict(select_power_view(power,**dict(selection,opponent_champion=opponent)),dataset_digest=digest(power),schema_version=power['schema_version']) for key,opponent in [('observed',selection['opponent_champion']),('fallback',None)]}
    paths=[q for folder in ['contracts','coach_v1','web_r4'] for q in (root/folder).rglob('*') if q.is_file() and '__pycache__' not in q.parts and q.suffix in {'.py','.json','.js','.css','.html','.md','.svg'}]
    paths += [Path(__file__).resolve(),HERE/'verify_real.cjs'] + [Path(b['path']) for b in bindings.values()]
    initial={str(q):sha(q) for q in sorted(set(paths))}
    output=a.output.resolve(); output.mkdir(parents=True,exist_ok=False)
    (output/'input-binding.json').write_text(json.dumps(dict(datasets=bindings,selection=selection,expected=expected,source_sha256=initial,expected_check_ids=IDS,scope='REAL anonymous aggregate UI verification over manually authored PRE_GAME draft; no live game observation, knowledge approval, or coaching accuracy claim'),ensure_ascii=False,indent=2)+'\n')
    error=None; code=None; audit=None; token=''; server=None
    with tempfile.TemporaryDirectory(prefix='real-pregame-') as td:
        private=Path(td); token_path=private/'token'; database=private/'work.sqlite'; experts=private/'empty-experts'; experts.mkdir()
        token=secrets.token_urlsafe(32); token_path.write_text(token+'\n'); token_path.chmod(0o600)
        command=[sys.executable,'-m','coach_v1.pregame_server','--db',str(database),'--token-file',str(token_path),'--port','0','--expert-claims-dir',str(experts),'--max-body-bytes','1000000','--max-observations','1000','--max-actions','100','--max-scenarios','100','--max-comparisons','100','--max-pending-jobs','10']
        for name,b in bindings.items(): command += ['--'+name+'-data',b['path']]
        try:
            with (output/'server-stderr.log').open('w') as stderr:
                server=subprocess.Popen(command,cwd=root,stdout=subprocess.PIPE,stderr=stderr,text=True)
                with selectors.DefaultSelector() as selector:
                    selector.register(server.stdout,selectors.EVENT_READ)
                    if not selector.select(timeout=30): raise RuntimeError('Production server readiness timeout')
                    startup=server.stdout.readline()
                url=startup.strip().split()[-1]
                if not url.startswith('http://127.0.0.1:'): raise RuntimeError('Production server readiness missing loopback URL')
                (output/'server-startup.log').write_text(startup)
                env=dict(os.environ,WORKBENCH_URL=url,WORKBENCH_TOKEN_FILE=str(token_path),REAL_EVIDENCE_DIR=str(output),NODE_PATH=os.environ.get('NODE_PATH','/opt/codex/cua_node/lib/node_modules'),CHROMIUM_EXECUTABLE=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'))
                child=subprocess.run(['node',str(HERE/'verify_real.cjs')],cwd=root,env=env,text=True,capture_output=True,timeout=180)
                code=child.returncode
                for name,value in [('stdout',child.stdout),('stderr',child.stderr)]: (output/(name+'.log')).write_text(value.replace(token,'[REDACTED]'))
        except Exception as exc: error=str(exc).replace(token,'[REDACTED]')
        finally:
            if server:
                server.terminate()
                try: server.wait(timeout=10)
                except subprocess.TimeoutExpired: server.kill(); server.wait(timeout=10)
                server.stdout.close()
        research=Path(str(database)+'.research.sqlite')
        if research.exists():
            with sqlite3.connect(research) as conn: rows=conn.execute('SELECT status,payload FROM knowledge_rules').fetchall()
            audit=dict(proposal_rows=len(rows),decision_rows=sum(json.loads(payload).get('schema_version')=='knowledge-decision.v1' for status,payload in rows),review_actor_rows=sum('review_decision' in json.loads(payload) for status,payload in rows))
    current={str(q):sha(q) for q in sorted(set(paths))}
    receipt=json.loads((output/'receipt.json').read_text()) if (output/'receipt.json').exists() else None
    passed=code==0 and error is None and current==initial and audit==dict(proposal_rows=0,decision_rows=0,review_actor_rows=0) and bool(receipt and receipt['passed'] and [v['id'] for v in receipt['checks']]==IDS)
    result=dict(passed=passed,finished_at=datetime.now(timezone.utc).isoformat(),process_exit_code=code,error=error,source_binding_unchanged=current==initial,source_sha256=current,datasets=bindings,selection=selection,store_audit=audit,browser=receipt,git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),scope='REAL aggregate browser proof; manually authored draft; coaching accuracy NOT_EVALUATED; no Riot requests or reviews',credentials='Disposable local token; no Riot key read or logged')
    (output/'runner.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=passed,output=str(output),checks=len(receipt['checks']) if receipt else 0,error=error)))
    return 0 if passed else 1

if __name__=='__main__': raise SystemExit(main())

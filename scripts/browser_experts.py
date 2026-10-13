"""Fresh Chromium verification in private, disposable expert-review servers.

Synthetic mode injects a read-only fixture knowledge view, never calls decide,
and does not prove approval persistence. Normal mode uses unmodified stores.
"""
from __future__ import annotations

import copy
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
import uuid
from datetime import datetime, timezone

ROOT = Path(os.environ.get('EXPERT_REPO_ROOT', Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0, str(ROOT))
SOURCE_FILES = ['requirements-private-cache.txt'] + sorted(str(p.relative_to(ROOT)) for folder in
    ['contracts', 'coach_v1', 'web_r4', 'tests_expert', 'scripts', 'knowledge_candidates', 'config', '.github']
    for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts
    and p.suffix in {'.py', '.cjs', '.js', '.html', '.css', '.svg', '.json', '.md', '.yml', '.yaml'})

EXPECTED_BROWSER_IDS = ['connected', 'empty-claims', 'manual-import', 'count-only-notification', 'safe-timestamp-link', 'speaker-context-patch', 'measurement-status', 'independent-source-counts', 'nonexecutable-review-state', 'selected-version-source-binding', 'incomplete-scope-disabled', 'complete-scope-enabled', 'scripted-approval-blocked', 'immutable-proposal-guard', 'idempotent-import', 'mobile-keyboard', 'friendly-manual-form', 'invalid-manual-timestamp-no-write', 'manual-builder-original-binding', 'late-auth-navigation', 'no-decisions-errors-source-change']

def now():return datetime.now(timezone.utc).isoformat()
def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCE_FILES}
def artifact_fixture():
    video_id='AaBbCcDdE12'
    return dict(schema_version='expert.claims.v1',video=dict(id=video_id,url='https://www.youtube.com/watch?v='+video_id,
        title='TEST manual fixture; not an actual expert source',channel_id=None,channel_name='TEST manual channel',
        speaker='UNKNOWN',speaker_verified=False,published_at=None,upload_date=None,duration_seconds=600,language='ko'),
        processing=dict(method='MANUAL_SUMMARY',model='UNKNOWN',processed_at='2026-10-11T00:00:00Z',input_sha256='a'*64),
        claims=[dict(timestamp='01:30',timestamp_seconds=90,paraphrase='TEST manually authored claim <img src=x onerror=alert(1)>',champion='Ornn',position='TOP',
            stage='EARLY',conditions=['TEST condition'],context='EXPLANATION',measurable=False,patch_range='UNKNOWN',
            counterexamples=['TEST counterexample not established'],limitations=['TEST no actual source acquisition'],
            measurement=None,independent_group_id='YOUTUBE:'+video_id)],rejections=[],visual_verified=False,coaching_accuracy=None)

def serve(mode,database,token_file):
    from coach_v1 import pregame_server as module
    from coach_v1.server import Limits
    server=module.PregameWorkbench(Path(database),Path(token_file).read_text().strip(),Limits(1_000_000,1000,100,100,100,10))
    if mode=='synthetic':
        from coach_v1 import expert_bridge as bridge
        original_list=bridge.list_expert_claims
        def list_view(*args,**kwargs):
            result=copy.deepcopy(original_list(*args,**kwargs))
            for row in result['claims'] if isinstance(result,dict) else result:row['proposal']['review_state']='REVIEWED'
            return result
        bridge.list_expert_claims=list_view
        if hasattr(module,'list_expert_claims'):module.list_expert_claims=list_view
        original_get=server.research.get_proposal
        def get_view(*args,**kwargs):
            result=copy.deepcopy(original_get(*args,**kwargs));result['review_state']='REVIEWED';return result
        server.research.get_proposal=get_view
    print('Expert TEST server: http://127.0.0.1:'+str(server.server_port),flush=True)
    try:server.serve_forever()
    finally:server.server_close()

def run_mode(mode, output):
    initial = hashes(); error = None; code = None; browser = None; server = None; token = ''
    logs = dict(stdout='', stderr='', server=''); store_audit = None
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='v13-pregame-') as td:
        token_path = Path(td) / 'token'; database = Path(td) / 'work.sqlite'
        token = secrets.token_urlsafe(32); token_path.write_text(token + '\n'); token_path.chmod(0o600)
        fixture_path = Path(td) / 'fixture.json'; fixture_path.write_text(json.dumps(artifact_fixture()))
        try:
            command=[sys.executable,str(Path(__file__).resolve()),'--serve',mode,str(database),str(token_path)]
            with (output / 'server-stderr.log').open('w') as stderr:
                server = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=stderr, text=True)
                with selectors.DefaultSelector() as selector:
                    selector.register(server.stdout, selectors.EVENT_READ)
                    if not selector.select(timeout=20):
                        raise RuntimeError('Server readiness timeout')
                    startup = server.stdout.readline(); logs['server'] = startup
                url = startup.strip().split()[-1]
                if not url.startswith('http://127.0.0.1:'):
                    raise RuntimeError('Server did not announce loopback URL')
                env = dict(os.environ, WORKBENCH_URL=url, WORKBENCH_TOKEN_FILE=str(token_path),
                    EXPERT_EVIDENCE_DIR=str(output), EXPERT_REPO_ROOT=str(ROOT), EXPERT_BROWSER_MODE=mode,
                    EXPERT_ARTIFACT_FILE=str(fixture_path), EXPERT_SOURCE_HASHES=json.dumps(initial),
                    NODE_PATH=os.environ.get('NODE_PATH', '/opt/codex/cua_node/lib/node_modules'),
                    CHROMIUM_EXECUTABLE=os.environ.get('CHROMIUM_EXECUTABLE', '/usr/bin/chromium'))
                child = subprocess.run(['node', 'tests_expert/browser_experts.cjs'], cwd=ROOT,
                    env=env, text=True, capture_output=True, timeout=180)
                code = child.returncode; logs.update(stdout=child.stdout, stderr=child.stderr)
        except Exception as exc:
            error = str(exc)
            for name in ['stdout', 'stderr']:
                value = getattr(exc, name, None)
                if value:
                    logs[name] = value.decode(errors='replace') if isinstance(value, bytes) else value
        finally:
            if server:
                server.terminate()
                try: server.wait(timeout=10)
                except subprocess.TimeoutExpired: server.kill(); server.wait(timeout=10)
                logs['server'] += server.stdout.read(); server.stdout.close()
        for name, content in logs.items():
            (output / (name + '.log')).write_text(content.replace(token, '[REDACTED]'))
        stderr_path = output / 'server-stderr.log'
        if stderr_path.exists(): stderr_path.write_text(stderr_path.read_text().replace(token, '[REDACTED]'))
        research_path = Path(str(database) + '.research.sqlite')
        if research_path.exists():
            try:
                with sqlite3.connect(research_path) as connection:
                    rows = connection.execute('SELECT status,payload FROM knowledge_rules').fetchall()
                store_audit = dict(proposal_rows=len(rows),states=sorted({status for status,payload in rows}),
                    decision_rows=sum(json.loads(payload).get('schema_version') == 'knowledge-decision.v1' for status,payload in rows),
                    review_actor_rows=sum('review_decision' in json.loads(payload) for status,payload in rows))
            except Exception as exc:
                error = error or ('Stored review audit failed: ' + str(exc))
    try:
        browser = json.loads((output / 'receipt.json').read_text())
    except Exception as exc:
        error = error or ('Browser receipt unavailable: ' + str(exc))
    current = hashes(); declared_checks = browser.get('checks') if isinstance(browser, dict) else None
    checks = declared_checks if isinstance(declared_checks, list) and all(isinstance(c, dict) for c in declared_checks) else []
    validation = dict(receipt_present=isinstance(browser, dict),
        fresh_execution=bool(browser and browser.get('evidence_kind') == 'FRESH_BROWSER_EXECUTION'),
        exact_checks=bool(browser and browser.get('expected_check_ids') == EXPECTED_BROWSER_IDS == [c.get('id') for c in checks]),
        unique_checks=bool(checks and len({c.get('id') for c in checks}) == len(checks)),
        checks_passed=bool(checks and all(c.get('passed') is True for c in checks)),
        browser_passed=bool(browser and browser.get('passed') is True and browser.get('first_failure') is None),
        console_clean=bool(browser and browser.get('page_errors') == [] and browser.get('console_errors') == [] and browser.get('http_errors') == []),
        browser_version_present=bool(browser and browser.get('browser_version')),
        source_binding=bool(browser and browser.get('source_sha256') == current == initial),
        all_sources_present=len(current) == len(SOURCE_FILES),
        no_user_reviews_persisted=bool(store_audit and store_audit['proposal_rows'] == 2 and store_audit['decision_rows'] == 0 and
            store_audit['review_actor_rows'] == 0 and store_audit['states'] == ['EXPLORATORY']))
    passed = code == 0 and error is None and all(validation.values())
    result = dict(passed=passed, mode=mode, process_exit_code=code,
        runner_error=error.replace(token, '[REDACTED]') if error else None,
        validation=validation, check_count=len(checks), expected_check_count=len(EXPECTED_BROWSER_IDS),
        checks_passed=sum(c.get('passed') is True for c in checks),
        checks_failed=sum(c.get('passed') is not True for c in checks),
        checks_not_executed=max(0,len(EXPECTED_BROWSER_IDS)-len(checks)),
        failed_check_ids=[c.get('id') for c in checks if c.get('passed') is not True],
        first_failure=browser.get('first_failure') if browser else None,
        source_sha256=current, store_review_audit=store_audit,
        git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        github_binding={k:os.environ.get(k) for k in ['GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_REPOSITORY','GITHUB_WORKFLOW','GITHUB_JOB']},
        credential_handling='Disposable token file; credentials excluded from receipts and logs',
        scope='TEST manually authored artifact on normal server/store' if mode=='actual' else
        'TEST read-only REVIEWED reply fixture; actual rows stay EXPLORATORY; no expert acquisition',
        real_expert_acquisition='NOT_EVALUATED', coaching_accuracy=None)
    (output / 'runner.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    if len(sys.argv)==5 and sys.argv[1]=='--serve':serve(*sys.argv[2:]);return 0
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    output=ROOT/'evidence/queue'/('browser-experts-'+run_id)
    results={mode:run_mode(mode,output/mode) for mode in ['actual','synthetic']}
    result=dict(passed=all(r['passed'] for r in results.values()),finished_at=now(),evidence_directory=str(output),
        expected_total_checks=2*len(EXPECTED_BROWSER_IDS),actual_total_checks=sum(r['check_count'] for r in results.values()),modes=results)
    (output/'runner.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

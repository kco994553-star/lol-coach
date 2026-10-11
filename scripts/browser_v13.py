"""Fresh Chromium verification in private, disposable PRE_GAME servers.

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

ROOT = Path(os.environ.get('PREGAME_REPO_ROOT', Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0, str(ROOT))
SOURCE_FILES = sorted(str(p.relative_to(ROOT)) for folder in
    ['contracts', 'coach_v1', 'web_r4', 'tests_pregame', 'scripts', 'knowledge_candidates']
    for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts
    and p.suffix in {'.py', '.cjs', '.js', '.html', '.css', '.svg', '.json', '.md'})
ROLES = ['TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT']
ALLY = ['Ornn', 'Sejuani', 'Ahri', 'Caitlyn', 'Lux']
ENEMY = ['Fiora', 'LeeSin', 'Zed', 'Ezreal', 'Nautilus']
PATCH = '16.19'
EXPECTED_BROWSER_IDS = ['connected', 'legacy-input-shape'] + [r + '-' + c for r in ROLES for c in
    ['nine-cards', 'common-identity', 'guard-state', 'operations-state', 'movement-state',
     'five-mini-graphs', 'lane-graph', 'dirty-hides']] + [
    'explicit-pick-metadata', 'metadata-reopen', 'power-renderer-ci-gaps', 'power-markers',
    'power-synthetic-gates', 'power-fallback-labels', 'power-late-dirty', 'power-late-logout',
    'no-decisions', 'no-browser-errors']


def now():
    return datetime.now(timezone.utc).isoformat()


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES if (ROOT / name).is_file()}


def synthetic_pairs():
    """Transient synthetic raw pairs. Only validated public aggregates are exposed."""
    pairs = []
    for match_index in range(30):
        participants = [dict(participantId=offset+i+1,teamId=team,teamPosition=position,
            championName=champions[i]) for team, offset, champions in [(100,0,ALLY),(200,5,ENEMY)]
            for i, position in enumerate(ROLES)]
        frames = []
        for minute in range(1,6):
            frames.append(dict(timestamp=minute*60000,participantFrames={str(p['participantId']):
                dict(totalGold=500+minute*(100+p['participantId']*10)+match_index*3,
                     xp=minute*(200+p['participantId']*5)+match_index*2,
                     minionsKilled=minute*5+match_index%3,jungleMinionsKilled=0,
                     level={1:2,2:3,3:6,4:11,5:16}[minute],
                     position=dict(x=(p['participantId']%5)*200+match_index,
                                   y=(p['participantId']%5)*200-match_index)) for p in participants},
                events=[dict(type='ITEM_PURCHASED',participantId=p['participantId'],
                    itemId=3001 if minute==2 else 3002,timestamp=minute*60000)
                    for p in participants] if minute in (2,4) else []))
        metadata=dict(matchId='KR_SYNTHETIC_BROWSER_'+str(match_index))
        pairs.append(dict(match=dict(metadata=metadata,info=dict(queueId=420,mapId=11,
            gameMode='CLASSIC',gameVersion=PATCH+'.1',gameStartTimestamp=100000,
            gameDuration=300,participants=participants)),timeline=dict(metadata=metadata,
            info=dict(frames=frames,frameInterval=60000))))
    return pairs


def synthetic_statistics():
    from coach_v1.power_stats import build_power_dataset
    from coach_v1.movement import build_movement_dataset
    source=dict(provider='SYNTHETIC',platform='KR',regional='ASIA',queue_id=420,map_id=11,
        tier='GOLD',patch=PATCH,window_start=None,window_end=None,
        retrieved_at='2026-10-11T00:00:00Z',sample_kind='SYNTHETIC',
        endpoints=['MATCH_V5_MATCH','MATCH_V5_TIMELINE'])
    pairs=synthetic_pairs()
    annotations=[dict(match_sha256=hashlib.sha256(p['match']['metadata']['matchId'].encode()).hexdigest(),
        timestamp_ms=minute*60000,stage=stage,stage_conditions=[dict(field=field,value=True)],
        source_sha256='a'*64,source_pointer='/synthetic/phase/'+str(minute),verification='VERIFIED')
        for p in pairs for minute,stage,field in [(1,'EARLY','LANING_ACTIVE'),
            (2,'MID','FIRST_TURRET_DESTROYED'),(3,'LATE','LONG_RESPAWN_RISK')]]
    return (build_power_dataset(pairs,source=source,complete_item_ids=(3001,3002)),
            build_movement_dataset(pairs,source=source,phase_annotations=annotations))


def synthetic_specs(movement):
    from tests_pregame.test_v13 import v2_rule
    from coach_v1.state import digest
    specs=[]
    def base(section,position='BOTTOM'):
        spec=v2_rule(section,position);spec['patches']=[PATCH]
        for source in spec['sources']:source.update(patch=PATCH,sha256='b'*64)
        spec['rule_id']='v13-'+position.lower()+'-'+section.lower()
        spec['output']['text']='SYNTHETIC fixture '+position+' '+section
        return spec
    for section in ['MAP','JUNGLE','COMPOSITION']:
        spec=base(section);spec['rule_id']='v13-common-'+section.lower();spec['output']['target']='GLOBAL';specs.append(spec)
    for position,champion in zip(ROLES,ALLY):
        for section in ['ROLE','LANE','FIGHT','OPERATIONS']:specs.append(base(section,position))
        spec=base('ROLE',position);spec['schema_version']='pregame.rule.v3'
        spec['rule_id']='v14-'+position.lower()+'-movement';spec['output'].update(section='MOVEMENT',movement=[])
        for stage,field in [('EARLY','LANING_ACTIVE'),('MID','FIRST_TURRET_DESTROYED'),('LATE','LONG_RESPAWN_RISK')]:
            cohort=next(c for c in movement['cohorts'] if c['champion']==champion and
                c['position']==position and c['stage']==stage)
            spec['output']['movement'].append(dict(stage=stage,layer='DEFAULT',subject='SELF',position=position,
                location='HOME_LANE' if stage=='EARLY' else 'MAIN_GROUP',role='SYNTHETIC role',
                why='SYNTHETIC rationale',exceptions=['SYNTHETIC exception'],
                stage_conditions=[dict(field=field,value=True)],overrides=[],
                statistics_ref=dict(dataset_sha256=digest(movement),cohort_id=cohort['id'])))
        specs.append(spec)
    return specs


def fixture_knowledge(specs):
    """Pure dict fixtures, no USER_WEB actor or actual review authority."""
    from coach_v1.pregame_contract import proposal_rule
    return [dict(proposal=dict(proposal_rule(s), schema_version='knowledge-proposal.v1',
        rule_id=s['rule_id'], version='v13-synthetic-view-1', review_state='REVIEWED',
        source_refs=[], supersedes=None, coaching_enabled=False), spec=copy.deepcopy(s)) for s in specs]


def serve_synthetic(database, token_file):
    from coach_v1 import pregame_server as module
    from coach_v1.server import Limits
    from coach_v1.pregame_contract import proposal_rule
    from coach_v1.state import digest
    server = module.PregameWorkbench(Path(database), Path(token_file).read_text().strip(),
                                     Limits(10_000_000, 1000, 100, 100, 100, 10))
    power,movement=synthetic_statistics();specs = synthetic_specs(movement); view = []
    # Expanded immutable v3 history contains full source-bound specs; this disposable fixture
    # server uses a 10MB response cap. Production defaults are unchanged.
    server.test_mode=True;server.power_data=power;server.movement_statistics=movement
    for spec in specs:
        source = server.research.add('RAW_DIAGNOSTIC', 'SYNTHETIC V13/V14 fixture',
            dict(schema_version=spec['schema_version'].replace('pregame.rule.', 'pregame.rule-source.'), spec=spec))
        note = server.research.put_note(source['id'], 'overview',
            dict(known='SYNTHETIC fixture sha256:' + digest(spec), intention='Test only',
                 alternative='', outcome='No gameplay validation'), 0)
        proposal = server.research.propose(proposal_rule(spec),
            dict(resource_id=source['id'], anchor='overview', note_revision=note['revision']),
            max_bytes=1_000_000)
        # Stored rows remain EXPLORATORY. Only the test view changes state.
        view.append(dict(proposal=dict(proposal, review_state='REVIEWED'), spec=spec))
    module.current_knowledge = lambda research: copy.deepcopy(view)
    print('SYNTHETIC test view: http://127.0.0.1:' + str(server.server_port) + '/pregame', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def run_mode(mode, output):
    initial = hashes(); error = None; code = None; browser = None; server = None; token = ''
    logs = dict(stdout='', stderr='', server=''); store_audit = None
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='v13-pregame-') as td:
        token_path = Path(td) / 'token'; database = Path(td) / 'work.sqlite'
        token = secrets.token_urlsafe(32); token_path.write_text(token + '\n'); token_path.chmod(0o600)
        fixture_path = Path(td) / 'fixture.json'; fixture_path.write_text('{}')
        try:
            if mode == 'synthetic':
                command = [sys.executable, str(Path(__file__).resolve()), '--serve-synthetic', str(database), str(token_path)]
            else:
                command = [sys.executable, '-m', 'coach_v1.pregame_server', '--db', str(database),
                    '--token-file', str(token_path), '--port', '0', '--max-body-bytes', '10000000',
                    '--max-observations', '1000', '--max-actions', '100', '--max-scenarios', '100',
                    '--max-comparisons', '100', '--max-pending-jobs', '10']
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
                    PREGAME_V13_EVIDENCE_DIR=str(output), PREGAME_REPO_ROOT=str(ROOT), PREGAME_SYNTHETIC_PATCH=PATCH, PREGAME_BROWSER_MODE=mode,
                    PREGAME_FIXTURE_FILE=str(fixture_path), PREGAME_SOURCE_HASHES=json.dumps(initial),
                    NODE_PATH=os.environ.get('NODE_PATH', '/opt/codex/cua_node/lib/node_modules'),
                    CHROMIUM_EXECUTABLE=os.environ.get('CHROMIUM_EXECUTABLE', '/usr/bin/chromium'))
                child = subprocess.run(['node', 'tests_pregame/browser_v13.cjs'], cwd=ROOT,
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
        no_user_reviews_persisted=bool(store_audit and store_audit['decision_rows'] == 0 and
            store_audit['review_actor_rows'] == 0 and store_audit['states'] == ([] if mode=='actual' else ['EXPLORATORY'])))
    passed = code == 0 and error is None and all(validation.values())
    result = dict(passed=passed, mode=mode, process_exit_code=code,
        runner_error=error.replace(token, '[REDACTED]') if error else None,
        validation=validation, check_count=len(checks), expected_check_count=len(EXPECTED_BROWSER_IDS),
        checks_passed=sum(c.get('passed') is True for c in checks),
        checks_failed=sum(c.get('passed') is not True for c in checks),
        checks_not_executed=max(0,len(EXPECTED_BROWSER_IDS)-len(checks)),
        source_sha256=current, store_review_audit=store_audit,
        git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        github_binding={k:os.environ.get(k) for k in ['GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_REPOSITORY','GITHUB_WORKFLOW','GITHUB_JOB']},
        credential_handling='Disposable token file; credentials excluded from receipts and logs',
        scope='Actual Golden10 normal empty knowledge; no authoritative current gameplay patch' if mode == 'actual' else
        'SYNTHETIC read-only reviewed fixture view over isolated EXPLORATORY source-bound proposals; does not prove actual approval persistence',
        real_match_validation='NOT_EVALUATED', coaching_accuracy=None)
    (output / 'runner.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--serve-synthetic':
        serve_synthetic(sys.argv[2], sys.argv[3]); return 0
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
    output = ROOT / 'evidence/queue' / ('browser-v13-' + run_id)
    results = {mode:run_mode(mode, output / mode) for mode in ['actual', 'synthetic']}
    result = dict(passed=all(r['passed'] for r in results.values()), finished_at=now(),
                  evidence_directory=str(output), expected_total_checks=2*len(EXPECTED_BROWSER_IDS),
                  actual_total_checks=sum(r['check_count'] for r in results.values()), modes=results)
    (output / 'runner.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], evidence_directory=str(output),
        expected_total_checks=result['expected_total_checks'], actual_total_checks=result['actual_total_checks'],
        modes={m:{k:r[k] for k in ['passed','check_count','expected_check_count','checks_passed','checks_failed','checks_not_executed','runner_error']} for m,r in results.items()})))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

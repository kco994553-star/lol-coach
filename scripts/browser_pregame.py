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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCE_FILES = ['contracts/pregame-v3-amendment.md','.github/workflows/riot-power-collection.yml','contracts/pregame-v2.md','contracts/pregame-v3.md',
    'coach_v1/pregame_v2.py','coach_v1/pregame_v3.py','coach_v1/movement.py',
    'coach_v1/power_stats.py','coach_v1/riot_collector.py','web_r4/pregame_power.js',
    'knowledge_candidates/initiative-v2.json','scripts/browser_v13.py','tests_pregame/browser_v13.cjs',
    'scripts/verify_queue_extensions.py','contracts/pregame-v1.md', 'docs/queue/API.md',
    'coach_v1/pregame_contract.py', 'coach_v1/pregame_evaluator.py',
    'coach_v1/pregame_store.py', 'coach_v1/pregame_server.py',
    'coach_v1/server.py', 'coach_v1/knowledge.py', 'coach_v1/research.py',
    'web_r4/pregame.html', 'web_r4/pregame.js', 'web_r4/pregame.css',
    'tests_pregame/browser_pregame.cjs', 'scripts/browser_pregame.py',
    'scripts/verify_pregame.py', 'tests_pregame/test_contract.py',
    'tests_pregame/test_evaluator.py', 'tests_pregame/test_store.py',
    'tests_pregame/test_http.py', 'knowledge_candidates/executable-v1.json',
    'knowledge_candidates/q05-review-priority.json', 'knowledge_candidates/q05-roster-profiles.json',
    '.github/workflows/pregame-ci.yml', 'web_r4/pregame-icon.svg',
    'tests_pregame/ui_pregame_pending_save.cjs',
    'knowledge_candidates/executable-expanded-v1.json',
    'evidence/queue/q05-expansion/validate.py',
    'evidence/queue/q05-expanded-adapter/validate.py',
    'evidence/queue/q05-expanded-adapter/manifest.json',
    'evidence/queue/q05-expansion/classify.py',
    'evidence/queue/q05-expansion/mechanic-audit.json',
    'evidence/queue/q05-expansion/source-receipts.json',
    'evidence/queue/q05-expansion/initial-source-manifest.json',
    'evidence/queue/q05-expansion/initial-roster.json']

EXPECTED_BROWSER_IDS = ['connected'] + [p + '-' + check for p in
    ['TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT'] for check in
    ['exact-input', 'nine-cards', 'selected-map-row', 'common-invariant',
     'personal-context', 'detail-input-binding', 'immutable-reopen', 'edit-hides-plan']] + [
    'source-preview', 'source-navigation', 'proposal-only-import', 'untrusted-approval-blocked',
    'empty-patch-approval-disabled', 'export-history', 'mobile-layout', 'logout-clears',
    'no-user-decisions', 'no-browser-errors', 'source-hashes-stable']


def now():
    return datetime.now(timezone.utc).isoformat()


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES if (ROOT / name).is_file()}


def synthetic_specs():
    from tests_pregame.test_contract import rule
    specs = []
    for section in ['MAP', 'JUNGLE', 'COMPOSITION']:
        s = rule(section); s['rule_id'] = 'q09-common-' + section.lower()
        s['output']['text'] = 'SYNTHETIC fixture common ' + section
        specs.append(s)
    for position in ['TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT']:
        for section in ['ROLE', 'LANE', 'FIGHT']:
            s = rule(section, position); s['rule_id'] = 'q09-' + position.lower() + '-' + section.lower()
            s['output']['text'] = 'SYNTHETIC fixture ' + position + ' ' + section
            specs.append(s)
    return specs


def fixture_knowledge(specs):
    """Pure dict fixtures, no USER_WEB actor or actual review authority."""
    from coach_v1.pregame_contract import proposal_rule
    return [dict(proposal=dict(proposal_rule(s), schema_version='knowledge-proposal.v1',
        rule_id=s['rule_id'], version='q09-synthetic-view-1', review_state='REVIEWED',
        source_refs=[], supersedes=None, coaching_enabled=False), spec=copy.deepcopy(s)) for s in specs]


def serve_synthetic(database, token_file):
    from coach_v1 import pregame_server as module
    from coach_v1.server import Limits
    from coach_v1.pregame_contract import proposal_rule
    from coach_v1.state import digest
    server = module.PregameWorkbench(Path(database), Path(token_file).read_text().strip(),
                                     Limits(1_000_000, 1000, 100, 100, 100, 10))
    specs = synthetic_specs(); view = []
    for spec in specs:
        source = server.research.add('RAW_DIAGNOSTIC', 'SYNTHETIC Q09 fixture',
            dict(schema_version='pregame.rule-source.v1', spec=spec))
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
    with tempfile.TemporaryDirectory(prefix='q09-pregame-') as td:
        token_path = Path(td) / 'token'; database = Path(td) / 'work.sqlite'
        token = secrets.token_urlsafe(32); token_path.write_text(token + '\n'); token_path.chmod(0o600)
        fixture_path = Path(td) / 'fixture.json'; fixture_path.write_text(json.dumps(synthetic_specs()[0]))
        try:
            if mode == 'synthetic':
                command = [sys.executable, str(Path(__file__).resolve()), '--serve-synthetic', str(database), str(token_path)]
            else:
                command = [sys.executable, '-m', 'coach_v1.pregame_server', '--db', str(database),
                    '--token-file', str(token_path), '--port', '0', '--max-body-bytes', '1000000',
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
                    PREGAME_BROWSER_EVIDENCE_DIR=str(output), PREGAME_BROWSER_MODE=mode,
                    PREGAME_FIXTURE_FILE=str(fixture_path), PREGAME_SOURCE_HASHES=json.dumps(initial),
                    NODE_PATH=os.environ.get('NODE_PATH', '/opt/codex/cua_node/lib/node_modules'),
                    CHROMIUM_EXECUTABLE=os.environ.get('CHROMIUM_EXECUTABLE', '/usr/bin/chromium'))
                child = subprocess.run(['node', 'tests_pregame/browser_pregame.cjs'], cwd=ROOT,
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
            store_audit['review_actor_rows'] == 0 and store_audit['states'] == ['EXPLORATORY']))
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
    output = ROOT / 'evidence/queue' / ('browser-' + run_id)
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

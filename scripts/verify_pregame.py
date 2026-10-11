"""Targeted additive contract, evaluator, store, HTTP, and golden-flow verifier.

This does not replace legacy verification or claim actual coaching accuracy.
"""
from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.browser_pregame import fixture_knowledge, hashes, synthetic_specs

EXPECTED_SEMANTIC_IDS = ['actual-unknown-patch-common-equality', 'actual-personal-context-differs',
    'actual-personal-unknown-reasons', 'synthetic-common-equality',
    'synthetic-personal-role-lane-fight-differ', 'missing-required-runes-unknown',
    'partial-required-runes-unknown', 'patch-mismatch-excluded', 'current-review-change-withholds',
    'stored-plan-exact-reopen', 'review-changes-expire-plan', 'position-update-expires-immutable-plan']


def semantic_checks():
    from coach_v1.pregame_contract import parse_input
    from coach_v1.pregame_evaluator import evaluate_gameplan, knowledge_fingerprint
    from coach_v1.pregame_store import PregameStore
    from tests_pregame.test_contract import golden, rule
    checks = []
    def check(name, passed, details=None):
        checks.append(dict(id=name, passed=bool(passed), details=details))
    knowledge = fixture_knowledge(synthetic_specs())
    roles = ['TOP','JUNGLE','MID','BOTTOM','SUPPORT']
    actual = [evaluate_gameplan(parse_input(golden(p)), []) for p in roles]
    check('actual-unknown-patch-common-equality', all(r['common'] == actual[0]['common'] for r in actual))
    check('actual-personal-context-differs', len({json.dumps(r['personal'],sort_keys=True) for r in actual}) == 5)
    check('actual-personal-unknown-reasons', all(c['status'] == 'UNKNOWN' and not c['texts'] and c['reasons'] for r in actual for c in r['personal'].values()))
    plans = [evaluate_gameplan(golden(p,patch='SYNTHETIC-1'), knowledge) for p in roles]
    check('synthetic-common-equality', all(r['common'] == plans[0]['common'] for r in plans))
    check('synthetic-personal-role-lane-fight-differ', all(
        r['personal'][section]['texts'] == ['SYNTHETIC fixture '+p+' '+section.upper()]
        for p,r in zip(roles,plans) for section in ['role','lane','fight']))
    s = rule(); s['required_fields'] = ['enemy.BOTTOM.runes']; k = fixture_knowledge([s])
    d = golden(patch='SYNTHETIC-1')
    trace = evaluate_gameplan(d,k)['evaluations'][0]
    check('missing-required-runes-unknown', trace['condition'] == 'UNKNOWN' and trace['missing_fields'] == s['required_fields'])
    d['slots'][8]['runes'].update(status='PARTIAL',values=['known'])
    trace = evaluate_gameplan(d,k)['evaluations'][0]
    check('partial-required-runes-unknown', trace['condition'] == 'UNKNOWN' and trace['missing_fields'] == s['required_fields'])
    d['patch'] = 'DIFFERENT-PATCH'; trace = evaluate_gameplan(d,k)['evaluations'][0]
    check('patch-mismatch-excluded', trace['condition'] == 'FALSE' and trace['status'] == 'EXCLUDED')
    changed = copy.deepcopy(knowledge)
    for item in changed: item['proposal'].update(review_state='REJECTED', version='synthetic-head-2')
    rejected = evaluate_gameplan(golden(patch='SYNTHETIC-1'), changed)
    check('current-review-change-withholds', all(not c['texts'] for c in rejected['personal'].values()) and
        rejected['knowledge_fingerprint'] != plans[0]['knowledge_fingerprint'])
    with tempfile.TemporaryDirectory(prefix='q09-verify-') as td:
        store = PregameStore(Path(td)/'isolated.sqlite')
        record = store.save(golden(patch='SYNTHETIC-1'),None,0,'save')
        result = evaluate_gameplan(record['input'],knowledge)
        saved = store.save_plan(record['session_id'],1,result,'plan')
        reopened = PregameStore(Path(td)/'isolated.sqlite').get_plan(saved['id'],knowledge_fingerprint(knowledge))
        check('stored-plan-exact-reopen', {k:v for k,v in reopened.items() if k not in ['validity','expiry_reasons']} == saved and reopened['validity'] == 'CURRENT')
        changed_plan = store.get_plan(saved['id'],knowledge_fingerprint(changed))
        check('review-changes-expire-plan', changed_plan['validity'] == 'EXPIRED' and 'KNOWLEDGE_CHANGED' in changed_plan['expiry_reasons'])
        store.save(golden('TOP',patch='SYNTHETIC-1'),record['session_id'],1,'position-change')
        expired = store.get_plan(saved['id'],knowledge_fingerprint(knowledge))
        check('position-update-expires-immutable-plan', expired['validity'] == 'EXPIRED' and
            'INPUT_REVISION_CHANGED' in expired['expiry_reasons'] and expired['input'] == saved['input'])
    return checks


def main():
    out = ROOT/'evidence/queue'/('q09-verifier-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    before = hashes(); errors = []; results = {}; semantic = []
    expected_minimum = {'test_contract':9,'test_evaluator':22,'test_store':7,'test_http':7}
    for module, minimum in expected_minimum.items():
        stream = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromName('tests_pregame.'+module)
        result = unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        (out/(module+'.log')).write_text(stream.getvalue())
        results[module] = dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
            skipped=len(result.skipped),passed=result.wasSuccessful() and result.testsRun >= minimum and not result.skipped)
    try:
        semantic = semantic_checks()
    except Exception as exc:
        errors.append(type(exc).__name__+': '+str(exc))
    after = hashes()
    report = dict(passed=all(r['passed'] for r in results.values()) and
        [c['id'] for c in semantic] == EXPECTED_SEMANTIC_IDS and
        all(c['passed'] for c in semantic) and not errors and before == after,
        evidence_kind='FRESH_SCOPED_PREGAME_VERIFICATION', suites=results,semantic_checks=semantic,
        expected_semantic_ids=EXPECTED_SEMANTIC_IDS,tests_run=sum(r['tests_run'] for r in results.values()),
        runner_errors=errors,source_sha256=after,sources_unchanged=before == after,
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        github_binding={k:os.environ.get(k) for k in ['GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_REPOSITORY']},
        synthetic_scope='Pure read-only REVIEWED test dicts; no USER_WEB authority or decisions, no approval persistence claim',
        real_match_validation='NOT_EVALUATED',coaching_accuracy=None,browser_e2e_executed=False)
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],evidence_directory=str(out),suites=results,
                         semantic_checks=len(semantic),semantic_failures=[c['id'] for c in semantic if not c['passed']],errors=errors)))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

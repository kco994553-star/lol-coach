"""Fresh source-bound expert plumbing checks; no source truth or API acquisition."""
import io
from contextlib import redirect_stdout, redirect_stderr
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import uuid
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.browser_experts import hashes


def main():
    out=ROOT/'evidence/queue'/('expert-verifier-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False);before=hashes();results={}
    minimum={'tests_expert.test_contract':10,'tests_expert.test_bridge':13,'tests_expert.test_measurement':15,
        'tests_expert.test_http':7,'tests_expert.test_collector':24,'tests_expert.test_entitlement':13,
        'tests_expert.test_video_korean':5,'tests_expert.test_preservation':3,'tests_expert.test_segments':17,'tests_expert.test_diagnostics':14,'tests_expert.test_diagnostic_cli':6,'tests_expert.test_probe_receipt_v2':3,'tests_expert.test_generatecontent':9,'tests_expert.test_v20_front':20}
    for name,count in minimum.items():
        stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromName(name)
        # CLI fixtures print safe status receipts; keep them in the suite log so
        # the launcher emits exactly one JSON object for required CI consumers.
        with redirect_stdout(stream), redirect_stderr(stream):
            run=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        (out/(name+'.log')).write_text(stream.getvalue())
        results[name]=dict(tests_run=run.testsRun,failures=len(run.failures),errors=len(run.errors),skipped=len(run.skipped),
            passed=run.wasSuccessful() and run.testsRun>=count and not run.skipped)
    from coach_v1.expert_collector import validate_config
    config=validate_config(json.loads((ROOT/'config/expert_channels.json').read_text()))
    receipt=dict(passed=all(r['passed'] for r in results.values()) and before==hashes(),
        evidence_kind='FRESH_EXPERT_PLUMBING_VERIFICATION',suites=results,tests_run=sum(r['tests_run'] for r in results.values()),
        source_sha256=hashes(),sources_unchanged=before==hashes(),
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        github_binding={k:os.environ.get(k) for k in ['GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_REPOSITORY']},
        approved_channels=len(config['channels']),disabled_channels=sum(not c['enabled'] for c in config['channels']),
        live_api_calls=0,actual_expert_claims_verified=0,coaching_accuracy=None,
        scope='Authored TEST statements/fake provider responses; no USER_WEB decisions or factual expert validation')
    (out/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(out),tests_run=receipt['tests_run'],suites=results)))
    return 0 if receipt['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

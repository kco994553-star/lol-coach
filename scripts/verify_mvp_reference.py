"""Bind reference-first operation to its exact practical-review predecessor.

Both historical contracts and verifiers remain unchanged. This entrypoint
accepts only recorded successor bytes and the archived official sources.
"""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import verify_mvp_practical as prior

CURRENT_PATHS={'coach_v1/official_reference.py','coach_v1/review_queue.py','coach_v1/pregame_server.py',
    'web_r4/official_reference.js','web_r4/pregame.js','web_r4/pregame.html','web_r4/review_queue.js','web_r4/review_queue.html',
    'AGENTS.md','data/official_reference/2026-10-14/manifest.json','scripts/collect_official_reference.py',
    'scripts/browser_reference_first.py','scripts/browser_practical_review.py','tests_pregame/test_reference_first.py','tests_pregame/test_practical_binding.py'}


def reference_binding():
    try:
        sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
        binding=json.loads((ROOT/'contracts/amendments/2026-10-14-reference-first.json').read_text())
        predecessor=json.loads((ROOT/binding['parent_amendment']).read_text())
        checks=dict(explicit_user_direction=binding['authority']=='USER_REFERENCE_FIRST_2026-10-14',
            parent_contract_unchanged=sha(binding['parent_amendment'])==binding['parent_amendment_sha256'],
            exact_paths=set(binding['current_sha256'])==CURRENT_PATHS,
            current_bytes=all(sha(p)==h for p,h in binding['current_sha256'].items()),
            exact_archive_directory=binding['parent_directory']=='evidence/queue/reference-first/parent',
            preserved_predecessors=all(sha(binding['parent_directory']+'/'+p)==h for p,h in predecessor['current_sha256'].items()),
            unchanged_other_paths=all(p in CURRENT_PATHS or sha(p)==h for p,h in predecessor['current_sha256'].items()),
            source_bytes=all(sha(p)==h for p,h in binding['official_source_sha256'].items()),
            frozen_unchanged=sha('FREEZE_MANIFEST.json')==binding['parent_freeze_sha256'],
            contract_bound=sha(binding['contract'])==binding['contract_sha256'],
            reference_only=binding['reference_only'] is True and binding['automatic_user_approval'] is False,
            no_sql_or_engine_activation=binding['sql_schema_change'] is False and binding['engine_activation'] is False)
        manifest=json.loads((ROOT/'data/official_reference/2026-10-14/manifest.json').read_text())
        files={'data/official_reference/2026-10-14/'+s['file']:s['sha256'] for s in manifest['sources']}
        checks['exact_official_sources']=files==binding['official_source_sha256'] and len(files)==13
        return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks)
    except (OSError,ValueError,KeyError,TypeError):return dict(status='FAIL',checks={'binding_readable':False})


def main():
    base=prior.practical_binding
    def chained_practical():
        historical=base();reference=reference_binding()
        result=dict(historical,checks=dict(historical['checks']),historical_result=historical,reference_first_source_binding=reference)
        result['checks']['current_bytes']=reference['status']=='PASS'
        result['status']='PASS' if all(result['checks'].values()) else 'FAIL'
        return result
    prior.practical_binding=chained_practical
    try:return prior.main()
    finally:prior.practical_binding=base


if __name__=='__main__':raise SystemExit(main())

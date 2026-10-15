"""Extend preserved verification with the USER-authorized GitHub channel.

Historical verifier/receipts keep their original bytes. Only the exact archived
knowledge.py successor chain is admitted; unrelated changes still fail.
"""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import verify_mvp_experts as experts
original=experts.original


def practical_binding():
    try:
        sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
        binding=json.loads((ROOT/'contracts/amendments/2026-10-14-practical-review.json').read_text())
        predecessor=json.loads((ROOT/'evidence/mvp/knowledge-review-version.json').read_text())
        initial_parent=json.loads((ROOT/'evidence/mvp/knowledge-review-parent.json').read_text())
        expected={'coach_v1/knowledge.py','coach_v1/practical_review.py','coach_v1/review_queue.py','coach_v1/pregame_server.py','knowledge_candidates/practical-review-v1.json','config/practical_review_issues.json','web_r4/review_queue.js','web_r4/review_queue.html','scripts/import_github_review.py','scripts/browser_practical_review.py','tests_pregame/test_practical_review.py','AGENTS.md'}
        checks=dict(explicit_user_authority=binding['authority']=='USER_DECISION_2026-10-14',
            exact_paths=set(binding['current_sha256'])==expected,
            current_bytes=all(sha(p)==h for p,h in binding['current_sha256'].items()),
            exact_parent_archive=binding['parent_archive']=='evidence/queue/practical-review-20261014/parent/knowledge.py',
            archived_predecessor=sha(binding['parent_archive'])==binding['parent_sha256']==predecessor['current_sha256']['coach_v1/knowledge.py'],
            archived_initial_parent=sha('evidence/mvp/knowledge-review-parent/coach_v1/knowledge.py')==initial_parent['prior_sha256']['coach_v1/knowledge.py'],
            original_review_binding_preserved=sha('evidence/mvp/knowledge-review-version.json')==binding['parent_review_binding_sha256'],
            frozen_unchanged=sha('FREEZE_MANIFEST.json')==binding['parent_freeze_sha256'],
            historical_verifier_unchanged=sha('scripts/verify_mvp.py')==predecessor['current_sha256']['scripts/verify_mvp.py'],
            contract_bound=sha(binding['contract'])==binding['contract_sha256'],
            no_ai_or_engine_activation=binding['ai_consensus_promotion_allowed'] is False and binding['engine_activation'] is False,
            no_sql_change=binding['sql_schema_change'] is False)
        return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks)
    except (OSError,ValueError,KeyError,TypeError):return dict(status='FAIL',checks={'binding_readable':False})


def main():
    binding=practical_binding()
    parent_sha=original.review_parent_sha;review_binding=original.knowledge_review_binding
    def chained_parent(path):
        if path=='coach_v1/knowledge.py' and binding['status']=='PASS':
            return original.read_json(ROOT/'evidence/mvp/knowledge-review-parent.json')['prior_sha256'][path]
        return parent_sha(path)
    def chained_review():
        historical=review_binding()
        result=dict(historical,checks=dict(historical['checks']),historical_result=historical,practical_user_version_binding=binding)
        # Validate all other original current paths exactly. The sole changed
        # path must bind the archived predecessor and exact authorized successor.
        version=original.read_json(ROOT/'evidence/mvp/knowledge-review-version.json')
        exact=all(original.sha(ROOT/p)==h for p,h in version['current_sha256'].items() if p!='coach_v1/knowledge.py')
        result['checks']['current_bytes_bound']=exact and binding['status']=='PASS'
        result['status']='PASS' if all(result['checks'].values()) else 'FAIL'
        return result
    original.review_parent_sha=chained_parent;original.knowledge_review_binding=chained_review
    try:return experts.main()
    finally:original.review_parent_sha=parent_sha;original.knowledge_review_binding=review_binding


if __name__=='__main__':raise SystemExit(main())

"""Queue v2.3 delta verification; completed v2.1 verification is reused, never run.

The parent tree and successful GitHub CI receipts are immutable historical inputs.
--prepare prints an unsealed candidate; Main seals only after source edits finish.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'fedc30060259b5eeac4ab2ca096daa6259e354b6'
AMENDMENT = 'contracts/amendments/2026-10-15-queue-v23.json'
PARENT_AMENDMENT = 'contracts/amendments/2026-10-15-queue-v21.json'
PARENT_DIRECTORY = 'evidence/queue/v23/parent'
PARENT_RECEIPT = PARENT_DIRECTORY + '/git-head.json'
PARENT_RECEIPT_SHA256 = '684093a61590aff3fa41d8ff853f5501ca0361d476b20bbe5fe5b8e9ae76594d'
BASE_TREE = PARENT_DIRECTORY + '/base-tree.json'
CONTRACT = 'contracts/queue-v23.md'
MODIFIED_PATHS = {
    'coach_v1/pc_coach.py', 'coach_v1/pc_runtime.py', 'coach_v1/pregame_server.py',
    'web_r4/pc.js', 'web_r4/pc.css', 'web_r4/postgame.js',
    '.github/workflows/pregame-ci.yml', '.github/workflows/private-mvp-ci.yml',
    'CURRENT_HANDOFF.md', 'docs/queue/QUEUE.md',
}
CURRENT_PATHS = MODIFIED_PATHS | {
    'coach_v1/recall_pc.py', 'coach_v1/recall_candidates.py', 'coach_v1/recall_stats.py',
    'coach_v1/recall_collection.py', 'coach_v1/official_items.py',
    'scripts/collect_recall_stats.py', 'scripts/browser_recall_v23.py', 'scripts/browser_recall_actual_v23.py',
    'scripts/report_queue_v23.py', 'scripts/verify_mvp_v23.py',
    '.github/workflows/recall-reference-collection.yml',
    'tests_pregame/test_recall_pc_v23.py', 'tests_pregame/test_recall_stats_v23.py',
    'tests_pregame/test_recall_collection_v23.py', 'tests_pregame/test_official_items_v23.py',
    'tests_pregame/test_recall_candidates_v23.py', 'tests_pregame/test_v23_binding.py',
    'knowledge_candidates/recall-v23.json', CONTRACT,
    'evidence/queue/v23/candidate-author-build.py',
    'docs/superpowers/plans/2026-10-15-queue-v23.md', 'docs/queue/V23_OPERATION.md',
}
DELTA_TESTS = [
    'tests_pregame.test_v23_binding', 'tests_pregame.test_recall_stats_v23',
    'tests_pregame.test_recall_collection_v23', 'tests_pregame.test_official_items_v23',
    'tests_pregame.test_recall_candidates_v23', 'tests_pregame.test_recall_pc_v23',
]
CI_RUNS = [(38722880438, '.github/workflows/private-mvp-ci.yml'),
           (38722880374, '.github/workflows/pregame-ci.yml')]


def sha(path):
    relative = Path(path)
    target = ROOT / relative
    if relative.is_absolute() or '..' in relative.parts or any(p.is_symlink() for p in [target, *target.parents]):
        raise ValueError('unsafe binding path')
    return hashlib.sha256(target.read_bytes()).hexdigest()


def _read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def _git(*arguments):
    return subprocess.check_output(['git', *arguments], cwd=ROOT, stderr=subprocess.DEVNULL)


def _inventory():
    return set(_git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')) - {''}


def _data_paths():
    return {str(path.relative_to(ROOT)) for folder in ('data/official_items', 'data/recall')
            for path in (ROOT / folder).rglob('*') if path.is_file()}


def _evidence_path(path):
    # Generated verification output is not executable source authority.
    return path.startswith('evidence/queue/v23/') and not path.startswith(PARENT_DIRECTORY + '/') and Path(path).suffix in {
        '.json', '.log', '.txt', '.md', '.png', '.html', '.csv',
    }


def required_paths():
    tree = _read(BASE_TREE)['sha256']
    receipt = _read(PARENT_RECEIPT)
    return (set(tree) | CURRENT_PATHS | {BASE_TREE, PARENT_RECEIPT} |
            {PARENT_DIRECTORY + '/' + path for path in receipt['sha256']} |
            {PARENT_DIRECTORY + '/' + path for path in receipt['ci_receipts']} | _data_paths())


def _ci_runs():
    return [_read(PARENT_DIRECTORY + '/ci-' + str(run) + '.json') for run, _ in CI_RUNS]


def prepare_binding():
    """Compute a reviewable candidate without executing historical code or tests."""
    tree = _read(BASE_TREE)['sha256']
    receipt = _read(PARENT_RECEIPT)
    return dict(
        schema_version='queue-v23.source-amendment.v1', authority='USER_QUEUE_V2.3_2026-10-15',
        parent_git_head=BASE, parent_amendment=PARENT_AMENDMENT,
        parent_amendment_sha256=tree[PARENT_AMENDMENT],
        parent_receipt_sha256=PARENT_RECEIPT_SHA256,
        contract=CONTRACT, contract_sha256=sha(CONTRACT),
        current_sha256={path: sha(path) for path in sorted(CURRENT_PATHS)},
        preserved_sha256={path: digest for path, digest in sorted(tree.items()) if path not in MODIFIED_PATHS},
        parent_archive_sha256=receipt['sha256'],
        data_sha256={path: sha(path) for path in sorted(_data_paths())},
        reused_ci_runs=_ci_runs(), prior_completed_verification_rerun=False,
        automatic_user_approval=False, auto_verified_to_user_reviewed=False,
        user_decisions_created=0, existing_user_decisions_mutated=False,
        existing_sql_schema_change=False, engine_activation=False,
        real_match_coaching_accuracy=None,
    )


def _git_parent_proof(tree):
    """Check base ancestry and manifest against Git objects, not prior assertions."""
    _git('merge-base', '--is-ancestor', BASE, 'HEAD')
    archive = _git('archive', BASE)
    expected = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        for member in stream:
            if member.isfile():
                expected[member.name] = hashlib.sha256(stream.extractfile(member).read()).hexdigest()
    return expected == tree


def v23_binding():
    checks = {}
    try:
        binding = _read(AMENDMENT)
        receipt = _read(PARENT_RECEIPT)
        tree = _read(BASE_TREE)['sha256']
        archived = receipt['sha256']
        expected_preserved = {p: h for p, h in tree.items() if p not in MODIFIED_PATHS}
        trusted_ci = _ci_runs()
        inventory = _inventory()
        parent_paths = ({BASE_TREE, PARENT_RECEIPT} |
                        {PARENT_DIRECTORY + '/' + p for p in archived} |
                        {PARENT_DIRECTORY + '/' + p for p in receipt['ci_receipts']})
        checks.update(
            explicit_user_authority=binding['schema_version'] == 'queue-v23.source-amendment.v1'
                and binding['authority'] == 'USER_QUEUE_V2.3_2026-10-15',
            immutable_parent_receipt=sha(PARENT_RECEIPT) == PARENT_RECEIPT_SHA256 == binding['parent_receipt_sha256'],
            exact_parent_commit=binding['parent_git_head'] == receipt['source_git_head'] == BASE,
            parent_tree_bound=sha(BASE_TREE) == receipt['parent_tree_sha256'],
            parent_git_ancestry_and_tree=_git_parent_proof(tree),
            parent_contract_unchanged=binding['parent_amendment'] == PARENT_AMENDMENT
                and sha(PARENT_AMENDMENT) == binding['parent_amendment_sha256'] == tree[PARENT_AMENDMENT],
            exact_current_paths=set(binding['current_sha256']) == CURRENT_PATHS,
            current_bytes=all(sha(p) == digest for p, digest in binding['current_sha256'].items()),
            exact_preserved_paths=binding['preserved_sha256'] == expected_preserved,
            preserved_bytes=all(sha(p) == digest for p, digest in expected_preserved.items()),
            exact_parent_archives=set(archived) == MODIFIED_PATHS and binding['parent_archive_sha256'] == archived,
            archived_parent_bytes=all(sha(PARENT_DIRECTORY + '/' + p) == digest == tree[p] for p, digest in archived.items()),
            original_ci_receipts=all(sha(PARENT_DIRECTORY + '/' + p) == digest for p, digest in receipt['ci_receipts'].items()),
            trusted_completed_ci=binding['reused_ci_runs'] == trusted_ci and all(
                run['id'] == expected_id and run['head_sha'] == BASE and run['path'] == workflow
                and run['status'] == 'completed' and run['conclusion'] == 'success'
                and run['event'] == 'push' and run['run_attempt'] == 1
                and run['repository']['full_name'] == 'kco994553-star/lol-coach'
                for run, (expected_id, workflow) in zip(trusted_ci, CI_RUNS)) and len(trusted_ci) == 2,
            exact_data_paths=set(binding['data_sha256']) == _data_paths(),
            data_files_only=all(Path(path).suffix == '.json' for path in binding['data_sha256']),
            data_bytes=all(sha(p) == digest for p, digest in binding['data_sha256'].items()),
            bounded_changes=all(path in tree or path in CURRENT_PATHS or path == AMENDMENT
                or path in binding['data_sha256'] or path in parent_paths
                or _evidence_path(path) for path in inventory),
            contract_bound=binding['contract'] == CONTRACT and sha(CONTRACT) == binding['contract_sha256'],
            no_prior_verification_rerun=binding['prior_completed_verification_rerun'] is False
                and receipt['prior_completed_verification_rerun'] is False,
            no_user_or_engine_promotion=binding['automatic_user_approval'] is False
                and binding['auto_verified_to_user_reviewed'] is False
                and type(binding['user_decisions_created']) is int and binding['user_decisions_created'] == 0
                and binding['existing_user_decisions_mutated'] is False
                and binding['existing_sql_schema_change'] is False and binding['engine_activation'] is False,
            no_accuracy_claim=binding['real_match_coaching_accuracy'] is None,
        )
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        checks['binding_readable'] = False
        return dict(status='FAIL', checks=checks, error=type(error).__name__ + ': ' + str(error),
                    prior_completed_verification_rerun=False, reused_ci_run_ids=[run for run, _ in CI_RUNS])
    return dict(status='PASS' if all(checks.values()) else 'FAIL', checks=checks,
                scope='v2.3 exact sources + immutable base hashes/ancestry + reused completed CI',
                prior_completed_verification_rerun=False, reused_ci_run_ids=[run for run, _ in CI_RUNS],
                real_match_coaching_accuracy=None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--tests', action='store_true', help='Run only new v2.3 affected unit/integration tests')
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(dict(state='UNSEALED_CANDIDATE', binding=prepare_binding()), ensure_ascii=False, indent=2))
        return 0
    result = v23_binding()
    if args.tests and result['status'] == 'PASS':
        completed = subprocess.run([sys.executable, '-m', 'unittest', *DELTA_TESTS, '-v'], cwd=ROOT)
        result['delta_tests_exit_code'] = completed.returncode
        if completed.returncode:
            result['status'] = 'FAIL'
    result['commit_sha'] = _git('rev-parse', 'HEAD').decode().strip()
    result['github_actions_context'] = {key: os.environ.get(value) for key, value in (
        ('run_id', 'GITHUB_RUN_ID'), ('run_attempt', 'GITHUB_RUN_ATTEMPT'))}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())

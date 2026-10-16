"""Exact actual-evidence delta; predecessor code/tests/collection are never executed."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
BASE='103b8b80c915accba7d7e5c82951d020b17d6e09'
BASE_TREE='0e2a5f3f883f149495054e624d2e0e48b09d22c2'
SEAL='contracts/amendments/2026-10-16-actual-evidence.json'
PARENT_CI='evidence/actual-evidence/parent/ci-main-pr40.json'
PARENT_CI_SHA='0a5c757eb4a0a069d754369009421a76f1522161091902ebb3502bb91489f892'
MODIFIED={'coach_v1/pc_coach.py','.github/workflows/private-mvp-ci.yml',
    '.github/workflows/pregame-ci.yml','.github/workflows/expert-video-collection.yml',
    '.github/workflows/pro-reference-collection.yml','scripts/collect_expert_claims.py',
    'scripts/diagnose_expert_front.py','scripts/diagnose_expert_video.py',
    'CURRENT_HANDOFF.md','docs/queue/QUEUE.md'}
CURRENT=MODIFIED|{
    'coach_v1/gemini_daily.py','scripts/run_gemini_daily.py','coach_v1/pov_metadata.py',
    'scripts/verify_pov_metadata.py','scripts/recover_resource_checkpoint.py','coach_v1/resource_recovery.py','coach_v1/resource_view.py',
    'config/evidence_intake.json','config/pov_channels.json','contracts/actual-evidence-v1.md',
    '.github/workflows/resource-recovery-offline.yml','scripts/verify_actual_evidence.py',
    'scripts/browser_actual_evidence.py','tests_expert/test_gemini_daily.py',
    'tests_expert/test_pov_metadata.py','tests_expert/test_daily_migration.py','tests_expert/test_daily_review_fixes.py','tests_pregame/test_resource_recovery.py',
    'tests_pregame/test_resource_view.py','tests_pregame/test_fixed_resource_checkpoint.py','tests_pregame/test_actual_evidence_binding.py',
    'docs/superpowers/plans/2026-10-16-actual-evidence.md',
}
TESTS=['tests_expert.test_daily_migration','tests_expert.test_daily_review_fixes','tests_expert.test_gemini_daily','tests_expert.test_pov_metadata',
       'tests_pregame.test_resource_recovery','tests_pregame.test_resource_view','tests_pregame.test_fixed_resource_checkpoint',
       'tests_pregame.test_actual_evidence_binding']
DATA_ROOTS=['data/resource_recovery/2026-10-16','data/pov_metadata/2026-10-16']



def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hashes(root,hashes):
    try:
        for name,expected in hashes.items():
            p=root/name
            if Path(name).is_absolute() or '..' in Path(name).parts or any(x.is_symlink() for x in [p,*p.parents]):return False
            if sha(p)!=expected:return False
        return True
    except (OSError,ValueError):return False


def exact_source_authority(binding):return set(binding['current_sha256'])==CURRENT


def base_hashes():
    result={}
    with tarfile.open(fileobj=io.BytesIO(git('archive',BASE))) as archive:
        for entry in archive:
            if entry.isfile():result[entry.name]=hashlib.sha256(archive.extractfile(entry).read()).hexdigest()
    return result


def new_data():
    return {str(p.relative_to(ROOT)):sha(p) for name in DATA_ROOTS for p in (ROOT/name).glob('*.json')}


def allowed_new(path):
    archived={'evidence/actual-evidence/parent/'+name for name in MODIFIED}
    return path in CURRENT or path==SEAL or path in archived or (
        path.startswith('evidence/actual-evidence/') and Path(path).suffix in {'.json','.md','.log','.png'}) or path in new_data()


def affected_browser_changed():
    path=os.environ.get('GITHUB_EVENT_PATH')
    if not path:return True
    event=json.loads(Path(path).read_text())
    before=event.get('pull_request',{}).get('base',{}).get('sha') or event.get('before')
    if not before or set(before)=={'0'}:return True
    changed=set(git('diff','--name-only',before,'HEAD').decode().splitlines())
    watched={'coach_v1/pc_coach.py','coach_v1/resource_view.py','coach_v1/resource_recovery.py','scripts/browser_actual_evidence.py'}
    return bool(changed & watched or any(p.startswith('data/resource_recovery/') for p in changed))


def prepare():
    parent=base_hashes()
    folder=ROOT/'evidence/actual-evidence/parent'
    for name in MODIFIED:
        p=folder/name;p.parent.mkdir(parents=True,exist_ok=True)
        original=git('show',BASE+':'+name)
        if p.exists() and p.read_bytes()!=original:raise ValueError('PARENT_ARCHIVE_CHANGED')
        if not p.exists():p.write_bytes(original)
    return dict(schema_version='actual-evidence.source-amendment.v1',authority='USER_2026-10-16_ACTUAL_EVIDENCE',
        parent_commit=BASE,parent_tree=BASE_TREE,parent_ci_sha256=PARENT_CI_SHA,
        current_sha256={p:sha(ROOT/p) for p in sorted(CURRENT)},
        preserved_sha256={p:h for p,h in sorted(parent.items()) if p not in MODIFIED},
        archived_sha256={p:parent[p] for p in sorted(MODIFIED)},data_sha256=new_data(),
        prior_completed_tests_rerun=False,approval_inherited=False,user_decisions_created=0,coaching_accuracy=None)


def affected_code_changed():
    """Evidence-only result publication reuses already completed pilot checks."""
    path=os.environ.get('GITHUB_EVENT_PATH')
    if not path:return True
    event=json.loads(Path(path).read_text())
    before=event.get('pull_request',{}).get('base',{}).get('sha') or event.get('before')
    if not before or set(before)=={'0'}:return True
    changed=set(git('diff','--name-only',before,'HEAD').decode().splitlines())
    executable={p for p in CURRENT if p.endswith(('.py','.js','.yml'))}
    content={'config/evidence_intake.json','config/pov_channels.json'}
    return bool(changed&(executable|content))


def selected_tests():
    path=os.environ.get('GITHUB_EVENT_PATH')
    if not path:return TESTS
    event=json.loads(Path(path).read_text());before=event.get('pull_request',{}).get('base',{}).get('sha') or event.get('before')
    if not before or set(before)=={'0'}:return TESTS
    changed=set(git('diff','--name-only',before,'HEAD').decode().splitlines())
    groups={
        'tests_expert.test_daily_migration':{'scripts/collect_expert_claims.py'},
        'tests_expert.test_daily_review_fixes':{'coach_v1/gemini_daily.py','scripts/run_gemini_daily.py'},
        'tests_expert.test_gemini_daily':{'coach_v1/gemini_daily.py','scripts/run_gemini_daily.py','config/evidence_intake.json','.github/workflows/expert-video-collection.yml'},
        'tests_expert.test_pov_metadata':{'coach_v1/pov_metadata.py','scripts/verify_pov_metadata.py','config/pov_channels.json','.github/workflows/resource-recovery-offline.yml'},
        'tests_pregame.test_resource_recovery':{'coach_v1/resource_recovery.py','.github/workflows/resource-recovery-offline.yml'},
        'tests_pregame.test_resource_view':{'coach_v1/resource_view.py','coach_v1/pc_coach.py'},
        'tests_pregame.test_fixed_resource_checkpoint':{'scripts/recover_resource_checkpoint.py'},
        'tests_pregame.test_actual_evidence_binding':{'scripts/verify_actual_evidence.py'},
    }
    return [t for t in TESTS if changed & (groups.get(t,set())|{t.replace('.','/')+'.py'})]


def verify():
    b=json.loads((ROOT/SEAL).read_text());parent=base_hashes()
    inventory=set(git('ls-files','--cached','--others','--exclude-standard','-z').decode().split('\0'))-{''}
    ci=json.loads((ROOT/PARENT_CI).read_text())
    checks=dict(
        authority=b['schema_version']=='actual-evidence.source-amendment.v1' and b['authority']=='USER_2026-10-16_ACTUAL_EVIDENCE',
        ancestry=subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,stdout=subprocess.DEVNULL).returncode==0,
        exact_parent=b['parent_commit']==BASE and b['parent_tree']==BASE_TREE and git('rev-parse',BASE+'^{tree}').decode().strip()==BASE_TREE,
        completed_ci_reused=sha(ROOT/PARENT_CI)==PARENT_CI_SHA==b['parent_ci_sha256'] and {r['id'] for r in ci['runs']}=={38891492364,38891492575}
            and all(r['head_sha']==BASE and r['conclusion']=='success' and all(j['conclusion']=='success' for j in r['jobs']) for r in ci['runs']),
        exact_source_authority=exact_source_authority(b),current_sources=check_hashes(ROOT,b['current_sha256']),
        exact_preserved=b['preserved_sha256']=={p:h for p,h in parent.items() if p not in MODIFIED},
        preserved_bytes=check_hashes(ROOT,b['preserved_sha256']),
        original_modified_archived=b['archived_sha256']=={p:parent[p] for p in MODIFIED} and check_hashes(ROOT/'evidence/actual-evidence/parent',b['archived_sha256']),
        new_data_bound=b['data_sha256']==new_data(),bounded_changes=all(p in parent or allowed_new(p) for p in inventory),
        no_approval_or_accuracy=b['approval_inherited'] is False and b['user_decisions_created']==0 and b['coaching_accuracy'] is None and b['prior_completed_tests_rerun'] is False)
    sys.path.insert(0,str(ROOT))
    from coach_v1.resource_recovery import load_bound_report
    for path in (ROOT/'data/resource_recovery/2026-10-16').glob('resources.json'):load_bound_report(path.parent)
    checks['resource_reports_bound']=True
    return_pov=[]
    for path in (ROOT/'data/pov_metadata/2026-10-16').glob('pov-metadata.json'):
        binding=json.loads((path.parent/'metadata-binding.json').read_text())
        expected={'coach_v1/pov_metadata.py','scripts/verify_pov_metadata.py','config/pov_channels.json','contracts/actual-evidence-v1.md'}
        assert binding['report_sha256']==sha(path) and set(binding['source_sha256'])==expected
        commit=binding['source_commit']
        assert len(commit)==40 and all(c in '0123456789abcdef' for c in commit)
        assert subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=ROOT,stdout=subprocess.DEVNULL).returncode==0
        assert all(h==sha(ROOT/p)==hashlib.sha256(git('show',commit+':'+p)).hexdigest() for p,h in binding['source_sha256'].items())
        assert binding['category']=='POV' and binding['expert_source'] is False
        return_pov.append(True)
    checks['pov_reports_bound']=all(return_pov)
    return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,commit_sha=git('rev-parse','HEAD').decode().strip(),
        scope='Actual evidence sources/data only; completed pilot/v2.3 CI reused, no predecessor tests executed',coaching_accuracy=None)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--tests',action='store_true');args=parser.parse_args()
    if args.prepare:
        (ROOT/SEAL).write_text(json.dumps(prepare(),ensure_ascii=False,indent=2)+'\n');return 0
    report=verify();code=0;report['new_tests_executed']=False
    if report['status']=='PASS' and args.tests:
        if affected_code_changed():
            report['selected_test_modules']=selected_tests()
            report['new_tests_executed']=bool(report['selected_test_modules'])
            if report['new_tests_executed']:code=subprocess.run([sys.executable,'-m','unittest','-v',*report['selected_test_modules']],cwd=ROOT).returncode
        else:report['unchanged_evidence_tests_reused']=True
    report['new_tests_exit_code']=code
    print(json.dumps(report,indent=2));return 0 if report['status']=='PASS' and code==0 else 1


if __name__=='__main__':raise SystemExit(main())

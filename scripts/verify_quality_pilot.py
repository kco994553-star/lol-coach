"""Exact pilot delta; predecessor code/tests/collection are never executed."""
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
BASE='9da650ae1ec000f3bb66d90be351174fe3c731f3'
BASE_TREE='37729ed4a6d7810f6885eb5d8e60f7b701616343'
SEAL='contracts/amendments/2026-10-16-quality-pilot.json'
PARENT_CI='evidence/quality-pilot/parent/ci-main-pr38.json'
PARENT_CI_SHA='930d6c03b0ef9d239d9f4354558b0693ffc191979474046b31e8c1c6f140ce4c'
MODIFIED={'coach_v1/pc_coach.py','web_r4/pc.js','.github/workflows/private-mvp-ci.yml',
          '.github/workflows/pregame-ci.yml','CURRENT_HANDOFF.md','docs/queue/QUEUE.md'}
CURRENT=MODIFIED|{
    'coach_v1/pilot_advice.py','coach_v1/pilot_observations.py',
    'knowledge_candidates/coaching-quality-pilot.json',
    'contracts/coaching-quality-pilot-v1.md',
    '.github/workflows/coaching-quality-offline.yml',
    'scripts/verify_quality_pilot.py','scripts/browser_quality_pilot.py','scripts/report_quality_pilot.py',
    'tests_pregame/test_pilot_advice.py','tests_pregame/test_pilot_observations.py','tests_pregame/test_quality_pilot_binding.py',
    'tests_pregame/test_quality_reporting.py',
    'docs/superpowers/plans/2026-10-16-coaching-quality-pilot.md',
    'evidence/quality-pilot/evidence-review.json','evidence/quality-pilot/tactical-review.json',
}
TESTS=['tests_pregame.test_pilot_advice','tests_pregame.test_pilot_observations','tests_pregame.test_quality_pilot_binding','tests_pregame.test_quality_reporting']


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
    return {str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'data/coaching_quality/2026-10-16').glob('*.json')}


def prepare():
    parent=base_hashes()
    folder=ROOT/'evidence/quality-pilot/parent'
    for name in MODIFIED:
        p=folder/name;p.parent.mkdir(parents=True,exist_ok=True)
        original=git('show',BASE+':'+name)
        if p.exists() and p.read_bytes()!=original:raise ValueError('PARENT_ARCHIVE_CHANGED')
        if not p.exists():p.write_bytes(original)
    return dict(schema_version='quality-pilot.source-amendment.v1',authority='USER_2026-10-16_SMALL_PILOT',
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
    content={'knowledge_candidates/coaching-quality-pilot.json','evidence/quality-pilot/evidence-review.json','evidence/quality-pilot/tactical-review.json'}
    return bool(changed&(executable|content))


def verify():
    b=json.loads((ROOT/SEAL).read_text());parent=base_hashes()
    inventory=set(git('ls-files','--cached','--others','--exclude-standard','-z').decode().split('\0'))-{''}
    def allowed(p):
        archived_paths={'evidence/quality-pilot/parent/'+name for name in MODIFIED}
        return p in parent or p in CURRENT or p==SEAL or p in archived_paths or (
            p.startswith('evidence/quality-pilot/') and Path(p).suffix in {'.json','.md','.log','.png'}) or p in new_data()
    ci=json.loads((ROOT/PARENT_CI).read_text())
    checks=dict(
        authority=b['schema_version']=='quality-pilot.source-amendment.v1' and b['authority']=='USER_2026-10-16_SMALL_PILOT',
        ancestry=subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,stdout=subprocess.DEVNULL).returncode==0,
        exact_parent=b['parent_commit']==BASE and b['parent_tree']==BASE_TREE and git('rev-parse',BASE+'^{tree}').decode().strip()==BASE_TREE,
        completed_ci_reused=sha(ROOT/PARENT_CI)==PARENT_CI_SHA==b['parent_ci_sha256'] and {r['id'] for r in ci['runs']}=={38732438850,38732438842}
            and all(r['head_sha']==BASE and r['conclusion']=='success' and all(j['conclusion']=='success' for j in r['jobs']) for r in ci['runs']),
        exact_source_authority=exact_source_authority(b),current_sources=check_hashes(ROOT,b['current_sha256']),
        exact_preserved=b['preserved_sha256']=={p:h for p,h in parent.items() if p not in MODIFIED},
        preserved_bytes=check_hashes(ROOT,b['preserved_sha256']),
        original_modified_archived=b['archived_sha256']=={p:parent[p] for p in MODIFIED} and check_hashes(ROOT/'evidence/quality-pilot/parent',b['archived_sha256']),
        new_data_bound=b['data_sha256']==new_data(),bounded_changes=all(allowed(p) for p in inventory),
        no_approval_or_accuracy=b['approval_inherited'] is False and b['user_decisions_created']==0 and b['coaching_accuracy'] is None and b['prior_completed_tests_rerun'] is False)
    sys.path.insert(0,str(ROOT))
    from coach_v1.pilot_advice import load_packet,review_receipts
    from coach_v1.pilot_observations import load_bound_report
    review_receipts(load_packet());checks['new_reviews_bound']=True
    for path in (ROOT/'data/coaching_quality/2026-10-16').glob('observations.json'):load_bound_report(path.parent)
    checks['offline_reports_valid']=True
    return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,commit_sha=git('rev-parse','HEAD').decode().strip(),
        scope='Pilot-only sources and data; completed v2.3 CI reused, no predecessor tests executed',coaching_accuracy=None)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--tests',action='store_true');args=parser.parse_args()
    if args.prepare:
        (ROOT/SEAL).write_text(json.dumps(prepare(),ensure_ascii=False,indent=2)+'\n');return 0
    report=verify();code=0;report['pilot_tests_executed']=False
    if report['status']=='PASS' and args.tests:
        if affected_code_changed():
            report['pilot_tests_executed']=True
            code=subprocess.run([sys.executable,'-m','unittest','-v',*TESTS],cwd=ROOT).returncode
        else:report['unchanged_pilot_tests_reused']=True
    report['new_tests_exit_code']=code
    print(json.dumps(report,indent=2));return 0 if report['status']=='PASS' and code==0 else 1


if __name__=='__main__':raise SystemExit(main())

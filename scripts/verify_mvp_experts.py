"""Run the preserved MVP verifier with one exact, authorized source amendment.

The original verifier, historical tests, Frozen bytes and prior receipts remain
unchanged. Only the explicitly versioned Korean topic index is admitted.
"""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import verify_mvp as original


def korean_binding():
    try:
        sha=lambda path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        binding=json.loads((ROOT/'contracts/amendments/2026-10-11-korean-topic-index.json').read_text())
        baseline=json.loads((ROOT/'evidence/r7/baseline-tree.json').read_text())['tree']
        row=next(r for r in baseline if r['path']=='coach_intake/video.py' and r['type']=='blob')
        parent=(ROOT/binding['parent_archive']).read_bytes()
        checks=dict(explicit_authority=binding['authority']=='USER_QUEUE_V1.6_2026-10-11',
            original_archive=binding['parent_archive']=='evidence/queue/v16/korean-source-parent/video.py',
            original_baseline_blob=hashlib.sha1(b'blob '+str(len(parent)).encode()+b'\0'+parent).hexdigest()==row['sha'],
            parent_sha=hashlib.sha256(parent).hexdigest()==binding['parent_sha256'],
            exact_current_paths=set(binding['current_sha256'])=={'coach_intake/video.py','tests_expert/test_video_korean.py'},
            current_bytes=all(sha(p)==h for p,h in binding['current_sha256'].items()),
            frozen_unchanged=sha('FREEZE_MANIFEST.json')==binding['parent_freeze_sha256'],
            verifier_unchanged=sha('scripts/verify_mvp.py')==binding['parent_verifier_sha256']==
                json.loads((ROOT/'evidence/mvp/knowledge-review-version.json').read_text())['current_sha256']['scripts/verify_mvp.py'])
        return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks)
    except (OSError,ValueError,KeyError,StopIteration,TypeError):
        return dict(status='FAIL',checks={'binding_readable':False})


def amended_preservation(report):
    binding=korean_binding();report=dict(report)
    report['korean_topic_version_binding']=binding
    errors=list(report['other_historical_byte_errors'])
    if binding['status']=='PASS':
        errors=[p for p in errors if p!='coach_intake/video.py']
        report['mvp_authorized_changed_paths']=sorted(set(report['mvp_authorized_changed_paths'])|{'coach_intake/video.py'})
    report['other_historical_byte_errors']=errors
    report['status']='PASS' if binding['status']=='PASS' and report['frozen_payload_files']==27 and not any(
        report[k] for k in ('frozen_errors','other_historical_byte_errors','r7_source_errors','old_test_file_set_errors')) else 'FAIL'
    return report


def main():
    base=original.preservation_gate
    original.preservation_gate=lambda:amended_preservation(base())
    try:return original.main()
    finally:original.preservation_gate=base

if __name__=='__main__':raise SystemExit(main())

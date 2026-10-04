"""Reproducible R7 evidence with immutable run directories and preserved R0-R6 gates."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,io,json,shutil,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from coach_audit.extraction import extract
from coach_audit.replay import compare_player_state

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def blob(path):
    data=path.read_bytes();return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def save(out,name,obj):(out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main():
    out=ROOT/'evidence/r7'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir()
    frozen=json.loads((ROOT/'FREEZE_MANIFEST.json').read_text())
    frozen_errors=[p for p,h in frozen['payload_sha256'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    tree=json.loads((ROOT/'evidence/r7/baseline-tree.json').read_text())
    old=[r for r in tree['tree'] if r['type']=='blob' and r['path']!='CURRENT_HANDOFF.md']
    baseline_errors=[r['path'] for r in old if not (ROOT/r['path']).is_file() or blob(ROOT/r['path'])!=r['sha']]
    sources=json.loads((ROOT/'contracts/r7/sources.json').read_text());source_ids=[s['id'] for s in sources['sources']]
    matrix=json.loads((ROOT/'contracts/r7/state_source_matrix.json').read_text());rows=matrix['entries']
    required={'decision_impact','required_precision','preferred_source','fallback_source','provenance','freshness_ttl','confidence_requirement','automatic_acquisition_feasibility','manual_fallback','vision_needed','availability_status'}
    static=[]
    if len(rows)!=29 or len({r['id'] for r in rows})!=29:static.append('MATRIX_COVERAGE')
    if len(source_ids)!=len(set(source_ids)):static.append('DUPLICATE_SOURCE')
    for row in rows:
        if not required.issubset(row):static.append(row['id']+':MISSING_FIELDS')
        if row['availability_status'] not in matrix['availability_status_enum']:static.append(row['id']+':STATUS')
    if not set(matrix['source_refs']).issubset(source_ids):static.append('DANGLING_SOURCE')
    for e in matrix['evidence']:
        if sha(ROOT/e['path'])!=e['sha256']:static.append(e['path']+':HASH')
    hard_gate=dict(frozen_payload_files=len(frozen['payload_sha256']),frozen_errors=frozen_errors,
        r0_r6_unchanged_files=len(old),baseline_errors=baseline_errors,static_errors=static)
    save(out,'hard-gates.json',hard_gate)
    if frozen_errors or baseline_errors or static:
        save(out,'verification.json',dict(passed=False,phase='HARD_GATE'));return 1
    log=io.StringIO();suite=unittest.TestSuite()
    for folder in ('tests_r3','tests_r4','tests_r5','tests_r6','tests_r7'):
        suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/folder),top_level_dir=str(ROOT)))
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    # Existing protected verifier writes evidence: isolate to retain historical bytes.
    with tempfile.TemporaryDirectory() as td:
        dest=Path(td)/'copy';shutil.copytree(ROOT,dest,ignore=shutil.ignore_patterns('__pycache__','.git','private'))
        protected=subprocess.run([sys.executable,'-m','validation'],cwd=dest,capture_output=True,text=True)
    (out/'tests.log').write_text(log.getvalue()+'\n'+protected.stderr)
    protected_result=json.loads(protected.stdout) if protected.returncode==0 else dict(error=protected.stderr)
    save(out,'protected-regression.json',protected_result)
    ref=json.loads((ROOT/'fixtures/r7/documentation_reference.json').read_text())
    extraction=extract((ROOT/ref['source_path']).read_bytes(),source_kind='DOCUMENTATION_SAMPLE',expected_sha=ref['source_sha256'])
    save(out,'documentation-extraction.json',extraction)
    by={r['field']:r for r in extraction['raw']}
    mismatches=[k for k,v in ref['expected'].items() if any(by[k][f]!=v[f] for f in ('state','value'))]
    replay=json.loads((ROOT/'fixtures/r7/representative_set.json').read_text())
    comparisons={c['case_id']:compare_player_state(c,{}) for c in replay['cases']}
    save(out,'reference-comparisons.json',comparisons)
    metrics={k:dict(value=None,numerator=0,denominator=0,status='NOT_RUN',reason='No established real player reference + aligned extracted state') for k in ('state_extraction_accuracy','state_completeness','state_freshness','decision_resolvability','vision_required_rate','manual_intervention_rate','unresolved_rate')}
    baseline=dict(documentation_parser_reference=dict(matches=len(ref['expected'])-len(mismatches),denominator=len(ref['expected']),mismatches=mismatches,scope='Values AND missingness labels on one documentation snapshot; not game accuracy'),
        documentation_present_fields=sum(r['state']=='PRESENT' for r in extraction['raw']),documentation_selected_paths=len(extraction['raw']),
        documentation_derived_resolved=sum(r['value'] is not None for r in extraction['derived']),
        planned_replay_slots=len(replay['cases']),topic_seed_slots=sum(c['status']=='TOPIC_SEED_ONLY' for c in replay['cases']),
        distinct_seed_locations=len({(c['video_id'],c['cue_index']) for c in replay['cases'] if c['cue_index'] is not None}),
        reference_states_established=0,frames_reviewed=0,real_cases_evaluated=0,real_coaching_accuracy=None,real_metrics=metrics)
    save(out,'baseline-metrics.json',baseline)
    inputs={p.relative_to(ROOT).as_posix():sha(p) for folder in ('coach_audit','tests_r7','fixtures/r7','contracts/r7') for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    inputs['scripts/verify_r7.py']=sha(Path(__file__))
    report=dict(at_utc=datetime.now(timezone.utc).isoformat(),baseline_head='884a435e52fa20e21971269dd52e30239fc4f8ff',
        risk='DEEP',tests_run=result.testsRun,skipped=len(result.skipped),failures=len(result.failures),errors=len(result.errors),
        passed=result.wasSuccessful() and not result.skipped and protected.returncode==0 and not mismatches,
        protected_passed=protected_result.get('passed'),protected_failed=protected_result.get('failed'),
        source_sha256=inputs,real_match_validation_passed=False,coaching_enabled=False,frozen_design_changed=False)
    save(out,'verification.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2));print(out)
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

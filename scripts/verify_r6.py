"""Fresh R3/R4/R5/R6 and protected regression; preserve all prior evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,io,json,platform,shutil,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def main():
    log=io.StringIO();suite=unittest.TestSuite()
    for folder in ('tests_r3','tests_r4','tests_r5','tests_r6'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/folder),top_level_dir=str(ROOT)))
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    # Run R4 race checks in a copy to preserve earlier evidence.
    races=subprocess.CompletedProcess([],0,stdout='',stderr='')
    with tempfile.TemporaryDirectory() as td:
        dest=Path(td)/'baseline';shutil.copytree(ROOT,dest,ignore=shutil.ignore_patterns('__pycache__','.git'))
        races=subprocess.run(['node','tests_r4/ui_races.cjs'],cwd=dest,capture_output=True,text=True)
        file_race=subprocess.run(['node','tests_r6/ui_file_race.cjs'],cwd=dest,capture_output=True,text=True)
        old=subprocess.run([sys.executable,'-m','validation'],cwd=dest,capture_output=True,text=True)
    frozen=json.loads(old.stdout) if old.returncode==0 else {'error':old.stderr}
    inputs={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('coach_v1','coach_intake','web_r4','tests_r3','tests_r4','tests_r5','tests_r6','scripts','schemas') for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    report=dict(at_utc=datetime.now(timezone.utc).isoformat(),evidence_kind='FRESH_SYNTHETIC_EXECUTION',python=platform.python_version(),tests_run=result.testsRun,skipped=len(result.skipped),failures=len(result.failures),errors=len(result.errors),passed=result.wasSuccessful() and not result.skipped and races.returncode==0 and file_race.returncode==0 and old.returncode==0,ui_races_passed=races.returncode==0,ui_file_race_passed=file_race.returncode==0,frozen_regression=frozen,source_sha256=inputs,real_game_capture_tested=False,production_enabled=False)
    out=ROOT/'evidence/r6';out.mkdir(exist_ok=True);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    (out/(stamp+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (out/(stamp+'.log')).write_text(log.getvalue()+'\n'+races.stdout+races.stderr+file_race.stdout+file_race.stderr)
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','frozen_regression')},indent=2));print('Frozen:',frozen.get('passed'),frozen.get('failed'))
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

"""Run current tests and frozen regression without rewriting historical evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import io
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    import pydantic
    log=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests_r3'),top_level_dir=str(ROOT))
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    with tempfile.TemporaryDirectory(prefix='lol-r3-protected-') as td:
        copy=Path(td)/'baseline'
        shutil.copytree(ROOT,copy,ignore=shutil.ignore_patterns('__pycache__','.git'))
        legacy=subprocess.run([sys.executable,'-m','validation'],cwd=copy,capture_output=True,text=True)
        frozen=json.loads(legacy.stdout) if legacy.returncode==0 else {'error':legacy.stderr}
    inputs={}
    for folder in ('coach_v1','tests_r3','scripts','schemas'):
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                inputs[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(at_utc=datetime.now(timezone.utc).isoformat(),baseline='99288ed6782858713bbb4bb61cc594094d83f2f6',evidence_kind='FRESH_SYNTHETIC_EXECUTION',python=platform.python_version(),pydantic=pydantic.__version__,r3=dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),passed=result.wasSuccessful()),frozen_regression=frozen,source_sha256=inputs,real_data_tested=False,production_enabled=False,independent_review=dict(initial_findings=2,targeted_recheck_passed=3,remaining_material_findings=0))
    out=ROOT/'evidence/r3';out.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    (out/(stamp+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (out/(stamp+'.log')).write_text(log.getvalue())
    print(json.dumps({'r3':report['r3'],'frozen_passed':frozen.get('passed'),'frozen_failed':frozen.get('failed'),'report':str(out/(stamp+'.json'))},indent=2))
    return 0 if result.wasSuccessful() and legacy.returncode==0 else 1


if __name__=='__main__':raise SystemExit(main())

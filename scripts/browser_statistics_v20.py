"""Isolated Chromium tier/progress verification; no provider calls or approvals."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    from coach_v1.pregame_server import PregameWorkbench
    from coach_v1.server import Limits
    from coach_v1.power_stats import build_power_dataset
    from tests_pregame.test_power_stats import pair,source
    output=ROOT/'evidence/queue/v20'/('statistics-browser-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(parents=True)
    names=['coach_v1/pregame_server.py','coach_v1/power_stats.py','coach_v1/collection_progress.py','web_r4/statistics.html','web_r4/statistics.js','web_r4/pregame_power.js','scripts/browser_statistics_v20.py','tests_pregame/browser_statistics_v20.cjs']
    hashes=lambda:{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
    before=hashes()
    with tempfile.TemporaryDirectory(prefix='stats-browser-v20-') as tmp:
        token=secrets.token_urlsafe(32);path=Path(tmp);tokenfile=path/'token';tokenfile.write_text(token);tokenfile.chmod(0o600)
        server=PregameWorkbench(path/'work.sqlite',token,Limits(1000000,1000,100,100,100,10));server.test_mode=True
        for tier in ['GOLD','CHALLENGER']:
            src=source();src['tier']=tier
            server.power_datasets[('16.19',tier)]=build_power_dataset([pair(i,i*2) for i in range(24)],source=src)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        env=dict(os.environ,WORKBENCH_TOKEN_FILE=str(tokenfile),WORKBENCH_URL=f'http://127.0.0.1:{server.server_port}',STATS_EVIDENCE_DIR=str(output))
        try:
            run=subprocess.run(['node',str(ROOT/'tests_pregame/browser_statistics_v20.cjs')],cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
            (output/'browser.log').write_text(run.stdout+run.stderr)
        finally:server.shutdown();thread.join();server.server_close()
    browser=json.loads((output/'browser.json').read_text()) if (output/'browser.json').exists() else dict(passed=False,error='NO_RECEIPT')
    receipt=dict(passed=run.returncode==0 and browser.get('passed') and before==hashes(),browser=browser,source_sha256=hashes(),sources_unchanged=before==hashes(),git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),github_binding={k:os.environ.get(k) for k in ('GITHUB_SHA','GITHUB_RUN_ID','GITHUB_REPOSITORY')},scope='SYNTHETIC only; no real matches/provider requests/user approvals',coaching_accuracy=None)
    (output/'runner.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(passed=receipt['passed'],evidence_directory=str(output))));return 0 if receipt['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

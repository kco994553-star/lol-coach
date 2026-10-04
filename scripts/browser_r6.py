"""Local Playwright end-to-end test with isolated synthetic database and token."""
import os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    token=Path(td)/'token'
    p=subprocess.Popen([sys.executable,'-m','coach_v1.server','--db',td+'/db.sqlite','--token-file',str(token),'--port','0','--max-body-bytes','1000000','--max-observations','1000','--max-actions','24','--max-scenarios','16','--max-comparisons','512','--max-pending-jobs','8'],cwd=ROOT,stdout=subprocess.PIPE,text=True)
    try:
        line=p.stdout.readline();url=line.strip().split()[-1]
        env=dict(os.environ,WORKBENCH_URL=url,WORKBENCH_TOKEN_FILE=str(token),BROWSER_DOWNLOAD_PATH=td+'/result.json')
        result=subprocess.run(['node','tests_r6/browser.cjs'],cwd=ROOT,env=env)
    finally:p.terminate();p.wait()
    sys.exit(result.returncode)

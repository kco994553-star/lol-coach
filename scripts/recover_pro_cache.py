#!/usr/bin/env python3
"""Recover ciphertext only; any unresolved earlier collection prevents new lookup."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.pro_checkpoint import select_checkpoint,extract_checkpoint_zip,MAX_OUTER_BYTES

def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',required=True);args=p.parse_args()
    root=Path(args.directory);root.mkdir(parents=True,exist_ok=True)
    repo=os.environ.get('GITHUB_REPOSITORY','');run=os.environ.get('GITHUB_RUN_ID','')
    def api(path):
        r=subprocess.run(['gh','api',path],capture_output=True,text=True,timeout=60)
        if r.returncode or len(r.stdout)>2_000_000:raise ValueError('PRO_CACHE_HISTORY_UNAVAILABLE')
        return json.loads(r.stdout)
    try:
        runs=api('repos/'+repo+'/actions/workflows/pro-reference-collection.yml/runs?per_page=100')['workflow_runs']
        result=select_checkpoint(runs,int(run),
            lambda i:api('repos/'+repo+'/actions/runs/'+str(i)+'/artifacts?per_page=100')['artifacts'],
            lambda i:api('repos/'+repo+'/actions/runs/'+str(i)+'/jobs?per_page=100')['jobs'],
            current_run_attempt=int(os.environ.get('GITHUB_RUN_ATTEMPT','0')))
        if result['status']=='FOUND':
            path=root/'checkpoint.zip'
            process=subprocess.Popen(['timeout','60s','gh','api','repos/'+repo+'/actions/artifacts/'+str(result['artifact_id'])+'/zip'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            try:
                size=0
                with path.open('wb') as stream:
                    while True:
                        block=process.stdout.read(65536)
                        if not block:break
                        size+=len(block)
                        if size>MAX_OUTER_BYTES:raise ValueError('PRO_CACHE_DOWNLOAD_SIZE_LIMIT')
                        stream.write(block)
                if process.wait(timeout=60):raise ValueError('PRO_CACHE_DOWNLOAD_UNAVAILABLE')
            finally:
                if process.poll() is None:process.kill();process.wait()
                process.stdout.close()
            extract_checkpoint_zip(path,root/'pro-private.bundle');path.unlink()
        (root/'recovery.json').write_text(json.dumps(result)+'\n')
        with open(os.environ['GITHUB_OUTPUT'],'a') as output:output.write('found='+str(result['status']=='FOUND').lower()+'\n')
        print(json.dumps(result));return 0
    except (ValueError,OSError,KeyError,subprocess.TimeoutExpired):
        print(json.dumps(dict(status='BLOCKED_EXTERNAL',reason='PRIVATE_CHECKPOINT_UNRESOLVED_NO_NEW_LOOKUPS')));return 2

if __name__=='__main__':raise SystemExit(main())

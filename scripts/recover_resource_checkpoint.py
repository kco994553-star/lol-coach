#!/usr/bin/env python3
"""Recover the fixed existing resource checkpoint, never a newer collection."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.pro_checkpoint import extract_checkpoint_zip,MAX_OUTER_BYTES

RUN_ID=38410710876
ARTIFACT_ID=11822391323
SOURCE_COMMIT='b6cdced0c819424e048ec412de6f7e57c5b1c545'


def validate_fixed(run,artifact):
    if not (run.get('id')==RUN_ID and run.get('head_branch')=='main' and run.get('event')=='workflow_dispatch'
        and run.get('path')=='.github/workflows/pro-reference-collection.yml' and run.get('run_attempt')==1 and run.get('head_sha')==SOURCE_COMMIT
        and artifact.get('id')==ARTIFACT_ID and artifact.get('name')=='pro-reference-private-encrypted'
        and artifact.get('expired') is False and type(artifact.get('size_in_bytes')) is int and 0<artifact['size_in_bytes']<=MAX_OUTER_BYTES
        and artifact.get('workflow_run',{}).get('id')==RUN_ID):
        raise ValueError('PINNED_EXISTING_CHECKPOINT_UNAVAILABLE')
    return dict(status='FOUND',run_id=RUN_ID,artifact_id=ARTIFACT_ID,artifact_name='pro-reference-private-encrypted')


def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',required=True);args=p.parse_args()
    root=Path(args.directory);root.mkdir(parents=True,exist_ok=True)
    repo=os.environ.get('GITHUB_REPOSITORY','');run=os.environ.get('GITHUB_RUN_ID','')
    def api(path):
        r=subprocess.run(['gh','api',path],capture_output=True,text=True,timeout=60)
        if r.returncode or len(r.stdout)>2_000_000:raise ValueError('PRO_CACHE_HISTORY_UNAVAILABLE')
        return json.loads(r.stdout)
    try:
        if repo!='kco994553-star/lol-coach' or os.environ.get('GITHUB_RUN_ATTEMPT')!='1':raise ValueError('TRUSTED_FIRST_ATTEMPT_REQUIRED')
        result=validate_fixed(api('repos/'+repo+'/actions/runs/'+str(RUN_ID)),api('repos/'+repo+'/actions/artifacts/'+str(ARTIFACT_ID)))
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

"""Fail-closed selection of encrypted checkpoints from trusted Actions history."""
import os
from pathlib import Path
import stat
import tempfile
import zipfile

MAX_OUTER_BYTES=520_000_000
MAX_CIPHER_BYTES=512_000_100

COLLECT_STEP='Collect user-selected pro timelines privately'
CACHE_NAME='pro-reference-private-encrypted'
PATH='.github/workflows/pro-reference-collection.yml'


def select_checkpoint(runs,current_run_id,list_artifacts,list_jobs,*,current_run_attempt=1):
    # Reruns reuse a run ID and can hide earlier attempts from the API view.
    # Require a new dispatch instead of ever replaying identity lookups.
    if current_run_attempt!=1:raise ValueError('PRO_CACHE_RERUN_FORBIDDEN')
    if not isinstance(runs,list) or len(runs)>100:raise ValueError('PRO_CACHE_HISTORY_UNAVAILABLE')
    trusted=[r for r in runs if r.get('id')!=current_run_id and r.get('head_branch')=='main' and
             r.get('event') in ('workflow_dispatch','schedule') and r.get('path')==PATH]
    for run in sorted(trusted,key=lambda r:r.get('run_number',0),reverse=True):
        if run.get('run_attempt',1)!=1:raise ValueError('PRO_CACHE_HISTORICAL_ATTEMPT_UNRESOLVED')
        artifacts=list_artifacts(run['id'])
        if not isinstance(artifacts,list) or len(artifacts)>100:raise ValueError('PRO_CACHE_HISTORY_UNAVAILABLE')
        matches=[a for a in artifacts if a.get('name')==CACHE_NAME]
        if len(matches)>1:raise ValueError('PRO_CACHE_AMBIGUOUS')
        if matches:
            a=matches[0]
            if a.get('expired') or type(a.get('id')) is not int:raise ValueError('PRO_CACHE_NEWEST_EXPIRED')
            if type(a.get('size_in_bytes')) is not int or not 0<a['size_in_bytes']<=MAX_OUTER_BYTES:raise ValueError('PRO_CACHE_ARTIFACT_SIZE_UNKNOWN')
            return dict(status='FOUND',run_id=run['id'],artifact_id=a['id'],artifact_name=CACHE_NAME)
        jobs=list_jobs(run['id'])
        if not isinstance(jobs,list) or len(jobs)!=1:raise ValueError('PRO_CACHE_UNRESOLVED_RUN')
        steps=[s for s in jobs[0].get('steps',[]) if s.get('name')==COLLECT_STEP]
        if len(steps)!=1 or steps[0].get('conclusion')!='skipped':
            raise ValueError('PRO_CACHE_INTERRUPTED_OR_UNCHECKPOINTED_COLLECTION')
    if len(runs)==100:raise ValueError('PRO_CACHE_HISTORY_BOUND_NO_BOOTSTRAP')
    return dict(status='ABSENT',run_id=None,artifact_id=None,reason='NO_PRIOR_COLLECTION_ATTEMPT')


def extract_checkpoint_zip(source,output):
    path=Path(source);dest=Path(output)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_OUTER_BYTES or dest.exists() or dest.is_symlink():raise ValueError('PRO_CACHE_INVALID_OUTER_ARTIFACT')
    try:
        with zipfile.ZipFile(path) as archive:
            members=archive.infolist()
            if len(members)!=1:raise ValueError('PRO_CACHE_INVALID_OUTER_MEMBERS')
            member=members[0];mode=member.external_attr>>16;kind=stat.S_IFMT(mode)
            if member.filename!='pro-private.bundle' or member.is_dir() or kind not in (0,stat.S_IFREG) or not 35<=member.file_size<=MAX_CIPHER_BYTES:
                raise ValueError('PRO_CACHE_INVALID_OUTER_MEMBER')
            dest.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(prefix='.cipher-',dir=dest.parent)
            try:
                os.fchmod(fd,0o600);size=0
                with os.fdopen(fd,'wb') as target,archive.open(member) as source_stream:
                    while True:
                        block=source_stream.read(65536)
                        if not block:break
                        size+=len(block)
                        if size>MAX_CIPHER_BYTES:raise ValueError('PRO_CACHE_OUTER_SIZE_LIMIT')
                        target.write(block)
                if size!=member.file_size:raise ValueError('PRO_CACHE_OUTER_SIZE_MISMATCH')
                os.replace(name,dest)
            finally:
                if os.path.exists(name):os.unlink(name)
    except (zipfile.BadZipFile,RuntimeError):raise ValueError('PRO_CACHE_INVALID_OUTER_ARTIFACT') from None

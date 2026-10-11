"""Bounded, gratis requests for the remaining pinned official champion data."""
from pathlib import Path
import concurrent.futures
import datetime
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'evidence/queue/q05-expansion'
SOURCES = HERE / 'sources'
SOURCES.mkdir(parents=True, exist_ok=True)
catalog = json.loads((ROOT / 'knowledge_candidates/q05-roster-profiles.json').read_text())
initial = set(catalog['detailed_profile_ids'])
remaining = [p['champion_id'] for p in catalog['profiles'] if p['champion_id'] not in initial]
assert len(remaining) == 160


def fetch(cid):
    url = f'https://ddragon.leagueoflegends.com/cdn/16.20.1/data/en_US/champion/{cid}.json'
    path = SOURCES / f'{cid}-16.20.1.json'
    began = datetime.datetime.now(datetime.timezone.utc).isoformat()
    response = subprocess.run(['curl','--fail','--silent','--show-error','--location','--max-time','45',
                               '--retry','0','--write-out','%{http_code} %{url_effective}',url,'-o',str(path)],
                              capture_output=True,text=True)
    end = datetime.datetime.now(datetime.timezone.utc).isoformat()
    body = path.read_bytes() if path.exists() else None
    semantic_error = None
    try:
        doc = json.loads(body) if body is not None else None
        assert response.returncode == 0 and response.stdout.startswith('200 ')
        assert doc['version']=='16.20.1' and set(doc['data'])=={cid}
        assert len(doc['data'][cid]['spells'])==4
    except (AssertionError, ValueError, TypeError, KeyError):
        semantic_error = 'EXPECTED_OFFICIAL_PINNED_CHAMPION_DOCUMENT_NOT_CONFIRMED'
    return dict(champion_id=cid,url=url,archive=str(path.relative_to(ROOT)) if body is not None else None,
                requested_at_utc=began,retrieved_at_utc=end,curl_exit=response.returncode,
                http_status_effective_url=response.stdout,error=response.stderr or None,
                bytes=len(body) if body is not None else None,
                sha256=hashlib.sha256(body).hexdigest() if body is not None else None,
                semantic_error=semantic_error,status='SOURCE_VERIFIED' if semantic_error is None else 'FAILED')


receipts = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for receipt in pool.map(fetch, remaining):
        receipts.append(receipt)
        (HERE / 'source-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
        if len(receipts)%20==0:
            print(f'Recorded {len(receipts)}/160 official response receipts.',flush=True)
summary = dict(requested_ids=remaining,initial_detailed_ids=sorted(initial),
               successful_ids=[r['champion_id'] for r in receipts if r['status']=='SOURCE_VERIFIED'],
               failed_ids=[r['champion_id'] for r in receipts if r['status']!='SOURCE_VERIFIED'],
               request_count=len(receipts),max_parallel=6,max_request_seconds=45,retries=0,
               paid_services=0,source_version='16.20.1')
(HERE / 'fetch-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(f"Complete: {len(summary['successful_ids'])}/160 source-verified;failed={summary['failed_ids']}")

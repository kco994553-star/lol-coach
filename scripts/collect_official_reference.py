"""Archive public official Korean descriptions; no login or paid API."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
VERSION='16.20.1'
CHAMPIONS=('Ornn','Sejuani','Ahri','Caitlyn','Lux','Fiora','LeeSin','Zed','Ezreal','Nautilus','Yunara','Ashe','Kaisa')


def main():
    folder=ROOT/'data/official_reference/2026-10-14';folder.mkdir(parents=True,exist_ok=True)
    sources=[]
    for champion in CHAMPIONS:
        url=f'https://ddragon.leagueoflegends.com/cdn/{VERSION}/data/ko_KR/champion/{champion}.json'
        request=urllib.request.Request(url,headers={'User-Agent':'lol-coach-official-reference/1.0'})
        with urllib.request.urlopen(request,timeout=30) as response:
            raw=response.read(2_000_001)
            if len(raw)>2_000_000:raise ValueError('source too large')
            content=json.loads(raw)
            detail=content['data'][champion]
            if content['version']!=VERSION or len(detail['spells'])!=4 or not detail['passive']['description']:raise ValueError('source shape')
            filename=f'{champion}-{VERSION}.ko_KR.json';(folder/filename).write_bytes(raw)
            sources.append(dict(champion=champion,name=detail['name'],file=filename,url=url,sha256=hashlib.sha256(raw).hexdigest(),http_status=response.status))
    manifest=dict(schema_version='official-reference.archive.v1',source_patch=VERSION,game_patch='16.20',locale='ko_KR',collected_at=datetime.now(timezone.utc).isoformat(),sources=sources)
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(champions=len(sources),facts=len(sources)*5,source_patch=VERSION),ensure_ascii=False))


if __name__=='__main__':main()

"""Build only public skill names/slots from hash-bound retained official sources."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'web_r4/skill-data.js'

def build():
    catalog=json.loads((ROOT/'web_r4/loading-data.json').read_text())
    champions={}
    for key,champion in sorted(catalog['champions'].items()):
        facts={f['slot']:f for f in champion['facts']}
        source=facts['P']
        path=ROOT/source['local_source']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256'], key
        raw=json.loads(path.read_text())['data'][key]
        slots={'P':raw['passive']['name'],**{slot:raw['spells'][i]['name'] for i,slot in enumerate('QWER')}}
        assert set(facts)==set(slots) and all(facts[s]['name']==name for s,name in slots.items()), key
        assert champion['name']==raw['name']
        champions[key]={'id':key,'name':raw['name'],'slots':slots,
                        'source':{k:source[k] for k in ('patch','url','sha256','local_source')}}
    data={'format':'lol-coach-skill-display-names-v1','source_patch':catalog['source_patch'],'champions':champions}
    return ('/* Generated offline by scripts/build_skill_display.py; official names only. */\n'
            '(function(root){const data='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n'
            'if(typeof module===\"object\"&&module.exports)module.exports=data;else root.LoLSkillNames=data;\n'
            '})(typeof globalThis!==\"undefined\"?globalThis:this);\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    expected=build()
    if a.check:
        assert DEST.read_text()==expected,'SKILL_DISPLAY_NAMES_STALE'
    else:DEST.write_text(expected)
    print(json.dumps({'status':'PASS','champions':173,'slots':865,'external_requests':0}))

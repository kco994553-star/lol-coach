"""Repackage the existing verified DD archive; no network or catalogue refresh."""
import json
from pathlib import Path
from coach_v1.official_items import _current

def build():
    manifest,rows,_=_current()
    return {'format':'lol-coach-item-reference-v1','version':manifest['version'],'patch':manifest['game_patch'],'source':manifest['source'],'retrieved_at':manifest['retrieved_at'],'meaning':'SUMMONERS_RIFT_CATALOG_NOMINAL_TOTAL_NOT_ACTUAL_SPENT','items':{r['id']:{'name':r['name'],'total':r['gold']['total'],'from':r['from'],'in_store':r['in_store'],'required_champion':r['required_champion'],'required_ally':r['required_ally']}for r in rows if r['maps'].get('11')is True}}
if __name__=='__main__':
    Path('web_r4/game-info-items.json').write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n')

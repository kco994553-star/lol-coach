"""Official Korean source text, independent of tactical USER approval.

A verified archived description is reference material. It never creates a
KnowledgeStore proposal/decision, predicts a trade, or bypasses plan guards.
"""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'data/official_reference/2026-10-14/manifest.json'


class _PlainText(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='br':self.parts.append(' ')
    def handle_data(self,data):self.parts.append(data)


def _plain(value):
    if not isinstance(value,str):raise ValueError('source text')
    parser=_PlainText();parser.feed(value);parser.close()
    text=re.sub(r'\s+',' ',''.join(parser.parts)).strip()
    if not text or len(text)>6000:raise ValueError('source text bounds')
    return text


def facts_response(champions=None,patch=None):
    result=dict(schema_version='official-reference.v1',approval_required=False,reference_only=True,game_patch=patch,
                reference_status='UNAVAILABLE',champions=[],unavailable=[])
    try:
        if MANIFEST.is_symlink() or MANIFEST.stat().st_size>2_000_000:raise ValueError('manifest file')
        manifest=json.loads(MANIFEST.read_text())
        if not isinstance(manifest,dict) or manifest.get('schema_version')!='official-reference.archive.v1':raise ValueError('manifest format')
        version=manifest.get('source_patch')
        if not isinstance(version,str) or not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('manifest version')
        if manifest.get('game_patch')!='.'.join(version.split('.')[:2]) or manifest.get('locale')!='ko_KR':raise ValueError('manifest patch mapping')
        rows=manifest.get('sources')
        if not isinstance(rows,list) or not rows or len(rows)>200:raise ValueError('manifest sources')
        if any(not isinstance(row,dict) or not isinstance(row.get('champion'),str) for row in rows):raise ValueError('source selector')
        sources={row['champion']:row for row in rows}
        if len(sources)!=len(rows):raise ValueError('duplicate sources')
    except (OSError,ValueError,KeyError,TypeError):
        result['reason']='OFFICIAL_MANIFEST_UNAVAILABLE_OR_INVALID'
        return result
    wanted=list(sources) if champions is None else list(dict.fromkeys(champions))
    result['reference_status']='AVAILABLE'
    for champion in wanted:
        try:
            source=sources[champion];version=manifest['source_patch']
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,99}',champion) or not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('source selector')
            filename=f'{champion}-{version}.ko_KR.json'
            url=f'https://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/champion/{champion}.json'
            if source['file']!=filename or source['url']!=url or manifest['locale']!='ko_KR':raise ValueError('source origin')
            path=MANIFEST.parent/filename
            if path.is_symlink() or path.stat().st_size>2_000_000:raise ValueError('source file')
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=source['sha256']:raise ValueError('source integrity')
            data=json.loads(raw)
            if data['version']!=version:raise ValueError('source patch')
            detail=data['data'][champion]
            if len(detail['spells'])!=4:raise ValueError('source spells')
            facts=[]
            for key,ability in [('passive',detail['passive']),*[(f'spells.{i}',spell) for i,spell in enumerate(detail['spells'])]]:
                facts.append(dict(name=_plain(ability['name']),text=_plain(ability['description']),verification='OFFICIAL_ARCHIVE_VERIFIED',
                    source=dict(url=url,sha256=source['sha256'],locator=f'data.{champion}.{key}.description',patch=version)))
            status='GAME_PATCH_UNKNOWN' if patch is None else 'MATCHING_ARCHIVE' if patch==manifest['game_patch'] else 'GAME_PATCH_MISMATCH'
            result['champions'].append(dict(champion=champion,name=detail['name'],source_patch=version,patch_status=status,facts=facts))
        except (OSError,ValueError,KeyError,TypeError):
            result['unavailable'].append(dict(champion=champion,reason='SOURCE_UNAVAILABLE_OR_UNVERIFIED'))
    return result


def request_facts(body):
    from .storage import ServiceError
    if not isinstance(body,dict) or set(body)!={'champions','patch'} or not isinstance(body['champions'],list) or len(body['champions'])>30:
        raise ServiceError(422,'INVALID_OFFICIAL_REFERENCE_REQUEST')
    if any(not isinstance(c,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,99}',c) for c in body['champions']) or body['patch'] is not None and (not isinstance(body['patch'],str) or not body['patch'].strip() or len(body['patch'])>100):
        raise ServiceError(422,'INVALID_OFFICIAL_REFERENCE_REQUEST')
    return facts_response(body['champions'],patch=body['patch'])

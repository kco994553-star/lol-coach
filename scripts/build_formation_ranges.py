"""Extract reference attackrange stats from retained official bytes, entirely offline."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = '16.20.1'
DEST = ROOT / 'web_r4/formation-ranges.js'
LIMITS = [
    '기본 공격 사거리는 공식 자료의 stats.attackrange에 기록된 게임 단위 참고 수치입니다.',
    '가상 배치의 원은 이 기본 수치를 비교하는 표시이며, 실제 위치·거리나 전체 위협 범위를 확정하지 않습니다.',
    '스킬 사거리, 현재 버프·아이템·형태 변화에 따른 사거리 변화는 반영하지 않습니다.',
    '챔피언·대상의 충돌 반경, 지형, 시야와 대상 지정 가능 여부를 계산하지 않으므로 원 안에 있어도 공격 가능을 보장하지 않습니다.',
    '자료를 확인할 수 없는 수치는 0으로 대체하지 않고 미확인으로 남깁니다. 이 수치만으로 교전 결과나 전술의 유효성을 판단할 수 없습니다.',
]


def build_data(root=ROOT):
    root = Path(root)
    catalog = json.loads((root / 'web_r4/loading-data.json').read_text(encoding='utf-8'))
    if catalog['source_patch'] != PATCH:
        raise ValueError('FORMATION_RANGE_SOURCE_PATCH_MISMATCH')
    champions = {}
    for champion, catalog_entry in sorted(catalog['champions'].items()):
        local = f'data/official_catalog/versions/{PATCH}/{champion}-{PATCH}.ko_KR.json'
        source = {
            'url': f'https://ddragon.leagueoflegends.com/cdn/{PATCH}/data/ko_KR/champion/{champion}.json',
            'patch': PATCH,
            'sha256': None,
            'local_source': local,
            'locator': f'data.{champion}.stats.attackrange',
        }
        entry = {'base_attack_range': None, 'source': source, 'missing_reason': None}
        path = root / local
        if not path.is_file():
            entry['missing_reason'] = '보관한 공식 챔피언 원문 파일을 확인할 수 없습니다.'
        else:
            raw_bytes = path.read_bytes()
            source['sha256'] = hashlib.sha256(raw_bytes).hexdigest()
            for fact in catalog_entry.get('facts', []):
                if fact.get('local_source') == local and fact.get('sha256') != source['sha256']:
                    raise ValueError(f'FORMATION_RANGE_SOURCE_HASH_MISMATCH:{champion}')
            document = json.loads(raw_bytes)
            raw = document.get('data', {}).get(champion)
            if document.get('version') != PATCH or not isinstance(raw, dict) or raw.get('id') != champion:
                raise ValueError(f'FORMATION_RANGE_SOURCE_ID_OR_PATCH_MISMATCH:{champion}')
            stats = raw.get('stats')
            value = stats.get('attackrange') if isinstance(stats, dict) else None
            if type(value) in (int, float) and math.isfinite(value) and value > 0:
                entry['base_attack_range'] = value
            else:
                entry['missing_reason'] = '공식 원문의 stats.attackrange에서 유효한 기본 공격 사거리를 확인할 수 없습니다.'
        champions[champion] = entry
    return {
        'format': 'lol-coach-formation-ranges-v1',
        'source_patch': PATCH,
        'champions': champions,
        'limits': list(LIMITS),
    }


def build(root=ROOT):
    data = json.dumps(build_data(root), ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return (
        '/* Generated offline by scripts/build_formation_ranges.py; official reference stats only. */\n'
        '(function(root){const data=' + data + ';\n'
        'if(typeof module==="object"&&module.exports)module.exports=data;else root.FormationRanges=data;\n'
        '})(typeof globalThis!=="undefined"?globalThis:this);\n'
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = build()
    if args.check:
        if not DEST.is_file() or DEST.read_text(encoding='utf-8') != expected:
            raise SystemExit('FORMATION_RANGES_STALE')
    else:
        DEST.write_text(expected, encoding='utf-8')
    data = build_data()
    print(json.dumps({
        'status': 'PASS',
        'champions': len(data['champions']),
        'missing': sum(entry['base_attack_range'] is None for entry in data['champions'].values()),
        'external_requests': 0,
    }))

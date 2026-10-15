"""New v2.3 item sources and candidate boundaries; no completed-catalog rerun."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def raw(value):
    return json.dumps(value, ensure_ascii=False).encode()


def fixture(version='19.4.2'):
    origin = 'https://ddragon.leagueoflegends.com'
    rows = {
        '1036': dict(name='롱소드', description='공격력 증가', gold=dict(total=350, purchasable=True), maps={'11': True, '12': True}),
        '3072': dict(name='피바라기', description='생명력 흡수', gold=dict(total=3400, purchasable=True), maps={'11': True, '12': False}, **{'from': ['1036']}),
        '9999': dict(name='상점 제외', description='특수', gold=dict(total=0, purchasable=False), maps={'11': False}),
    }
    return {origin+'/api/versions.json': raw([version, 'lolpatch_7.20']),
            f'{origin}/cdn/{version}/data/ko_KR/item.json': raw(dict(type='item', version=version, data=rows))}


class OfficialItemsV23Tests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.official_items'), 'new official item catalog is missing')
        from coach_v1 import official_items
        self.catalog = official_items
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'items'
        p = patch.object(self.catalog, 'CATALOG_ROOT', self.root); p.start(); self.addCleanup(p.stop)

    def collect(self, version='19.4.2', data=None):
        data = fixture(version) if data is None else data
        return self.catalog.refresh_if_due(force=True, fetch=lambda url, limit, timeout: data[url])

    def test_official_bytes_and_component_map_prices_have_machine_provenance(self):
        data = fixture(); self.assertEqual(self.collect(data=data)['state'], 'UPDATED')
        result = self.catalog.items_response('19.4.9.123')
        self.assertTrue(result['prices_usable'])
        self.assertEqual(result['patch_status'], 'MATCHING_ARCHIVE')
        self.assertEqual(result['requested_patch'], '19.4.9.123')
        self.assertEqual(result['catalog_version'], '19.4.2')
        rows = {i['id']: i for i in result['items']}
        self.assertEqual(rows['3072']['gold']['total'], 3400)
        self.assertEqual(rows['3072']['from'], ['1036'])
        self.assertFalse(rows['3072']['maps']['12'])
        self.assertFalse(rows['9999']['in_store'])
        source = result['source']
        self.assertEqual(source['sha256'], hashlib.sha256(data[source['url']]).hexdigest())
        self.assertEqual((self.root/'versions/19.4.2/item.ko_KR.json').read_bytes(), data[source['url']])

    def test_patch_unknown_mismatch_or_invalid_never_exposes_goal_prices(self):
        self.collect()
        for actual, status in [(None,'GAME_PATCH_UNKNOWN'),('19.5','GAME_PATCH_MISMATCH'),('../19.4','GAME_PATCH_INVALID'),(19.4,'GAME_PATCH_INVALID')]:
            with self.subTest(actual=actual):
                result = self.catalog.items_response(actual)
                self.assertFalse(result['prices_usable']); self.assertEqual(result['items'], [])
                self.assertEqual(result['patch_status'], status)
                self.assertTrue(result['warnings'])
        self.assertTrue(self.catalog.items_response('19.4')['prices_usable'])

    def test_append_only_archive_failure_fallback_and_readers_stay_offline(self):
        self.collect(); previous = (self.root/'versions/19.4.2/item.ko_KR.json').read_bytes()
        self.collect('19.5.1'); pointer = (self.root/'current.json').read_bytes()
        def offline(*args): raise OSError('offline')
        self.assertEqual(self.catalog.refresh_if_due(force=True, fetch=offline)['state'], 'OFFLINE_FALLBACK')
        checked = (self.root/'refresh-status.json').read_bytes()
        with patch.object(self.catalog, '_fetch', side_effect=AssertionError('reader network')):
            self.assertTrue(self.catalog.items_response('19.5')['prices_usable'])
            self.assertEqual(self.catalog.refresh_if_due(fetch=offline)['state'], 'OFFLINE_FALLBACK')
        self.assertEqual((self.root/'refresh-status.json').read_bytes(), checked)
        self.assertEqual((self.root/'current.json').read_bytes(), pointer)
        self.assertEqual((self.root/'versions/19.4.2/item.ko_KR.json').read_bytes(), previous)
        self.assertEqual(self.collect('19.4.2')['state'], 'UNCHANGED')
        self.assertEqual((self.root/'versions/19.4.2/item.ko_KR.json').read_bytes(), previous)

    def test_corrupt_source_or_manifest_fail_closed(self):
        self.collect(); path = self.root/'versions/19.4.2/item.ko_KR.json'
        path.write_bytes(b'{}')
        self.assertEqual(self.catalog.items_response('19.4')['status'], 'UNAVAILABLE')
        self.assertEqual(self.catalog.items_response('19.4')['items'], [])
        self.assertEqual(self.collect()['state'], 'UNAVAILABLE')
        self.assertEqual(path.read_bytes(), b'{}')

    def test_invalid_source_size_version_prices_maps_components_never_publish(self):
        for alteration in ['size','version','price','boolean_price','maps','component','wrong_kind']:
            data = fixture(); key = next(k for k in data if k.endswith('/item.json'))
            doc = json.loads(data[key])
            if alteration == 'size': data[key] = b' ' * (self.catalog.MAX_SOURCE+1)
            elif alteration == 'version': doc['version'] = '19.5.1'
            elif alteration == 'price': doc['data']['1036']['gold']['total'] = -1
            elif alteration == 'boolean_price': doc['data']['1036']['gold']['total'] = True
            elif alteration == 'maps': doc['data']['1036']['maps']['11'] = 'yes'
            elif alteration == 'component': doc['data']['3072']['from'] = ['../escape']
            elif alteration == 'wrong_kind': doc['type'] = 'champion'
            if alteration != 'size': data[key] = raw(doc)
            with self.subTest(alteration=alteration):
                self.assertEqual(self.collect(data=data)['state'], 'UNAVAILABLE')
                self.assertFalse((self.root/'current.json').exists())

    def test_bounded_discovery_and_refresh_age(self):
        for versions in [[], ['../escape'], ['19.4.2']*10001]:
            data=fixture(); data[self.catalog.VERSIONS_URL]=raw(versions)
            self.assertEqual(self.collect(data=data)['state'], 'UNAVAILABLE')
        for age in [True, -1, math.inf, math.nan, 31_536_001]:
            with self.subTest(age=age), self.assertRaises(ValueError):
                self.catalog.refresh_if_due(max_age_seconds=age)
        self.collect()
        self.assertEqual(self.catalog.refresh_if_due(fetch=lambda *a: self.fail('fresh catalog fetched'))['state'], 'FRESH')

    def test_official_unnamed_mode_items_are_preserved_without_invented_names(self):
        data=fixture(); key=next(k for k in data if k.endswith('/item.json'))
        doc=json.loads(data[key]); doc['data']['9999']['name']=''
        data[key]=raw(doc)
        self.assertEqual(self.collect(data=data)['state'], 'UPDATED')
        item=next(x for x in self.catalog.items_response('19.4')['items'] if x['id']=='9999')
        self.assertEqual(item['name'],''); self.assertFalse(item['maps']['11'])

    def test_native_lock_serializes_refresh(self):
        self.root.mkdir()
        lock = self.catalog._acquire_refresh_lock()
        try:
            self.assertEqual(self.collect()['reason'], 'REFRESH_IN_PROGRESS')
        finally:
            self.catalog._release_refresh_lock(lock)
        self.assertEqual(self.collect()['state'], 'UPDATED')


class RecallV23CandidateTests(unittest.TestCase):
    def test_preferred_classifications_and_advice_remain_unverified_with_exact_sources(self):
        path=ROOT/'knowledge_candidates/recall-v23.json'
        self.assertTrue(path.is_file(), 'separate source-backed candidate packet missing')
        packet=json.loads(path.read_bytes())
        self.assertEqual(packet['schema_version'], 'recall-candidates.v1')
        classifications=[c for c in packet['rows'] if c['kind']=='CLASSIFICATION']
        self.assertEqual({c['champion'] for c in classifications}, {'Yunara','Ashe','Kaisa','Caitlyn'})
        self.assertEqual(len(classifications),12)
        for champion in ['Yunara','Ashe','Kaisa','Caitlyn']:
            self.assertEqual({c['dimension'] for c in classifications if c['champion']==champion},
                             {'wave_clear_speed','low_health_sustain','opponent_finishing'})
        for candidate in packet['rows']:
            self.assertIn(candidate['status'], ['HYPOTHESIS','UNKNOWN'])
            self.assertIsNone(candidate['value'])
            self.assertTrue(candidate['limitations']); self.assertTrue(candidate['counterarguments'])
            self.assertEqual(set(candidate['advice']), {'상황','할 것','하지 말 것','상대 권리','무효 조건','근거','패치'})
            self.assertEqual(candidate['review_status'], 'HOLD')
            self.assertEqual(candidate['tactical_verification'], 'UNKNOWN')
            self.assertTrue(candidate['hold_reasons'])
            self.assertTrue(candidate['sources'])
            for source in candidate['sources']: self.assert_source(source)
        self.assertEqual(len([c for c in packet['rows'] if c['kind']=='ADVICE']),8)

    def test_lowhealth_uses_mobility_range_wave_and_macro_conditions_have_opponent_rights(self):
        packet=json.loads((ROOT/'knowledge_candidates/recall-v23.json').read_bytes())
        for candidate in packet['rows']:
            if candidate.get('dimension')=='low_health_sustain':
                self.assertIn('이동기·사거리·원거리 웨이브',candidate['advice']['할 것'])
                self.assertIn('상대 사거리',candidate['advice']['무효 조건'])
            if candidate['kind']=='ADVICE':
                expected=(4,3) if candidate['section']=='RECALL' else (4,5)
                self.assertEqual((len(candidate['macro_conditions']['good']),len(candidate['macro_conditions']['avoid'])),expected)
                for conditions in candidate['macro_conditions'].values():
                    for condition in conditions:
                        self.assertEqual(condition['scenario_origin'],'USER_REQUESTED_NOT_OBSERVED')
                        self.assertTrue(condition['상대 권리'])
                        self.assertTrue(condition['무효 조건'])
                        self.assertEqual(condition['source_support'],'UNKNOWN')

    def assert_source(self, source):
        path=ROOT/source['path']
        self.assertTrue(path.is_relative_to(ROOT))
        contents=path.read_bytes()
        self.assertEqual(hashlib.sha256(contents).hexdigest(), source['sha256'])
        node=json.loads(contents)
        for segment in source['locator'].split('.'):
            node=node[int(segment)] if isinstance(node,list) else node[segment]
        self.assertEqual(node, source['excerpt'])
        self.assertTrue(source['url'].startswith('https://ddragon.leagueoflegends.com/cdn/'))
        self.assertIn('/data/ko_KR/',source['url'])


if __name__ == '__main__': unittest.main()

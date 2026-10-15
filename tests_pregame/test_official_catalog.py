"""Catalog publication, provenance, and offline behavior without live networking."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


def raw(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


def fixture(version, champions=('Ahri', 'Ashe')):
    base='https://ddragon.leagueoflegends.com'
    data={base+'/api/versions.json':raw([version, '15.1.1'])}
    roster={c:dict(id=c, name='한국어 '+c) for c in champions}
    data[f'{base}/cdn/{version}/data/ko_KR/champion.json']=raw(dict(type='champion',version=version,data=roster))
    for c in champions:
        ability=dict(name='한국어 능력',description='<mainText>설명<br>다음 &amp; 효과</mainText>')
        detail=dict(roster[c],passive=ability,spells=[ability]*4)
        data[f'{base}/cdn/{version}/data/ko_KR/champion/{c}.json']=raw(dict(type='champion',version=version,data={c:detail}))
    return data


class OfficialCatalogTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.official_catalog'), 'all-champion catalog is missing')
        from coach_v1 import official_catalog
        self.catalog=official_catalog
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'catalog'
        self.patch=patch.object(self.catalog,'CATALOG_ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)
        self.legacy=patch.object(self.catalog,'LEGACY_ROOT',Path(self.tmp.name)/'legacy');self.legacy.start();self.addCleanup(self.legacy.stop)

    def collect(self,version='19.4.2',data=None):
        data=data or fixture(version)
        return self.catalog.update_catalog(fetch=lambda url,limit,timeout:data[url])

    def test_discovers_version_archives_exact_bytes_and_serves_all_five_abilities(self):
        data=fixture('19.4.2');status=self.collect(data=data)
        self.assertEqual(status['state'],'UPDATED')
        self.assertEqual(status['champion_count'],2)
        response=self.catalog.facts_response(patch='19.4')
        self.assertEqual(len(response['champions']),2)
        self.assertFalse(response['approval_required'])
        self.assertEqual(response['unavailable'],[])
        for c in response['champions']:
            self.assertEqual(c['patch_status'],'MATCHING_ARCHIVE')
            self.assertEqual(len(c['facts']),5)
            for fact in c['facts']:
                self.assertEqual(fact['text'],'설명 다음 & 효과')
                self.assertEqual(fact['source']['sha256'],hashlib.sha256(data[fact['source']['url']]).hexdigest())
        manifest=json.loads((self.root/'versions/19.4.2/manifest.json').read_text())
        for source in [manifest['discovery'],manifest['roster'],*manifest['sources']]:
            self.assertEqual((self.root/'versions/19.4.2'/source['file']).read_bytes(),data[source['url']])

    def test_new_release_preserves_prior_archive_and_failed_release_keeps_pointer(self):
        self.collect();previous=(self.root/'versions/19.4.2/manifest.json').read_bytes()
        self.collect('19.5.1')
        pointer=(self.root/'current.json').read_bytes()
        data=fixture('19.6.1');key=next(k for k in data if k.endswith('/Ashe.json'));data[key]=b'{}'
        status=self.collect(data=data)
        self.assertEqual(status['state'],'OFFLINE_FALLBACK')
        self.assertEqual((self.root/'current.json').read_bytes(),pointer)
        self.assertEqual((self.root/'versions/19.4.2/manifest.json').read_bytes(),previous)
        self.assertFalse((self.root/'versions/19.6.1').exists())
        self.assertEqual(self.catalog.facts_response()['source_patch'],'19.5.1')

    def test_refresh_throttles_success_and_offline_attempts_without_ui_network(self):
        self.collect()
        def offline(*args):
            raise OSError('network unavailable')
        with patch.object(self.catalog,'_fetch',side_effect=AssertionError('UI must be offline')):
            self.assertEqual(self.catalog.facts_response()['reference_status'],'AVAILABLE')
            self.assertEqual(self.catalog.refresh_if_due(fetch=offline)['state'],'FRESH')
            self.assertEqual(self.catalog.refresh_if_due(force=True,fetch=offline)['state'],'OFFLINE_FALLBACK')
            self.assertEqual(self.catalog.refresh_if_due(fetch=offline)['state'],'OFFLINE_FALLBACK')

    def test_corruption_unknown_champion_and_actual_patch_mismatch_are_explicit(self):
        self.collect()
        for actual,status in [(None,'GAME_PATCH_UNKNOWN'),('19.4','MATCHING_ARCHIVE'),('19.4.2','MATCHING_ARCHIVE'),('19.5','GAME_PATCH_MISMATCH')]:
            result=self.catalog.facts_response(['Ahri'],actual)
            self.assertEqual(result['game_patch'],actual)
            self.assertEqual(result['champions'][0]['patch_status'],status)
        (self.root/'versions/19.4.2/Ahri-19.4.2.ko_KR.json').write_bytes(b'{}')
        result=self.catalog.facts_response(['Ahri','Unknown','Ashe'])
        self.assertEqual([c['champion'] for c in result['champions']],['Ashe'])
        self.assertEqual([c['champion'] for c in result['unavailable']],['Ahri','Unknown'])

    def test_invalid_discovery_oversize_and_roster_mismatch_never_publish(self):
        for alter in ['version','oversize','roster']:
            data=fixture('19.4.2')
            if alter=='version':data[self.catalog.VERSIONS_URL]=raw(['../../evil'])
            elif alter=='oversize':data[self.catalog.VERSIONS_URL]=b' '*200001
            else:
                key=next(k for k in data if k.endswith('/Ashe.json'))
                value=json.loads(data[key]);value['data']['Ashe']['id']='Ahri';data[key]=raw(value)
            with self.subTest(alter=alter):
                self.assertEqual(self.collect(data=data)['state'],'UNAVAILABLE')
                self.assertFalse((self.root/'current.json').exists())

    def test_manifest_and_roster_hash_are_required_for_trusted_catalog(self):
        self.collect()
        pointer=json.loads((self.root/'current.json').read_text())
        pointer['manifest_sha256']='0'*64
        (self.root/'current.json').write_bytes(raw(pointer))
        self.assertEqual(self.catalog.facts_response()['reference_status'],'UNAVAILABLE')

    def test_official_historical_version_labels_do_not_reject_latest_release(self):
        data=fixture('19.4.2')
        data[self.catalog.VERSIONS_URL]=raw(['19.4.2','10.10.3216176','lolpatch_7.20'])
        self.assertEqual(self.collect(data=data)['state'],'UPDATED')

    def test_legacy_reuse_requires_exact_manifest_hash(self):
        data=fixture('19.4.2');legacy=self.catalog.LEGACY_ROOT;legacy.mkdir()
        sources=[]
        for c in ('Ahri','Ashe'):
            url=self.catalog._source_url('19.4.2',c)
            filename=f'{c}-19.4.2.ko_KR.json'
            (legacy/filename).write_bytes(data[url])
            sources.append(dict(champion=c,file=filename,url=url,sha256=hashlib.sha256(data[url]).hexdigest()))
        # A corrupt legacy member must be fetched rather than trusted.
        (legacy/'Ashe-19.4.2.ko_KR.json').write_bytes(b'{}')
        (legacy/'manifest.json').write_bytes(raw(dict(source_patch='19.4.2',locale='ko_KR',sources=sources)))
        del data[self.catalog._source_url('19.4.2','Ahri')]
        self.assertEqual(self.collect(data=data)['reused_legacy_count'],1)
        self.assertEqual(len(self.catalog.facts_response()['champions']),2)

    def test_failure_retry_timestamp_is_not_renewed_by_skipped_calls(self):
        self.collect()
        status=self.catalog.refresh_if_due(force=True,fetch=lambda *args: (_ for _ in ()).throw(OSError('offline')))
        original=(self.root/'refresh-status.json').read_bytes()
        self.assertEqual(status['state'],'OFFLINE_FALLBACK')
        skipped=self.catalog.refresh_if_due(fetch=lambda *args: (_ for _ in ()).throw(AssertionError('not due')))
        self.assertEqual((self.root/'refresh-status.json').read_bytes(),original)
        self.assertEqual(skipped['checked_at'],status['checked_at'])

    def test_refresh_excludes_live_process_and_recovers_after_owner_is_killed(self):
        self.assertTrue(hasattr(self.catalog,'_acquire_refresh_lock'), 'process-safe recoverable lock missing')
        self.root.mkdir()
        script='''
import sys,time
from pathlib import Path
from coach_v1 import official_catalog as c
c.CATALOG_ROOT=Path(sys.argv[1])
lock=c._acquire_refresh_lock()
print('locked' if lock else 'failed',flush=True)
time.sleep(60)
'''
        process=subprocess.Popen([sys.executable,'-c',script,str(self.root)],stdout=subprocess.PIPE,text=True)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        self.addCleanup(process.stdout.close)
        self.assertEqual(process.stdout.readline().strip(),'locked')
        self.assertEqual(self.collect()['reason'],'REFRESH_IN_PROGRESS')
        process.kill();process.wait(timeout=5)
        self.assertEqual(self.collect()['state'],'UPDATED')
        metadata=json.loads((self.root/'.refresh-lock').read_text())
        self.assertEqual(metadata['pid'],os.getpid())

    def test_request_supports_full_roster_and_rejects_unsafe_selectors(self):
        self.collect()
        self.assertEqual(len(self.catalog.request_facts(dict(champions=['Ahri']*40,patch=None))['champions']),1)
        from coach_v1.storage import ServiceError
        for body in [dict(champions=['../Ahri'],patch=None),dict(champions=['Ahri'],patch=12),dict(champions=[],patch=None,actor='USER')]:
            with self.assertRaises(ServiceError):self.catalog.request_facts(body)


class ShippedOfficialCatalogTests(unittest.TestCase):
    def test_archived_roster_is_complete_verified_korean_and_offline(self):
        from coach_v1 import official_catalog
        with patch.object(official_catalog,'_fetch',side_effect=AssertionError('offline reader')):
            result=official_catalog.facts_response(patch='0.0')
        self.assertEqual(result['reference_status'],'AVAILABLE')
        self.assertGreaterEqual(result['catalog_champion_count'],170)
        self.assertEqual(len(result['champions']),result['catalog_champion_count'])
        self.assertEqual(result['unavailable'],[])
        for c in result['champions']:
            self.assertEqual(c['patch_status'],'GAME_PATCH_MISMATCH')
            self.assertEqual(len(c['facts']),5)
            for f in c['facts']:
                self.assertRegex(f['text'],r'[가-힣]')
                self.assertNotRegex(f['text'],r'<[^>]*>')

if __name__=='__main__':unittest.main()

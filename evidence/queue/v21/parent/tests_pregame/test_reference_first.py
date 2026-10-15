"""Facts are read-only references; focused tactics never create USER decisions."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from coach_v1.pregame_server import PregameWorkbench,current_knowledge
from coach_v1.server import Limits
from coach_v1.review_queue import queue_response
from tests_pregame.test_contract import golden


class ReferenceFirstTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.official_reference'),'official Korean facts missing')
        from coach_v1 import official_reference
        self.f=official_reference
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.server=PregameWorkbench(Path(self.tmp.name)/'work.sqlite','fictional-reference-first-token-1234567890',Limits(1000000,100,100,100,100,10))
        self.addCleanup(self.server.server_close)

    def test_korean_official_facts_are_available_without_user_approval(self):
        response=self.f.facts_response(['Caitlyn','Ezreal','Nautilus'],patch='16.20')
        self.assertEqual(len(response['champions']),3)
        self.assertEqual(sum(len(c['facts']) for c in response['champions']),15)
        self.assertFalse(response['approval_required'])
        self.assertTrue(response['reference_only'])
        for champion in response['champions']:
            self.assertEqual(champion['patch_status'],'MATCHING_ARCHIVE')
            for fact in champion['facts']:
                self.assertEqual(fact['verification'],'OFFICIAL_ARCHIVE_VERIFIED')
                self.assertRegex(fact['text'],r'[가-힣]')
                self.assertTrue(fact['source']['url'].startswith('https://ddragon.leagueoflegends.com/cdn/16.20.1/data/ko_KR/'))
                self.assertNotRegex(fact['text'],r'<[^>]*>')
        self.assertEqual(current_knowledge(self.server.research),[])

    def test_all_priority_13_champions_have_65_facts(self):
        response=self.f.facts_response()
        self.assertEqual(len(response['champions']),13)
        self.assertEqual(sum(len(c['facts']) for c in response['champions']),65)
        self.assertEqual(response['unavailable'],[])

    def test_source_patch_never_becomes_current_game_patch(self):
        for patch,status in [(None,'GAME_PATCH_UNKNOWN'),('16.21','GAME_PATCH_MISMATCH')]:
            response=self.f.facts_response(['Caitlyn'],patch=patch)
            self.assertEqual(response['champions'][0]['patch_status'],status)
            self.assertEqual(response['game_patch'],patch)
            self.assertEqual(response['champions'][0]['source_patch'],'16.20.1')

    def test_corrupt_or_missing_source_is_not_shown_as_verified(self):
        manifest=self.f.MANIFEST
        data=json.loads(manifest.read_text())
        root=Path(self.tmp.name)/'facts';root.mkdir()
        data['sources']=[r for r in data['sources'] if r['champion']=='Caitlyn']
        (root/'manifest.json').write_text(json.dumps(data))
        source=root/data['sources'][0]['file'];source.write_text('{}')
        with patch.object(self.f,'MANIFEST',root/'manifest.json'):
            response=self.f.facts_response(['Caitlyn'])
        self.assertEqual(response['champions'],[])
        self.assertEqual(response['unavailable'][0]['champion'],'Caitlyn')

    def test_unknown_champion_has_no_invented_facts(self):
        response=self.f.facts_response(['MissingChampion'])
        self.assertEqual(response['champions'],[])
        self.assertEqual(response['unavailable'][0]['champion'],'MissingChampion')

    def test_default_focus_is_five_optional_tactics_not_thirty_obligations(self):
        response=queue_response(self.server,focused=True)
        self.assertLessEqual(len(response['candidates']),5)
        self.assertEqual(response['progress']['reviewed'],0)
        self.assertFalse(response['operating_policy']['review_required_for_reference'])
        self.assertEqual(response['pagination']['ready_pages'],1)
        self.assertGreater(response['progress']['optional_archive'],0)
        self.assertTrue(response['official_reference']['champions'])
        self.assertEqual(current_knowledge(self.server.research),[])

    def test_selected_pick_drives_focus_and_reference_champions(self):
        draft=golden('BOTTOM',patch='16.20');draft['my_champion']='Yunara';draft['slots'][3]['champion']='Yunara'
        self.server.pregame.save(draft,None,0,'yunara-pick')
        response=queue_response(self.server,focused=True)
        self.assertEqual(response['focus']['champion'],'Yunara')
        self.assertTrue(any(any(p['field']=='my.champion' and p['value']=='Yunara' for p in c['spec']['conditions']) for c in response['candidates']))
        self.assertFalse(any(any(p['field']=='my.champion' and p['value']=='Caitlyn' for p in c['spec']['conditions']) for c in response['candidates']))
        self.assertIn('Yunara',[c['champion'] for c in response['official_reference']['champions']])

    def test_archive_and_old_catalog_stay_accessible(self):
        from coach_v1.pregame_server import candidate_specs
        self.assertEqual(len(candidate_specs()),350)
        first=queue_response(self.server);second=queue_response(self.server,page=1)
        self.assertEqual(len(first['candidates'])+len(second['candidates']),30)
        self.assertEqual(current_knowledge(self.server.research),[])


    def test_manifest_patch_mapping_cannot_mislabel_an_old_archive(self):
        import shutil
        data=json.loads(self.f.MANIFEST.read_text());data['game_patch']='16.21'
        root=Path(self.tmp.name)/'mapping';root.mkdir()
        source=next(s for s in data['sources'] if s['champion']=='Caitlyn')
        shutil.copyfile(self.f.MANIFEST.parent/source['file'],root/source['file'])
        (root/'manifest.json').write_text(json.dumps(data))
        with patch.object(self.f,'MANIFEST',root/'manifest.json'):
            response=self.f.facts_response(['Caitlyn'],patch='16.21')
        self.assertEqual(response['champions'],[])
        self.assertEqual(response['reference_status'],'UNAVAILABLE')

    def test_missing_or_malformed_manifest_does_not_block_tactical_queue(self):
        root=Path(self.tmp.name)/'bad-manifest.json'
        for contents in [None,'not json','{}']:
            if contents is not None:root.write_text(contents)
            with patch.object(self.f,'MANIFEST',root):
                response=queue_response(self.server,focused=True)
            self.assertEqual(response['official_reference']['reference_status'],'UNAVAILABLE')
            self.assertTrue(response['candidates'])
            self.assertEqual(current_knowledge(self.server.research),[])


class ReferenceFirstHTTPTests(unittest.TestCase):
    from tests_pregame.test_v20_http import QueueV20HTTPTests as _helpers
    setUp=_helpers.setUp
    cleanup=_helpers.cleanup
    call=_helpers.call

    def test_fact_route_requires_auth_and_never_creates_decisions(self):
        path='/dev/v1/pregame/official-facts'
        self.assertEqual(self.call(path,auth=False)[0],401)
        status,result=self.call(path);self.assertEqual(status,200)
        self.assertEqual(len(result['champions']),13)
        self.assertEqual(self.call('/dev/v1/pregame/knowledge')[1],[])

    def test_post_limits_champions_and_preserves_patch_mismatch(self):
        path='/dev/v1/pregame/official-facts'
        status,result=self.call(path,'POST',dict(champions=['Ashe'],patch='16.21'))
        self.assertEqual(status,200);self.assertEqual(result['champions'][0]['patch_status'],'GAME_PATCH_MISMATCH')
        for body in [dict(champions=['../Caitlyn'],patch=None),dict(champions=['Caitlyn'],patch=123),dict(champions=['Caitlyn'],patch=None,actor='USER'),dict(champions=['Caitlyn']*31,patch=None)]:
            self.assertEqual(self.call(path,'POST',body)[0],422)
        self.assertEqual(self.call('/dev/v1/pregame/knowledge')[1],[])

    def test_default_http_queue_focuses_five_and_archive_retains_thirty(self):
        prefix='/dev/v1/pregame/review-queue'
        status,focused=self.call(prefix);self.assertEqual(status,200)
        self.assertLessEqual(len(focused['candidates']),5)
        self.assertIn('operating_policy',focused)
        first=self.call(prefix+'/archive')[1]
        second=self.call(prefix+'/archive/page','POST',dict(page=1,later_page=0))[1]
        self.assertEqual(len(first['candidates'])+len(second['candidates']),30)
        self.assertEqual(self.call('/dev/v1/pregame/knowledge')[1],[])

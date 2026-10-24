import copy
import unittest
from coach_v1.gameplan_input import normalize, from_lcu, POSITIONS


class CompositionInputTests(unittest.TestCase):
    def setUp(self):
        self.heroes = ['Hero' + str(i) for i in range(10)]
        self.raw = dict(allies=[dict(champion=h, position=r) for h,r in zip(self.heroes[:5], POSITIONS)],
                        enemies=[dict(champion=h, position=r) for h,r in zip(self.heroes[5:], POSITIONS)],
                        own_champion='Hero0', own_position='TOP', side='BLUE', patch='16.20',
                        opponent_mode='ASSIGNED', lane_opponent=None)
        self.meta = dict(session_id='capture-1', observed_at=10, now=11)

    def test_manual_auto_parity_and_no_input_mutation(self):
        snap = dict(self.raw, status='CONNECTED', phase='ChampSelect', revision=3)
        snap = copy.deepcopy(snap)
        for team in ('allies','enemies'):
            for row in snap[team]: row['locked'] = True
        manual = normalize(self.raw, self.heroes, **self.meta)
        auto = from_lcu(snap, self.heroes, side='BLUE', **self.meta)
        self.assertTrue(auto['ready'])
        self.assertEqual(manual['input'], auto['input'])
        auto['input']['allies'][0]['champion'] = None
        self.assertEqual(snap['allies'][0]['champion'], 'Hero0')

    def test_unknown_roles_preserved_without_inference(self):
        self.raw['enemies'][0]['position'] = None
        self.assertIsNone(normalize(self.raw,self.heroes,**self.meta)['input']['enemies'][0]['position'])
        self.raw['own_position'] = None
        self.assertFalse(normalize(self.raw,self.heroes,**self.meta)['ready'])

    def test_stale_future_session_metadata_and_invalid_sources(self):
        for now in (9, 13):
            result=normalize(self.raw,self.heroes,**(self.meta | dict(now=now)))
            self.assertFalse(result['ready'])
        for change in (dict(observed_at=float('nan')),dict(session_id=''),dict(source='LIVE_CLIENT')):
            with self.assertRaises(ValueError): normalize(self.raw,self.heroes,**(self.meta|change))
        self.assertEqual(normalize(self.raw,self.heroes,**(self.meta|dict(session_id='capture-2')))['source']['session_id'],'capture-2')

    def test_conflicting_or_private_input_fails(self):
        for mutate in (lambda x:x.update(puuid='secret'),
                       lambda x:x['enemies'][0].update(champion='Hero0'),
                       lambda x:x['allies'][1].update(position='TOP'),
                       lambda x:x.update(own_position='BOTTOM')):
            raw=copy.deepcopy(self.raw);mutate(raw)
            with self.assertRaises(ValueError):normalize(raw,self.heroes,**self.meta)

    def test_lcu_hover_disconnect_and_unknown_side_not_ready(self):
        snap=dict(self.raw,status='CONNECTED',phase='ChampSelect',revision=1)
        result=from_lcu(snap,self.heroes,**self.meta)
        self.assertFalse(result['ready'])
        self.assertTrue(all(r['champion'] is None for r in result['input']['allies']))
        snap['phase']='InProgress'
        result=from_lcu(snap,self.heroes,**self.meta)
        self.assertEqual(result['input']['allies'],[])
        self.assertFalse(result['source']['current'])
        self.assertFalse(result['live_coaching_enabled'])


if __name__ == '__main__': unittest.main()


class PCGameplanInputHTTPTests(unittest.TestCase):
    def test_status_requires_auth_preserves_fallback_and_never_invents_freshness(self):
        import http.client
        import json
        import tempfile
        import threading
        from pathlib import Path
        from unittest.mock import patch
        from coach_v1.pregame_server import PregameWorkbench
        from coach_v1.server import Limits
        from coach_v1.pc_runtime import draft_input
        heroes=['Ornn','LeeSin','Ahri','Caitlyn','Lux','Darius','Vi','Syndra','Kaisa','Nautilus']
        snap=dict(status='CONNECTED',phase='ChampSelect',revision=2,patch=None,
                  own_champion='Caitlyn',own_position='BOTTOM',
                  allies=[dict(champion=h,position=r) for h,r in zip(heroes[:5],POSITIONS)],
                  enemies=[dict(champion=h,position=r) for h,r in zip(heroes[5:],POSITIONS)])
        snap['enemies'][0]['position']=None
        snap['input']=draft_input(snap)
        payload=dict(connection=snap,review_summary={},weekly_report={})
        token='synthetic-gameplan-token-12345678901234567890'
        with tempfile.TemporaryDirectory() as directory:
            server=PregameWorkbench(Path(directory)/'test.sqlite',token,Limits(1000000,100,100,100,100,10))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                def get(auth=True):
                    client=http.client.HTTPConnection('127.0.0.1',server.server_port)
                    client.request('GET','/dev/v1/pregame/pc-status',headers={'Authorization':'Bearer '+token} if auth else {})
                    response=client.getresponse();body=json.loads(response.read());status=response.status;client.close()
                    return status,body
                with patch('coach_v1.pc_runtime.pc_status',side_effect=lambda _:copy.deepcopy(payload)) as read:
                    self.assertEqual(get(False)[0],401)
                    read.assert_not_called()
                    status,body=get()
                    self.assertEqual(status,200)
                    self.assertEqual(body['connection'],snap)
                    normalized=body['gameplan_input']
                    self.assertIsNone(normalized['input']['enemies'][0]['position'])
                    self.assertIsNone(normalized['input']['side'])
                    self.assertIsNone(normalized['source']['session_id'])
                    self.assertIsNone(normalized['source']['observed_at'])
                    self.assertFalse(normalized['ready'])
                    self.assertIn('SOURCE_METADATA_MISSING',normalized['reasons'])
                    self.assertIn('PICK_FINALITY_UNVERIFIED',normalized['reasons'])
                    payload['connection']=dict(snap,status='MANUAL_FALLBACK',reason='LOCAL_FEED_NOT_CURRENT',input=None)
                    status,body=get()
                    self.assertEqual(body['connection']['reason'],'LOCAL_FEED_NOT_CURRENT')
                    self.assertIsNone(body['gameplan_input']['input'])
                    self.assertFalse(body['gameplan_input']['ready'])
                    payload['connection']=dict(snap,phase='InProgress')
                    self.assertIsNone(get()[1]['gameplan_input']['input'])
            finally:
                server.shutdown();thread.join();server.server_close()

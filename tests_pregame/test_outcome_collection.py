"""Ephemeral fake transport proves outcome collection needs no extra requests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from coach_v1.riot_collector import RiotCollector
from tests_pregame.test_power_stats import pair
from tests_pregame.test_riot_collector import Responses, Clock, okay


class OutcomeCollectionTests(unittest.TestCase):
    def collector(self, responses):
        self.transport=Responses(responses);clock=Clock()
        return RiotCollector('PRIVATE_TEST_KEY',transport=self.transport,
            clock=clock.now,sleeper=clock.sleep)

    def collect(self,c,**kwargs):
        return c.collect(tier='GOLD',division='I',patch='16.19',start_time=1,
            end_time=2000000000,collect_items=False,collect_outcome=True,**kwargs)

    def test_companion_uses_same_pairs_without_additional_http_or_raw_return(self):
        p=pair(0);p['match']['metadata']['matchId']='KR_100';p['timeline']['metadata']['matchId']='KR_100'
        info=p['match']['info'];info['gameEndTimestamp']=info['gameStartTimestamp']+180000
        info['teams']=[{'teamId':100,'win':True},{'teamId':200,'win':False}]
        for participant in info['participants']:participant['win']=participant['teamId']==100
        c=self.collector([okay([{'puuid':'PRIVATE_PLAYER'}]),okay(['KR_100']),okay(p['match']),okay(p['timeline'])])
        power=self.collect(c)
        self.assertEqual(len(self.transport.urls),4)
        self.assertEqual(c.outcome_status,'READY')
        self.assertEqual(c.outcome_data['samples']['real_matches'],1)
        self.assertEqual(c.outcome_data['source']['patch'],power['source']['patch'])
        self.assertEqual(c.outcome_data['samples']['hashed_match_ids'],power['samples']['hashed_match_ids'])
        self.assertNotIn('PRIVATE',json.dumps(c.outcome_data));self.assertNotIn('KR_100',json.dumps(c.outcome_data))
        self.assertNotIn('pairs',c.__dict__)

    def test_auth_failure_has_no_usable_companion(self):
        c=self.collector([(403,{},b'PRIVATE_TEST_KEY')]);power=self.collect(c)
        self.assertEqual(power['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(c.outcome_status,'BLOCKED_EXTERNAL');self.assertIsNone(c.outcome_data)

    def test_script_removes_stale_companion_on_missing_key_and_rejects_path_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            power=Path(tmp)/'power.json';outcome=Path(tmp)/'outcome.json'
            outcome.write_text('stale previous aggregate');env=dict(os.environ);env.pop('RIOT_API_KEY',None)
            base=[sys.executable,'scripts/collect_power_stats.py','--output',str(power),'--outcome-output',str(outcome)]
            result=subprocess.run(base,env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertFalse(outcome.exists())
            self.assertEqual(json.loads(power.read_text())['status'],'BLOCKED_EXTERNAL')
            self.assertEqual(json.loads(result.stdout)['outcome_status'],'BLOCKED_EXTERNAL')
            result=subprocess.run([sys.executable,'scripts/collect_power_stats.py','--output',str(power),
                '--outcome-output',str(power)],env=env,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)


if __name__=='__main__':unittest.main()

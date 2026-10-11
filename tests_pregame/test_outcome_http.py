"""Auxiliary outcome HTTP checks; synthetic fixtures are not gameplay evidence."""
import copy
import http.client
import json
from pathlib import Path
from unittest.mock import Mock,patch
import unittest
from tests_pregame import test_http


def request(**changes):
    return dict(dict(champion='Champion',position='TOP',patch='16.19',tier=None,opponent_champion='Opponent'),**changes)


def dataset():
    from coach_v1.outcome_stats import build_outcome_dataset
    from tests_pregame.test_power_stats import pair,source
    pairs=[]
    for i in range(2):
        sample=pair(i);info=sample['match']['info']
        info.update(gameDuration=1800,gameEndTimestamp=info['gameStartTimestamp']+1800000,
                    teams=[dict(teamId=100,win=True),dict(teamId=200,win=False)])
        for participant in info['participants']:
            participant['win']=participant['teamId']==100
            participant['teamPosition']={'MID':'MIDDLE','SUPPORT':'UTILITY'}.get(participant['teamPosition'],participant['teamPosition'])
        pairs.append(sample)
    return build_outcome_dataset(pairs,source=source())


class OutcomeHTTPTests(unittest.TestCase):
    setUp=test_http.HTTPTests.setUp
    cleanup=test_http.HTTPTests.cleanup
    call=test_http.HTTPTests.call
    route='/dev/v1/pregame/outcome-view'

    def test_no_source_unknown_without_zero_or_existing_api_changes(self):
        self.assertIsNone(self.server.outcome_data)
        status_before=self.call('/dev/v1/pregame/status')[1]
        power_before=self.call('/dev/v1/pregame/power-view','POST',request())[1]
        status,result=self.call(self.route,'POST',request())
        self.assertEqual(status,200);self.assertEqual(set(result),{'view','test_mode'})
        self.assertFalse(result['test_mode']);self.assertEqual(result['view']['status'],'UNKNOWN')
        self.assertEqual(result['view']['points'],[]);self.assertIsNone(result['view']['dataset_digest'])
        self.assertEqual(result['view']['schema_version'],'pregame.outcome-data.v1')
        self.assertEqual(status_before,self.call('/dev/v1/pregame/status')[1])
        self.assertEqual(power_before,self.call('/dev/v1/pregame/power-view','POST',request())[1])

    def test_auth_methods_strict_fields_and_origin(self):
        self.assertEqual(self.call(self.route,'POST',request(),auth=False)[0],401)
        self.assertEqual(self.call(self.route)[0],404)
        for body in [dict(request(),test_mode=True),dict(request(),opponent_champion=['Opponent']),
                     request(champion='x'*101),request(position='ADC'),request(patch=True),request(tier='ALL'),
                     {k:v for k,v in request().items() if k!='opponent_champion'}]:
            self.assertEqual(self.call(self.route,'POST',body)[0],422)
        con=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        con.request('POST',self.route,json.dumps(request()),{'Authorization':'Bearer '+self.token,
            'Content-Type':'application/json','Origin':'https://foreign.example'})
        result=con.getresponse();result.read();con.close();self.assertEqual(result.status,403)

    def test_independent_synthetic_gating_digest_fallback_and_missing_cohorts(self):
        from coach_v1.state import digest
        aggregate=dataset();self.server.outcome_data=aggregate
        self.assertIsNone(self.server.power_data)
        self.assertEqual(self.call(self.route,'POST',request())[1]['view']['status'],'UNKNOWN')
        self.server.test_mode=True
        status_before=self.call('/dev/v1/pregame/status')[1]
        result=self.call(self.route,'POST',request())[1]
        self.assertEqual(result['view']['status'],'KNOWN');self.assertTrue(result['test_mode'])
        self.assertEqual(result['view']['dataset_digest'],digest(aggregate))
        self.assertEqual(result['view']['source']['tier'],'GOLD')
        self.assertEqual([(p['minute'],p['n'],p['wins']) for p in result['view']['points']],[(30,2,2)])
        self.assertEqual(result['view']['points'][0]['comparison'],'MATCHUP')
        fallback=self.call(self.route,'POST',request(opponent_champion='UnseenOpponent'))[1]['view']
        self.assertEqual(fallback['status'],'KNOWN');self.assertEqual(fallback['points'][0]['comparison'],'CHAMPION_ROLE')
        for change in [dict(patch=None),dict(patch='16.18'),dict(tier='PLATINUM'),dict(champion='UnseenChampion'),dict(position='JUNGLE')]:
            view=self.call(self.route,'POST',request(**change))[1]['view']
            self.assertEqual(view['status'],'UNKNOWN');self.assertEqual(view['points'],[])
        self.assertEqual(status_before,self.call('/dev/v1/pregame/status')[1])
        self.assertEqual(self.call('/dev/v1/pregame/power-view','POST',request())[1]['view']['status'],'UNKNOWN')
        for raw in ['PRIVATE_SYNTHETIC','participantId','puuid','KR_SYNTHETIC']:self.assertNotIn(raw,json.dumps(result))

    def test_outcome_changes_do_not_expire_saved_plan_or_expose_raw_data(self):
        from tests_pregame.test_contract import golden
        record=self.call('/dev/v1/pregame/inputs','POST',dict(input=golden()),'outcome-input')[1]
        path='/dev/v1/pregame/inputs/'+record['session_id']+'/plans'
        plan=self.call(path,'POST',dict(expected_revision=1),'outcome-plan')[1]
        self.server.test_mode=True;self.server.outcome_data=dataset()
        self.assertEqual(self.call('/dev/v1/pregame/plans/'+plan['id'])[1],plan)
        changed=copy.deepcopy(self.server.outcome_data);changed['source']['retrieved_at']='2026-10-11T01:00:00Z'
        self.server.outcome_data=changed
        self.assertEqual(self.call('/dev/v1/pregame/plans/'+plan['id'])[1],plan)
        self.assertEqual(self.call('/dev/v1/pregame/outcome-data')[0],404)

    def test_cli_rejects_synthetic_or_raw_data_with_cleanup(self):
        from coach_v1.pregame_server import main
        token_path=Path(self.tmp.name)/'outcome-cli-token';token_path.write_text(self.token)
        data_path=Path(self.tmp.name)/'outcome-cli-data.json'
        for payload in [dataset(),dict(raw=dict(puuid='PRIVATE_FIXTURE'))]:
            data_path.write_text(json.dumps(payload));fake=Mock()
            args=['pregame','--db',self.tmp.name+'/outcome-cli.sqlite','--token-file',str(token_path),'--outcome-data',str(data_path)]
            for flag in ['body-bytes','observations','actions','scenarios','comparisons','pending-jobs']:args.extend(['--max-'+flag,'1000000'])
            with patch('sys.argv',args),patch('coach_v1.pregame_server.PregameWorkbench',return_value=fake):
                with self.assertRaises(ValueError):main()
            fake.server_close.assert_called_once();fake.serve_forever.assert_not_called()

    def test_outcome_response_uses_existing_size_guard(self):
        oversized=dict(view=dict(status='UNKNOWN',reasons=['x'*1000001]),test_mode=False)
        with patch('coach_v1.pregame_server.outcome_response',return_value=oversized):
            status,result=self.call(self.route,'POST',request())
        self.assertEqual(status,413);self.assertEqual(result['error_code'],'PREGAME_TOO_LARGE')

    def test_cli_accepts_valid_real_empty_aggregate_independently(self):
        from coach_v1.pregame_server import main
        from coach_v1.outcome_stats import build_outcome_dataset
        from tests_pregame.test_power_stats import source
        aggregate=build_outcome_dataset([],source=source('REAL'))
        self.assertEqual(aggregate['samples']['real_matches'],0)
        token_path=Path(self.tmp.name)/'real-empty-token';token_path.write_text(self.token)
        data_path=Path(self.tmp.name)/'real-empty-outcome.json';data_path.write_text(json.dumps(aggregate))
        fake=Mock();fake.server_port=8765
        args=['pregame','--db',self.tmp.name+'/real-empty-cli.sqlite','--token-file',str(token_path),'--outcome-data',str(data_path)]
        for flag in ['body-bytes','observations','actions','scenarios','comparisons','pending-jobs']:args.extend(['--max-'+flag,'1000000'])
        with patch('sys.argv',args),patch('coach_v1.pregame_server.PregameWorkbench',return_value=fake),patch('builtins.print'):
            main()
        self.assertEqual(fake.outcome_data,aggregate)
        self.assertNotIn('power_data',fake.__dict__)
        fake.serve_forever.assert_called_once();fake.server_close.assert_called_once()


if __name__=='__main__':unittest.main()

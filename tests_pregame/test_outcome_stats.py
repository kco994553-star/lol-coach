"""Synthetic ending-result tests; no acquired Riot samples or identities."""
import copy
import importlib
import importlib.util
import json
import unittest

from tests_pregame.test_power_stats import pair as power_pair, source


def pair(number=0, duration=120, win=True, opponent='Opponent', patch='16.19'):
    p=power_pair(number,opponent=opponent,patch=patch)
    info=p['match']['info']
    info.update(gameDuration=duration,gameEndTimestamp=100000+duration*1000,
                teams=[dict(teamId=100,win=win),dict(teamId=200,win=not win)])
    for person in info['participants']:
        person['win']=win if person['teamId']==100 else not win
        person['teamPosition']={'MID':'MIDDLE','SUPPORT':'UTILITY'}.get(person['teamPosition'],person['teamPosition'])
    return p


class OutcomeStatsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.outcome_stats'),'Q15 outcome module missing')
        self.outcome=importlib.import_module('coach_v1.outcome_stats')

    def dataset(self,pairs):
        return self.outcome.build_outcome_dataset(pairs,source=source())

    def cohort(self,d,comparison='CHAMPION_ROLE'):
        return next(c for c in d['cohorts'] if c['champion']=='Champion' and c['comparison']==comparison)

    def test_independent_wilson_values_and_one_trial_uncertainty(self):
        examples=[([False],0,.7934506856227626),([True],.20654931437723745,1),
                  ([True]*5+[False]*5,.236593090512564,.763406909487436)]
        for outcomes,low,high in examples:
            point=self.cohort(self.dataset([pair(i,win=w) for i,w in enumerate(outcomes)]))['points'][0]
            self.assertEqual(point['wins'],sum(outcomes));self.assertEqual(point['n'],len(outcomes))
            self.assertEqual(point['win_rate'],sum(outcomes)/len(outcomes))
            self.assertAlmostEqual(point['ci95']['low'],low,places=12)
            self.assertAlmostEqual(point['ci95']['high'],high,places=12)

    def test_dedup_public_hashes_and_all_five_canonical_roles(self):
        p=pair();d=self.dataset([p,copy.deepcopy(p),pair(1,win=False)])
        self.assertEqual(d['samples']['synthetic_matches'],2)
        self.assertEqual(d['samples']['real_matches'],0)
        self.assertEqual({c['position'] for c in d['cohorts']},{'TOP','JUNGLE','MID','BOTTOM','SUPPORT'})
        point=self.cohort(d)['points'][0]
        self.assertEqual((point['n'],point['wins']),(2,1))
        self.assertEqual(set(point['input_match_hashes']),set(d['samples']['hashed_match_ids']))
        self.assertIsNone(d['coaching_accuracy'])
        for secret in ('PRIVATE_SYNTHETIC','KR_SYNTHETIC','puuid','participantId','gameEndTimestamp'):
            self.assertNotIn(secret,json.dumps(d))
        self.assertEqual(self.outcome.validate_outcome_dataset(d),d)

    def test_reported_seconds_boundary_and_delayed_end_timestamp(self):
        inputs=[pair(0,119),pair(1,120),pair(2,179)]
        inputs[0]['match']['info']['gameEndTimestamp']=9000000000
        points=self.cohort(self.dataset(inputs))['points']
        self.assertEqual([(p['minute'],p['n']) for p in points],[(1,1),(2,2)])

    def test_missing_conflicting_and_non_boolean_results_never_become_losses(self):
        mutations=[lambda i:i['participants'][0].pop('win'),
                   lambda i:i['participants'][0].update(win='false'),
                   lambda i:i['participants'][0].update(win=1),
                   lambda i:i['participants'][0].update(win=False),
                   lambda i:i['teams'][1].update(win=True),
                   lambda i:i.pop('teams')]
        for mutation in mutations:
            p=pair();mutation(p['match']['info']);d=self.dataset([p])
            self.assertEqual(d['status'],'INSUFFICIENT_DATA');self.assertEqual(d['cohorts'],[])
            self.assertEqual(d['samples']['synthetic_matches'],0)

    def test_duration_units_and_unknown_duration_withheld(self):
        for field,value in [('gameDuration',None),('gameDuration',0),('gameDuration',True),
                            ('gameDuration',120.5),('gameEndTimestamp',None),
                            ('gameEndTimestamp',True),('gameEndTimestamp',99999),
                            ('gameEndTimestamp',120000.5),('gameStartTimestamp',True)]:
            p=pair();p['match']['info'][field]=value
            self.assertEqual(self.dataset([p])['cohorts'],[],(field,value))
        old=source();old['patch']='11.19'
        try:old_dataset=self.outcome.build_outcome_dataset([pair(patch='11.19')],source=old)
        except ValueError:self.fail('known older patch must withhold trials instead of rejecting empty numeric source lineage')
        self.assertEqual(old_dataset['cohorts'],[])
        s=source();s['patch']='11.20'
        d=self.outcome.build_outcome_dataset([pair(patch='11.20')],source=s)
        self.assertEqual(d['status'],'READY')

    def test_mirror_champion_role_excluded_without_discarding_other_roles(self):
        d=self.dataset([pair(opponent='Champion')])
        self.assertFalse(any(c['champion']=='Champion' for c in d['cohorts']))
        self.assertEqual({c['position'] for c in d['cohorts']},{'JUNGLE','MID','BOTTOM','SUPPORT'})
        self.assertEqual(d['samples']['synthetic_matches'],1)

    def test_eligibility_patch_window_metadata_and_roles(self):
        mutations=[lambda p:p['match']['info'].update(queueId=440),
                   lambda p:p['match']['info'].update(mapId=12),
                   lambda p:p['match']['info'].update(gameMode='ARAM'),
                   lambda p:p['match']['info'].update(gameVersion='16.18.1'),
                   lambda p:p['match']['info'].update(gameStartTimestamp=0),
                   lambda p:p['timeline'].update(metadata={'matchId':'KR_MISMATCH'}),
                   lambda p:p['match']['info']['participants'][0].update(teamPosition='UNKNOWN'),
                   lambda p:p['match']['info']['participants'][0].update(championName='bad/name')]
        for mutation in mutations:
            p=pair();mutation(p);self.assertEqual(self.dataset([p])['cohorts'],[])

    def test_timeline_frames_are_not_result_quality_gate_and_inputs_unmodified(self):
        p=pair();p['timeline']['info']={'frames':[],'frameInterval':23000}
        before=copy.deepcopy(p);d=self.dataset([p]);self.assertEqual(d['status'],'READY')
        self.assertEqual(p,before)

    def test_per_bin_matchup_then_all_opponents_and_no_missing_bin_synthesis(self):
        d=self.dataset([pair(0,120,opponent='Opponent'),pair(1,180,opponent='Other')])
        view=self.outcome.select_outcome_view(d,'Champion','TOP','16.19','GOLD','Opponent')
        self.assertEqual(view['status'],'KNOWN')
        self.assertEqual([(p['minute'],p['comparison'],p['opponent_champion']) for p in view['points']],
                         [(2,'MATCHUP','Opponent'),(3,'CHAMPION_ROLE',None)])
        for champion,role,patch,tier in [('Missing','TOP','16.19','GOLD'),('Champion','MID','16.19','GOLD'),
                                        ('Champion','TOP','16.18','GOLD'),('Champion','TOP','16.19','SILVER')]:
            self.assertEqual(self.outcome.select_outcome_view(d,champion,role,patch,tier)['status'],'UNKNOWN')
        self.assertEqual(self.outcome.select_outcome_view(d,'Champion','TOP',None,None)['status'],'UNKNOWN')

    def test_read_safe_validator_rejects_bad_counts_hashes_ratios_intervals_and_leaks(self):
        d=self.dataset([pair(0),pair(1,win=False)])
        mutations=[lambda x:x.update(raw_match={'puuid':'secret'}),
                   lambda x:x['source'].update(api_key='secret'),
                   lambda x:x['source'].update(provider='RIOT_API'),
                   lambda x:x['cohorts'][0].update(tier='SILVER'),
                   lambda x:x['cohorts'][0]['points'][0].update(n=3),
                   lambda x:x['cohorts'][0]['points'][0].update(wins=True),
                   lambda x:x['cohorts'][0]['points'][0].update(win_rate=.9),
                   lambda x:x['cohorts'][0]['points'][0]['ci95'].update(low=float('nan')),
                   lambda x:x['cohorts'][0]['points'][0]['ci95'].update(high=1),
                   lambda x:x['cohorts'][0]['points'][0].update(input_match_hashes=['0'*64,'1'*64]),
                   lambda x:x['samples'].update(real_matches=1),
                   lambda x:x['cohorts'].append(copy.deepcopy(x['cohorts'][0])),
                   lambda x:x['source']['limitations'].append('RAW_PRIVATE_PLAYER'),
                   lambda x:x.update(status='BLOCKED_EXTERNAL')]
        for mutation in mutations:
            bad=copy.deepcopy(d);mutation(bad)
            with self.assertRaises(ValueError):self.outcome.validate_outcome_dataset(bad)
        v=self.outcome.validate_outcome_dataset(d);v['source']['endpoints'].clear()
        self.assertNotEqual(v,d)

    def test_repeated_hash_in_two_bins_and_null_patch_with_samples_rejected(self):
        d=self.dataset([pair()]);p=copy.deepcopy(d['cohorts'][0]['points'][0]);p['minute']+=1
        d['cohorts'][0]['points'].append(p)
        with self.assertRaises(ValueError):self.outcome.validate_outcome_dataset(d)
        d=self.dataset([pair()]);d['source']['patch']=None
        with self.assertRaises(ValueError):self.outcome.validate_outcome_dataset(d)

    def test_nonempty_old_patch_or_missing_official_pair_endpoints_rejected(self):
        for mutate in (lambda d:d['source'].update(patch='11.19'),
                       lambda d:d['source'].update(endpoints=[]),
                       lambda d:d['source'].update(endpoints=['MATCH_V5_MATCH']),
                       lambda d:d['source'].update(endpoints=['MATCH_V5_TIMELINE'])):
            d=self.dataset([pair()]);mutate(d)
            if d['source']['patch']=='11.19':
                for c in d['cohorts']:c['patch']='11.19'
            with self.assertRaises(ValueError):self.outcome.validate_outcome_dataset(d)
        empty=self.dataset([]);empty['source']['endpoints']=[]
        self.outcome.validate_outcome_dataset(empty)

    def test_real_vs_synthetic_lineage_and_empty_blocked_views(self):
        s=source('REAL');p=pair();p['match']['metadata']['matchId']='KR_123456'
        p['timeline']['metadata']=copy.deepcopy(p['match']['metadata'])
        d=self.outcome.build_outcome_dataset([p],source=s)
        self.assertEqual((d['samples']['real_matches'],d['samples']['synthetic_matches']),(1,0))
        self.assertEqual(self.outcome.build_outcome_dataset([pair()],source=s)['cohorts'],[])
        empty=self.dataset([]);empty['status']='BLOCKED_EXTERNAL'
        view=self.outcome.select_outcome_view(empty,'Champion','TOP','16.19','GOLD')
        self.assertEqual((view['status'],view['points']),('UNKNOWN',[]))

    def test_matchup_wins_must_reconstruct_all_opponent_total(self):
        d=self.dataset([pair(0),pair(1,win=False)])
        point=self.cohort(d,'MATCHUP')['points'][0]
        point.update(wins=2,win_rate=1.,ci95={'low':.342380227506653,'high':1.})
        with self.assertRaises(ValueError):self.outcome.validate_outcome_dataset(d)

    def test_reverse_matchup_must_have_complementary_results(self):
        d=self.dataset([pair(0),pair(1,win=False)])
        for c in d['cohorts']:
            if c['champion']=='Champion':
                c['points'][0].update(wins=2,win_rate=1.,ci95={'low':.342380227506653,'high':1.})
        with self.assertRaises(ValueError):self.outcome.validate_outcome_dataset(d)

    def test_one_match_has_one_ending_minute_across_all_roles_and_comparisons(self):
        d=self.dataset([pair()])
        for c in d['cohorts']:
            if c['position']=='TOP':c['points'][0]['minute']=3
        with self.assertRaises(ValueError):self.outcome.validate_outcome_dataset(d)

    def test_complete_partition_missing_duplicate_or_reassigned_cohorts_rejected(self):
        d=self.dataset([pair(0,opponent='Opponent'),pair(1,opponent='Other')])
        mutations=[lambda x:x['cohorts'].remove(self.cohort(x)),
                   lambda x:x['cohorts'].remove(self.cohort(x,'MATCHUP')),
                   lambda x:x['cohorts'].remove(next(c for c in x['cohorts'] if c['champion']=='Opponent' and c['comparison']=='MATCHUP')),
                   lambda x:self.cohort(x,'MATCHUP')['points'][0].update(input_match_hashes=[next(iter(
                       set(self.cohort(x)['points'][0]['input_match_hashes'])-
                       set(self.cohort(x,'MATCHUP')['points'][0]['input_match_hashes'])))]),
                   lambda x:self.cohort(x,'MATCHUP')['points'][0].update(minute=3)]
        for mutation in mutations:
            bad=copy.deepcopy(d);mutation(bad)
            with self.assertRaises(ValueError):self.outcome.validate_outcome_dataset(bad)


if __name__=='__main__':unittest.main()

"""Independent synthetic checks, never real gameplay receipts."""
import copy
import importlib
import importlib.util
import json
import math
import unittest

POSITIONS = ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT')


def source(kind='SYNTHETIC'):
    return dict(provider='SYNTHETIC' if kind == 'SYNTHETIC' else 'RIOT_API',
                platform='KR', regional='ASIA', queue_id=420, map_id=11,
                tier='GOLD', patch='16.19', window_start=1, window_end=2000000000,
                retrieved_at='2026-10-11T00:00:00+00:00', sample_kind=kind,
                endpoints=['LEAGUE_V4_ENTRIES', 'MATCH_V5_IDS', 'MATCH_V5_MATCH', 'MATCH_V5_TIMELINE'])


def pair(number=0, delta=100, opponent='Opponent', patch='16.19', minutes=(1, 2, 3)):
    participants=[]
    for team, offset in ((100, 0), (200, 5)):
        for i, position in enumerate(POSITIONS, 1):
            participants.append(dict(participantId=offset+i, teamId=team,
                teamPosition=position, championName=('Champion' if i == 1 else 'Champion'+str(i))
                if team == 100 else (opponent if i == 1 else 'Opponent'+str(i)),
                puuid='PRIVATE_SYNTHETIC_PUUID', summonerName='PRIVATE_SYNTHETIC_NAME'))
    frames=[]
    for minute in minutes:
        pf={}
        for p in participants:
            advantage=delta if p['teamId'] == 100 else 0
            pf[str(p['participantId'])]=dict(totalGold=500+minute*100+advantage,
                xp=minute*200+advantage, minionsKilled=minute*5+(advantage/10),
                jungleMinionsKilled=0, level={1:2,2:3,3:6,4:11,5:16}.get(minute,16))
        events=[]
        if minute == 2:
            events=[dict(type='ITEM_PURCHASED',participantId=1,itemId=1001,timestamp=90000),
                    dict(type='ITEM_PURCHASED',participantId=1,itemId=3001,timestamp=100000)]
        if minute == 3:
            events=[dict(type='ITEM_PURCHASED',participantId=1,itemId=3002,timestamp=150000)]
        frames.append(dict(timestamp=minute*60000,participantFrames=pf,events=events))
    metadata=dict(matchId='KR_SYNTHETIC_'+str(number),participants=['PRIVATE_SYNTHETIC_PUUID'])
    return dict(match=dict(metadata=metadata,info=dict(queueId=420,mapId=11,
        gameMode='CLASSIC',gameVersion=patch+'.1',gameStartTimestamp=100000,
        gameDuration=max(minutes)*60,participants=participants)),
        timeline=dict(metadata=metadata,info=dict(frames=frames,frameInterval=60000)))


class PowerStatsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.power_stats'), 'Q15 module missing')
        self.power=importlib.import_module('coach_v1.power_stats')

    def cohort(self, dataset, metric='gold_delta', comparison='MATCHUP'):
        return next(c for c in dataset['cohorts'] if c['champion']=='Champion'
                    and c['metric']==metric and c['comparison']==comparison)

    def test_student_t_against_independent_nist_values_and_ci_example(self):
        for df, expected in [(1,12.706),(2,4.303),(17,2.110),(100,1.984),(194,1.9723)]:
            self.assertAlmostEqual(self.power.student_t_critical(df),expected,delta=.0006)
        mean=9.261460;sd=.022789;n=195
        margin=self.power.student_t_critical(n-1)*sd/math.sqrt(n)
        self.assertAlmostEqual(mean-margin,9.258242,delta=.000001)
        self.assertAlmostEqual(mean+margin,9.264679,delta=.000001)

    def test_signed_deltas_all_roles_and_no_identifier_persistence(self):
        d=self.power.build_power_dataset([pair(0),pair(1)],source=source())
        self.assertEqual(d['samples']['real_matches'],0)
        self.assertEqual(d['samples']['synthetic_matches'],2)
        self.assertEqual({c['position'] for c in d['cohorts']},set(POSITIONS))
        self.assertEqual(self.cohort(d)['points'][0]['mean'],100)
        self.assertEqual(self.cohort(d,'xp_delta')['points'][0]['mean'],100)
        self.assertEqual(self.cohort(d,'cs_delta')['points'][0]['mean'],10)
        opposite=next(c for c in d['cohorts'] if c['champion']=='Opponent' and c['metric']=='gold_delta')
        self.assertEqual(opposite['points'][0]['mean'],-100)
        serialized=json.dumps(d)
        for forbidden in ('PRIVATE_SYNTHETIC','KR_SYNTHETIC','puuid','summonerName','participantId'):
            self.assertNotIn(forbidden,serialized)
        self.assertTrue(all(len(h)==64 for h in d['samples']['hashed_match_ids']))
        self.assertIsNone(d['coaching_accuracy'])
        self.power.validate_power_dataset(d)

    def test_adaptive_precision_variable_spread_and_constant_sample(self):
        d=self.power.build_power_dataset([pair(i,i*100) for i in range(4)],source=source())
        p=self.cohort(d)['points'][0]
        self.assertFalse(p['visible']);self.assertEqual(p['omission_reason'],'CI_TOO_WIDE')
        d=self.power.build_power_dataset([pair(i,i*100) for i in range(20)],source=source())
        p=self.cohort(d)['points'][0]
        self.assertTrue(p['visible']);self.assertLess(p['ci95']['high']-p['ci95']['low'],600)
        d=self.power.build_power_dataset([pair(0),pair(1)],source=source())
        self.assertTrue(self.cohort(d)['points'][0]['visible'])
        self.assertIn('CONSTANT_SAMPLES_DO_NOT_PROVE_POPULATION_CERTAINTY',d['source']['limitations'])

    def test_override_has_lineage_and_invalid_width_rejected(self):
        d=self.power.build_power_dataset([pair(0,0),pair(1,100)],source=source(),ci_width_limits={'gold_delta':2000})
        self.assertTrue(self.cohort(d)['points'][0]['visible'])
        self.assertEqual(d['source']['precision_policy']['ci_width_limits'],{'gold_delta':2000})
        for bad in ({'gold_delta':-1},{'invented':2},{'gold_delta':float('nan')}):
            with self.assertRaises(ValueError):self.power.build_power_dataset([],source=source(),ci_width_limits=bad)

    def test_dedup_pair_binding_patch_mode_and_missing_frames(self):
        a=pair();wrong=pair(4);wrong['timeline']['metadata']['matchId']='OTHER'
        pve=pair(5);pve['match']['info']['queueId']=400
        wrongmode=pair(6);wrongmode['match']['info']['gameMode']='ARAM'
        wrongmap=pair(7);wrongmap['match']['info']['mapId']=12
        d=self.power.build_power_dataset([a,a,wrong,pve,wrongmode,wrongmap,pair(8,patch='16.18'),pair(9,minutes=(1,3))],source=source())
        self.assertEqual(d['samples']['synthetic_matches'],2)
        self.assertEqual([p['n'] for p in self.cohort(d)['points']],[2,1,2])
        self.assertFalse(self.cohort(d)['points'][1]['visible'])
        sparse=pair(10);del sparse['timeline']['info']['frames'][0]['participantFrames']['1']['xp']
        d=self.power.build_power_dataset([sparse],source=source())
        self.assertNotIn(1,[p['minute'] for p in self.cohort(d,'xp_delta')['points']])

    def test_perminute_matchup_fallback_preserves_gaps_and_unknown(self):
        pairs=[pair(i,100,opponent='Other',minutes=(1,3)) for i in range(20)]
        pairs.extend([pair(100,100,opponent='Opponent',minutes=(1,2)),pair(101,100,opponent='Opponent',minutes=(1,))])
        d=self.power.build_power_dataset(pairs,source=source())
        view=self.power.select_power_view(d,'Champion','TOP','16.19','GOLD','Opponent')
        gold=[p for p in view['points'] if p['metric']=='gold_delta']
        self.assertEqual([(p['minute'],p['comparison']) for p in gold],[(1,'MATCHUP'),(3,'ROLE_POPULATION')])
        self.assertEqual(view['status'],'KNOWN')
        self.assertIn('INSUFFICIENT_AT_MINUTE:2:gold_delta',view['reasons'])
        self.assertEqual(self.power.select_power_view(d,'Champion','TOP','16.18','GOLD')['status'],'UNKNOWN')

    def test_level_item_median_iqr_modes_undo_and_no_catalog(self):
        d=self.power.build_power_dataset([pair(0,minutes=(1,2,3,4,5)),pair(1,minutes=(1,2,3,4,5))],source=source(),complete_item_ids=(3001,3002))
        marks=self.cohort(d)['markers']
        self.assertEqual({m['level'] for m in marks if m['kind']=='LEVEL'},{2,3,6,11,16})
        items=[m for m in marks if m['kind']=='ITEM']
        self.assertEqual([(m['item_order'],m['item_id'],m['n']) for m in items],[(1,3001,2),(2,3002,2)])
        self.assertAlmostEqual(items[0]['median_minute'],100/60)
        undone=pair(3);undone['timeline']['info']['frames'][1]['events'].append(dict(type='ITEM_UNDO',participantId=1,beforeId=3001,afterId=0,timestamp=110000))
        d=self.power.build_power_dataset([undone],source=source(),complete_item_ids=(3001,3002))
        self.assertEqual([m['item_id'] for m in self.cohort(d)['markers'] if m['kind']=='ITEM'],[3002])
        d=self.power.build_power_dataset([pair()],source=source())
        self.assertFalse(any(m['kind']=='ITEM' for m in self.cohort(d)['markers']))

    def test_validator_rejects_injected_raw_identifiers_and_fabricated_counts(self):
        d=self.power.build_power_dataset([pair(),pair(1)],source=source())
        mutations=[lambda x:x.update(raw={'puuid':'private'}),lambda x:x['source'].update(puuid='private'),
            lambda x:x['samples']['hashed_match_ids'].append('KR_RAW'),
            lambda x:x['samples'].update(real_matches=2),lambda x:x.update(coaching_accuracy=.95),
            lambda x:x['cohorts'][0].update(participantId=1),
            lambda x:x['cohorts'][0]['points'][0].update(mean=float('inf')),
            lambda x:x['cohorts'][0]['points'][0].update(n=200),
            lambda x:x['samples']['hashed_match_ids'].append({}),
            lambda x:x['source'].update(collection={'key_kind':'PRIVATE_KEY'}),
            lambda x:x['cohorts'][0]['points'][0].update(ci95={'low':0,'high':200})]
        for mutation in mutations:
            bad=copy.deepcopy(d);mutation(bad)
            with self.assertRaises(ValueError):self.power.validate_power_dataset(bad)

    def test_missing_source_metadata_or_malformed_pair_rejected_safely(self):
        with self.assertRaises(ValueError):self.power.build_power_dataset([],source={'sample_kind':'REAL'})
        malformed=pair();malformed['match']['info']=[]
        result=self.power.build_power_dataset([malformed],source=source())
        self.assertEqual(result['samples']['synthetic_matches'],0)

    def test_role_population_is_pooled_rate_reference_and_mirror_cluster(self):
        d=self.power.build_power_dataset([pair(0,150),pair(1,150)],source=source())
        points=self.cohort(d,comparison='ROLE_POPULATION')['points']
        self.assertEqual([p['mean'] for p in points],[75,37.5,25])
        self.assertEqual([p['reference_n'] for p in points],[4,4,4])
        self.assertEqual(self.cohort(d,'cs_delta','ROLE_POPULATION')['points'][0]['mean'],7.5)
        self.assertEqual(d['source']['population_reference']['kind'],'POOLED_SAME_POSITION_RATE_MEAN_CLUSTERED')
        self.assertEqual(d['source']['population_reference']['position_participant_count'],4)
        mirrored=[pair(0,100,opponent='Champion'),pair(1,200,opponent='Champion')]
        d=self.power.build_power_dataset(mirrored,source=source())
        points=self.cohort(d,comparison='ROLE_POPULATION')['points']
        self.assertEqual(points[0]['n'],2);self.assertEqual(points[0]['mean'],0)
        self.assertEqual(points[0]['champion_n'],4)

    def test_other_champions_change_pooled_reference_independent_cluster_example(self):
        third=pair(2,1000);third['match']['info']['participants'][0]['championName']='Different'
        pairs=[pair(0,100),pair(1,300),third]
        d=self.power.build_power_dataset(pairs+[third],source=source())
        p=self.cohort(d,comparison='ROLE_POPULATION')['points'][0]
        self.assertEqual(p['n'],3);self.assertEqual(p['champion_n'],2);self.assertEqual(p['reference_n'],6)
        self.assertEqual(p['champion_mean'],800)
        self.assertAlmostEqual(p['reference_mean'],2500/3)
        self.assertAlmostEqual(p['mean'],-100/3)
        contributions=[400,600,-1100]
        import statistics
        # Closed-form df=2 quantile, independent of the production beta/CDF.
        critical=math.sqrt(2*.95**2/(1-.95**2))
        margin=critical*statistics.stdev(contributions)/math.sqrt(3)
        self.assertAlmostEqual(p['ci95']['low'],-100/3-margin,places=8)
        self.assertAlmostEqual(p['ci95']['high'],-100/3+margin,places=8)
        self.assertFalse(p['visible'])
        sparse=self.power.build_power_dataset([pair(0,100)]+[dict(third,match=dict(third['match'],
            metadata=dict(third['match']['metadata'],matchId='KR_SYNTHETIC_'+str(i))),
            timeline=dict(third['timeline'],metadata=dict(third['timeline']['metadata'],matchId='KR_SYNTHETIC_'+str(i))))
            for i in range(1,22)],source=source())
        p=self.cohort(sparse,comparison='ROLE_POPULATION')['points'][0]
        self.assertEqual(p['champion_n'],1);self.assertFalse(p['visible'])
        self.assertEqual(p['omission_reason'],'CHAMPION_N_LT_2')

    def test_frame_jitter_same_bin_latest_only_and_irregular_interval(self):
        pairs=[]
        for number,timestamp in enumerate((300000,300153,300321)):
            p=pair(number,minutes=(5,));p['match']['info']['gameDuration']=360
            p['timeline']['info']['frames'][0]['timestamp']=timestamp;pairs.append(p)
        d=self.power.build_power_dataset(pairs,source=source())
        point=self.cohort(d)['points'][0]
        self.assertEqual(point['minute'],5);self.assertEqual(point['n'],3)
        self.assertTrue(point['visible'])
        self.assertEqual(d['source']['time_bin_policy'],dict(kind='ELAPSED_MINUTE_FLOOR',
            frame_interval_ms=60000,selection='LATEST_RECEIVED_FRAME_PER_MATCH_BIN'))
        latest=copy.deepcopy(pairs[0]['timeline']['info']['frames'][0]);latest['timestamp']=300900
        latest['participantFrames']['1']['totalGold']=5000
        pairs[0]['timeline']['info']['frames'].append(latest)
        d=self.power.build_power_dataset([pairs[0]],source=source())
        self.assertEqual(self.cohort(d)['points'][0]['mean'],4000)
        self.assertEqual(self.cohort(d)['points'][0]['n'],1)
        pairs[0]['timeline']['info']['frameInterval']=30000
        d=self.power.build_power_dataset([pairs[0]],source=source())
        self.assertEqual(d['samples']['synthetic_matches'],0)
        self.assertEqual(d['status'],'INSUFFICIENT_DATA')
        self.assertIn('UNSUPPORTED_FRAME_INTERVAL',d['source']['limitations'])

    def test_item_markers_use_actual_joint_mode_never_unobserved_combination(self):
        pairs=[]
        for number,(first,second) in enumerate([(3001,3002)]*3+[(3003,3004)]*2+[(3003,3005)]*2):
            p=pair(number)
            p['timeline']['info']['frames'][1]['events'][1]['itemId']=first
            p['timeline']['info']['frames'][2]['events'][0]['itemId']=second
            pairs.append(p)
        d=self.power.build_power_dataset(pairs,source=source(),complete_item_ids=(3001,3002,3003,3004,3005))
        marks=[m for m in self.cohort(d)['markers'] if m['kind']=='ITEM']
        self.assertEqual([(m['item_id'],m['n']) for m in marks],[(3001,3),(3002,3)])

    def test_after_reported_end_drops_tail_preserving_earlier_observations(self):
        p=pair(0,minutes=(1,5));p['timeline']['info']['frames'][-1]['timestamp']=300153
        d=self.power.build_power_dataset([p],source=source())
        self.assertEqual(d['samples']['synthetic_matches'],1)
        self.assertEqual([point['minute'] for point in self.cohort(d)['points']],[1])
        self.assertIn('FRAME_AFTER_REPORTED_END_EXCLUDED_DURATION_RESOLUTION_UNKNOWN',d['source']['limitations'])


if __name__ == '__main__':unittest.main()

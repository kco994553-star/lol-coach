"""Isolated fabricated envelopes; REAL labels exercise validation, not real evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from coach_v1.postgame_match import PostgameStore


def envelope(selected=1):
    roles=['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY']
    champions=['Ornn','Sejuani','Ahri','Caitlyn','Lux','Gnar','Vi','Syndra','Ashe','Nami']
    people=[dict(participantId=i,puuid='PRIVATE_ACCOUNT_'+str(i),championName=champions[i-1],
                 teamPosition=roles[(i-1)%5],teamId=100 if i<=5 else 200) for i in range(1,11)]
    frames=[]
    for t in (0,60000,120000,180000,600000,900000):
        frames.append(dict(timestamp=t,events=[],participantFrames={str(i):dict(
            participantId=i,level=min(18,1+t//60000),totalGold=500+t//100+i,
            position=dict(x=5000,y=5000),championStats=dict(health=500,healthMax=1000)) for i in range(1,11)}))
    metadata=dict(matchId='KR_123456789',participants=[p['puuid'] for p in people])
    return dict(source='REAL',participant_id=selected,
        match=dict(metadata=copy.deepcopy(metadata),info=dict(gameVersion='16.19.1',gameDuration=960,
            mapId=11,queueId=420,gameMode='CLASSIC',participants=people)),
        timeline=dict(metadata=copy.deepcopy(metadata),info=dict(frameInterval=60000,
            participants=[dict(participantId=p['participantId'],puuid=p['puuid']) for p in people],frames=frames)))


def level(pid,lev,t):return dict(type='LEVEL_UP',participantId=pid,level=lev,timestamp=t)


class PilotObservationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.pilot_observations'),'offline observation module absent')
        from coach_v1.pilot_observations import audit_private_cache,validate_report
        self.audit=audit_private_cache;self.validate=validate_report
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.store=PostgameStore(self.root/'private'/'matches')

    def report(self,b=None):
        self.store.import_match(b or envelope())
        return self.audit(self.root)

    def test_level_up_exact_dedup_and_skill_level_up_never_champion_level(self):
        b=envelope();events=b['timeline']['info']['frames'][2]['events']
        for pid in ('1','6'):b['timeline']['info']['frames'][1]['participantFrames'][pid]['level']=1
        events.extend([level(1,2,61000),level(1,2,61000),level(6,2,65000),
                       dict(type='SKILL_LEVEL_UP',participantId=1,level=3,timestamp=62000),
                       dict(type='SECRET_ARBITRARY_EVENT',timestamp=70000)])
        r=self.report(b);c=r['cohorts'][0]
        self.assertEqual(c['level_2']['earlier_n'],1)
        self.assertEqual(c['level_2']['own_exact_event_n'],1)
        self.assertEqual(c['level_3']['own_exact_event_n'],0)
        counts={x['event_type']:x for x in r['inspection']['events']}
        self.assertEqual(counts['LEVEL_UP'],dict(event_type='LEVEL_UP',count=3,duplicate_n=1))
        self.assertEqual(counts['OTHER']['count'],1)
        self.assertNotIn('SECRET_ARBITRARY_EVENT',json.dumps(r))

    def test_conflicting_or_malformed_level_events_are_unknown_without_frame_fallback(self):
        for events in ([level(1,2,61000),level(1,2,62000),level(6,2,65000)],
                       [dict(type='LEVEL_UP',participantId=1,timestamp=61000),level(6,2,65000)]):
            with self.subTest(events=events),tempfile.TemporaryDirectory() as tmp:
                b=envelope();b['timeline']['info']['frames'][2]['events']=events
                root=Path(tmp);PostgameStore(root/'private'/'matches').import_match(b)
                stat=self.audit(root)['cohorts'][0]['level_2']
                self.assertEqual(stat['unknown_n'],1);self.assertEqual(stat['own_interval_width_ms']['missing_n'],1)

    def test_cross_level_chronology_and_event_frame_contradiction_are_unknown(self):
        cases=[[level(1,3,60000),level(1,2,120000)], [level(1,2,61000)]]
        for events in cases:
            with self.subTest(events=events),tempfile.TemporaryDirectory() as tmp:
                b=envelope();b['timeline']['info']['frames'][2]['events']=events
                root=Path(tmp);PostgameStore(root/'private'/'matches').import_match(b)
                cohort=self.audit(root)['cohorts'][0]
                self.assertEqual(cohort['level_2']['own_exact_event_n'],0)
                self.assertEqual(cohort['level_2']['unknown_n'],1)

    def test_schema_valid_report_without_actual_source_binding_is_not_usable(self):
        from coach_v1 import pilot_observations
        self.assertTrue(hasattr(pilot_observations,'load_bound_report'),'bound report loader missing')
        folder=self.root/'public';folder.mkdir()
        (folder/'observations.json').write_text(json.dumps(self.report()))
        with self.assertRaises(ValueError):pilot_observations.load_bound_report(folder)
        (folder/'source-binding.json').write_text(json.dumps({'report_sha256':'0'*64}))
        with self.assertRaises(ValueError):pilot_observations.load_bound_report(folder)

    def test_overlapping_frame_bounds_are_unknown_and_disjoint_bounds_order(self):
        b=envelope();r=self.report(b);c=r['cohorts'][0]
        self.assertEqual(c['level_2']['unknown_n'],1)
        self.assertEqual(c['level_2']['own_frame_interval_n'],1)
        self.assertEqual(c['level_2']['own_interval_width_ms']['median'],60000)
        self.assertEqual(c['level_2']['own_exact_event_n'],0)
        with tempfile.TemporaryDirectory() as tmp:
            b=envelope()
            for f in b['timeline']['info']['frames']:
                f['participantFrames']['6']['level']=1 if f['timestamp']<180000 else 2
            root=Path(tmp);PostgameStore(root/'private'/'matches').import_match(b)
            self.assertEqual(self.audit(root)['cohorts'][0]['level_2']['earlier_n'],1)

    def test_gold_requires_same_exact_frame_and_total_gold(self):
        r=self.report();c=r['cohorts'][0]
        self.assertEqual(c['gold_at_10']['median'],-5)
        self.assertEqual(c['gold_at_15']['n_valid'],1)
        with tempfile.TemporaryDirectory() as tmp:
            b=envelope();b['timeline']['info']['frames'][-2]['timestamp']=600001
            del b['timeline']['info']['frames'][-1]['participantFrames']['6']['totalGold']
            root=Path(tmp);PostgameStore(root/'private'/'matches').import_match(b)
            c=self.audit(root)['cohorts'][0]
            self.assertEqual(c['gold_at_10']['n_valid'],0)
            self.assertEqual(c['gold_at_15']['missing_n'],1)

    def test_ambiguous_opposite_role_never_selects_arbitrary_opponent(self):
        b=envelope();b['match']['info']['participants'][6]['teamPosition']='TOP'
        c=self.report(b)['cohorts'][0]
        self.assertIsNone(c['opponent_champion']);self.assertEqual(c['opponent_missing_n'],1)
        self.assertEqual(c['gold_at_10']['missing_n'],1)
        self.assertEqual(c['level_2']['unknown_n'],1)

    def test_counts_use_selected_people_and_match_dedup_and_patch_separation(self):
        b=envelope();self.store.import_match(b);b['participant_id']=2;self.store.import_match(b)
        r=self.audit(self.root)
        self.assertEqual(r['source']['matches'],1)
        self.assertEqual(r['source']['participant_observations'],2)
        self.assertEqual(r['patches'],[dict(patch='16.19',matches=1,participant_observations=2)])
        self.assertEqual(len(r['cohorts']),2)
        self.assertEqual(r['inspection']['frames'],6)
        self.assertEqual(r['inspection']['participant_frames'],60)

    def test_jungle_only_first_observed_lane_kill_involvement_is_not_first_gank(self):
        b=envelope(2);b['timeline']['info']['frames'][2]['events']=[
            dict(type='CHAMPION_KILL',timestamp=61000,killerId=1,victimId=7,assistingParticipantIds=[],position=dict(x=5000,y=5000)),
            dict(type='CHAMPION_KILL',timestamp=62000,killerId=1,victimId=7,assistingParticipantIds=[2],position=dict(x=5000,y=5000)),
            dict(type='CHAMPION_KILL',timestamp=63000,killerId=2,victimId=1,position=dict(x=5000,y=5000))]
        c=self.report(b)['cohorts'][0];j=c['jungle_lane_kill_involvement']
        self.assertEqual(j['timing_ms']['median'],62000)
        self.assertEqual(j['label'],'FIRST_OBSERVED_LANE_KILL_INVOLVEMENT')
        self.assertEqual(j['lanes'],dict(TOP=0,MID=1,BOTTOM=0))
        self.assertEqual(j['first_gank'],'UNKNOWN')

    def test_identity_nonleak_strict_recursive_validator_and_copy(self):
        r=self.report();serialized=json.dumps(r,allow_nan=False)
        for secret in ('PRIVATE_ACCOUNT','KR_123456789',str(self.root),'participantId','puuid','participant_id','match_sha256'):
            self.assertNotIn(secret,serialized)
        copy_r=self.validate(r);copy_r['source']['matches']=0
        self.assertEqual(r['source']['matches'],1)
        for mutate in (lambda d:d['cohorts'][0].update(raw='PRIVATE'),
                       lambda d:d['inspection']['events'][0].update(event_type='PRIVATE'),
                       lambda d:d['cohorts'][0]['gold_at_10'].update(median=float('nan')),
                       lambda d:d['cohorts'][0]['level_2'].update(unknown_n=True),
                       lambda d:d['evaluation'].update(reason='PRIVATE')):
            bad=copy.deepcopy(r);mutate(bad)
            with self.assertRaises(ValueError):self.validate(bad)
        self.assertEqual(r['evaluation']['evaluable_scenes'],0)
        self.assertIsNone(r['evaluation']['accuracy'])

    def test_touching_intervals_and_equal_event_times_remain_unknown(self):
        for events in ([level(1,2,61000),level(6,2,61000)], [level(1,2,60000)]):
            with self.subTest(events=events),tempfile.TemporaryDirectory() as tmp:
                b=envelope();b['timeline']['info']['frames'][2]['events']=events
                root=Path(tmp);PostgameStore(root/'private'/'matches').import_match(b)
                stat=self.audit(root)['cohorts'][0]['level_2']
                self.assertEqual(stat['earlier_n'],0);self.assertEqual(stat['later_n'],0)
                self.assertEqual(stat['unknown_n'],1)

    def test_frame_without_prior_lower_level_is_unknown_and_health_presence_is_validated(self):
        b=envelope()
        for f in b['timeline']['info']['frames']:
            f['participantFrames']['1']['level']=3
            f['participantFrames']['1']['championStats']['health']=-1
        r=self.report(b);c=r['cohorts'][0]
        self.assertEqual(c['level_2']['own_interval_width_ms']['missing_n'],1)
        self.assertEqual(c['level_3']['own_interval_width_ms']['missing_n'],1)
        self.assertEqual(r['inspection']['health_present'],54)

    def test_unknown_champion_name_fails_closed_instead_of_releasing_arbitrary_strings(self):
        b=envelope();b['match']['info']['participants'][0]['championName']='PrivateAccountName'
        self.store.import_match(b)
        with self.assertRaises(ValueError):self.audit(self.root)

    def test_level_arrival_bound_marginals_preserve_frame_and_exact_event_times(self):
        r=self.report();stat=r['cohorts'][0]['level_2']
        self.assertIn('own_interval_bounds_ms',stat)
        bounds=stat['own_interval_bounds_ms']
        self.assertEqual(bounds['aggregation'],'MARGINAL_DISTRIBUTIONS_NOT_JOINT_SCENES')
        self.assertEqual(bounds['lower_ms']['median'],0)
        self.assertEqual(bounds['upper_ms']['median'],60000)
        copied=self.validate(r)
        copied['cohorts'][0]['level_2']['own_interval_bounds_ms']['lower_ms']['median']=99
        self.assertEqual(bounds['lower_ms']['median'],0)
        for mutate in (lambda d:d['cohorts'][0]['level_2']['own_interval_bounds_ms'].update(scene='PRIVATE'),
                       lambda d:d['cohorts'][0]['level_2']['own_interval_bounds_ms']['lower_ms'].update(extra=1),
                       lambda d:d['cohorts'][0]['level_2']['own_interval_bounds_ms'].update(aggregation='PRIVATE'),
                       lambda d:d['cohorts'][0]['level_2']['own_interval_bounds_ms']['lower_ms'].update(n_valid=True)):
            bad=copy.deepcopy(r);mutate(bad)
            with self.assertRaises(ValueError):self.validate(bad)
        with tempfile.TemporaryDirectory() as tmp:
            b=envelope();b['timeline']['info']['frames'][2]['events']=[level(1,2,61000)]
            b['timeline']['info']['frames'][1]['participantFrames']['1']['level']=1
            root=Path(tmp);PostgameStore(root/'private'/'matches').import_match(b)
            exact=self.audit(root)['cohorts'][0]['level_2']['own_interval_bounds_ms']
            self.assertEqual(exact['lower_ms']['median'],61000)
            self.assertEqual(exact['upper_ms']['median'],61000)

    def test_level_up_inspection_reports_malformed_and_conflicting_group_counts(self):
        b=envelope();b['timeline']['info']['frames'][2]['events']=[
            level(1,2,61000),level(1,2,61000),level(1,2,62000),
            level(6,2,65000),dict(type='LEVEL_UP',participantId=1,timestamp=63000),
            dict(type='SKILL_LEVEL_UP',participantId=1,timestamp=64000)]
        r=self.report(b)
        self.assertIn('level_up_malformed_n',r['inspection'])
        self.assertEqual(r['inspection']['level_up_malformed_n'],1)
        self.assertEqual(r['inspection']['level_up_conflicting_groups_n'],1)
        bad=copy.deepcopy(r);bad['inspection']['level_up_malformed_n']=True
        with self.assertRaises(ValueError):self.validate(bad)

    def test_synthetic_source_rejected_and_missing_cache_fails_without_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=envelope();b['source']='SYNTHETIC';root=Path(tmp)
            PostgameStore(root/'private'/'matches',test_mode=True).import_match(b)
            with self.assertRaises(ValueError):self.audit(root)
        missing=self.root/'not-created'
        with self.assertRaises(ValueError):self.audit(missing)
        self.assertFalse(missing.exists())

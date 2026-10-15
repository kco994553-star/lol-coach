"""New v2.3 synthetic observations only; no completed queue evidence rerun."""
import copy
import importlib.util
import json
import unittest


def fixture(number=1, *, patch='16.20', end=600000):
    players=[dict(participantId=1,teamId=100,championName='Ahri',teamPosition='MIDDLE',puuid='PRIVATE_PUUID'),
             dict(participantId=6,teamId=200,championName='Syndra',teamPosition='MIDDLE')]
    match=dict(metadata=dict(matchId=f'KR_PRIVATE_{number}'),info=dict(gameVersion=patch+'.1',queueId=420,mapId=11,participants=players))
    frames=[]
    for t in range(0,end+1,60000):
        pf={str(p['participantId']):dict(currentGold=900+t/1000,championStats=dict(health=200 if t==180000 else 1000,healthMax=1000),position=dict(x=7000,y=7000)) for p in players}
        frames.append(dict(timestamp=t,participantFrames=pf,events=[]))
    timeline=dict(metadata=match['metadata'].copy(),info=dict(frames=frames))
    return match,timeline


def event(timeline,kind,time,**fields):
    timeline['info']['frames'][-1]['events'].append(dict(type=kind,timestamp=time,**fields))


class RecallStatsTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.recall_stats'),'new recall extraction module missing')
        from coach_v1 import recall_stats
        return recall_stats
    def extract(self,match,timeline):return self.module().extract_match(match,timeline,population='CHALLENGER')
    def participant(self,observation,champion='Ahri'):return next(p for p in observation['participants'] if p['champion']==champion)
    def dataset(self,observations):return self.module().build_dataset(observations,population='CHALLENGER',retrieved_at='2026-10-15T00:00:00Z')

    def test_chronological_first_bundle_undo_and_preceding_gold(self):
        match,tl=fixture();event(tl,'ITEM_PURCHASED',200000,participantId=1,itemId=1052)
        event(tl,'ITEM_PURCHASED',160000,participantId=1,itemId=1001)
        event(tl,'ITEM_PURCHASED',140000,participantId=1,itemId=2003)
        event(tl,'ITEM_UNDO',141000,participantId=1,beforeId=2003,afterId=0)
        event(tl,'ITEM_PURCHASED',1000,participantId=1,itemId=1056)
        tl['info']['frames'].reverse()
        first=self.participant(self.extract(match,tl))['first_recall']
        self.assertEqual(first['timestamp_ms'],160000);self.assertEqual(first['item_ids'],[1001])
        self.assertEqual(first['current_gold'],1020);self.assertEqual(first['gold_frame_timestamp_ms'],120000)
        self.assertEqual(first['timing_kind'],'FIRST_PURCHASE_PROXY')

    def test_pre_purchase_death_excludes_post_death_shop(self):
        match,tl=fixture();event(tl,'CHAMPION_KILL',150000,victimId=1,killerId=6)
        event(tl,'ITEM_PURCHASED',160000,participantId=1,itemId=1001)
        first=self.participant(self.extract(match,tl))['first_recall']
        self.assertEqual(first['status'],'UNKNOWN');self.assertEqual(first['reason'],'DEATH_BEFORE_FIRST_PURCHASE')

    def test_low_health_stay_actual_lane_then_death_is_not_recall(self):
        match,tl=fixture();event(tl,'CHAMPION_KILL',250000,victimId=1,killerId=6,position=dict(x=7000,y=7000))
        event(tl,'ITEM_PURCHASED',260000,participantId=1,itemId=1001)
        low=self.participant(self.extract(match,tl))['low_health']
        self.assertEqual(low['action'],'STAY');self.assertEqual(low['outcomes']['self_deaths']['value'],1)

    def test_low_health_purchase_before_death_and_opponent_other_lane_assist(self):
        match,tl=fixture();event(tl,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
        event(tl,'CHAMPION_KILL',220000,victimId=2,killerId=8,assistingParticipantIds=[6],position=dict(x=1000,y=8000))
        event(tl,'TURRET_PLATE_DESTROYED',230000,killerId=6,teamId=100,position=dict(x=7000,y=7000))
        event(tl,'ELITE_MONSTER_KILL',235000,killerId=6,killerTeamId=200,position=dict(x=9500,y=4500))
        low=self.participant(self.extract(match,tl))['low_health']
        self.assertEqual(low['action'],'PURCHASE')
        self.assertEqual(low['outcomes']['opponent_other_lane_involvements']['value'],1)
        self.assertEqual(low['outcomes']['opponent_plates']['value'],1)
        self.assertEqual(low['outcomes']['opponent_jungle_objectives']['value'],1)

    def test_partial_window_and_missing_event_position_are_unknown(self):
        # Retained coverage reaches240s after excluding final300s; the
        # purchase is observed, but the180-300s outcome window is incomplete.
        match,tl=fixture(end=300000);event(tl,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
        low=self.participant(self.extract(match,tl))['low_health']
        self.assertIsNone(low['outcomes']['self_deaths']['value'])
        match,tl=fixture();event(tl,'CHAMPION_KILL',220000,killerId=6,victimId=2)
        low=self.participant(self.extract(match,tl))['low_health']
        self.assertIsNone(low['outcomes']['opponent_other_lane_involvements']['value'])
        self.assertEqual(low['outcomes']['self_deaths']['value'],0)

    def test_jungle_missing_health_and_unknown_lane_are_separate_exclusions(self):
        match,tl=fixture();match['info']['participants'][0]['teamPosition']='JUNGLE'
        low=self.participant(self.extract(match,tl))['low_health'];self.assertEqual(low['reason'],'JUNGLE_EXCLUDED')
        match,tl=fixture()
        for f in tl['info']['frames']:f['participantFrames']['1'].pop('championStats')
        self.assertEqual(self.participant(self.extract(match,tl))['low_health']['reason'],'HEALTH_UNOBSERVED')
        match,tl=fixture();tl['info']['frames'][4]['participantFrames']['1']['position']={}
        self.assertEqual(self.participant(self.extract(match,tl))['low_health']['reason'],'NEXT_FRAME_LANE_UNKNOWN')

    def test_priority_gap_is_observed_noncausal_and_sensitivity_grid(self):
        match,tl=fixture();event(tl,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
        event(tl,'ITEM_PURCHASED',250000,participantId=6,itemId=1052)
        p=self.participant(self.extract(match,tl));gap=p['first_recall']['priority_gap']
        self.assertEqual(gap['gap_ms'],50000);self.assertEqual(gap['signal'],'FIRST_RECALL_PRIORITY_GAP')
        self.assertEqual({(s['health_ratio'],s['window_ms']) for s in p['sensitivity']},{(h,w) for h in (.2,.3,.4) for w in (60000,120000,180000)})

    def test_aggregation_cluster_dedup_patch_population_and_privacy(self):
        observations=[]
        for n in range(1,6):
            m,t=fixture(n);event(t,'ITEM_PURCHASED',180000+n*1000,participantId=1,itemId=1001)
            observations.append(self.extract(m,t))
        data=self.dataset(observations+[copy.deepcopy(observations[0])])
        self.assertEqual(data['samples']['matches'],5)
        exact=next(c for c in data['cohorts'] if c['champion']=='Ahri')
        self.assertEqual(exact['first_recall']['timing']['median'],183000)
        self.assertEqual(exact['first_recall']['timing']['q1'],182000)
        self.assertEqual(exact['first_recall']['purchases'][0]['item_ids'],[1001])
        public=json.dumps(data)
        for text in ('PRIVATE_PUUID','KR_PRIVATE_','cluster_key','participantId'):self.assertNotIn(text,public)
        other=copy.deepcopy(observations[0]);other['population']='PRO_REFERENCE'
        with self.assertRaises(ValueError):self.dataset([other])
        m,t=fixture(99,patch='16.19');mixed=self.dataset(observations+[self.extract(m,t)])
        self.assertEqual({c['patch'] for c in mixed['cohorts']},{'16.20','16.19'})

    def test_view_champion_role_unknown_uses_matches_not_participant_count(self):
        obs=[]
        for n in range(1,6):
            m,t=fixture(n);event(t,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
            obs.append(self.extract(m,t))
        data=self.dataset(obs)
        view=self.module().recall_view(data,champion='Ahri',position='MIDDLE',patch='16.20')
        self.assertEqual(view['scope'],'CHAMPION');self.assertEqual(view['sample']['matches'],5)
        view=self.module().recall_view(data,champion='Lux',position='MID',patch='16.20')
        self.assertEqual(view['scope'],'ROLE')
        data=self.dataset(obs[:3]);view=self.module().recall_view(data,champion='Lux',position='MID',patch='16.20')
        self.assertEqual(view['status'],'UNKNOWN');self.assertEqual(view['sample']['matches'],3)
        self.assertIsNone(view['first_recall'])
        view=self.module().recall_view(data,champion='Ahri',position='MID',patch='16.19')
        self.assertEqual(view['sample']['matches'],0)

    def test_strict_validation_rejects_identity_and_nested_shape_injection(self):
        module=self.module();data=self.dataset([self.extract(*fixture())]);module.validate_dataset(data)
        for inject in ('identity','nested','forged'):
            bad=copy.deepcopy(data)
            if inject=='identity':bad['puuid']='PRIVATE'
            elif inject=='nested':bad['cohorts'][0]['first_recall']['purchases']=[dict(item_ids=[1001],count=1,matches=1,puuid='PRIVATE')]
            else:bad['cohorts'][0]['matches']=100
            with self.assertRaises(ValueError):module.validate_dataset(bad)

    def test_missing_gold_is_missing_not_zero_and_match_weighted_outcomes(self):
        m,t=fixture();event(t,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
        for f in t['info']['frames']:f['participantFrames']['1'].pop('currentGold')
        data=self.dataset([self.extract(m,t)])
        exact=next(c for c in data['cohorts'] if c['champion']=='Ahri')
        self.assertIsNone(exact['first_recall']['current_gold']['median'])
        self.assertEqual(exact['first_recall']['current_gold']['missing_n'],1)
        self.assertEqual(exact['low_health']['purchase']['outcomes']['self_deaths']['n'],1)

    def test_pro_requires_selected_players_but_retains_opponent_context(self):
        m,t=fixture();event(t,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
        event(t,'ITEM_PURCHASED',250000,participantId=6,itemId=1052)
        module=self.module()
        with self.assertRaises(ValueError):module.extract_match(m,t,population='PRO_REFERENCE')
        for ids in ([],[True],[1,1],[99]):
            with self.assertRaises(ValueError):module.extract_match(m,t,population='PRO_REFERENCE',participant_ids=ids)
        selected=module.extract_match(m,t,population='PRO_REFERENCE',participant_ids=[1])
        self.assertEqual(len(selected['participants']),1)
        self.assertEqual(selected['participants'][0]['first_recall']['priority_gap']['gap_ms'],50000)
        data=module.build_dataset([selected],population='PRO_REFERENCE',retrieved_at='2026-10-15T00:00:00Z')
        self.assertEqual(data['samples']['participant_observations'],1)

    def test_enough_matches_without_valid_recall_does_not_claim_usable_timing(self):
        observations=[self.extract(*fixture(n)) for n in range(1,6)]
        data=self.dataset(observations)
        view=self.module().recall_view(data,champion='Ahri',position='MID',patch='16.20')
        self.assertEqual(view['status'],'UNKNOWN')
        self.assertEqual(view['reason'],'VALID_RECALL_MATCH_N_LT_5')
        self.assertIsNone(view['first_recall'])
        raw=next(c for c in data['cohorts'] if c['champion']=='Ahri')['first_recall']['timing']
        self.assertEqual(raw['status'],'UNKNOWN');self.assertEqual(raw['n'],0)

    def test_first_purchase_bundle_stops_before_subsequent_death(self):
        m,t=fixture();event(t,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
        event(t,'CHAMPION_KILL',210000,victimId=1,killerId=6)
        event(t,'ITEM_PURCHASED',220000,participantId=1,itemId=1052)
        self.assertEqual(self.participant(self.extract(m,t))['first_recall']['item_ids'],[1001])

    def test_five_valid_matches_exposes_distribution_status(self):
        observations=[]
        for n in range(5):
            m,t=fixture(n);event(t,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
            observations.append(self.extract(m,t))
        exact=next(c for c in self.dataset(observations)['cohorts'] if c['champion']=='Ahri')
        self.assertEqual(exact['first_recall']['timing']['status'],'AVAILABLE')
        self.assertIsNone(exact['first_recall']['timing']['reason'])

    def test_fallback_uses_valid_recall_matches_not_total_matches(self):
        observations=[]
        for n in range(1,6):
            m,t=fixture(n)
            if n<=2:event(t,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
            event(t,'ITEM_PURCHASED',250000,participantId=6,itemId=1052)
            observations.append(self.extract(m,t))
        view=self.module().recall_view(self.dataset(observations),champion='Ahri',position='MID',patch='16.20')
        self.assertEqual(view['scope'],'ROLE')
        self.assertEqual(view['first_recall']['timing']['match_n'],5)

    def test_outcome_status_separates_unobserved_from_complete_zero(self):
        data=self.dataset([self.extract(*fixture())])
        c=next(c for c in data['cohorts'] if c['champion']=='Ahri')
        empty=c['low_health']['purchase']['outcomes']['self_deaths']
        zero=c['low_health']['stay']['outcomes']['self_deaths']
        self.assertEqual(empty['status'],'UNKNOWN');self.assertIsNone(empty['mean'])
        self.assertEqual(zero['status'],'AVAILABLE');self.assertEqual(zero['mean'],0)

    def test_role_outcomes_weight_matches_equally_with_unequal_windows(self):
        m,t=fixture(1);event(t,'CHAMPION_KILL',250000,victimId=1,killerId=6,position=dict(x=7000,y=7000))
        observations=[self.extract(m,t)]
        m,t=fixture(2)
        t['info']['frames'][3]['participantFrames']['6']['championStats']['health']=1000
        observations.append(self.extract(m,t))
        role=next(c for c in self.dataset(observations)['cohorts'] if c['champion'] is None)
        outcome=role['low_health']['stay']['outcomes']['self_deaths']
        self.assertEqual(outcome['n'],2);self.assertEqual(outcome['participant_n'],3)
        self.assertEqual(outcome['mean'],.25);self.assertEqual(outcome['total'],1)

    def test_missing_event_stream_does_not_invent_known_zero(self):
        m,t=fixture();t['info']['frames'][4].pop('events')
        with self.assertRaises(ValueError):self.extract(m,t)

    def test_jungle_first_purchase_does_not_invent_opponent_lane_roam(self):
        m,t=fixture()
        for p in m['info']['participants']:p['teamPosition']='JUNGLE'
        event(t,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
        event(t,'ITEM_PURCHASED',250000,participantId=6,itemId=1052)
        gap=self.participant(self.extract(m,t))['first_recall']['priority_gap']
        self.assertIsNone(gap['outcomes']['opponent_other_lane_involvements']['value'])

    def test_malformed_shapes_fail_closed_with_value_errors(self):
        for side,key in (('match','metadata'),('timeline','metadata'),('match','info'),('timeline','info')):
            m,t=fixture();(m if side=='match' else t)[key]=None
            with self.subTest(side=side,key=key):
                with self.assertRaises(ValueError):self.extract(m,t)
        data=self.dataset([self.extract(*fixture())])
        data['cohorts'][0]['first_recall']['timing']['match_n']='5'
        with self.assertRaises(ValueError):self.module().validate_dataset(data)

    def test_private_context_has_observations_without_population_or_identity(self):
        m,t=fixture();event(t,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
        event(t,'ITEM_PURCHASED',250000,participantId=6,itemId=1052)
        context=self.module().extract_private_context(m,t,1)
        self.assertEqual(set(context),{'first_recall','low_health','sensitivity','champion','position'})
        self.assertEqual(context['champion'],'Ahri')
        self.assertEqual(context['first_recall']['priority_gap']['gap_ms'],50000)
        public=json.dumps(context)
        for text in ('PRIVATE','CHALLENGER','PRO_REFERENCE','population','cluster_key','participantId'):
            self.assertNotIn(text,public)

    def test_private_context_rejects_invalid_selection_and_public_local_population(self):
        module=self.module();m,t=fixture()
        for pid in (True,0,99):
            with self.assertRaises(ValueError):module.extract_private_context(m,t,pid)
        with self.assertRaises(ValueError):module.extract_match(m,t,population='LOCAL_PRIVATE',participant_ids=[1])
        with self.assertRaises(ValueError):module.build_dataset([],population='LOCAL_PRIVATE',retrieved_at='2026-10-15T00:00:00Z')

    def test_private_post_action_roam_requires_after_purchase_without_extending_window(self):
        for roam_time,expected in ((190000,0),(220000,1),(310000,0)):
            m,t=fixture();event(t,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
            event(t,'CHAMPION_KILL',roam_time,victimId=2,killerId=6,position=dict(x=1000,y=8000))
            with self.subTest(roam_time=roam_time):
                context=self.module().extract_private_context(m,t,1)
                post=context['low_health'].get('post_action_outcomes')
                self.assertIsNotNone(post,'private context needs an action-relative outcome window')
                self.assertEqual(post['opponent_other_lane_involvements']['value'],expected)
                public=self.participant(self.extract(m,t))['low_health']
                self.assertNotIn('post_action_outcomes',public)
                self.assertEqual(public['outcomes']['opponent_other_lane_involvements']['value'],int(roam_time<=300000))

    def test_cadence_guard_rejects_internal_frame_loss_before_extracting_zero(self):
        m,t=fixture();t['info']['frameInterval']=60000
        by_time={f['timestamp']:f for f in t['info']['frames']}
        by_time[180000]['events'].append(dict(type='ITEM_PURCHASED',timestamp=160000,participantId=1,itemId=1001))
        by_time[240000]['events'].append(dict(type='CHAMPION_KILL',timestamp=220000,victimId=1,killerId=6,position=dict(x=7000,y=7000)))
        by_time[300000]['events'].append(dict(type='ITEM_PURCHASED',timestamp=250000,participantId=6,itemId=1052))
        complete=self.participant(self.extract(m,t))
        self.assertEqual(complete['first_recall']['priority_gap']['outcomes']['self_deaths']['value'],1)
        t['info']['frames']=[f for f in t['info']['frames'] if f['timestamp']!=240000]
        with self.assertRaisesRegex(ValueError,'cadence'):self.extract(m,t)
        with self.assertRaisesRegex(ValueError,'cadence'):self.module().extract_private_context(m,t,1)

    def test_cadence_guard_accepts_timestamp_jitter_and_short_final_interval(self):
        m,t=fixture();t['info']['frameInterval']=60000
        for index,frame in enumerate(t['info']['frames']):frame['timestamp']=index*60030
        t['info']['frames'][-1]['timestamp']=570000
        self.assertEqual(self.extract(m,t)['patch'],'16.20')

    def test_cadence_guard_rejects_missing_origin_and_unsupported_declared_interval(self):
        m,t=fixture();t['info']['frames']=t['info']['frames'][1:]
        with self.assertRaisesRegex(ValueError,'origin'):self.extract(m,t)
        for interval in (None,True,60000.0,30000,120000):
            m,t=fixture();t['info']['frameInterval']=interval
            with self.subTest(interval=interval):
                with self.assertRaisesRegex(ValueError,'cadence'):self.extract(m,t)

    def test_pre_guard_dataset_policy_cannot_project_as_current_evidence(self):
        data=self.dataset([self.extract(*fixture())])
        self.assertIn('coverage_guard',data['measurement_policy'])
        data['measurement_policy'].pop('coverage_guard')
        with self.assertRaises(ValueError):self.module().validate_dataset(data)
        with self.assertRaises(ValueError):self.module().recall_view(data,champion='Ahri',position='MID',patch='16.20')

    def test_missing_penultimate_regular_frame_before_short_final_is_rejected(self):
        m,t=fixture(end=240000);t['info']['frameInterval']=60000
        final=copy.deepcopy(t['info']['frames'][-1]);final['timestamp']=270000;final['events']=[]
        t['info']['frames'].append(final)
        event(t,'ITEM_PURCHASED',140000,participantId=1,itemId=1001)
        event(t,'ITEM_PURCHASED',150000,participantId=6,itemId=1052)
        t['info']['frames'][-2]['events'].append(dict(type='CHAMPION_KILL',timestamp=220000,victimId=1,killerId=6,position=dict(x=7000,y=7000)))
        t['info']['frames']=[f for f in t['info']['frames'] if f['timestamp']!=240000]
        with self.assertRaisesRegex(ValueError,'cadence'):self.extract(m,t)

    def test_short_final_frame_cannot_establish_action_purchase_or_completed_window(self):
        m,t=fixture(end=240000);t['info']['frameInterval']=60000
        m['info']['participants'].append(dict(participantId=2,teamId=100,championName='Lux',teamPosition='TOP'))
        final=copy.deepcopy(t['info']['frames'][-1]);final['timestamp']=241000;final['events']=[]
        t['info']['frames'].append(final)
        event(t,'ITEM_PURCHASED',140000,participantId=1,itemId=1001)
        event(t,'ITEM_PURCHASED',150000,participantId=6,itemId=1052)
        event(t,'ITEM_PURCHASED',220000,participantId=2,itemId=1056)
        event(t,'ITEM_PURCHASED',250000,participantId=2,itemId=1001)
        t['info']['frames']=[f for f in t['info']['frames'] if f['timestamp']!=240000]
        observation=self.extract(m,t);own=self.participant(observation)
        self.assertEqual(own['first_recall']['timestamp_ms'],140000)
        self.assertIsNone(own['first_recall']['priority_gap']['outcomes']['self_deaths']['value'])
        self.assertEqual(own['low_health']['status'],'EXCLUDED')
        self.assertEqual(own['low_health']['reason'],'NEXT_FRAME_UNOBSERVED')
        self.assertEqual(self.participant(observation,'Lux')['first_recall']['status'],'UNKNOWN')

    def test_malformed_or_cross_match_input_rejected(self):
        m,t=fixture();t['metadata']['matchId']='OTHER'
        with self.assertRaises(ValueError):self.extract(m,t)
        m,t=fixture();m['info']['queueId']=450
        with self.assertRaises(ValueError):self.extract(m,t)

if __name__=='__main__':unittest.main()

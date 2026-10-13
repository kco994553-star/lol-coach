"""SYNTHETIC private personal match mechanics; no real account data."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


def body():
    people=[dict(participantId=i,puuid='PRIVATE_PUUID_'+str(i),championName=['Ornn','Sejuani','Ahri','Caitlyn','Lux'][(i-1)%5],teamPosition=['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY'][(i-1)%5],teamId=100 if i<=5 else 200) for i in range(1,11)]
    frames=[]
    for minute in (0,1,3):
        pf={str(i):dict(participantId=i,totalGold=500+100*minute+i,xp=60*minute,minionsKilled=5*minute,jungleMinionsKilled=minute,level=1+minute,position=dict(x=100*i+minute*20,y=100*i)) for i in range(1,11)}
        events=[]
        if minute==1:events=[dict(type='ITEM_PURCHASED',timestamp=61000,participantId=4,itemId=1001),dict(type='WARD_PLACED',timestamp=62000,creatorId=5,wardType='YELLOW_TRINKET'),dict(type='CHAMPION_KILL',timestamp=63000,victimId=4,killerId=7),dict(type='ELITE_MONSTER_KILL',timestamp=64000,killerId=2,monsterType='DRAGON')]
        frames.append(dict(timestamp=minute*60000,participantFrames=pf,events=events))
    return dict(source='SYNTHETIC',participant_id=4,match=dict(metadata=dict(matchId='KR_123456',participants=[p['puuid'] for p in people]),info=dict(gameVersion='16.19.1',gameDuration=240,mapId=11,queueId=420,gameMode='CLASSIC',participants=people)),timeline=dict(metadata=dict(matchId='KR_123456',participants=[p['puuid'] for p in people]),info=dict(frameInterval=60000,participants=[dict(participantId=p['participantId'],puuid=p['puuid']) for p in people],frames=frames)))


class PostgameTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.postgame_match'),'postgame implementation absent')
        from coach_v1.postgame_match import PostgameStore
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'private'/'postgame';self.store=PostgameStore(self.path,test_mode=True)
    def detail(self,b=None,**kwargs):
        row=self.store.import_match(b or body());return self.store.get_match(row['id'],**kwargs)
    def test_import_private_roundtrip_without_identity_in_response(self):
        b=body();before=copy.deepcopy(b);row=self.store.import_match(b)
        self.assertEqual(b,before);self.assertEqual(self.store.import_match(b),row)
        self.assertEqual(self.store.list_matches()['matches'],[row]);d=self.store.get_match(row['id'])
        self.assertNotIn('PRIVATE_PUUID',json.dumps(d));self.assertNotIn('KR_123456',json.dumps(d))
        files=list(self.path.glob('*.json'));self.assertEqual(len(files),1)
        if os.name!='nt':self.assertEqual(os.stat(files[0]).st_mode&0o777,0o600)
        self.assertEqual(json.loads(files[0].read_text())['match'],b['match'])
        if os.name!='nt':self.assertEqual(os.stat(self.path).st_mode&0o777,0o700)
    def test_synthetic_is_rejected_without_server_test_mode(self):
        from coach_v1.postgame_match import PostgameStore
        with self.assertRaises(ValueError):PostgameStore(self.path).import_match(body())
    def test_malformed_pair_ids_timestamps_owner_and_nan_never_written(self):
        variants=[]
        b=body();b['timeline']['metadata']['matchId']='KR_999';variants.append(b)
        b=body();b['participant_id']=True;variants.append(b)
        b=body();b['match']['info']['participants'][3]['puuid']='not_owner';variants.append(b)
        b=body();b['timeline']['info']['frames'][1]['timestamp']=-1;variants.append(b)
        b=body();b['timeline']['info']['frames'][0]['participantFrames']['4']['xp']=float('nan');variants.append(b)
        b=body();b['match']['metadata']['matchId']='../../escape';variants.append(b)
        b=body();b['timeline']['info']['frames'][1]['participantFrames']['4']['participantId']=8;variants.append(b)
        for b in variants:
            with self.subTest(b=b):
                with self.assertRaises(ValueError):self.store.import_match(b)
        self.assertEqual(list(self.path.glob('*.json')),[])
    def test_missing_resources_are_null_and_gaps_never_interpolated(self):
        b=body();del b['timeline']['info']['frames'][1]['participantFrames']['4']['xp'];d=self.detail(b)
        self.assertEqual([p['minute'] for p in d['resources']], [0,1,3])
        self.assertIsNone(d['resources'][1]['xp']);self.assertEqual(d['gaps'],[2])
        self.assertEqual(d['resources'][2]['cs'],18)
        self.assertTrue(any(m['kind']=='ITEM' and m['minute']==61000/60000 for m in d['markers']))
        self.assertTrue(any(m['kind']=='LEVEL' for m in d['markers']))
    def test_contexts_dependency_and_plan_have_no_causal_or_outcome_judgment(self):
        d=self.detail(plan={'personal':{'role':{'status':'KNOWN','texts':['SYNTHETIC PLAN']}}})
        kinds={c['kind'] for c in d['contexts']};self.assertTrue({'DEATH','OBJECTIVE','TEAM_WARD'}<=kinds)
        self.assertEqual(d['contexts'][0]['inference'],'SUSPECTED_CONTEXT_ONLY')
        self.assertTrue(all(p['stage']=='UNKNOWN' and p['comparison']['status']=='UNKNOWN' for p in d['positioning']))
        self.assertEqual(d['dependency']['status'],'RECORDED_MOVEMENT_ONLY')
        self.assertEqual(d['plan_review']['execution']['status'],'UNKNOWN')
        self.assertEqual(d['plan_review']['effect']['status'],'UNKNOWN')
        self.assertNotIn('win',d);self.assertIn('SKILL_STATE_UNKNOWN',d['limitations'])
    def test_missing_allied_positions_never_use_enemies_or_zero(self):
        b=body();del b['timeline']['info']['frames'][1]['participantFrames']['2']['position'];d=self.detail(b)
        self.assertIsNone(d['positioning'][1]['distance_to_allies_median'])
        self.assertEqual(d['positioning'][1]['comparison']['status'],'UNKNOWN')
    def test_path_traversal_and_symlink_storage_are_rejected(self):
        with self.assertRaises(ValueError):self.store.get_match('../secret')
        b=body();row=self.store.import_match(b);path=self.path/(row['id']+'.json');path.unlink();outside=Path(self.tmp.name)/'outside';outside.write_text('{}');path.symlink_to(outside)
        with self.assertRaises(ValueError):self.store.get_match(row['id'])
    def test_expired_and_mismatched_plans_are_unknown_and_withheld(self):
        for plan in ({'validity':'EXPIRED','input':{'patch':'16.19','my_champion':'Caitlyn','my_position':'BOTTOM'}}, {'validity':'CURRENT','input':{'patch':'16.19','my_champion':'Ashe','my_position':'BOTTOM'}}):
            plan['personal']={'role':{'texts':['INAPPLICABLE TACTIC']}}
            d=self.detail(plan=plan)
            self.assertEqual(d['plan_review']['premise']['status'],'UNKNOWN')
            self.assertEqual(d['plan_review']['premise']['recorded_plan'],[])
        d=self.detail(plan={'validity':'CURRENT','input':{'patch':'16.19','my_champion':'Caitlyn','my_position':'BOTTOM'},'personal':{'role':{'texts':['RECORDED PLAN']}}})
        self.assertEqual(d['plan_review']['premise']['recorded_plan'],['RECORDED PLAN'])
        self.assertEqual(d['plan_review']['premise']['status'],'PLAN_RECORDED_UNVERIFIED')
    def test_verified_phase_reference_and_resource_deltas_use_honest_units(self):
        import hashlib
        from coach_v1.movement import build_movement_dataset
        from coach_v1.power_stats import build_power_dataset
        from tests_pregame.test_movement import source
        b=body();b['match']['info']['gameStartTimestamp']=100000
        pairs=[];annotations=[]
        for n in (1,2):
            pair=copy.deepcopy(b);pair['match']['metadata']['matchId']='KR_'+str(n);pair['timeline']['metadata']['matchId']='KR_'+str(n)
            pairs.append(pair)
            annotations.append(dict(match_sha256=hashlib.sha256(('KR_'+str(n)).encode()).hexdigest(),timestamp_ms=60000,stage='EARLY',stage_conditions=[dict(field='LANING_ACTIVE',value=True)],source_sha256='a'*64,source_pointer='/verified/phase/0',verification='VERIFIED'))
        annotation=copy.deepcopy(annotations[0]);annotation['match_sha256']=hashlib.sha256(b['match']['metadata']['matchId'].encode()).hexdigest();b['phase_annotations']=[annotation]
        movement=build_movement_dataset(pairs,source=source(),phase_annotations=annotations)
        power=build_power_dataset(pairs,source=source())
        d=self.detail(b,power_data=power,movement_data=movement)
        self.assertEqual(d['positioning'][1]['stage'],'EARLY');self.assertEqual(d['positioning'][1]['comparison']['status'],'KNOWN')
        self.assertEqual(d['positioning'][2]['stage'],'UNKNOWN')
        self.assertEqual(d['reference']['units'],'RESOURCE_DELTA_NOT_ABSOLUTE_TOTAL')
        self.assertTrue(d['reference']['cohorts']);self.assertTrue(all(c['metric'].endswith('_delta') for c in d['reference']['cohorts']))
        self.assertEqual(d['resources'][1]['matchup_delta']['gold'],-5)
    def test_real_pair_import_requires_owner_roster_and_preserves_original(self):
        from coach_v1.postgame_match import PostgameStore
        b=body();b['source']='REAL';row=PostgameStore(self.path).import_match(b)
        self.assertEqual(row['source'],'REAL')
    def test_conflicting_reimport_preserves_private_original(self):
        b=body();row=self.store.import_match(b);b['match']['info']['participants'][3]['championName']='Ashe'
        with self.assertRaises(ValueError):self.store.import_match(b)
        self.assertEqual(self.store.get_match(row['id'])['champion'],'Caitlyn')

    def test_event_context_never_uses_a_future_frame_in_the_same_minute(self):
        b=body();b['timeline']['info']['frames'][1]['timestamp']=65000
        d=self.detail(b);death=next(c for c in d['contexts'] if c['kind']=='DEATH')
        self.assertEqual(death['recorded_context']['timestamp_ms'],0)
        self.assertEqual(death['position_sample_age_seconds'],63)
    def test_malformed_roles_and_roster_types_raise_validation_errors(self):
        b=body();b['match']['info']['participants'][3]['teamPosition']=['BOTTOM']
        with self.assertRaises(ValueError):self.store.import_match(b)
        b=body();b['timeline']['info']['participants'][3]['participantId']=[4]
        with self.assertRaises(ValueError):self.store.import_match(b)

    def test_reference_overlay_normalizes_exact_elapsed_and_never_uses_absolute_ci(self):
        from coach_v1.power_stats import build_power_dataset
        from tests_pregame.test_movement import source
        b=body();b['match']['info']['gameStartTimestamp']=100000;b['timeline']['info']['frames'][1]['timestamp']=65000
        pairs=[]
        for n in (1,2):
            p=copy.deepcopy(b);p['match']['metadata']['matchId']='KR_'+str(n);p['timeline']['metadata']['matchId']='KR_'+str(n);pairs.append(p)
        d=self.detail(b,power_data=build_power_dataset(pairs,source=source()))
        population=next(c for c in d['reference']['cohorts'] if c['metric']=='gold_delta' and c['comparison']=='ROLE_POPULATION')
        ref=next(p for p in population['points'] if p['minute']==1);actual=next(p for p in population['personal_points'] if p['minute']==1)
        self.assertAlmostEqual(actual['value'],604/(65000/60000)-ref['reference_mean'])
        self.assertEqual(population['units'],'gold/minute difference vs role population rate')
        self.assertNotIn('ci95',actual)
        matchup=next(c for c in d['reference']['cohorts'] if c['metric']=='gold_delta' and c['comparison']=='MATCHUP')
        self.assertEqual(next(p for p in matchup['personal_points'] if p['minute']==1)['value'],-5)

    def test_collector_finds_own_participant_and_stops_on_first_auth_failure(self):
        from coach_v1.personal_riot import PersonalRiotCollector
        from coach_v1.riot_collector import CollectionBlocked
        key='RGAPI-'+'00000000-0000-0000-0000-000000000000';b=body();calls=[]
        def transport(url,headers,timeout):
            calls.append((url,headers,timeout))
            payload={'puuid':'PRIVATE_PUUID_4'} if '/accounts/' in url else ['KR_123456'] if '/ids?' in url else b['timeline'] if url.endswith('/timeline') else b['match']
            return 200,{},json.dumps(payload).encode()
        c=PersonalRiotCollector(api_key=' '+key+' ',transport=transport,max_retries=0)
        result=c.collect(riot_id='SYNTHETIC Name#TEST',server='KR',store=self.store)
        self.assertEqual(result['matches'][0]['champion'],'Caitlyn');self.assertEqual(len(calls),4)
        self.assertTrue(all(h['X-Riot-Token']==key for _,h,_ in calls));self.assertNotIn('PRIVATE_PUUID',json.dumps(result))
        blocked=[]
        def denied(*args):blocked.append(args);return 403,{},b'{}'
        c=PersonalRiotCollector(api_key=key,transport=denied,max_retries=3)
        with self.assertRaises(CollectionBlocked):c.collect(riot_id='synthetic#test',server='KR',store=self.store)
        self.assertEqual(len(blocked),1)

    def test_portable_permission_fallback_without_descriptor_chmod(self):
        from unittest.mock import patch
        with patch.object(os,'fchmod',None):
            row=self.store.import_match(body())
            self.assertEqual(self.store.get_match(row['id'])['champion'],'Caitlyn')

    def test_only_reviewed_applied_displayed_rules_supply_plan_premises(self):
        from coach_v1.pregame_evaluator import evaluate_gameplan
        from tests_pregame.test_contract import golden,rule
        from tests_pregame.test_evaluator import approved
        base=rule();base['patches']=['16.19'];base['conditions']=[dict(field='ally.BOTTOM.champion',op='EQ',value='Caitlyn')]
        base['required_fields']=['ally.BOTTOM.champion'];base['output']['text']='APPLIED PLAN'
        rejected=copy.deepcopy(base);rejected['rule_id']='rejected-rule';rejected['output']['text']='REJECTED PLAN'
        plan=evaluate_gameplan(golden(patch='16.19'),[approved(base),approved(rejected,state='REJECTED')]);plan['validity']='CURRENT'
        d=self.detail(plan=plan);conditions=d['plan_review']['premise']['conditions']
        self.assertEqual(len(conditions),1);self.assertEqual(conditions[0]['rule_id'],base['rule_id'])
        self.assertEqual(conditions[0]['version'],'decision-1');self.assertNotIn('REJECTED PLAN',d['plan_review']['premise']['recorded_plan'])
        plan=evaluate_gameplan(golden(patch='16.19'),[approved(rejected,state='REJECTED')]);plan['validity']='CURRENT'
        self.assertEqual(self.detail(plan=plan)['plan_review']['premise']['conditions'],[])
    def test_ambiguous_allied_roles_do_not_select_a_jungler(self):
        b=body();b['match']['info']['participants'][0]['teamPosition']='JUNGLE';d=self.detail(b)
        self.assertIsNone(d['dependency']['samples'][0]['allied_jungle_position'])
        self.assertEqual(len(d['dependency']['samples'][0]['allied_positions']),5)
        self.assertTrue(all(a['role']=='UNKNOWN' for a in d['dependency']['samples'][0]['allied_positions'] if a['champion'] in ('Ornn','Sejuani')))
        b=body();b['match']['metadata']['matchId']='KR_987';b['timeline']['metadata']['matchId']='KR_987';b['match']['info']['participants'][0]['teamPosition']='BOTTOM';self.assertEqual(self.detail(b)['role'],'UNKNOWN')
    def test_saved_plan_target_requires_unique_champion_role_and_records_missing_movement(self):
        b=body();del b['timeline']['info']['frames'][1]['participantFrames']['2']['position']
        plan=dict(validity='CURRENT',input=dict(patch='16.19',my_champion='Caitlyn',my_position='BOTTOM'),team_dependencies=dict(allies=[dict(champion='Sejuani',position='JUNGLE',initiative=['INITIATOR'],needs=[]),dict(champion='Ashe',position='JUNGLE',initiative=['INITIATOR'],needs=[])]))
        d=self.detail(b,plan=plan);targets=d['dependency']['plan_targets'];self.assertEqual(targets[0]['champion'],'Sejuani')
        self.assertEqual(targets[0]['samples'][1]['status'],'UNKNOWN');self.assertEqual(targets[0]['samples'][0]['status'],'RECORDED_MOVEMENT_ONLY')
        self.assertTrue(all(p['status']=='UNKNOWN' for p in targets[1]['samples']))
        self.assertEqual(d['dependency']['coordination'],'UNKNOWN');self.assertNotIn('PRIVATE_PUUID',json.dumps(targets))

    def test_private_path_parent_traversal_rejected_before_any_write(self):
        from coach_v1.postgame_match import PostgameStore
        escaped=Path(self.tmp.name)/'private'/'..'/'public'
        with self.assertRaises(ValueError):PostgameStore(escaped)
        self.assertFalse((Path(self.tmp.name)/'public').exists())

    def test_personal_collector_is_key_gated_and_private(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.personal_riot'))
        from coach_v1.personal_riot import PersonalRiotCollector
        called=[]
        c=PersonalRiotCollector(api_key='',transport=lambda *a:called.append(a))
        with self.assertRaises(ValueError):c.collect(riot_id='name#tag',server='KR',store=self.store)
        self.assertEqual(called,[])

if __name__=='__main__':unittest.main()

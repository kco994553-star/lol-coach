"""Synthetic mechanics only: no tactical knowledge or personal match evidence."""
import copy
import hashlib
import importlib.util
import unittest
from coach_v1.state import digest

POSITIONS=('TOP','JUNGLE','MID','BOTTOM','SUPPORT')

def source(kind='SYNTHETIC'):
    return dict(provider='SYNTHETIC' if kind=='SYNTHETIC' else 'RIOT_API',platform='KR',regional='ASIA',
        queue_id=420,map_id=11,tier='GOLD',patch='16.19',window_start=None,window_end=None,
        retrieved_at='2026-10-11T00:00:00Z',sample_kind=kind,endpoints=['MATCH_V5_MATCH','MATCH_V5_TIMELINE'])

def pair(i=0,minute=40):
    participants=[];pf={}
    for team,offset in ((100,0),(200,5)):
        for j,pos in enumerate(POSITIONS,1):
            pid=offset+j;participants.append(dict(participantId=pid,teamId=team,teamPosition=pos,
                championName='Champion'+str(j) if team==100 else 'Enemy'+str(j),puuid='PRIVATE_ID'))
            pf[str(pid)]=dict(position=dict(x=(0,10,20,30,1000)[j-1],y=(0,10,20,30,1000)[j-1]))
    metadata=dict(matchId='KR_PRIVATE_'+str(i))
    return dict(match=dict(metadata=metadata,info=dict(queueId=420,mapId=11,gameMode='CLASSIC',
        gameVersion='16.19.1',gameStartTimestamp=100000,gameDuration=minute*60,participants=participants)),
        timeline=dict(metadata=metadata,info=dict(frameInterval=60000,
            frames=[dict(timestamp=minute*60000,participantFrames=pf)])))

def annotation(p,verification='VERIFIED'):
    return dict(match_sha256=hashlib.sha256(p['match']['metadata']['matchId'].encode()).hexdigest(),
        timestamp_ms=p['timeline']['info']['frames'][0]['timestamp'],stage='LATE',
        stage_conditions=[dict(field='LONG_RESPAWN_RISK',value=True)],source_sha256='a'*64,
        source_pointer='/verified/phase/0',verification=verification)

def role(ref=None,layer='DEFAULT',location='SIDE_LANE',overrides=None):
    return dict(stage='LATE',layer=layer,subject='SELF',position='TOP',location=location,
        role='SYNTHETIC role',why='SYNTHETIC rationale',exceptions=['SYNTHETIC exception'],
        stage_conditions=[dict(field='LONG_RESPAWN_RISK',value=True)],overrides=overrides or [],statistics_ref=ref)

def trace(r,rule_id='base'):
    sources=[dict(kind='SYNTHETIC',patch='16.19',sha256='b'*64,url='https://example.org/synthetic')]
    output=dict(section='MOVEMENT',movement=[r],text='SYNTHETIC plan')
    return dict(rule_id=rule_id,status='APPLIED',condition='TRUE',review_state='REVIEWED',reasons=[],
        sources=sources,output=output,spec=dict(schema_version='pregame.rule.v3',patches=['16.19'],sources=sources,
        output=output),version='1',spec_sha256='c'*64)

def draft():
    return dict(patch='16.19',my_champion='Champion1',my_position='TOP',
        slots=[dict(side='ALLY',position=p,champion='Champion'+str(i)) for i,p in enumerate(POSITIONS,1)])

class MovementTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.movement'),'Q18 movement module absent')
        from coach_v1 import movement
        self.m=movement
    def dataset(self,annotations=True,kind='SYNTHETIC'):
        pairs=[pair(0),pair(1)]
        return self.m.build_movement_dataset(pairs,source=source(kind),
            phase_annotations=[annotation(p) for p in pairs] if annotations else None)
    def reference(self,d):
        c=next(c for c in d['cohorts'] if c['champion']=='Champion1' and c['stage']=='LATE')
        return dict(dataset_sha256=digest(d),cohort_id=c['id'])
    def test_coordinate_median_proxy_no_minute_phase_or_raw_identity(self):
        d=self.dataset(False)
        self.assertTrue(all(c['stage'] is None for c in d['cohorts']))
        c=next(c for c in d['cohorts'] if c['champion']=='Champion1')
        self.assertAlmostEqual(c['points'][0]['mean_distance'],(20**2+20**2)**.5)
        self.assertEqual(c['points'][0]['n'],2)
        self.assertNotIn('KR_PRIVATE',str(d));self.assertNotIn('participantId',str(d));self.assertNotIn('PRIVATE_ID',str(d))
        self.assertIn('KNOWN_ALLIES_MEDIAN_NOT_ACTUAL_MAIN_BODY',d['source']['limitations'])
    def test_missing_coordinates_not_zero_and_match_dedup(self):
        p=pair();del p['timeline']['info']['frames'][0]['participantFrames']['1']['position']
        d=self.m.build_movement_dataset([p,p],source=source())
        self.assertFalse(any(c['champion']=='Champion1' for c in d['cohorts']))
        self.assertEqual(d['samples']['synthetic_matches'],1)
        self.assertTrue(all(pt['n']==1 and not pt['visible'] for c in d['cohorts'] for pt in c['points']))
    def test_verified_stage_lineage_and_manual_unknown(self):
        d=self.dataset();self.assertTrue(any(c['stage']=='LATE' for c in d['cohorts']))
        self.assertEqual(d['source']['phase_annotation_sources'][0]['sha256'],'a'*64)
        ps=[pair(0),pair(1)]
        manual=self.m.build_movement_dataset(ps,source=source(),phase_annotations=[annotation(p,'MANUAL_UNVERIFIED') for p in ps])
        self.assertTrue(all(c['stage'] is None for c in manual['cohorts']))
        bad=[annotation(ps[0]),dict(annotation(ps[0]),stage='EARLY')]
        with self.assertRaises(ValueError):self.m.build_movement_dataset(ps,source=source(),phase_annotations=bad)
    def test_plan_requires_matching_stats_and_synthetic_isolation(self):
        d=self.dataset();t=trace(role(self.reference(d)))
        self.assertEqual(self.m.build_movement_plan([t],draft(),d)['status'],'UNKNOWN')
        self.assertEqual(self.m.build_movement_plan([t],draft(),d,test_mode=True)['status'],'KNOWN')
        self.assertEqual(self.m.build_movement_plan([trace(role())],draft(),d,test_mode=True)['status'],'UNKNOWN')
        bad=copy.deepcopy(t);bad['output']['movement'][0]['statistics_ref']['dataset_sha256']='d'*64
        self.assertEqual(self.m.build_movement_plan([bad],draft(),d,test_mode=True)['status'],'UNKNOWN')
        q=draft();q['patch']='16.18'
        self.assertEqual(self.m.build_movement_plan([t],q,d,test_mode=True)['status'],'UNKNOWN')
    def test_conflicts_preserved_override_only_higher_matching_layer(self):
        d=self.dataset();ref=self.reference(d);a=trace(role(ref));b=trace(role(ref,'CHAMPION','MAIN_GROUP'),'specific')
        c=self.m.build_movement_plan([a,b],draft(),d,test_mode=True)
        self.assertEqual(c['status'],'CONFLICTING');self.assertEqual(len(c['rules']),2)
        b['output']['movement'][0]['overrides']=['base']
        c=self.m.build_movement_plan([a,b],draft(),d,test_mode=True)
        self.assertEqual(c['status'],'KNOWN');self.assertEqual(c['rules'][0]['status'],'OVERRIDDEN')
        b['output']['movement'][0]['layer']='DEFAULT'
        self.assertEqual(self.m.build_movement_plan([a,b],draft(),d,test_mode=True)['status'],'CONFLICTING')
    def test_subject_binding_precision_privacy_and_no_mutation(self):
        d=self.dataset();t=trace(role(self.reference(d)));before=copy.deepcopy([t,d])
        q=draft();q['my_champion']='Other'
        self.assertEqual(self.m.build_movement_plan([t],q,d,test_mode=True)['status'],'UNKNOWN')
        self.m.build_movement_plan([t],draft(),d,test_mode=True);self.assertEqual([t,d],before)
        for change in (lambda x:x.update(raw_coordinates=[1,2]),lambda x:x['cohorts'][0]['points'][0].update(n=99),
                       lambda x:x['samples'].update(real_matches=2),lambda x:x.update(coaching_accuracy=.8)):
            bad=copy.deepcopy(d);change(bad)
            with self.assertRaises(ValueError):self.m.validate_movement_dataset(bad)

    def test_minute_only_cohort_cannot_support_stage_and_partial_rows_visible(self):
        d=self.dataset(False);c=next(c for c in d['cohorts'] if c['champion']=='Champion1')
        ref=dict(dataset_sha256=digest(d),cohort_id=c['id'])
        cell=self.m.build_movement_plan([trace(role(ref))],draft(),d,test_mode=True)
        self.assertEqual(cell['status'],'UNKNOWN')
        self.assertIn('MOVEMENT_STATISTICS_COHORT_MISMATCH',cell['rules'][0]['reasons'])
        known=self.dataset();ref=self.reference(known)
        t=trace(role(ref));t['output']['movement'].append(role(None,'TYPE'))
        cell=self.m.build_movement_plan([t],draft(),known,test_mode=True)
        self.assertEqual(cell['status'],'KNOWN')
        self.assertEqual([r['status'] for r in cell['rules']],['APPLIED','UNKNOWN'])

    def test_wide_interval_not_eligible_and_same_match_teams_not_independent(self):
        ps=[pair(0),pair(1)]
        ps[1]['timeline']['info']['frames'][0]['participantFrames']['1']['position']['x']=100
        d=self.m.build_movement_dataset(ps,source=source(),phase_annotations=[annotation(p) for p in ps])
        c=next(c for c in d['cohorts'] if c['champion']=='Champion1' and c['stage']=='LATE')
        self.assertFalse(c['points'][0]['visible'])
        cell=self.m.build_movement_plan([trace(role(dict(dataset_sha256=digest(d),cohort_id=c['id'])))],draft(),d,test_mode=True)
        self.assertEqual(cell['status'],'UNKNOWN')
        for p in ps:
            p['match']['info']['participants'][5]['championName']='Champion1'
        d=self.m.build_movement_dataset(ps,source=source())
        c=next(c for c in d['cohorts'] if c['champion']=='Champion1')
        self.assertEqual(c['points'][0]['n'],2)

    def test_real_source_exact_hash_and_unknown_higher_cannot_override(self):
        d=self.dataset(kind='REAL');t=trace(role(self.reference(d)))
        self.assertEqual(self.m.build_movement_plan([t],draft(),d)['status'],'UNKNOWN')
        t['sources'][0]['kind']='OFFICIAL'
        self.assertEqual(self.m.build_movement_plan([t],draft(),d)['status'],'KNOWN')
        higher=trace(role(self.reference(d),'CHAMPION','MAIN_GROUP',['base']),'higher')
        higher['status']='UNKNOWN'
        cell=self.m.build_movement_plan([t,higher],draft(),d,test_mode=True)
        self.assertEqual([r['status'] for r in cell['rules']],['APPLIED','UNKNOWN'])
        t['sources'][0]['sha256']=None
        self.assertEqual(self.m.build_movement_plan([t],draft(),d)['status'],'UNKNOWN')

    def test_late_requires_received_respawn_condition_and_bad_datasets_rejected(self):
        p=pair();a=annotation(p);a['stage_conditions']=[dict(field='FIRST_TURRET_DESTROYED',value=True)]
        with self.assertRaises(ValueError):self.m.build_movement_dataset([p],source=source(),phase_annotations=[a])
        d=self.dataset()
        for mutate in (lambda x:x['source'].update(raw={'puuid':'ID'}),
                       lambda x:x['cohorts'][0].update(condition_signature=[dict(field='LONG_RESPAWN_RISK',value=False)]),
                       lambda x:x['cohorts'][0]['points'][0].update(mean_distance=float('inf')),
                       lambda x:x['cohorts'][0]['points'][0].update(visible=False)):
            q=copy.deepcopy(d);mutate(q)
            with self.assertRaises(ValueError):self.m.validate_movement_dataset(q)

    def test_upstream_conflict_is_not_silently_downgraded(self):
        d=self.dataset();t=trace(role(self.reference(d)));t['status']='CONFLICTING'
        t['reasons']=['REVIEWED_OUTPUT_CONFLICT']
        c=self.m.build_movement_plan([t],draft(),d,test_mode=True)
        self.assertEqual(c['status'],'CONFLICTING')
        self.assertIn('REVIEWED_OUTPUT_CONFLICT',c['rules'][0]['reasons'])

    def test_jitter_frames_have_floor_bins_and_exact_annotation_times(self):
        ps=[pair(i,minute=8) for i in range(3)]
        for p in ps:
            frame=p['timeline']['info']['frames'][0]
            p['timeline']['info']['frames']=[dict(copy.deepcopy(frame),timestamp=t) for t in (300153,360211,420399)]
        ds=self.m.build_movement_dataset(ps,source=source(),phase_annotations=[annotation(p) for p in ps])
        self.assertTrue(ds['cohorts'],'ordinary jittered frames must produce cohorts')
        c=next(c for c in ds['cohorts'] if c['champion']=='Champion1' and c['stage'] is None)
        self.assertEqual([(pt['minute'],pt['n'],pt['visible']) for pt in c['points']],[(5,3,True),(6,3,True),(7,3,True)])
        c=next(c for c in ds['cohorts'] if c['champion']=='Champion1' and c['stage']=='LATE')
        self.assertEqual([pt['minute'] for pt in c['points']],[5])
        self.assertEqual(ds['source']['time_bin_policy']['frame_interval_ms'],60000)

    def test_latest_received_frame_in_bin_and_nonminute_interval_withheld(self):
        ps=[pair(i,minute=6) for i in range(3)]
        old_annotations=[]
        for p in ps:
            frame=p['timeline']['info']['frames'][0]
            old=dict(copy.deepcopy(frame),timestamp=300001)
            new=dict(copy.deepcopy(frame),timestamp=300153)
            new['participantFrames']['1']['position']['x']=100
            p['timeline']['info']['frames']=[old,new]
            old_annotations.append(annotation(p))
        d=self.m.build_movement_dataset(ps,source=source(),phase_annotations=old_annotations)
        self.assertTrue(d['cohorts'],'duplicate bins must select a received frame')
        self.assertTrue(all(c['stage'] is None for c in d['cohorts']))
        c=next(c for c in d['cohorts'] if c['champion']=='Champion1')
        self.assertEqual(c['points'][0]['n'],3)
        self.assertAlmostEqual(c['points'][0]['mean_distance'],(70**2+20**2)**.5)
        for p in ps:p['timeline']['info']['frameInterval']=30000
        self.assertEqual(self.m.build_movement_dataset(ps,source=source())['cohorts'],[])

    def test_provider_kind_parity_and_canonical_champion_names(self):
        d=self.dataset();d['source']['sample_kind']='REAL'
        d['samples']['real_matches']=2;d['samples']['synthetic_matches']=0
        with self.assertRaises(ValueError):self.m.validate_movement_dataset(d)
        p=pair();p['match']['info']['participants'][0]['championName']='PRIVATE_PLAYER_ID'
        self.assertEqual(self.m.build_movement_dataset([p],source=source())['cohorts'],[])
        d=self.dataset();d['source']['provider']='RIOT_API'
        with self.assertRaises(ValueError):self.m.validate_movement_dataset(d)

    def test_asymmetric_confidence_interval_and_private_tier_are_rejected(self):
        ps=[pair(i) for i in range(20)]
        d=self.m.build_movement_dataset(ps,source=source())
        q=copy.deepcopy(d);point=q['cohorts'][0]['points'][0]
        point['ci95']=dict(low=0,high=40)
        with self.assertRaises(ValueError):self.m.validate_movement_dataset(q)
        q=copy.deepcopy(d);q['source']['tier']='GOLD_PRIVATE_ID'
        for c in q['cohorts']:
            c['tier']='GOLD_PRIVATE_ID'
            c['id']=digest({k:c[k] for k in ('champion','position','patch','tier','stage','condition_signature')})
        with self.assertRaises(ValueError):self.m.validate_movement_dataset(q)
        q=copy.deepcopy(d);q['source']['patch']='PRIVATE_PATCH'
        for c in q['cohorts']:
            c['patch']='PRIVATE_PATCH'
            c['id']=digest({k:c[k] for k in ('champion','position','patch','tier','stage','condition_signature')})
        with self.assertRaises(ValueError):self.m.validate_movement_dataset(q)

if __name__=='__main__':unittest.main()

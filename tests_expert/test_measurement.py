"""Synthetic comparison mechanics; no real expert claims or gameplay receipts."""
import copy
import importlib.util
import math
import unittest
from coach_v1.movement import build_movement_dataset
from coach_v1.state import digest
from tests_pregame.test_movement import pair,source,annotation


def dataset(kind='REAL',count=20,verified=True,spread=False,patch='16.19'):
    # REAL metadata here exercises isolation gates only; all inputs remain authored fixtures.
    ps=[pair(i) for i in range(count)]
    for i,p in enumerate(ps):
        p['match']['info']['gameVersion']=patch+'.1'
        if spread:p['timeline']['info']['frames'][0]['participantFrames']['1']['position']['x']=i
    s=source(kind);s['patch']=patch
    return build_movement_dataset(ps,source=s,
        phase_annotations=[annotation(p,'VERIFIED' if verified else 'MANUAL_UNVERIFIED') for p in ps])


def claim(d,operator='LE',threshold=30,stage='LATE'):
    cohort=next(c for c in d['cohorts'] if c['champion']=='Champion1' and c['stage']==stage)
    return dict(champion='Champion1',position='TOP',stage=stage,measurable=True,
        paraphrase='SYNTHETIC numerical candidate; never a tactical recommendation.',patch_range='UNKNOWN',
        measurement=dict(kind='MOVEMENT_MEAN_DISTANCE',cohort_id=cohort['id'],patch='16.19',tier='GOLD',
            minute=40,operator=operator,threshold=threshold,criterion_source_url='https://example.org/synthetic-criterion',
            rationale='SYNTHETIC caller-selected numerical criterion',origin='MANUAL'))


class ExpertMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.expert_measurement'),'measurement consumer missing')
        from coach_v1.expert_measurement import compare_claim
        self.compare=compare_claim

    def test_le_and_ge_support_and_contradiction(self):
        d=dataset()
        for op,threshold,status in (('LE',30,'AGREES'),('LE',20,'DISAGREES'),('GE',20,'AGREES'),('GE',30,'DISAGREES')):
            with self.subTest(op=op,threshold=threshold):self.assertEqual(self.compare(claim(d,op,threshold),d)['status'],status)

    def test_inclusive_threshold_boundary(self):
        d=dataset();c=claim(d);p=next(c for c in d['cohorts'] if c['id']==claim(d)['measurement']['cohort_id'])['points'][0]
        c['measurement']['threshold']=p['ci95']['high']
        self.assertEqual(self.compare(c,d)['status'],'AGREES')
        c['measurement']['operator']='GE';c['measurement']['threshold']=p['ci95']['low']
        self.assertEqual(self.compare(c,d)['status'],'AGREES')

    def test_visible_interval_crossing_is_inconclusive_not_zero(self):
        d=dataset(spread=True);c=claim(d)
        point=next(co for co in d['cohorts'] if co['id']==c['measurement']['cohort_id'])['points'][0]
        self.assertTrue(point['visible']);c['measurement']['threshold']=point['mean_distance']
        r=self.compare(c,d);self.assertEqual(r['status'],'INSUFFICIENT')
        self.assertIn('CONFIDENCE_INTERVAL_CROSSES_THRESHOLD',r['reasons'])
        self.assertEqual(r['statistic']['n'],20)

    def test_no_typed_criterion_or_not_measurable_is_unmeasurable(self):
        d=dataset();c=claim(d);c['measurement']=None;c['paraphrase']='near the main body'
        self.assertEqual(self.compare(c,d)['status'],'UNMEASURABLE')
        c=claim(d);c['measurable']=False
        self.assertEqual(self.compare(c,d)['status'],'UNMEASURABLE')

    def test_missing_dataset_is_insufficient_without_zero_evidence(self):
        c=claim(dataset());r=self.compare(c,None)
        self.assertEqual(r['status'],'INSUFFICIENT');self.assertIsNone(r['statistic'])

    def test_synthetic_dataset_only_isolated_test_evidence(self):
        d=dataset('SYNTHETIC');c=claim(d)
        self.assertEqual(self.compare(c,d)['status'],'INSUFFICIENT')
        r=self.compare(c,d,test_mode=True);self.assertEqual(r['status'],'AGREES')
        self.assertEqual(r['statistic']['evidence_kind'],'TEST')
        self.assertIn('SYNTHETIC_TEST_NOT_REAL_EVIDENCE',r['statistic']['limitations'])

    def test_champion_role_stage_unknown_or_mismatch_withheld(self):
        d=dataset();c=claim(d)
        for key,wrong in (('champion','UNKNOWN'),('champion','Other'),('position','UNKNOWN'),('position','MID'),('stage','UNKNOWN'),('stage','MID')):
            q=copy.deepcopy(c);q[key]=wrong
            with self.subTest(key=key,value=wrong):self.assertEqual(self.compare(q,d)['status'],'INSUFFICIENT')

    def test_exact_patch_tier_minute_and_cohort_required(self):
        d=dataset();c=claim(d)
        for key,wrong in (('patch','16.18'),('tier','DIAMOND'),('minute',39),('cohort_id','b'*64)):
            q=copy.deepcopy(c);q['measurement'][key]=wrong
            with self.subTest(key=key):self.assertEqual(self.compare(q,d)['status'],'INSUFFICIENT')

    def test_mixed_patches_do_not_use_other_patch_cohort(self):
        d=dataset();other=dataset(patch='16.18')
        d['source']['patch']=None;d['cohorts'].extend(other['cohorts'])
        c=claim(d);self.assertEqual(self.compare(c,d)['status'],'AGREES')
        c['measurement']['cohort_id']=next(co['id'] for co in other['cohorts'] if co['champion']=='Champion1' and co['stage']=='LATE')
        self.assertEqual(self.compare(c,d)['status'],'INSUFFICIENT')

    def test_unverified_phase_or_minute_only_cohort_cannot_agree(self):
        d=dataset();c=claim(d);manual=dataset(verified=False)
        c['measurement']['cohort_id']=next(co['id'] for co in manual['cohorts'] if co['champion']=='Champion1')
        self.assertEqual(self.compare(c,manual)['status'],'INSUFFICIENT')
        no_lineage=copy.deepcopy(d);no_lineage['source']['phase_annotation_sources']=[]
        self.assertEqual(self.compare(claim(d),no_lineage)['status'],'INSUFFICIENT')

    def test_insufficient_n_and_invisible_interval_withheld(self):
        for d in (dataset(count=1),dataset(count=2,spread=True)):
            r=self.compare(claim(d),d);self.assertEqual(r['status'],'INSUFFICIENT');self.assertIsNone(r['statistic'])

    def test_invalid_dataset_and_invalid_numerical_criteria_rejected(self):
        d=dataset();c=claim(d);bad=copy.deepcopy(d);bad['source']['provider']='SYNTHETIC'
        self.assertEqual(self.compare(c,bad)['status'],'INSUFFICIENT')
        for key,wrong in (('threshold',math.nan),('threshold',True),('threshold',10**1000),('operator','NEAR'),('origin','AI'),
                          ('criterion_source_url','https://user:secret@example.org'),('minute',True)):
            q=copy.deepcopy(c);q['measurement'][key]=wrong
            with self.subTest(key=key):self.assertEqual(self.compare(q,d)['status'],'UNMEASURABLE')

    def test_bounded_safe_evidence_no_mutation_or_approval_conclusion(self):
        d=dataset();c=claim(d);before=copy.deepcopy([c,d]);r=self.compare(c,d)
        self.assertEqual([c,d],before);s=r['statistic']
        self.assertEqual(s['dataset_sha256'],digest(d));self.assertEqual(s['criterion'],c['measurement'])
        self.assertEqual(s['formula'],d['source']['formula_version']);self.assertEqual(s['evidence_kind'],'REAL_AGGREGATE')
        for forbidden in ('hashed_match_ids','participantId','puuid','PRIVATE_ID','USER_WEB','approved','causal'):
            self.assertNotIn(forbidden,str(r))
        self.assertIn('NUMERICAL_COMPARISON_NOT_TACTICAL_VALIDATION_OR_APPROVAL',s['limitations'])

    def test_large_source_metadata_withheld_without_echo(self):
        d=dataset();c=claim(d)
        d['source']['limitations'].extend(['BOUNDED_METADATA_'+'X'*1800]*100)
        r=self.compare(c,d)
        self.assertEqual(r['status'],'INSUFFICIENT');self.assertIsNone(r['statistic'])
        self.assertIn('SOURCE_METADATA_TOO_LARGE',r['reasons'])

if __name__=='__main__':unittest.main()

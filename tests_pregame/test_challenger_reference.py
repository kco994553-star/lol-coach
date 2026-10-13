"""Synthetic Challenger priority tests. No Riot requests or user approvals."""
import copy
import importlib
import unittest
from types import SimpleNamespace
from coach_v1.power_stats import build_power_dataset
from tests_pregame.test_power_stats import pair, source


def dataset(tier, sparse=False, patch='16.19'):
    src=source();src['tier']=tier;src['patch']=patch
    pairs=[pair(i,delta=100+i*10,patch=patch,minutes=(1,3) if sparse and i<23 else (1,2,3)) for i in range(24)]
    return build_power_dataset(pairs,source=src)


class ChallengerReferenceTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.challenger_reference'),'primary/auxiliary module missing')
        return importlib.import_module('coach_v1.challenger_reference')

    def request(self):return dict(champion='Champion',position='TOP',patch='16.19')

    def test_challenger_points_win_and_gm_fills_only_exact_missing_minutes(self):
        module=self.module();primary=dataset('CHALLENGER',True);aux=dataset('GRANDMASTER')
        rows={('16.19','CHALLENGER'):primary,('16.19','GRANDMASTER'):aux}
        result=module.select_challenger_reference(rows,self.request(),test_mode=True)
        self.assertEqual(result['summary']['primary_points'],6)
        self.assertEqual(result['summary']['auxiliary_points'],3)
        self.assertEqual(result['auxiliary']['use_policy'],'INSUFFICIENT_PRIMARY_ONLY')
        for series in result['series']:
            self.assertEqual([p['origin'] for p in series['points']],['PRIMARY','AUXILIARY','PRIMARY'])
            self.assertEqual(series['points'][1]['source_tier'],'GRANDMASTER')
            self.assertEqual(series['points'][1]['primary_precision']['status'],'UNKNOWN')
            self.assertEqual(series['points'][0]['primary_precision']['estimated_remaining_matches'],0)
        self.assertEqual(result['point_sources']['gold_delta:2']['tier'],'GRANDMASTER')
        self.assertNotEqual(result['primary']['dataset_digest'],result['auxiliary']['dataset_digest'])
        self.assertEqual(primary,rows[('16.19','CHALLENGER')])

    def test_auxiliary_mismatch_and_insufficient_points_stay_unknown(self):
        module=self.module();primary=dataset('CHALLENGER',True)
        for aux in (dataset('GRANDMASTER',patch='16.20'),dataset('GOLD')):
            result=module.select_challenger_reference({('16.19','CHALLENGER'):primary,
                (aux['source']['patch'],aux['source']['tier']):aux},self.request(),test_mode=True)
            self.assertEqual(result['summary']['auxiliary_points'],0)
            self.assertEqual(result['summary']['unknown_points'],3)
            self.assertTrue(result['summary']['needs_auxiliary_collection'])
            point=result['series'][0]['points'][1]
            self.assertEqual(point['status'],'UNKNOWN')
            self.assertIsNone(point['mean']);self.assertIsNone(point['primary_precision']['estimated_remaining_matches'])

    def test_unknown_champion_and_synthetic_production_gate_do_not_fall_through(self):
        module=self.module();rows={('16.19','CHALLENGER'):dataset('CHALLENGER')}
        self.assertEqual(module.select_challenger_reference(rows,self.request())['status'],'UNKNOWN')
        request=self.request();request['champion']='DifferentChampion'
        self.assertEqual(module.select_challenger_reference(rows,request,test_mode=True)['status'],'UNKNOWN')
        request=self.request();request['position']='MID'
        self.assertEqual(module.select_challenger_reference(rows,request,test_mode=True)['status'],'UNKNOWN')

    def test_auth_adapter_and_request_validation(self):
        module=self.module();data=dataset('CHALLENGER');rows={('16.19','CHALLENGER'):data}
        server=SimpleNamespace(test_mode=True,validated_power_datasets=lambda:rows,power_progress={})
        result=module.challenger_reference_response(server,self.request())
        self.assertEqual(result['status'],'KNOWN');self.assertEqual(result['summary']['auxiliary_points'],0)
        for request in ({**self.request(),'tier':'GOLD'},{**self.request(),'patch':None},{**self.request(),'champion':'<script>'}):
            with self.assertRaises(ValueError):module.challenger_reference_response(server,request)

    def test_primary_future_sample_requirement_is_not_erased_by_auxiliary(self):
        module=self.module();src=source();src['tier']='CHALLENGER'
        primary=build_power_dataset([pair(i,delta=100+i*10,minutes=(1,)) for i in range(3)],source=src)
        auxiliary_source=source();auxiliary_source['tier']='GRANDMASTER'
        auxiliary=build_power_dataset([pair(i,delta=100+i*10,minutes=(1,)) for i in range(24)],source=auxiliary_source)
        result=module.select_challenger_reference({('16.19','CHALLENGER'):primary,
            ('16.19','GRANDMASTER'):auxiliary},self.request(),test_mode=True)
        point=result['series'][0]['points'][0]
        self.assertEqual(point['origin'],'AUXILIARY')
        self.assertEqual(point['primary_precision']['estimated_remaining_matches'],15)
        self.assertEqual(point['primary_precision']['estimated_required_matches'],18)
        self.assertEqual(result['summary']['estimated_remaining_primary_matches'],15)


if __name__=='__main__':unittest.main()

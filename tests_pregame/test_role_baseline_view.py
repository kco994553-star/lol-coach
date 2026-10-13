import copy
import importlib
import unittest
from coach_v1.power_accumulator import PowerAccumulator
from coach_v1.collection_progress import progress_response
from tests_pregame.test_power_stats import pair,source

class BaselineViewTests(unittest.TestCase):
    def setUp(self):
        self.acc=PowerAccumulator()
        self.data=self.acc.add_pairs([pair(i,delta=100+30*i) for i in range(18)],source=source())
        self.progress=self.acc.progress('16.19','GOLD')
    def view(self,data=None,progress=None):
        module=importlib.import_module('coach_v1.role_baseline_view')
        return module.role_baseline_curves_from_validated(data or self.data,progress or self.progress)
    def test_reconstructed_means_and_cluster_intervals_equal_original_records(self):
        expected=self.acc.progress('16.19','GOLD',include_points=True)
        actual=self.view()
        for role,wanted in zip(actual['roles'],expected['roles']):
            self.assertEqual(role['position'],wanted['position'])
            for curve,w in zip(role['curves'],wanted['role_baseline']['curves']):
                self.assertEqual(curve['metric'],w['metric'])
                for point,p in zip(curve['points'],w['points']):
                    for key in ('minute','match_count','participant_count','status','estimated_remaining_matches'):
                        self.assertEqual(point[key],p[key])
                    self.assertAlmostEqual(point['mean'],p['mean'],places=10)
                    self.assertAlmostEqual(point['ci95']['low'],p['ci95']['low'])
                    self.assertAlmostEqual(point['ci95']['high'],p['ci95']['high'])
    def test_missing_or_conflicting_population_mean_stays_unknown(self):
        data=copy.deepcopy(self.data)
        for cohort in data['cohorts']:
            if cohort['comparison']=='ROLE_POPULATION' and cohort['position']=='TOP':
                for point in cohort['points']:point['reference_mean']+=1
                break
        self.assertTrue(any(p['status']=='UNKNOWN' for c in self.view(data)['roles'][0]['curves'] for p in c['points']))
        data['cohorts']=[c for c in data['cohorts'] if c['comparison']!='ROLE_POPULATION']
        self.assertTrue(all(p['mean'] is None and p['status']=='UNKNOWN' for r in self.view(data)['roles'] for c in r['curves'] for p in c['points']))
    def test_missing_baseline_precision_is_empty_unknown(self):
        view=self.view(progress=progress_response(self.data))
        self.assertTrue(all(r['status']=='UNKNOWN' and r['curves']==[] for r in view['roles']))
    def test_inputs_unchanged_and_no_individual_records_exported(self):
        before=copy.deepcopy((self.data,self.progress));view=self.view()
        self.assertEqual((self.data,self.progress),before)
        self.assertIsNone(view['coaching_accuracy'])
        self.assertNotIn('hashed_match_ids',str(view));self.assertNotIn('precision_evidence',str(view))

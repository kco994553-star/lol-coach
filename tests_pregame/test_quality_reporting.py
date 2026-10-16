import importlib.util
import unittest


class QualityReportingTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.report_quality_pilot'),'quality report missing')
        from scripts import report_quality_pilot
        return report_quality_pilot

    def test_role_rate_is_never_substituted_for_matchup_absolute_gold(self):
        module=self.module()
        data={'cohorts':[dict(champion='Ahri',position='MID',opponent_champion=None,comparison='ROLE_POPULATION',metric='gold_delta',patch='16.20',tier='CHALLENGER',points=[dict(minute=10,n=100,mean=15,visible=True)])]}
        result=module.matchup_bins(data,'Ahri','Zed','MID')
        self.assertEqual(result['status'],'UNKNOWN_NO_MATCHUP_COHORT')
        self.assertEqual(result['points'],[])

    def test_existing_precision_hold_and_unknown_missing_denominator_are_preserved(self):
        module=self.module()
        point=dict(minute=10,n=5,mean=709.2,visible=False,omission_reason='CI_TOO_WIDE')
        data={'cohorts':[dict(champion='Caitlyn',position='BOTTOM',opponent_champion='Ezreal',comparison='MATCHUP',metric='gold_delta',patch='16.20',tier='CHALLENGER',points=[point])]}
        result=module.matchup_bins(data,'Caitlyn','Ezreal','BOTTOM')
        self.assertEqual(result['status'],'EXISTING_AGGREGATE_ONLY')
        self.assertFalse(result['points'][0]['visible'])
        self.assertIsNone(result['missing_n'])
        self.assertEqual(result['unit'],'GOLD_ABSOLUTE_DIFFERENCE_SAMPLED_MINUTE_BIN')
        self.assertEqual(result['points'][0]['mean'],709.2)


if __name__=='__main__':unittest.main()

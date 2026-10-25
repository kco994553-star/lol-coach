"""Future cohort admission only; all-tier amendment 2026-10-25; old fixtures and archives stay valid."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MasterStatisticsPolicyTests(unittest.TestCase):
 def test_future_policy_allows_ten_leaf_tiers_but_not_aggregate_or_unknown(self):
  from coach_v1 import riot_collection_policy as p
  self.assertTrue(hasattr(p,'validate_new_statistics_tier'),'missing future admission guard')
  for tier in ['IRON','BRONZE','SILVER','GOLD','PLATINUM','EMERALD','DIAMOND','MASTER','GRANDMASTER','CHALLENGER']:self.assertEqual(p.validate_new_statistics_tier(tier),tier)
  for tier in ['ALL','MASTER_PLUS','UNKNOWN',None]:
   with self.assertRaises(ValueError):p.validate_new_statistics_tier(tier)
 def test_unknown_tier_cli_stops_before_key_or_network_and_does_not_relabel_data(self):
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'power.json';output.write_text('prior evidence')
   env=dict(os.environ);env.pop('RIOT_API_KEY',None)
   r=subprocess.run([sys.executable,'scripts/collect_power_stats.py','--output',str(output),'--tier','UNKNOWN'],cwd=ROOT,env=env,capture_output=True,text=True)
   self.assertEqual(r.returncode,2);self.assertIn('invalid choice',r.stderr);self.assertEqual(output.read_text(),'prior evidence')
 def test_manual_workflow_and_resolver_accept_master_without_new_schedule(self):
  workflow=(ROOT/'.github/workflows/riot-power-collection.yml').read_text()
  self.assertIn('options: [IRON, BRONZE, SILVER, GOLD, PLATINUM, EMERALD, DIAMOND, MASTER, GRANDMASTER, CHALLENGER]',workflow)
  self.assertEqual(workflow.count("cron: '17 3 * * *'"),1)
  resolver=(ROOT/'scripts/resolve_riot_collection.py').read_text();self.assertIn('choices=FUTURE_STATISTICS_TIERS',resolver)
  policy=json.loads((ROOT/'config/riot_collection_policy.json').read_text());self.assertEqual(policy['future_statistics']['participant_rank_at_match_time'],'UNVERIFIED')
 def test_amendment_and_private_artifact_boundaries_preserve_guards(self):
  workflow=(ROOT/'.github/workflows/riot-power-collection.yml').read_text()
  public=workflow.split('- name: Retain public-safe aggregate for seven days',1)[1].split('- name: Refresh private anonymous sufficient state',1)[0]
  private=workflow.split('- name: Refresh private anonymous sufficient state',1)[1]
  self.assertIn('power-output/*.json',public)
  self.assertNotIn('matchup-results',public);self.assertNotIn('result-completeness',public)
  self.assertIn('power-state/matchup-results.json.gz',private)
  self.assertIn('power-state/result-completeness.json',private)
  self.assertIn('retention-days: 90',private);self.assertIn('retention-days: 7',public)
  for guard in ("github.ref == 'refs/heads/main'",'persist-credentials: false','--max-matches 300 --max-requests 650 --max-players 40 --max-pages 1 --max-retries 2 --deadline-seconds 900',"if: steps.policy.outputs.enabled == 'true'"):
   self.assertIn(guard,workflow)
  policy=json.loads((ROOT/'config/riot_collection_policy.json').read_text())
  self.assertEqual(policy['future_statistics']['default_browser_scope'],'MASTER_PLUS')
  self.assertEqual(len(policy['future_statistics']['allowed_seed_tiers']),10)
  self.assertEqual(policy['key_valid_until'],'2026-10-16T10:16:49Z')
  self.assertIn('2026-10-25',(ROOT/'docs/gameplan-content/all-tier-collection-v1.md').read_text())
if __name__=='__main__':unittest.main()

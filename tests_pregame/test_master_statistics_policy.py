"""Future cohort admission only; old lower-tier fixtures and archives stay valid."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MasterStatisticsPolicyTests(unittest.TestCase):
 def test_future_policy_allows_master_plus_but_not_lower_or_unknown(self):
  from coach_v1 import riot_collection_policy as p
  self.assertTrue(hasattr(p,'validate_new_statistics_tier'),'missing future admission guard')
  for tier in ['MASTER','GRANDMASTER','CHALLENGER']:self.assertEqual(p.validate_new_statistics_tier(tier),tier)
  for tier in ['DIAMOND','GOLD','UNKNOWN',None]:
   with self.assertRaises(ValueError):p.validate_new_statistics_tier(tier)
 def test_low_tier_cli_stops_before_key_or_network_and_does_not_relabel_data(self):
  with tempfile.TemporaryDirectory() as tmp:
   output=Path(tmp)/'power.json';output.write_text('prior evidence')
   env=dict(os.environ);env.pop('RIOT_API_KEY',None)
   r=subprocess.run([sys.executable,'scripts/collect_power_stats.py','--output',str(output),'--tier','DIAMOND'],cwd=ROOT,env=env,capture_output=True,text=True)
   self.assertEqual(r.returncode,2);self.assertIn('MASTER_PLUS_REQUIRED',r.stderr);self.assertEqual(output.read_text(),'prior evidence')
 def test_manual_workflow_and_resolver_accept_master_without_new_schedule(self):
  workflow=(ROOT/'.github/workflows/riot-power-collection.yml').read_text()
  self.assertIn('options: [CHALLENGER, GRANDMASTER, MASTER]',workflow)
  resolver=(ROOT/'scripts/resolve_riot_collection.py').read_text();self.assertIn("'CHALLENGER','GRANDMASTER','MASTER'",resolver)
  policy=json.loads((ROOT/'config/riot_collection_policy.json').read_text());self.assertEqual(policy['future_statistics']['participant_rank_at_match_time'],'UNVERIFIED')
if __name__=='__main__':unittest.main()

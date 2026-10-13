"""Anonymous timeline signal tests; SYNTHETIC input is not tactical approval."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


def observation(number=1):
    positions=[];resources=[]
    for minute in (0,1,2,12,22):
        positions.append(dict(minute=minute,timestamp_ms=minute*60000,own_position=dict(x=1000+minute*10,y=2000),allied_jungle_position=dict(x=1200,y=2000),allied_support_position=dict(x=900,y=2000)))
        resources.append(dict(minute=minute,timestamp_ms=minute*60000,gold=500+minute*100,xp=minute*200,cs=minute*6))
    return dict(match_sha256=f'{number:064x}',champion='Caitlyn',role='BOTTOM',patch='16.19',resources=resources,movement=positions,
        contexts=[dict(kind='DEATH',minute=1.1,event_type='CHAMPION_KILL'),dict(kind='OBJECTIVE',minute=12.1,event_type='ELITE_MONSTER_KILL'),dict(kind='TEAM_WARD',minute=1.2,event_type='WARD_PLACED')])


class ReferenceCaseTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.pro_reference_cases'),'reference cases module absent')
        from coach_v1 import pro_reference_cases
        return pro_reference_cases
    def data(self,observations=None):return self.module().build_reference_cases(observations or [observation(i) for i in (1,2,3)],roster_sha256='a'*64,retrieved_at='2026-10-13T00:00:00Z',sample_kind='SYNTHETIC')
    def test_operational_stages_grid_scope_no_raw_id_coords_or_tactical_verification(self):
        d=self.data();self.assertEqual(d['schema_version'],'postgame.pro-reference-cases.v1')
        self.assertEqual({c['stage'] for c in d['cohorts']},{'OP_OPENING','OP_TRANSITION','OP_20_PLUS'})
        self.assertTrue(all(c['tactical_phase']=='UNKNOWN' for c in d['cohorts']))
        self.assertTrue(all(c['match_n']==3 for c in d['cohorts']))
        self.assertNotIn('match_sha256',json.dumps(d));self.assertNotIn('own_position',json.dumps(d));self.assertNotIn('participantId',json.dumps(d))
        self.assertEqual(d['sample_counts']['unique_matches'],3)
    def test_building_transition_is_operational_not_verified_phase(self):
        observations=[observation(i) for i in (1,2,3)]
        for o in observations:o['contexts'].append(dict(kind='OBJECTIVE',minute=.5,event_type='BUILDING_KILL'))
        d=self.data(observations);opening=next(c for c in d['cohorts'] if c['stage']=='OP_OPENING');transition=next(c for c in d['cohorts'] if c['stage']=='OP_TRANSITION')
        self.assertEqual(opening['sample_n'],3);self.assertEqual(transition['sample_n'],9)
        self.assertEqual(transition['tactical_phase'],'UNKNOWN')
    def test_aliases_dedup_and_missing_positions_do_not_invent_zero_or_context(self):
        obs=[observation(1),observation(1)];obs[1]=copy.deepcopy(obs[0]);d=self.data(obs)
        self.assertEqual(d['sample_counts']['unique_matches'],1)
        self.assertTrue(all(c['location']['status']=='UNKNOWN' for c in d['cohorts']))
        obs=[observation(i) for i in (1,2,3)]
        for o in obs:
            for p in o['movement']:p['own_position']=None;p['allied_jungle_position']=None
        d=self.data(obs);self.assertTrue(all(c['location']['grid_counts']==[] for c in d['cohorts']))
        death=next(s for c in d['cohorts'] for s in c['signals'] if s['type']=='PRE_DEATH_CONTEXT')
        distance=next(m for m in death['metrics'] if m['metric']=='distance_to_allied_jungle')
        self.assertEqual(distance['status'],'UNKNOWN');self.assertIsNone(distance['mean'])
    def test_q16_event_windows_adjacent_resources_no_hidden_signals_or_blame(self):
        d=self.data();signals=[s for c in d['cohorts'] for s in c['signals']]
        self.assertTrue({'PRE_DEATH_CONTEXT','OBJECTIVE_EVENT_CONTEXT','TEAM_WARD_PLACEMENT','ADJACENT_RESOURCE_GAIN'}<={s['type'] for s in signals})
        for c in d['cohorts']:
            gain=next((s for s in c['signals'] if s['type']=='ADJACENT_RESOURCE_GAIN'),None)
            if gain:self.assertEqual(gain['event_count'],6 if c['stage']=='OP_OPENING' else 0)
        self.assertIn('WAVE_STATE_UNKNOWN',d['limitations']);self.assertIn('SKILL_AND_COOLDOWN_STATE_UNKNOWN',d['limitations'])
        self.assertTrue(all(s['inference']=='RECORDED_SIGNAL_NON_CAUSAL' for s in signals));self.assertNotIn('win',d)
    def test_stale_event_frame_over_90_seconds_remains_unknown(self):
        obs=[observation(i) for i in (1,2,3)]
        for o in obs:o['contexts']=[dict(kind='DEATH',minute=7,event_type='CHAMPION_KILL')]
        d=self.data(obs);death=next(s for c in d['cohorts'] for s in c['signals'] if s['type']=='PRE_DEATH_CONTEXT' and s['event_count']>0)
        self.assertEqual(death['unknown_context_events'],3)
        self.assertTrue(all(m['status']=='UNKNOWN' for m in death['metrics']))
    def test_strict_validator_rejects_privacy_fields_and_forged_ci(self):
        m=self.module();d=self.data();bad=copy.deepcopy(d);bad['puuid']='PRIVATE'
        with self.assertRaises(ValueError):m.validate_reference_cases(bad)
        bad=copy.deepcopy(d);bad['cohorts'][0]['tactical_phase']='VERIFIED'
        with self.assertRaises(ValueError):m.validate_reference_cases(bad)
        bad=copy.deepcopy(d);bad['cohorts'][0]['location']['coordinates']['x']['mean']=999999
        with self.assertRaises(ValueError):m.validate_reference_cases(bad)
    def test_public_export_safe_receipt_strips_ids_and_private_paths(self):
        m=self.module();receipt=dict(status='READY',reason=None,request_count=4,unique_recorded_matches=3,roster_sha256='a'*64,selections=[dict(primary_player='PUBLIC_ROSTER_NAME',selected_player='other',status='SELECTED')],failed_accounts=['player:private'],privacy='LOCAL_PRIVATE')
        safe=m.public_collection_receipt(receipt)
        self.assertNotIn('PUBLIC_ROSTER_NAME',json.dumps(safe));self.assertNotIn('player:private',json.dumps(safe))
        self.assertEqual(safe['selection_counts']['selected'],1)

class PublicExportTests(unittest.TestCase):
    def test_cli_emits_safe_initial_receipt_and_empty_cases_without_key(self):
        import contextlib
        import io
        from unittest.mock import patch
        from scripts import collect_pro_reference as cli
        from coach_v1.pro_reference import ProReferenceCollector
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/'public';private=Path(td)/'private'/'pro-reference'
            collector=ProReferenceCollector(api_key='')
            text=io.StringIO()
            with patch.object(cli,'ProReferenceCollector',return_value=collector),contextlib.redirect_stdout(text):
                code=cli.main(['--private-directory',str(private),'--public-output-directory',str(output)])
            self.assertEqual(code,2)
            receipt=json.loads((output/'collection-receipt.json').read_text())
            self.assertEqual(receipt['request_count'],0);self.assertNotIn('failed_accounts',receipt)
            cases=json.loads((output/'reference-cases.json').read_text());self.assertEqual(cases['sample_counts']['unique_matches'],0)
            self.assertFalse(private.exists());self.assertNotIn('accounts.json',text.getvalue())
    def test_public_receipt_masks_unrecognized_failure_text(self):
        from coach_v1.pro_reference_cases import public_collection_receipt
        receipt=public_collection_receipt(dict(status='BLOCKED_EXTERNAL',reason='PRIVATE_PUUID_SENSITIVE',roster_sha256='a'*64))
        self.assertNotIn('PRIVATE_PUUID_SENSITIVE',json.dumps(receipt))
        self.assertEqual(receipt['reason'],'UNKNOWN_COLLECTION_REASON')

    def test_public_export_rejects_raw_directory_overlap(self):
        from coach_v1.pro_reference_cases import validate_public_directory
        with tempfile.TemporaryDirectory() as td:
            private=Path(td)/'private'/'pro-reference'
            for output in (private,Path(td),private/'public',Path(td)/'private'/'..'/'public'):
                with self.assertRaises(ValueError):validate_public_directory(output,private)

if __name__=='__main__':unittest.main()

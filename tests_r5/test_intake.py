import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from coach_intake.audit import inspect
from coach_intake.io import strict_json,sha,write_new,fetch,GAME_URL
from coach_intake.__main__ import acquire

def sample():return dict(activePlayer={'championStats':{'currentHealth':5,'maxHealth':10},'currentGold':0,'level':1},allPlayers=[{'summonerName':'PRIVATE_NAME'}],events={'Events':[{'EventID':0,'EventName':'GameStart','EventTime':0}]},gameData={'gameTime':1})
def raw(data=None):return json.dumps(sample() if data is None else data).encode()

class IntakeTests(unittest.TestCase):
    def test_sample_never_promoted(self):
        r=inspect(raw(),'DOCUMENTATION_SAMPLE',sha(raw()))
        self.assertTrue(r['integrity_hash_matched']);self.assertFalse(r['source_authenticity_verified'])
        self.assertFalse(r['game_end_verified']);self.assertFalse(r['coaching_enabled'])
        self.assertTrue(all(not f['decision_eligible'] for f in r['raw_facts']))
        self.assertNotIn('PRIVATE_NAME',json.dumps(r));self.assertEqual(r['player_count'],1)
    def test_hash_tamper_rejected(self):
        with self.assertRaises(ValueError):inspect(raw(),expected_sha='0'*64)
    def test_ambiguous_and_nonfinite_json_rejected(self):
        for s in ('{"a":1,"a":2}','{"a":NaN}','{"a":1e999}','{"a":Infinity}'):
            with self.assertRaises(ValueError):strict_json(s)
    def test_missing_null_wrong_type_are_distinct(self):
        r=inspect(raw({'activePlayer':None,'allPlayers':'bad'}))
        self.assertEqual(r['sections']['activePlayer'],'NULL');self.assertEqual(r['sections']['allPlayers'],'WRONG_TYPE');self.assertEqual(r['sections']['gameData'],'MISSING')
    def test_zero_is_not_missing_and_bool_is_not_numeric(self):
        p=sample();p['gameData']['gameTime']=0;p['activePlayer']['currentGold']=False
        r=inspect(raw(p));self.assertEqual(r['raw_facts'][0]['value'],0);self.assertEqual(r['raw_facts'][3]['state'],'INVALID')
    def test_future_end_and_duplicate_event_do_not_verify_end(self):
        p=sample();p['events']['Events'].append({'EventID':0,'EventName':'GameEnd','EventTime':999})
        r=inspect(raw(p));self.assertIn('EVENT_AFTER_SNAPSHOT',r['issues']);self.assertIn('EVENT_ID_INVALID_OR_DUPLICATE',r['issues']);self.assertEqual(r['game_end_markers_observed'],1);self.assertFalse(r['game_end_verified'])
    def test_invalid_field_cannot_leak_identifier(self):
        p=sample();p['activePlayer']['currentGold']={'name':'PRIVATE_NAME'}
        r=inspect(raw(p));self.assertNotIn('PRIVATE_NAME',json.dumps(r))
    def test_exclusive_write_preserves_prior(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'one';write_new(p,b'first')
            with self.assertRaises(FileExistsError):write_new(p,b'second')
            self.assertEqual(p.read_bytes(),b'first');self.assertEqual(len(list(Path(td).iterdir())),1)
    def test_fixed_endpoint_and_ca_gate(self):
        with self.assertRaises(ValueError):fetch('https://example.com',100,1)
        with self.assertRaises(ValueError):fetch(GAME_URL,100,1)
    def test_acquire_reports_failure_without_fake_receipt(self):
        with tempfile.TemporaryDirectory() as td,patch('coach_intake.__main__.fetch',side_effect=ConnectionRefusedError):
            p=Path(td)/'run';r=acquire(p,'sample',1000,1)
            self.assertFalse(r['passed']);self.assertEqual(r['error_code'],'ENDPOINT_UNAVAILABLE');self.assertFalse((p/'receipt.json').exists());self.assertTrue((p/'status.json').exists())
    def test_acquire_preserves_raw_and_receipt(self):
        with tempfile.TemporaryDirectory() as td,patch('coach_intake.__main__.fetch',return_value=raw()):
            p=Path(td)/'run';r=acquire(p,'sample',1000,1)
            self.assertTrue(r['passed']);self.assertEqual((p/'raw.json').read_bytes(),raw());self.assertEqual(json.loads((p/'receipt.json').read_text())['evidence_kind'],'DOCUMENTATION_SAMPLE')

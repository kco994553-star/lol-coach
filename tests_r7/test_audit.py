import copy
import json
import unittest
from pathlib import Path
from coach_audit.extraction import extract
from coach_audit.sufficiency import assess_information, next_acquisition
from coach_audit.replay import compare_player_state, evaluate_ordered
from coach_v1.models import ReviewInput
from coach_v1.engine import run_review
from tests_r3.helpers import fixture, observation

ROOT = Path(__file__).resolve().parents[1]
RAW = (ROOT/'evidence/r5/official-sample-retry-20261004/raw.json').read_bytes()


def altered(**stats):
    p = json.loads(RAW)
    p['activePlayer']['championStats'].update(stats)
    return json.dumps(p).encode()


def bridge_payload(raw):
    # Explicitly synthetic end-to-end mechanics test, not a real-data adapter.
    result = extract(raw)
    payload = fixture()
    by = {r['field']: r for r in result['raw']}
    for field in ('active_health', 'active_max_health'):
        payload['observations'].append(observation(field, field, by[field]['value']))
    row = result['derived'][0]
    payload['observations'].append(observation('ratio', 'health_fraction', row['value'], kind='DERIVED',
        lineage_ids=row['lineage'], formula=row['formula'], formula_version=row['formula_version'],
        missing_reason='INVALID_HEALTH_INPUT' if row['value'] is None else None))
    for a in payload['actions']:
        a['required_keys'].append('self:health_fraction')
    return payload


def run(payload):
    return run_review(ReviewInput.model_validate(payload), allow_synthetic=True)


class ExtractionTests(unittest.TestCase):
    def test_document_reference_and_no_promotion(self):
        ref = json.loads((ROOT/'fixtures/r7/documentation_reference.json').read_text())
        out = extract(RAW, source_kind='DOCUMENTATION_SAMPLE', expected_sha=ref['source_sha256'])
        actual = {r['field']:{k:r[k] for k in ('value','state')} for r in out['raw']}
        self.assertEqual(actual,ref['expected'])
        self.assertIsNone(out['derived'][0]['value'])
        self.assertFalse(out['coaching_enabled']);self.assertFalse(out['strategic'])
        self.assertIsNone(out['player_information_state'])
        self.assertNotIn('Riot Tuxedo',json.dumps(out))

    def test_mismatched_source_hash_rejected(self):
        with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):
            extract(RAW,expected_sha='0'*64)

    def test_zero_health_is_not_missing_and_zero_capacity_not_fraction(self):
        self.assertEqual(extract(altered(currentHealth=0,maxHealth=100))['derived'][0]['value'],0)
        for hp,cap in ((0,0),(200,100),(-1,100),(True,100),(None,100)):
            self.assertIsNone(extract(altered(currentHealth=hp,maxHealth=cap))['derived'][0]['value'])

    def test_wrong_container_null_missing_and_empty_are_distinct(self):
        p=json.loads(RAW)
        for players,expected in ((None,'NULL_ANCESTOR'),([], 'MISSING'),([None],'NULL_ANCESTOR'),([{'position':None}],'NULL'),([{'position':0}],'INVALID')):
            p['allPlayers']=players
            role=next(r for r in extract(json.dumps(p).encode())['raw'] if r['field']=='role_label')
            self.assertEqual(role['state'],expected)

    def test_metadata_not_readiness_or_coordinates(self):
        p=json.loads(RAW);p['allPlayers'][0]['position']='MIDDLE'
        out=extract(json.dumps(p).encode());facts={r['field']:r for r in out['raw']}
        self.assertEqual(facts['role_label']['value'],'MIDDLE')
        for absent in ('champion_position','ultimate_ready','wave_state','summoner_ready'):
            self.assertNotIn(absent,facts)
        self.assertTrue(all(not f['decision_eligible'] for f in out['raw']+out['derived']))


class SufficiencyTests(unittest.TestCase):
    def test_information_growth_and_own_feasibility_required(self):
        empty=assess_information({})
        for earlier,later in zip(empty,empty[1:]):
            self.assertLess(set(earlier['required_keys']),set(later['required_keys']))
        known={k:'KNOWN' for k in empty[0]['required_keys']}
        partial=assess_information(known)
        self.assertEqual(partial[0]['information_sufficiency'],'PROFILE_REQUIREMENTS_MET')
        self.assertIn('THREAT',partial[-1]['lower_commitment_candidates'])
        self.assertEqual(partial[-1]['engine_action_type'],'CHASE')
        self.assertTrue(all(r['permission']=='NOT_EVALUATED' for r in partial))

    def test_uncertainty_or_missing_cannot_strengthen(self):
        fields={k:'KNOWN' for k in assess_information({})[-1]['required_keys']}
        before=assess_information(fields)
        for status in ('UNKNOWN','STALE','CONDITIONAL','CONFLICTING'):
            changed=dict(fields);changed['return_path']=status
            after=assess_information(changed)
            self.assertTrue(all(len(a['missing_information']) >= len(b['missing_information']) for a,b in zip(after,before)))
            self.assertTrue(all(a['unlock_conditions'] for a in after))

    def test_cheaper_verified_source_avoids_vision(self):
        out=next_acquisition({'STRUCTURED':dict(available=True,verified_sufficient=True,decision_eligible=True), 'SNAPSHOT_VISION':dict(available=True)})
        self.assertEqual(out,dict(source='STRUCTURED',status='REUSE',invoke=False))

    def test_unverified_source_not_reused_and_vision_selective(self):
        out=next_acquisition({'STRUCTURED':dict(available=True,attempted=True,verified_sufficient=True,decision_eligible=False), 'SNAPSHOT_VISION':dict(available=True)})
        self.assertEqual(out['source'],'SNAPSHOT_VISION');self.assertTrue(out['invoke'])
        self.assertEqual(next_acquisition({})['status'],'EVIDENCE_GAP')


class StateDecisionTests(unittest.TestCase):
    def test_synthetic_extraction_to_existing_state_engine(self):
        payload=bridge_payload(altered(currentHealth=50,maxHealth=100))
        out=run(payload)
        field=next(f for f in out['snapshot']['fields'] if f['key']=='self:health_fraction')
        self.assertEqual((field['value'],field['state']),(0.5,'KNOWN'))
        self.assertEqual(out['evaluations'][0]['sufficiency'],'SUFFICIENT')
        self.assertIsNone(out['recommendation'])

    def test_invalid_or_hidden_lineage_blocks_strategic_promotion(self):
        p=bridge_payload(RAW)
        self.assertEqual(run(p)['evaluations'][0]['sufficiency'],'INSUFFICIENT')
        p=bridge_payload(altered(currentHealth=50,maxHealth=100))
        p['observations'][1]['perspective']='OBSERVER'
        self.assertEqual(run(p)['evaluations'][0]['sufficiency'],'INSUFFICIENT')

    def test_future_and_ground_truth_do_not_change_player_decision(self):
        p=bridge_payload(altered(currentHealth=50,maxHealth=100));a=run(p)
        p['observations'] += [observation('hidden','jungle','nearby',perspective='OBSERVER'),observation('later','jungle','nearby',event_time_ms=2000)]
        p['outcome_note']='Lost fight later; must not rewrite the earlier decision.'
        b=run(p)
        for key in ('evaluations','dominance','alternatives'):
            self.assertEqual(a[key],b[key])
        self.assertFalse(b['outcome']['used_for_decision'])

    def test_reference_gate_truth_is_never_reference_substitute(self):
        case=json.loads((ROOT/'fixtures/r7/representative_set.json').read_text())['cases'][0]
        case['reference']['GROUND_TRUTH_STATE']=dict(status='ESTABLISHED',fields={'enemy':'near'},evidence_refs=['observer-frame'])
        self.assertEqual(compare_player_state(case,{'enemy':'near'})['denominator'],0)
        case['reference']['PLAYER_INFORMATION_STATE']=dict(status='ESTABLISHED',fields={'enemy':'unknown'},evidence_refs=['player-frame'])
        self.assertEqual(compare_player_state(case,{'enemy':'near'})['diagnostic']['classification_candidate'],'STATE_ERROR')
        self.assertFalse(compare_player_state(case,{'enemy':'unknown'})['engine_eligible'])

    def test_good_outcome_does_not_rescue_bad_decision_or_state(self):
        stages=dict(state='FAIL',decision='PASS',outcome='PASS')
        result=evaluate_ordered(stages)
        self.assertEqual(result['classification'],'STATE_ERROR');self.assertEqual(result['decision_quality'],'NOT_EVALUATED')
        stages.update(state='PASS',knowledge='PASS',strategy='PASS',decision='FAIL')
        self.assertEqual(evaluate_ordered(stages)['classification'],'DECISION_ERROR')
        stages.update(decision='PASS',execution='PASS',coach='PASS',outcome='FAIL')
        self.assertEqual(evaluate_ordered(stages)['decision_quality'],'PASS')

    def test_self_declared_reference_cannot_enter_real_denominator(self):
        case=json.loads((ROOT/'fixtures/r7/representative_set.json').read_text())['cases'][0]
        case['reference']['PLAYER_INFORMATION_STATE']=dict(status='ESTABLISHED',fields={'hp':1},evidence_refs=['observer-only-frame'])
        out=compare_player_state(case,{'hp':1})
        self.assertEqual(out['status'],'BLOCKED');self.assertEqual(out['denominator'],0)
        self.assertEqual(out['diagnostic']['values_equal'],1)
        out=compare_player_state(case,{'hp':True})
        self.assertEqual(out['diagnostic']['values_equal'],0)
        self.assertEqual(out['diagnostic']['mismatches'],['hp'])

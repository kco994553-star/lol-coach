import copy
import unittest
from pydantic import ValidationError
from coach_v1.models import Observation, SnapshotRequest
from coach_v1.state import reduce_snapshot
from .helpers import observation,request


def state(rows,**req):
    return reduce_snapshot(tuple(Observation.model_validate(x) for x in rows),SnapshotRequest.model_validate(request(**req)))


class StateTests(unittest.TestCase):
    def test_missing_is_unknown_not_zero(self):
        f=state([]).field('self:position');self.assertEqual((f.state,f.value),('UNKNOWN',None))

    def test_delayed_older_observation_cannot_overwrite(self):
        old=observation('old',value='jungle',event_time_ms=900,received_at='2026-10-04T09:30:00+00:00')
        self.assertEqual(state([observation(),old]).field('self:position').value,'lane')

    def test_future_excluded(self):
        s=state([observation(event_time_ms=1001)])
        self.assertEqual(s.field('self:position').state,'UNKNOWN');self.assertIn(('o1','FUTURE_EVENT'),s.excluded)

    def test_duplicate_idempotency_and_input_order(self):
        a=observation();b=observation('b',field='health',value=50)
        self.assertEqual(state([a,b]),state([b,a,a]))

    def test_id_collision_quarantines_both_keys(self):
        s=state([observation(),observation(field='health',value=50)])
        self.assertEqual(s.conflict_ids,('o1',))
        self.assertTrue(all(f.state=='CONFLICTING' for f in s.fields))

    def test_same_time_conflict_preserved(self):
        s=state([observation(),observation('o2',value='base')])
        self.assertEqual(s.field('self:position').state,'CONFLICTING')
        self.assertEqual(s.field('self:position').evidence_refs,('o1','o2'))

    def test_hidden_observer_does_not_override_visible_state(self):
        s=state([observation(),observation('hidden',value='base',perspective='OBSERVER',visibility_at_event='NOT_VISIBLE')])
        self.assertEqual(s.field('self:position').value,'lane')
        self.assertNotIn('hidden',s.known_refs)

    def test_late_review_keeps_player_visible_scene(self):
        late=observation(received_at='2026-10-04T09:30:00+00:00')
        self.assertEqual(state([late]).field('self:position').state,'KNOWN')
        self.assertEqual(state([late],knowledge_cutoff='2026-10-04T09:10:00+00:00',view='RECEIVED_AS_OF').field('self:position').state,'UNKNOWN')

    def test_current_position_expires_without_ttl_guess(self):
        self.assertEqual(state([observation(event_time_ms=900)]).field('self:position').state,'STALE')

    def test_last_seen_does_not_populate_current_location(self):
        s=state([observation(field='jungle.last_seen',event_time_ms=900,validity='HISTORICAL_FACT')])
        self.assertEqual(s.field('self:jungle.last_seen').state,'KNOWN')
        self.assertEqual(s.field('self:position').state,'UNKNOWN')

    def test_cast_is_not_cooldown_and_cs_not_wave(self):
        s=state([observation(field='spell.cast_event',event_time_ms=900,validity='HISTORICAL_FACT'),observation('cs',field='cs',value=20)],required_keys=['self:spell.ready','self:wave_combat_support'])
        self.assertEqual(s.field('self:spell.ready').state,'UNKNOWN')
        self.assertEqual(s.field('self:wave_combat_support').state,'UNKNOWN')

    def test_manual_and_inferred_not_facts(self):
        for change in ({'kind':'MANUAL','author':'reviewer'},{'kind':'INFERRED','hypothesis':'possible intent'}):
            self.assertEqual(state([observation(**change)]).field('self:position').state,'CONDITIONAL')

    def test_missing_or_hidden_lineage_not_laundered(self):
        derived=observation('d',field='escape',kind='DERIVED',lineage_ids=['hidden'],formula='identity',formula_version='1')
        for rows in ([derived],[derived,observation('hidden',perspective='OBSERVER')]):
            self.assertNotIn('d',state(rows).known_refs)

    def test_patch_and_clock_mismatch_not_known(self):
        for change in ({'patch':'OTHER'},{'game_clock_basis':'other'}):
            self.assertNotIn('o1',state([observation(**change)]).known_refs)

    def test_independent_source_group_deduplicated(self):
        self.assertEqual(state([observation(),observation('o2')]).field('self:position').independent_groups,('frame-1',))

    def test_missing_provenance_nonfinite_or_naive_time_rejected(self):
        for change in ({'source_hash':''},{'value':float('nan')},{'received_at':'2026-10-04T09:00:00'},{'value':None},{'validity':'HISTORICAL_FACT'},{'kind':'DERIVED'}):
            with self.assertRaises(ValidationError):Observation.model_validate(observation(**change))

    def test_snapshot_immutable_and_new_revision(self):
        s=state([observation()]);p=state([observation(value='base')],revision_parent=s.snapshot_id)
        self.assertNotEqual(s.snapshot_id,p.snapshot_id)
        self.assertEqual(s.field('self:position').value,'lane')
        with self.assertRaises(ValidationError):s.snapshot_id='changed'

    def test_cross_session_rejected(self):
        with self.assertRaises(ValueError):state([observation(session_id='different')])

    def test_conflicting_lineage_not_laundered(self):
        rows=[observation(),observation('o2',value='base'),observation('derived',field='escape',kind='DERIVED',lineage_ids=['o1'],formula='fixture-identity',formula_version='1')]
        self.assertNotIn('derived',state(rows).known_refs)

    def test_later_event_cannot_support_earlier_historical_derivation(self):
        rows=[observation(),observation('derived',field='escape.event',event_time_ms=900,validity='HISTORICAL_FACT',kind='DERIVED',lineage_ids=['o1'],formula='fixture',formula_version='1')]
        s=state(rows);self.assertNotIn('derived',s.known_refs)
        self.assertIn('FUTURE_LINEAGE',s.field('self:escape.event').reasons)

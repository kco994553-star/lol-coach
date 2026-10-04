"""Offline evidence audit only. Reuses R7 equality and R3 state gates; no activation."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pydantic import ValidationError
from coach_audit.replay import compare_reference_values
from coach_audit.sufficiency import assess_information
from coach_v1.models import Observation, SnapshotRequest, ReviewInput
from coach_v1.state import reduce_snapshot


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observations_for(ref, received_at):
    # UNKNOWN is an explicit audit sentinel, never an asserted game patch/version.
    base = dict(session_id=ref['reference_id'], event_time_ms=ref['timestamp_seconds'] * 1000,
                received_at=received_at, game_clock_basis='VISIBLE_HUD_SECONDS',
                source_id=ref['source_family'], source_version='PUBLIC_CAPTURE_PATCH_UNKNOWN',
                source_location=ref['source_location'], source_hash=ref['source_sha256'],
                lineage_ids=(), independent_group_id=ref['source_sha256'],
                perspective='PLAYER' if ref['perspective'] == 'PLAYER_STYLE_HUD' else 'OBSERVER',
                visibility_at_event='KNOWN', patch='UNKNOWN_FROM_CAPTURE',
                quality_state=dict(accuracy='UNVERIFIED', completeness='UNVERIFIED', freshness='UNVERIFIED'),
                validity='AT_EVENT')
    result = []
    for field, value in ref['observed_values'].items():
        result.append(Observation(observation_id=ref['reference_id'] + ':' + field,
                                  entity_id='capture', field_key=field, value=value,
                                  kind='MANUAL', author=ref['operator'], **base))
    if 'hp' in ref['observed_values']:
        result.append(Observation(**{**base, 'lineage_ids': (ref['reference_id'] + ':hp', ref['reference_id'] + ':max_hp')},
            observation_id=ref['reference_id'] + ':health_fraction', entity_id='capture',
            field_key='health_fraction', value=ref['observed_values']['hp'] / ref['observed_values']['max_hp'],
            kind='DERIVED', formula='hp/max_hp', formula_version='r7.health_fraction.v1'))
    return tuple(result)


def request_for(ref, received_at):
    return SnapshotRequest(session_id=ref['reference_id'], patch='UNKNOWN_FROM_CAPTURE',
                          as_of_event_time_ms=ref['timestamp_seconds'] * 1000,
                          knowledge_cutoff=received_at, game_clock_basis='VISIBLE_HUD_SECONDS',
                          view='PLAYER_REVIEW', required_keys=('capture:enemy_jungle_position',))


def real_mode_gate(ref, observations, request):
    # A complete, explicitly REAL request is rejected. No SYNTHETIC relabel or run_review call.
    payload = dict(schema_version='r3.v1', evidence_kind='REAL', mode='POST_GAME',
        objective='Offline public capture validation', scope_reason='Only a single visible frame; match end unverified',
        snapshot_request=request.model_dump(mode='json'),
        observations=[o.model_dump(mode='json') for o in observations],
        scenarios=[dict(scenario_id='visible-frame', description='Unverified still-frame context',
                        support_refs=(observations[0].observation_id,), conditions=('Patch and mode unknown',))],
        actions=[dict(action_id='conditional-wait', action_type='WAIT', feasibility='UNKNOWN',
                      feasibility_refs=(), required_keys=('capture:enemy_jungle_position',),
                      target='Not selected', path='Not selected', entry_condition='No permission asserted',
                      resource_budget='Not assessed', exit_condition='Not assessed',
                      abort_conditions=('Evidence remains insufficient',), postcondition='Not assessed',
                      deadline_event='Not established')], assessments=[], comparisons=[])
    try:
        ReviewInput.model_validate(payload)
    except ValidationError as exc:
        errors = [dict(location=list(e['loc']), type=e['type']) for e in exc.errors()]
        return dict(status='BLOCKED_AS_EXPECTED', errors=errors,
                    evidence_kind_submitted='REAL', relabelled_synthetic=False,
                    existing_engine_executed=False, coaching_N=0)
    raise AssertionError('Protected evidence_kind gate unexpectedly accepted REAL')


def extraction_projection(extracted):
    values = dict(extracted['observed_values'])
    enemies = values.get('enemy_champions', [])
    # Documented mapping from one readable visible enemy, not a cross-source identity join.
    if len(enemies) == 1:
        values['visible_enemy_champion'] = enemies[0].get('champion')
        values['visible_enemy_level'] = enemies[0].get('level')
    return values


def audit(media_dir=None):
    refs = read('fixtures/r7-real/visual-reference-initial.json')
    lock = read('evidence/r7-real/visual-reference-lock.json')
    assert sha(ROOT / lock['reference_path']) == lock['reference_sha256'], 'REFERENCE_LOCK_CHANGED'
    vision = read('evidence/r7-real/vision-extraction.json')
    received_at = datetime.fromisoformat(refs['locked_at'])
    assert datetime.fromisoformat(vision['extracted_at']) >= received_at, 'REFERENCE_NOT_FIRST'
    extracted = {r['reference_id']: r for r in vision['references']}
    assert len(extracted) == len(vision['references']), 'DUPLICATE_EXTRACTION_ID'
    revision_path = ROOT / 'evidence/r7-real/reference-revisions.json'
    revisions = read('evidence/r7-real/reference-revisions.json') if revision_path.exists() else None
    if revisions:
        assert revisions['parent_reference_sha256'] == lock['reference_sha256'], 'WRONG_REVISION_PARENT'
    results = []
    for ref in refs['references']:
        if media_dir is not None:
            assert sha(Path(media_dir) / ref['source_image']) == ref['source_sha256'], 'MEDIA_BYTES_CHANGED'
        other = extracted[ref['reference_id']]
        assert other['provenance']['image_sha256'] == ref['source_sha256'], 'SOURCE_HASH_MISMATCH'
        comparison = compare_reference_values(ref['observed_values'], extraction_projection(other))
        comparison['classification_candidate'] = 'EXTRACTION_ERROR_OR_REFERENCE_ERROR' if comparison['mismatches'] else None
        original_ref = ref
        for revision in (revisions or {}).get('revisions', []):
            if revision['reference_id'] == ref['reference_id']:
                assert revision['source_sha256'] == ref['source_sha256'], 'WRONG_REVISION_SOURCE'
                values = dict(ref['observed_values'])
                for key, change in revision['changes'].items():
                    assert values[key] == change['old'], 'WRONG_REVISION_VALUE'
                    values[key] = change['new']
                ref = {**ref, 'observed_values': values}
        revised_comparison = compare_reference_values(ref['observed_values'], extraction_projection(other))
        observations = observations_for(ref, received_at)
        request = request_for(ref, received_at)
        snapshot = reduce_snapshot(observations, request)
        assert not snapshot.known_refs, 'MANUAL_OR_OBSERVER_PROMOTED_TO_KNOWN'
        assert snapshot.field('capture:enemy_jungle_position').state == 'UNKNOWN'
        if ref['perspective'] == 'OBSERVER':
            assert all(reason == 'NOT_PLAYER_KNOWN' for _, reason in snapshot.excluded)
        else:
            assert snapshot.field('capture:health_fraction').state == 'CONDITIONAL'
        results.append(dict(reference_id=ref['reference_id'], scenario_type=ref['scenario_type'],
                            diagnostic_comparison=comparison,
                            revised_comparison=revised_comparison,
                            revision_is_blind_reference=ref == original_ref,
                            state_contract=snapshot.model_dump(mode='json'),
                            information_requirements=assess_information({}),
                            strategic_state_generated=False,
                            coaching_gate=real_mode_gate(ref, observations, request)))
    # Actual observer observations cannot cross into another actual frame's session.
    player = refs['references'][0]
    observer = next(r for r in refs['references'] if r['perspective'] == 'OBSERVER')
    try:
        reduce_snapshot(observations_for(observer, received_at), request_for(player, received_at))
    except ValueError as exc:
        assert str(exc) == 'cross-session observation'
        cross_session = 'REJECTED'
    else:
        raise AssertionError('CROSS_SESSION_OBSERVER_LEAK')
    return dict(schema_version='r7-real.audit.v1', at_kst=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
        input_sha256={path: sha(ROOT / path) for path in (
            'scripts/audit_real_r7.py', 'fixtures/r7-real/visual-reference-initial.json',
            'evidence/r7-real/visual-reference-lock.json', 'evidence/r7-real/vision-extraction.json',
            'coach_v1/models.py', 'coach_v1/state.py', 'coach_v1/engine.py',
            'coach_audit/replay.py', 'coach_audit/sufficiency.py', 'contracts/r7/action_requirements.json')},
        reference_sha256=lock['reference_sha256'], operator_reference_human=False,
        fresh_media_byte_hashes_checked=media_dir is not None,
        revision_sha256=sha(revision_path) if revisions else None,
        comparison_scope='Independent AI extraction vs AI-operator transcription; not human-gold accuracy',
        results=results, no_hindsight=dict(observer_exclusion='PASS', cross_session=cross_session,
           matched_player_ground_truth_pairs=0, decision_quality_evaluated=False,
           scope='Actual published observer image rejected; no matched-game outcome claim'),
        real_match_authenticated=0, real_verified_state_variables=0, coaching_validation_N=0,
        existing_core_executions=0, frozen_design_changed=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--media-dir', type=Path, help='Original acquired assets, freshly SHA-256 checked')
    args = parser.parse_args()
    output = ROOT / 'evidence/r7-real' / datetime.now(ZoneInfo('Asia/Seoul')).strftime('audit-%Y%m%dT%H%M%S%fKST')
    output.mkdir()
    result = audit(args.media_dir)
    (output / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(output=str(output.relative_to(ROOT)),
                         compared=sum(r['diagnostic_comparison']['fields_compared'] for r in result['results']),
                         equal=sum(r['diagnostic_comparison']['values_equal'] for r in result['results']),
                         no_hindsight=result['no_hindsight'], coaching_N=0), ensure_ascii=False))

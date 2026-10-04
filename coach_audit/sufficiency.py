"""Exploratory requirements diagnostic. No action permission, ranking or numeric TTL."""
import json
from pathlib import Path


def assess_information(field_states, catalog=None):
    if catalog is None:
        catalog = json.loads((Path(__file__).resolve().parents[1] / 'contracts/r7/action_requirements.json').read_text())
    results = []
    for spec in catalog['actions']:
        missing = [key for key in spec['required_keys'] if field_states.get(key) != 'KNOWN']
        results.append(dict(action=spec['action'], engine_action_type=spec['engine_action_type'],
                            required_keys=spec['required_keys'], missing_information=missing,
                            information_sufficiency='INSUFFICIENT' if missing else 'PROFILE_REQUIREMENTS_MET',
                            permission='NOT_EVALUATED',
                            unlock_conditions=[dict(field=key, requirement='Player-known, source-backed and current at decision time') for key in missing],
                            lower_commitment_candidates=[r['action'] for r in results if not r['missing_information']],
                            fallback='Evaluate a reversible or conditional candidate with its own feasibility evidence; no automatic NO_ACTION'))
    return results


def next_acquisition(attempts):
    """Choose first sufficient eligible rung or first untried available rung; never skip untested cheaper data."""
    ladder = ('STRUCTURED', 'EVENT', 'DETERMINISTIC', 'KNOWLEDGE_INFERENCE', 'SNAPSHOT_VISION', 'SHORT_CLIP_VISION', 'MANUAL_TAG')
    for rung in ladder:
        row = attempts.get(rung, {})
        if row.get('verified_sufficient') and row.get('available') and row.get('decision_eligible'):
            return dict(source=rung, status='REUSE', invoke=False)
        if row.get('available') and not row.get('attempted'):
            return dict(source=rung, status='TRY', invoke=True)
    return dict(source=None, status='EVIDENCE_GAP', invoke=False)

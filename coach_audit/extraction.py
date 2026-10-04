"""Allowlisted L0 extraction with provenance; never auto-promotes into GameState."""
import math
from coach_intake.audit import inspect
from coach_intake.io import strict_json, sha

# Existing five diagnostic paths are reused, not duplicated.
EXTRA_PATHS = {
    'active_resource': ('/activePlayer/championStats/resourceValue', 'number'),
    'active_resource_max': ('/activePlayer/championStats/resourceMax', 'number'),
    'champion_name': ('/allPlayers/0/championName', 'text'),
    'role_label': ('/allPlayers/0/position', 'text'),
    'kills': ('/allPlayers/0/scores/kills', 'integer'),
    'deaths': ('/allPlayers/0/scores/deaths', 'integer'),
    'assists': ('/allPlayers/0/scores/assists', 'integer'),
    'cs': ('/allPlayers/0/scores/creepScore', 'integer'),
    'keystone_id': ('/allPlayers/0/runes/keystone/id', 'integer'),
    'summoner_one_name': ('/allPlayers/0/summonerSpells/summonerSpellOne/displayName', 'text'),
    'summoner_two_name': ('/allPlayers/0/summonerSpells/summonerSpellTwo/displayName', 'text'),
    'ultimate_level': ('/activePlayer/abilities/R/abilityLevel', 'integer'),
}


def _read(data, pointer, kind):
    value = data
    for key in pointer.strip('/').split('/'):
        if value is None:
            return None, 'NULL_ANCESTOR'
        if isinstance(value, dict):
            if key not in value:
                return None, 'MISSING'
            value = value[key]
        elif isinstance(value, list) and key.isdigit():
            if int(key) >= len(value):
                return None, 'MISSING'
            value = value[int(key)]
        else:
            return None, 'WRONG_CONTAINER'
    if value is None:
        return None, 'NULL'
    if kind == 'text':
        valid = type(value) is str
    else:
        valid = type(value) in ((int,) if kind == 'integer' else (int, float)) and math.isfinite(value) and value >= 0
    if not valid:
        return None, 'INVALID'
    return (None, 'EMPTY') if value == '' else (value, 'PRESENT')


def extract(raw, *, source_kind='UNVERIFIED_IMPORT', expected_sha=None):
    diagnostic = inspect(raw, source_kind, expected_sha)
    data = strict_json(raw)
    facts = [dict(row) for row in diagnostic['raw_facts']]
    for field, (pointer, kind) in EXTRA_PATHS.items():
        value, state = _read(data, pointer, kind)
        facts.append(dict(field=field, pointer=pointer, state=state, value=value, decision_eligible=False))
    for row in facts:
        row.update(layer='L0', source_sha256=sha(raw), source_kind=source_kind,
                   participant_scope='activePlayer' if row['pointer'].startswith('/activePlayer') else
                   'allPlayers[0] (not identity-joined to activePlayer)' if row['pointer'].startswith('/allPlayers') else 'gameData')
    by_field = {row['field']: row for row in facts}
    hp, cap = by_field['active_health'], by_field['active_max_health']
    ratio = None
    if hp['state'] == cap['state'] == 'PRESENT' and cap['value'] > 0 and 0 <= hp['value'] <= cap['value']:
        ratio = hp['value'] / cap['value']
    derived = dict(field='health_fraction', layer='L1', value=ratio,
                   state='DERIVED_DIAGNOSTIC' if ratio is not None else 'UNKNOWN',
                   formula='active_health / active_max_health', formula_version='r7.health_fraction.v1',
                   lineage=['active_health', 'active_max_health'], source_sha256=sha(raw),
                   decision_eligible=False,
                   missing_reason=None if ratio is not None else 'HEALTH_INPUT_MISSING_OR_SEMANTICALLY_INVALID')
    return dict(schema_version='r7.extraction.v1', source_kind=source_kind, raw_sha256=sha(raw),
                existing_intake=diagnostic, raw=facts, derived=[derived], strategic=[],
                player_information_state=None, ground_truth_state=None,
                coaching_enabled=False,
                activation_blockers=diagnostic['activation_blockers'] + ['REAL_REFERENCE_STATE_MISSING', 'ENGINE_SYNTHETIC_ONLY'],
                non_equivalences=['role_label != spatial position', 'ultimate_level != ultimate readiness',
                                  'CS != wave state', 'spell name != cooldown', 'health ratio != trade permission'])

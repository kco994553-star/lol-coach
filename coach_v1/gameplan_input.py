"""Pure composition boundary. No I/O, identities, role inference or live approval.

``input`` reuses loading-engine's legacy eight-field input. Incomplete captures
remain inspectable but must not be evaluated unless ``ready`` is true.
"""
import math
import re

POSITIONS = ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT')
FIELDS = ('allies', 'enemies', 'own_champion', 'own_position', 'side', 'patch',
          'opponent_mode', 'lane_opponent')


def _stamp(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def normalize(raw, champions, *, source='MANUAL', session_id, observed_at,
              now, max_age=2, current=True, revision=0):
    """Normalize canonical catalogue IDs using a trusted, local champion roster.

    session_id is a caller-created opaque capture-session token, never an account
    or credential fingerprint. Clock values must share one monotonic clock.
    max_age is transport liveness only, not gameplay validity. Manual captures
    use the same freshness gate; resubmission must create a fresh observation.
    """
    if source not in ('MANUAL', 'LCU_CHAMP_SELECT'):
        raise ValueError('SOURCE_UNSUPPORTED')
    if not isinstance(session_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', session_id):
        raise ValueError('SESSION_REQUIRED')
    if not all(_stamp(v) for v in (observed_at, now, max_age)) or max_age <= 0:
        raise ValueError('CLOCK_INVALID')
    if type(current) is not bool or type(revision) is not int or revision < 0:
        raise ValueError('SOURCE_METADATA_INVALID')
    if not isinstance(raw, dict) or set(raw) != set(FIELDS):
        raise ValueError('INPUT_SCHEMA')
    roster = set(champions)
    out = {}
    reasons = []
    seen = set()
    for team in ('allies', 'enemies'):
        rows = raw[team]
        if not isinstance(rows, list) or len(rows) > 5:
            raise ValueError('TEAM_SCHEMA')
        out[team] = []
        roles = set()
        for row in rows:
            if not isinstance(row, dict) or set(row) != {'champion', 'position'}:
                raise ValueError('PLAYER_SCHEMA')
            hero, role = row['champion'], row['position']
            if hero is not None and (not isinstance(hero, str) or hero not in roster):
                raise ValueError('CHAMPION_UNKNOWN')
            if role is not None and role not in POSITIONS:
                raise ValueError('POSITION_INVALID')
            if hero and hero in seen:
                raise ValueError('CHAMPION_DUPLICATE')
            if role and role in roles:
                raise ValueError('POSITION_DUPLICATE')
            if hero: seen.add(hero)
            if role: roles.add(role)
            out[team].append(dict(champion=hero, position=role))
        if len(rows) != 5 or any(row['champion'] is None for row in rows):
            reasons.append('COMPOSITION_INCOMPLETE')
    own, role = raw['own_champion'], raw['own_position']
    if own is not None and (not isinstance(own, str) or own not in roster):
        raise ValueError('SELF_UNKNOWN')
    if role is not None and role not in POSITIONS:
        raise ValueError('POSITION_INVALID')
    self_rows = [r for r in out['allies'] if own and r['champion'] == own]
    if own is None or not self_rows or role is None:
        reasons.append('SELF_INCOMPLETE')
    if self_rows and role and (self_rows[0]['position'] not in (None, role) or any(r['champion'] != own and r['position'] == role for r in out['allies'])):
        raise ValueError('SELF_POSITION_CONFLICT')
    side, patch, mode, opponent = (raw[k] for k in ('side', 'patch', 'opponent_mode', 'lane_opponent'))
    if side not in (None, 'BLUE', 'RED'): raise ValueError('SIDE_INVALID')
    if side is None: reasons.append('SIDE_UNKNOWN')
    if patch is not None and (not isinstance(patch, str) or not re.fullmatch(r'\d{1,3}\.\d{1,3}(?:\.\d{1,3})?', patch)):
        raise ValueError('PATCH_INVALID')
    if mode not in ('ASSIGNED', 'UNKNOWN', 'MANUAL'): raise ValueError('OPPONENT_MODE_INVALID')
    if mode == 'MANUAL':
        if not isinstance(opponent, str) or not any(r['champion'] == opponent for r in out['enemies']):
            raise ValueError('OPPONENT_INVALID')
    elif opponent is not None: raise ValueError('OPPONENT_INVALID')
    out.update(own_champion=own, own_position=role, side=side, patch=patch,
               opponent_mode=mode, lane_opponent=opponent)
    fresh = current and 0 <= now - observed_at <= max_age
    if not fresh: reasons.append('SOURCE_NOT_CURRENT')
    return dict(format='lol-coach-composition-capture-v1', input=out,
                ready=not reasons, reasons=list(dict.fromkeys(reasons)),
                source=dict(kind=source, session_id=session_id, revision=revision,
                            observed_at=observed_at, age=max(0, now-observed_at), current=fresh),
                live_coaching_enabled=False)


def from_lcu(snapshot, champions, *, side=None, session_id, observed_at, now,
             max_age=2):
    """Consume only the existing privacy-filtered LCUDraftAdapter projection.

    No side default: LCU projection has no side field. Caller must supply an
    explicitly selected side. Non-ChampSelect states discard old composition.
    Hovered picks remain partial; completed picks may be normalized.
    """
    connected = snapshot.get('status') == 'CONNECTED' and snapshot.get('phase') == 'ChampSelect'
    raw = dict(allies=[], enemies=[], own_champion=None, own_position=None,
               side=side, patch=snapshot.get('patch'), opponent_mode='ASSIGNED', lane_opponent=None)
    if connected:
        for team in ('allies', 'enemies'):
            raw[team] = [dict(champion=r.get('champion') if r.get('locked') is True else None,
                              position=r.get('position')) for r in snapshot.get(team, [])]
        raw['own_champion'] = snapshot.get('own_champion')
        raw['own_position'] = snapshot.get('own_position')
    return normalize(raw, champions, source='LCU_CHAMP_SELECT', session_id=session_id,
                     observed_at=observed_at, now=now, max_age=max_age,
                     current=connected, revision=snapshot.get('revision', 0))

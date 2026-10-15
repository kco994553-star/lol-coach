"""SYNTHETIC LCU fixtures; never contacts a game client or an account API."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


ROSTER = {1: 'Annie', 2: 'Olaf', 3: 'Galio', 4: 'TwistedFate'}
PHASE = '/lol-gameflow/v1/gameflow-phase'
SESSION = '/lol-champ-select/v1/session'


def fixture():
    return {
        'localPlayerCellId': 0,
        'myTeam': [{'cellId': 0, 'championId': 1, 'assignedPosition': 'middle',
                    'summonerId': 'DO_NOT_READ', 'puuid': 'DO_NOT_READ',
                    'summonerName': 'DO_NOT_READ', 'riotId': 'DO_NOT_READ'},
                   {'cellId': 1, 'championId': 2, 'assignedPosition': 'jungle'}],
        'theirTeam': [{'cellId': 5, 'championId': 0, 'assignedPosition': ''}],
        'actions': [[{'id': 1, 'actorCellId': 0, 'championId': 1,
                      'completed': True, 'isAllyAction': True, 'type': 'pick'},
                     {'id': 2, 'actorCellId': 1, 'championId': 2,
                      'completed': False, 'isAllyAction': True, 'type': 'pick'}]],
        'bans': {'myTeamBans': [3, -1], 'theirTeamBans': [4, 0], 'numBans': 4},
        'timer': {'phase': 'BAN_PICK'},
    }


class FakeTransport:
    def __init__(self):
        self.phase = 'ChampSelect'
        self.session = fixture()
        self.calls = []
        self.error = None
        self.on_session = None

    def __call__(self, credentials, path):
        self.calls.append((credentials.port, path))
        if self.error:
            raise self.error
        if path == PHASE:
            return self.phase
        if path == SESSION:
            if self.on_session:
                self.on_session()
            return copy.deepcopy(self.session)
        raise AssertionError('endpoint must never be requested')


class LCUDraftTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.lcu_draft'),
                             'LCU adapter implementation absent')
        from coach_v1.lcu_draft import LCUDraftAdapter
        self.cls = LCUDraftAdapter
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lockfile = Path(self.tmp.name) / 'lockfile'
        self.lockfile.write_text('LeagueClient:123:2999:PRIVATE_TOKEN:https')
        self.transport = FakeTransport()
        self.adapter = self.cls(self.lockfile, ROSTER, patch='16.19',
                                transport=self.transport)

    def test_projection_hidden_enemy_identity_omission_and_immutability(self):
        before = copy.deepcopy(self.transport.session)
        result = self.adapter.poll()
        self.assertEqual(result['status'], 'CONNECTED')
        self.assertEqual(result['own_champion'], 'Annie')
        self.assertEqual(result['own_position'], 'MID')
        self.assertEqual(result['allies'], [
            dict(champion='Annie', position='MID', locked=True),
            dict(champion='Olaf', position='JUNGLE', locked=False)])
        self.assertEqual(result['enemies'], [dict(champion=None, position=None, locked=None)])
        self.assertEqual(result['bans'], {'allies': ['Galio', None],
                                         'enemies': ['TwistedFate', None]})
        self.assertEqual(result['pick_phase'], 'BAN_PICK')
        self.assertEqual(self.transport.session, before)
        self.assertNotIn('DO_NOT_READ', json.dumps(result))
        self.assertNotIn('PRIVATE_TOKEN', repr(self.adapter))
        result['allies'][0]['champion'] = 'CORRUPT'
        self.assertEqual(self.adapter.snapshot()['own_champion'], 'Annie')
        self.assertEqual([p for _, p in self.transport.calls], [PHASE, SESSION, PHASE])

    def test_revision_changes_only_for_projected_changes_and_reconnection(self):
        first = self.adapter.poll()
        self.assertEqual(self.adapter.poll(), first)
        self.transport.session['myTeam'][0]['summonerName'] = 'OTHER_PRIVATE'
        self.assertEqual(self.adapter.poll(), first)
        self.transport.session['myTeam'][0]['championId'] = 2
        second = self.adapter.poll()
        self.assertEqual(second['revision'], first['revision'] + 1)
        self.lockfile.write_text('LeagueClient:456:3000:ROTATED_TOKEN:https')
        third = self.adapter.poll()
        self.assertGreater(third['revision'], second['revision'])
        self.assertEqual(third['status'], 'CONNECTED')
        self.assertEqual(self.transport.calls[-1][0], 3000)

    def test_game_start_unknown_and_phase_race_clear_all_draft_data(self):
        self.adapter.poll()
        for phase in ['GameStart', 'InProgress', 'Reconnect', 'Lobby', 'NewUnknownPhase', None]:
            self.transport.phase = phase
            row = self.adapter.poll()
            self.assertEqual(row['status'], 'MANUAL_FALLBACK')
            self.assertEqual(row['allies'], [])
            self.assertIsNone(row['own_champion'])
            self.assertIsNone(row['pick_phase'])
        self.transport.phase = 'ChampSelect'
        self.transport.on_session = lambda: setattr(self.transport, 'phase', 'GameStart')
        row = self.adapter.poll()
        self.assertEqual(row['reason'], 'PHASE_CHANGED')
        self.assertEqual(row['enemies'], [])

    def test_required_fields_and_unknown_schema_fail_closed(self):
        variants = []
        for key in ['myTeam', 'theirTeam', 'actions', 'timer', 'localPlayerCellId', 'bans']:
            value = fixture(); del value[key]; variants.append(value)
        value = fixture(); del value['myTeam'][0]['championId']; variants.append(value)
        value = fixture(); value['newUnexpectedField'] = True; variants.append(value)
        value = fixture(); value['myTeam'][0]['newUnexpectedField'] = True; variants.append(value)
        value = fixture(); value['myTeam'][0]['championId'] = True; variants.append(value)
        value = fixture(); value['myTeam'][0]['championId'] = 99999; variants.append(value)
        value = fixture(); value['timer']['phase'] = 'SOMETHING_NEW'; variants.append(value)
        value = fixture(); value['actions'][0][0]['completed'] = 'true'; variants.append(value)
        value = fixture(); value['myTeam'].append(copy.deepcopy(value['myTeam'][0])); variants.append(value)
        value = fixture(); value['localPlayerCellId'] = 99; variants.append(value)
        for value in variants:
            self.transport.session = value
            with self.subTest(value=value):
                row = self.adapter.poll()
                self.assertEqual(row['reason'], 'SCHEMA_UNSUPPORTED')
                self.assertEqual(row['status'], 'MANUAL_FALLBACK')
                self.assertEqual(row['allies'], [])

    def test_invalid_lockfiles_and_missing_client_never_send_requests(self):
        for content in ['LeagueClient:1:2999:token:http',
                        'LeagueClient:1:127.0.0.2:token:https',
                        'LeagueClient:1:2999:token:https:evil.example',
                        'https://evil.example:1:2999:token:https',
                        'LeagueClient:1:65536:token:https',
                        'LeagueClient:1:2999:token\r\nX-Evil:https']:
            self.lockfile.write_text(content)
            self.assertEqual(self.adapter.poll()['reason'], 'LOCKFILE_INVALID')
        self.assertEqual(self.transport.calls, [])
        self.lockfile.unlink()
        row = self.adapter.poll()
        self.assertEqual(row['status'], 'BLOCKED_EXTERNAL')
        self.assertEqual(row['reason'], 'LCU_NOT_AVAILABLE')

    def test_rotation_during_poll_discards_result(self):
        self.transport.on_session = lambda: self.lockfile.write_text(
            'LeagueClient:456:3000:ROTATED_TOKEN:https')
        row = self.adapter.poll()
        self.assertEqual(row['reason'], 'SESSION_CHANGED')
        self.assertEqual(row['allies'], [])
        self.transport.on_session = None
        self.assertEqual(self.adapter.poll()['status'], 'CONNECTED')

    def test_failure_has_no_raw_exception_secrets_or_cached_selection(self):
        self.adapter.poll()
        self.transport.error = OSError('PRIVATE_TOKEN summonerName: PRIVATE_NAME')
        row = self.adapter.poll()
        self.assertEqual(row['reason'], 'LCU_REQUEST_FAILED')
        self.assertEqual(row['status'], 'MANUAL_FALLBACK')
        self.assertNotIn('PRIVATE', json.dumps(row))
        self.assertEqual(row['allies'], [])

    def test_real_transport_requires_explicit_pin_before_any_connection(self):
        adapter = self.cls(self.lockfile, ROSTER)
        self.assertEqual(adapter.poll()['reason'], 'TLS_PIN_REQUIRED')

    def test_lockfile_symlink_is_rejected(self):
        alias = Path(self.tmp.name) / 'alias'
        alias.symlink_to(self.lockfile)
        self.assertEqual(self.cls(alias, ROSTER, transport=self.transport).poll()['reason'],
                         'LOCKFILE_INVALID')

    def test_pinned_tls_checks_certificate_before_sending_auth(self):
        from coach_v1 import lcu_draft as module
        connection = Mock()
        connection.sock.getpeercert.return_value = b'WRONG_CERTIFICATE'
        with patch.object(module.http.client, 'HTTPSConnection', return_value=connection) as factory:
            row = self.cls(self.lockfile, ROSTER, certificate_sha256='0' * 64).poll()
        self.assertEqual(row['reason'], 'TLS_PIN_MISMATCH')
        factory.assert_called_once()
        self.assertEqual(factory.call_args.args[:2], ('127.0.0.1', 2999))
        connection.request.assert_not_called()
        connection.close.assert_called_once()

    def test_pinned_tls_get_only_no_redirects_and_bounded_schema(self):
        import hashlib
        from coach_v1 import lcu_draft as module
        connection = Mock()
        connection.sock.getpeercert.return_value = b'CERTIFICATE'
        response = connection.getresponse.return_value
        response.status = 302
        pin = hashlib.sha256(b'CERTIFICATE').hexdigest()
        with patch.object(module.http.client, 'HTTPSConnection', return_value=connection):
            row = self.cls(self.lockfile, ROSTER, certificate_sha256=pin).poll()
        self.assertEqual(row['reason'], 'LCU_HTTP_FAILED')
        self.assertEqual(connection.request.call_args.args, ('GET', PHASE))
        response.read.assert_not_called()
        response.status = 429
        with patch.object(module.http.client, 'HTTPSConnection', return_value=connection):
            row = self.cls(self.lockfile, ROSTER, certificate_sha256=pin).poll()
        self.assertEqual(row['reason'], 'LCU_RATE_LIMITED')
        response.status = 200
        response.getheader.return_value = 'application/json'
        response.read.return_value = b'{"a":1,"a":2}'
        with patch.object(module.http.client, 'HTTPSConnection', return_value=connection):
            row = self.cls(self.lockfile, ROSTER, certificate_sha256=pin).poll()
        self.assertEqual(row['reason'], 'SCHEMA_UNSUPPORTED')
        response.read.assert_called_with(module.MAX_RESPONSE_BYTES + 1)

    def test_identity_values_are_never_indexed_or_copied_by_projection(self):
        class IdentityGuard(dict):
            def __getitem__(self, key):
                if key in ('puuid', 'summonerName', 'summonerId', 'riotId'):
                    raise AssertionError('identity value read')
                return super().__getitem__(key)
        self.transport.session['myTeam'][0] = IdentityGuard(self.transport.session['myTeam'][0])
        # Use a no-copy transport so the dictionary guards apply to projection.
        adapter = self.cls(self.lockfile, ROSTER, transport=lambda _, endpoint:
                           self.transport.session if endpoint == SESSION else 'ChampSelect')
        self.assertEqual(adapter.poll()['own_champion'], 'Annie')

    def test_pairing_requires_verified_local_process_and_does_not_send_auth(self):
        import hashlib
        from coach_v1 import lcu_draft as module
        self.assertTrue(hasattr(module, 'pair_certificate'), 'local TLS pairing absent')
        validator = Mock()
        connection = Mock()
        connection.sock.getpeercert.return_value = b'LOCAL_CERTIFICATE'
        with patch.object(module, '_validate_windows_client', validator), \
                patch.object(module.http.client, 'HTTPSConnection', return_value=connection):
            pin = module.pair_certificate(self.lockfile)
        self.assertEqual(pin, hashlib.sha256(b'LOCAL_CERTIFICATE').hexdigest())
        self.assertEqual(validator.call_count, 2)
        connection.request.assert_not_called()
        connection.close.assert_called_once()
        with patch.object(module, '_validate_windows_client', side_effect=ValueError('LOCAL_PROCESS_UNVERIFIED')), \
                patch.object(module.http.client, 'HTTPSConnection') as factory:
            with self.assertRaisesRegex(ValueError, 'LOCAL_PROCESS_UNVERIFIED'):
                module.pair_certificate(self.lockfile)
            factory.assert_not_called()

    def test_pairing_rechecks_rotation_after_tls_handshake(self):
        from coach_v1 import lcu_draft as module
        self.assertTrue(hasattr(module, 'pair_certificate'), 'local TLS pairing absent')
        connection = Mock()
        connection.sock.getpeercert.return_value = b'LOCAL_CERTIFICATE'
        connection.connect.side_effect = lambda: self.lockfile.write_text(
            'LeagueClient:456:3000:ROTATED_TOKEN:https')
        with patch.object(module, '_validate_windows_client'), \
                patch.object(module.http.client, 'HTTPSConnection', return_value=connection):
            with self.assertRaisesRegex(ValueError, 'SESSION_CHANGED'):
                module.pair_certificate(self.lockfile)
        connection.request.assert_not_called()

    def test_rate_limit_cooldown_respects_retry_after_across_polls(self):
        import hashlib
        from coach_v1 import lcu_draft as module
        connection = Mock()
        connection.sock.getpeercert.return_value = b'CERTIFICATE'
        response = connection.getresponse.return_value
        response.status = 429
        response.getheader.return_value = '120'
        adapter = self.cls(self.lockfile, ROSTER,
                           certificate_sha256=hashlib.sha256(b'CERTIFICATE').hexdigest())
        with patch.object(module.http.client, 'HTTPSConnection', return_value=connection) as factory:
            first = adapter.poll()
            self.assertEqual(first['reason'], 'LCU_RATE_LIMITED')
            self.assertEqual(adapter.poll(), first)
            self.assertEqual(factory.call_count, 1)

    @unittest.skipIf(os.name == 'nt', 'non-Windows boundary only')
    def test_native_discovery_and_pairing_fail_closed_off_windows(self):
        from coach_v1 import lcu_draft as module
        self.assertIsNone(module.discover_lockfile())
        with self.assertRaisesRegex(ValueError, 'WINDOWS_CLIENT_REQUIRED'):
            module.pair_certificate(self.lockfile)

    def test_unlocked_or_unassigned_draft_keeps_unknowns(self):
        self.transport.session['myTeam'][0]['assignedPosition'] = ''
        self.transport.session['myTeam'][0]['championId'] = 0
        row = self.adapter.poll()
        self.assertEqual(row['status'], 'CONNECTED')
        self.assertIsNone(row['own_champion'])
        self.assertIsNone(row['own_position'])
        self.assertIsNone(row['allies'][0]['locked'])

    def test_nonascii_lockfile_is_rejected_without_raw_text(self):
        self.lockfile.write_bytes(b'LeagueClient:1:2999:PRIVATE_\xff:https')
        row = self.adapter.poll()
        self.assertEqual(row['reason'], 'LOCKFILE_INVALID')
        self.assertNotIn('PRIVATE', json.dumps(row))
        from coach_v1.lcu_draft import pair_certificate
        with self.assertRaisesRegex(ValueError, '^LOCKFILE_INVALID$'):
            pair_certificate(self.lockfile)

    def test_visible_allied_intent_is_unlocked_but_enemy_intent_stays_hidden(self):
        self.transport.session['myTeam'][0]['championId'] = 0
        self.transport.session['myTeam'][0]['championPickIntent'] = 2
        self.transport.session['theirTeam'][0]['championPickIntent'] = 3
        row = self.adapter.poll()
        self.assertEqual(row['own_champion'], 'Olaf')
        self.assertEqual(row['allies'][0]['locked'], False)
        self.assertEqual(row['enemies'][0], dict(champion=None, position=None, locked=None))

    def test_in_progress_allied_pick_action_projects_unlocked_without_intent(self):
        self.transport.session['myTeam'][0]['championId'] = 0
        action = self.transport.session['actions'][0][0]
        action.update(completed=False, isInProgress=True, isAllyAction=True)
        row = self.adapter.poll()
        self.assertEqual(row['own_champion'], 'Annie')
        self.assertFalse(row['allies'][0]['locked'])
        action['isInProgress'] = False
        self.assertIsNone(self.adapter.poll()['own_champion'])

    def test_unknown_allied_intent_fails_closed_and_never_reads_enemy_intent(self):
        self.transport.session['myTeam'][0]['championId'] = 0
        self.transport.session['myTeam'][0]['championPickIntent'] = 99999
        self.assertEqual(self.adapter.poll()['reason'], 'SCHEMA_UNSUPPORTED')
        self.transport.session['myTeam'][0]['championPickIntent'] = 0
        self.transport.session['theirTeam'][0]['championPickIntent'] = {'unread': 'private'}
        row = self.adapter.poll()
        self.assertEqual(row['status'], 'CONNECTED')
        self.assertIsNone(row['own_champion'])
        self.assertIsNone(row['enemies'][0]['champion'])


if __name__ == '__main__':
    unittest.main()

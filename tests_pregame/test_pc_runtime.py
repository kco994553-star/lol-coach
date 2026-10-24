"""LCU liveness is independent of slow reference maintenance."""
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch
import unittest
from coach_v1.pc_runtime import PCServices,draft_input,start_pc_services
from scripts.launch_pc import create_server


def snapshot(revision=1):
    return dict(status='CONNECTED',reason='CHAMP_SELECT_VERIFIED',phase='ChampSelect',patch=None,revision=revision,
        own_champion='Caitlyn',own_position='BOTTOM',allies=[dict(champion='Caitlyn',position='BOTTOM',locked=False)],enemies=[dict(champion='Ezreal',position='BOTTOM',locked=True)],bans=dict(allies=[],enemies=[]),pick_phase='BAN_PICK')


class PCRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.server=create_server(Path(self.tmp.name),port=0);self.addCleanup(self.server.server_close)

    def test_sanitized_projection_does_not_infer_actual_game_patch(self):
        from coach_v1.pregame_contract import parse_input
        draft=draft_input(snapshot());parse_input(draft)
        self.assertIsNone(draft['patch'])
        self.assertEqual(draft['phase'],'PRE_GAME')
        self.assertEqual(len(draft['slots']),10)
        self.assertIsNone(draft_input(dict(snapshot(),phase='InProgress')))

    def test_session_rotation_and_stalled_connection_clear_old_input(self):
        service=PCServices(self.server)
        service._publish(snapshot(1));one=service.snapshot()['revision']
        service._publish(snapshot(2));self.assertGreater(service.snapshot()['revision'],one)
        service.observed=time.monotonic()-3
        view=service.snapshot()
        self.assertEqual(view['status'],'MANUAL_FALLBACK')
        self.assertIsNone(view['input'])

    def test_connect_loads_verified_roster_and_does_not_copy_source_patch(self):
        service=PCServices(self.server,lcu_lockfile=Path(self.tmp.name)/'lockfile',lcu_certificate_sha256='a'*64)
        with patch('coach_v1.lcu_draft.LCUDraftAdapter') as adapter:
            service._connect()
            args,kwargs=adapter.call_args
            self.assertEqual(args[1][51],'Caitlyn')
            self.assertNotIn('patch',kwargs)
            self.assertEqual(kwargs['certificate_sha256'],'a'*64)

    def test_slow_refresh_never_blocks_pick_phase_polling(self):
        entered=threading.Event();release=threading.Event();polled=threading.Event()
        def refresh():entered.set();release.wait(2)
        class Adapter:
            def poll(self):polled.set();return snapshot()
        def connect(service):service.adapter=Adapter()
        with patch('coach_v1.official_catalog.refresh_if_due',side_effect=refresh),patch('coach_v1.official_items.refresh_if_due'),patch.object(PCServices,'_connect',connect):
            service=start_pc_services(self.server)
            try:
                self.assertTrue(entered.wait(1))
                self.assertTrue(polled.wait(1),'maintenance must not block LCU phase reads')
            finally:release.set();service.close()

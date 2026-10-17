"""New public asset boundary plus the affected existing PC/auth routes only."""
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from coach_v1.server import Limits
from scripts.build_directions_web import build, FILES


class DirectionsHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from coach_v1.pregame_server import PregameWorkbench
        cls.temp=tempfile.TemporaryDirectory()
        cls.server=PregameWorkbench(Path(cls.temp.name)/'work.sqlite','synthetic-direction-test-token-not-a-credential',Limits(1_000_000,100,100,100,100,10))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.thread.join();cls.server.server_close();cls.temp.cleanup()

    def get(self,path):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=15)
        c.request('GET',path);r=c.getresponse();body=r.read();headers=dict(r.getheaders());c.close()
        return r.status,body,headers

    def test_new_public_learning_routes_and_preserved_pc_auth(self):
        for path in ['/directions','/directions-engine.js','/directions-data.json','/direction-assets/map11.png','/status.html']:
            status,body,headers=self.get(path)
            self.assertEqual(status,200,path);self.assertGreater(len(body),0)
            self.assertIn("img-src 'self'",headers['Content-Security-Policy'])
        self.assertEqual(self.get('/pc')[0],200)
        self.assertEqual(self.get('/dev/v1/pregame/pc-status')[0],401)
        self.assertEqual(self.get('/directions?token=fake')[0],400)
        self.assertNotEqual(self.get('/direction-assets/../../CURRENT_HANDOFF.md')[0],200)
        self.assertEqual(len(self.server.research.list()),0)

    def test_public_export_is_exact_allowlist_not_pc_or_private_store(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'site';manifest=build(out)
            files={str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}
            self.assertEqual(files,set(FILES.values())|{'build-info.json','.nojekyll'})
            self.assertEqual(set(manifest['sha256']),set(FILES.values()))
            self.assertFalse(manifest['live_game_connection'])
            self.assertIsNone(manifest['coaching_accuracy'])
            self.assertFalse(any('token' in p or 'sqlite' in p or 'pc.js' in p for p in files))
            self.assertEqual(json.loads((out/'directions-data.json').read_text())['strategy_level'],'DESIGN_HYPOTHESIS')


if __name__=='__main__':unittest.main()

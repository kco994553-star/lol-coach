"""Only new loading assets, changed public export, and affected PC auth boundary."""
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from coach_v1.server import Limits
from scripts.build_directions_web import build,FILES


class LoadingHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from coach_v1.pregame_server import PregameWorkbench
        cls.temp=tempfile.TemporaryDirectory()
        cls.server=PregameWorkbench(Path(cls.temp.name)/'work.sqlite','synthetic-loading-test-token-not-a-credential',Limits(1_000_000,100,100,100,100,10))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.thread.join();cls.server.server_close();cls.temp.cleanup()

    def get(self,path):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=15)
        c.request('GET',path);r=c.getresponse();body=r.read();headers=dict(r.getheaders());c.close()
        return r.status,body,headers

    def test_loading_assets_and_original_pc_access_boundary(self):
        for path in ['/loading','/loading.html','/loading-engine.js','/loading-exploration.js','/loading-interactive.js','/loading-map.js','/loading-data.json','/loading-assets/champion0.png','/skill-data.js','/skill-display.js']:
            status,body,headers=self.get(path);self.assertEqual(status,200,path)
            self.assertGreater(len(body),0);self.assertIn("img-src 'self'",headers['Content-Security-Policy'])
        self.assertEqual(self.get('/dev/v1/pregame/pc-status')[0],401)
        self.assertEqual(self.get('/loading?token=not-real')[0],400)
        self.assertNotEqual(self.get('/loading-assets/../../config/expert_runtime.json')[0],200)
        self.assertIn(b'10',self.get('/index.html')[1])
        self.assertIn(b'loading',self.get('/pc')[1])
        self.assertEqual(len(self.server.research.list()),0)

    def test_export_root_is_loading_and_six_scene_workbench_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'site';result=build(out)
            names={str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()}
            self.assertEqual(names,set(FILES.values())|{'build-info.json','.nojekyll'})
            self.assertIn(b'loading', (out/'index.html').read_bytes())
            self.assertIn(b'direction-app',(out/'directions.html').read_bytes())
            self.assertEqual(len(json.loads((out/'directions-data.json').read_text())['presets']),6)
            self.assertNotIn('pc.js',names)
            self.assertFalse(any('token' in p or 'sqlite' in p or 'ledger' in p for p in names))
            self.assertFalse(result['live_game_connection'])

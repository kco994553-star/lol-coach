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

    def test_pc_html_script_urls_are_accepted_by_server(self):
        import re
        html=self.get('/loading')[1].decode()
        for src in re.findall(r'<script src="\./([^" ]+)"',html):
            self.assertEqual(self.get('/'+src)[0],200,src)

    def test_public_html_versions_changed_scripts_by_exact_bytes(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'site';build(out);html=(out/'loading.html').read_text()
            for asset in ('loading.js','loading-coach-view.js','loading-presentation.js'):
                version=hashlib.sha256((out/asset).read_bytes()).hexdigest()[:16]
                self.assertIn('src="./'+asset+'?v='+version+'"',html)
            self.assertFalse((out/'tests_pregame').exists())

    def test_loading_assets_and_original_pc_access_boundary(self):
        for path in ['/home-assets/AsheBase.jpg', '/home-assets/AsheSkin17.jpg', '/home-assets/KaisaBase.jpg', '/home-assets/KaisaSkin14.jpg', '/home-assets/JinxBase.jpg', '/home-assets/JinxSkin4.jpg', '/home-assets/EzrealBase.jpg', '/home-assets/EzrealSkin21.jpg', '/home-assets/LuxBase.jpg', '/home-assets/LuxSkin17.jpg', '/home-assets/YasuoBase.jpg', '/home-assets/YasuoSkin9.jpg', '/home-assets/YoneBase.jpg', '/home-assets/YoneSkin1.jpg', '/home-assets/IreliaBase.jpg', '/home-assets/IreliaSkin37.jpg', '/home-assets/VayneBase.jpg', '/home-assets/VayneSkin25.jpg', '/home-assets/LeonaBase.jpg', '/home-assets/LeonaSkin10.jpg', '/home-assets/game-lane.webp', '/home-assets/game-operations.webp', '/home-assets/game-fight.webp']+['/loading-presentation.js','/loading-presentation.css','/loading-coach.js', '/loading-coach-view.js', '/loading-coach.css', '/loading-knowledge.json', '/loading-study.js','/home-assets/AhriSkin27.jpg','/home-assets/LuxSkin7.jpg','/home-assets/Moonlit.webp','/home-assets/strategy-objectives.webp','/coach-theme.css','/coach-shell.js','/hero-art.json','/home-assets/strategy-panels.webp','/home-assets/Ahri.jpg','/home-assets/Caitlyn.jpg','/home-assets/lane.jpg','/home-assets/fight.jpg','/loading','/loading.html','/loading-engine.js','/loading-exploration.js','/loading-interactive.js','/dashboard.html','/dashboard.js','/dashboard.css','/pro-dashboard.json','/loading-exchange.js','/loading-exchange-view.js','/loading-engagement.js','/loading-engagement-view.js','/loading-wave.js','/loading-wave-view.js','/loading-map.js','/loading-data.json','/loading-assets/champion0.png','/skill-data.js','/skill-display.js']:
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

    def test_public_art_sources_separate_official_splashes_from_ai_decoration(self):
        import hashlib
        catalog=json.loads(Path('web_r4/hero-art.json').read_text())
        registry=json.loads(Path('config/home_design_assets.json').read_text())
        official={r['path']:r for r in registry['assets']}
        refresh=json.loads(Path('config/art_refresh_assets.json').read_text())
        official.update({r['path']:r for r in refresh['official_skins']})
        gameplay=json.loads(Path('config/gameplay_cards_assets.json').read_text())
        official.update({r['path']:r for r in gameplay['backgrounds']})
        self.assertEqual(len(catalog['assets']),25)
        for r in gameplay['cards']:
            self.assertEqual(r['kind'],'ACTUAL_GAMEPLAY_STILL');self.assertFalse(r['ai_generated']);self.assertFalse(r['tactical_evidence'])
            self.assertEqual(r['sha256'],hashlib.sha256(Path(r['path']).read_bytes()).hexdigest())
        self.assertEqual({r['kind'] for r in catalog['assets']},{'OFFICIAL_STATIC_SPLASH','OFFICIAL_SKIN_SPLASH','GENERATED_DECORATION'})
        for row in catalog['assets']:
            path='web_r4/'+row['src'].removeprefix('./')
            self.assertEqual(row['sha256'],hashlib.sha256(Path(path).read_bytes()).hexdigest())
            if row['kind'].startswith('OFFICIAL_'):
                self.assertEqual(row['source_url'],official[path]['source_url'])
            else:
                self.assertIsNone(row['source_url'])
                self.assertFalse(refresh['generated']['hero']['official_riot_asset'])
                self.assertEqual(row['sha256'],refresh['generated']['hero']['sha256'])
        ai=json.loads(Path('config/shared_theme_assets.json').read_text())
        self.assertFalse(ai['official_riot_asset']);self.assertFalse(ai['tactical_evidence'])
        self.assertEqual(ai['sha256'],hashlib.sha256(Path(ai['public_path']).read_bytes()).hexdigest())
        self.assertLess(ai['public_webp_bytes'],ai['original_png_bytes'])

    def test_private_account_route_auth_and_missing_configuration(self):
        from coach_v1.account_dashboard import AccountDashboardService
        self.server.account_dashboard_service=AccountDashboardService(api_key='')
        def post(token=None):
            c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=15)
            headers={'Content-Type':'application/json'}
            if token:headers['Authorization']='Bearer '+token
            c.request('POST','/dev/v1/account/lookup',json.dumps({'riot_id':'synthetic-fixture#KR1','region':'KR'}),headers)
            r=c.getresponse();body=json.loads(r.read());status=r.status;c.close();return status,body
        self.assertEqual(post()[0],401)
        status,body=post(self.server.token);self.assertEqual(status,200);self.assertEqual(body['status'],'API_UNAVAILABLE');self.assertEqual(body['provider_requests'],0)

    def test_direction_profiles_are_served_exported_and_browser_bound(self):
        import hashlib
        import ast
        asset='loading-direction-profiles.js'
        expected=Path('web_r4',asset).read_bytes()
        status,body,headers=self.get('/'+asset)
        self.assertEqual(status,200)
        self.assertEqual(body,expected)
        self.assertIn('javascript',headers['Content-Type'])
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'site';manifest=build(out)
            self.assertEqual((out/asset).read_bytes(),expected)
            self.assertEqual(manifest['sha256'][asset],hashlib.sha256(expected).hexdigest())
        # Read only the source inventory without importing Playwright or launching a browser.
        tree=ast.parse(Path('scripts/browser_loading.py').read_text())
        assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCES' for t in n.targets))
        scope={};exec(compile(ast.Module(body=[assignment],type_ignores=[]),'inventory','exec'),scope)
        self.assertIn('web_r4/'+asset,scope['SOURCES'])

"""New public projections and authenticated selection preserve PC boundaries."""
import hashlib
import re
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from coach_v1.champion_insights import select_insights
from scripts.build_directions_web import build, FILES, ROOT
from scripts.launch_pc import create_server


class ChampionInsightsHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.server = create_server(Path(cls.temp.name) / 'private', port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()
        cls.temp.cleanup()

    def request(self, method, path, value=None, auth=False):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=15)
        headers = {'Content-Type': 'application/json'}
        if auth:
            headers['Authorization'] = 'Bearer ' + self.server.token
        conn.request(method, path, json.dumps(value) if value is not None else None, headers)
        response = conn.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        conn.close()
        return result

    def test_public_entry_dependencies_have_exact_content_versions(self):
        # A new entry page must not load a cached pre-tier state or return adapter.
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'public'
            build(out)
            for page in ('champion.html', 'champions.html', 'loading.html'):
                public = (out / page).read_text()
                original = (ROOT / 'web_r4' / page).read_text()
                assets = re.findall(r'(?:src|href)="\./([^"?]+\.(?:js|css))"', original)
                self.assertTrue(assets)
                for asset in assets:
                    with self.subTest(page=page, asset=asset):
                        version = hashlib.sha256((ROOT / 'web_r4' / asset).read_bytes()).hexdigest()[:16]
                        self.assertIn('./' + asset + '?v=' + version + '"', public)
                        self.assertNotIn('./' + asset + '?', original)

    def test_public_projection_allowlist_and_private_exclusions(self):
        names = ('champion-insights.js', 'champion-insights.json', 'champion-matchup-knowledge.json')
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'public'
            manifest = build(out)
            for name in names:
                with self.subTest(name=name):
                    self.assertIn(name, FILES)
                    status, body, headers = self.request('GET', '/' + name)
                    self.assertEqual(status, 200)
                    self.assertEqual(body, (ROOT / 'web_r4' / name).read_bytes())
                    self.assertEqual((out / name).read_bytes(), body)
                    self.assertIn(name, manifest['sha256'])
                    self.assertIn("script-src 'self'", headers['Content-Security-Policy'])
                    self.assertEqual(self.request('GET', '/' + name + '?key=bad')[0], 400)
        for name in ('matchup-results.json', 'matchup-complete.json', 'config/champion_matchup_references.json'):
            self.assertIn(self.request('GET', '/' + name)[0], (401, 404))

    def test_authenticated_default_and_each_tier_match_pure_selection(self):
        request = {'champion': 'Caitlyn', 'position': 'BOTTOM'}
        self.assertEqual(self.request('POST', '/dev/v1/champion/insights', request)[0], 401)
        data = json.loads((ROOT / 'web_r4/champion-insights.json').read_text())
        for tier in ('MASTER_PLUS', 'ALL', 'IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER'):
            status, body, _ = self.request('POST', '/dev/v1/champion/insights', dict(request, tier=tier), True)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body), select_insights(data, 'Caitlyn', 'BOTTOM', tier))
        status, body, _ = self.request('POST', '/dev/v1/champion/insights', request, True)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['scope']['tier'], 'MASTER_PLUS')
        self.assertEqual(len(self.server.research.list()), 0)

    def test_malformed_or_private_request_never_falls_back(self):
        base = {'champion': 'Caitlyn', 'position': 'BOTTOM'}
        for change in ({'tier': 'UNREGISTERED'}, {'tier': None}, {'patch': '../../private'}, {'position': 'ADC'}, {'champion': '../Caitlyn'}, {'riot_id': 'not-for-public'}):
            self.assertEqual(self.request('POST', '/dev/v1/champion/insights', dict(base, **change), True)[0], 422, change)
        self.assertEqual(self.request('POST', '/dev/v1/champion/insights?token=bad', base, True)[0], 400)

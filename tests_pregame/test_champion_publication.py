"""Public champion publication boundaries, served bytes, and export receipts."""
import hashlib
import http.client
import json
from pathlib import Path
import re
import tempfile
import threading
import unittest
from urllib.parse import urlsplit

from scripts.build_directions_web import FILES, ROOT, build
from scripts.launch_pc import create_server

CHAMPION_ASSETS = (
    'champions.html', 'champion.html', 'champion.css', 'champion-picker.js',
    'champion-page.js', 'champion-state.js', 'champion-stats.json', 'loading-draft.js',
    'loading-champion-baseline.js',
)


class ChampionPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='champion-publication-')
        cls.server = create_server(Path(cls.temporary.name) / 'private', port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()
        cls.temporary.cleanup()

    def get(self, path):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=15)
        connection.request('GET', path)
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result

    def test_pc_assets_are_exact_bytes_without_query_or_auth_relaxation(self):
        for asset in CHAMPION_ASSETS:
            with self.subTest(asset=asset):
                status, body, headers = self.get('/' + asset)
                self.assertEqual(status, 200)
                self.assertEqual(body, (ROOT / 'web_r4' / asset).read_bytes())
                self.assertIn("script-src 'self'", headers['Content-Security-Policy'])
                self.assertEqual(self.get('/' + asset + '?v=fake')[0], 400)
        for alias in ('champions', 'champion'):
            status, body, _ = self.get('/' + alias)
            self.assertEqual(status, 200)
            self.assertEqual(body, (ROOT / 'web_r4' / (alias + '.html')).read_bytes())
        for page in ('champions.html', 'champion.html', 'loading.html'):
            html = self.get('/' + page)[1].decode()
            for target in re.findall(r'(?:src|href)=["\']([^"\']+)["\']', html):
                if target.startswith(('./', '/')) and not target.startswith('//'):
                    self.assertFalse(urlsplit(target).query, (page, target))
        self.assertEqual(self.get('/dev/v1/pregame/pc-status')[0], 401)
        self.assertEqual(len(self.server.research.list()), 0)

    def test_export_contains_champion_assets_and_only_explicit_public_files(self):
        self.assertTrue(set(CHAMPION_ASSETS).issubset(FILES), 'champion assets must be explicit export inputs')
        with tempfile.TemporaryDirectory(prefix='champion-export-') as temp:
            output = Path(temp) / 'lol-coach'
            manifest = build(output)
            actual = {str(path.relative_to(output)) for path in output.rglob('*') if path.is_file()}
            self.assertEqual(actual, set(FILES.values()) | {'build-info.json', '.nojekyll'})
            self.assertEqual(set(manifest['sha256']), set(FILES.values()))
            for name, digest in manifest['sha256'].items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest, name)
            forbidden = ('access-token', '.sqlite', '.env', 'pc.html', 'pc.js', 'pc.css', 'research', 'private', 'raw')
            self.assertFalse([name for name in actual if any(part in name for part in forbidden)])
            self.assertFalse(manifest['live_game_connection'])
            self.assertIsNone(manifest['coaching_accuracy'])
            stats = json.loads((output / 'champion-stats.json').read_text())
            self.assertEqual(stats['format'], 'lol-coach-champion-statistics-v1')
            self.assertEqual(stats['draw_min_n'], 100)
            self.assertTrue({'runes', 'item_builds', 'skill_order', 'pick_rate', 'ban_rate'}.issubset(stats['unsupported_metrics']))
            for page in ('champions.html', 'champion.html'):
                html = (output / page).read_text()
                for target in re.findall(r'(?:src|href)=["\']([^"\']+)["\']', html):
                    parsed = urlsplit(target)
                    if target.startswith('./') and parsed.path:
                        self.assertTrue((output / parsed.path).is_file(), (page, target))
            self.assertEqual(len(self.server.research.list()), 0)

    def test_current_feature_matrix_is_complete_when_present(self):
        path = ROOT / 'docs/gameplan-content/frontend-v2-feature-matrix.json'
        if not path.is_file():
            self.skipTest('current matrix has not been authored yet; no coverage claim')
        matrix = json.loads(path.read_text())
        rows = matrix['features']
        self.assertEqual(len(rows), 160)
        self.assertEqual(len({row['id'] for row in rows}), 160)
        contract = (ROOT / 'contracts/information-architecture-v1.md').read_text()
        body, appendices = contract.split('## 부록 A.', 1)
        canonical_ids = re.findall(r'^\| (\d+\.\d+\.\d+(?:\.\d+)?) \|', body, re.M)
        self.assertEqual([row['id'] for row in rows], canonical_ids)
        historical = appendices.split('## 부록 B.', 1)[0]
        historical_pairs = re.findall(r'^\| (\d+(?:\.\d+){2,3}) \| (\d+(?:\.\d+){2,3}) \|', historical, re.M)
        self.assertEqual(len(historical_pairs), 125)
        self.assertEqual({row['id']: row['legacy_id'] for row in rows if row['legacy_id']},
                         {current: old for old, current in historical_pairs})
        required = {'name', 'purpose', 'existing', 'missing', 'input', 'output',
                    'exceptions', 'done', 'test', 'dependency', 'risk', 'status', 'evidence'}
        for row in rows:
            with self.subTest(id=row['id']):
                self.assertTrue(required.issubset(row))
                self.assertTrue(all(row[key] for key in required - {'evidence'}))
                self.assertIn(row['status'], {'NOT_STARTED', 'IMPLEMENTED', 'TESTED', 'INTEGRATED', 'DEPLOYED', 'LIVE_VERIFIED'})
                if row['status'] in {'TESTED', 'INTEGRATED', 'DEPLOYED', 'LIVE_VERIFIED'}:
                    self.assertTrue(row['evidence'], 'advanced status rows need current evidence')


if __name__ == '__main__':
    unittest.main()

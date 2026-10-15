"""Local launcher checks; no Windows installation or real LCU is simulated."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, parse_qs


class PCLauncherTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.launch_pc'), 'PC launcher is missing')
        from scripts import launch_pc
        self.launcher = launch_pc
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def server(self):
        server = self.launcher.create_server(Path(self.tmp.name) / 'private', port=0)
        self.addCleanup(server.server_close)
        return server

    def test_server_is_loopback_private_token_and_browser_fragment_only(self):
        server = self.server()
        self.assertEqual(server.server_address[0], '127.0.0.1')
        self.assertGreaterEqual(len(server.token), 43)
        url = self.launcher.browser_url(server)
        parsed = urlsplit(url)
        self.assertEqual(parsed.path, '/pc')
        self.assertEqual(parsed.query, '')
        self.assertEqual(parse_qs(parsed.fragment), {'token': [server.token]})
        self.assertNotIn(server.token, url.split('#')[0])
        token_file = Path(self.tmp.name) / 'private' / 'access-token'
        self.assertEqual(token_file.read_text().strip(), server.token)
        if __import__('os').name != 'nt':
            self.assertEqual(token_file.stat().st_mode & 0o777, 0o600)

    def test_token_rotates_without_putting_token_in_console_output(self):
        first = self.server()
        first_token = first.token
        first.server_close()
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            second = self.launcher.create_server(Path(self.tmp.name) / 'private', port=0)
            self.launcher.print_ready(second)
        self.addCleanup(second.server_close)
        self.assertNotEqual(first_token, second.token)
        self.assertNotIn(first_token, capture.getvalue())
        self.assertNotIn(second.token, capture.getvalue())
        self.assertIn('/pc', capture.getvalue())

    def test_http_status_requires_bearer_token_and_page_hides_token(self):
        server = self.server()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        origin = self.launcher.browser_url(server).split('#')[0]
        with urlopen(origin, timeout=3) as response:
            page = response.read().decode('utf-8')
        self.assertIn('pc.js', page)
        self.assertNotIn(server.token, page)
        endpoint = origin.replace('/pc', '/dev/v1/pregame/pc-status')
        with self.assertRaises(HTTPError) as caught:
            urlopen(endpoint, timeout=3)
        self.assertEqual(caught.exception.code, 401)
        request = Request(endpoint, headers={'Authorization': 'Bearer ' + server.token})
        with urlopen(request, timeout=3) as response:
            self.assertEqual(response.status, 200)
            self.assertNotIn(server.token.encode(), response.read())

    def test_rejects_unsafe_existing_token_symlink_and_invalid_port(self):
        root = Path(self.tmp.name) / 'unsafe'
        root.mkdir()
        target = Path(self.tmp.name) / 'untouched'
        target.write_text('keep')
        try:
            (root / 'access-token').symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('symlink unavailable')
        with self.assertRaises(ValueError):
            self.launcher.create_server(root, port=0)
        self.assertEqual(target.read_text(), 'keep')
        for port in (-1, 65536):
            with self.assertRaises(ValueError):
                self.launcher.create_server(root, port=port)

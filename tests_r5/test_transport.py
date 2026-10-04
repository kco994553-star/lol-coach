"""Synthetic loopback TLS transport tests; these are NOT actual LoL evidence.

An ephemeral self-signed certificate and fake HTTPS endpoint exercise the exact
fixed GAME_URL. No Riot/client payloads, accounts, or certificates are used.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import tempfile
import threading
import unittest
import urllib.error
from unittest.mock import patch

from coach_intake.io import GAME_URL, fetch


class FakeGameHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.paths.append(self.path)
        if self.server.redirect:
            self.send_response(302)
            self.send_header('Location', 'https://127.0.0.1:2999/must-not-follow')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        body = b'{"synthetic_transport_only":true,"coaching_enabled":false}'
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class LocalSyntheticTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        executable = shutil.which('openssl')
        if executable is None:
            raise unittest.SkipTest('SYNTHETIC_TLS_NOT_RUN: openssl unavailable')
        cls.directory = tempfile.TemporaryDirectory(prefix='lol-fake-tls-')
        cls.addClassCleanup(cls.directory.cleanup)
        root = Path(cls.directory.name)

        def certificate(name):
            cert, key = root / (name + '.pem'), root / (name + '.key')
            subprocess.run([
                executable, 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                '-days', '1', '-subj', '/CN=SYNTHETIC-TRANSPORT-NOT-RIOT',
                '-addext', 'subjectAltName=IP:127.0.0.1',
                '-addext', 'basicConstraints=critical,CA:TRUE',
                '-keyout', str(key), '-out', str(cert),
            ], check=True, capture_output=True, timeout=30)
            return cert, key

        cls.trusted_cert, key = certificate('trusted')
        cls.unrelated_cert, _ = certificate('unrelated')
        try:
            cls.server = ThreadingHTTPServer(('127.0.0.1', 2999), FakeGameHandler)
        except OSError as error:
            raise unittest.SkipTest(
                'SYNTHETIC_TLS_NOT_RUN: fixed loopback port 2999 unavailable '
                f'(errno={error.errno})'
            ) from None
        cls.addClassCleanup(cls.server.server_close)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(cls.trusted_cert), str(key))
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        cls.server.redirect = False
        cls.server.paths = []
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.stop_server)

    @classmethod
    def stop_server(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=3)

    def setUp(self):
        self.server.redirect = False
        self.server.paths.clear()

    def test_matching_ca_accepted_and_environment_proxy_ignored(self):
        # An unreachable proxy would break this if local payloads used env proxy.
        proxy = 'http://127.0.0.1:1'
        with patch.dict(os.environ, {
            'HTTP_PROXY': proxy, 'HTTPS_PROXY': proxy, 'ALL_PROXY': proxy,
            'http_proxy': proxy, 'https_proxy': proxy, 'all_proxy': proxy,
            'NO_PROXY': '', 'no_proxy': '',
        }):
            raw = fetch(GAME_URL, limit=1024, timeout=3, ca=self.trusted_cert)
        self.assertEqual(raw, b'{"synthetic_transport_only":true,"coaching_enabled":false}')
        self.assertEqual(self.server.paths, ['/liveclientdata/allgamedata'])

    def test_untrusted_certificate_rejected_before_payload(self):
        with self.assertRaises(urllib.error.URLError) as caught:
            fetch(GAME_URL, limit=1024, timeout=3, ca=self.unrelated_cert)
        self.assertIsInstance(caught.exception.reason, ssl.SSLCertVerificationError)
        self.assertEqual(self.server.paths, [])

    def test_redirect_refused_without_followup_request(self):
        self.server.redirect = True
        with self.assertRaisesRegex(ValueError, '^REDIRECT_REFUSED$'):
            fetch(GAME_URL, limit=1024, timeout=3, ca=self.trusted_cert)
        self.assertEqual(self.server.paths, ['/liveclientdata/allgamedata'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

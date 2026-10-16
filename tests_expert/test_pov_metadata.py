"""Metadata-only fixtures; never use credentials, media, or network."""
import contextlib
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit


def config():
    return {'format': 'lol-coach-pov-channels-v1', 'category': 'POV', 'checked_at': None,
            'verification_status': 'USER_PROVIDED_PENDING_VERIFICATION', 'channels': [
                {'channel_id': 'UC' + 'a' * 22, 'handle': '@Alpha'},
                {'channel_id': 'UC' + 'b' * 22, 'handle': '@Beta'}]}


class MetadataHTTP:
    def __init__(self, change=None):
        self.calls = []
        self.change = change

    def __call__(self, method, url, headers, body, timeout, max_bytes):
        self.calls.append((method, url, headers, body, timeout, max_bytes))
        endpoint = urlsplit(url).path.rsplit('/', 1)[-1]
        query = parse_qs(urlsplit(url).query)
        if endpoint == 'channels':
            letter = ('a' if query.get('forHandle', [''])[0].lower() == '@alpha' else 'b') if 'forHandle' in query else query['id'][0][2]
            value = {'items': [{'id': 'UC' + letter * 22,
                'snippet': {'title': letter.upper(), 'customUrl': '@Alpha' if letter == 'a' else '@Beta', 'description': 'DO_NOT_EXPORT'},
                'contentDetails': {'relatedPlaylists': {'uploads': 'UU' + letter * 22}}}]}
        elif endpoint == 'playlistItems':
            letter = query['playlistId'][0][2]
            value = {'items': [{'contentDetails': {'videoId': letter * 11}}]}
        elif endpoint == 'videos':
            letter = query['id'][0][0]
            value = {'items': [{'id': letter * 11, 'snippet': {'channelId': 'UC' + letter * 22,
                'title': 'Player Champion vs Opponent 2026/10/12', 'publishedAt': '2026-10-13T00:00:00Z',
                'description': 'DO_NOT_EXPORT', 'liveBroadcastContent': 'none'},
                'contentDetails': {'duration': 'PT43M38S'},
                'status': {'privacyStatus': 'public', 'uploadStatus': 'processed'}}]}
        else:
            raise AssertionError('Unexpected endpoint')
        if self.change:
            changed = self.change(endpoint, query, value)
            if changed is not None:
                return changed
        return 200, {}, json.dumps(value).encode()


class PovMetadataTests(unittest.TestCase):
    def verify(self, http, cfg=None, key='TEST_ONLY_KEY'):
        try:
            from coach_v1.pov_metadata import verify_channels
        except ImportError:
            self.fail('Metadata-only verifier has not been implemented')
        return verify_channels(cfg or config(), key, transport=http, now=lambda: 1792148400)

    def test_verified_canonical_metadata_retains_only_public_allowlist(self):
        cfg = config(); original = deepcopy(cfg); http = MetadataHTTP()
        report = self.verify(http, cfg)
        self.assertEqual(report['status'], 'VERIFIED_METADATA')
        self.assertEqual(report['category'], 'POV'); self.assertFalse(report['expert_source'])
        self.assertEqual(report['request_counts'], {'METADATA': 8, 'TEXT_PROBE': 0, 'VIDEO_CLIP': 0})
        self.assertEqual(cfg, original)
        self.assertEqual(len(report['channels']), 2)
        for channel in report['channels']:
            self.assertEqual(channel['verification_status'], 'CANONICAL_CHANNEL_METADATA_VERIFIED')
            self.assertEqual(len(channel['videos']), 1)
            video = channel['videos'][0]
            self.assertEqual(video['duration_seconds'], 2618)
            self.assertEqual(video['published_at'], '2026-10-13T00:00:00Z')
            for key in ('game_date', 'patch', 'opponent', 'game_link', 'view_type', 'continuity', 'intent'):
                self.assertEqual(video[key], 'UNKNOWN')
        self.assertEqual(len(report['sources']), 8)
        for source in report['sources']:
            self.assertEqual(len(source['response_sha256']), 64)
            self.assertEqual(source['checked_at'], report['checked_at'])
        serialized = json.dumps(report)
        self.assertNotIn('DO_NOT_EXPORT', serialized); self.assertNotIn('TEST_ONLY_KEY', serialized)
        for method, url, headers, body, _, _ in http.calls:
            self.assertEqual(method, 'GET'); self.assertIsNone(body)
            self.assertEqual(headers['x-goog-api-key'], 'TEST_ONLY_KEY')
            self.assertNotIn('key=', url)
            self.assertEqual(urlsplit(url).hostname, 'www.googleapis.com')

    def test_handle_mismatch_empty_and_malformed_fail_without_playlist_lookup(self):
        for kind in ('mismatch', 'empty', 'malformed'):
            def change(endpoint, query, value):
                if endpoint == 'channels' and 'forHandle' in query:
                    if kind == 'mismatch': value['items'][0]['id'] = 'UC' + 'z' * 22
                    elif kind == 'empty': value['items'] = []
                    else: return 200, {}, b'{not-json TEST_ONLY_KEY'
            http = MetadataHTTP(change); report = self.verify(http)
            self.assertEqual(report['status'], 'PARTIAL')
            self.assertTrue(all(c['verification_status'] != 'CANONICAL_CHANNEL_METADATA_VERIFIED' for c in report['channels']))
            self.assertEqual(report['request_counts']['METADATA'], 4)
            self.assertNotIn('TEST_ONLY_KEY', json.dumps(report))

    def test_failures_are_safe_typed_no_retries_and_other_channel_still_runs(self):
        for failure, expected in ((TimeoutError('TEST_ONLY_KEY'), 'NETWORK_TIMEOUT'),
                                  (RuntimeError('TEST_ONLY_KEY'), 'NETWORK_FAILURE'),
                                  ((403, {}, b'{"error":"TEST_ONLY_KEY"}'), 'HTTP_FAILURE')):
            def change(endpoint, query, value):
                if endpoint == 'channels' and query.get('id') == ['UC' + 'a' * 22]:
                    if isinstance(failure, Exception): raise failure
                    return failure
            report = self.verify(MetadataHTTP(change))
            self.assertEqual(report['status'], 'PARTIAL')
            self.assertEqual(report['channels'][0]['reason'], expected)
            self.assertEqual(report['channels'][1]['verification_status'], 'CANONICAL_CHANNEL_METADATA_VERIFIED')
            self.assertEqual(report['request_counts']['METADATA'], 5)
            self.assertNotIn('TEST_ONLY_KEY', json.dumps(report))

    def test_nonpublic_unprocessed_foreign_and_live_videos_are_excluded(self):
        for mutation in ('private', 'processing', 'foreign', 'live'):
            def change(endpoint, query, value):
                if endpoint == 'videos':
                    item = value['items'][0]
                    if mutation == 'private': item['status']['privacyStatus'] = 'private'
                    elif mutation == 'processing': item['status']['uploadStatus'] = 'uploaded'
                    elif mutation == 'foreign': item['snippet']['channelId'] = 'UC' + 'z' * 22
                    else: item['snippet']['liveBroadcastContent'] = 'live'
            report = self.verify(MetadataHTTP(change))
            self.assertEqual(sum(len(c['videos']) for c in report['channels']), 0)
            self.assertEqual(report['status'], 'PARTIAL')

    def test_missing_key_and_invalid_or_excess_channels_make_zero_requests(self):
        cases = [(config(), ''), ({**config(), 'channels': config()['channels'] * 10}, 'key'),
                 ({**config(), 'category': 'EXPERT'}, 'key'),
                 ({**config(), 'channels': [{'channel_id': '../bad', 'handle': '@x'}]}, 'key')]
        for cfg, key in cases:
            http = MetadataHTTP(); report = self.verify(http, cfg, key)
            self.assertEqual(report['status'], 'BLOCKED_EXTERNAL')
            self.assertEqual(report['request_counts']['METADATA'], 0)
            self.assertEqual(http.calls, [])

    def test_request_size_and_upload_count_are_bounded(self):
        def change(endpoint, query, value):
            if endpoint == 'playlistItems':
                self.assertEqual(query['maxResults'], ['3'])
                value['items'] = [{'contentDetails': {'videoId': str(i).zfill(11)}} for i in range(200)]
        http = MetadataHTTP(change); report = self.verify(http)
        self.assertLessEqual(report['request_counts']['METADATA'], 12)
        for _, url, _, _, timeout, max_bytes in http.calls:
            self.assertLessEqual(timeout, 30); self.assertLessEqual(max_bytes, 1_000_000)
            if '/videos?' in url: self.assertLessEqual(len(parse_qs(urlsplit(url).query)['id'][0].split(',')), 3)

    def test_cli_binds_actual_report_bytes_and_sources_without_config_mutation(self):
        try:
            from scripts import verify_pov_metadata as cli
        except ImportError:
            self.fail('Metadata-only CLI has not been implemented')
        from coach_v1 import expert_collector
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); cfg = root/'channels.json'; cfg.write_text(json.dumps(config())); before = cfg.read_bytes()
            out = root/'output'; stdout = io.StringIO()
            with patch.dict(os.environ, {'YOUTUBE_API_KEY': 'TEST_ONLY_KEY'}, clear=True), \
                 patch.object(expert_collector, '_transport', MetadataHTTP()), contextlib.redirect_stdout(stdout):
                code = cli.main(['--config', str(cfg), '--output-dir', str(out)], clock=lambda: 1792148400)
            self.assertEqual(code, 0); self.assertEqual(cfg.read_bytes(), before)
            report_bytes = (out/'pov-metadata.json').read_bytes()
            binding = json.loads((out/'metadata-binding.json').read_text())
            self.assertEqual(binding['report_sha256'], hashlib.sha256(report_bytes).hexdigest())
            self.assertEqual(binding['request_counts']['METADATA'], 8)
            self.assertRegex(binding['source_commit'], r'^[0-9a-f]{40}$')
            self.assertEqual(len(binding['source_sha256']), 4)
            self.assertIn('contracts/actual-evidence-v1.md', binding['source_sha256'])
            self.assertNotIn('TEST_ONLY_KEY', report_bytes.decode()+json.dumps(binding)+stdout.getvalue())
            self.assertEqual(set(p.name for p in out.iterdir()), {'pov-metadata.json', 'metadata-binding.json'})

    def test_cli_config_hash_binds_the_bytes_actually_used_for_discovery(self):
        from scripts import verify_pov_metadata as cli
        from coach_v1 import expert_collector
        with tempfile.TemporaryDirectory() as temp:
            cfg = Path(temp)/'config.json'; cfg.write_text(json.dumps(config())); original = cfg.read_bytes()
            def change(endpoint, query, value):
                cfg.write_text('{"changed_after_read":true}')
            out = Path(temp)/'out'
            with patch.dict(os.environ, {'YOUTUBE_API_KEY': 'TEST_ONLY_KEY'}, clear=True), \
                 patch.object(expert_collector, '_transport', MetadataHTTP(change)), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(['--config', str(cfg), '--output-dir', str(out)]), 0)
            binding = json.loads((out/'metadata-binding.json').read_text())
            self.assertEqual(binding['source_sha256'][str(cfg)], hashlib.sha256(original).hexdigest())


if __name__ == '__main__': unittest.main()

import base64
import hashlib
import unittest
from coach_v1.capture import envelope,NoRedirect,ENDPOINT

class CaptureTests(unittest.TestCase):
    def test_raw_preservation_and_no_promotion(self):
        raw=b'{ "gameData": {"gameTime": 0}, "activePlayer": null }'
        result=envelope(raw,'2026-10-04T00:00:00+00:00')
        self.assertEqual(base64.b64decode(result['raw_base64']),raw)
        self.assertEqual(result['raw_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertFalse(result['coaching_enabled']);self.assertFalse(result['game_end_verified'])
        self.assertEqual(result['evidence_kind'],'UNVERIFIED_LOCAL_CAPTURE')
    def test_bad_json_and_redirect_refused(self):
        for raw in (b'[]',b'{',b'{"x":NaN}'):
            with self.assertRaises(ValueError):envelope(raw,'now')
        with self.assertRaises(ValueError):NoRedirect().redirect_request(None,None,302,'',{},'https://example.com')
        self.assertEqual(ENDPOINT,'https://127.0.0.1:2999/liveclientdata/allgamedata')

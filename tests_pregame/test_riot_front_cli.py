"""Main CLI integration receipt; no real Riot requests or credentials."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.collect_power_stats import main
from tests_pregame.test_riot_diagnostics import TEST_KEY

class RiotFrontCliTests(unittest.TestCase):
    def test_collection403_retains_only_bounded_safe_front_observation(self):
        def response(*_):
            return 403,{'Content-Type':'text/html','Server':'gateway','CF-Ray':'PRIVATE_MARKER'},b'<html>Forbidden '+TEST_KEY.encode()+b'</html>'
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);log=io.StringIO()
            with patch.dict(os.environ,{'RIOT_API_KEY':TEST_KEY},clear=True),\
                    patch('coach_v1.riot_collector._transport',response),contextlib.redirect_stdout(log):
                code=main(['--output',str(out/'power.json'),'--diagnostics-output',str(out/'diagnostics.json')])
            self.assertEqual(code,0);diagnostic=json.loads((out/'diagnostics.json').read_text())
            self.assertEqual(diagnostic['schema_version'],'riot.diagnostics.v2')
            self.assertEqual(diagnostic['front_errors'][0]['http_status'],403)
            self.assertFalse(diagnostic['front_errors'][0]['is_json'])
            self.assertTrue(diagnostic['front_errors'][0]['markers']['cf-ray'])
            self.assertNotIn(TEST_KEY,log.getvalue()+json.dumps(diagnostic))
            self.assertNotIn('PRIVATE_MARKER',log.getvalue()+json.dumps(diagnostic))
            self.assertEqual(diagnostic['request_count'],1);self.assertEqual(diagnostic['retry_count'],0)

if __name__=='__main__':unittest.main()

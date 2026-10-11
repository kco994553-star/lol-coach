"""Injected Riot diagnostics only; synthetic keys and no provider requests."""
import importlib.util
from contextlib import redirect_stdout
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import quote

from coach_v1.riot_collector import RiotCollector, _transport
from tests_pregame.test_riot_collector import Clock, Responses, okay

TEST_KEY='RGAPI-00000000-0000-4000-8000-000000000000'


class RiotDiagnosticsTests(unittest.TestCase):
    def collector(self,key,responses,**kwargs):
        self.http=Responses(responses);clock=Clock()
        return RiotCollector(key,transport=self.http,clock=clock.now,sleeper=clock.sleep,**kwargs)

    def collect(self,c):return c.collect(tier='CHALLENGER',patch='16.19',collect_items=False)

    def test_outer_whitespace_trimmed_before_header_shape_only_callback(self):
        observed=[];raw=' \n'+TEST_KEY+'\r\n'
        c=self.collector(raw,[okay({'entries':[]})],on_key_shape=observed.append)
        result=self.collect(c)
        self.assertEqual(result['status'],'INSUFFICIENT_DATA')
        self.assertEqual(self.http.headers[0]['X-Riot-Token'],TEST_KEY)
        self.assertEqual(observed,[dict(raw_length=len(raw),normalized_length=42,raw_has_prefix=False,
            normalized_has_prefix=True,has_outer_whitespace=True,contains_line_break=True,valid_shape=True)])
        self.assertNotIn(TEST_KEY,json.dumps(observed))

    def test_invalid_shapes_stop_with_zero_requests_and_no_inferred_auth_status(self):
        for raw in ('PRIVATE_INVALID',' RGAPI-not-a-uuid ',TEST_KEY[:15]+'\n'+TEST_KEY[15:],'rgapi-'+TEST_KEY[6:],''):
            c=self.collector(raw,[]);result=self.collect(c)
            self.assertEqual(result['status'],'BLOCKED_EXTERNAL');self.assertEqual(self.http.urls,[])
            self.assertEqual(c.requests,0);self.assertIsNone(c.first_http_status)
            self.assertFalse(c.key_shape['valid_shape'])
            self.assertEqual(result['source']['collection']['reason'],'MISSING_API_KEY' if raw=='' else 'INVALID_API_KEY_SHAPE')

    def test_401_403_selected_message_no_auth_retry_and_all_key_variants_redacted(self):
        for status,message in [(403,'Forbidden'),(401,'Unknown apikey '+TEST_KEY)]:
            observed=[];raw=' '+TEST_KEY+'\n'
            message+=' '+quote(raw,safe='')+' https://example.invalid/?key='+TEST_KEY+' Authorization: '+TEST_KEY
            c=self.collector(raw,[(status,{},dict(status=dict(message=message,status_code=status),raw='PRIVATE_RAW_BODY'))],
                on_http_error=observed.append)
            result=self.collect(c)
            self.assertEqual(c.requests,1);self.assertEqual(c.retries,0)
            self.assertEqual(result['status'],'BLOCKED_EXTERNAL');self.assertEqual(c.first_http_status,status)
            self.assertEqual(observed,c.http_errors);self.assertEqual(len(observed),1)
            diagnostic=observed[0]
            self.assertEqual(diagnostic['http_status'],status)
            self.assertIsNone(diagnostic['error_status']);self.assertIsNone(diagnostic['error_code'])
            self.assertTrue(diagnostic['error_message'].startswith(message.split(' ')[0]))
            self.assertEqual(diagnostic['reason'],'UNAUTHORIZED_OR_EXPIRED_OR_UNSUPPORTED_PATH')
            for forbidden in (TEST_KEY,quote(raw,safe=''),'PRIVATE_RAW_BODY','example.invalid'):
                self.assertNotIn(forbidden,json.dumps(observed)+json.dumps(result))

    def test_non_json_and_network_diagnostics_are_null_with_fixed_reasons(self):
        for response,code,reason in [((403,{},b'PRIVATE_NOT_JSON'),403,'UNAUTHORIZED_OR_EXPIRED_OR_UNSUPPORTED_PATH'),
                                   (OSError('PRIVATE_EXCEPTION '+TEST_KEY),None,'NETWORK_FAILURE')]:
            c=self.collector(TEST_KEY,[response],max_retries=0);self.collect(c)
            self.assertEqual(c.http_errors,[dict(http_status=code,error_status=None,error_code=None,
                error_message=None,reason=reason)])
            self.assertNotIn('PRIVATE',json.dumps(c.http_errors))

    def test_http_error_body_read_is_bounded_and_unparsed_oversize_is_not_saved(self):
        class BoundedBody(BytesIO):
            sizes=[]
            def read(self,size=-1):
                self.sizes.append(size);return super().read(size)
        body=BoundedBody(b'x'*100000)
        error=HTTPError('https://kr.api.riotgames.com/TEST',403,'Forbidden',{},body)
        with patch('coach_v1.riot_collector.build_opener') as opener:
            opener.return_value.open.side_effect=error
            code,headers,raw=_transport('https://kr.api.riotgames.com/TEST',{'X-Riot-Token':TEST_KEY},1)
        self.assertEqual(body.sizes,[65537]);self.assertEqual(len(raw),65537);self.assertEqual(code,403)
        c=self.collector(TEST_KEY,[(code,headers,raw)]);self.collect(c)
        self.assertIsNone(c.http_errors[0]['error_message'])
        self.assertLess(len(json.dumps(c.http_errors)),250)

    def cli(self):
        spec=importlib.util.spec_from_file_location('riot_diagnostics_cli','scripts/collect_power_stats.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

    def test_cli_invalid_key_diagnostic_only_clears_stale_aggregates_without_http(self):
        cli=self.cli()
        with tempfile.TemporaryDirectory() as td:
            power=Path(td)/'power.json';movement=Path(td)/'movement.json';outcome=Path(td)/'outcome.json'
            diagnostics=Path(td)/'diagnostics.json'
            for path in (power,movement,outcome):path.write_text('STALE_AGGREGATE')
            output=StringIO()
            with patch.dict(os.environ,{'RIOT_API_KEY':'PRIVATE_INVALID'},clear=True),redirect_stdout(output),\
                    patch('coach_v1.riot_collector._transport',side_effect=AssertionError('HTTP forbidden')) as http:
                code=cli.main(['--output',str(power),'--movement-output',str(movement),'--outcome-output',str(outcome),
                    '--diagnostics-output',str(diagnostics)])
            self.assertEqual(code,0);http.assert_not_called()
            self.assertTrue(all(not path.exists() for path in (power,movement,outcome)))
            data=json.loads(diagnostics.read_text());self.assertFalse(data['key_shape']['valid_shape'])
            self.assertEqual(data['request_count'],0);self.assertIsNone(data['first_http_status'])
            self.assertEqual(data['http_errors'],[]);self.assertEqual(data['collection_reason'],'INVALID_API_KEY_SHAPE')
            self.assertIn('RIOT_KEY_SHAPE_RECEIPT_JSON=',output.getvalue())
            self.assertNotIn('PRIVATE',output.getvalue()+diagnostics.read_text())

    def test_cli_auth_failure_artifact_contains_only_safe_selected_message(self):
        cli=self.cli();http=Responses([(403,{},dict(status=dict(message='Forbidden '+TEST_KEY),private='PRIVATE_RAW_BODY'))])
        with tempfile.TemporaryDirectory() as td:
            diagnostics=Path(td)/'diagnostics.json';output=StringIO()
            with patch.dict(os.environ,{'RIOT_API_KEY':TEST_KEY},clear=True),redirect_stdout(output),\
                    patch('coach_v1.riot_collector._transport',http):
                code=cli.main(['--output',str(Path(td)/'power.json'),'--diagnostics-output',str(diagnostics)])
            self.assertEqual(code,0)
            data=json.loads(diagnostics.read_text())
            self.assertEqual(data['first_http_status'],403);self.assertEqual(data['http_errors'][0]['error_message'],'Forbidden [REDACTED_KEY]')
            self.assertEqual(data['request_count'],1);self.assertEqual(data['retry_count'],0)
            self.assertIn('RIOT_HTTP_ERROR_RECEIPT_JSON=',output.getvalue())
            for forbidden in (TEST_KEY,'PRIVATE_RAW_BODY'):
                self.assertNotIn(forbidden,output.getvalue()+diagnostics.read_text())


if __name__=='__main__':unittest.main()

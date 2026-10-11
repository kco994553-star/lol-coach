"""Injected paired clients only; no real Riot credentials or provider requests."""
import copy
from contextlib import redirect_stdout
from io import BytesIO,StringIO
import importlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import quote

TEST_KEY='RGAPI-00000000-0000-4000-8000-000000000000'
UA='lol-coach/1.0 (+https://github.com/kco994553-star/lol-coach)'


class RiotFrontTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.riot_front_diagnostics'),'paired module missing')
        self.m=importlib.import_module('coach_v1.riot_front_diagnostics')

    def pair(self,responses,key=TEST_KEY):
        self.calls=[]
        def client(index):
            def request(url,headers,timeout,max_bytes):
                self.calls.append((index,url,copy.deepcopy(headers),timeout,max_bytes))
                value=responses[index]
                if isinstance(value,Exception):raise value
                return value
            return request
        return self.m.diagnose_riot_front(key,curl_transport=client(0),python_transport=client(1))

    def test_same_trimmed_key_ua_exact_two_no_retry_and_ready_only_both_200(self):
        for codes,status in [((200,200),'READY'),((403,200),'BLOCKED_EXTERNAL'),((200,401),'BLOCKED_EXTERNAL'),((503,503),'BLOCKED_EXTERNAL')]:
            result=self.pair([(code,{},b'{"entries":[]}',True) for code in codes],key=' \n'+TEST_KEY+'\r\n')
            self.assertEqual(result['status'],status);self.assertEqual(result['statuses'],dict(zip(('curl','python'),codes)))
            self.assertEqual(result['request_count'],2);self.assertEqual(len(self.calls),2)
            self.assertEqual(self.calls[0][1],self.calls[1][1])
            for call in self.calls:
                self.assertEqual(call[2]['X-Riot-Token'],TEST_KEY);self.assertEqual(call[2]['User-Agent'],UA)
            self.assertNotIn(TEST_KEY,json.dumps(result));self.m.validate_front_receipt(result)

    def test_invalid_shape_zero_clients_and_all_null_unknown(self):
        result=self.pair([],key='INVALID_TEST')
        self.assertEqual(self.calls,[]);self.assertEqual(result['request_count'],0)
        self.assertEqual(result['status'],'BLOCKED_EXTERNAL')
        self.assertEqual(result['statuses'],dict(curl=None,python=None))
        self.assertTrue(all(x['is_json'] is None for x in result['observations'].values()))
        self.assertTrue(all(x['reason'] is None for x in result['observations'].values()))

    def test_200_raw_identifiers_headers_and_body_are_completely_withheld(self):
        result=self.pair([(200,{'Server':'PRIVATE_SERVER','CF-Ray':'PRIVATE_MARKER'},b'{"puuid":"PRIVATE_PLAYER"}',True)]*2)
        self.assertEqual(result['status'],'READY')
        for observation in result['observations'].values():
            self.assertTrue(all(observation[k] is None for k in ('headers_content_type','headers_server','is_json','body_prefix','error_message')))
            self.assertFalse(any(observation['markers'].values()))
        self.assertNotIn('PRIVATE',json.dumps(result))
        bad=copy.deepcopy(result);bad['observations']['curl']['body_prefix']='safe-looking response'
        with self.assertRaises(ValueError):self.m.validate_front_receipt(bad)

    def test_encoded_known_keys_redacted_before_pii_and_prefix_truncation(self):
        raw=' \n'+TEST_KEY+'\r\n';encoded=quote(raw,safe='')
        result=self.pair([(403,{},('Forbidden '+encoded+' '+TEST_KEY+' '+('word '*50)).encode(),True),
                          (200,{},b'{}',True)],key=raw)
        serialized=json.dumps(result)
        for forbidden in (encoded,TEST_KEY,TEST_KEY[:18]):self.assertNotIn(forbidden,serialized)
        self.assertIn('[REDACTED_KEY]',result['observations']['curl']['body_prefix'])

    def test_403_header_markers_and_body_sanitized_before_prefix_bound(self):
        raw=json.dumps({'puuid':'PRIVATE_PLAYER_IDENTIFIER','summonerName':'PLAYER#KR1',
            'status':{'message':'Forbidden '+TEST_KEY+' player puuid=PRIVATE_PLAYER_IDENTIFIER '+'A'*120}}).encode()
        result=self.pair([(403,{'Content-Type':'text/html; key='+TEST_KEY,'Server':'proxy https://private.invalid/'+TEST_KEY,
            'CF-Ray':'PRIVATE_MARKER_VALUE','x-sucuri-id':'PRIVATE_ID'},raw,True),(200,{},b'{}',True)])
        obs=result['observations']['curl']
        self.assertTrue(obs['is_json']);self.assertTrue(obs['markers']['cf-ray']);self.assertTrue(obs['markers']['x-sucuri-id'])
        self.assertFalse(obs['markers']['cf-cache-status']);self.assertLessEqual(len(obs['body_prefix']),100)
        self.assertLessEqual(len(obs['headers_content_type']),128);self.assertLessEqual(len(obs['headers_server']),128)
        for forbidden in (TEST_KEY,'PRIVATE_PLAYER_IDENTIFIER','PLAYER#KR1','PRIVATE_MARKER_VALUE','private.invalid'):
            self.assertNotIn(forbidden,json.dumps(result))
        self.assertIn('Forbidden',obs['error_message'])

    def test_json_unknown_fields_and_values_never_enter_safe_prefix(self):
        body=json.dumps({'status':{'message':'Forbidden '+TEST_KEY},'private':'PRIVATE_RAW_BODY',
            'player':{'unrelated':'PRIVATE_PLAYER_VALUE'},'PRIVATE_FIELD_LABEL':'PRIVATE_DATA'}).encode()
        result=self.pair([(403,{},body,True),(200,{},b'{}',True)])
        observation=result['observations']['curl']
        self.assertTrue(observation['is_json']);self.assertIn('Forbidden',observation['body_prefix'])
        self.assertEqual(observation['error_message'],'Forbidden [REDACTED_KEY]')
        self.assertNotIn('PRIVATE',json.dumps(result))
        bad=copy.deepcopy(result);bad['observations']['curl']['body_prefix']='{"private":"PRIVATE_RAW_BODY"}'
        with self.assertRaises(ValueError):self.m.validate_front_receipt(bad)
        partial=self.pair([(403,{},b'{"private":"PRIVATE_RAW_BODY",',False),(200,{},b'{}',True)])
        self.assertNotIn('PRIVATE',json.dumps(partial));self.assertIsNone(partial['observations']['curl']['is_json'])

    def test_json_numeric_identifiers_and_unrelated_primitives_are_withheld(self):
        body=b'{"puuid":123456789,"status":{"message":"Forbidden","status_code":403},"private":true}'
        result=self.pair([(403,{},body,True),(200,{},b'{}',True)])
        self.assertNotIn('123456789',json.dumps(result))
        self.assertNotIn(':true',result['observations']['curl']['body_prefix'])
        bad=copy.deepcopy(result);bad['observations']['curl']['body_prefix']='{"puuid":123456789}'
        with self.assertRaises(ValueError):self.m.validate_front_receipt(bad)

    def test_unsafe_json_prefix_is_unavailable_not_synthetic_evidence(self):
        for body,complete,classification in (
                (b'{"private":"PRIVATE_RAW_BODY",',False,None),
                (b'{"private":"PRIVATE_RAW_BODY",',True,False),
                (b'{"private":"'+b'x'*65536,True,None)):
            result=self.pair([(403,{},body,complete),(200,{},b'{}',True)])
            observation=result['observations']['curl']
            self.assertEqual(observation['is_json'],classification)
            self.assertIsNone(observation['body_prefix'])
            self.assertNotIn('PRIVATE',json.dumps(result))
        result=self.pair([(403,{},b'<html>Forbidden</html>',True),(200,{},b'{}',True)])
        self.assertEqual(result['observations']['curl']['body_prefix'],'<html>Forbidden</html>')

    def test_json_message_identifier_quotes_do_not_break_safe_prefix_validation(self):
        raw=b'{"status":{"message":"Forbidden id=PRIVATE", "status_code":403}}'
        result=self.pair([(403,{},raw,True),(200,{},b'{}',True)])
        self.assertEqual(result['statuses']['curl'],403)
        self.assertNotIn('PRIVATE',json.dumps(result))
        self.assertTrue(result['observations']['curl']['body_prefix'].startswith('{"status":{"message":'))
        self.assertIn('status_code',result['observations']['curl']['body_prefix'])
        self.m.validate_front_receipt(result)

    def test_non_json_false_incomplete_and_network_unknown_preserve_literal_status(self):
        result=self.pair([(403,{},b'<html>Forbidden</html>',True),OSError('PRIVATE '+TEST_KEY)])
        self.assertFalse(result['observations']['curl']['is_json'])
        self.assertIsNone(result['observations']['python']['is_json']);self.assertIsNone(result['statuses']['python'])
        self.assertEqual(result['observations']['python']['reason'],'NETWORK_FAILURE')
        result=self.pair([(200,{},b'{"unfinished":',False),(200,{},b'x'*65537,True)])
        self.assertEqual(result['status'],'READY');self.assertEqual(result['statuses'],dict(curl=200,python=200))
        self.assertTrue(all(x['is_json'] is None for x in result['observations'].values()))

    def test_strict_receipt_rejects_raw_fields_keys_pii_and_inconsistent_ready(self):
        result=self.pair([(403,{},b'Forbidden',True),(200,{},b'{}',True)])
        for mutate in (lambda x:x.update(raw_body='PRIVATE'),lambda x:x.update(status='READY'),
                lambda x:x['observations']['curl'].update(body_prefix=TEST_KEY),
                lambda x:x['observations']['curl'].update(body_prefix='puuid="PRIVATE_PLAYER_IDENTIFIER"'),
                lambda x:x['observations']['curl'].update(body_prefix='PLAYER#KR1'),
                lambda x:x['observations']['curl']['markers'].update(**{'cf-ray':'PRIVATE'}),
                lambda x:x['observations']['curl'].update(headers_server='x'*129),
                lambda x:x['statuses'].update(curl='403')):
            bad=copy.deepcopy(result);mutate(bad)
            with self.assertRaises(ValueError):self.m.validate_front_receipt(bad)

    def test_python_preserves_status_oversize_and_disables_redirects(self):
        with patch.object(self.m,'build_opener') as opener:
            response=opener.return_value.open.return_value.__enter__.return_value
            response.status=200;response.headers={};response.read.return_value=b'x'*65537
            status,headers,body,complete=self.m._python_transport(self.m.CHALLENGER_URL,
                {'X-Riot-Token':TEST_KEY,'User-Agent':UA},1,65536)
        self.assertEqual(status,200);self.assertFalse(complete);self.assertLessEqual(len(body),65536)
        self.assertIsInstance(opener.call_args.args[0],self.m._RejectRedirect)
        self.assertIsNone(self.m._RejectRedirect().redirect_request(None,None,302,'m',{},'https://other.invalid'))

    def test_curl_header_parser_proxy_block_and_oversize_preserve_final_status(self):
        wire=b'HTTP/1.1 200 Connection established\r\n\r\nHTTP/2 403\r\nContent-Type: text/html\r\nCF-Ray: PRIVATE\r\n\r\n<html>Forbidden</html>'
        status,headers,body,complete=self.m._parse_curl_output(wire,True,65536)
        self.assertEqual(status,403);self.assertEqual(body,b'<html>Forbidden</html>');self.assertTrue(complete)
        self.assertEqual(headers['cf-ray'],'PRIVATE')
        status,headers,body,complete=self.m._parse_curl_output(b'HTTP/2 200\r\n\r\n'+b'x'*70000,False,65536)
        self.assertEqual(status,200);self.assertFalse(complete);self.assertLessEqual(len(body),65536)
        status,headers,body,complete=self.m._parse_curl_output(b'HTTP/2 403\r\n\r\nHTTP/2 200\r\n\r\nBODY',True,65536)
        self.assertEqual(status,403);self.assertEqual(body,b'HTTP/2 200\r\n\r\nBODY')

    def test_curl_configuration_stdin_only_never_redirect_or_retry(self):
        configuration=self.m._curl_config(self.m.CHALLENGER_URL,{'X-Riot-Token':TEST_KEY,'User-Agent':UA},20)
        self.assertIn('X-Riot-Token: '+TEST_KEY,configuration)
        self.assertIn('user-agent = "'+UA+'"',configuration)
        self.assertNotIn('location',configuration);self.assertNotIn('retry',configuration)
        self.assertIn('RIOT_CURL_HTTP_STATUS:%{http_code}',configuration)
        self.assertEqual(self.m.CURL_COMMAND,('curl','--disable','--config','-'))
        self.assertNotIn(TEST_KEY,' '.join(self.m.CURL_COMMAND))

    def test_curl_subprocess_bounds_transient_pipe_and_key_only_stdin(self):
        class Input(BytesIO):
            def close(self):self.captured=self.getvalue();super().close()
        class Process:
            def __init__(self):
                read_fd,write_fd=os.pipe();self.stdout=os.fdopen(read_fd,'rb',buffering=0);self.stdin=Input();self.code=None
                def write():
                    try:
                        os.write(write_fd,b'HTTP/2 200\r\n\r\n')
                        for _ in range(30):os.write(write_fd,b'x'*16384)
                    except BrokenPipeError:pass
                    finally:os.close(write_fd)
                self.thread=threading.Thread(target=write);self.thread.start()
            def kill(self):self.code=-9
            def wait(self,timeout):
                if self.code is None:self.code=0
                return self.code
            def poll(self):return self.code
        process=Process()
        with patch.object(self.m.subprocess,'Popen',return_value=process) as spawn:
            status,headers,body,complete=self.m._curl_transport(self.m.CHALLENGER_URL,
                {'X-Riot-Token':TEST_KEY,'User-Agent':UA},1,65536)
        process.thread.join(timeout=2);self.assertFalse(process.thread.is_alive())
        self.assertEqual(status,200);self.assertFalse(complete);self.assertLessEqual(len(body),65536)
        self.assertEqual(spawn.call_args.args[0],self.m.CURL_COMMAND)
        self.assertEqual(spawn.call_args.kwargs['stderr'],self.m.subprocess.DEVNULL)
        self.assertIn(TEST_KEY.encode(),process.stdin.captured)
        self.assertNotIn(TEST_KEY,str(spawn.call_args))

    def test_curl_writeout_preserves_200_when_filesize_rejected_before_headers(self):
        class Input(BytesIO):
            def close(self):self.captured=self.getvalue();super().close()
        class Process:
            def __init__(self):
                read_fd,write_fd=os.pipe();os.write(write_fd,b'\nRIOT_CURL_HTTP_STATUS:200\n');os.close(write_fd)
                self.stdout=os.fdopen(read_fd,'rb',buffering=0);self.stdin=Input()
            def wait(self,timeout):return 63
            def poll(self):return 63
            def kill(self):raise AssertionError('already completed')
        process=Process()
        with patch.object(self.m.subprocess,'Popen',return_value=process):
            status,headers,body,complete=self.m._curl_transport(self.m.CHALLENGER_URL,
                {'X-Riot-Token':TEST_KEY,'User-Agent':UA},1,65536)
        self.assertEqual(status,200);self.assertEqual(headers,{})
        self.assertIsNone(body);self.assertFalse(complete)

    def test_cli_invalid_key_safe_artifact_and_zero_provider_calls(self):
        spec=importlib.util.spec_from_file_location('riot_front_cli','scripts/diagnose_riot_front.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'safe.json';output=StringIO()
            with patch.dict(os.environ,{'RIOT_API_KEY':'PRIVATE_INVALID'},clear=True),redirect_stdout(output),\
                    patch.object(self.m,'_curl_transport',side_effect=AssertionError('curl forbidden')) as curl,\
                    patch.object(self.m,'_python_transport',side_effect=AssertionError('Python forbidden')) as python:
                self.assertEqual(cli.main(['--output',str(path)]),0)
            curl.assert_not_called();python.assert_not_called()
            receipt=self.m.validate_front_receipt(json.loads(path.read_text()))
            self.assertEqual(receipt['status'],'BLOCKED_EXTERNAL');self.assertEqual(receipt['request_count'],0)
            self.assertIn('RIOT_FRONT_RECEIPT_JSON=',output.getvalue())
            self.assertNotIn('PRIVATE',output.getvalue()+path.read_text())


if __name__=='__main__':unittest.main()

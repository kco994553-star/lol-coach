"""Authored fake credentials/errors only; diagnostics cannot retain provider bodies."""
import json
import unittest
from coach_v1.api_diagnostics import inspect_riot_key, safe_http_error

TEST_KEY='RGAPI-00000000-0000-0000-0000-000000000001'

class ApiDiagnosticTests(unittest.TestCase):
    def test_shape_strips_only_outer_whitespace_and_reports_no_value(self):
        normalized,shape=inspect_riot_key(' \n'+TEST_KEY+'\r\n')
        self.assertEqual(normalized,TEST_KEY)
        self.assertEqual(shape['normalized_length'],42)
        self.assertTrue(shape['has_outer_whitespace'] and shape['contains_line_break'] and shape['valid_shape'])
        self.assertFalse(shape['raw_has_prefix']);self.assertTrue(shape['normalized_has_prefix'])
        self.assertNotIn(TEST_KEY,json.dumps(shape))

    def test_bad_shape_or_missing_key_rejected(self):
        for value in [None,'','RGAPI-x','x'+TEST_KEY,TEST_KEY[:15]+' '+TEST_KEY[15:],True]:
            with self.subTest(value_type=type(value).__name__):
                normalized,shape=inspect_riot_key(value);self.assertIsNone(normalized);self.assertFalse(shape['valid_shape'])

    def test_riot_only_extracts_status_message(self):
        result=safe_http_error('RIOT',403,json.dumps({'status':{'message':'Unknown apikey','status_code':403},'private':'DO_NOT_RETAIN'}).encode(),secrets=[TEST_KEY])
        self.assertEqual(result,dict(http_status=403,error_status=None,error_code=None,error_message='Unknown apikey'))
        self.assertNotIn('DO_NOT_RETAIN',json.dumps(result))

    def test_google_preserves_literal_status_message_and_code(self):
        result=safe_http_error('GEMINI',400,{'error':{'status':'INVALID_ARGUMENT','code':400,'message':'Unsupported field'}},secrets=[])
        self.assertEqual(result,dict(http_status=400,error_status='INVALID_ARGUMENT',error_code=400,error_message='Unsupported field'))
        self.assertEqual(safe_http_error('GEMINI',403,{'error':{'code':'permission_denied','message':'Forbidden'}})['error_code'],'permission_denied')

    def test_redacts_known_keys_encoded_keys_patterns_and_urls_before_bounding(self):
        from urllib.parse import quote
        key='AIza'+'Z'*35
        message='key='+key+' '+TEST_KEY+' '+quote('\n'+TEST_KEY+'\n',safe='')+' https://example.test/?key='+key+' PRIVATE_LAST'
        result=safe_http_error('GEMINI',403,{'error':{'status':'PERMISSION_DENIED','message':message}},secrets=[key,TEST_KEY,'\n'+TEST_KEY+'\n'])
        raw=json.dumps(result)
        for value in [key,TEST_KEY,quote(TEST_KEY,safe=''),'https://example.test']:self.assertNotIn(value,raw)
        self.assertIn('REDACTED',raw);self.assertIn('PRIVATE_LAST',raw)
        result=safe_http_error('RIOT',403,{'status':{'message':'x'*600+TEST_KEY}},secrets=[TEST_KEY]);self.assertLessEqual(len(result['error_message']),512);self.assertNotIn(TEST_KEY,json.dumps(result))

    def test_error_symbols_cannot_echo_credentials(self):
        key='AIza'+'Z'*35
        for field in ['status','code']:
            r=safe_http_error('GEMINI',403,{'error':{field:key,'message':'Forbidden'}},secrets=[key])
            self.assertNotIn(key,json.dumps(r));self.assertIsNone(r['error_'+field])
        r=safe_http_error('GEMINI',403,{'error':{'status':TEST_KEY,'code':TEST_KEY}})
        self.assertNotIn(TEST_KEY,json.dumps(r))

    def test_malformed_oversized_deep_or_nonresponse_fields_stay_unknown(self):
        for body in [b'<html>SECRET_BODY</html>',b'{',b'x'*65537,b'{"error":'+b'['*20000+b'0'+b']'*20000+b'}',{'error':{'status':{},'message':['SECRET_BODY'],'code':True}}]:
            result=safe_http_error('GEMINI',None,body)
            self.assertEqual(result,dict(http_status=None,error_status=None,error_code=None,error_message=None))
            self.assertNotIn('SECRET_BODY',json.dumps(result))

if __name__=='__main__':unittest.main()

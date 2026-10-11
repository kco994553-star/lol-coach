"""Auxiliary outcome HTTP checks; synthetic fixtures are not gameplay evidence."""
import copy
import http.client
import json
from pathlib import Path
from unittest.mock import Mock,patch
import unittest
from tests_pregame import test_http


def request(**changes):
    return dict(dict(champion='Champion',position='TOP',patch='16.19',tier=None,opponent_champion='Opponent'),**changes)


class OutcomeHTTPTests(unittest.TestCase):
    setUp=test_http.HTTPTests.setUp
    cleanup=test_http.HTTPTests.cleanup
    call=test_http.HTTPTests.call
    route='/dev/v1/pregame/outcome-view'

    def test_no_source_unknown_without_zero_or_existing_api_changes(self):
        self.assertIsNone(self.server.outcome_data)
        status_before=self.call('/dev/v1/pregame/status')[1]
        power_before=self.call('/dev/v1/pregame/power-view','POST',request())[1]
        status,result=self.call(self.route,'POST',request())
        self.assertEqual(status,200);self.assertEqual(set(result),{'view','test_mode'})
        self.assertFalse(result['test_mode']);self.assertEqual(result['view']['status'],'UNKNOWN')
        self.assertEqual(result['view']['points'],[]);self.assertIsNone(result['view']['dataset_digest'])
        self.assertEqual(result['view']['schema_version'],'pregame.outcome-data.v1')
        self.assertEqual(status_before,self.call('/dev/v1/pregame/status')[1])
        self.assertEqual(power_before,self.call('/dev/v1/pregame/power-view','POST',request())[1])

    def test_auth_methods_strict_fields_and_origin(self):
        self.assertEqual(self.call(self.route,'POST',request(),auth=False)[0],401)
        self.assertEqual(self.call(self.route)[0],404)
        for body in [dict(request(),test_mode=True),dict(request(),opponent_champion=['Opponent']),
                     request(champion='x'*101),request(position='ADC'),request(patch=True),request(tier='ALL'),
                     {k:v for k,v in request().items() if k!='opponent_champion'}]:
            self.assertEqual(self.call(self.route,'POST',body)[0],422)
        con=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        con.request('POST',self.route,json.dumps(request()),{'Authorization':'Bearer '+self.token,
            'Content-Type':'application/json','Origin':'https://foreign.example'})
        result=con.getresponse();result.read();con.close();self.assertEqual(result.status,403)


if __name__=='__main__':unittest.main()

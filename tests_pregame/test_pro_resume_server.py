import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from coach_v1.pregame_server import PregameWorkbench
from coach_v1.server import Limits


class ProResumeServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.server=PregameWorkbench(Path(self.tmp.name)/'work.sqlite','fixture-token-'+'x'*32,Limits(12000000,1000,100,100,100,10))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()

    def request(self,path,body=None,auth=True):
        headers={'Content-Type':'application/json'}
        if auth:headers['Authorization']='Bearer fixture-token-'+'x'*32
        r=Request('http://127.0.0.1:'+str(self.server.server_port)+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        try:
            with urlopen(r) as response:return response.status,json.load(response)
        except HTTPError as error:return error.code,json.load(error)

    def test_cases_read_requires_auth_and_has_no_own_identity_dependency(self):
        route='/dev/v1/postgame/reference-cases'
        self.assertEqual(self.request(route,auth=False)[0],401)
        status,data=self.request(route)
        self.assertEqual(status,200)
        self.assertEqual(data['schema_version'],'postgame.pro-reference-cases.v1')
        self.assertEqual(data['sample_counts']['unique_matches'],0)
        self.assertNotIn('own_riot_id',data)

    def test_challenger_reference_has_no_tier_selector(self):
        status,data=self.request('/dev/v1/pregame/challenger-reference',dict(champion='Caitlyn',position='BOTTOM',patch='16.20'))
        self.assertEqual(status,200)
        self.assertEqual(data['schema_version'],'pregame.challenger-reference.v1')
        self.assertEqual(self.request('/dev/v1/pregame/challenger-reference',dict(champion='Caitlyn',position='BOTTOM',patch='16.20',tier='MASTER'))[0],422)

    def test_pc_statistics_stylesheet_is_served(self):
        with urlopen('http://127.0.0.1:'+str(self.server.server_port)+'/statistics.css') as response:
            self.assertEqual(response.status,200)

    def test_public_aggregate_gzip_is_bounded_and_never_reads_symlinks(self):
        import gzip
        from coach_v1.pregame_server import read_aggregate_file
        path=Path(self.tmp.name)/'aggregate.json.gz';path.write_bytes(gzip.compress(b'{"public":true}'))
        self.assertEqual(read_aggregate_file(path),{'public':True})
        path.write_bytes(gzip.compress(json.dumps({'large':'x'*4096}).encode()))
        with self.assertRaises(ValueError):read_aggregate_file(path,max_bytes=200)
        link=Path(self.tmp.name)/'link.json.gz';link.symlink_to(path)
        with self.assertRaises(ValueError):read_aggregate_file(link)

    def test_cli_default_real_cases_remain_roster_bound(self):
        from unittest.mock import Mock,patch
        from coach_v1.pregame_server import main,ROOT
        path=ROOT/'data/pro_reference/2026-10-13/reference-cases.json'
        expected=json.loads(path.read_text())
        token=Path(self.tmp.name)/'cli-token';token.write_text('fixture-cli-token')
        argv=['pregame','--db',self.tmp.name+'/cli.sqlite','--token-file',str(token)]
        for flag in ('body-bytes','observations','actions','scenarios','comparisons','pending-jobs'):
            argv.extend(['--max-'+flag,'12000000'])
        for roster_digest,success in ((self.server.current_pro_roster_digest(),True),('f'*64,False)):
            fake=Mock();fake.server_port=8765;fake.test_mode=True
            fake.current_pro_roster_digest.return_value=roster_digest
            with patch('sys.argv',argv),patch('coach_v1.pregame_server.PregameWorkbench',return_value=fake),patch('builtins.print'):
                if success:
                    main();self.assertEqual(fake.pro_cases_data,expected);fake.serve_forever.assert_called_once()
                else:
                    with self.assertRaises(ValueError):main()
                    fake.serve_forever.assert_not_called()
            fake.server_close.assert_called_once()

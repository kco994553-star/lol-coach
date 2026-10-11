import copy
import json
import http.client
import os
from pathlib import Path
import threading
import unittest
from tests_pregame import test_http
from tests_expert.test_contract import artifact


class ExpertHTTPTests(unittest.TestCase):
    setUp=test_http.HTTPTests.setUp
    cleanup=test_http.HTTPTests.cleanup
    call=test_http.HTTPTests.call

    def test_auth_exact_shape_and_no_write_on_invalid_artifact(self):
        self.assertEqual(self.call('/dev/v1/experts/claims',auth=False)[0],401)
        self.assertEqual(self.call('/dev/v1/experts/import','POST',dict(artifact=artifact()),auth=False)[0],401)
        for body in [dict(artifact=artifact(),approve=True),dict(artifact=dict(artifact(),visual_verified=True)),dict(artifact=None)]:
            self.assertEqual(self.call('/dev/v1/experts/import','POST',body)[0],422)
        self.assertEqual(self.server.research.list(),[])
        self.assertEqual(self.call('/dev/v1/experts/claims')[1],dict(claims=[],new_candidates=0,coaching_accuracy=None))

    def test_import_restart_idempotency_and_latest_proposal_without_user_approval(self):
        status,result=self.call('/dev/v1/experts/import','POST',dict(artifact=artifact()))
        self.assertEqual(status,201);self.assertEqual(result['new_candidates'],1)
        rows=self.call('/dev/v1/experts/claims')[1]['claims'];self.assertEqual(len(rows),1)
        row=rows[0];self.assertEqual(row['artifact'],{k:v for k,v in artifact().items() if k not in ('claims','rejections')})
        self.assertEqual(self.server.research.get(row['resource_id'])['report']['artifact'],artifact())
        self.assertEqual(row['claim'],artifact()['claims'][0]);self.assertEqual(row['proposal']['review_state'],'EXPLORATORY')
        self.assertEqual(row['comparison']['status'],'UNMEASURABLE')
        proposal=row['proposal'];path='/dev/v1/knowledge/proposals/'+proposal['rule_id']
        self.assertEqual(self.call(path)[1],proposal)
        self.server.shutdown();self.thread.join();self.server.server_close()
        from coach_v1.pregame_server import PregameWorkbench
        from coach_v1.server import Limits
        self.server=PregameWorkbench(Path(self.tmp.name)/'work.sqlite',self.token,Limits(1000000,100,100,100,100,10))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        retry=self.call('/dev/v1/experts/import','POST',dict(artifact=artifact()))[1]
        self.assertEqual(retry['new_candidates'],0)
        self.assertEqual(self.call('/dev/v1/experts/claims')[1]['claims'],rows)
        with self.server.research._db() as db:
            payloads=[json.loads(r[0]) for r in db.execute('SELECT payload FROM knowledge_rules')]
        self.assertTrue(payloads);self.assertTrue(all(p['review_state']=='EXPLORATORY' and p.get('review_decision') is None for p in payloads))

    def test_size_guards_preserve_no_writes(self):
        malformed=dict(artifact(),claims=[])
        for i in range(60):
            c=copy.deepcopy(artifact()['claims'][0]);c.update(timestamp=f'00:{i:02d}',timestamp_seconds=i,
                paraphrase='가'*500,conditions=['가'*200]*10)
            malformed['claims'].append(c)
        self.assertEqual(self.call('/dev/v1/experts/import','POST',dict(artifact=malformed))[0],422)
        self.assertEqual(self.server.research.list(),[])
        # The server rejects advertised oversized bodies before consuming them.
        # Send only headers to avoid a client-side broken-pipe race.
        con=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        try:
            con.putrequest('POST','/dev/v1/experts/import')
            con.putheader('Authorization','Bearer '+self.token);con.putheader('Content-Type','application/json')
            con.putheader('Content-Length','1000001');con.endheaders()
            response=con.getresponse();response.read();self.assertEqual(response.status,413)
        finally:con.close()
        self.assertEqual(self.server.research.list(),[])

    def test_startup_file_count_bytes_and_nonregular_files_rejected(self):
        from coach_v1.pregame_server import load_expert_directory
        directory=Path(self.tmp.name)/'limited-files';directory.mkdir()
        large=directory/'large.json';large.write_bytes(b' '*200001)
        with self.assertRaises(ValueError):load_expert_directory(self.server,directory,explicit=True)
        large.unlink()
        if hasattr(os,'mkfifo'):
            fifo=directory/'fifo.json';os.mkfifo(fifo)
            with self.assertRaises(ValueError):load_expert_directory(self.server,directory,explicit=True)
            fifo.unlink()
        for i in range(101):(directory/f'file-{i}.json').write_text(json.dumps(artifact()))
        with self.assertRaises(ValueError):load_expert_directory(self.server,directory,explicit=True)
        self.assertEqual(self.server.research.list(),[])

    def test_startup_batch_rejects_malformed_before_any_import(self):
        from coach_v1.pregame_server import load_expert_directory
        directory=Path(self.tmp.name)/'expert-files';directory.mkdir()
        (directory/'a.json').write_text(json.dumps(artifact()))
        (directory/'b.json').write_text('{invalid')
        with self.assertRaises(ValueError):load_expert_directory(self.server,directory,explicit=True)
        self.assertEqual(self.server.research.list(),[])
        (directory/'b.json').unlink()
        imported=load_expert_directory(self.server,directory,explicit=True)
        self.assertEqual(imported['new_candidates'],1)
        self.assertEqual(load_expert_directory(self.server,directory,explicit=True)['new_candidates'],0)

    def test_startup_directory_paths_symlinks_duplicate_json_keys_and_absence(self):
        from coach_v1.pregame_server import load_expert_directory
        missing=Path(self.tmp.name)/'missing'
        self.assertEqual(load_expert_directory(self.server,missing)['new_candidates'],0)
        with self.assertRaises(ValueError):load_expert_directory(self.server,missing,explicit=True)
        directory=Path(self.tmp.name)/'unsafe-files';directory.mkdir()
        other=Path(self.tmp.name)/'other.json';other.write_text(json.dumps(artifact()))
        (directory/'linked.json').symlink_to(other)
        with self.assertRaises(ValueError):load_expert_directory(self.server,directory,explicit=True)
        (directory/'linked.json').unlink();(directory/'duplicate.json').write_text('{"schema_version":"x","schema_version":"y"}')
        with self.assertRaises(ValueError):load_expert_directory(self.server,directory,explicit=True)
        self.assertEqual(self.server.research.list(),[])


if __name__=='__main__':unittest.main()

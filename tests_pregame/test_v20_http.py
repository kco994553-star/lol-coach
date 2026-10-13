import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from coach_v1.server import Limits
from coach_v1.pregame_server import PregameWorkbench

class QueueV20HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.token='isolated-v20-token-not-real-'*2
        self.server=PregameWorkbench(Path(self.tmp.name)/'work.sqlite',self.token,Limits(1_000_000,100,100,100,100,10))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.cleanup)
    def cleanup(self):
        self.server.shutdown();self.thread.join();self.server.server_close();self.tmp.cleanup()
    def call(self,path,method='GET',body=None,auth=True):
        con=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=15)
        headers={'Authorization':'Bearer '+self.token} if auth else {}
        if body is not None:headers['Content-Type']='application/json'
        con.request(method,path,json.dumps(body) if body is not None else None,headers)
        r=con.getresponse();raw=r.read();status=r.status;typ=r.getheader('Content-Type','');con.close()
        return status,json.loads(raw) if 'application/json' in typ else raw.decode()
    def test_review_queue_authenticated_and_never_reviews_by_loading(self):
        path='/dev/v1/pregame/review-queue'
        self.assertEqual(self.call(path,auth=False)[0],401)
        status,result=self.call(path);self.assertEqual(status,200)
        self.assertEqual(result['progress']['reviewed'],0)
        self.assertGreater(result['progress']['pending'],0)
        self.assertEqual(self.call('/dev/v1/pregame/knowledge')[1],[])
    def test_defer_reloads_without_approval(self):
        path='/dev/v1/pregame/review-queue'
        status,result=self.call(path);self.assertEqual(status,200)
        first=result['candidates'][0]
        body={k:first[k] for k in ('candidate_id','selected_version')}
        self.assertEqual(self.call(path+'/later','POST',body)[0],200)
        updated=self.call(path)[1]
        self.assertEqual(updated['progress']['deferred'],1)
        self.assertEqual(updated['progress']['reviewed'],0)
        self.assertEqual(self.call('/dev/v1/pregame/knowledge')[1],[])
    def test_personal_routes_are_authenticated_private_and_reject_malformed(self):
        path='/dev/v1/postgame/matches'
        self.assertEqual(self.call(path,auth=False)[0],401)
        status,result=self.call(path);self.assertEqual(status,200)
        self.assertEqual(result['matches'],[])
        self.assertEqual(self.call('/dev/v1/postgame/import','POST',{})[0],422)
        self.assertEqual(self.call(path+'/not-a-hash')[0],404)
    def test_missing_statistics_progress_is_unknown(self):
        status,result=self.call('/dev/v1/pregame/collection-progress')
        self.assertEqual(status,200)
        self.assertEqual(result['status'],'UNKNOWN')
    def test_edited_candidate_keeps_revision_lineage(self):
        from tests_pregame.test_contract import rule
        self.server.test_mode=True
        spec=rule();status,first=self.call('/dev/v1/pregame/candidates','POST',dict(spec=spec))
        self.assertEqual(status,201)
        proposal=first['proposal'];spec['output']['text']='SYNTHETIC revised wording'
        status,second=self.call('/dev/v1/pregame/candidates','POST',dict(spec=spec,rule_id=proposal['rule_id'],expected_version=proposal['version']))
        self.assertEqual(status,201)
        self.assertEqual(second['proposal']['rule_id'],proposal['rule_id'])
        self.assertEqual(second['proposal']['supersedes'],proposal['version'])
        self.assertEqual(second['proposal']['review_state'],'EXPLORATORY')
        status,_=self.call('/dev/v1/pregame/candidates','POST',dict(spec=spec,rule_id=proposal['rule_id'],expected_version=proposal['version']))
        self.assertEqual(status,409)

    def test_personal_synthetic_import_get_and_plan_analysis(self):
        from tests_pregame.test_v20_postgame import body
        self.server.test_mode=True
        status,row=self.call('/dev/v1/postgame/import','POST',body());self.assertEqual(status,201)
        status,detail=self.call('/dev/v1/postgame/matches/'+row['id']);self.assertEqual(status,200)
        self.assertNotIn('PRIVATE_PUUID',json.dumps(detail))
        status,analysis=self.call('/dev/v1/postgame/analyze','POST',dict(match_id=row['id'],plan_id=None))
        self.assertEqual(status,200);self.assertEqual(analysis['resources'],detail['resources'])
        self.assertEqual(self.call('/dev/v1/postgame/matches/'+'f'*64)[0],404)
        self.assertEqual(self.call('/dev/v1/postgame/analyze','POST',dict(match_id=row['id'],plan_id='not-a-plan'))[0],422)

    def test_directory_statistics_are_used_for_personal_reference(self):
        from tests_pregame.test_v20_postgame import body
        from tests_pregame.test_power_stats import pair,source
        from coach_v1.power_stats import build_power_dataset
        self.server.test_mode=True;src=source();src['tier']='CHALLENGER'
        pairs=[pair(i,i*2) for i in range(24)]
        for p in pairs:p['match']['info']['participants'][3]['championName']='Caitlyn'
        data=build_power_dataset(pairs,source=src)
        self.server.power_datasets={('16.19','CHALLENGER'):data}
        row=self.call('/dev/v1/postgame/import','POST',body())[1]
        status,d=self.call('/dev/v1/postgame/matches/'+row['id']);self.assertEqual(status,200)
        self.assertEqual(d['reference']['status'],'KNOWN')
        self.assertEqual(d['reference']['source']['tier'],'CHALLENGER')

    def test_multi_tier_catalog_and_exact_selection(self):
        from tests_pregame.test_power_stats import pair,source
        from coach_v1.power_stats import build_power_dataset
        self.server.test_mode=True
        gold=build_power_dataset([pair(0),pair(1)],source=source())
        src=source();src['tier']='CHALLENGER'
        high=build_power_dataset([pair(2),pair(3)],source=src)
        self.server.power_datasets={('16.19','GOLD'):gold,('16.19','CHALLENGER'):high}
        status,catalog=self.call('/dev/v1/pregame/power-catalog')
        self.assertEqual(status,200)
        self.assertEqual({d['tier'] for d in catalog['datasets']},{'GOLD','CHALLENGER'})
        req=dict(champion='Champion',position='TOP',patch='16.19',tier='GOLD',opponent_champion=None)
        status,result=self.call('/dev/v1/pregame/power-view','POST',req)
        self.assertEqual(status,200);self.assertEqual(result['view']['source']['tier'],'GOLD')
        req['tier']='CHALLENGER'
        result=self.call('/dev/v1/pregame/power-view','POST',req)[1]
        self.assertEqual(result['view']['source']['tier'],'CHALLENGER')
        req['patch']='UNKNOWN-PATCH'
        result=self.call('/dev/v1/pregame/power-view','POST',req)[1]
        self.assertEqual(result['view']['status'],'UNKNOWN')

    def test_pro_reference_is_bound_to_current_user_roster(self):
        from tests_pregame.test_v20_postgame import body
        from coach_v1.pro_reference import build_pro_reference
        from coach_v1.state import digest
        self.server.test_mode=True
        observed=dict(match_sha256='a'*64,role='BOTTOM',champion='Caitlyn',patch='16.19',resources=[dict(minute=1,gold=1000,xp=200,cs=10)])
        other=dict(observed,match_sha256='b'*64)
        self.server.pro_reference_data=build_pro_reference([observed,other],roster_sha256='c'*64,retrieved_at='2026-10-13T00:00:00Z',sample_kind='SYNTHETIC')
        row=self.call('/dev/v1/postgame/import','POST',body())[1]
        d=self.call('/dev/v1/postgame/matches/'+row['id'])[1]
        self.assertEqual(d['pro_reference']['status'],'UNKNOWN')
        self.assertEqual(d['pro_reference']['reason'],'PRO_ROSTER_VERSION_MISMATCH')
        self.server.pro_reference_data['roster_sha256']=digest(json.loads((Path(__file__).resolve().parents[1]/'config/pro_reference_players.json').read_text()))
        d=self.call('/dev/v1/postgame/matches/'+row['id'])[1]
        self.assertEqual(d['pro_reference']['status'],'KNOWN')

    def test_user_supplied_pro_roster_is_authenticated_and_unverified(self):
        path='/dev/v1/postgame/reference-roster'
        self.assertEqual(self.call(path,auth=False)[0],401)
        status,roster=self.call(path);self.assertEqual(status,200)
        self.assertEqual(roster['verification'],'USER_REPORT_NOT_NETWORK_VERIFIED')
        self.assertEqual(len(roster['roles']),5)
        self.assertEqual(sum(len(r['players']) for r in roster['roles']),25)
        self.assertEqual(roster['backup_count'],9)

    def test_app_db_inside_private_uses_same_personal_cli_directory(self):
        path=Path(self.tmp.name)/'private'/'second.sqlite'
        other=PregameWorkbench(path,self.token,Limits(1000000,100,100,100,100,10))
        try:self.assertEqual(other.personal_directory,path.parent/'postgame')
        finally:other.server_close()

    def test_new_pages_and_assets_available(self):
        for path in ('/review-queue','/review_queue.js','/review_queue.css','/postgame','/postgame.js','/postgame.css','/setup','/statistics','/statistics.js'):
            with self.subTest(path=path):self.assertEqual(self.call(path)[0],200)

if __name__=='__main__':unittest.main()

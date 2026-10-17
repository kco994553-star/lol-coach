"""Private account projection and confirmed LCK-only reference; fixtures aren't real players."""
import importlib.util,json,unittest
from pathlib import Path

class AccountDashboardTests(unittest.TestCase):
    def module(self):
        self.assertTrue(Path('coach_v1/account_dashboard.py').exists(),'safe account service missing')
        from coach_v1 import account_dashboard
        return account_dashboard
    def test_missing_key_and_invalid_input_never_call_riot(self):
        m=self.module();calls=[]
        s=m.AccountDashboardService(api_key='',transport=lambda *args:calls.append(args))
        self.assertEqual(s.lookup({'riot_id':'fixture#KR1','region':'KR'})['status'],'API_UNAVAILABLE');self.assertEqual(calls,[])
        self.assertEqual(s.lookup({'riot_id':'bad','region':'KR'})['status'],'INPUT_ERROR')
        self.assertEqual(s.lookup({'riot_id':'fixture#KR1','region':'NA'})['status'],'REGION_UNSUPPORTED')
    def test_solo_projection_has_real_denominator_window_and_no_identifiers(self):
        m=self.module();people=[dict(puuid='private-own-fixture',championName='Caitlyn',win=True,kills=4,deaths=0,assists=3)]
        good=dict(info=dict(queueId=420,gameStartTimestamp=1000,gameDuration=1800,participants=people))
        wrong=dict(info=dict(queueId=430,gameStartTimestamp=2000,gameDuration=1600,participants=people))
        x=m.project_profile('fixture#KR1','KR',{'queueType':'RANKED_SOLO_5x5','tier':'GOLD','rank':'II','leaguePoints':30},[good,wrong],'private-own-fixture',retrieved_at='2026-10-17T00:00:00Z')
        self.assertEqual(x['statistics']['sample_n'],1);self.assertEqual(x['statistics']['wins'],1);self.assertEqual(x['statistics']['win_rate'],100);self.assertIsNone(x['statistics']['kda']);self.assertEqual(x['omitted_matches'],1)
        self.assertEqual(x['statistics']['window_start'],1000);self.assertEqual(x['rank']['lp'],30);self.assertNotIn('private-own-fixture',json.dumps(x));self.assertIsNone(x['coaching_score']);self.assertEqual(x['notes'],[])
        people[0].pop('deaths');x=m.project_profile('fixture#KR1','KR',None,[good],'private-own-fixture',retrieved_at='2026-10-17T00:00:00Z');self.assertEqual(x['statistics']['sample_n'],0);self.assertIsNone(x['statistics']['win_rate']);self.assertIsNone(x['rank'])
    def test_invalid_champion_field_is_omitted_instead_of_publicly_echoed(self):
        m=self.module();match={'info':{'queueId':420,'gameStartTimestamp':1000,'participants':[{'puuid':'private','championName':'private@example.test','win':True,'kills':1,'deaths':1,'assists':1}]}}
        x=m.project_profile('fixture#KR1','KR',None,[match],'private',retrieved_at='2026-10-17T00:00:00Z');self.assertEqual(x['statistics']['sample_n'],0);self.assertNotIn('private@example.test',json.dumps(x))

    def test_authentication_failure_stops_subsequent_external_requests(self):
        m=self.module();calls=[]
        def transport(*args):calls.append(1);return 403,{},b'{}'
        s=m.AccountDashboardService(api_key='RGAPI-'+'00000000-0000-0000-0000-000000000000',transport=transport)
        for _ in range(2):self.assertEqual(s.lookup({'riot_id':'fixture#KR1','region':'KR'})['status'],'API_UNAVAILABLE')
        self.assertEqual(len(calls),1)
    def test_not_found_is_distinct_from_no_matches_and_no_fake_zero_metrics(self):
        m=self.module()
        s=m.AccountDashboardService(api_key='RGAPI-'+'00000000-0000-0000-0000-000000000000',transport=lambda *args:(404,{},b'{}'))
        self.assertEqual(s.lookup({'riot_id':'fixture#KR1','region':'KR'})['status'],'ACCOUNT_NOT_FOUND')
        x=m.project_profile('fixture#KR1','KR',None,[],'private',retrieved_at='2026-10-17T00:00:00Z');self.assertEqual(x['statistics']['sample_n'],0);self.assertIsNone(x['statistics']['win_rate']);self.assertIsNone(x['statistics']['kda'])
    def test_current_lck_and_account_source_verification_both_required(self):
        m=self.module();c={'format':'lol-coach-verified-lck-v1','accounts':[]};self.assertEqual(m.verified_accounts(c),[])
        bad=dict(player='Synthetic player',team='Synthetic team',position='BOTTOM',riot_id='fixture#KR1',region='KR',roster_status='USER_PROVIDED',account_status='VERIFIED',roster_source='https://lolesports.com/',account_source='https://example.test/',checked_at='2026-10-17')
        c['accounts']=[bad]
        with self.assertRaises(ValueError):m.verified_accounts(c)
        bad['roster_status']='CURRENT_LCK_FIRST_TEAM_VERIFIED';self.assertEqual(len(m.verified_accounts(c)),1)
        bad['account_source']=None
        with self.assertRaises(ValueError):m.verified_accounts(c)
    def test_periodic_publication_updates_manifest_but_rejects_unverified_data(self):
        from scripts.publish_verified_pro_dashboard import publication_data
        manifest={'format':'lol-coach-loading-public-export-v1','sha256':{'dashboard.js':'fixture-hash'}}
        empty={'format':'lol-coach-pro-dashboard-v1','queue_id':420,'profiles':[],'updated_at':None}
        files=publication_data(empty,{'format':'lol-coach-verified-lck-v1','accounts':[]},manifest)
        import hashlib
        self.assertEqual(json.loads(files['build-info.json'])['sha256']['pro-dashboard.json'],hashlib.sha256(files['pro-dashboard.json'].encode()).hexdigest())
        self.assertEqual(set(files),{'pro-dashboard.json','build-info.json'})
        empty['profiles']=[{'profile':{'riot_id':'unconfirmed#KR1'}}]
        with self.assertRaises(ValueError):publication_data(empty,{'format':'lol-coach-verified-lck-v1','accounts':[]},manifest)

    def test_publisher_rejects_private_fields_outside_profile(self):
        from scripts.publish_verified_pro_dashboard import publication_data
        m=self.module();row=dict(player='Synthetic',team='Synthetic',position='MID',riot_id='fixture#KR1',region='KR',roster_status='CURRENT_LCK_FIRST_TEAM_VERIFIED',account_status='VERIFIED',roster_source='https://example.test/roster',account_source='https://example.test/account',checked_at='2026-10-17')
        profile=m.project_profile('fixture#KR1','KR',None,[],'private',retrieved_at='2026-10-17T00:00:00Z')
        pro={k:row[k] for k in ('player','team','position','roster_status','account_status','roster_source','account_source')};pro.update(account_checked_at=row['checked_at'],profile=profile,raw_account={'puuid':'must-not-leak'})
        data={'format':'lol-coach-pro-dashboard-v1','queue_id':420,'profiles':[pro],'updated_at':None}
        with self.assertRaises(ValueError):publication_data(data,{'format':'lol-coach-verified-lck-v1','accounts':[row]},{'format':'lol-coach-loading-public-export-v1','sha256':{'dashboard.js':'fixture'}})

    def test_nested_private_fields_are_rejected_and_failed_refresh_keeps_previous(self):
        from scripts.publish_verified_pro_dashboard import publication_data
        m=self.module();row=dict(player='Synthetic',team='Synthetic',position='MID',riot_id='fixture#KR1',region='KR',roster_status='CURRENT_LCK_FIRST_TEAM_VERIFIED',account_status='VERIFIED',roster_source='https://example.test/roster',account_source='https://example.test/account',checked_at='2026-10-17')
        profile=m.project_profile('fixture#KR1','KR',None,[],'private',retrieved_at='2026-10-17T00:00:00Z')
        pro={k:row[k] for k in ('player','team','position','roster_status','account_status','roster_source','account_source')};pro.update(account_checked_at=row['checked_at'],profile=profile)
        previous={'format':'lol-coach-pro-dashboard-v1','queue_id':420,'profiles':[pro],'status':'READY','updated_at':'2026-10-17T00:00:00Z'}
        config={'format':'lol-coach-verified-lck-v1','accounts':[row]};manifest={'format':'lol-coach-loading-public-export-v1','sha256':{'dashboard.js':'fixture'}}
        for field in ['rank','statistics','champions']:
            import copy
            unsafe=copy.deepcopy(previous);unsafe['profiles'][0]['profile'][field]={'email':'private-fixture@example.test'}
            with self.assertRaises(ValueError):publication_data(unsafe,config,manifest)
        failure={'format':'lol-coach-pro-dashboard-v1','queue_id':420,'profiles':[],'status':'BLOCKED_EXTERNAL','eligible_accounts':1,'failures':[{'status':'API_UNAVAILABLE','reason':'KEY_NOT_CONFIGURED'}],'updated_at':None,'attempted_at':'2026-10-17T01:00:00Z'}
        files=publication_data(failure,config,manifest,previous=previous);out=json.loads(files['pro-dashboard.json']);self.assertEqual(out['profiles'],previous['profiles']);self.assertEqual(out['updated_at'],previous['updated_at']);self.assertEqual(out['refresh_status'],'FAILED_PREVIOUS_RETAINED');self.assertEqual(out['last_attempt_at'],failure['attempted_at'])

    def test_scheduled_refresh_does_not_retry_a_published_auth_failure(self):
        from scripts.refresh_verified_pro_dashboard import previous_auth_blocked
        base={'format':'lol-coach-pro-dashboard-v1','queue_id':420,'profiles':[],'status':'BLOCKED_EXTERNAL'}
        for reason in ['AUTHORIZATION_STOPPED','KEY_NOT_CONFIGURED','PREVIOUS_AUTH_FAILURE_NO_RETRY','AUTH_STOP_STATE_UNAVAILABLE']:
            self.assertTrue(previous_auth_blocked(dict(base,failures=[{'status':'API_UNAVAILABLE','reason':reason}])))
        self.assertFalse(previous_auth_blocked(dict(base,failures=[{'status':'API_UNAVAILABLE','reason':'RATE_LIMIT_STOPPED'}])))
        for invalid in [{},[],{'format':'wrong'}]:self.assertTrue(previous_auth_blocked(invalid))

    def test_first_deployment_requires_exact_previous_artifact_and_manifest(self):
        from scripts.refresh_verified_pro_dashboard import first_deployment_verified
        old={'format':'lol-coach-loading-public-export-v1','source_commit':'8acd8dfee2ccbdc1d5aacf2460dca94468221530','sha256':{'loading.js':'fixture'}}
        self.assertTrue(first_deployment_verified('ca85725e1ef6205f8f9ca1f5977ad2ce93fb6894',old))
        self.assertFalse(first_deployment_verified('other-artifact',old))
        old['sha256']['dashboard.js']='fixture';self.assertFalse(first_deployment_verified('ca85725e1ef6205f8f9ca1f5977ad2ce93fb6894',old))

    def test_public_entry_and_strategy_link_are_separate(self):
        self.assertTrue(Path('web_r4/dashboard.html').exists(),'Riot ID entry missing')
        s=Path('web_r4/dashboard.html').read_text();self.assertIn('riot-id',s);self.assertIn('loading.html',s);self.assertNotIn('RGAPI-',s)

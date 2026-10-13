"""SYNTHETIC roster/account mechanics; external Riot requests are never made."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import quote


class ProReferenceTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.pro_reference'),'pro reference module absent')
        from coach_v1 import pro_reference
        return pro_reference
    def test_exact_spaces_case_and_korean_account_routes(self):
        m=self.module()
        for riot_id in ('오 너#111','JUGKlNG#kr','강 철#샤 넬','DNS Quantum#KR 1'):
            name,tag=riot_id.split('#')
            self.assertEqual(m.account_url(riot_id),'https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/'+quote(name,safe='')+'/'+quote(tag,safe=''))
    def test_successful_account_cache_uses_stable_player_key_across_nickname_changes(self):
        m=self.module()
        with tempfile.TemporaryDirectory() as td:
            cache=m.ProReferenceCache(Path(td)/'private'/'pro-reference')
            calls=[]
            def lookup(url):calls.append(url);return {'puuid':'PRIVATE_SYNTHETIC_PUUID'}
            self.assertEqual(cache.resolve('player:Oner:primary','오 너#111',lookup),'PRIVATE_SYNTHETIC_PUUID')
            self.assertEqual(cache.resolve('player:Oner:primary','Changed Nick#Different',lookup),'PRIVATE_SYNTHETIC_PUUID')
            self.assertEqual(len(calls),1)
            fresh=m.ProReferenceCache(Path(td)/'private'/'pro-reference')
            self.assertEqual(fresh.resolve('player:Oner:primary','Another#Name',lookup),'PRIVATE_SYNTHETIC_PUUID')
            self.assertEqual(len(calls),1)
            self.assertNotIn('PRIVATE_SYNTHETIC_PUUID',json.dumps(cache.safe_summary()))
    def test_failed_account_skips_without_inventing_puuid(self):
        m=self.module()
        with tempfile.TemporaryDirectory() as td:
            cache=m.ProReferenceCache(Path(td)/'private'/'pro-reference')
            self.assertIsNone(cache.resolve('player:Missing:primary','Wrong#ID',lambda _:None))
            self.assertEqual(cache.safe_summary()['failed_accounts'],['player:Missing:primary'])


class ProCollectionTests(unittest.TestCase):
    def setUp(self):
        from coach_v1 import pro_reference
        self.m=pro_reference
        self.config=json.loads(Path('config/pro_reference_players.json').read_text())
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.directory=Path(self.tmp.name)/'private'/'pro-reference'
        self.now=2_000_000_000;self.clock_value=float(self.now);self.calls=[];self.accounts={};self.match_ids={};self.pairs={}
    def transport(self,url,headers,timeout):
        self.calls.append(url)
        if '/accounts/' in url:
            response=self.accounts.get(url)
            return (200,{},json.dumps(response).encode()) if response else (404,{},b'{}')
        from urllib.parse import unquote
        if '/by-puuid/' in url:
            puuid=unquote(url.split('/by-puuid/')[1].split('/ids')[0]);return 200,{},json.dumps(self.match_ids.get(puuid,[])).encode()
        mid=url.split('/matches/')[1].split('/')[0]
        pair=self.pairs.get(mid)
        return (200,{},json.dumps(pair['timeline'] if url.endswith('/timeline') else pair['match']).encode()) if pair else (404,{},b'{}')
    def collector(self,transport=None,**limits):
        return self.m.ProReferenceCollector(api_key='RGAPI-'+'00000000-0000-0000-0000-000000000000',transport=transport or self.transport,clock=lambda:self.clock_value,sleeper=self.sleep,max_retries=0,**limits)
    def sleep(self,seconds):self.clock_value+=seconds
    def add_account(self,role,index=0,backup=False,puuid='PRIVATE_OWNER',mid='KR_10',assigned=None):
        from tests_pregame.test_v20_postgame import body
        player=self.config['backups' if backup else 'players'][role][index]
        self.accounts[self.m.account_url(player['riot_id'])]={'puuid':puuid}
        self.match_ids[puuid]=[mid]
        b=body();canonical=self.m.CANONICAL_ROLES[assigned or role];pid={'TOP':1,'JUNGLE':2,'MID':3,'BOTTOM':4,'SUPPORT':5}[canonical]
        people=b['match']['info']['participants'];people[pid-1]['puuid']=puuid
        for payload in (b['match'],b['timeline']):payload['metadata']['matchId']=mid;payload['metadata']['participants']=[p['puuid'] for p in people]
        b['timeline']['info']['participants'][pid-1]['puuid']=puuid;b['match']['info']['gameStartTimestamp']=(self.now-60)*1000
        self.pairs[mid]=b;return player
    def test_strict_roster_and_safe_ready_preparation_has_unknown_tier(self):
        import copy
        d=self.m.prepare_pro_reference(self.config)
        self.assertEqual(d['primary_count'],25);self.assertEqual(d['backup_count'],9);self.assertEqual(d['alt_count'],1)
        self.assertEqual(d['roles'][3]['role'],'BOTTOM');self.assertEqual(d['tier'],'UNKNOWN')
        self.assertEqual(d['status'],'READY_TO_COLLECT');self.assertNotIn('\"puuid\":',json.dumps(d).lower())
        for bad in [dict(self.config,unknown=True),dict(self.config,region='EU')]:
            with self.assertRaises(ValueError):self.m.validate_pro_roster(bad)
        bad=copy.deepcopy(self.config);bad['players']['TOP'].pop()
        with self.assertRaises(ValueError):self.m.validate_pro_roster(bad)
    def test_alias_merge_dedups_account_and_games_and_private_permissions(self):
        player=self.add_account('MID',1,puuid='PRIVATE_SHOWMAKER',mid='KR_20')
        self.accounts[self.m.account_url(player['alt_riot_ids'][0])]={'puuid':'PRIVATE_SHOWMAKER'}
        c=self.collector();receipt=c.collect(self.config,self.directory,now=self.now)
        self.assertEqual(receipt['unique_recorded_matches'],1)
        self.assertEqual(sum('/by-puuid/PRIVATE_SHOWMAKER/ids' in url for url in self.calls),1)
        self.assertEqual(sum(url.endswith('/matches/KR_20') for url in self.calls),1)
        self.assertNotIn('PRIVATE_SHOWMAKER',json.dumps(receipt))
        data=json.loads((self.directory/'reference-data.json').read_text());self.assertEqual(data['tier'],'UNKNOWN');self.assertEqual(data['match_count'],1)
        self.assertNotIn('PRIVATE_SHOWMAKER',json.dumps(data));self.assertNotIn('KR_20',json.dumps(data))
        import os
        if os.name!='nt':
            for path in self.directory.rglob('*.json'):self.assertEqual(path.stat().st_mode&0o777,0o600)
        lookup_calls=len([url for url in self.calls if '/accounts/' in url]);self.calls.clear()
        changed=json.loads(json.dumps(self.config));changed['players']['MID'][1]['riot_id']='Changed Name#TAG'
        self.collector().collect(changed,self.directory,now=self.now)
        self.assertFalse(any('/accounts/' in url and 'Changed%20Name' in url for url in self.calls))
    def test_no_recent_and_low_share_replace_with_recorded_same_role_backup(self):
        primary=self.add_account('TOP',puuid='PRIVATE_NO_RECENT',mid='KR_30');self.match_ids['PRIVATE_NO_RECENT']=[]
        backup=self.add_account('TOP',backup=True,puuid='PRIVATE_BACKUP_TOP',mid='KR_31')
        self.add_account('JUNGLE',puuid='PRIVATE_WRONG_ROLE',mid='KR_32',assigned='MID')
        jungle_backup=self.add_account('JUNGLE',backup=True,puuid='PRIVATE_BACKUP_JUNGLE',mid='KR_33')
        receipt=self.collector().collect(self.config,self.directory,now=self.now)
        top=next(s for s in receipt['selections'] if s['primary_player']==primary['name'])
        self.assertEqual(top['selected_player'],backup['name']);self.assertEqual(top['replacements'][0]['reason'],'NO_RANKED_SOLO_420_WITHIN_30_DAYS')
        jungle=next(s for s in receipt['selections'] if s['primary_player']==self.config['players']['JUNGLE'][0]['name'])
        self.assertEqual(jungle['selected_player'],jungle_backup['name']);self.assertEqual(jungle['replacements'][0]['reason'],'POSITION_SHARE_BELOW_OPERATIONAL_THRESHOLD')
        self.assertEqual(receipt['position_share_threshold'],.5)
    def test_first_auth_failure_stops_globally_before_backups(self):
        called=[]
        def forbidden(url,*_):called.append(url);return 403,{},b'{}'
        receipt=self.collector(forbidden).collect(self.config,self.directory,now=self.now)
        self.assertEqual(len(called),1);self.assertEqual(receipt['status'],'BLOCKED_EXTERNAL');self.assertEqual(receipt['selections'],[])
        self.assertNotIn('PRIVATE_',json.dumps(receipt))
        self.assertEqual(receipt['observed_http_status'],403)
        self.assertEqual(receipt['user_key_expiry_attribution'],'KEY_EXPIRED_PER_USER_RULE')
        from coach_v1.pro_reference_cases import public_collection_receipt
        self.assertEqual(public_collection_receipt(receipt)['observed_http_status'],403)
    def test_missing_key_zero_requests_and_request_budget_bounded(self):
        c=self.m.ProReferenceCollector(api_key='',transport=self.transport)
        receipt=c.collect(self.config,self.directory,now=self.now);self.assertEqual(receipt['request_count'],0);self.assertEqual(self.calls,[])
        receipt=self.collector(max_requests=2).collect(self.config,self.directory,now=self.now)
        self.assertEqual(receipt['request_count'],2);self.assertEqual(receipt['status'],'BLOCKED_EXTERNAL')
    def test_private_cache_rejects_parent_traversal_before_any_write(self):
        escaped=Path(self.tmp.name)/'private'/'..'/'public'
        with self.assertRaises(ValueError):self.m.ProReferenceCache(escaped)
        self.assertFalse((Path(self.tmp.name)/'public').exists())
    def test_requested_match_identity_mismatch_cannot_create_double_samples(self):
        self.add_account('MID',1,puuid='PRIVATE_SHOWMAKER',mid='KR_20')
        self.match_ids['PRIVATE_SHOWMAKER']=['KR_20','KR_21'];self.pairs['KR_21']=self.pairs['KR_20']
        receipt=self.collector().collect(self.config,self.directory,now=self.now)
        self.assertEqual(receipt['status'],'BLOCKED_EXTERNAL');self.assertEqual(receipt['unique_recorded_matches'],0)
        self.assertFalse((self.directory/'reference-data.json').exists())

    def test_missing_timeline_does_not_trigger_unauthorized_backup_replacement(self):
        primary=self.add_account('TOP',puuid='PRIVATE_TOP',mid='KR_30')
        self.add_account('TOP',backup=True,puuid='PRIVATE_TOP_BACKUP',mid='KR_31')
        def missing(url,*args):
            if url.endswith('/KR_30/timeline'):self.calls.append(url);return 404,{},b'{}'
            return self.transport(url,*args)
        receipt=self.collector(missing).collect(self.config,self.directory,now=self.now)
        row=next(r for r in receipt['selections'] if r['primary_player']==primary['name'])
        self.assertEqual(row['replacements'],[]);self.assertEqual(row['reason'],'NO_USABLE_ROLE_TIMELINES')
        self.assertEqual(row['position_share'],1)
    def test_unknown_position_assignment_is_unknown_without_low_share_replacement(self):
        primary=self.add_account('TOP',puuid='PRIVATE_UNKNOWN_ROLE',mid='KR_40')
        self.pairs['KR_40']['match']['info']['participants'][0]['teamPosition']=''
        receipt=self.collector().collect(self.config,self.directory,now=self.now)
        row=next(r for r in receipt['selections'] if r['primary_player']==primary['name'])
        self.assertEqual(row['replacements'],[]);self.assertEqual(row['reason'],'POSITION_ASSIGNMENT_UNVERIFIED')
        self.assertIsNone(row['position_share'])

    def test_default_budget_reaches_all_25_players_and_all_five_roles(self):
        import copy
        number=1000
        for role in self.m.ROLES:
            for index in range(5):
                puuid='PRIVATE_'+role+'_'+str(index);mid='KR_'+str(number)
                player=self.add_account(role,index,puuid=puuid,mid=mid)
                base=self.pairs[mid];ids=[]
                for offset in range(20):
                    current='KR_'+str(number+offset);pair=copy.deepcopy(base)
                    pair['match']['metadata']['matchId']=current;pair['timeline']['metadata']['matchId']=current
                    self.pairs[current]=pair;ids.append(current)
                number+=20;self.match_ids[puuid]=ids
                for alt in player.get('alt_riot_ids',[]):self.accounts[self.m.account_url(alt)]={'puuid':puuid}
        def bounded(url,*args):
            from urllib.parse import parse_qs,urlsplit,unquote
            if '/by-puuid/' in url:
                self.calls.append(url);puuid=unquote(url.split('/by-puuid/')[1].split('/ids')[0]);count=int(parse_qs(urlsplit(url).query)['count'][0])
                return 200,{},json.dumps(self.match_ids[puuid][:count]).encode()
            return self.transport(url,*args)
        receipt=self.collector(bounded,max_matches=100,max_requests=250).collect(self.config,self.directory,now=self.now)
        selected=[r for r in receipt['selections'] if r['status']=='SELECTED']
        self.assertEqual(len(selected),25);self.assertEqual({r['role'] for r in selected},{'TOP','JUNGLE','MID','BOTTOM','SUPPORT'})
        self.assertLessEqual(receipt['request_count'],250);self.assertEqual(receipt['matches_per_account'],3)

    def test_collector_emits_anonymous_cases_from_selected_private_timeline(self):
        self.add_account('MID',1,puuid='PRIVATE_SHOWMAKER',mid='KR_20')
        c=self.collector();receipt=c.collect(self.config,self.directory,now=self.now)
        self.assertEqual(receipt['reference_cases_file'],'reference-cases.json')
        cases=json.loads((self.directory/'reference-cases.json').read_text())
        self.assertEqual(cases['schema_version'],'postgame.pro-reference-cases.v1')
        self.assertNotIn('PRIVATE_SHOWMAKER',json.dumps(cases));self.assertNotIn('KR_20',json.dumps(cases));self.assertNotIn('match_sha256',json.dumps(cases))
        self.assertEqual(cases,c.reference_cases_data)

    def test_cache_symlink_and_extra_aggregate_identity_rejected(self):
        self.directory.mkdir(parents=True);outside=Path(self.tmp.name)/'outside.json';outside.write_text('{}');(self.directory/'accounts.json').symlink_to(outside)
        with self.assertRaises(ValueError):self.m.ProReferenceCache(self.directory)

class ProOverlayTests(unittest.TestCase):
    def test_pro_actual_total_overlay_preserves_units_existing_delta_and_synthetic_gate(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.pro_reference_overlay'),'pro overlay module absent')
        from coach_v1.pro_reference_overlay import attach_pro_reference
        from coach_v1.pro_reference import build_pro_reference
        import copy
        observation=dict(match_sha256='a'*64,role='BOTTOM',champion='Caitlyn',patch='16.19',resources=[dict(minute=1,gold=1000,xp=200,cs=10)])
        other=copy.deepcopy(observation);other['match_sha256']='b'*64
        data=build_pro_reference([observation,other],roster_sha256='c'*64,retrieved_at='2026-10-13T00:00:00Z',sample_kind='SYNTHETIC')
        detail=dict(champion='Caitlyn',role='BOTTOM',patch='16.19',resources=[dict(minute=1,gold=1200,xp=250,cs=12)],reference=dict(status='UNKNOWN',units='RESOURCE_DELTA_NOT_ABSOLUTE_TOTAL',cohorts=[]))
        baseline=copy.deepcopy(detail);blocked=attach_pro_reference(detail,data)
        self.assertEqual(detail,baseline);self.assertEqual(blocked['pro_reference']['status'],'UNKNOWN')
        ready=attach_pro_reference(detail,data,test_mode=True)
        self.assertEqual(ready['reference'],baseline['reference']);self.assertEqual(ready['pro_reference']['comparison_group'],'PRO_ROSTER')
        self.assertEqual(ready['pro_reference']['tier'],'UNKNOWN');self.assertEqual(ready['pro_reference']['status'],'KNOWN')
        gold=next(c for c in ready['pro_reference']['cohorts'] if c['metric']=='gold')
        self.assertEqual(gold['units'],'gold total');self.assertEqual(gold['personal_points'][0]['value'],1200)
        self.assertEqual(gold['points'][0]['mean'],1000);self.assertEqual(gold['points'][0]['n'],2)
        wrong=copy.deepcopy(detail);wrong['role']='MID'
        self.assertEqual(attach_pro_reference(wrong,data,test_mode=True)['pro_reference']['status'],'UNKNOWN')
    def test_strict_pro_reference_rejects_raw_identity_fields_and_forged_visible_ci(self):
        from coach_v1.pro_reference import build_pro_reference,validate_pro_reference
        import copy
        o=dict(match_sha256='a'*64,role='BOTTOM',champion='Caitlyn',patch='16.19',resources=[dict(minute=1,gold=1000,xp=200,cs=10)])
        data=build_pro_reference([o],roster_sha256='c'*64,retrieved_at='2026-10-13T00:00:00Z',sample_kind='SYNTHETIC')
        bad=copy.deepcopy(data);bad['puuid']='PRIVATE_SHOULD_REJECT'
        with self.assertRaises(ValueError):validate_pro_reference(bad)
        bad=copy.deepcopy(data);bad['cohorts'][0]['points'][0]['visible']=True
        with self.assertRaises(ValueError):validate_pro_reference(bad)

if __name__=='__main__':unittest.main()

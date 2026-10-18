import unittest,subprocess,json,math
from pathlib import Path
class RiotGameInfoTests(unittest.TestCase):
 def mod(self):
  self.assertTrue(Path('coach_v1/game_info.py').exists(),'shared game-info service missing')
  from coach_v1 import game_info
  return game_info
 def test_projection_strips_identity_and_never_invents_state(self):
  m=self.mod();doc={'gameData':{'gameTime':60},'activePlayer':{'currentGold':125,'summonerName':'private-name','abilities':{'R':{'abilityLevel':1}}},'allPlayers':[{'championName':'Caitlyn','team':'ORDER','level':2,'position':'BOTTOM','items':[{'itemID':1055,'count':1,'slot':0}],'riotId':'private#id','summonerName':'private-name'}],'events':{'Events':[{'EventID':1,'EventName':'DragonKill','EventTime':55,'KillerName':'private-name'}]}}
  x=m.project(doc,received_at=100);self.assertEqual(x['game_time'],60);self.assertEqual(x['cash'],125);self.assertIsNone(x['earned_gold']);self.assertFalse(x['coaching_enabled']);self.assertIsNone(x['players'][0]['coordinates']);self.assertIsNone(x['timers']['ally_ultimate']);self.assertEqual(x['players'][0]['items'][0]['id'],'1055');self.assertNotIn('private',json.dumps(x));self.assertNotIn('abilities',x)
 def test_events_dedup_conflict_and_future_are_not_countdowns(self):
  m=self.mod();doc={'gameData':{'gameTime':60},'events':{'Events':[{'EventID':1,'EventName':'DragonKill','EventTime':55},{'EventID':1,'EventName':'DragonKill','EventTime':55},{'EventID':2,'EventName':'BaronKill','EventTime':61},{'EventID':3,'EventName':'TurretKilled','EventTime':10},{'EventID':3,'EventName':'TurretKilled','EventTime':11}]}}
  x=m.project(doc,received_at=100);self.assertEqual(len(x['events']),1);self.assertEqual(x['event_omissions'],4);self.assertTrue(x['event_conflicts']);self.assertIsNone(x['timers']['camps']);self.assertIsNone(x['timers']['objectives'])
 def test_service_coalesces_and_disconnect_marks_old_snapshot_stale(self):
  m=self.mod();calls=[];clock=[100.]
  def fetch(*a,**k):
   calls.append(1)
   if len(calls)>1:raise OSError('secret network info')
   return b'{"gameData":{"gameTime":10}}'
  service=m.GameInfoService(ca='fixture-ca',transport=fetch,clock=lambda:clock[0]);a=service.read();b=service.read();self.assertEqual(len(calls),1);self.assertEqual(a['snapshot'],b['snapshot']);clock[0]=102;c=service.read();self.assertEqual(c['status'],'STALE');self.assertFalse(c['current']);self.assertEqual(c['snapshot']['game_time'],10);self.assertNotIn('secret',json.dumps(c))
 def test_no_ca_no_request_and_no_fake_expired_key(self):
  m=self.mod();calls=[];x=m.GameInfoService(ca='',transport=lambda *a,**k:calls.append(1)).read();self.assertEqual(x['status'],'BLOCKED_EXTERNAL');self.assertEqual(calls,[]);self.assertNotIn('EXPIRED',json.dumps(x))
 def test_nonfinite_and_backward_session_cannot_replay_old_events(self):
  m=self.mod()
  with self.assertRaises(ValueError):m.project({'gameData':{'gameTime':float('nan')}},received_at=0)
  rows=iter([b'{"gameData":{"gameTime":90},"events":{"Events":[{"EventID":1,"EventName":"DragonKill","EventTime":70}]}}',b'{"gameData":{"gameTime":5}}']);clock=[0.];s=m.GameInfoService(ca='fixture',transport=lambda *a,**k:next(rows),clock=lambda:clock[0]);a=s.read();clock[0]=2;b=s.read();self.assertNotEqual(a['session'],b['session']);self.assertEqual(b['snapshot']['events'],[])
 def test_malformed_game_schema_and_huge_numbers_return_structured_failure(self):
  m=self.mod()
  for value in [None,[],False,10**400]:
   doc={'gameData':value} if not isinstance(value,int) or isinstance(value,bool) else {'gameData':{'gameTime':value}}
   service=m.GameInfoService(ca='fixture',transport=lambda *a,**k:json.dumps(doc).encode(),clock=lambda:100.)
   self.assertEqual(service.read()['status'],'DISCONNECTED');self.assertEqual(service.read()['status'],'DISCONNECTED')
 def test_slow_failure_is_shared_by_waiting_readers(self):
  import concurrent.futures
  m=self.mod();calls=[];clock=[100.]
  def slow(*a,**k):calls.append(1);clock[0]+=2;raise OSError('fixture timeout')
  service=m.GameInfoService(ca='fixture',transport=slow,clock=lambda:clock[0])
  with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(lambda _:service.read(),range(3)))
  self.assertEqual(len(calls),1);self.assertTrue(all(r['status']=='DISCONNECTED'for r in results))
  clock[0]+=1.1;service.read();self.assertEqual(len(calls),2)
 def test_verified_champion_names_normalize_without_retaining_arbitrary_names(self):
  m=self.mod();x=m.project({'gameData':{'gameTime':1},'allPlayers':[{'championName':name,'team':'ORDER'}for name in ["Kai'Sa","Cho'Gath","Miss Fortune",'카이사','privateName123']]},received_at=100)
  self.assertEqual([p['champion']for p in x['players']],['Kaisa','Chogath','MissFortune','Kaisa']);self.assertEqual(x['player_omissions'],1);self.assertNotIn('private',json.dumps(x))
 def node(self,code):
  r=subprocess.run(['node','-e',"const assert=require('assert/strict'),M=require('./web_r4/game-info-engine.js');const cat={version:'16.20.1',patch:'16.20',items:{'1055':{name:'도란의 검',total:450,from:[]},'3031':{name:'완성품',total:3000,from:['1055']},'0':{name:'무료',total:0,from:[]}}};"+code],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr[-2200:])
 def test_inventory_held_slots_not_nested_components_or_cash(self):
  self.node("let x=M.value([{slot:0,id:'3031',count:1},{slot:1,id:'1055',count:1}],cat,'16.20');assert.equal(x.total,3450);assert.equal(x.kind,'MANUAL_HYPOTHESIS');assert.equal(x.cash,null);assert.equal(x.earned_gold,null);assert.equal(M.value([],cat,'16.20').total,0);assert.equal(M.value([{slot:0,id:'0',count:1}],cat,'16.20').total,0);")
 def test_unknown_partial_mismatch_duplicate_and_bad_count(self):
  self.node("const a=M.value([{slot:0,id:'1055',count:1},{slot:1,id:'999999',count:1}],cat,'16.20');assert.equal(a.total,null);assert.equal(a.known_subtotal,450);assert.equal(a.missing.length,1);assert.equal(M.value([{slot:0,id:'1055',count:1}],cat,null).total,null);assert.equal(M.value([{slot:0,id:'1055',count:1}],cat,'16.19').total,null);assert.throws(()=>M.value([{slot:0,id:'1055',count:1},{slot:0,id:'1055',count:1}],cat,'16.20'));for(const count of [NaN,-1,0,1.5])assert.throws(()=>M.value([{slot:0,id:'1055',count}],cat,'16.20'));")
if __name__=='__main__':unittest.main()

class GameInfoTeamTests(unittest.TestCase):
 node=RiotGameInfoTests.node
 def test_team_value_requires_five_observed_complete_inventories(self):
  self.node("const a=Array.from({length:5},(_,i)=>({slot:i,team:'ORDER',items:[{slot:0,id:'1055',count:1}]})),b=Array.from({length:5},(_,i)=>({slot:i+5,team:'CHAOS',items:[]}));let x=M.teams([...a,...b],cat,'16.20');assert.equal(x.ORDER.total,2250);assert.equal(x.CHAOS.total,0);assert.equal(x.difference,2250);x=M.teams(a.slice(0,4),cat,'16.20');assert.equal(x.ORDER.total,null);assert.equal(x.ORDER.observed_players,4);a[0].items=null;assert.equal(M.teams([...a,...b],cat,'16.20').ORDER.total,null);")

 def test_malformed_partial_inventory_and_unknown_patch_do_not_erase_or_invent_subtotals(self):
  self.node("const x=M.teams([{slot:0,team:'ORDER',items:[{slot:0,id:'1055',count:1},{slot:1,id:'3031',count:null}]}],cat,'16.20');assert.equal(x.ORDER.total,null);assert.equal(x.ORDER.known_subtotal,450);assert.equal(M.teams([{team:'ORDER',items:[]}],cat,null).ORDER.known_subtotal,null);")

class GameInfoHTTPTests(unittest.TestCase):
 def test_local_route_requires_auth_and_does_not_need_riot_api_key(self):
  import http.client,tempfile,threading
  from coach_v1.pregame_server import PregameWorkbench
  from coach_v1.server import Limits
  with tempfile.TemporaryDirectory() as t:
   server=PregameWorkbench(Path(t)/'work.sqlite','synthetic-info-token-12345678901234567890',Limits(1000000,100,100,100,100,10));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   from coach_v1.game_info import GameInfoService
   server.game_info_service=GameInfoService(ca='')
   try:
    def get(headers):
     c=http.client.HTTPConnection('127.0.0.1',server.server_port);c.request('GET','/dev/v1/game-info',headers=headers);r=c.getresponse();body=r.read();status=r.status;c.close();return status,body
    self.assertEqual(get({})[0],401);status,body=get({'Authorization':'Bearer synthetic-info-token-12345678901234567890'});self.assertEqual(status,200);self.assertEqual(json.loads(body)['status'],'BLOCKED_EXTERNAL');self.assertEqual(len(server.research.list()),0)
    server.game_info_service=GameInfoService(ca='fixture',transport=lambda *a,**k:b'{"gameData":{"gameTime":60},"activePlayer":{"currentGold":125}}');status,body=get({'Authorization':'Bearer synthetic-info-token-12345678901234567890'});data=json.loads(body);self.assertEqual(status,200);self.assertTrue(data['transport_current']);self.assertFalse(data['display_eligible']);self.assertIsNone(data['snapshot']);self.assertNotIn('cash',data)
   finally:server.shutdown();thread.join();server.server_close()

"""Identity-free observational projection; never emits tactical live advice."""
import copy,math,os,re,threading,time
from functools import lru_cache
from urllib.error import HTTPError
from coach_intake.io import fetch,strict_json,GAME_URL

def number(x):
    if type(x) not in (int,float):return False
    try:return math.isfinite(x) and x>=0
    except OverflowError:return False

def champion_key(value):return re.sub(r"[^\w]",'',value).casefold() if isinstance(value,str) else ''

@lru_cache(maxsize=1)
def champion_names():
    from coach_v1.official_catalog import _current
    _,_,roster,_,_=_current()
    return {champion_key(alias):identity for identity,row in roster.items() for alias in (identity,row['name'])}


def project(doc,*,received_at):
    if not isinstance(doc,dict)or not number(received_at):raise ValueError('SNAPSHOT_SCHEMA')
    game=doc.get('gameData',{})
    if not isinstance(game,dict):raise ValueError('GAME_SCHEMA')
    stamp=game.get('gameTime')
    if stamp is not None and not number(stamp):raise ValueError('GAME_CLOCK')
    active=doc.get('activePlayer',{});cash=active.get('currentGold')if isinstance(active,dict)else None
    rows=doc.get('allPlayers');players=[];omitted=0
    for index,row in enumerate(rows if isinstance(rows,list)else[]):
        if not isinstance(row,dict)or champion_key(row.get('championName'))not in champion_names()or row.get('team')not in('ORDER','CHAOS'):omitted+=1;continue
        inventory=row.get('items');items=[]
        for item in inventory if isinstance(inventory,list)else[]:
            if not isinstance(item,dict):items.append({'id':None,'slot':None,'count':None});continue
            identity=item.get('itemID');count=item.get('count');slot=item.get('slot')
            items.append({'id':str(identity)if type(identity)is int and identity>=0 else None,'count':count if type(count)is int and count>0 else None,'slot':slot if type(slot)is int and 0<=slot<=6 else None})
        level=row.get('level');position=row.get('position')
        players.append({'slot':index,'champion':champion_names()[champion_key(row['championName'])],'team':row['team'],'level':level if type(level)is int and 1<=level<=30 else None,'role':position if position in('TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY')else None,'coordinates':None,'items':items if isinstance(inventory,list)else None})
    events=doc.get('events',{});events=events.get('Events',[])if isinstance(events,dict)else[]
    groups={};bad=0;conflicts=[]
    # Store event kind/time only. Names, kills/assisters and any identifiers are discarded.
    for e in events if isinstance(events,list)else[]:
        if not isinstance(e,dict)or type(e.get('EventID'))is not int or e['EventID']<0 or e.get('EventName')not in('GameStart','MinionsSpawning','DragonKill','BaronKill','HeraldKill','TurretKilled','InhibKilled','InhibRespawned')or not number(e.get('EventTime'))or stamp is None or e['EventTime']>stamp:bad+=1;continue
        safe={'id':e['EventID'],'kind':e['EventName'],'game_time':e['EventTime']};groups.setdefault(e['EventID'],[]).append(safe)
    accepted=[]
    for identity,group in groups.items():
        if any(e!=group[0]for e in group):conflicts.append(identity);bad+=len(group)
        else:accepted.append(group[0]);bad+=len(group)-1
    accepted.sort(key=lambda e:(e['game_time'],e['id']))
    return {'format':'lol-coach-game-observation-v1','source':GAME_URL,'source_kind':'LOCAL_UNVERIFIED','received_at':received_at,'game_time':stamp,'map_number':game.get('mapNumber') if type(game.get('mapNumber')) is int else None,'cash':cash if number(cash)else None,'earned_gold':None,'players':players,'players_observed':isinstance(rows,list),'player_omissions':omitted,'events':accepted,'event_omissions':bad,'event_conflicts':conflicts,'timers':{'camps':None,'objectives':None,'ally_ultimate':None},'patch':None,'coaching_enabled':False,'decision_eligible':False,'freshness_verified':False}

class GameInfoService:
    def __init__(self,*,ca=None,transport=None,clock=None):
        self.ca=ca if ca is not None else os.environ.get('LOL_COACH_RIOT_CA');self.transport=transport or fetch;self.clock=clock or time.time;self.lock=threading.Lock();self.last_at=None;self.last=None;self.session=1;self.blocked=False
    def read(self):
        with self.lock:
            now=self.clock()
            if self.last_at is not None and 0<=now-self.last_at<1:return copy.deepcopy(self.last)
            if not self.ca or self.blocked:
                self.last={'status':'BLOCKED_EXTERNAL','reason':'LOCAL_ACCESS_REQUIRED','snapshot':None,'current':False,'session':self.session};self.last_at=self.clock();return copy.deepcopy(self.last)
            prior=self.last.get('snapshot')if self.last else None
            try:
                raw=self.transport(GAME_URL,2_000_000,2,ca=self.ca);snap=project(strict_json(raw),received_at=self.clock())
                if snap['game_time']is None:raise ValueError('GAME_CLOCK_REQUIRED')
                if prior and snap['game_time']<prior['game_time']:self.session+=1
                self.last={'status':'OBSERVATION_ONLY','snapshot':snap,'current':True,'session':self.session,'actual_client_verified':False}
            except (OSError,ValueError,TypeError,KeyError)as exc:
                if isinstance(exc,HTTPError)and exc.code in(401,403):self.blocked=True
                self.last={'status':'STALE'if prior else 'DISCONNECTED','snapshot':prior,'current':False,'session':self.session,'reason':'LOCAL_DATA_UNAVAILABLE','actual_client_verified':False}
            self.last_at=self.clock()
            return copy.deepcopy(self.last)

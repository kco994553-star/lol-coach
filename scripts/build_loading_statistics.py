"""Offline projection of preserved aggregates, never a new collection or strength model."""
import gzip,json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from coach_v1.outcome_stats import _wilson
POWER='data/riot/2026-10-13/archives/full-power-16.20-CHALLENGER.json.gz'
OUTCOME='data/riot/2026-10-11/outcome-data.json.gz'
PAIRS={'A':('Caitlyn','Kaisa','BOTTOM'),'B':('Yunara','Kaisa','BOTTOM'),'BR':('Kaisa','Yunara','BOTTOM'),'C':('Darius','Ambessa','TOP'),'D':('Ezreal','Kaisa','BOTTOM')}
def read(name):return json.loads(gzip.decompress((ROOT/name).read_bytes()))
def source(data,name):
 s=data['source'];return dict(local_source=name,sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),provider=s['provider'],patch=s['patch'],queue_id=s['queue_id'],platform=s['platform'],tier=s['tier'],tier_scope='CURRENT_LEAGUE_SEED_COHORT_NOT_EVERY_PARTICIPANT_RANK',window_start=datetime.fromtimestamp(s['window_start'],timezone.utc).isoformat(),window_end=datetime.fromtimestamp(s['window_end'],timezone.utc).isoformat(),retrieved_at=s['retrieved_at'],matches=data['samples']['real_matches'],formula_version=s['formula_version'],population_formula_version=s.get('population_reference',{}).get('formula_version'))
def project():
 power,outcome=read(POWER),read(OUTCOME)
 for data in (power,outcome):
  if any(data['source'].get(key)!=value for key,value in [('patch','16.20'),('queue_id',420),('map_id',11),('tier','CHALLENGER'),('sample_kind','REAL')]):raise ValueError('ARCHIVE_SCOPE_MISMATCH')
 result=dict(format='lol-coach-statistical-context-v1',datasets=dict(power=source(power,POWER),outcome=source(outcome,OUTCOME)),matchups={},claims_of_fight_strength=False)
 for mid,(own,enemy,position)in PAIRS.items():
  exact=[];role=[]
  for c in power['cohorts']:
   if c['champion']!=own or c['position']!=position:continue
   matched=c['comparison']=='MATCHUP'and c['opponent_champion']==enemy
   if not matched and c['comparison']!='ROLE_POPULATION':continue
   for p in c['points']:
    if p['minute']not in(10,15):continue
    row=dict(metric=c['metric'],minute=p['minute'],n=p['n'],mean=p['mean']if p['visible']else None,ci95=p['ci95']if p['visible']else dict(low=None,high=None),legacy_visible=p['visible'],omission_reason=p['omission_reason'],unit={'gold_delta':'골드','xp_delta':'경험치','cs_delta':'CS'}[c['metric']]+(' / 분'if not matched else''))
    if not matched:row.update(champion_n=p['champion_n'],reference_n=p['reference_n'])
    (exact if matched else role).append(row)
  wins=0;n=0;seen=set()
  for c in outcome['cohorts']:
   if(c['champion'],c['opponent_champion'],c['position'],c['comparison'])!=(own,enemy,position,'MATCHUP'):continue
   for p in c['points']:
    hashes=p['input_match_hashes']
    if len(hashes)!=p['n']or seen.intersection(hashes):raise ValueError('OUTCOME_MATCH_REPEATED')
    seen.update(hashes);wins+=p['wins'];n+=p['n']
  result['matchups'][mid]=dict(matchup=dict(pair=[own,enemy],position=position,comparison='PAIRED_ROLE_DELTA_NOT_DUO',dataset='power',points=exact),role_context=dict(champion=own,position=position,comparison='ROLE_POPULATION_RATE',dataset='power',points=role),outcome=dict(scope='FULL_MATCH_RESULT_NOT_FIGHT_WIN',dataset='outcome',n=n,wins=wins if n else None,win_rate=wins/n if n else None,ci95=_wilson(wins,n)if n else dict(low=None,high=None)),duo_verified=False,support_pair=None,interpretation='표본과 구간이 다른 참고 통계. 원딜 상대 통계는 서포터 포함 2대2를 입증하지 않으며 자원 차이·승률은 교전력이나 최적 행동이 아니다.')
 return result
if __name__=='__main__':
 value=project()
 if '--write'in sys.argv:
  path=ROOT/'web_r4/loading-knowledge.json';k=json.loads(path.read_text());k['statistical_context']=value;path.write_text(json.dumps(k,ensure_ascii=False,indent=2)+'\n')
 else:print(json.dumps(value,ensure_ascii=False,indent=2))

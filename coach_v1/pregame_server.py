"""Additive local PRE_GAME app; all legacy Workbench routes remain available."""
import argparse
import gzip
import json
import os
from pathlib import Path
import re
import secrets
import stat
from urllib.parse import urlsplit

from .server import Workbench, Handler, Limits, ROOT
from .storage import ServiceError
from .pregame_contract import parse_input, parse_rule, proposal_rule, import_capture
from .pregame_store import PregameStore, plan_fields
from .knowledge import validate_knowledge_content, _records, _head
from .state import digest


def read_aggregate_file(path,*,max_bytes=64_000_000):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>max_bytes:raise ValueError('Invalid aggregate file')
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rb') as stream:body=stream.read(max_bytes+1)
    if len(body)>max_bytes:raise ValueError('Expanded aggregate exceeds limit')
    return json.loads(body)


def current_knowledge(research):
    """Read one coherent validated research transaction, never infer prose scope."""
    with research._db() as db:
        validate_knowledge_content(db)
        records=_records(db);heads={r['id']:_head(db,r['id']) for r in records}
        result=[]
        for row in records:
            if row['version']!=heads[row['id']]:continue
            proposal=json.loads(row['payload']);spec=None
            source=db.execute('SELECT report FROM resources WHERE id=?',(row['resource_id'],)).fetchone()
            if source:
                report=json.loads(source[0])
                if report.get('schema_version') in ('pregame.rule-source.v1','pregame.rule-source.v2','pregame.rule-source.v3'):
                    try:
                        parsed=parse_rule(report['spec']).model_dump(mode='json')
                        if report['schema_version']==parsed['schema_version'].replace('.rule.','.rule-source.'):
                            spec=parsed
                    except (ValueError,TypeError,KeyError):pass
            result.append(dict(proposal=proposal,spec=spec))
        return sorted(result,key=lambda r:r['proposal']['rule_id'])


def candidate_specs():
    rows=[]
    for name in ('executable-v1.json','executable-expanded-v1.json','initiative-v2.json','initiative-expansion-v2.json'):
        path=ROOT/'knowledge_candidates'/name
        if path.exists():
            data=json.loads(path.read_text())
            rows.extend(data if isinstance(data,list) else data['specs'])
    specs=[parse_rule(r).model_dump(mode='json') for r in rows]
    if len({s['rule_id'] for s in specs})!=len(specs):raise ServiceError(409,'CANDIDATE_ID_CONFLICT')
    return specs


def roster():
    path=ROOT/'knowledge_candidates'/'q05-roster-profiles.json'
    if not path.exists():return dict(static_version=None,champions=[])
    data=json.loads(path.read_text())
    return dict(static_version=data['source_snapshot_version'],champions=[dict(id=r['champion_id'],name=r['name'],roles=[])
        for r in data['profiles']])


class PregameWorkbench(Workbench):
    def __init__(self,db,token,limits,port=0):
        # The parent acquires the same cross-process database owner lock first.
        super().__init__(db,token,limits,port)
        try:
            self.pregame=PregameStore(str(db)+'.pregame.sqlite');self.RequestHandlerClass=PregameHandler
            # Internal fixture injection only. No HTTP operation can change these.
            self.test_mode=False;self.power_data=None;self.movement_statistics=None
            self.outcome_data=None;self.expert_new_candidates=0;self.power_datasets={};self.power_progress={};self.pro_reference_data=None
            self.pro_cases_data=None;self.opponent_right_annotations=[]
            parent=Path(db).resolve().parent
            self.personal_directory=(parent if 'private' in parent.parts else parent/'private')/'postgame'
        except Exception:self.server_close();raise

    def validated_power_data(self):
        if self.power_data is None:return None
        from .power_stats import validate_power_dataset
        dataset=validate_power_dataset(self.power_data)
        if dataset['source']['sample_kind']=='SYNTHETIC' and not self.test_mode:return None
        return dataset

    def validated_power_datasets(self):
        from .power_stats import validate_power_dataset
        rows={}
        for data in [self.power_data,*self.power_datasets.values()]:
            if data is None:continue
            item=validate_power_dataset(data)
            if item['source']['sample_kind']=='SYNTHETIC' and not self.test_mode:continue
            key=(item['source']['patch'],item['source']['tier'])
            if key in rows and digest(rows[key])!=digest(item):raise ServiceError(409,'POWER_DATASET_CONFLICT')
            rows[key]=item
        return rows

    def select_power_data(self,patch,tier):
        rows=self.validated_power_datasets()
        if patch is not None and tier is not None:return rows.get((patch,tier))
        candidates=[data for (p,t),data in rows.items() if (patch is None or p==patch) and (tier is None or t==tier)]
        return candidates[0] if len(candidates)==1 else None

    def current_pro_roster_digest(self):
        from .pro_reference import validate_pro_roster
        try:return digest(validate_pro_roster(json.loads((ROOT/'config/pro_reference_players.json').read_text())))
        except (ValueError,OSError,TypeError):return None

    def validated_progress(self,data):
        from .collection_progress import progress_response,validate_progress
        if data is None:return progress_response(None)
        progress=self.power_progress.get((data['source']['patch'],data['source']['tier']))
        return validate_progress(progress,data) if progress is not None else progress_response(data)

    def power_tiers(self):
        return sorted({tier for patch,tier in self.validated_power_datasets()})

    def validated_outcome_data(self):
        if self.outcome_data is None:return None
        from .outcome_stats import validate_outcome_dataset
        dataset=validate_outcome_dataset(self.outcome_data)
        if dataset['source']['sample_kind']=='SYNTHETIC' and not self.test_mode:return None
        return dataset


def unknown_power_view(reason):
    return dict(status='UNKNOWN',points=[],markers=[],reasons=[reason],source=None,samples=None,
                dataset_digest=None,schema_version='pregame.power-data.v1')


def power_request(body):
    fields={'champion','position','patch','tier','opponent_champion'}
    if not isinstance(body,dict) or set(body)!=fields:raise ServiceError(422,'INVALID_POWER_REQUEST')
    def champion(value,nullable=False):
        return nullable and value is None or isinstance(value,str) and re.fullmatch('[A-Za-z][A-Za-z0-9]{0,99}',value) is not None
    if not champion(body['champion']) or not champion(body['opponent_champion'],True):raise ServiceError(422,'INVALID_POWER_REQUEST')
    if body['position'] not in ('TOP','JUNGLE','MID','BOTTOM','SUPPORT'):raise ServiceError(422,'INVALID_POWER_REQUEST')
    if body['patch'] is not None and (not isinstance(body['patch'],str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,99}',body['patch'])):
        raise ServiceError(422,'INVALID_POWER_REQUEST')
    if body['tier'] is not None and body['tier'] not in ('IRON','BRONZE','SILVER','GOLD','PLATINUM','EMERALD','DIAMOND','MASTER','GRANDMASTER','CHALLENGER'):
        raise ServiceError(422,'INVALID_POWER_REQUEST')
    return body


def power_response(server,request):
    from .recall_pc import pc_power_response
    cached=pc_power_response(server,request)
    if cached is not None:return cached
    data=server.select_power_data(request['patch'],request['tier'])
    reason='POWER_DATA_NOT_AVAILABLE' if data is None else None
    if request['patch'] is None:reason='PATCH_UNKNOWN'
    tier=request['tier']
    if data is not None and tier is None:
        tiers={c['tier'] for c in data['cohorts'] if c['patch']==request['patch']}
        if len(tiers)==1:tier=next(iter(tiers))
        else:reason='TIER_UNKNOWN_OR_AMBIGUOUS'
    if reason:return dict(view=unknown_power_view(reason),opponent_view=None,test_mode=server.test_mode)
    from .power_stats import select_power_view
    fingerprint=digest(data)
    def select(champion,opponent):
        result=select_power_view(data,champion,request['position'],request['patch'],tier,opponent)
        return dict(result,dataset_digest=fingerprint,schema_version=data['schema_version'])
    return dict(view=select(request['champion'],request['opponent_champion']),
                opponent_view=select(request['opponent_champion'],request['champion']) if request['opponent_champion'] else None,
                test_mode=server.test_mode)


def outcome_response(server,request):
    data=server.validated_outcome_data()
    reason='OUTCOME_DATA_NOT_AVAILABLE' if data is None else None
    if request['patch'] is None:reason='PATCH_UNKNOWN'
    tier=request['tier']
    if data is not None and tier is None:
        tiers={c['tier'] for c in data['cohorts'] if c['patch']==request['patch']}
        if len(tiers)==1:tier=next(iter(tiers))
        else:reason='TIER_UNKNOWN_OR_AMBIGUOUS'
    if reason:
        view=dict(status='UNKNOWN',points=[],reasons=[reason],source=None,samples=None,
                  dataset_digest=None,schema_version='pregame.outcome-data.v1')
    else:
        from .outcome_stats import select_outcome_view
        selected=select_outcome_view(data,request['champion'],request['position'],request['patch'],tier,request['opponent_champion'])
        view=dict(selected,dataset_digest=digest(data),schema_version=data['schema_version'])
    return dict(view=view,test_mode=server.test_mode)


def postgame_response(server,store,match_id,plan=None):
    """Choose only same-patch descriptive reference, preferring high seed tiers."""
    result=store.get_match(match_id,plan=plan,movement_data=server.movement_statistics)
    datasets=server.validated_power_datasets()
    preference={'CHALLENGER':0,'GRANDMASTER':1,'MASTER':2}
    candidates=[data for (patch,tier),data in datasets.items() if patch==result['patch'] and
        any(c['champion']==result['champion'] and c['position']==result['role'] for c in data['cohorts'])]
    candidates.sort(key=lambda data:(preference.get(data['source']['tier'],3),data['source']['tier']))
    if candidates:
        result=store.get_match(match_id,power_data=candidates[0],movement_data=server.movement_statistics,plan=plan)
    if server.pro_reference_data is not None:
        from .pro_reference_overlay import attach_pro_reference
        matches=server.pro_reference_data['roster_sha256']==server.current_pro_roster_digest()
        result=attach_pro_reference(result,server.pro_reference_data if matches else None,test_mode=server.test_mode)
        if not matches:result['pro_reference']['reason']='PRO_ROSTER_VERSION_MISMATCH'
    from .recall_pc import private_context
    body,_,_=store._load(match_id)
    try:
        result['recall_contexts']=private_context(body['match'],body['timeline'],body['participant_id'])
    except (ValueError,KeyError,TypeError):
        result['recall_contexts']=dict(status='UNKNOWN',reason='RECALL_FIELDS_OR_SUPPORTED_MATCH_UNAVAILABLE',signals=[])
    return result


def load_expert_directory(server,directory,*,explicit=False):
    """Validate the complete bounded local batch before the first import write."""
    from .expert_contract import validate_expert_artifact,MAX_BYTES
    from .server import strict_json
    directory=Path(directory)
    if directory.is_symlink():raise ValueError('INVALID_EXPERT_DIRECTORY')
    if not directory.exists():
        if explicit:raise ValueError('EXPERT_DIRECTORY_UNAVAILABLE')
        return dict(new_candidates=0,claims=[])
    if not directory.is_dir():raise ValueError('INVALID_EXPERT_DIRECTORY')
    files=[]
    for path in directory.glob('*.json'):
        files.append(path)
        if len(files)>100:raise ValueError('EXPERT_DIRECTORY_LIMIT')
    artifacts=[];total=0
    for path in sorted(files):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\.json',path.name) or path.is_symlink() or path.resolve().parent!=directory.resolve():
            raise ValueError('INVALID_EXPERT_FILE')
        try:
            if not stat.S_ISREG(path.lstat().st_mode):raise ValueError('INVALID_EXPERT_FILE')
            fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
            with os.fdopen(fd,'rb') as stream:
                info=os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size>MAX_BYTES:raise ValueError('INVALID_EXPERT_FILE')
                raw=stream.read(MAX_BYTES+1)
            total+=len(raw)
            if len(raw)>MAX_BYTES or total>2_000_000:raise ValueError('EXPERT_DIRECTORY_LIMIT')
            artifacts.append(validate_expert_artifact(strict_json(raw.decode('utf-8'))))
        except (OSError,UnicodeError,ValueError,RecursionError):raise ValueError('INVALID_EXPERT_FILE') from None
    if not artifacts:return dict(new_candidates=0,claims=[])
    from .expert_bridge import import_expert_artifact
    result=dict(new_candidates=0,claims=[])
    for artifact in artifacts:
        imported=import_expert_artifact(server.research,artifact,max_bytes=server.limits.body_bytes)
        result['new_candidates']+=imported['new_candidates'];result['claims'].extend(imported['claims'])
    server.expert_new_candidates+=result['new_candidates']
    return result


class PregameHandler(Handler):
    def bounded_reply(self,status,value):
        if len(json.dumps(value,ensure_ascii=False,allow_nan=False).encode())>self.server.limits.body_bytes:
            raise ServiceError(413,'PREGAME_TOO_LARGE')
        return self.reply(status,value)

    def check_input(self,value):
        parsed=parse_input(value)
        provenance=[parsed.source]
        for slot in parsed.slots:provenance.extend([slot.champion_source,slot.position_source,slot.runes.source,slot.summoners.source])
        if any(p.kind=='AUTOMATIC' and p.verification=='SOURCE_VERIFIED' for p in provenance):
            raise ServiceError(422,'AUTOMATIC_ADAPTER_UNAVAILABLE')
        if parsed.original_capture is not None:
            original=parsed.original_capture
            try:stored=self.server.store.get_capture(original['session_id'],original['revision'],max_bytes=self.server.limits.body_bytes)
            except (KeyError,ValueError,TypeError):raise ServiceError(409,'ORIGINAL_CAPTURE_MISMATCH') from None
            if stored!=original:raise ServiceError(409,'ORIGINAL_CAPTURE_MISMATCH')
        return parsed.model_dump(mode='json')

    def fingerprint(self,knowledge):
        from .pregame_evaluator import knowledge_fingerprint
        return knowledge_fingerprint(knowledge)

    def checked_plan(self,pid,knowledge):
        from .pregame_evaluator import evaluate_gameplan
        result=self.server.pregame.get_plan(pid,self.fingerprint(knowledge))
        # A restored archive is data, not new approval authority. Even if its
        # declared fingerprint matches, its generated content must match the
        # current source-bound deterministic evaluator before becoming CURRENT.
        if result['validity']=='CURRENT':
            draft=parse_input(result['input'])
            if result['schema_version']=='pregame.plan.v3':
                from .pregame_v3 import evaluate_gameplan_v3
                expected=evaluate_gameplan_v3(draft,knowledge,self.server.movement_statistics,self.server.test_mode)
                if result['movement_statistics_fingerprint']!=expected['movement_statistics_fingerprint']:
                    return dict(result,validity='EXPIRED',expiry_reasons=['MOVEMENT_STATISTICS_CHANGED'])
            elif result['schema_version']=='pregame.plan.v2':
                from .pregame_v2 import evaluate_gameplan_v2
                expected=evaluate_gameplan_v2(draft,knowledge)
            else:expected=evaluate_gameplan(draft,knowledge)
            if {k:result[k] for k in plan_fields(result)}!=expected:
                result=dict(result,validity='EXPIRED',expiry_reasons=['PLAN_RESULT_MISMATCH'])
        return result

    def dispatch(self):
        self.preflight();path=urlsplit(self.path);route=path.path
        if path.query or path.fragment:raise ServiceError(400,'QUERY_NOT_SUPPORTED')
        # Public, manual learning examples only. No account/live-game adapter or
        # private workbench export is reachable from this explicit asset list.
        learning_assets={
            **{'/home-assets/'+p:('home-assets/'+p,'image/jpeg') for p in ('Ahri.jpg','Caitlyn.jpg','AhriSkin27.jpg','LuxSkin7.jpg','lane.jpg','fight.jpg')},
            '/coach-theme.css':('coach-theme.css','text/css; charset=utf-8'),
            '/coach-shell.js':('coach-shell.js','text/javascript; charset=utf-8'),
            '/hero-art.json':('hero-art.json','application/json; charset=utf-8'),
            **{'/home-assets/'+p:('home-assets/'+p,'image/jpeg') for p in ('AsheBase.jpg', 'AsheSkin17.jpg', 'KaisaBase.jpg', 'KaisaSkin14.jpg', 'JinxBase.jpg', 'JinxSkin4.jpg', 'EzrealBase.jpg', 'EzrealSkin21.jpg', 'LuxBase.jpg', 'LuxSkin17.jpg', 'YasuoBase.jpg', 'YasuoSkin9.jpg', 'YoneBase.jpg', 'YoneSkin1.jpg', 'IreliaBase.jpg', 'IreliaSkin37.jpg', 'VayneBase.jpg', 'VayneSkin25.jpg', 'LeonaBase.jpg', 'LeonaSkin10.jpg')},
            **{'/home-assets/'+p:('home-assets/'+p,'image/webp') for p in ('game-lane.webp', 'game-operations.webp', 'game-fight.webp')},
            '/home-assets/strategy-panels.webp':('home-assets/strategy-panels.webp','image/webp'),
            **{'/home-assets/'+p:('home-assets/'+p,'image/webp') for p in ('Moonlit.webp','strategy-objectives.webp')},
            '/dashboard.html':('dashboard.html','text/html; charset=utf-8'),
            '/dashboard.js':('dashboard.js','text/javascript; charset=utf-8'),
            '/dashboard.css':('dashboard.css','text/css; charset=utf-8'),
            '/pro-dashboard.json':('pro-dashboard.json','application/json; charset=utf-8'),
            '/skill-data.js':('skill-data.js','text/javascript; charset=utf-8'),
            '/skill-display.js':('skill-display.js','text/javascript; charset=utf-8'),
            '/loading':('loading.html','text/html; charset=utf-8'),
            '/loading.html':('loading.html','text/html; charset=utf-8'),
            '/loading.js':('loading.js','text/javascript; charset=utf-8'),
            **{'/'+p:(p,'application/json; charset=utf-8' if p.endswith('.json') else 'text/css; charset=utf-8' if p.endswith('.css') else 'text/html; charset=utf-8' if p.endswith('.html') else 'text/javascript; charset=utf-8') for p in ('game-info.html','game-info.js','game-info-engine.js','game-info.css','game-info-items.json')},
            '/loading-planboard.js':('loading-planboard.js','text/javascript; charset=utf-8'),
            '/loading-formation.js':('loading-formation.js','text/javascript; charset=utf-8'),
            '/loading-coach.js':('loading-coach.js','text/javascript; charset=utf-8'),
            '/loading-coach-view.js':('loading-coach-view.js','text/javascript; charset=utf-8'),
            '/loading-coach.css':('loading-coach.css','text/css; charset=utf-8'),
            '/loading-knowledge.json':('loading-knowledge.json','application/json; charset=utf-8'),
            '/loading-study.js':('loading-study.js','text/javascript; charset=utf-8'),
            '/loading-exchange.js':('loading-exchange.js','text/javascript; charset=utf-8'),
            '/loading-exchange-view.js':('loading-exchange-view.js','text/javascript; charset=utf-8'),
            '/loading-engagement.js':('loading-engagement.js','text/javascript; charset=utf-8'),
            '/loading-engagement-view.js':('loading-engagement-view.js','text/javascript; charset=utf-8'),
            '/loading-wave.js':('loading-wave.js','text/javascript; charset=utf-8'),
            '/loading-wave-view.js':('loading-wave-view.js','text/javascript; charset=utf-8'),
            '/loading-exploration.js':('loading-exploration.js','text/javascript; charset=utf-8'),
            '/loading-interactive.js':('loading-interactive.js','text/javascript; charset=utf-8'),
            '/loading-engine.js':('loading-engine.js','text/javascript; charset=utf-8'),
            '/loading-map.js':('loading-map.js','text/javascript; charset=utf-8'),
            '/loading.css':('loading.css','text/css; charset=utf-8'),
            '/loading-data.json':('loading-data.json','application/json; charset=utf-8'),
            **{'/loading-assets/champion'+str(i)+'.png':('loading-assets/champion'+str(i)+'.png','image/png') for i in range(6)},
            '/directions':('directions.html','text/html; charset=utf-8'),
            '/directions.html':('directions.html','text/html; charset=utf-8'),
            '/index.html':('dashboard.html','text/html; charset=utf-8'),
            '/directions.js':('directions.js','text/javascript; charset=utf-8'),
            '/directions-engine.js':('directions-engine.js','text/javascript; charset=utf-8'),
            '/directions.css':('directions.css','text/css; charset=utf-8'),
            '/directions-data.json':('directions-data.json','application/json; charset=utf-8'),
            '/directions-status.json':('directions-status.json','application/json; charset=utf-8'),
            '/directions-status.js':('directions-status.js','text/javascript; charset=utf-8'),
            '/status.html':('status.html','text/html; charset=utf-8'),
            **{'/direction-assets/'+name:('direction-assets/'+name,'image/png')
               for name in ('map11.png','Caitlyn.png','Fiora.png','Ornn.png')}}
        if self.command=='GET' and route in learning_assets:
            filename,ctype=learning_assets[route]
            return self.reply(200,(ROOT/'web_r4'/filename).read_bytes(),ctype)
        assets={'/pc':('pc.html','text/html; charset=utf-8'),'/pc/':('pc.html','text/html; charset=utf-8'),
            '/pc.js':('pc.js','text/javascript; charset=utf-8'),'/pc.css':('pc.css','text/css; charset=utf-8'),
            '/pregame':('pregame.html','text/html; charset=utf-8'),'/pregame/':('pregame.html','text/html; charset=utf-8'),
            '/experts':('experts.html','text/html; charset=utf-8'),'/experts/':('experts.html','text/html; charset=utf-8'),
            '/experts.js':('experts.js','text/javascript; charset=utf-8'),
            '/experts_review.js':('experts_review.js','text/javascript; charset=utf-8'),
            '/experts.css':('experts.css','text/css; charset=utf-8'),
            '/pregame.js':('pregame.js','text/javascript; charset=utf-8'),'/pregame.css':('pregame.css','text/css; charset=utf-8'),
            '/pregame_power.js':('pregame_power.js','text/javascript; charset=utf-8'),
            '/pregame_outcome.js':('pregame_outcome.js','text/javascript; charset=utf-8'),
            '/pregame-icon.svg':('pregame-icon.svg','image/svg+xml'),
            '/review-queue':('review_queue.html','text/html; charset=utf-8'),
            '/review-queue/':('review_queue.html','text/html; charset=utf-8'),
            '/review_queue.html':('review_queue.html','text/html; charset=utf-8'),
            '/review_queue.js':('review_queue.js','text/javascript; charset=utf-8'),
            '/review_queue.css':('review_queue.css','text/css; charset=utf-8'),
            '/official_reference.js':('official_reference.js','text/javascript; charset=utf-8'),
            '/postgame':('postgame.html','text/html; charset=utf-8'),
            '/postgame/':('postgame.html','text/html; charset=utf-8'),
            '/postgame.html':('postgame.html','text/html; charset=utf-8'),
            '/postgame.js':('postgame.js','text/javascript; charset=utf-8'),
            '/postgame.css':('postgame.css','text/css; charset=utf-8'),
            '/pro_reference_view.js':('pro_reference_view.js','text/javascript; charset=utf-8'),
            '/setup':('setup.html','text/html; charset=utf-8'),
            '/statistics':('statistics.html','text/html; charset=utf-8'),
            '/statistics.js':('statistics.js','text/javascript; charset=utf-8'),
            '/statistics.css':('statistics.css','text/css; charset=utf-8')}
        if self.command=='GET' and route in assets:
            filename,ctype=assets[route];file=ROOT/'web_r4'/filename
            if not file.exists():raise ServiceError(404,'PREGAME_UI_NOT_INSTALLED')
            return self.reply(200,file.read_bytes(),ctype)
        if route=='/dev/v1/game-info' and self.command=='GET':
            self.authorize()
            from .game_info import GameInfoService
            with self.server.job_lock:
                if not hasattr(self.server,'game_info_service'):self.server.game_info_service=GameInfoService()
                service=self.server.game_info_service
            data=service.read()
            # Ingestion availability does not authorize live dynamic display (Frozen mode gate).
            return self.bounded_reply(200,{k:data[k] for k in ('status','reason','session') if k in data}|dict(current=False,snapshot=None,transport_current=data['current'],display_eligible=False,reason_display='LIVE_DISPLAY_POLICY_UNVERIFIED'))
        if route=='/dev/v1/account/lookup' and self.command=='POST':
            self.authorize()
            from .account_dashboard import AccountDashboardService
            if not hasattr(self.server,'account_dashboard_service'):
                # Reuse a single service for rate windows and auth/rate-limit stop state.
                with self.server.job_lock:
                    if not hasattr(self.server,'account_dashboard_service'):
                        self.server.account_dashboard_service=AccountDashboardService()
            return self.bounded_reply(200,self.server.account_dashboard_service.lookup(self.body()))
        if route.startswith('/dev/v1/experts/'):
            self.authorize()
            if route=='/dev/v1/experts/claims' and self.command=='GET':
                from .expert_bridge import list_expert_claims
                result=list_expert_claims(self.server.research,max_bytes=self.server.limits.body_bytes,
                    movement_data=self.server.movement_statistics,test_mode=self.server.test_mode)
                result['new_candidates']=self.server.expert_new_candidates
                return self.bounded_reply(200,result)
            if route=='/dev/v1/experts/import' and self.command=='POST':
                from .expert_contract import validate_expert_artifact
                body=self.body();self.fields(body,('artifact',))
                artifact=validate_expert_artifact(body['artifact'])
                from .expert_bridge import import_expert_artifact
                return self.bounded_reply(201,import_expert_artifact(self.server.research,artifact,max_bytes=self.server.limits.body_bytes))
            raise ServiceError(404,'NOT_FOUND')
        if route.startswith('/dev/v1/postgame/'):
            self.authorize()
            if route=='/dev/v1/postgame/reference-cases' and self.command=='GET':
                from .pro_reference_cases import validate_reference_cases,empty_reference_cases
                data=self.server.pro_cases_data
                if data is not None:
                    data=validate_reference_cases(data)
                    if data['roster_sha256']!=self.server.current_pro_roster_digest() or (data['sample_kind']=='SYNTHETIC' and not self.server.test_mode):data=None
                return self.bounded_reply(200,data if data is not None else empty_reference_cases())
            if route=='/dev/v1/postgame/reference-roster' and self.command=='GET':
                from .pro_reference import prepare_pro_reference
                return self.bounded_reply(200,prepare_pro_reference(json.loads((ROOT/'config/pro_reference_players.json').read_text())))
            from .postgame_match import PostgameStore
            store=PostgameStore(self.server.personal_directory,test_mode=self.server.test_mode)
            if route=='/dev/v1/postgame/matches' and self.command=='GET':
                return self.bounded_reply(200,store.list_matches())
            if route=='/dev/v1/postgame/import' and self.command=='POST':
                return self.bounded_reply(201,store.import_match(self.body()))
            if route=='/dev/v1/postgame/analyze' and self.command=='POST':
                body=self.body();self.fields(body,('match_id','plan_id'))
                if not isinstance(body['match_id'],str) or not re.fullmatch('[a-f0-9]{64}',body['match_id']):raise ServiceError(422,'INVALID_MATCH_ID')
                if body['plan_id'] is not None and (not isinstance(body['plan_id'],str) or not re.fullmatch('[a-f0-9]{32}',body['plan_id'])):raise ServiceError(422,'INVALID_PLAN_ID')
                plan=self.checked_plan(body['plan_id'],current_knowledge(self.server.research)) if body['plan_id'] else None
                try:
                    result=postgame_response(self.server,store,body['match_id'],plan)
                except KeyError:raise ServiceError(404,'POSTGAME_MATCH_NOT_FOUND') from None
                return self.bounded_reply(200,result)
            match_route=re.fullmatch(r'/dev/v1/postgame/matches/([a-f0-9]{64})',route)
            if match_route and self.command=='GET':
                try:
                    result=postgame_response(self.server,store,match_route[1])
                except KeyError:raise ServiceError(404,'POSTGAME_MATCH_NOT_FOUND') from None
                return self.bounded_reply(200,result)
            raise ServiceError(404,'NOT_FOUND')
        prefix='/dev/v1/pregame'
        if not route.startswith(prefix+'/'):return super().dispatch()
        self.authorize();pg=self.server.pregame;limit=self.server.limits.body_bytes
        if route==prefix+'/pc-preview' and self.command=='POST':
            from .pc_coach import preview
            return self.bounded_reply(200,preview(self.server,self.body()))
        if route==prefix+'/recall-reference' and self.command=='POST':
            from .recall_pc import reference_response
            return self.bounded_reply(200,reference_response(self.server,self.body()))
        if route==prefix+'/official-items' and self.command=='POST':
            body=self.body()
            self.fields(body,('patch',))
            if body['patch'] is not None and (not isinstance(body['patch'],str) or not re.fullmatch(r'\d{1,3}\.\d{1,3}(?:\.\d{1,3})?',body['patch'])):
                raise ServiceError(422,'INVALID_ITEM_PATCH')
            from .official_items import items_response
            return self.bounded_reply(200,items_response(body['patch']))
        if route==prefix+'/pc-status' and self.command=='GET':
            from .pc_runtime import pc_status
            return self.bounded_reply(200,pc_status(self.server))
        if route==prefix+'/pc-objection' and self.command=='POST':
            # Same-account human/code distinction is an operating rule, as for
            # USER_WEB. Only the trusted user button calls this protected route.
            from .pc_coach import objection
            return self.bounded_reply(200,objection(self.server,self.body()))
        if route==prefix+'/official-catalog':
            from .official_catalog import facts_response,request_facts
            if self.command=='GET':return self.bounded_reply(200,facts_response())
            if self.command=='POST':return self.bounded_reply(200,request_facts(self.body()))
        if route==prefix+'/status' and self.command=='GET':
            return self.bounded_reply(200,dict(mode='PRE_GAME',automatic_collection='UNAVAILABLE',current_patch=None,
                knowledge_count=len(current_knowledge(self.server.research)),accuracy=None,
                test_mode=self.server.test_mode,power_tiers=self.server.power_tiers()))
        if route==prefix+'/review-queue' and self.command=='GET':
            from .review_queue import queue_response
            return self.bounded_reply(200,queue_response(self.server,focused=True))
        if route==prefix+'/official-facts':
            from .official_reference import facts_response,request_facts
            if self.command=='GET':return self.bounded_reply(200,facts_response())
            if self.command=='POST':return self.bounded_reply(200,request_facts(self.body()))
        if route==prefix+'/review-queue/archive' and self.command=='GET':
            from .review_queue import queue_response
            return self.bounded_reply(200,queue_response(self.server))
        if route==prefix+'/review-queue/archive/page' and self.command=='POST':
            from .review_queue import queue_response
            body=self.body();self.fields(body,('page','later_page'))
            return self.bounded_reply(200,queue_response(self.server,page=body['page'],later_page=body['later_page']))
        if route==prefix+'/review-queue/github-sync' and self.command=='POST':
            self.fields(self.body(),())
            from .practical_review import sync_github
            return self.bounded_reply(200,sync_github(self.server.research))
        if route==prefix+'/review-queue/page' and self.command=='POST':
            from .review_queue import queue_response
            body=self.body();self.fields(body,('page','later_page'))
            if any(type(body[k]) is not int or not 0<=body[k]<=10000 for k in body):raise ServiceError(422,'INVALID_REVIEW_PAGE')
            return self.bounded_reply(200,queue_response(self.server,page=body['page'],later_page=body['later_page'],focused=True))
        if route==prefix+'/review-queue/later' and self.command=='POST':
            from .review_queue import defer_candidate
            return self.bounded_reply(200,defer_candidate(self.server,self.body()))
        if route==prefix+'/power-catalog' and self.command=='GET':
            from .collection_progress import progress_response
            datasets=[]
            from .role_baseline_view import role_baseline_curves_from_validated
            for (patch,tier),data in sorted(self.server.validated_power_datasets().items(),key=lambda row:str(row[0])):
                progress=self.server.validated_progress(data)
                datasets.append(dict(patch=patch,tier=tier,sample_kind=data['source']['sample_kind'],
                    champions=sorted({c['champion'] for c in data['cohorts']}),progress=progress,
                    role_baseline_curves=role_baseline_curves_from_validated(data,progress)))
            return self.bounded_reply(200,dict(datasets=datasets,test_mode=self.server.test_mode))
        if route==prefix+'/collection-progress' and self.command=='GET':
            from .collection_progress import progress_response
            return self.bounded_reply(200,self.server.validated_progress(self.server.validated_power_data()))
        if route==prefix+'/power-view' and self.command=='POST':
            return self.bounded_reply(200,power_response(self.server,power_request(self.body())))
        if route==prefix+'/challenger-reference' and self.command=='POST':
            from .challenger_reference import challenger_reference_response
            try:result=challenger_reference_response(self.server,self.body())
            except ValueError:raise ServiceError(422,'INVALID_CHALLENGER_REFERENCE_REQUEST') from None
            return self.bounded_reply(200,result)
        if route==prefix+'/opponent-rights' and self.command=='POST':
            from .opponent_rights import opponent_rights_response
            body=self.body();self.fields(body,('plan_id',))
            if not isinstance(body['plan_id'],str) or not re.fullmatch('[a-f0-9]{32}',body['plan_id']):raise ServiceError(422,'INVALID_PLAN_ID')
            plan=self.checked_plan(body['plan_id'],current_knowledge(self.server.research))
            return self.bounded_reply(200,opponent_rights_response(self.server,plan))
        if route==prefix+'/outcome-view' and self.command=='POST':
            return self.bounded_reply(200,outcome_response(self.server,power_request(self.body())))
        if route==prefix+'/roster' and self.command=='GET':return self.bounded_reply(200,roster())
        if route==prefix+'/review-priority' and self.command=='GET':
            path=ROOT/'knowledge_candidates'/'q05-review-priority.json'
            return self.bounded_reply(200,json.loads(path.read_text())['recommended_review_order'] if path.exists() else [])
        if route==prefix+'/knowledge' and self.command=='GET':return self.bounded_reply(200,current_knowledge(self.server.research))
        if route==prefix+'/candidates':
            if self.command=='GET':return self.bounded_reply(200,candidate_specs())
            if self.command=='POST':
                b=self.body();self.fields(b,('spec',),('rule_id','expected_version'));spec=parse_rule(b['spec'])
                if ('rule_id' in b)!=('expected_version' in b) or (b.get('rule_id') is None)!=(b.get('expected_version') is None):raise ServiceError(422,'CANDIDATE_REVISION_REQUIRED')
                if b.get('rule_id') is not None:
                    prior=self.server.research.get_proposal(b['rule_id'],max_bytes=limit)
                    if prior['version']!=b.get('expected_version'):raise ServiceError(409,'REVISION_CONFLICT')
                source=self.server.research.add('RAW_DIAGNOSTIC',spec.rule_id[:200],
                    dict(schema_version=spec.schema_version.replace('.rule.','.rule-source.'),spec=spec.model_dump(mode='json')))
                note=self.server.research.get_note(source['id'],'overview')
                if note['revision']==0:
                    note=self.server.research.put_note(source['id'],'overview',dict(known='AI 구조화 후보 명세 sha256:'+digest(spec.model_dump(mode='json')),
                        intention='경기 전 사용자 검토용; 출처 원문/패치/반례는 저장 자료 명세에 포함',alternative='',outcome='실제 코칭 성능 미검증'),0)
                proposal=self.server.research.propose(proposal_rule(spec),dict(resource_id=source['id'],anchor='overview',note_revision=note['revision']),b.get('rule_id'),b.get('expected_version'),max_bytes=limit)
                return self.bounded_reply(201,dict(proposal=proposal,spec=spec.model_dump(mode='json')))
        if route==prefix+'/export' and self.command=='GET':return self.bounded_reply(200,pg.export_data())
        if route==prefix+'/restore' and self.command=='POST':
            b=self.body();self.fields(b,('archive',))
            archive=b['archive']
            if not isinstance(archive,dict) or not isinstance(archive.get('inputs'),list):raise ServiceError(422,'INVALID_PREGAME_ARCHIVE')
            for record in archive['inputs']:self.check_input(record['input'])
            return self.bounded_reply(200,pg.import_data(archive))
        if route==prefix+'/inputs':
            if self.command=='GET':return self.bounded_reply(200,pg.list_inputs())
            if self.command=='POST':
                b=self.body();self.fields(b,('input',));key=self.key();value=self.check_input(b['input'])
                return self.bounded_reply(201,pg.save(value,None,0,key))
        imported=re.fullmatch(re.escape(prefix)+r'/import-draft/([a-f0-9]{32})',route)
        if imported and self.command=='GET':
            record=self.server.store.get_capture(imported[1],max_bytes=limit)
            return self.bounded_reply(200,import_capture(record))
        input_route=re.fullmatch(re.escape(prefix)+r'/inputs/([a-f0-9]{32})(?:/(history|plans|plan-history))?',route)
        if input_route:
            sid,action=input_route.groups()
            if action=='history' and self.command=='GET':return self.bounded_reply(200,pg.history(sid))
            if action=='plan-history' and self.command=='GET':
                knowledge=current_knowledge(self.server.research)
                fields=('id','session_id','revision','input_revision','created_at','validity','expiry_reasons','schema_version')
                history=[]
                for plan in pg.list_plans(sid,self.fingerprint(knowledge)):
                    checked=self.checked_plan(plan['id'],knowledge)
                    history.append({key:checked[key] for key in fields})
                return self.bounded_reply(200,history)
            if action=='plans':
                from .pregame_v3 import evaluate_gameplan_v3
                knowledge=current_knowledge(self.server.research)
                if self.command=='GET':
                    plans=pg.list_plans(sid,self.fingerprint(knowledge))
                    return self.bounded_reply(200,[self.checked_plan(p['id'],knowledge) for p in plans])
                if self.command=='POST':
                    b=self.body();self.fields(b,('expected_revision',));key=self.key()
                    replay=pg.replay_plan(sid,b['expected_revision'],key)
                    if replay:return self.bounded_reply(201,self.checked_plan(replay['id'],knowledge))
                    record=pg.get_input(sid)
                    if record['revision']!=self.revision(b['expected_revision']):raise ServiceError(409,'REVISION_CONFLICT')
                    result=evaluate_gameplan_v3(parse_input(record['input']),knowledge,self.server.movement_statistics,self.server.test_mode)
                    if self.fingerprint(current_knowledge(self.server.research))!=result['knowledge_fingerprint']:
                        raise ServiceError(409,'KNOWLEDGE_CHANGED')
                    saved=pg.save_plan(sid,b['expected_revision'],result,key)
                    return self.bounded_reply(201,self.checked_plan(saved['id'],current_knowledge(self.server.research)))
            if action is None:
                if self.command=='GET':return self.bounded_reply(200,pg.get_input(sid))
                if self.command=='PUT':
                    b=self.body();self.fields(b,('input','expected_revision'));key=self.key();value=self.check_input(b['input'])
                    return self.bounded_reply(200,pg.save(value,sid,self.revision(b['expected_revision']),key))
        plan=re.fullmatch(re.escape(prefix)+r'/plans/([a-f0-9]{32})',route)
        if plan and self.command=='GET':return self.bounded_reply(200,self.checked_plan(plan[1],current_knowledge(self.server.research)))
        raise ServiceError(404,'NOT_FOUND')


def main():
    parser=argparse.ArgumentParser(description='Local pregame plans and source review; no in-game coaching')
    parser.add_argument('--db',type=Path,required=True);parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--token-file',type=Path,required=True)
    parser.add_argument('--power-data',type=Path,help='Validated aggregate-only Q15 JSON')
    parser.add_argument('--power-data-dir',type=Path,help='Directory of validated power-<patch>-<tier>.json aggregates')
    parser.add_argument('--movement-data',type=Path,help='Validated aggregate-only Q18 JSON')
    parser.add_argument('--outcome-data',type=Path,help='Validated aggregate-only ending-duration outcome JSON')
    parser.add_argument('--pro-reference-data',type=Path,help='Validated private pro-reference totals aggregate; separate from tier cohorts')
    parser.add_argument('--pro-cases-data',type=Path,help='Anonymous derived pro stage/location/signal reference cases')
    parser.add_argument('--opponent-rights-annotations',type=Path,help='Manual reviewed-claim and statistics-bound rights annotations; no automatic approval')
    parser.add_argument('--expert-claims-dir',type=Path,help='Validated local expert summaries; no raw videos or transcripts')
    for flag in ('body-bytes','observations','actions','scenarios','comparisons','pending-jobs'):
        parser.add_argument('--max-'+flag,type=int,required=True)
    args=parser.parse_args()
    if args.token_file.exists():token=args.token_file.read_text().strip()
    else:
        args.token_file.parent.mkdir(parents=True,exist_ok=True);token=secrets.token_urlsafe(32)
        fd=os.open(args.token_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream:stream.write(token+'\n')
    limits=Limits(args.max_body_bytes,args.max_observations,args.max_actions,args.max_scenarios,args.max_comparisons,args.max_pending_jobs)
    server=PregameWorkbench(args.db,token,limits,args.port)
    try:
        if args.power_data:
            from .power_stats import validate_power_dataset
            server.power_data=validate_power_dataset(json.loads(args.power_data.read_text()))
            if server.power_data['source']['sample_kind']=='SYNTHETIC':raise ValueError('Synthetic power data requires an isolated test fixture')
        power_directory=args.power_data_dir
        if power_directory is None and args.power_data is None and not server.test_mode and server.power_data is None and not server.power_datasets:
            # Only anonymous dated patch/tier snapshots. Explicit flags override.
            candidates=sorted((ROOT/'data/riot').glob('20??-??-??'),reverse=True)
            power_directory=next((p for p in candidates if p.is_dir() and any(p.glob('power-*-*.json*'))),None)
        if power_directory:
            from .power_stats import validate_power_dataset
            directory=power_directory
            if directory.is_symlink() or not directory.is_dir():raise ValueError('Invalid power dataset directory')
            paths=sorted([*directory.glob('power-*.json'),*directory.glob('power-*.json.gz')])
            if len(paths)>100:raise ValueError('Power dataset directory exceeds100 files')
            for path in paths:
                if path.is_symlink() or path.stat().st_size>64_000_000:raise ValueError('Invalid power aggregate file')
                data=validate_power_dataset(read_aggregate_file(path))
                if data['source']['sample_kind']!='REAL':raise ValueError('Synthetic power data requires an isolated test fixture')
                key=(data['source']['patch'],data['source']['tier'])
                if key in server.power_datasets and digest(server.power_datasets[key])!=digest(data):raise ValueError('Conflicting power datasets')
                server.power_datasets[key]=data
        if power_directory:
            from .collection_progress import validate_progress
            for key,data in server.power_datasets.items():
                patch,tier=key
                path=power_directory/('progress-'+str(patch)+'-'+tier+'.json')
                if not path.exists():path=path.with_suffix('.json.gz')
                if path.exists():
                    if path.is_symlink() or path.stat().st_size>1_000_000:raise ValueError('Invalid progress companion file')
                    server.power_progress[key]=validate_progress(read_aggregate_file(path,max_bytes=1_000_000),data)
        if args.movement_data:
            from .movement import validate_movement_dataset
            server.movement_statistics=validate_movement_dataset(json.loads(args.movement_data.read_text()))
            if server.movement_statistics['source']['sample_kind']=='SYNTHETIC':raise ValueError('Synthetic movement data requires an isolated test fixture')
        if args.outcome_data:
            from .outcome_stats import validate_outcome_dataset
            server.outcome_data=validate_outcome_dataset(json.loads(args.outcome_data.read_text()))
            if server.outcome_data['source']['sample_kind']=='SYNTHETIC':raise ValueError('Synthetic outcome data requires an isolated test fixture')
        if args.pro_reference_data:
            from .pro_reference import validate_pro_reference
            path=args.pro_reference_data
            if '..' in path.parts or path.is_symlink() or 'private' not in path.resolve().parts or path.stat().st_size>12_000_000:raise ValueError('Pro reference data must be bounded private local file')
            server.pro_reference_data=validate_pro_reference(json.loads(path.read_text()))
            if server.pro_reference_data['sample_kind']!='REAL':raise ValueError('Synthetic pro reference data requires an isolated test fixture')
            if server.pro_reference_data['roster_sha256']!=server.current_pro_roster_digest():raise ValueError('Pro reference roster version mismatch')
        cases_path=args.pro_cases_data or ROOT/'data/pro_reference/2026-10-13/reference-cases.json'
        if args.pro_cases_data or cases_path.exists():
            from .pro_reference_cases import validate_reference_cases
            if cases_path.is_symlink() or not cases_path.is_file() or cases_path.stat().st_size>12_000_000:raise ValueError('Invalid anonymous reference cases file')
            server.pro_cases_data=validate_reference_cases(json.loads(cases_path.read_text()))
            if server.pro_cases_data['sample_kind']!='REAL' or server.pro_cases_data['roster_sha256']!=server.current_pro_roster_digest():raise ValueError('Reference cases sample/roster mismatch')
        if args.opponent_rights_annotations:
            from .opponent_rights import validate_right_annotations
            path=args.opponent_rights_annotations
            if path.is_symlink() or not path.is_file() or path.stat().st_size>1_000_000:raise ValueError('Invalid rights annotation file')
            server.opponent_right_annotations=validate_right_annotations(json.loads(path.read_text()))
        expert_import=load_expert_directory(server,args.expert_claims_dir or ROOT/'data'/'expert_claims',explicit=args.expert_claims_dir is not None)
    except Exception:
        server.server_close();raise
    print(f'경기 전 준비: http://127.0.0.1:{server.server_port}/pregame',flush=True)
    print(f'기존 자료·지식 화면: http://127.0.0.1:{server.server_port}/ · 접속키 파일: {args.token_file}',flush=True)
    print('PRE_GAME 수동 진술·승인 지식 기반. 자동 수집·실제 경기 코칭 정확도 미검증.',flush=True)
    if expert_import['new_candidates']:print('새 전문가 후보 '+str(expert_import['new_candidates'])+'개',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()

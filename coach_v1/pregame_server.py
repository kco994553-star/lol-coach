"""Additive local PRE_GAME app; all legacy Workbench routes remain available."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
from urllib.parse import urlsplit

from .server import Workbench, Handler, Limits, ROOT
from .storage import ServiceError
from .pregame_contract import parse_input, parse_rule, proposal_rule, import_capture
from .pregame_store import PregameStore, plan_fields
from .knowledge import validate_knowledge_content, _records, _head
from .state import digest


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
    for name in ('executable-v1.json','executable-expanded-v1.json','initiative-v2.json'):
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
        except Exception:self.server_close();raise

    def validated_power_data(self):
        if self.power_data is None:return None
        from .power_stats import validate_power_dataset
        dataset=validate_power_dataset(self.power_data)
        if dataset['source']['sample_kind']=='SYNTHETIC' and not self.test_mode:return None
        return dataset

    def power_tiers(self):
        data=self.validated_power_data()
        return sorted({c['tier'] for c in data['cohorts']}) if data is not None else []


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
    data=server.validated_power_data()
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
        assets={'/pregame':('pregame.html','text/html; charset=utf-8'),'/pregame/':('pregame.html','text/html; charset=utf-8'),
            '/pregame.js':('pregame.js','text/javascript; charset=utf-8'),'/pregame.css':('pregame.css','text/css; charset=utf-8'),
            '/pregame_power.js':('pregame_power.js','text/javascript; charset=utf-8'),
            '/pregame-icon.svg':('pregame-icon.svg','image/svg+xml')}
        if self.command=='GET' and route in assets:
            filename,ctype=assets[route];file=ROOT/'web_r4'/filename
            if not file.exists():raise ServiceError(404,'PREGAME_UI_NOT_INSTALLED')
            return self.reply(200,file.read_bytes(),ctype)
        prefix='/dev/v1/pregame'
        if not route.startswith(prefix+'/'):return super().dispatch()
        self.authorize();pg=self.server.pregame;limit=self.server.limits.body_bytes
        if route==prefix+'/status' and self.command=='GET':
            return self.bounded_reply(200,dict(mode='PRE_GAME',automatic_collection='UNAVAILABLE',current_patch=None,
                knowledge_count=len(current_knowledge(self.server.research)),accuracy=None,
                test_mode=self.server.test_mode,power_tiers=self.server.power_tiers()))
        if route==prefix+'/power-view' and self.command=='POST':
            return self.bounded_reply(200,power_response(self.server,power_request(self.body())))
        if route==prefix+'/roster' and self.command=='GET':return self.bounded_reply(200,roster())
        if route==prefix+'/review-priority' and self.command=='GET':
            path=ROOT/'knowledge_candidates'/'q05-review-priority.json'
            return self.bounded_reply(200,json.loads(path.read_text())['recommended_review_order'] if path.exists() else [])
        if route==prefix+'/knowledge' and self.command=='GET':return self.bounded_reply(200,current_knowledge(self.server.research))
        if route==prefix+'/candidates':
            if self.command=='GET':return self.bounded_reply(200,candidate_specs())
            if self.command=='POST':
                b=self.body();self.fields(b,('spec',));spec=parse_rule(b['spec'])
                source=self.server.research.add('RAW_DIAGNOSTIC',spec.rule_id[:200],
                    dict(schema_version=spec.schema_version.replace('.rule.','.rule-source.'),spec=spec.model_dump(mode='json')))
                note=self.server.research.get_note(source['id'],'overview')
                if note['revision']==0:
                    note=self.server.research.put_note(source['id'],'overview',dict(known='AI 구조화 후보 명세 sha256:'+digest(spec.model_dump(mode='json')),
                        intention='경기 전 사용자 검토용; 출처 원문/패치/반례는 저장 자료 명세에 포함',alternative='',outcome='실제 코칭 성능 미검증'),0)
                proposal=self.server.research.propose(proposal_rule(spec),dict(resource_id=source['id'],anchor='overview',note_revision=note['revision']),max_bytes=limit)
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
    parser.add_argument('--movement-data',type=Path,help='Validated aggregate-only Q18 JSON')
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
        if args.movement_data:
            from .movement import validate_movement_dataset
            server.movement_statistics=validate_movement_dataset(json.loads(args.movement_data.read_text()))
            if server.movement_statistics['source']['sample_kind']=='SYNTHETIC':raise ValueError('Synthetic movement data requires an isolated test fixture')
    except Exception:
        server.server_close();raise
    print(f'경기 전 준비: http://127.0.0.1:{server.server_port}/pregame',flush=True)
    print(f'기존 자료·지식 화면: http://127.0.0.1:{server.server_port}/ · 접속키 파일: {args.token_file}',flush=True)
    print('PRE_GAME 수동 진술·승인 지식 기반. 자동 수집·실제 경기 코칭 정확도 미검증.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()

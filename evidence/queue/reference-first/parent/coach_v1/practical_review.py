"""Practical advice and read-only GitHub USER decision import.

Never writes, edits, or comments on a decision issue. Same-account isolation is
an operating rule in AGENTS.md, not a claim of cryptographic human detection.
"""
import copy
import hashlib
import json
from pathlib import Path
import re

from .knowledge import RULE_FIELDS, _GITHUB_REVIEW_AUTHORITY, _github_comment
from .pregame_contract import parse_rule, proposal_rule
from .state import digest
from .storage import ServiceError

ROOT = Path(__file__).resolve().parents[1]
BUDGET = 1_000_000


def advice_catalog():
    rows=json.loads((ROOT/'knowledge_candidates/practical-review-v1.json').read_text())
    for row in rows:
        row['spec']=parse_rule(row['spec']).model_dump(mode='json')
    return rows


def ensure_proposal(store,row):
    from .pregame_server import current_knowledge
    existing=[r['proposal'] for r in current_knowledge(store) if r['spec'] and r['spec']['rule_id']==row['id']]
    if len(existing)>1:raise ServiceError(409,'AMBIGUOUS_PRACTICAL_CANDIDATE')
    if existing:return existing[0]
    spec=row['spec']
    resource=store.add('RAW_DIAGNOSTIC',row['id'],dict(schema_version=spec['schema_version'].replace('.rule.','.rule-source.'),spec=spec))
    note=store.get_note(resource['id'],'overview')
    if not note['revision']:
        note=store.put_note(resource['id'],'overview',dict(known='기존 후보 '+row['original_candidate_id']+' / '+row['original_spec_sha256'],intention='사용자 검토용',alternative='',outcome='미승인'),0)
    # IDs differ from the preserved original proposal lineage.
    return store.propose(proposal_rule(spec),dict(resource_id=resource['id'],anchor='overview',note_revision=note['revision']),max_bytes=BUDGET)


def parse_commands(body,allowed):
    commands=[]
    for line in re.split(r'\n|\s+/\s+(?=승인|거절|수정)', body):
        line=line.strip()
        if not line:continue
        match=re.fullmatch(r'(승인|거절)\s+(KR-\d{3}(?:[\s,]+KR-\d{3})*)',line)
        if match:
            commands.extend((match[1],rid,None) for rid in re.findall(r'KR-\d{3}',match[2]))
            continue
        match=re.fullmatch(r'수정\s+(KR-\d{3})\s*:\s*(\S.*)',line)
        if match and len(match[2])<=2000:
            commands.append(('수정',match[1],match[2]));continue
        raise ValueError('승인 ID / 거절 ID / 수정 ID: 내용 형식만 가져옵니다.')
    ids=[c[1] for c in commands]
    if not commands or len(ids)!=len(set(ids)) or not set(ids)<=set(allowed):raise ValueError('중복 ID 또는 다른 묶음의 ID입니다.')
    return commands


def _audit(manifest,issue_number,comment):
    body=comment['body']
    value=dict(repository=manifest['repository'],issue_number=issue_number,comment_id=comment['id'],url=comment['html_url'],
               created_at=comment['created_at'],updated_at=comment['updated_at'],body=body,author=comment['user']['login'],
               body_sha256=hashlib.sha256(body.encode()).hexdigest())
    return _github_comment(value)


def _seen(store,audit):
    # Immutable raw comment resources also preserve revision-only decisions and
    # survive the ordinary research backup/restore alongside knowledge rows.
    for brief in store.list():
        if brief['kind']=='USER_GITHUB':
            old=store.get(brief['id'])['report']
            if old.get('url')==audit['url']:
                if old!=audit:raise ValueError('이미 가져온 댓글 원문이 바뀌었습니다. 새 댓글을 작성하세요.')
                return True
    return False


def import_comments(store,manifest,issue_number,comments):
    issues=[i for i in manifest['issues'] if i['number']==issue_number]
    if len(issues)!=1:raise ValueError('등록하지 않은 결정 이슈입니다.')
    allowed=issues[0]['candidate_versions'];catalog={r['id']:r for r in advice_catalog()}
    receipt=dict(applied=0,decisions=[],skipped=[])
    # GitHub ID gives stable order even for comments in the same second.
    for c in sorted(comments,key=lambda c:(c['created_at'],c['id'])):
        if c.get('user',{}).get('login')!=manifest['user_login']:continue
        start=len(receipt['decisions'])
        try:
            audit=_audit(manifest,issue_number,c)
            if _seen(store,audit):continue
            commands=parse_commands(c['body'],allowed)
            # Preflight every command before creating candidates or decisions.
            from .pregame_server import current_knowledge
            heads=current_knowledge(store)
            selected=[]
            for action,rid,text in commands:
                row=catalog[rid]
                if digest(row['spec'])!=allowed[rid]:raise ValueError('게시 후보 버전이 현재 자료와 다릅니다.')
                matches=[h for h in heads if h['spec'] and h['spec']['rule_id']==rid]
                if len(matches)>1:raise ValueError('동일 ID 후보가 여러 개입니다.')
                if matches:
                    h=matches[0]
                    # Scope or claim changed in PC must not be overwritten by
                    # approval of the frozen issue snapshot.
                    expected=proposal_rule(row['spec'])
                    if any(h['proposal'][k]!=expected[k] for k in RULE_FIELDS):raise ValueError('PC 또는 댓글에서 후보가 바뀌었습니다. 새 버전을 검토하세요.')
                selected.append((action,row,text,matches[0]['proposal']['version'] if matches else None))
            # Outer transaction spans resource receipts and all nested writes,
            # preventing a partial batch or crash from replaying a decision.
            with store.atomic():
                if _seen(store,audit):continue
                for action,row,text,preflight_version in selected:
                    p=ensure_proposal(store,row)
                    if preflight_version is not None and p['version']!=preflight_version:
                        raise ServiceError(409,'REVISION_CONFLICT')
                    expected=proposal_rule(row['spec'])
                    if any(p[k]!=expected[k] for k in RULE_FIELDS):
                        raise ServiceError(409,'REVISION_CONFLICT')
                    if action=='수정':
                        spec=copy.deepcopy(row['spec']);spec['output']['text']=text
                        spec['version']='user-revision-'+str(c['id'])
                        spec['limitations'].append('사용자 수정 원문: '+audit['url'])
                        # A new structured source binds the exact revised claim.
                        resource=store.add('RAW_DIAGNOSTIC',row['id']+' 사용자 수정',dict(schema_version=spec['schema_version'].replace('.rule.','.rule-source.'),spec=spec))
                        note=store.get_note(resource['id'],'overview')
                        if not note['revision']:note=store.put_note(resource['id'],'overview',dict(known=text,intention=audit['url'],alternative='',outcome='수정 후 재검토 필요'),0)
                        rule=proposal_rule(spec);rule['author']='USER_GITHUB'
                        saved=store.propose(rule,dict(resource_id=resource['id'],anchor='overview',note_revision=note['revision']),p['rule_id'],p['version'],max_bytes=BUDGET)
                    else:
                        saved=store.decide(p['rule_id'],p['version'],p['version'],'REVIEWED' if action=='승인' else 'REJECTED',p['patch_range'],p['applicability'],max_bytes=BUDGET,github_authority=_GITHUB_REVIEW_AUTHORITY,github_comment=audit)
                    receipt['decisions'].append(dict(id=row['id'],action=action,version=saved['version'],url=audit['url']))
                store.add('USER_GITHUB','사용자 결정 댓글',audit)
            receipt['applied']+=len(selected)
        except (ValueError,KeyError,TypeError,ServiceError) as error:
            del receipt['decisions'][start:]
            receipt['skipped'].append(dict(url=c.get('html_url'),reason=str(error)))
    return receipt


def issue_body(rows):
    lines=['사용자 검토 전 조언 후보입니다. 아래 글과 근거를 확인하고 **새 댓글**에 결정만 적어 주세요.',
           '','예: `승인 KR-001 KR-002` / `거절 KR-003` / `수정 KR-004: 바꿀 내용`',
           '','승인은 아래 적힌 전체 내용과 패치·조건에 대한 결정입니다. 수정은 새 미검토 버전으로 저장합니다. 수정한 후보는 PC에서 새 내용을 확인한 뒤 승인하세요.',
           '','Codex는 이 이슈와 댓글을 수정하거나 댓글을 쓰지 않습니다. 같은 계정의 사용자 결정은 이 규칙으로 구분합니다. 이미 쓴 댓글을 편집하면 가져오지 않으므로 정정은 새 댓글로 남겨 주세요.','']
    for row in rows:
        lines.extend(['## '+row['id'],'','기존 후보: `'+row['original_candidate_id']+'` · 원본 명세 해시: `'+row['original_spec_sha256']+'`',''])
        for k,v in row['advice'].items():lines.append('**'+k+'**: '+v+'\n')
        lines.append('공식 근거 링크:')
        for s in row['spec']['sources']:lines.append('- ['+s['title']+']('+s['url']+') · 확인 항목 `'+s['locator']+'`')
        lines.extend(['','Q15 통계는 자원 변화의 관측 자료입니다. 이 조언의 교전 승패·인과관계를 확인하지 않으므로 전술 수치 근거로 쓰지 않았습니다. 전문가 수동 요약 근거는 연결되지 않았습니다.',
                      '','게시 명세 해시: `'+digest(row['spec'])+'`',''])
    return '\n'.join(lines)


def sync_github(store,manifest=None):
    """GET-only gh API calls; no GitHub write capability is used."""
    import subprocess
    if manifest is None:
        manifest=json.loads((ROOT/'config/practical_review_issues.json').read_text())
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',manifest['repository']):raise ValueError('repository')
    fetched=[]
    for issue in manifest['issues']:
        number=issue['number']
        if type(number) is not int or number<1:raise ValueError('issue number')
        try:
            result=subprocess.run(['gh','api','--method','GET',f"repos/{manifest['repository']}/issues/{number}/comments?per_page=100",'--paginate'],capture_output=True,text=True,timeout=30,check=True)
            # gh before --slurp emits adjacent JSON arrays for pagination.
            # Decode each array without assuming one page or truncating >100.
            decoder=json.JSONDecoder();remaining=result.stdout.strip();comments=[]
            while remaining:
                page,end=decoder.raw_decode(remaining)
                if not isinstance(page,list):raise ValueError('comment page')
                comments.extend(page);remaining=remaining[end:].lstrip()
        except (OSError,subprocess.SubprocessError,ValueError):
            raise ServiceError(503,'GITHUB_REVIEW_READ_FAILED') from None
        fetched.append((number,comments))
    batches=[import_comments(store,manifest,number,comments) for number,comments in fetched]
    from .pregame_server import current_knowledge
    from .review_queue import _coverage
    knowledge=current_knowledge(store)
    return dict(actor_class='USER',applied=sum(b['applied'] for b in batches),batches=batches,
                example_card_filled=_coverage(knowledge),example_card_total=45,example_card_by_patch={'16.20':_coverage(knowledge,patch='16.20')})

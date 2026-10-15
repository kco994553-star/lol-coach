"""Deterministically author the NEW v2.3 packet from four existing pinned sources.

Does not refresh, rewrite, or revalidate the completed all-roster catalog.
Independent source and counter review are deliberately separate from authorship.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
VERSION='16.20.1'
folder=ROOT/f'data/official_catalog/versions/{VERSION}'
manifest=json.loads((folder/'manifest.json').read_bytes())
pinned={s['champion']:s for s in manifest['sources']}


def source(champion, locator):
    name=f'{champion}-{VERSION}.ko_KR.json'
    content=(folder/name).read_bytes()
    node=json.loads(content)
    full=f'data.{champion}.{locator}.description'
    for part in full.split('.'):
        node=node[int(part)] if isinstance(node,list) else node[part]
    # Specific reused source integrity, not a full catalog revalidation.
    assert hashlib.sha256(content).hexdigest()==pinned[champion]['sha256']
    return dict(url=pinned[champion]['url'],patch=VERSION,sha256=pinned[champion]['sha256'],
                path=f'data/official_catalog/versions/{VERSION}/{name}',locator=full,excerpt=node)


facts={
 'Yunara': dict(wave=('spells.0','주변 적에게 확산되는 기본 공격'),sustain=('spells.2','유체화·이동 속도 증가 및 초월 상태의 돌진'),finish=('spells.1','피해와 둔화를 주는 구슬 또는 빛줄기')),
 'Ashe': dict(wave=('spells.1','원뿔 모양으로 발사하는 화살'),sustain=('passive','공격 대상에게 적용되는 둔화'),finish=('spells.3','적 챔피언 적중 시 피해·기절, 주변 적 유닛 피해·둔화')),
 'Kaisa': dict(wave=('spells.0','근처 적을 추격하는 미사일 세례'),sustain=('spells.2','이동 속도와 공격 속도 증가, 살아있는 무기 조건의 투명 상태'),finish=('spells.3','적 챔피언 근처로 향하는 돌진')),
 'Caitlyn': dict(wave=('spells.0','관통 탄환과 다음 명중 대상에 대한 피해 감소'),sustain=('spells.2','그물 둔화와 자신을 뒤로 미는 반동'),finish=('spells.3','먼 거리 단일 대상 사격과 다른 적 챔피언의 탄환 차단')),
}
labels={'Yunara':'유나라','Ashe':'애쉬','Kaisa':'카이사','Caitlyn':'케이틀린'}
base_limitations=[
 '공식 설명은 기술의 기전만 제공하며 웨이브 처리 시간·저체력 생존·압박 유지율·킬 확률의 비교 표본은 아니다.',
 '스킬 레벨·아이템·마나·재사용 대기시간·거리·대상 수·상대 방해가 관측되지 않았다.',
 '이 파일은 새 미검토 후보 계보이며 기존 30개 자동 검토 패킷 및 USER 승인 이력을 바꾸지 않는다.',
 '경기 전 계획과 경기 후 검토 전용. 진행 중 게임의 자동 행동 지시로 사용하지 않는다.',
]
# User-requested scenario hypotheses, not observed game-state predicates or approvals.
RECALL_GOOD=[
 ('웨이브를 상대 포탑에 밀어 넣은 직후의 귀환 안을 검토한다.', '상대는 빠르게 정리하거나 다음 웨이브를 조절하고 먼저 움직일 수 있다.', '실제 포탑 도달·미니언 상태·상대 정리 속도가 확인되지 않으면 보류한다.'),
 ('목표 구매 골드에 도달했을 때의 귀환 안을 검토한다.', '상대는 구매 공백 동안 라인을 밀거나 체력·골드 우세를 유지할 수 있다.', '현재 골드·부품·할인·구매 가능 여부·동일 패치 가격이 불명하면 보류한다.'),
 ('오브젝트 생성 전에 준비할 여유가 있는 귀환 안을 검토한다.', '상대는 먼저 시야를 잡거나 합류를 막고 교전을 시작할 수 있다.', '실제 생성 시각·귀환 및 이동 시간·팀 계획이 불명하면 여유를 단정하지 않는다. 임의 시간 수치를 적용하지 않는다.'),
 ('아군 정글러의 귀환과 맞추는 귀환 안을 검토한다.', '상대 라인과 정글은 남아 있는 동안 라인·시야·오브젝트에 먼저 관여할 수 있다.', '아군 정글러의 실제 귀환·동선·팀 계획이 확인되지 않으면 보류한다.'),
]
RECALL_AVOID=[
 ('큰 웨이브가 우리 쪽으로 오는 동안의 귀환은 보류 후보로 검토한다.', '상대는 웨이브를 포탑에 넣거나 다이브를 준비하고 먼저 움직일 수 있다.', '웨이브 크기·위치·도착 시점·수비 가능성이 불명하면 손실을 확정하지 않는다.'),
 ('오브젝트 생성 직전의 귀환은 보류 후보로 검토한다.', '상대는 인원 우세를 이용해 먼저 자리를 잡거나 오브젝트를 시작할 수 있다.', '실제 생성 시각·왕복 시간·인원·팀 포기 계획이 불명하면 직전을 판정하지 않는다. 임의 시간 수치를 만들지 않는다.'),
 ('상대만 체력·골드 우세로 라인에 남는 상황의 귀환은 추가 검토한다.', '상대는 우세 자원으로 웨이브·포탑 압박 또는 다른 라인 개입을 시도할 수 있다.', '상대 체력·실제 구매력·잔류 위치·웨이브를 모르면 우세나 귀환 손해를 확정하지 않는다.'),
]
LOW_STAY=[
 ('웨이브가 상대 쪽으로 밀리는 동안 저체력 잔류 안을 검토한다.', '상대는 웨이브를 멈추거나 긴 추격 구간을 이용해 접근·다이브를 시도할 수 있다.', '웨이브 방향·위치·이동 수단·상대 사거리를 모르면 안전 잔류를 판정하지 않는다.'),
 ('상대 정글러가 반대편에 실제로 보이거나 관련 시야가 있을 때 잔류 안을 검토한다.', '상대 정글러는 관측 후 이동할 수 있고 다른 적이 접근할 수 있다.', '관측 시각·정확한 위치·접근 경로·시야 유효성이 불명하면 정글 안전을 단정하지 않는다.'),
 ('상대의 궁극기·점멸·순간 피해 등 킬 수단이 없다고 확인된 때 잔류 안을 검토한다.', '상대는 다른 스킬·사거리·아군 합류로 여전히 처치를 시도할 수 있다.', '궁극기·점멸·피해·자원·대기시간을 실제 확인하지 못하면 킬 수단 부재로 판정하지 않는다.'),
 ('다른 곳에 곧 오브젝트 교전이 있어 상대 라이너를 묶을 가치를 검토할 때 잔류 안을 비교한다.', '상대는 라인을 버리고 합류하거나 잔류자를 먼저 압박할 수 있다.', '실제 교전 계획·오브젝트 시각·합류 경로·라인 압박 효과가 불명하면 묶는 가치를 단정하지 않는다.'),
]
LOW_RECALL=[
 ('상대 정글러 위치가 불명일 때 잔류를 보류하고 귀환 안을 검토한다.', '상대 정글러는 접근·귀환 중단·다이브를 시도할 수 있다.', '안전한 귀환 위치·경로·상대 접근을 확인하지 못하면 귀환 안전도 UNKNOWN이다.'),
 ('웨이브가 우리 쪽으로 올 때 잔류를 보류하고 귀환 안을 검토한다.', '상대는 웨이브를 포탑에 넣거나 다이브·다른 라인 관여를 시도할 수 있다.', '웨이브 규모·도착 시점·아군 수비를 모르면 귀환의 손익을 확정하지 않는다.'),
 ('상대 킬 압박이 확인될 때 잔류를 보류하고 귀환 안을 검토한다.', '상대는 사거리·돌진·군중 제어로 추격하거나 귀환을 끊을 수 있다.', '피해·사거리·대기시간·시야가 불명하면 킬 압박과 귀환 안전을 확정하지 않는다.'),
 ('곧 큰 교전이 없는 것으로 확인될 때 귀환 안을 검토한다.', '상대는 예상하지 못한 교전·오브젝트·라인 압박을 만들 수 있다.', '실제 팀 계획과 맵 상황이 불명하면 큰 교전 부재로 판정하지 않는다.'),
 ('핵심 아이템 구매 골드가 있을 때 귀환 안을 검토한다.', '상대는 구매 공백에 라인·포탑·다른 라인 관여 기회를 얻을 수 있다.', '보유 부품·할인·골드·동일 패치 가격·아이템 필요성이 불명하면 핵심 구매 이득을 확정하지 않는다.'),
]


def macro(entries, intended_choice):
    return [dict(text=text,status='HYPOTHESIS',source_support='UNKNOWN',
                 scenario_origin='USER_REQUESTED_NOT_OBSERVED',intended_choice=intended_choice,
                 **{'상대 권리':right,'무효 조건':invalid}) for text,right,invalid in entries]


rows=[]
for champ, data in facts.items():
    name=labels[champ]
    for dimension,key,label in [('wave_clear_speed','wave','웨이브 처리 속도'),('low_health_sustain','sustain','저체력 유지력'),('opponent_finishing','finish','상대 마무리 능력')]:
        loc,mechanic=data[key]
        s=source(champ,loc)
        status='UNKNOWN' if key=='sustain' else 'HYPOTHESIS'
        interpretation={
            'wave':f'공식 기전({mechanic})이 복수 대상 처리에 관련될 수 있다는 가설만 둔다. 빠름·느림의 등급은 UNKNOWN이다.',
            'sustain':f'이동기·사거리·원거리 웨이브 처리로 저체력 상태에서도 생존과 라인 압박을 유지할 가능성을 검토한다. 공식 기전({mechanic})과 웨이브 관련 기술을 근거 후보로 두되 실제 사거리 수치·상대 사거리·시야·자원·대기시간이 없어 잔류 안전성과 압박 수준은 UNKNOWN이다.',
            'finish':f'공식 기전({mechanic})이 상대를 마무리하는 상황에 관련될 수 있다는 가설만 둔다. 높은 마무리 성능·처형 판정·확정 킬은 UNKNOWN이다.',
        }[key]
        counter={
            'wave':'미니언 수·배치·체력과 스킬 자원이 달라지면 동일 기전이어도 처리 시간이 달라진다. 복수 대상 기전은 빠른 처리의 증명이 아니다.',
            'sustain':'이동·둔화·원거리 웨이브 처리 수단이 있어도 상대 사거리·돌진·다이브·시야 및 자신의 자원·대기시간에 따라 생존과 압박이 끊길 수 있다. 유지력의 검토 대상은 체력 재생량이 아니라 저체력에서의 생존·압박 가능성이다.',
            'finish':'돌진·사거리·기절·피해는 처형이 아니다. 방어·회복·차단·거리·대기시간 때문에 상대가 생존할 수 있다.',
        }[key]
        rows.append(dict(id=f'RV23-CLASS-{champ}-{dimension}',champion=champ,kind='CLASSIFICATION',dimension=dimension,
            value=None,status=status,review_status='HOLD',tactical_verification='UNKNOWN',conditions=[],
            advice={'상황':f'{name}의 {label}를 경기 전 검토할 때',
                    '할 것':interpretation,'하지 말 것':'스킬 설명만으로 빠름·높음·안전함 등 전투 성능 등급을 확정하지 않는다.',
                    '상대 권리':'상대의 스킬·위치·방어·회복 및 아군 개입은 별도로 확인해야 하며 현재 UNKNOWN이다.',
                    '무효 조건':'실제 패치 불일치 또는 필요한 스킬·대상·자원·상대 사거리·시야 정보가 없으면 적용 판단을 보류한다.',
                    '근거':f'공식 원문: {s["excerpt"]} 해석: {interpretation}',
                    '패치':f'공식 한국어 정적 자료 {VERSION}; 경기 패치 16.20 범위. 실제 패치가 다르면 보류.'},
            sources=([s,source(champ,data['wave'][0])] if key=='sustain' else [s]),hold_reasons=['독립 근거 검사 및 반론 검사 전 작성 후보이다.','공식 기술 설명은 전투 성능 등급을 검증하지 않는다.'],
            counterarguments=[counter],limitations=base_limitations))
    for section,key in [('RECALL','wave'),('LOW_HEALTH','finish')]:
        loc,mechanic=data[key]
        own=source(champ,loc)
        sources=[own,source(champ,data['sustain'][0])]
        if section=='RECALL':
            situation=f'{name}의 첫 구매 묶음·귀환 분포를 경기 전 계획 또는 경기 후 기록에서 검토하는 때'
            do='웨이브를 처리한 뒤 귀환하는 안을 검토 후보로 남기되, 실제 웨이브 상태·귀환 안전·구매 자원·상대 위치가 확인되기 전에는 좋은 귀환이라고 판정하지 않는다.'
            dont='광역 또는 관통 기술이 있다는 이유만으로 지금 밀고 귀환하면 이득이라고 단정하지 않는다.'
            good=macro(RECALL_GOOD,'RECALL_REVIEW')
            avoid=macro(RECALL_AVOID,'DEFER_RECALL_REVIEW')
        else:
            situation=f'{name}의 저체력 잔류와 구매 관측을 경기 전 계획 또는 경기 후 기록에서 비교하는 때'
            do='저체력에서 귀환하는 안과 잔류하는 안을 모두 검토 후보로 둔다. 이동기·사거리·원거리 웨이브 처리 수단과 상대 사거리·시야·자원·귀환 중단 가능성이 확인되지 않으면 선택을 보류한다.'
            dont='체력 비율만으로 반드시 귀환 또는 반드시 잔류라고 지시하지 않는다. 이동·사거리·웨이브 처리 기술만으로 안전 잔류 또는 확정 마무리를 보장하지 않는다.'
            good=macro(LOW_STAY,'STAY_REVIEW')
            avoid=macro(LOW_RECALL,'RECALL_REVIEW')
        rows.append(dict(id=f'RV23-ADVICE-{champ}-{section}',champion=champ,kind='ADVICE',section=section,value=None,
            status='HYPOTHESIS',review_status='HOLD',tactical_verification='UNKNOWN',conditions=[],
            macro_conditions=dict(good=good,avoid=avoid),
            advice={'상황':situation,'할 것':do,'하지 말 것':dont,
                    '상대 권리':'상대는 라인 잔류·귀환·추격·다른 라인 개입을 선택할 수 있다. 현재 원문은 그 선택의 성공이나 필연성을 보장하지 않는다.',
                    '무효 조건':'실제 패치가 다르거나 웨이브·이동기·사거리·상대 위치·시야·자원·대기시간을 확인할 수 없으면 행동 적용은 HOLD/UNKNOWN이다.',
                    '근거':f'공식 기술 원문: {own["excerpt"]} 이 원문은 {mechanic}를 설명한다. 귀환 시점·밀고 귀환의 이득·저체력 잔류의 안전·상대 로밍의 인과는 직접 설명하지 않으므로 위 행동 제안은 미검증 가설이다.',
                    '패치':f'공식 자료 {VERSION}; 경기 패치 16.20 범위의 새 검토 후보. 다른 패치에 자동 적용하지 않는다.'},
            sources=sources,hold_reasons=['공식 원문에 귀환/웨이브/저체력 매크로 행동의 좋고 나쁨을 직접 뒷받침하는 문장이 없다.',
                '게임별 웨이브·의도·귀환 시작 시점이 UNKNOWN이며 관측 집계는 비인과적이다.',
                '독립 근거 검사·반론 검사 및 별도 전술 검증을 통과하지 않았다.'],
            counterarguments=['귀환은 안전을 늘려도 상대에게 라인·다른 라인 관여 기회를 줄 수 있고, 잔류는 압박을 유지해도 사망 위험이 커질 수 있다. 방향과 크기는 현재 자료에서 UNKNOWN이다.',
                '구매 시각은 귀환 완료의 대리 관측이며, 분포의 최빈값과 중앙값은 최적 행동이 아니다.'],limitations=base_limitations))
packet=dict(schema_version='recall-candidates.v1',version='queue-v23-2026-10-15',source_patch=VERSION,
            author='Codex candidate author',review_state='PENDING_INDEPENDENT_SOURCE_AND_COUNTER_REVIEW',
            source_scope='Four pinned existing Korean champion archives only; completed all-roster evidence reused.',
            automatic_activation=False,user_approval_count=0,rows=rows)
(ROOT/'knowledge_candidates/recall-v23.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
print(f'Authored {len(rows)} candidates: 12 classifications, 8 advice; all HOLD, 0 verified tactics.')

"""Strict additive pregame contracts. Prose is never an executable condition."""
from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .state import digest

Position = Literal['TOP','JUNGLE','MID','BOTTOM','SUPPORT']
POSITIONS = ('TOP','JUNGLE','MID','BOTTOM','SUPPORT')
PROFILE_FIELDS = ('threats','protection','strong_when','lane_style','jungle_style')
FIELD = re.compile(r'(patch|my\.(position|champion)|(ally|enemy)\.((TOP|JUNGLE|MID|BOTTOM|SUPPORT)\.(champion|position|runes|summoners|threats|protection|strong_when|lane_style|jungle_style)|(threats|protection|lane_style|jungle_style)))\Z')


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


def timestamp(value):
    if value is not None and (not isinstance(value,str) or datetime.fromisoformat(value).utcoffset() is None):
        raise ValueError('timezone required')
    return value


class Provenance(Strict):
    kind: Literal['MANUAL','AUTOMATIC','UNKNOWN']
    reference: str | None = Field(max_length=2000)
    observed_at: str | None
    verification: Literal['UNVERIFIED','SOURCE_VERIFIED','UNKNOWN']
    _time = field_validator('observed_at')(timestamp)

    @model_validator(mode='after')
    def check(self):
        if self.kind=='MANUAL' and self.verification=='SOURCE_VERIFIED':raise ValueError('manual unverified')
        if self.kind=='AUTOMATIC' and not self.reference:raise ValueError('automatic source required')
        return self


class Selection(Strict):
    status: Literal['FULL','PARTIAL','UNKNOWN']
    values: list[str] = Field(max_length=32)
    source: Provenance

    @model_validator(mode='after')
    def check(self):
        if bool(self.values)!=(self.status!='UNKNOWN') or any(not v.strip() or len(v)>100 for v in self.values):
            raise ValueError('selection completeness declaration')
        if len(set(self.values))!=len(self.values):raise ValueError('duplicate selections')
        return self


class Slot(Strict):
    side: Literal['ALLY','ENEMY']
    slot: int = Field(ge=1,le=5)
    champion: str | None = Field(max_length=100)
    position: Position | None
    position_candidates: list[Position] = Field(max_length=5)
    uncertainty: str = Field(min_length=1,max_length=2000)
    champion_source: Provenance
    position_source: Provenance
    runes: Selection
    summoners: Selection

    @model_validator(mode='after')
    def check(self):
        if self.position and self.position_candidates:raise ValueError('ambiguous role cannot be confirmed')
        if len(set(self.position_candidates))!=len(self.position_candidates):raise ValueError('duplicate candidates')
        if self.champion is not None and not self.champion.strip():raise ValueError('blank champion')
        return self


class InputDraft(Strict):
    title: str = Field(min_length=1,max_length=200)
    patch: str | None = Field(max_length=100)
    phase: Literal['PRE_GAME','UNKNOWN']
    observed_at: str | None
    my_position: Position | None
    my_champion: str | None = Field(max_length=100)
    my_slot: int | None = Field(ge=1,le=5)
    slots: list[Slot] = Field(min_length=10,max_length=10)
    source: Provenance
    original_capture: dict | None
    _time = field_validator('observed_at')(timestamp)

    @model_validator(mode='after')
    def check(self):
        if not self.title.strip() or self.patch is not None and not self.patch.strip():raise ValueError('blank input')
        keys={(s.side,s.slot) for s in self.slots}
        if keys!={(side,i) for side in ('ALLY','ENEMY') for i in range(1,6)}:raise ValueError('ten unique slots')
        for side in ('ALLY','ENEMY'):
            roles=[s.position for s in self.slots if s.side==side and s.position]
            if len(set(roles))!=len(roles):raise ValueError('duplicate definite positions')
        own=next((s for s in self.slots if s.side=='ALLY' and s.slot==self.my_slot),None)
        if own:
            if self.my_champion and own.champion and self.my_champion!=own.champion:raise ValueError('self champion conflict')
            if self.my_position and own.position and self.my_position!=own.position:raise ValueError('self position conflict')
        role=next((s for s in self.slots if s.side=='ALLY' and s.position==self.my_position),None)
        if role and self.my_champion and role.champion and self.my_champion!=role.champion:raise ValueError('selected role champion conflict')
        return self


class Source(Strict):
    url: str = Field(min_length=9,max_length=2000)
    title: str = Field(min_length=1,max_length=500)
    locator: str = Field(min_length=1,max_length=2000)
    patch: str | None = Field(max_length=100)
    sha256: str | None
    kind: Literal['OFFICIAL','DATA_DRAGON','PATCH_NOTES','REFERENCE','SYNTHETIC']

    @model_validator(mode='after')
    def check(self):
        from urllib.parse import urlsplit
        url=urlsplit(self.url)
        if url.scheme!='https' or not url.netloc or url.username or url.password:raise ValueError('public https source')
        if self.sha256 is not None and not re.fullmatch('[a-f0-9]{64}',self.sha256):raise ValueError('source hash')
        return self


class Predicate(Strict):
    field: str
    op: Literal['EQ','HAS','INTERSECTS']
    value: str | list[str]

    @model_validator(mode='after')
    def check(self):
        if not FIELD.fullmatch(self.field):raise ValueError('unsupported field')
        if self.op in ('EQ','HAS') and not isinstance(self.value,str):raise ValueError('scalar predicate')
        if self.op=='INTERSECTS' and (not isinstance(self.value,list) or not self.value):raise ValueError('set predicate')
        return self


class ChampionProfile(Strict):
    champion: str = Field(min_length=1,max_length=100)
    roles: list[Position]
    threats: list[Literal['ASSASSINATION','DIVE','GRAB_PICK','POKE','NONE']]
    protection: list[Literal['PEEL','FRONTLINE','NONE']]
    strong_when: list[Literal['EARLY','MID','LATE']]
    lane_style: list[Literal['PRESSURE','SCALING','ROAM','SPLIT']]
    jungle_style: list[Literal['EARLY_GANK','SCALING']]


class RuleOutput(Strict):
    section: Literal['PROFILE','MAP','JUNGLE','COMPOSITION','ROLE','LANE','FIGHT','CHANGES']
    target: Literal['GLOBAL','SELF','ALLY','ENEMY','TOP','JUNGLE','MID','BOTTOM','SUPPORT']
    outlook: Literal['FAVORABLE','UNFAVORABLE','CONTESTED','UNKNOWN'] | None
    text: str = Field(min_length=1,max_length=2000)
    alternatives: list[str]
    change_conditions: list[str]


class BaseCooldown(Strict):
    status: Literal['CONFIRMED','CONFLICTING','UNKNOWN']
    values: list[float] = Field(max_length=20)
    patch: str | None
    sources: list[Source]

    @model_validator(mode='after')
    def check(self):
        import math
        if any(not math.isfinite(v) or v<0 for v in self.values):raise ValueError('base values')
        if self.status=='CONFIRMED' and (not self.values or not self.patch or len({s.url for s in self.sources})<2
            or not any(s.kind not in ('DATA_DRAGON','SYNTHETIC') for s in self.sources)):
            raise ValueError('cross-confirmed cooldown sources required')
        return self


class HasteCondition(Strict):
    haste: float | None = Field(ge=0,allow_inf_nan=False)
    source: Source | None
    kind: Literal['ABILITY','SUMMONER']


class Cooldown(Strict):
    name: str = Field(min_length=1,max_length=100)
    side: Literal['ALLY','ENEMY']
    position: Position
    category: Literal['NORMAL','CHARGE','RESET_REFUND','STACK','TRANSFORM','UNKNOWN']
    spell_kind: Literal['ABILITY','SUMMONER']
    base: BaseCooldown
    conditional: HasteCondition
    remaining: Literal['NOT_AVAILABLE']
    linked_condition: str = Field(min_length=1,max_length=2000)


class RuleSpec(Strict):
    schema_version: Literal['pregame.rule.v1']
    rule_id: str = Field(pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$')
    version: str = Field(min_length=1,max_length=100)
    scope: Literal['COMMON','POSITION']
    positions: list[Position]
    patches: list[str] = Field(max_length=100)
    sources: list[Source] = Field(min_length=1,max_length=32)
    required_fields: list[str] = Field(max_length=100)
    conditions: list[Predicate] = Field(max_length=100)
    counterconditions: list[Predicate] = Field(max_length=100)
    stop_conditions: list[Predicate] = Field(max_length=100)
    counterexamples: list[str] = Field(min_length=1,max_length=20)
    limitations: list[str] = Field(min_length=1,max_length=20)
    output: RuleOutput
    profile: ChampionProfile | None
    cooldowns: list[Cooldown] = Field(max_length=30)

    @model_validator(mode='after')
    def check(self):
        if any(not FIELD.fullmatch(f) for f in self.required_fields):raise ValueError('unsupported required field')
        fields=[*self.required_fields,*[p.field for p in self.conditions+self.counterconditions+self.stop_conditions]]
        if any(not p.strip() or p.upper()=='UNKNOWN' or p=='미확인' for p in self.patches):raise ValueError('exact patches or empty')
        if self.scope=='COMMON':
            if self.positions or any(f.startswith('my.') for f in fields) or self.output.section in ('ROLE','LANE','FIGHT'):
                raise ValueError('common scope depends on personal position')
        elif not self.positions or self.output.section in ('PROFILE','MAP','JUNGLE','COMPOSITION'):
            raise ValueError('position scope')
        if self.profile and (self.scope!='COMMON' or self.output.section!='PROFILE' or self.output.target!='GLOBAL'):
            raise ValueError('profile scope')
        if self.output.section=='PROFILE' and not self.profile:raise ValueError('profile required')
        if any(not v.strip() or len(v)>2000 for v in self.counterexamples+self.limitations+self.output.alternatives+self.output.change_conditions):
            raise ValueError('bounded claim text')
        return self


def parse_input(value):
    if isinstance(value,dict) and value.get('schema_version')=='pregame.input-draft.v2':
        from .pregame_v2 import InputDraftV2
        return InputDraftV2.model_validate(value)
    return InputDraft.model_validate(value)
def parse_rule(value):
    if isinstance(value,dict) and value.get('schema_version')=='pregame.rule.v2':
        from .pregame_v2 import RuleSpecV2
        return RuleSpecV2.model_validate(value)
    return RuleSpec.model_validate(value)


def proposal_rule(spec):
    spec=parse_rule(spec) if isinstance(spec,dict) else spec
    return dict(patch_range=','.join(spec.patches) or 'UNKNOWN',
        applicability=dict(champion='TYPE_BASED',role='ALL' if spec.scope=='COMMON' else ','.join(spec.positions),
            matchup='STRUCTURED_CONDITIONS',level='PRE_GAME_CONDITIONAL',context='PRE_GAME'),
        required_fields=[('EXECUTABLE_V2_SHA256:' if spec.schema_version=='pregame.rule.v2' else 'EXECUTABLE_V1_SHA256:')+digest(spec.model_dump(mode='json')),*spec.required_fields],
        claim=spec.output.text,mechanism='구조화 명세와 원본 출처를 확인하세요. 조건은 자유문에서 해석하지 않습니다.',
        counterexamples=spec.counterexamples,limitations=spec.limitations,author='AI_EXPLORATORY')


def binding_matches(proposal,spec):
    expected=proposal_rule(spec)
    return all(proposal.get(k)==expected[k] for k in ('claim','patch_range','applicability','required_fields','counterexamples','limitations'))


def import_capture(record):
    """Normalize existing slots while preserving the complete immutable original."""
    from .draft import _capture
    cap=_capture(record['capture'])
    source=dict(kind='MANUAL',reference=cap['source']['description'],observed_at=cap['observed_at'],verification='UNVERIFIED')
    picks={(r['side'],r['slot']):r['champion'] for r in cap['visible_picks']}
    roles={(r['side'],r['slot']):r for r in cap['role_assignments']}
    slots=[]
    for side in ('ALLY','ENEMY'):
        for i in range(1,6):
            role=roles.get((side,i),{})
            slots.append(dict(side=side,slot=i,champion=picks.get((side,i)),position=role.get('role'),position_candidates=[],
                uncertainty=role.get('uncertainty','UNKNOWN'),champion_source=source,position_source=source,
                runes=dict(status='UNKNOWN',values=[],source=source),summoners=dict(status='UNKNOWN',values=[],source=source)))
    return parse_input(dict(title=cap['title'],patch=cap['patch'],phase='PRE_GAME' if cap['phase']=='PRE_GAME' else 'UNKNOWN',observed_at=cap['observed_at'],
        my_position=None,my_champion=None,my_slot=None,slots=slots,source=source,original_capture=record)).model_dump(mode='json')

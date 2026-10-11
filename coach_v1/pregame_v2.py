"""Additive reviewed PRE_GAME planning. No observed/live state or prose evaluator."""
from copy import deepcopy
import re
from typing import Literal
from pydantic import Field,model_validator
from .pregame_contract import (Strict,Position,POSITIONS,FIELD,InputDraft,ChampionProfile,
                               Predicate,RuleOutput,RuleSpec,PROFILE_FIELDS)

INITIATIVES=('INITIATOR','FOLLOW_UP','SELF_SUFFICIENT','PROTECTOR')
NEEDS=('ALLY_INITIATION','ALLY_CC','ALLY_PEEL')
FIELD_V2=re.compile(r'(?:'+FIELD.pattern.removesuffix(r'\Z')+r'|(ally|enemy)\.(?:(TOP|JUNGLE|MID|BOTTOM|SUPPORT)\.)?(initiative|needs)|my\.(initiative|needs))\Z')


def _text(value):
    if not value.strip() or len(value)>2000:raise ValueError('bounded original text required')
    # Conservative known abusive formulations, never rewrite an approved quote.
    if any(t in value.lower().replace(' ','') for t in ('정글차이','서폿차이','팀원탓','못하네','쓰레기','왜안하','너때문','junglediff','supportdiff')):
        raise ValueError('blame language not allowed')
    return value


class VisibleSignal(Strict):
    field:Literal['ALLY_MINIMAP','WAVE','SELF_HEALTH','SELF_RESOURCE','GAME_TIME']
    text:str=Field(min_length=1,max_length=2000)
    @model_validator(mode='after')
    def check(self):_text(self.text);return self


class PlanGuard(Strict):
    preconditions:list[VisibleSignal]=Field(min_length=1,max_length=10)
    invalidation_signals:list[VisibleSignal]=Field(min_length=1,max_length=10)
    alternative:str=Field(min_length=1,max_length=2000)
    @model_validator(mode='after')
    def check(self):_text(self.alternative);return self


class ChampionProfileV2(ChampionProfile):
    initiative:list[Literal['INITIATOR','FOLLOW_UP','SELF_SUFFICIENT','PROTECTOR']]=Field(max_length=4)
    needs:list[Literal['ALLY_INITIATION','ALLY_CC','ALLY_PEEL']]=Field(max_length=3)
    necessary_conditions:list[str]=Field(max_length=30)
    @model_validator(mode='after')
    def check(self):
        for s in self.necessary_conditions:_text(s)
        if len(set(self.initiative))!=len(self.initiative) or len(set(self.needs))!=len(self.needs):raise ValueError('duplicate profile classification')
        return self


class PredicateV2(Predicate):
    @model_validator(mode='after')
    def check(self):
        if not FIELD_V2.fullmatch(self.field):raise ValueError('unsupported field')
        if self.op in ('EQ','HAS') and not isinstance(self.value,str):raise ValueError('scalar predicate')
        if self.op=='INTERSECTS' and (not isinstance(self.value,list) or not self.value):raise ValueError('set predicate')
        if self.field.endswith('.initiative'):
            values=self.value if isinstance(self.value,list) else [self.value]
            if any(v not in INITIATIVES for v in values):raise ValueError('initiative enum')
        if self.field.endswith('.needs'):
            values=self.value if isinstance(self.value,list) else [self.value]
            if any(v not in NEEDS for v in values):raise ValueError('dependency enum')
        return self


class TeamDependency(Strict):
    position:Position
    required_play:str
    @model_validator(mode='after')
    def check(self):_text(self.required_play);return self


class MinimumPlay(Strict):
    position:Position
    plays:list[str]=Field(min_length=1,max_length=2)
    @model_validator(mode='after')
    def check(self):
        for p in self.plays:_text(p)
        return self


class PickCandidate(Strict):
    champion:str=Field(min_length=1,max_length=100)
    reason:str
    @model_validator(mode='after')
    def check(self):_text(self.champion);_text(self.reason);return self


class OperationsOutput(Strict):
    opening_allies:list[Position]=Field(max_length=5)
    pressure_allies:list[Position]=Field(max_length=5)
    win_condition_allies:list[Position]=Field(max_length=5)
    dependencies:list[TeamDependency]=Field(max_length=5)
    minimum_plays:list[MinimumPlay]=Field(max_length=5)
    request_templates:list[str]=Field(max_length=5)
    solo_alternative:str
    pick_candidates:list[PickCandidate]=Field(max_length=10)
    @model_validator(mode='after')
    def check(self):
        _text(self.solo_alternative)
        for p in self.request_templates:_text(p)
        for fields in ('opening_allies','pressure_allies','win_condition_allies'):
            values=getattr(self,fields)
            if len(set(values))!=len(values):raise ValueError('duplicate operating ally')
        if len({m.position for m in self.minimum_plays})!=len(self.minimum_plays):raise ValueError('duplicate minimum play position')
        return self


class RuleOutputV2(RuleOutput):
    section:Literal['PROFILE','MAP','JUNGLE','COMPOSITION','ROLE','LANE','FIGHT','CHANGES','OPERATIONS']
    operations:OperationsOutput|None
    @model_validator(mode='after')
    def check(self):
        _text(self.text)
        if (self.section=='OPERATIONS')!=(self.operations is not None):raise ValueError('operating output section')
        return self


class RuleSpecV2(RuleSpec):
    schema_version:Literal['pregame.rule.v2']
    profile:ChampionProfileV2|None
    output:RuleOutputV2
    conditions:list[PredicateV2]=Field(max_length=100)
    counterconditions:list[PredicateV2]=Field(max_length=100)
    stop_conditions:list[PredicateV2]=Field(max_length=100)
    plan_guard:PlanGuard|None
    @model_validator(mode='after')
    def check(self):
        if any(not FIELD_V2.fullmatch(f) for f in self.required_fields):raise ValueError('unsupported required field')
        fields=[*self.required_fields,*[p.field for p in self.conditions+self.counterconditions+self.stop_conditions]]
        if any(not p.strip() or p.upper()=='UNKNOWN' or p=='미확인' for p in self.patches):raise ValueError('exact patches or empty')
        if self.scope=='COMMON':
            if self.positions or any(f.startswith('my.') for f in fields) or self.output.section in ('ROLE','LANE','FIGHT','OPERATIONS'):
                raise ValueError('common depends on personal position')
        elif not self.positions or self.output.section in ('PROFILE','MAP','JUNGLE','COMPOSITION'):raise ValueError('position scope')
        if self.profile and (self.scope!='COMMON' or self.output.section!='PROFILE' or self.output.target!='GLOBAL'):raise ValueError('profile scope')
        if self.output.section=='PROFILE' and not self.profile:raise ValueError('profile required')
        if (self.output.section=='PROFILE')!=(self.plan_guard is None):raise ValueError('nonprofile requires visible guard')
        for t in self.counterexamples+self.limitations+self.output.alternatives+self.output.change_conditions:_text(t)
        return self


class InputDraftV2(InputDraft):
    schema_version:Literal['pregame.input-draft.v2']
    my_pick_state:Literal['UNPICKED','PICKED','UNKNOWN']
    frequent_champions:list[str]=Field(max_length=30)
    @model_validator(mode='after')
    def check_pick(self):
        if self.my_pick_state=='UNPICKED':
            own=next((s for s in self.slots if s.side=='ALLY' and (s.slot==self.my_slot or s.position==self.my_position)),None)
            if self.my_champion is not None or own and own.champion is not None:raise ValueError('unpicked requires no selected champion')
        if self.my_pick_state=='PICKED' and self.my_champion is None:raise ValueError('picked requires selected champion')
        if len(set(self.frequent_champions))!=len(self.frequent_champions):raise ValueError('duplicate preferences')
        for c in self.frequent_champions:
            if not c.strip() or len(c)>100:raise ValueError('bounded champion preference')
        return self


def _profiles_for_summary(traces):
    from .pregame_evaluator import _profiles
    eligible=[]
    for trace in traces:
        if trace.get('spec',{} ) and trace['spec']['profile'] and trace['condition']=='TRUE' and trace['status'] in ('APPLIED','CONFLICTING'):
            t=deepcopy(trace);t['status']='APPLIED';eligible.append(t)
    return _profiles(eligible)


def _team_summary(draft,profiles,conflicts):
    allies=[];missing=[]
    for position in POSITIONS:
        slot=next((s for s in draft['slots'] if s['side']=='ALLY' and s['position']==position),None)
        champion=slot['champion'] if slot else None
        profile=profiles.get(champion,{})
        if not champion or not profile.get('initiative'):missing.append(position)
        allies.append(dict(position=position,champion=champion,initiative=profile.get('initiative',[]),needs=profile.get('needs',[])))
    own=profiles.get(draft['my_champion'],{})
    if not own.get('initiative'):missing.append('SELF')
    relevant=[reason for reason,_ in conflicts if reason.endswith('.initiative') or reason.endswith('.needs')]
    relevant=[reason for reason in relevant if any(a['champion'] and (':'+a['champion']+'.') in reason for a in allies)]
    count=sum('INITIATOR' in a['initiative'] for a in allies) if not missing and not relevant else None
    risk=None
    if count is not None:
        risk=('NO_INITIATOR' if count==0 else 'SINGLE_INITIATOR' if count==1 else 'NONE') if 'FOLLOW_UP' in own['initiative'] else 'NONE'
    return dict(status='CONFLICTING' if relevant else 'UNKNOWN' if missing else 'KNOWN',dependency_risk=risk,
                initiator_count=count,allies=allies,reasons=relevant+['INITIATIVE_UNKNOWN:'+p for p in missing])


def evaluate_gameplan_v2(input,knowledge):
    from .pregame_evaluator import evaluate_gameplan,_cell
    result=evaluate_gameplan(input,knowledge);result['schema_version']='pregame.plan.v2'
    operations=_cell('OPERATIONS','운영 중심·팀 의존도')
    eligible=[t for t in result['evaluations'] if t['output'] and t['output']['section']=='OPERATIONS']
    applied=[deepcopy(t) for t in eligible if t['status']=='APPLIED']
    if applied:
        outlooks={t['output']['outlook'] for t in applied if t['output']['outlook'] not in (None,'UNKNOWN')}
        # Distinct operating templates for one target cannot silently pick an opener.
        templates={str(t['output']['operations']) for t in applied}
        conflict=len(outlooks)>1 or len(templates)>1
        operations.update(status='CONFLICTING' if conflict else 'KNOWN',rules=applied,
            texts=list(dict.fromkeys(t['output']['text'] for t in applied)),
            reasons=['OPERATING_OUTPUT_CONFLICT'] if conflict else [],outlook=next(iter(outlooks)) if len(outlooks)==1 and not conflict else None)
        if conflict:
            for t in operations['rules']:t['status']='CONFLICTING';t['reasons'].append('OPERATING_OUTPUT_CONFLICT')
            for t in eligible:
                if t['status']=='APPLIED':t['status']='CONFLICTING';t['reasons'].append('OPERATING_OUTPUT_CONFLICT')
    else:operations['reasons']=sorted(set(operations['reasons']+[r for t in eligible for r in t['reasons']]))
    profiles,conflicts=_profiles_for_summary(result['evaluations'])
    result['operations']=operations;result['team_dependencies']=_team_summary(result['input'],profiles,conflicts)
    warnings=[];draft=result['input']
    # Explicitly unpicked own slot is not missing allied initiative. All other
    # allied roles must be fully classified before a shortage can be asserted.
    other_allies=[a for a in result['team_dependencies']['allies'] if a['position']!=draft.get('my_position')]
    shortage=(len(other_allies)==4 and all(a['champion'] and a['initiative'] for a in other_allies)
              and not any(':initiative' in reason or '.initiative' in reason for reason,_ in conflicts)
              and sum('INITIATOR' in a['initiative'] for a in other_allies)<=1)
    if operations['status']=='KNOWN' and draft.get('my_pick_state')=='UNPICKED' and shortage:
        for t in applied:
            for c in t['output']['operations']['pick_candidates']:
                profile=profiles.get(c['champion'],{})
                if c['champion'] in draft.get('frequent_champions',[]) and set(profile.get('initiative',[]))&{'INITIATOR','SELF_SUFFICIENT'}:
                    warnings.append(dict(c,rule_id=t['rule_id'],version=t['version'],spec_sha256=t['spec_sha256'],sources=t['sources']))
    result['pick_warnings']=warnings
    return result

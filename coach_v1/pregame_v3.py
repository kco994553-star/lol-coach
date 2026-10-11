"""Additive conditional Q18 plans; no live state or phase inference."""
import re
from typing import Literal
from pydantic import Field,model_validator
from .pregame_contract import Strict,Position
from .pregame_v2 import RuleSpecV2,RuleOutputV2,_text,evaluate_gameplan_v2
from .state import digest


class StageCondition(Strict):
    field:Literal['LANING_ACTIVE','FIRST_TURRET_DESTROYED','MAJOR_OBJECTIVE_CONTEST','LONG_RESPAWN_RISK']
    value:bool


class StatisticsRef(Strict):
    dataset_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    cohort_id:str=Field(min_length=1,max_length=200)


class StageRole(Strict):
    stage:Literal['EARLY','MID','LATE']
    layer:Literal['DEFAULT','TYPE','CHAMPION','COMPOSITION']
    subject:Literal['SELF','ALLY','ENEMY']
    position:Position
    location:Literal['HOME_LANE','JUNGLE','MAIN_GROUP','SIDE_LANE','OBJECTIVE_AREA']
    role:str
    why:str
    exceptions:list[str]=Field(min_length=1,max_length=20)
    stage_conditions:list[StageCondition]=Field(min_length=1,max_length=4)
    overrides:list[str]=Field(max_length=30)
    statistics_ref:StatisticsRef|None
    @model_validator(mode='after')
    def check(self):
        for t in [self.role,self.why,*self.exceptions]:_text(t)
        if len({c.field for c in self.stage_conditions})!=len(self.stage_conditions):raise ValueError('duplicate stage condition')
        values={c.field:c.value for c in self.stage_conditions}
        if self.stage=='EARLY' and values.get('LANING_ACTIVE') is not True:raise ValueError('early requires explicit laning')
        if self.stage=='MID' and not (values.get('FIRST_TURRET_DESTROYED') is True or values.get('MAJOR_OBJECTIVE_CONTEST') is True):raise ValueError('mid requires explicit transition')
        if self.stage=='LATE' and values.get('LONG_RESPAWN_RISK') is not True:raise ValueError('late requires explicit respawn risk')
        if len(set(self.overrides))!=len(self.overrides) or any(not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}',r) for r in self.overrides):raise ValueError('override rule id')
        return self


class RuleOutputV3(RuleOutputV2):
    section:Literal['PROFILE','MAP','JUNGLE','COMPOSITION','ROLE','LANE','FIGHT','CHANGES','OPERATIONS','MOVEMENT']
    movement:list[StageRole]=Field(max_length=30)
    @model_validator(mode='after')
    def check(self):
        _text(self.text)
        if (self.section=='OPERATIONS')!=(self.operations is not None):raise ValueError('operating section')
        if (self.section=='MOVEMENT')!=bool(self.movement):raise ValueError('movement section')
        return self


class RuleSpecV3(RuleSpecV2):
    schema_version:Literal['pregame.rule.v3']
    output:RuleOutputV3
    @model_validator(mode='after')
    def movement_scope(self):
        if self.output.section=='MOVEMENT' and self.scope!='POSITION':raise ValueError('movement personal scope')
        return self


def movement_fingerprint(statistics=None,test_mode=False):
    if statistics is None:return None
    from .movement import validate_movement_dataset
    verified=validate_movement_dataset(statistics)
    if verified['source']['sample_kind']=='SYNTHETIC' and not test_mode:return None
    return digest(verified)


def evaluate_gameplan_v3(input,knowledge,movement_statistics=None,test_mode=False):
    from .pregame_evaluator import _cell
    result=evaluate_gameplan_v2(input,knowledge)
    fingerprint=movement_fingerprint(movement_statistics,test_mode)
    if fingerprint is None:
        # Unsupported synthetic statistics are identical to absent statistics.
        # No module-dependent interpretation or source inventing for empty input.
        movement=_cell('MOVEMENT','단계별 기본 움직임')
        candidates=[t for t in result['evaluations'] if t.get('output') and t['output']['section']=='MOVEMENT']
        movement['rules']=candidates
        movement['reasons']=sorted(set(movement['reasons']+['MOVEMENT_STATISTICS_UNAVAILABLE']))
        for t in candidates:
            if t['status']=='APPLIED':
                t['status']='UNKNOWN';t['reasons'].append('MOVEMENT_STATISTICS_UNAVAILABLE')
    else:
        from .movement import build_movement_plan
        movement=build_movement_plan(result['evaluations'],result['input'],movement_statistics,test_mode)
    result.update(schema_version='pregame.plan.v3',movement=movement,movement_statistics_fingerprint=fingerprint)
    return result

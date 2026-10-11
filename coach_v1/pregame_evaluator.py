"""Pure PRE_GAME evaluation. Only exact, current reviewed bindings supply text.

The caller validates immutable source documents through KnowledgeStore. This
module neither creates approvals nor interprets prose or live gameplay state.
"""
from collections import defaultdict
from copy import deepcopy

from .pregame_contract import (InputDraft, POSITIONS, PROFILE_FIELDS,
                               binding_matches, parse_input, parse_rule)
from .state import canonical, digest


def knowledge_fingerprint(knowledge):
    """Order-independent digest including unbound and rejected current reports."""
    records=[]
    for item in knowledge:
        spec=item.get('spec')
        if hasattr(spec,'model_dump'):
            spec=spec.model_dump(mode='json')
        records.append(dict(proposal=item['proposal'],spec_sha256=digest(spec) if spec is not None else None))
    return digest(sorted(records,key=canonical))


def _and(values):
    return 'FALSE' if 'FALSE' in values else 'UNKNOWN' if 'UNKNOWN' in values else 'TRUE'


def _or(values):
    return 'TRUE' if 'TRUE' in values else 'UNKNOWN' if 'UNKNOWN' in values else 'FALSE'


class _Facts:
    def __init__(self, draft, profiles):
        self.draft=draft
        self.slots={(s['side'].lower(),s['position']):s for s in draft['slots'] if s['position']}
        self.profiles=profiles

    def get(self, field):
        """Return (declared values, complete). Partial positive membership is known."""
        if field=='patch':return self.draft['patch'],self.draft['patch'] is not None
        if field.startswith('my.'):
            value=self.draft['my_'+field.split('.')[1]]
            return value,value is not None
        parts=field.split('.')
        if len(parts)==2:
            values=[];complete=True
            for position in POSITIONS:
                value,known=self.get(parts[0]+'.'+position+'.'+parts[1])
                values.extend(value or []);complete=complete and known
            return sorted(set(values)),complete
        side,position,name=parts
        slot=self.slots.get((side,position))
        if slot is None:return None,False
        if name in ('champion','position'):
            value=slot[name];return value,value is not None
        if name in ('runes','summoners'):
            selection=slot[name]
            return selection['values'],selection['status']=='FULL'
        value=self.profiles.get(slot['champion'],{}).get(name)
        return value,value is not None

    def predicate(self, predicate):
        value,complete=self.get(predicate['field'])
        op=predicate['op'];expected=predicate['value']
        if value is None:return 'UNKNOWN'
        if op=='EQ':
            if isinstance(value,str) and value==expected:return 'TRUE'
            return 'FALSE' if complete else 'UNKNOWN'
        if not isinstance(value,list):return 'FALSE' if complete else 'UNKNOWN'
        match=expected in value if op=='HAS' else bool(set(value)&set(expected))
        return 'TRUE' if match else 'FALSE' if complete else 'UNKNOWN'


def _current_flags(knowledge):
    """Defend against accidentally passing a full PR10 history to the evaluator."""
    groups=defaultdict(list)
    for i,item in enumerate(knowledge):groups[item['proposal'].get('rule_id')].append(i)
    flags=[True]*len(knowledge)
    for indices in groups.values():
        superseded={knowledge[i]['proposal'].get('supersedes') for i in indices}
        heads=[i for i in indices if knowledge[i]['proposal'].get('version') not in superseded
               and knowledge[i]['proposal'].get('current') is not False]
        for i in indices:flags[i]=len(heads)==1 and i in heads
    return flags


def _trace(item, current):
    proposal=deepcopy(item['proposal']);raw=item.get('spec')
    spec=parse_rule(raw).model_dump(mode='json') if raw is not None else None
    trace=dict(rule_id=spec['rule_id'] if spec else proposal.get('rule_id'),
        version=proposal.get('version'),spec_version=spec['version'] if spec else None,
        spec_sha256=digest(spec) if spec else None,review_state=proposal.get('review_state'),
        condition='UNKNOWN',status='UNKNOWN',reasons=[],missing_fields=[],
        sources=deepcopy(spec['sources']) if spec else [],
        conditions=[dict(predicate=deepcopy(p),condition='UNKNOWN') for p in spec['conditions']] if spec else [],
        counterconditions=[dict(predicate=deepcopy(p),condition='UNKNOWN') for p in spec['counterconditions']] if spec else [],
        stop_conditions=[dict(predicate=deepcopy(p),condition='UNKNOWN') for p in spec['stop_conditions']] if spec else [],
        output=deepcopy(spec['output']) if spec else None,proposal=proposal,spec=spec,cooldowns=[])
    if not current:trace['reasons'].append('NOT_CURRENT_PROPOSAL')
    if proposal.get('review_state')!='REVIEWED':trace['reasons'].append('NOT_REVIEWED')
    if spec is None:trace['reasons'].append('UNBOUND_SPEC')
    elif not binding_matches(proposal,spec):trace['reasons'].append('APPROVAL_BINDING_MISMATCH')
    return trace


def _evaluate(trace, facts):
    result=deepcopy(trace)
    spec=result['spec']
    if facts.draft['phase']!='PRE_GAME':
        result['reasons'].append('PHASE_NOT_CONFIRMED')
        return result
    if result['reasons'] or spec is None:return result
    values=[];reasons=[]
    patch=facts.draft['patch']
    if not spec['patches']:
        values.append('UNKNOWN');reasons.append('RULE_PATCH_UNKNOWN')
    elif patch is None:
        values.append('UNKNOWN');reasons.append('PATCH_UNKNOWN')
    elif patch not in spec['patches']:
        values.append('FALSE');reasons.append('PATCH_MISMATCH')
    if spec['scope']=='POSITION':
        if facts.draft['my_position'] is None:
            values.append('UNKNOWN');reasons.append('MY_POSITION_UNKNOWN')
        elif facts.draft['my_position'] not in spec['positions']:
            values.append('FALSE');reasons.append('POSITION_SCOPE_MISMATCH')
    if spec['profile'] and not any(s['champion']==spec['profile']['champion'] for s in facts.draft['slots']):
        values.append('FALSE');reasons.append('PROFILE_CHAMPION_NOT_PRESENT')
    missing=[field for field in spec['required_fields'] if not facts.get(field)[1]]
    if missing:values.append('UNKNOWN');reasons.append('REQUIRED_FIELDS_UNKNOWN')
    result['missing_fields']=missing
    for key in ('conditions','counterconditions','stop_conditions'):
        result[key]=[dict(predicate=deepcopy(p),condition=facts.predicate(p)) for p in spec[key]]
        for predicate in result[key]:
            if predicate['condition']=='UNKNOWN' and predicate['predicate']['field'] not in missing:
                missing.append(predicate['predicate']['field'])
    condition=_and([p['condition'] for p in result['conditions']])
    values.append(condition)
    if condition!='TRUE':reasons.append('CONDITIONS_'+condition)
    for key in ('counterconditions','stop_conditions'):
        excluded=_or([p['condition'] for p in result[key]])
        if excluded=='TRUE':values.append('FALSE');reasons.append(key.upper()+'_MATCHED')
        elif excluded=='UNKNOWN':values.append('UNKNOWN');reasons.append(key.upper()+'_UNKNOWN')
    result['condition']=_and(values)
    result['status']={'TRUE':'APPLIED','FALSE':'EXCLUDED','UNKNOWN':'UNKNOWN'}[result['condition']]
    result['reasons']=reasons
    return result


def _profiles(traces):
    claims=defaultdict(lambda:defaultdict(list))
    for trace in traces:
        spec=trace['spec']
        if trace['status']=='APPLIED' and spec['profile']:
            profile=spec['profile']
            for field in PROFILE_FIELDS:
                if profile[field]:claims[profile['champion']][field].append((sorted(set(profile[field])),trace))
    profiles={};conflicts=[]
    for champion,fields in claims.items():
        profiles[champion]={}
        for field,entries in fields.items():
            if len({canonical(value) for value,_ in entries})>1:
                reason='PROFILE_FIELD_CONFLICT:'+champion+'.'+field
                conflicts.append((reason,[trace for _,trace in entries]))
            else:profiles[champion][field]=entries[0][0]
    return profiles,conflicts


def _priority(cooldown, draft):
    position=draft['my_position']
    if position is None:return False
    # An applicable personal rule is the approved link to allied synergy.
    if cooldown['side']=='ALLY':return True
    if cooldown['position']==position:return True
    if position in ('BOTTOM','SUPPORT') and cooldown['position'] in ('BOTTOM','SUPPORT'):return True
    if position=='JUNGLE':return True
    return False


def _cooldown(cooldown, draft):
    c=deepcopy(cooldown);base=c['base'];conditional=c['conditional'];patch=draft['patch'];reasons=[]
    if base['status']!='CONFIRMED':reasons.append('BASE_'+base['status'])
    if c['category']=='UNKNOWN':reasons.append('CATEGORY_UNKNOWN')
    if patch is None or base['patch']!=patch:reasons.append('COOLDOWN_PATCH_UNCONFIRMED')
    if any(s['patch']!=patch for s in base['sources']):reasons.append('COOLDOWN_SOURCE_PATCH_MISMATCH')
    if (not base['values'] or len({s['url'] for s in base['sources']})<2
        or not any(s['kind'] not in ('DATA_DRAGON','SYNTHETIC') for s in base['sources'])):
        reasons.append('COOLDOWN_SOURCES_UNCONFIRMED')
    values=base['values'] if not reasons else []
    labels={'NORMAL':'가속 0 기준 상한값','CHARGE':'재충전 시간·가속 0 기준 상한값',
            'RESET_REFUND':'RESET_REFUND·조건부 가속 0 기준 상한값',
            'STACK':'STACK·조건부 가속 0 기준 상한값','TRANSFORM':'TRANSFORM·조건부 가속 0 기준 상한값',
            'UNKNOWN':'미확인'}
    calculation=[];conditional_reasons=[]
    if conditional['haste'] is None or conditional['source'] is None:conditional_reasons.append('HASTE_SOURCE_UNKNOWN')
    elif conditional['kind']!=c['spell_kind']:conditional_reasons.append('HASTE_KIND_MISMATCH')
    elif conditional['source']['patch']!=patch:conditional_reasons.append('HASTE_SOURCE_PATCH_MISMATCH')
    elif values:calculation=[value*100/(100+conditional['haste']) for value in values]
    return dict(name=c['name'],side=c['side'],position=c['position'],category=c['category'],spell_kind=c['spell_kind'],
        status='KNOWN' if values else 'UNKNOWN',label=labels[c['category']],base_values=deepcopy(values),
        conditional_values=calculation,conditional_label='계산/조건부',conditional=conditional,
        sources=base['sources'],base=base,linked_condition=c['linked_condition'],remaining='NOT_AVAILABLE',
        priority=_priority(c,draft),reasons=reasons,conditional_reasons=conditional_reasons)


def _cell(key,title):
    return dict(key=key,title=title,status='UNKNOWN',texts=[],reasons=['NO_APPLICABLE_REVIEWED_RULE'],rules=[],outlook=None,cooldowns=[])


def _cooldown_conflicts(bases, draft):
    """Audit static claims independently of the selected role and plan guards.

    A claim can block inconsistent numeric displays without applying its rule.
    Only current, exactly bound REVIEWED claims with this explicit patch and
    confirmed numeric sources participate. Variant identity is not in v1, so
    ambiguous variants are conservatively withheld rather than conflated.
    """
    groups=defaultdict(set)
    for trace in bases:
        spec=trace['spec']
        if trace['reasons'] or spec is None or draft['patch'] not in spec['patches']:continue
        for raw in spec['cooldowns']:
            cooldown=_cooldown(raw,draft)
            if cooldown['status']=='KNOWN':
                key=(cooldown['side'],cooldown['position'],cooldown['name'],cooldown['spell_kind'])
                groups[key].add(canonical((cooldown['base_values'],cooldown['category'])))
    return {key for key,values in groups.items() if len(values)>1}


def evaluate_gameplan(input, knowledge):
    """Evaluate declared facts without modifying inputs or archived reports."""
    draft=(input if isinstance(input,InputDraft) else parse_input(input)).model_dump(mode='json')
    knowledge=deepcopy(knowledge)
    bases=[_trace(item,current) for item,current in zip(knowledge,_current_flags(knowledge))]
    # Ground profiles from declared facts, then resolve type dependencies to a
    # fixed point. Cyclic or oscillating derivations remain conservatively unknown.
    profiles={};seen=set();profile_bases=[t for t in bases if t['spec'] and t['spec']['profile']]
    unresolved=False
    for _ in range(len(profile_bases)+2):
        signature=digest(profiles)
        if signature in seen:unresolved=True;profiles={};break
        seen.add(signature)
        evaluated=[_evaluate(t,_Facts(draft,profiles)) for t in profile_bases]
        derived,_=_profiles(evaluated)
        if derived==profiles:break
        profiles=derived
    else:unresolved=True;profiles={}
    facts=_Facts(draft,profiles)
    traces=[_evaluate(t,facts) for t in bases]
    _,profile_conflicts=_profiles(traces)
    for reason,contributors in profile_conflicts:
        for trace in contributors:
            trace['reasons'].append(reason)
            # This profile may still supply its undisputed fields.
            trace['status']='CONFLICTING'
    if unresolved:
        for trace in traces:
            if trace['spec'] and trace['spec']['profile']:trace['reasons'].append('PROFILE_DEPENDENCY_UNRESOLVED')
    common=dict(map=[_cell(position, '원딜' if position=='BOTTOM' else position) for position in POSITIONS],
                jungle=_cell('JUNGLE','정글'),composition=_cell('COMPOSITION','조합'))
    position=draft['my_position']
    position_label={'TOP':'탑','JUNGLE':'정글','MID':'미드','BOTTOM':'원딜','SUPPORT':'서포터'}.get(position,'포지션 미확인')
    personal=dict(role=_cell('ROLE',position_label+' · 내 역할'),
                  lane=_cell('LANE',position_label+' · 라인/동선'),
                  fight=_cell('FIGHT',position_label+' · 교전/생존'))
    changes=_cell('CHANGES','변경/미확인')
    for trace in traces:
        if trace['status']=='APPLIED' and trace['output']['section']!='PROFILE':
            trace['cooldowns']=[_cooldown(c,draft) for c in trace['spec']['cooldowns']]
            if trace['spec']['scope']=='COMMON':
                for cooldown in trace['cooldowns']:cooldown['priority']=False
    conflicts=_cooldown_conflicts(bases,draft)
    for trace in traces:
        for cooldown in trace['cooldowns']:
            key=(cooldown['side'],cooldown['position'],cooldown['name'],cooldown['spell_kind'])
            if cooldown['status']=='KNOWN' and key in conflicts:
                cooldown.update(status='UNKNOWN',base_values=[],conditional_values=[])
                cooldown['reasons'].append('COOLDOWN_VALUE_CONFLICT')
    def cells_for(output):
        section=output['section']
        if section=='MAP':return [c for c in common['map'] if output['target'] not in POSITIONS or c['key']==output['target']]
        if section in ('JUNGLE','COMPOSITION'):return [common[section.lower()]]
        if section in ('ROLE','LANE','FIGHT'):return [personal[section.lower()]]
        return [changes] if section=='CHANGES' else []
    cell_trace_origins={}
    for trace in traces:
        if trace['output'] is None:continue
        for cell in cells_for(trace['output']):
            if trace['status'] in ('APPLIED','CONFLICTING'):
                # A GLOBAL rule can conflict in one row while remaining
                # applicable in another; per-cell copies preserve that boundary.
                local_trace=deepcopy(trace)
                cell['rules'].append(local_trace)
                cell_trace_origins[id(local_trace)]=trace
            else:
                cell['reasons'].extend(trace['reasons'])
    for cell in [*common['map'],common['jungle'],common['composition'],*personal.values(),changes]:
        entries=cell['rules']
        if entries:
            outlooks={t['output']['outlook'] for t in entries if t['output']['outlook'] not in (None,'UNKNOWN')}
            if len(outlooks)>1:
                for local_trace in entries:
                    local_trace['status']='CONFLICTING'
                    local_trace['reasons'].append('OUTPUT_OUTLOOK_CONFLICT')
                    local_trace['cooldowns']=[]
                    origin=cell_trace_origins[id(local_trace)]
                    origin['status']='CONFLICTING';origin['cooldowns']=[]
                    for reason in ('OUTPUT_OUTLOOK_CONFLICT','OUTPUT_OUTLOOK_CONFLICT_CELL:'+cell['key']):
                        if reason not in origin['reasons']:origin['reasons'].append(reason)
            cell['status']='CONFLICTING' if any(t['status']=='CONFLICTING' for t in entries) else 'KNOWN'
            cell['texts']=list(dict.fromkeys(t['output']['text'] for t in entries))
            cell['reasons']=sorted({reason for t in entries for reason in t['reasons']})
            cell['outlook']=next(iter(outlooks)) if len(outlooks)==1 and cell['status']=='KNOWN' else None
            cell['cooldowns']=[c for t in entries for c in t['cooldowns'] if c['priority']]
        else:
            if cell['key'] in ('ROLE','LANE','FIGHT'):
                cell['reasons'].append('NO_REVIEWED_POSITION_RULE:'+(position or 'UNKNOWN'))
            cell['reasons']=sorted(set(cell['reasons']))
    return dict(schema_version='pregame.plan.v1',mode='PRE_GAME',input=draft,common=common,personal=personal,
        changes=changes,evaluations=traces,knowledge_fingerprint=knowledge_fingerprint(knowledge),
        coaching_accuracy=None,real_match_validation='NOT_EVALUATED')

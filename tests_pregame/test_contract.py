import copy
import importlib.util
import unittest


def manual():
    return dict(kind='MANUAL', reference='사용자 픽창 진술', observed_at=None, verification='UNVERIFIED')


def golden(position='BOTTOM', patch=None):
    teams = [['Ornn','Sejuani','Ahri','Caitlyn','Lux'], ['Fiora','LeeSin','Zed','Ezreal','Nautilus']]
    positions=['TOP','JUNGLE','MID','BOTTOM','SUPPORT']
    slots=[]
    for side,champions in zip(['ALLY','ENEMY'],teams):
        for i,(champion,role) in enumerate(zip(champions,positions),1):
            slots.append(dict(side=side,slot=i,champion=champion,position=role,position_candidates=[],
                uncertainty='수동 지정; 실제 클라이언트 미검증',champion_source=manual(),position_source=manual(),
                runes=dict(status='UNKNOWN',values=[],source=manual()),
                summoners=dict(status='UNKNOWN',values=[],source=manual())))
    return dict(title='Golden 픽창',patch=patch,phase='PRE_GAME',observed_at=None,
        my_position=position,my_champion=teams[0][positions.index(position)] if position else None,
        my_slot=positions.index(position)+1 if position else None,slots=slots,source=manual(),original_capture=None)


def rule(section='ROLE',position='BOTTOM'):
    common=section in ['PROFILE','MAP','JUNGLE','COMPOSITION','CHANGES']
    return dict(schema_version='pregame.rule.v1',rule_id='test-rule',version='1',scope='COMMON' if common else 'POSITION',
        positions=[] if common else [position],patches=['SYNTHETIC-1'],
        sources=[dict(url='https://example.org/synthetic',title='SYNTHETIC fixture',locator='test only',patch='SYNTHETIC-1',sha256=None,kind='SYNTHETIC')],
        required_fields=[],conditions=[],counterconditions=[],stop_conditions=[],counterexamples=['합성 테스트 전용'],limitations=['실제 코칭 지식 아님'],
        output=dict(section=section,target='TOP' if section=='MAP' else 'GLOBAL' if common else 'SELF',outlook=None,text='합성 승인 문장',alternatives=[],change_conditions=[]),profile=None,cooldowns=[])


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.pregame_contract'), 'strict pregame contract missing')
        from coach_v1 import pregame_contract as c
        self.c=c

    def test_golden_all_positions_and_unknown_patch(self):
        for position in ['TOP','JUNGLE','MID','BOTTOM','SUPPORT']:
            self.assertEqual(self.c.parse_input(golden(position)).my_position,position)
        self.assertIsNone(self.c.parse_input(golden()).patch)

    def test_duplicate_missing_or_live_data_rejected(self):
        for mutate in [lambda d:d['slots'].pop(),lambda d:d['slots'].__setitem__(1,d['slots'][0]),lambda d:d.update(enemy_cooldown_remaining=3)]:
            d=golden();mutate(d)
            with self.assertRaises(ValueError):self.c.parse_input(d)

    def test_ambiguous_roles_retained_self_conflict_rejected(self):
        d=golden(None);d['slots'][0].update(position=None,position_candidates=['TOP','MID'])
        self.assertEqual(self.c.parse_input(d).slots[0].position_candidates,['TOP','MID'])
        d=golden();d['my_champion']='Ashe'
        with self.assertRaises(ValueError):self.c.parse_input(d)

    def test_partial_runes_and_unknown_values(self):
        d=golden();d['slots'][0]['runes'].update(status='PARTIAL',values=['keystone:1'])
        self.assertEqual(self.c.parse_input(d).slots[0].runes.status,'PARTIAL')
        d['slots'][0]['runes']['status']='UNKNOWN'
        with self.assertRaises(ValueError):self.c.parse_input(d)

    def test_manual_provenance_never_verified(self):
        d=golden();d['source']['verification']='SOURCE_VERIFIED'
        with self.assertRaises(ValueError):self.c.parse_input(d)

    def test_import_does_not_confirm_missing_phase(self):
        record=dict(capture=dict(title='original',phase=None,patch=None,observed_at=None,
            visible_picks=[],visible_bans=[],role_assignments=[],source=dict(author='manual',perspective='UNKNOWN',description='unknown')))
        self.assertEqual(self.c.import_capture(record)['phase'],'UNKNOWN')

    def test_common_cannot_depend_on_me_and_prose_is_not_predicate(self):
        for pred in [dict(field='my.position',op='EQ',value='BOTTOM'),'아군이면 진입']:
            d=rule('COMPOSITION');d['conditions']=[pred]
            with self.assertRaises(ValueError):self.c.parse_rule(d)

    def test_exact_approval_binding_and_no_prose_inference(self):
        spec=self.c.parse_rule(rule());p=self.c.proposal_rule(spec)
        proposal=dict(p,review_state='REVIEWED')
        self.assertTrue(self.c.binding_matches(proposal,spec))
        proposal['patch_range']='any patch'
        self.assertFalse(self.c.binding_matches(proposal,spec))

    def test_cooldown_dd_alone_cannot_confirm(self):
        d=rule();d['cooldowns']=[dict(name='Q',side='ENEMY',position='BOTTOM',category='NORMAL',spell_kind='ABILITY',
            base=dict(status='CONFIRMED',values=[10],patch='SYNTHETIC-1',sources=d['sources']),
            conditional=dict(haste=None,source=None,kind='ABILITY'),remaining='NOT_AVAILABLE',linked_condition='조건부 테스트')]
        with self.assertRaises(ValueError):self.c.parse_rule(d)


if __name__=='__main__':unittest.main()

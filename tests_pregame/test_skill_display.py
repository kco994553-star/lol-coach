"""Display semantics, official provenance and non-mutation, not coaching accuracy."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]

def js(code):
    p=subprocess.run(['node','-e',"const S=require('./web_r4/skill-display.js');\n"+code],cwd=ROOT,capture_output=True,text=True)
    if p.returncode:raise AssertionError(p.stderr)
    return json.loads(p.stdout)

class SkillDisplayTests(unittest.TestCase):
    def test_five_caitlyn_slots_and_explicit_owners(self):
        actual=js("console.log(JSON.stringify(['P','Q','W','E','R'].map(s=>S.label('Caitlyn',s))))")
        self.assertEqual(actual,['케이틀린의 헤드샷(P)','케이틀린의 필트오버 피스메이커(Q)','케이틀린의 요들잡이 덫(W)','케이틀린의 90구경 투망(E)','케이틀린의 비장의 한 발(R)'])

    def test_multiple_champions_same_key_and_group(self):
        actual=js("console.log(JSON.stringify(S.format('럭스 Q 뒤 케이틀린 W, 노틸러스 Q와 럭스 W/E',{champions:['Caitlyn','Lux','Nautilus']})))")
        for name in ('럭스의 빛의 속박(Q)','케이틀린의 요들잡이 덫(W)','노틸러스의 닻줄 견인(Q)','럭스의 프리즘 보호막(W)','럭스의 광휘의 특이점(E)'):
            self.assertIn(name,actual)

    def test_existing_key_is_idempotent(self):
        actual=js("const a=S.format('럭스의 빛의 속박(Q), 케이틀린 요들잡이 덫(W)',{champions:['Lux','Caitlyn']});console.log(JSON.stringify([a,S.format(a,{champions:['Lux','Caitlyn']})]))")
        self.assertEqual(actual[0],actual[1]);self.assertNotIn('(Q)(Q)',actual[0]);self.assertNotIn('의 럭스의',actual[0])

    def test_real_duplicate_name_needs_owner(self):
        actual=js("console.log(JSON.stringify([S.format('동상',{champions:['Anivia','Braum']}),S.format('브라움의 동상',{champions:['Anivia','Braum']}),S.label('Anivia','E')]))")
        self.assertEqual(actual[0],'동상');self.assertEqual(actual[1],'브라움의 동상(Q)');self.assertEqual(actual[2],'애니비아의 동상(E)')

    def test_bare_key_not_defaulted_to_own(self):
        actual=js("console.log(JSON.stringify(S.format('E가 없으면 Q를 보류, official:Lux:Q',{own:'Caitlyn',champions:['Caitlyn','Lux']})))")
        self.assertEqual(actual,'E가 없으면 Q를 보류, official:Lux:Q')

    def test_generic_effects_and_common_words_are_not_skill_mentions(self):
        actual=js("console.log(JSON.stringify(S.format('교전 준비와 상대의 반격·매혹·공포를 확인합니다.',{champions:['Katarina','Jax','Ahri','Fiddlesticks']})))")
        self.assertEqual(actual,'교전 준비와 상대의 반격·매혹·공포를 확인합니다.')

    def test_explicit_owner_key_with_existing_key_is_idempotent(self):
        actual=js("const a=S.format('럭스 Q(Q)',{champions:['Lux']});console.log(JSON.stringify([a,S.format(a,{champions:['Lux']})]))")
        self.assertEqual(actual,['럭스의 빛의 속박(Q)','럭스의 빛의 속박(Q)'])

    def test_unqualified_name_only_in_explicitly_typed_name_field(self):
        actual=js("console.log(JSON.stringify([S.format('빛의 속박',{owner:'Lux'}),S.format('빛의 속박',{owner:'Lux',skillNames:true})]))")
        self.assertEqual(actual,['빛의 속박','럭스의 빛의 속박(Q)'])

    def test_alias_does_not_corrupt_canonical_name_or_repeat(self):
        actual=js("const o={champions:['Caitlyn'],aliases:[{text:'덫',champion:'Caitlyn',slot:'W'}]};const a=S.format('요들잡이 덫(W)과 덫',o);console.log(JSON.stringify([a,S.format(a,o)]))")
        self.assertEqual(actual[0],'케이틀린의 요들잡이 덫(W)과 케이틀린의 요들잡이 덫(W)');self.assertEqual(actual[0],actual[1])

    def test_explicit_mention_bindings_preserve_different_e_owners(self):
        actual=js("const input='E가 없거나 보호막이 닿지 않으면 회복합니다. E로 보지 못한 구역은 미확인입니다.';const opts={bindings:[{text:'E가 없거나',champion:'Caitlyn',slot:'E',prefix:true},{text:'E로 보지 못한',champion:'Lux',slot:'E',prefix:true}]};const before=JSON.stringify(opts);const a=S.format(input,opts);console.log(JSON.stringify([a,before===JSON.stringify(opts),S.format(a,opts)]))")
        self.assertIn('케이틀린의 90구경 투망(E)가 없거나',actual[0]);self.assertIn('럭스의 광휘의 특이점(E)로 보지 못한',actual[0]);self.assertTrue(actual[1]);self.assertEqual(actual[0],actual[2])

    def test_exact_locator_and_no_item_or_summoner_slots(self):
        actual=js("console.log(JSON.stringify([S.factLabel('Caitlyn',{name:'헤드샷',source:{locator:'data.Caitlyn.passive.description'}}),S.factLabel('Lux',{name:'빛의 속박',source:{locator:'data.Lux.spells.0.description'}}),S.factLabel('Lux',{name:'빛의 속박',source:{locator:'data.Caitlyn.spells.0.description'}}),S.factLabel('Lux',{name:'장화',slot:'ITEM'}),S.format('점멸 / 회복',{champions:['Lux']})]))")
        self.assertEqual(actual,['케이틀린의 헤드샷(P)','럭스의 빛의 속박(Q)','럭스의 빛의 속박(키 미확인)','장화','점멸 / 회복'])

    def test_display_input_objects_unchanged(self):
        actual=js("const x={name:'빛의 속박',text:'럭스 Q 원문',source:{locator:'data.Lux.spells.0.description',sha256:'fixed'}};const before=JSON.stringify(x);S.factLabel('Lux',x);S.format(x.text,{champions:['Lux']});console.log(JSON.stringify(before===JSON.stringify(x)))")
        self.assertTrue(actual)

    def test_existing_conflicting_key_is_not_resolved_for_cooldown(self):
        actual=js("console.log(JSON.stringify([S.resolveSlot('Lux','빛의 속박(Q)'),S.resolveSlot('Lux','빛의 속박(W)'),S.resolveSlot('Lux','Q'),S.resolveSlot('Lux','점멸')]))")
        self.assertEqual(actual,['Q',None,None,None])

    def test_official_name_with_owner_prefix_and_whitespace_is_not_stripped(self):
        actual=js("const d=require('./web_r4/skill-data.js');const bad=[];for(const c of Object.values(d.champions))for(const [slot,name] of Object.entries(c.slots)){for(const value of [name,name+'('+slot+')',S.label(c.id,slot)])if(S.resolveSlot(c.id,value)!==slot)bad.push([c.id,slot,value]);}console.log(JSON.stringify(bad))")
        self.assertEqual(actual,[])

    def test_official_display_whitespace_does_not_change_source_names(self):
        actual=js("const d=require('./web_r4/skill-data.js');const before=JSON.stringify(d);const label=S.factLabel('Belveth',{name:'연보랏빛 죽음',source:{locator:'data.Belveth.passive.description'}});const bad=[];for(const c of Object.values(d.champions))for(const slot of Object.keys(c.slots)){const value=S.label(c.id,slot);if(S.format(value,{champions:[c.id]})!==value)bad.push([c.id,slot]);}console.log(JSON.stringify([label,bad,before===JSON.stringify(d)]))")
        self.assertEqual(actual,['벨베스의 연보랏빛 죽음(P)',[],True])

    def test_offline_name_table_is_exact(self):
        p=subprocess.run(['python','scripts/build_skill_display.py','--check'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)

if __name__=='__main__':unittest.main()

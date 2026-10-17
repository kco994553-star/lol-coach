"""Semantic context counterexamples fixed before implementation; no accuracy claim."""
import unittest
import tests_pregame.test_loading_strategy as legacy


class LoadingContextTests(unittest.TestCase):
    run_node = legacy.LoadingStrategyTests.run_node
    # Keep this class's selected execution independent of inherited old tests.
    def test_lane_domain_does_not_inherit_global_partners(self):
        self.run_node(r'''
const a=E.exampleInput(C,0),r=E.analyze(a,C);
assert(r.contexts,'explicit context contract missing');
assert.equal(r.contexts.lane.kind,'DUO');
assert.deepEqual(r.contexts.lane.partners.map(p=>p.champion),['Lux']);
assert.deepEqual(new Set(r.contexts.lane.threats.map(p=>p.champion)),new Set(['Kaisa','Nautilus']));
assert(r.contexts.lane.threats.find(p=>p.champion==='Nautilus').evidence_ids.includes('official:Nautilus:Q'));
assert.equal(r.contexts.jungle.observation,'NOT_OBSERVED');
assert.deepEqual(r.contexts.jungle.partners.map(p=>p.champion),['Sejuani']);
assert(!/오른|세주아니|제드|피오라/.test(JSON.stringify(r.lane)));
const laneIds=new Set(r.contexts.lane.threats.map(p=>p.champion)),fightIds=new Set(r.teamfight.threats.map(p=>p.champion));
assert(!laneIds.has('Zed')&&fightIds.has('Zed'));
assert(r.scenarios.every(s=>s.context==='LANE'&&s.map.entities.every(e=>['Caitlyn','Lux'].includes(e.champion))));
''')

    def test_summary_is_compact_but_details_keep_conditions_and_all_candidates(self):
        self.run_node(r"""
const r=E.analyze(E.exampleInput(C,0),C);
for(const key of ['our_plan','fight_key']){
 assert(!/아리|오른|세주아니|피오라|리 신|제드/.test(r.summary[key]),'summary must describe functions, not enumerate candidates');
 assert(r.summary[key].length<150,'bounded summary length is a readability check, not comprehension evidence');
}
assert(/제어/.test(r.summary.our_plan)&&/거리/.test(r.summary.our_plan)&&/끊기/.test(r.summary.our_plan));
assert(/남은 인원·웨이브/.test(r.summary.our_plan)&&/귀환/.test(r.summary.our_plan),'conversion prerequisites must survive shortening');
assert(/럭스 Q/.test(r.summary.lane_key)&&/발동/.test(r.summary.lane_key)&&/거리/.test(r.summary.lane_key));
assert(/수급선/.test(r.summary.lane_key));
assert(/보호/.test(r.summary.fight_key)&&/접근/.test(r.summary.fight_key)&&/추격/.test(r.summary.fight_key));
assert(r.gameplan.base.includes('아리·럭스·오른·세주아니'));
assert.equal(r.contexts.teamfight.threats.length,5);assert(r.teamfight.role.includes('아리·럭스·오른·세주아니'));
const a=E.exampleInput(C,0);a.allies.find(p=>p.position==='SUPPORT').champion='Ziggs';
const noCover=E.analyze(a,C);assert(!noCover.summary.fight_key.includes('보호 연결 안에서'));assert(noCover.summary.fight_key.includes('내 이탈'));
""")

    def test_array_order_does_not_change_strategic_meaning_or_map(self):
        self.run_node(r'''
const a=E.exampleInput(C,0),r=E.analyze(a,C),project=x=>{const c=copy(x);delete c.input;return c;};
for(let i=0;i<5;i++)for(let j=0;j<5;j++){
 const b=copy(a);b.allies=[...a.allies.slice(i),...a.allies.slice(0,i)].reverse();b.enemies=[...a.enemies.slice(j),...a.enemies.slice(0,j)].reverse();
 assert.deepEqual(project(E.analyze(b,C)),project(r),'same champions/assignedroles must preserve meaning');
}
for(const ctx of Object.values(r.contexts))for(const p of [...(ctx.partners||[]),...(ctx.threats||[])]){assert(p.reasons.length);assert(!Object.hasOwn(p,'score'));assert(!Object.hasOwn(p,'priority'));}
''')

    def test_local_support_change_and_distant_ally_change_have_distinct_scope(self):
        self.run_node(r'''
const a=E.exampleInput(C,0),r=E.analyze(a,C),b=copy(a);b.allies.find(p=>p.position==='SUPPORT').champion='Janna';
const support=E.analyze(b,C);assert.deepEqual(support.contexts.lane.partners.map(p=>p.champion),['Janna']);
assert.deepEqual(support.contexts.lane.threats,r.contexts.lane.threats);
assert(!support.lane.matchup_id);assert(!JSON.stringify(support.lane).includes('빛의 속박'));assert(support.lane.rows.some(row=>row.evidence_ids.some(id=>id.startsWith('official:Janna:'))));
const c=copy(a);c.enemies.find(p=>p.position==='SUPPORT').champion='Lulu';const enemySupport=E.analyze(c,C);
assert(!enemySupport.lane.matchup_id);assert(!JSON.stringify(enemySupport.lane).includes('닻줄 견인'));
assert.deepEqual(new Set(enemySupport.contexts.lane.threats.map(p=>p.champion)),new Set(['Kaisa','Lulu']));
const d=copy(a);d.allies.find(p=>p.position==='TOP').champion='Malphite';const distant=E.analyze(d,C);
assert.deepEqual(distant.lane,r.lane);assert.deepEqual(distant.contexts.lane,r.contexts.lane);assert.deepEqual(distant.contexts.jungle,r.contexts.jungle);
assert(distant.teamfight.partners.some(p=>p.champion==='Malphite'));assert(!distant.teamfight.partners.some(p=>p.champion==='Ornn'));
''')

    def test_six_milestones_are_distinct_hypothetical_decisions_with_replies(self):
        self.run_node(r'''
const r=E.analyze(E.exampleInput(C,0),C);
assert.equal(r.lane.matchup_id,'Caitlyn_Lux__Kaisa_Nautilus_v2');
assert.deepEqual(r.lane.rows.map(row=>row.decision_id),['RECEIVE_WITH_SPACE','FOLLOW_BIND_WITH_EXIT','KEEP_ESCAPE_VS_REENGAGE','RESPECT_TARGETED_CONTROL','REASSESS_PURCHASE_AND_RETURN','KEEP_FOLLOWUP_AFTER_CORE']);
for(const row of r.lane.rows){
 assert.deepEqual(row.actors,{self:'Caitlyn',ally:'Lux',enemies:['Kaisa','Nautilus']});
 assert.equal(row.assumption_status,'NOT_OBSERVED');assert(row.assumptions.length&&row.opponent_response&&row.alternative&&row.fact_scope&&row.changes.length);
 assert.equal(row.level,'DESIGN_HYPOTHESIS');assert(row.judgment!=='조건부 대응 가능 · 매치업 우열 미확인');
 assert(row.evidence_ids.every(id=>r.evidence.facts.some(f=>f.id===id)||r.evidence.statistics.some(s=>s.id===id)));
}
assert(r.lane.rows[1].evidence_ids.includes('official:Lux:Q'));assert(r.lane.rows[1].evidence_ids.includes('official:Caitlyn:W'));
assert(r.lane.rows[2].evidence_ids.includes('official:Caitlyn:E'));assert(r.lane.rows[3].evidence_ids.includes('official:Nautilus:R'));
assert(r.lane.rows[3].evidence_ids.includes('official-detail:Kaisa:R'));
assert(r.lane.rows.every(row=>!Object.hasOwn(row,'advantage_score')));
assert.equal(r.evidence.real_coaching_n,0);assert.equal(r.evidence.accuracy,null);
''')

    def test_missing_assignment_retains_unknown_and_base_role_is_separate(self):
        self.run_node(r'''
const a=E.exampleInput(C,0),r=E.analyze(a,C),b=copy(a);b.enemies.find(p=>p.position==='SUPPORT').position=null;
const missing=E.analyze(b,C);assert.equal(missing.contexts.lane.kind,'DUO_INCOMPLETE');assert(!missing.lane.matchup_id);assert(!missing.contexts.lane.threats.some(p=>p.champion==='Nautilus'));assert(missing.teamfight.threats.some(p=>p.champion==='Nautilus'));
const u=copy(a);u.opponent_mode='UNKNOWN';const unknown=E.analyze(u,C);assert.equal(unknown.lane.opponent,null);assert(!unknown.lane.matchup_id);assert.deepEqual(unknown.contexts.lane.threats,[]);
const c=copy(a);c.allies=[{champion:'Gangplank',position:'TOP'},{champion:'Kindred',position:'JUNGLE'},{champion:'Hwei',position:'MID'},{champion:'Caitlyn',position:'BOTTOM'},{champion:'Teemo',position:'SUPPORT'}];
const insufficient=E.analyze(c,C);assert.equal(r.roles.base.id,insufficient.roles.base.id);assert.equal(insufficient.roles.changed,false);assert(insufficient.roles.proposed.limits.length);
assert(r.roles.proposed.action_ids.includes('FOLLOW_CONFIRMED_CONTROL'));assert(r.roles.proposed.action_ids.includes('KEEP_COVER_CONNECTION'));
assert(!insufficient.roles.proposed.action_ids.includes('KEEP_COVER_CONNECTION'));
const noCover=copy(a);noCover.allies.find(p=>p.position==='SUPPORT').champion='Ziggs';const exposed=E.analyze(noCover,C);
assert.equal(exposed.roles.base.id,r.roles.base.id);assert(!exposed.roles.proposed.action_ids.includes('KEEP_COVER_CONNECTION'));assert(exposed.roles.proposed.action_ids.includes('KEEP_SELF_EXIT'));
''')

    def test_retained_supplements_bind_exact_source_and_preserve_original_projections(self):
        from pathlib import Path
        import hashlib, json
        root=Path(__file__).resolve().parents[1]
        catalog=json.loads((root/'web_r4/loading-data.json').read_text())
        baseline=json.loads((root/'evidence/actual-evidence/loading-context/baseline-projection.json').read_text())
        def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        self.assertEqual(digest({k:v['facts'] for k,v in catalog['champions'].items()}),baseline['original_865_facts'])
        self.assertEqual(digest(catalog['statistics']),baseline['original_353_statistics'])
        self.assertEqual(digest(catalog['directions']),baseline['original_six_scenes'])
        self.assertEqual({f['id'] for f in catalog['context_facts']},{'official-detail:Kaisa:R','official-detail:Lux:W','official-detail:Lux:E','official-item:1001','official-item:1036'})
        for fact in catalog['context_facts']:
            raw=(root/fact['local_source']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),fact['sha256'])
            node=json.loads(raw)
            for part in fact['locator'].split('.'):
                node=node[int(part)] if isinstance(node,list) else node[part]
            self.assertEqual(node,fact['raw_excerpt'])
            self.assertEqual(fact['patch'],catalog['source_patch'])
        self.assertIn('플라즈마',next(f['text'] for f in catalog['context_facts'] if f['id']=='official-detail:Kaisa:R'))

    def test_known_enemy_support_survives_unknown_carry_assignment(self):
        self.run_node(r'''
const a=E.exampleInput(C,0);a.enemies.find(p=>p.position==='BOTTOM').position=null;
const r=E.analyze(a,C);assert.equal(r.lane.opponent,null);assert.equal(r.contexts.lane.kind,'DUO_INCOMPLETE');
assert.deepEqual(r.contexts.lane.threats.map(p=>p.champion),['Nautilus']);assert(!r.lane.matchup_id);
assert(r.summary.lane_key.includes('노틸러스'));
''')

    def test_role_swapped_enemy_duo_does_not_inherit_representative_template(self):
        self.run_node(r'''
const a=E.exampleInput(C,0);a.enemies.find(p=>p.champion==='Kaisa').position='SUPPORT';a.enemies.find(p=>p.champion==='Nautilus').position='BOTTOM';
const r=E.analyze(a,C);assert.equal(r.lane.opponent.id,'Nautilus');assert.equal(r.lane.matchup_id,null);
assert.deepEqual(new Set(r.contexts.lane.threats.map(p=>p.champion)),new Set(['Kaisa','Nautilus']));
''')

    def test_unbound_control_does_not_survive_as_a_concrete_followup_action(self):
        self.run_node(r'''
const a=E.exampleInput(C,0);a.allies=[{champion:'Gangplank',position:'TOP'},{champion:'Kindred',position:'JUNGLE'},{champion:'Hwei',position:'MID'},{champion:'Caitlyn',position:'BOTTOM'},{champion:'Teemo',position:'SUPPORT'}];
const r=E.analyze(a,C);assert.equal(r.roles.changed,false);assert(!r.roles.proposed.action_ids.includes('FOLLOW_CONFIRMED_CONTROL'));
assert(!r.teamfight.actions[1].includes('제어가 적중'));assert(r.teamfight.actions[1].includes('90구경 투망'));
assert(r.teamfight.actions[1].includes('미확인'));
''')

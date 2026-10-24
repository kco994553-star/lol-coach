"""GP-0.6 baseline and conditional composition trace, through the real report."""
import unittest
from tests_pregame import test_gameplan_coaching_content as runner


class GameplanDirectionTests(unittest.TestCase):
    node = runner.GameplanCoachingContentTests.node
    def test_direction_profiles_and_projection(self):
        self.node(r"""
const x=E.exampleInput(catalog,0),before=JSON.stringify(x),r=E.analyze(x,catalog),b=r.coach.planboard;
assert.equal(JSON.stringify(x),before);
for(const area of ['lane','operations','fight']){
 const d=b.direction_hierarchy[area];
 assert.equal(d.baseline.champion,'Caitlyn');assert.equal(d.baseline.phase,area);
 assert.equal(d.observation,false);assert.equal(d.review_state,'TACTICAL_UNREVIEWED');
 assert.equal(d.composition.response,b.narrative_decisions[area].response);
 assert.equal(d.composition.pressure,b.narrative_decisions[area].pressure);
 assert(b.coaching_explanation[area][0].startsWith(d.baseline.explanation));
 assert.equal(b.action_summaries[area].items.length,5);
}
assert.deepEqual(P.project(r).cards[0].explanation,b.coaching_explanation.lane);
x.allies[3].champion='Ezreal';x.own_champion='Ezreal';const ez=run(x);
for(const area of ['lane','operations','fight'])assert.notEqual(b.direction_hierarchy[area].baseline.explanation,ez.direction_hierarchy[area].baseline.explanation);
assert.equal(b.coverage.status,'BASIC_PLAN_CONDITIONAL');
""")

    def test_composition_and_state_are_separate(self):
        self.node(r"""
const x=E.exampleInput(catalog,0),b=run(x);x.allies[4].champion='Lulu';const lulu=run(x);
assert.deepEqual(b.direction_hierarchy.lane.baseline,lulu.direction_hierarchy.lane.baseline);
assert.notEqual(b.direction_hierarchy.lane.composition.response,lulu.direction_hierarchy.lane.composition.response);
x.schema_version='lol-coach-loading-input-v4';x.preferences={risk:'BALANCED'};
x.planning={basis:'loading-plan-example-v1',overrides:{income:'LOSING',opportunity:'MISSED'}};
x.scenario={standard:'lane-standard-v1',overrides:{resources:'LOW'}};
const blocked=run(x),d=blocked.direction_hierarchy.lane;
assert.deepEqual(d.baseline,lulu.direction_hierarchy.lane.baseline);
assert.equal(d.state_adjustment.state,'OPPORTUNITY_MISSED');
assert.equal(d.execution.response,blocked.narrative_decisions.lane.response);
assert.equal(d.state_adjustment.action,blocked.engagement_decision.action);
assert.notEqual(d.composition.response,d.execution.response);
assert.equal(d.composition.basis,'SCENARIO_PLAN_BEFORE_WAITING_RECONCILIATION');
assert.deepEqual(blocked.direction_hierarchy.fight,lulu.direction_hierarchy.fight);
""")

    def test_unknown_coverage_does_not_become_matchup_claim(self):
        self.node(r"""
const x=E.exampleInput(catalog,0);x.allies[4].champion='Blitzcrank';x.enemies[3].champion='Ezreal';x.enemies[4].champion='Karma';
const b=run(x),d=b.direction_hierarchy.lane;
assert.equal(d.change.kind,'LIMITED');assert.equal(d.composition,null);
assert.equal(d.coverage,'BASELINE_ONLY');assert.match(b.coaching_explanation.lane[0],/확정하지/);
assert.equal(b.narrative_decisions,undefined);
x.patch='1.1';assert.equal(run(x).direction_hierarchy,undefined);
x.patch='16.20';x.own_position='SUPPORT';x.own_champion='Blitzcrank';assert.equal(run(x).direction_hierarchy,undefined);
const y=E.exampleInput(catalog,0),c=structuredClone(catalog);
c.champions.Caitlyn.facts=c.champions.Caitlyn.facts.filter(f=>f.slot!=='P');
assert.equal(E.analyze(y,c).coach.planboard.direction_hierarchy,undefined);
y.opponent_mode='MANUAL';y.lane_opponent='Fiora';
assert.equal(run(y).direction_hierarchy.lane.composition,null);
""")

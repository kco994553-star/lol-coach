"""Exact tier/phase/basis selection: synthetic rows stay isolated from real files."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ChampionInsightsFrontendTests(unittest.TestCase):
    def node(self, body):
        result = subprocess.run(['node', '-e', "const assert=require('node:assert/strict'),fs=require('node:fs'),I=require('./web_r4/champion-insights.js'),S=require('./web_r4/champion-state.js');" + body], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_tier_default_roundtrip_and_navigation_do_not_change_facts(self):
        self.node("""
assert.equal(S.clean({}).tier,'MASTER_PLUS');assert.equal(S.clean({tier:'garbage'}).tier,'INVALID');assert.equal(S.decode(S.encode({tier:'garbage'})).tier,'INVALID');assert.equal(S.TIERS.length,12);
for(const tier of S.TIERS){const state=S.decode(S.encode({champion:'Caitlyn',position:'BOTTOM',tier,opponent:'Ezreal'}));assert.equal(state.tier,tier);assert.equal(S.applySelection(state,{champion:'Ahri',tier:'GOLD'}).tier,tier);assert.equal(S.selectChampion(state,'Ahri').tier,tier);assert.equal(S.chooseOpponent(state,'Ashe').tier,tier);assert.equal(S.beginSelection(state).tier,tier);}
const D=require('./web_r4/loading-draft.js');const intent=D.createIntent({champion:'Caitlyn',position:'BOTTOM',return_state:S.clean({champion:'Caitlyn',tier:'GOLD'})});assert.equal(intent.champion,'Caitlyn');assert.equal(intent.tier,undefined);
""")

    def test_real_default_partial_and_gold_empty_no_growth_or_tier_fallback(self):
        self.node("""
const index=require('./web_r4/champion-insights.json'),stats=require('./web_r4/champion-stats.json');const partial=I.select(index,'Caitlyn','BOTTOM');assert.equal(partial.scope.tier,'MASTER_PLUS');assert.equal(partial.scope.coverage,'PARTIAL');assert.deepEqual(partial.scope.available_tiers,['CHALLENGER']);assert.deepEqual(partial.scope.missing_tiers,['MASTER','GRANDMASTER']);const invalid=I.select(index,'Caitlyn','BOTTOM',S.clean({tier:'INVALID'}).tier);assert.equal(invalid.scope.coverage,'EMPTY');assert.equal(invalid.summary.n,0);const gold=I.select(index,'Caitlyn','BOTTOM','GOLD');assert.equal(gold.scope.coverage,'EMPTY');assert.equal(gold.summary.n,0);assert.equal(gold.summary.win_rate,null);assert.deepEqual(gold.frequent_opponents,[]);for(const role of I.POSITIONS)assert.equal(gold.by_enemy_position[role].eligible_count,0);assert.equal(I.legacyAvailable(stats,'GOLD',index.default_patch),false);assert.equal(I.legacyAvailable(stats,'MASTER_PLUS','99.99'),false);assert.equal(I.legacyAvailable(stats,'MASTER_PLUS',index.default_patch),true);assert.equal(I.select(index,'Caitlyn','BOTTOM','MASTER_PLUS','99.99').summary.n,0);assert.equal(I.select(index,'Caitlyn','TOP').summary.n,0);for(const role of I.POSITIONS)assert.equal(partial.by_enemy_position[role].eligible_count,0);
""")

    def test_exact_rank_basis_minimum_order_ties_overlap_and_own_perspective(self):
        self.node("""
const row=(enemy,n,wins,basis='ENEMY_TEAM_ROSTER',enemy_position='JUNGLE',extra={})=>({champion:'Ahri',position:'MID',tier:'GOLD',patch:'16.20',enemy_champion:enemy,enemy_position,n,wins,win_rate:wins/n,basis,...extra});const index={default_patch:'16.20',ranking_min_n:20,ranking_overlap:'INDEPENDENT_TOP5_BOTTOM5_OVERLAP_DISCLOSED_WHEN_FEW_ELIGIBLE',scopes:[],summaries:[],matchups:[row('Zed',3,2,'SAME_ROLE_ENCOUNTERS','MID'),row('Lux',25,20,'SAME_ROLE_ENCOUNTERS','MID'),row('Garen',100,100,'SAME_ROLE_ENCOUNTERS','JUNGLE'),row('LeeSin',30,15),row('Elise',40,20),row('Nidalee',19,19),row('Ivern',40,20),row('Udyr',40,20,'ENEMY_TEAM_ROSTER','JUNGLE',{tier:'MASTER'}),row('Vi',40,40,'ENEMY_TEAM_ROSTER','JUNGLE',{patch:'16.19'}),row('Zed',80,80,'ENEMY_TEAM_ROSTER','MID')]};const a=I.select(index,'Ahri','MID','GOLD');assert.deepEqual(a.frequent_opponents.map(r=>r.enemy_champion),['Garen','Lux','Zed']);assert.deepEqual(a.by_enemy_position.MID.best.map(r=>r.enemy_champion),['Lux']);assert.deepEqual(a.by_enemy_position.JUNGLE.best.map(r=>r.enemy_champion),['Elise','Ivern','LeeSin']);assert.equal(a.by_enemy_position.JUNGLE.overlap_count,3);assert.equal(a.by_enemy_position.JUNGLE.all_tied,true);assert.equal(a.by_enemy_position.JUNGLE.rate_ties,true);assert.equal(a.by_enemy_position.TOP.eligible_count,0);assert.equal(a.by_enemy_position.MID.best[0].win_rate,.8);const many={...index,matchups:Array.from({length:12},(_,i)=>row('Hero'+String(i).padStart(2,'0'),20,i))};const ranked=I.select(many,'Ahri','MID','GOLD').by_enemy_position.JUNGLE;assert.equal(ranked.best.length,5);assert.equal(ranked.worst.length,5);assert.equal(ranked.best[0].enemy_champion,'Hero11');assert.equal(ranked.worst[0].enemy_champion,'Hero00');assert.equal(ranked.overlap_count,0);
""")

    def test_top5_separate_and_knowledge_phase_category_author_source_preserved(self):
        self.node("""
const candidate=(opponent,extra={})=>({champion:'Ahri',position:'MID',opponent,opponent_position:'MID',assessment_scope:'LANING',publication_eligibility:'CONDITIONAL_CANDIDATE',qualitative_difficulty:'DIFFICULT',author_category:'Extreme',...extra});const records=[...Array.from({length:7},(_,i)=>candidate('Hero'+i)),candidate('Easy',{qualitative_difficulty:'RELATIVELY_EASIER_CONDITIONAL'}),candidate('WrongPhase',{assessment_scope:'OVERALL_UNSPECIFIED'}),candidate('Reference',{publication_eligibility:'REFERENCE_ONLY'}),candidate('WrongRole',{opponent_position:'TOP'})];const selected=I.knowledge({records},'Ahri','MID');assert.equal(selected.difficult.length,5);assert.equal(selected.easy.length,1);assert.equal(selected.easy[0].opponent,'Easy');assert.equal(selected.difficult[0].author_category,'Extreme');assert.equal(selected.difficult.some(r=>r.opponent==='WrongPhase'),false);assert.equal(I.knowledge({records},'Ahri','JUNGLE').difficult.length,0);
""")

    def test_advanced_rows_follow_selected_tier_patch_search_and_sort_with_intervals(self):
        self.node("""
const service=require('./web_r4/loading-champion-baseline.js').createService(require('./web_r4/loading-data.json'));
const row=(tier,enemy,n,wins)=>({champion:'Caitlyn',position:'BOTTOM',tier,patch:'16.20',enemy_champion:enemy,enemy_position:'BOTTOM',basis:'SAME_ROLE_ENCOUNTERS',n,wins,win_rate:wins/n,ci95:{low:.05,high:.95},status:'READY'});
const index={default_patch:'16.20',ranking_min_n:20,scopes:[],summaries:[],matchups:[row('GOLD','Ezreal',30,3),row('GOLD','Ashe',40,30),row('MASTER_PLUS','Ezreal',80,64),row('MASTER_PLUS','Ashe',20,2)]};
const gold=I.opponentRows(service,index,'Caitlyn','BOTTOM','GOLD');assert.deepEqual(gold.map(r=>[r.id,r.summary.n,r.summary.wins,r.summary.win_rate_pct]),[['Ashe',40,30,75],['Ezreal',30,3,10]]);assert.equal(gold[1].summary.ci_low_pct,5);assert.equal(gold[1].summary.ci_high_pct,95);assert.equal(gold[1].basis,'SAME_ROLE_ENCOUNTERS');assert.equal(gold[1].tier,'GOLD');assert.equal(gold[1].patch,'16.20');
const master=I.opponentRows(service,index,'Caitlyn','BOTTOM','MASTER_PLUS');assert.deepEqual(master.map(r=>[r.id,r.summary.n,r.summary.wins,r.summary.win_rate_pct]),[['Ezreal',80,64,80],['Ashe',20,2,10]]);assert.equal(I.opponentRows(service,index,'Caitlyn','BOTTOM','GOLD','이즈리얼')[0].summary.n,30);assert.deepEqual(I.opponentRows(service,index,'Caitlyn','BOTTOM','GOLD','','rate-asc').map(r=>r.id),['Ezreal','Ashe']);assert.deepEqual(I.opponentRows(service,index,'Caitlyn','BOTTOM','GOLD','','rate-desc').map(r=>r.id),['Ashe','Ezreal']);assert.equal(I.opponentRows(service,index,'Caitlyn','MID','GOLD').length,0);assert.equal(I.opponentRows(service,index,'Caitlyn','BOTTOM','GOLD','','sample','99.99').length,0);assert.equal(I.opponentRows(service,index,'Caitlyn','BOTTOM','SILVER').length,0);assert.equal(I.opponentRows(service,index,'Caitlyn','BOTTOM','GOLD','missing-hero').length,0);
""")

    def test_python_selector_parity_for_real_exact_scopes(self):
        from coach_v1.champion_insights import select_insights
        index = json.loads((ROOT / 'web_r4/champion-insights.json').read_text())
        for tier, patch, champion, position in [('MASTER_PLUS',None,'Caitlyn','BOTTOM'),('GOLD',None,'Caitlyn','BOTTOM'),('CHALLENGER','16.20','Ahri','MID'),('ALL','99.99','Ahri','MID')]:
            result = subprocess.run(['node','-e',"const I=require('./web_r4/champion-insights.js'),index=require('./web_r4/champion-insights.json');process.stdout.write(JSON.stringify(I.select(index,...JSON.parse(process.argv[1]))));",json.dumps([champion,position,tier]+([patch] if patch is not None else []))],cwd=ROOT,capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(result.stdout),select_insights(index,champion,position,tier,patch))

if __name__ == '__main__':
    unittest.main()

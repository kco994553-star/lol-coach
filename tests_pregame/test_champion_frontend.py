"""Champion exploration state and honest statistics projection, exercised in Node."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ChampionFrontendTests(unittest.TestCase):
    def node(self, body):
        script = "const assert=require('node:assert/strict'); const fs=require('node:fs');const path=require('node:path');const modulePath=path.resolve('web_r4/champion-state.js');assert.ok(fs.existsSync(modulePath),'champion state module is implemented');const S=require(modulePath);" + body
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_hash_roundtrip_whitelist_and_corruption(self):
        self.node("""
const state={champion:'Ahri',position:'MID',query:'카이 사',filter:'UNCLASSIFIED',scroll:324,opponent:'Zed',opponent_position:'MID',ally_support:'Lulu',enemy_support:'Nami',redirect:'https://evil.test',__proto__:{x:1}};
const back=S.decode(S.encode(state));assert.equal(back.champion,'Ahri');assert.equal(back.query,'카이 사');assert.equal(back.scroll,324);assert.equal(back.redirect,undefined);assert.equal(back.x,undefined);assert.equal(S.decode('#state=%zz').champion,'');assert.equal(S.clean({position:'FAKE',champion:'../foo',scroll:-2}).position,'');assert.equal(S.clean({champion:'../foo'}).champion,'');
""")

    def test_recent_dedup_limit_and_broken_storage(self):
        self.node("""
let memory={};const storage={getItem:k=>memory[k]||null,setItem:(k,v)=>memory[k]=v};
for(const id of ['Ahri','Zed','Lux','Annie','Garen','Ivern','Nami','Lulu','Caitlyn','Ahri'])S.remember(storage,id);
assert.deepEqual(S.recent(storage),['Ahri','Caitlyn','Lulu','Nami','Ivern','Garen','Annie','Lux']);assert.deepEqual(Object.keys(memory),['lol-coach-champion-recent-v1']);memory['lol-coach-champion-recent-v1']='oops';assert.deepEqual(S.recent(storage),[]);assert.doesNotThrow(()=>S.remember({getItem(){throw Error()},setItem(){throw Error()}},'Ahri'));
""")

    def test_observed_filter_is_not_authored_profile_filter(self):
        self.node("""
const catalog=JSON.parse(fs.readFileSync('web_r4/loading-data.json','utf8'));const service=require('./web_r4/loading-champion-baseline.js').createService(catalog);
const stats={champions:{Ahri:{observed_positions:[{position:'MID',matches:4}]},Caitlyn:{observed_positions:[]}}};
assert.equal(S.results(service,stats,'','ALL').length,173);assert.ok(S.results(service,stats,'','MID').some(x=>x.id==='Ahri'));assert.equal(S.results(service,stats,'','MID').length,1);assert.ok(S.results(service,stats,'','UNCLASSIFIED').some(x=>x.id==='Caitlyn'));assert.equal(S.results(service,stats,'카이 사','ALL')[0].id,'Kaisa');
""")

    def test_modal_changes_are_temporary_until_applied(self):
        self.node("""
const current=S.clean({champion:'Ahri',position:'MID',query:'아리',opponent:'Zed'});const draft=S.beginSelection(current);draft.champion='Lux';draft.query='럭스';draft.filter='SUPPORT';assert.equal(current.champion,'Ahri');const applied=S.applySelection(current,draft);assert.equal(applied.champion,'Lux');assert.equal(applied.position,'MID');assert.equal(applied.query,'아리');assert.equal(applied.opponent,'Zed');
""")

    def test_duration_gaps_never_interpolate_or_invert_opponent(self):
        self.node("""
const bins=[{start_minute:0,end_minute:5,n:99,win_rate_pct:80,drawable:false},{start_minute:5,end_minute:10,n:100,win_rate_pct:40,drawable:true},{start_minute:10,end_minute:15,n:0,win_rate_pct:null,drawable:false},{start_minute:15,end_minute:20,n:100,win_rate_pct:65,drawable:true}];
const series=S.series(bins);assert.deepEqual(series.map(x=>x.value),[null,40,null,65]);assert.equal(series[1].value,40);assert.equal(S.scope({champions:{Ahri:{positions:{MID:{summary:{n:12},opponents:{Zed:{summary:{n:3}}}}}}}},'Ahri','MID','Zed').summary.n,3);assert.equal(S.scope({champions:{}},'Ahri','MID'),null);
""")

    def test_detail_return_scroll_and_section_are_whitelisted(self):
        self.node("""
const state=S.decode(S.encode({champion:'Caitlyn',position:'BOTTOM',query:'케이',filter:'BOTTOM',scroll:342,detail_scroll:818,section:'matchup'}));assert.equal(state.detail_scroll,818);assert.equal(state.section,'matchup');assert.equal(state.scroll,342);assert.equal(state.query,'케이');assert.equal(S.clean({section:'javascript:evil',detail_scroll:-8}).section,'overview');assert.equal(S.clean({detail_scroll:-8}).detail_scroll,0);
""")

    def test_opponent_rows_use_own_role_real_summary_and_search(self):
        self.node("""
const catalog=JSON.parse(fs.readFileSync('web_r4/loading-data.json','utf8'));const service=require('./web_r4/loading-champion-baseline.js').createService(catalog);const stats={champions:{Ahri:{positions:{MID:{opponents:{Zed:{summary:{n:9,wins:1,win_rate_pct:11.1}},Lux:{summary:{n:3,wins:2,win_rate_pct:66.7}},Annie:{summary:{n:0,wins:0,win_rate_pct:null}}}},TOP:{opponents:{Garen:{summary:{n:40,wins:20,win_rate_pct:50}}}}}}}};
assert.deepEqual(S.opponents(service,stats,'Ahri','MID','','sample').map(x=>x.id),['Zed','Lux']);assert.equal(S.opponents(service,stats,'Ahri','MID','제드','sample')[0].summary.wins,1);assert.equal(S.opponents(service,stats,'Ahri','MID','가렌','sample').length,0);assert.deepEqual(S.opponents(service,stats,'Ahri','MID','','name').map(x=>x.id),['Lux','Zed']);assert.deepEqual(S.opponents(service,stats,'Ahri','MID','','rate-desc').map(x=>x.id),['Lux','Zed']);assert.deepEqual(S.opponents(service,stats,'Ahri','MID','','rate-asc').map(x=>x.id),['Zed','Lux']);const state=S.chooseOpponent(S.clean({champion:'Ahri',position:'MID',query:'아리',detail_scroll:40}),'Zed');assert.equal(state.opponent,'Zed');assert.equal(state.opponent_position,'MID');assert.equal(state.query,'아리');
""")

    def test_growth_values_only_visible_and_difference_interval_is_separate(self):
        self.node("""
const growth={points:[{metric:'gold_delta',minute:10,unit:'GOLD_PER_MINUTE',champion_mean:301,champion_n:5,reference_mean:290,reference_n:80,n:5,mean_delta:11,delta_ci95:{low:-2,high:24},visible:true},{metric:'xp_delta',minute:15,champion_mean:410,champion_n:1,reference_mean:400,reference_n:80,n:1,mean_delta:10,delta_ci95:{low:1,high:19},visible:false,omission_reason:'INSUFFICIENT_N'}]};const rows=S.growthPoints(growth);assert.equal(rows[0].champion_value,301);assert.equal(rows[0].reference_value,290);assert.deepEqual(rows[0].difference_ci,{low:-2,high:24});assert.equal(rows[0].champion_ci,undefined);assert.equal(rows[1].champion_value,null);assert.equal(rows[1].reference_value,null);assert.equal(rows[1].difference_value,null);assert.equal(rows[1].difference_ci,null);assert.equal(rows[1].n,1);assert.equal(rows[1].omission_reason,'INSUFFICIENT_N');assert.deepEqual(S.growthPoints(null),[]);
""")

    def test_explicit_selector_filter_carries_position_without_all_role_inference(self):
        self.node("""
for(const role of S.POSITIONS){const next=S.selectChampion(S.clean({filter:role,position:'',query:'케이',scroll:123}),'Caitlyn');assert.equal(next.position,role);assert.equal(next.query,'케이');assert.equal(next.scroll,123);const linkState=S.decode(S.encode(next));assert.equal(linkState.position,role);}
assert.equal(S.selectChampion(S.clean({filter:'ALL'}),'Ahri').position,'');assert.equal(S.selectChampion(S.clean({filter:'UNCLASSIFIED'}),'Ahri').position,'');assert.equal(S.selectChampion(S.clean({filter:'ALL',position:'TOP'}),'Ahri').position,'TOP');assert.equal(S.selectChampion(S.clean({filter:'UNCLASSIFIED',position:'MID'}),'Ahri').position,'MID');assert.equal(S.selectChampion(S.clean({filter:'BOTTOM',position:'MID'}),'Caitlyn').position,'BOTTOM');
""")

    def test_recent_champion_position_pairs_roundtrip_and_legacy_migration(self):
        self.node("""
let memory={'lol-coach-champion-recent-v1':JSON.stringify(['Ahri','Zed'])};const storage={getItem:k=>memory[k]||null,setItem:(k,v)=>memory[k]=v};assert.deepEqual(S.recentSelections(storage),[{champion:'Ahri',position:''},{champion:'Zed',position:''}]);S.remember(storage,'Ahri','MID');S.remember(storage,'Ahri','TOP');S.remember(storage,'Ahri','MID');assert.deepEqual(S.recentSelections(storage).slice(0,2),[{champion:'Ahri',position:'MID'},{champion:'Ahri',position:'TOP'}]);assert.deepEqual(S.recent(storage),['Ahri','Zed']);for(const champion of ['Lux','Annie','Garen','Ivern','Nami','Lulu','Caitlyn'])S.remember(storage,champion,'SUPPORT');assert.equal(S.recentSelections(storage).length,8);const entry=S.recentSelections(storage)[0];const selected=S.selectChampion(S.clean({filter:'BOTTOM'}),entry.champion,entry.position);assert.equal(S.decode(S.encode(selected)).position,'SUPPORT');memory['lol-coach-champion-recent-v1']=JSON.stringify([{champion:'Lux',position:'FAKE'},null,23,{champion:'../unsafe',position:'MID'}]);assert.deepEqual(S.recentSelections(storage),[{champion:'Lux',position:''}]);
""")

if __name__ == '__main__': unittest.main()

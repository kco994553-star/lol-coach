"""Champion lookup contracts; real retained catalog, no network or tactical approval."""
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRELUDE = r"""
const assert=require('node:assert/strict');
const B=require('./web_r4/loading-champion-baseline.js');
assert.equal(typeof B.createService,'function','baseline service must exist');
const catalog=require('./web_r4/loading-data.json');
const profiles=require('./web_r4/loading-direction-profiles.js');
const E=require('./web_r4/loading-engine.js');
const make=(c=catalog,p=profiles)=>B.createService(c,p);
const input=(champion='Caitlyn',position='BOTTOM',patch='16.20')=>({champion,position,patch});
"""

class ChampionBaselineTests(unittest.TestCase):
    def node(self, body):
        p=subprocess.run(['node','-e',PRELUDE+body],cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(p.returncode,0,p.stderr[-6000:])

    def test_registered_aliases_and_unicode_normalization(self):
        self.node(r"""
const s=make();
for(const q of ['카이사',"Kai'Sa",' KAI’SA ','ＫａｉＳａ']){
 const r=s.search({query:q});assert.equal(r.items[0].id,'Kaisa');
 assert.equal(r.items[0].match,'EXACT');assert.equal(r.selection,null);
}
assert.equal(s.search({query:'케이틀린'}).items[0].id,'Caitlyn');
""")

    def test_ranking_and_ambiguity_are_deterministic_not_auto_selected(self):
        self.node(r"""
const c=structuredClone(catalog);
c.champions.Caitlyn.aliases.push('공유','abc');
c.champions.Ezreal.aliases.push('공유','abcd');
c.champions.Fiora.aliases.push('zabc');
const s=make(c),r=s.search({query:'abc'});
assert.deepEqual(r.items.slice(0,3).map(x=>x.id),['Caitlyn','Ezreal','Fiora']);
assert.deepEqual(r.items.slice(0,3).map(x=>x.match),['EXACT','PREFIX','CONTAINS']);
assert.equal(s.search({query:'공유'}).items.length,2);assert.equal(s.search({query:'공유'}).selection,null);
assert.throws(()=>s.getBaseline(input('공유')),e=>e.code==='CHAMPION_AMBIGUOUS');
assert.deepEqual(s.search({query:''}),s.search({query:''}));
""")

    def test_real_roster_and_missing_content_are_distinct(self):
        self.node(r"""
const s=make(),r=s.search({query:'',limit:200});
assert.equal(r.total,Object.keys(catalog.champions).length);assert.equal(r.items.length,r.total);
const k=r.items.find(x=>x.id==='Kaisa');assert.equal(k.baseline_status,'NO_PROFILE');
assert.deepEqual(k.authored_positions,[]);assert.equal(k.selectable_positions.length,5);
assert.equal(s.search({query:'not-a-champion'}).status,'NO_RESULTS');
assert.equal(s.search({query:'!!!'}).total,0);
assert.equal(s.search({query:'',limit:2}).items.length,2);
""")

    def test_filters_use_authored_positions_not_official_class(self):
        self.node(r"""
const s=make();assert.deepEqual(s.search({position:'TOP'}).items.map(x=>x.id),['Fiora']);
assert.deepEqual(s.search({position:'JUNGLE'}).items.map(x=>x.id),['Graves']);
const c=structuredClone(catalog);c.champions.Kaisa.official_tags=['Support'];
assert(!make(c).search({position:'SUPPORT'}).items.some(x=>x.id==='Kaisa'));
assert.equal(s.getBaseline(input('Caitlyn','SUPPORT')).status,'UNSUPPORTED_POSITION');
""")

    def test_invalid_catalog_is_not_an_empty_search(self):
        self.node(r"""
for(const c of [null,{}, {champions:{}}, {...catalog,champions:[]}])
 assert.throws(()=>make(c),e=>e.code==='CATALOG_INVALID');
const c=structuredClone(catalog);c.champions.Caitlyn.id='Ezreal';
assert.throws(()=>make(c),e=>e.code==='CATALOG_INVALID');
""")

    def test_search_and_baseline_input_are_strict(self):
        self.node(r"""
const s=make();
for(const options of [{query:42},{query:'a'.repeat(101)},{position:'ADC'},{limit:0},{limit:Infinity},{other:true},[]])
 assert.throws(()=>s.search(options),e=>e.code==='INPUT_INVALID');
for(const x of [null,[],{champion:'Caitlyn',position:'ADC'}, {...input(),game:'VALORANT'}, {...input(),mode:'ARAM'}, {...input(),patch:'latest'}, {...input(),allies:[]}])
 assert.throws(()=>s.getBaseline(x),e=>e.code==='INPUT_INVALID');
for(const champion of ['__proto__','constructor','toString','NoSuchChampion'])
 assert.throws(()=>s.getBaseline(input(champion)),e=>e.code==='CHAMPION_NOT_FOUND');
""")

    def test_baseline_is_independent_of_ten_pick_analysis(self):
        self.node(r"""
const before=E.analyze;E.analyze=()=>{throw Error('composition analysis must not run');};
const r=make().getBaseline(input());E.analyze=before;
assert.equal(r.view_mode,'BASELINE');assert.equal(r.composition,null);assert.equal(r.observation,false);
assert.equal(r.status,'REFERENCE_ONLY');assert.equal(r.profile.version,profiles.version);
assert.equal(r.tactical_validation,'UNREVIEWED');assert.equal(r.patch_status,'MATCH');
assert(!('allies' in r.input));assert(!('advantage' in r));
for(const p of Object.values(r.phases)){
 assert.equal(p.status,'REFERENCE_ONLY');assert.equal(p.delivery,null);
 assert.deepEqual(p.tags,[]);assert(p.reference.paragraphs.length);
 assert(p.reason_codes.includes('FIVE_ACTION_CONTENT_NOT_AUTHORED'));
 assert(!/\{[PQWER]\}/.test(JSON.stringify(p.reference)));
}
""")

    def test_four_existing_profiles_preserve_original_text_and_versions(self):
        self.node(r"""
const P=require('./web_r4/loading-planboard.js'),s=make();
for(const [id,row] of Object.entries(profiles.champions)){
 const r=s.getBaseline(input(id,row.role));
 const old=P.resolveDirectionProfiles(profiles,id,row.role,catalog);
 for(const phase of ['lane','operations','fight'])
  assert.equal(r.phases[phase].reference.paragraphs[0],old.phases[phase].explanation);
 assert.equal(r.versions.direction_data,old.version);
}
assert.equal(s.getBaseline(input('Graves','JUNGLE')).phases.lane.label,'초반 정글');
""")

    def test_unknown_champion_role_and_missing_profile_do_not_reuse_another_plan(self):
        self.node(r"""
const s=make();
for(const [x,status] of [[{champion:'Caitlyn'},'POSITION_REQUIRED'],[input('Caitlyn','MID'),'UNSUPPORTED_POSITION'],[input('Kaisa'),'NO_PROFILE']]){
 const r=s.getBaseline(x);assert.equal(r.status,status);
 assert(Object.values(r.phases).every(p=>p.reference===null&&p.delivery===null));
}
assert.equal(s.getBaseline(input()).status,'REFERENCE_ONLY');
""")

    def test_unknown_and_different_patches_never_become_current_actions(self):
        self.node(r"""
const s=make();const unknown=s.getBaseline({champion:'Caitlyn',position:'BOTTOM'});
assert.equal(unknown.patch_status,'NOT_CONFIRMED');assert.equal(unknown.status,'REFERENCE_ONLY');
assert.equal(unknown.profile.source_patch,'16.20.1');assert.equal(unknown.phases.lane.delivery,null);
for(const patch of ['16.21','16.20.2']){
 const r=s.getBaseline(input('Caitlyn','BOTTOM',patch));assert.equal(r.status,'SOURCE_REVIEW_REQUIRED');
 assert.equal(r.patch_status,'MISMATCH');assert(Object.values(r.phases).every(p=>p.reference===null));
}
const p=structuredClone(profiles);p.source_patch='16.21.1';
assert.equal(make(catalog,p).getBaseline(input()).status,'SOURCE_REVIEW_REQUIRED');
""")

    def test_phase_failure_is_isolated(self):
        self.node(r"""
const p=structuredClone(profiles);delete p.champions.Caitlyn.phases.fight;
const r=make(catalog,p).getBaseline(input());assert.equal(r.status,'PARTIAL');
assert.equal(r.phases.fight.status,'NO_PHASE_CONTENT');assert.equal(r.phases.lane.status,'REFERENCE_ONLY');
const c=structuredClone(catalog);c.champions.Caitlyn.facts=c.champions.Caitlyn.facts.filter(f=>f.slot!=='E');
const z=make(c).getBaseline(input());assert.equal(z.phases.fight.status,'SOURCE_REVIEW_REQUIRED');
assert.equal(z.phases.lane.status,'REFERENCE_ONLY');
""")

    def test_facts_require_retained_source_bindings(self):
        self.node(r"""
for(const field of ['sha256','patch','local_source','id','name']){
 const c=structuredClone(catalog);c.champions.Caitlyn.facts.find(f=>f.slot==='Q')[field]=field==='name'?'':'invalid';
 const r=make(c).getBaseline(input());assert.equal(r.phases.lane.status,'SOURCE_REVIEW_REQUIRED',field);
}
const c=structuredClone(catalog);c.source_bindings=[];
assert.equal(make(c).getBaseline(input()).status,'SOURCE_REVIEW_REQUIRED');
""")

    def test_bad_templates_and_profile_metadata_fail_closed(self):
        self.node(r"""
for(const value of ['{R}','{bad}','{Q','']){
 const p=structuredClone(profiles);p.champions.Caitlyn.phases.lane.explanation=value;
 assert.equal(make(catalog,p).getBaseline(input()).phases.lane.status,'SOURCE_REVIEW_REQUIRED');
}
for(const value of [null,{}, {...profiles,review_state:'APPROVED'}, {...profiles,version:''}, {...profiles,schema_version:'future'}])
 assert.equal(make(catalog,value).getBaseline(input()).status,'SOURCE_REVIEW_REQUIRED');
""")

    def test_evidence_trace_is_per_phase_without_approval_promotion(self):
        self.node(r"""
const r=make().getBaseline(input());
for(const [phase,p] of Object.entries(r.phases)){
 assert.equal(p.reference.source_path,'web_r4/loading-direction-profiles.js');
 assert.equal(p.reference.locator,`champions.Caitlyn.phases.${phase}`);
 assert.equal(p.reference.review_state,'TACTICAL_UNREVIEWED');
 assert(p.reference.evidence.every(f=>f.id.startsWith('official:Caitlyn:')&&/^[a-f0-9]{64}$/.test(f.sha256)));
 assert.equal(p.reference.mechanism_evidence_is_tactical_validation,false);
}
""")

    def test_results_and_service_snapshot_do_not_mutate_shared_inputs(self):
        self.node(r"""
const c=structuredClone(catalog),p=structuredClone(profiles),before=JSON.stringify([c,p]),s=make(c,p);
const first=s.getBaseline(input()),expected=JSON.stringify(first);
first.phases.lane.reference.paragraphs[0]='corrupted';
const results=s.search();results.items[0].name='corrupted';
assert.equal(JSON.stringify([c,p]),before);assert.equal(JSON.stringify(s.getBaseline(input())),expected);
p.version='changed';c.champions.Caitlyn.name='corrupted';
assert.equal(JSON.stringify(s.getBaseline(input())),expected);
assert.notEqual(JSON.stringify(s.getBaseline(input('Caitlyn','TOP'))),expected);
""")

    def test_handoff_is_an_immutable_intent_not_a_dummy_draft(self):
        self.node(r"""
const s=make(),r=s.prepareHandoff({champion:'카이사',position:'BOTTOM'});
assert.equal(r.status,'READY');assert.equal(r.apply_automatically,false);
assert.deepEqual(r.intent,{own_champion:'Kaisa',own_position:'BOTTOM'});
assert.equal(r.draft,null);assert.equal(r.composition_ready,false);
assert(!('enemies' in r.intent));assert(!('allies' in r.intent));
""")

    def test_existing_draft_and_context_are_preserved_exactly(self):
        self.node(r"""
const s=make(),d=E.exampleInput(catalog),before=JSON.stringify(d);
d.notes='keep me';const r=s.prepareHandoff({champion:'Caitlyn',position:'BOTTOM'},d);
assert.equal(r.status,'READY');assert.deepEqual(r.draft,d);assert.equal(r.apply_automatically,false);
r.draft.notes='changed';assert.equal(d.notes,'keep me');
assert.equal(JSON.stringify({...d,notes:undefined}),before);
""")

    def test_handoff_detects_replacement_duplicate_and_role_conflicts(self):
        self.node(r"""
const s=make(),d=E.exampleInput(catalog),before=JSON.stringify(d);
let r=s.prepareHandoff({champion:'Ezreal',position:'BOTTOM'},d);
assert.equal(r.status,'CONFIRMATION_REQUIRED');assert(r.conflicts.some(x=>x.code==='SLOT_OCCUPIED'));
r=s.prepareHandoff({champion:'Kaisa',position:'BOTTOM'},d);
assert.equal(r.status,'BLOCKED');assert(r.conflicts.some(x=>x.code==='CHAMPION_ON_ENEMY_TEAM'));
r=s.prepareHandoff({champion:'Lux',position:'BOTTOM'},d);
assert.equal(r.status,'CONFIRMATION_REQUIRED');assert(r.conflicts.some(x=>x.code==='CHAMPION_IN_OTHER_SLOT'));
assert.equal(JSON.stringify(d),before);assert.deepEqual(r.draft,d);
""")

    def test_ambiguous_partial_draft_does_not_silently_replace_unknown_slot(self):
        self.node(r"""
const s=make(),d={allies:[{champion:'Caitlyn',position:null}],enemies:[],own_champion:'Caitlyn',own_position:'BOTTOM'};
const r=s.prepareHandoff({champion:'Caitlyn',position:'BOTTOM'},d);
assert.equal(r.status,'CONFIRMATION_REQUIRED');assert(r.conflicts.some(x=>x.code==='POSITION_UNCONFIRMED'));
assert.equal(r.composition_ready,false);assert.deepEqual(r.draft,d);
for(const d of [[],{allies:[],enemies:'bad'},{allies:[{champion:'NoSuch',position:null}],enemies:[]}])
 assert.throws(()=>s.prepareHandoff({champion:'Caitlyn',position:'BOTTOM'},d),e=>e.code==='DRAFT_INVALID');
""")

    def test_existing_ten_pick_validation_stays_strict(self):
        self.node(r"""
for(let i=0;i<6;i++)assert(E.analyze(E.exampleInput(catalog,i),catalog));
const d=E.exampleInput(catalog);d.enemies.pop();assert.throws(()=>E.analyze(d,catalog));
assert.throws(()=>E.analyze(input(),catalog));
""")

    def test_handoff_rejects_existing_cross_team_duplicates_and_full_unknown_slots(self):
        self.node(r"""
const s=make(),d=E.exampleInput(catalog);
d.enemies[0].champion='Ornn';
assert.equal(s.prepareHandoff({champion:'Caitlyn',position:'BOTTOM'},d).status,'BLOCKED');
const partial={allies:[{champion:'Ornn',position:'TOP'},{champion:'Sejuani',position:'JUNGLE'},{champion:'Ahri',position:'MID'},{champion:'Ashe',position:null},{champion:'Lux',position:'SUPPORT'}],enemies:[]};
const r=s.prepareHandoff({champion:'Caitlyn',position:'BOTTOM'},partial);
assert.equal(r.status,'CONFIRMATION_REQUIRED');assert(r.conflicts.some(x=>x.code==='POSITION_UNCONFIRMED'));
""")

    def test_explicit_canonical_id_remains_selectable_when_alias_is_ambiguous(self):
        self.node(r"""
const c=structuredClone(catalog);c.champions.Ezreal.aliases.push('Caitlyn');
const s=make(c);assert.equal(s.search({query:'Caitlyn'}).items.length,2);
assert.equal(s.search({query:'Caitlyn'}).selection,null);
assert.equal(s.getBaseline(input('Caitlyn')).input.champion,'Caitlyn');
assert.throws(()=>s.getBaseline(input('caitlyn')),e=>e.code==='CHAMPION_AMBIGUOUS');
""")

    def test_declared_but_corrupt_profile_is_not_reported_as_absent(self):
        self.node(r"""
const p=structuredClone(profiles);p.champions.Caitlyn=null;
const s=make(catalog,p);assert.equal(s.getBaseline(input()).status,'SOURCE_REVIEW_REQUIRED');
assert.equal(s.search({query:'Caitlyn'}).items[0].baseline_status,'SOURCE_REVIEW_REQUIRED');
""")

    def test_browser_umd_without_node_or_network(self):
        self.node(r"""
const fs=require('node:fs'),vm=require('node:vm');
const ctx={LoadingDirectionProfiles:profiles};vm.createContext(ctx);
vm.runInContext(fs.readFileSync('./web_r4/loading-champion-baseline.js','utf8'),ctx);
assert.equal(typeof ctx.LoadingChampionBaseline.createService,'function');
assert.equal(ctx.LoadingChampionBaseline.createService(catalog).search({query:'카이사'}).items[0].id,'Kaisa');
""")

class ChampionBaselineTransportTests(unittest.TestCase):
    def test_public_export_includes_backend_module_without_private_files(self):
        import tempfile
        from scripts.build_directions_web import build
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'site'
            build(out)
            self.assertEqual((out/'loading-champion-baseline.js').read_bytes(),(ROOT/'web_r4/loading-champion-baseline.js').read_bytes())
            self.assertFalse((out/'pc.js').exists())
            self.assertFalse((out/'tests_pregame').exists())

    def test_pc_static_route_preserves_private_auth_boundary(self):
        import http.client
        import tempfile
        import threading
        from coach_v1.pregame_server import PregameWorkbench
        from coach_v1.server import Limits
        with tempfile.TemporaryDirectory() as tmp:
            server=PregameWorkbench(Path(tmp)/'work.sqlite','synthetic-baseline-token-not-a-credential',Limits(1_000_000,100,100,100,100,10))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                for path,expected in [('/loading-champion-baseline.js',200),('/dev/v1/pregame/pc-status',401),('/loading-champion-baseline.js?token=bad',400)]:
                    conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
                    conn.request('GET',path);response=conn.getresponse();body=response.read();conn.close()
                    self.assertEqual(response.status,expected,path)
                    if expected==200:self.assertEqual(body,(ROOT/'web_r4/loading-champion-baseline.js').read_bytes())
            finally:
                server.shutdown();thread.join();server.server_close()

if __name__=='__main__':unittest.main()

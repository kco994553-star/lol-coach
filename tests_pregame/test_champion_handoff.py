"""Preservation-safe partial draft and champion transfer behavior (Node UMD)."""
import subprocess
import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRELUDE = r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
assert.ok(fs.existsSync('./web_r4/loading-draft.js'),'partial draft adapter must exist');
const D=require('./web_r4/loading-draft.js'), E=require('./web_r4/loading-engine.js');
const catalog=require('./web_r4/loading-data.json');
const complete=()=>E.exampleInput(catalog);
const blank=()=>D.fromInput({allies:[],enemies:[],side:'RED',patch:'16.20',preferences:{risk:'LOSS_LIMIT'}});
"""

class ChampionHandoffTests(unittest.TestCase):
    def node(self, body):
        result = subprocess.run(['node', '-e', PRELUDE + body], cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr[-7000:])

    def test_intent_is_immutable_and_roundtrips_exact_contract(self):
        self.node(r"""
const raw={champion:'Caitlyn',position:'BOTTOM',opponent:'Kaisa',opponent_position:'BOTTOM',ally_support:'Lux',enemy_support:'Nautilus',reference:'profile:bottom',return_state:{target:'champion.html',champion:'Caitlyn',position:'BOTTOM'}};
const intent=D.createIntent(raw);raw.return_state.champion='Ezreal';
assert.ok(Object.isFrozen(intent));assert.ok(Object.isFrozen(intent.return_state));
assert.equal(intent.return_state.champion,'Caitlyn');assert.deepEqual(D.decodeIntent(D.encodeIntent(intent)),intent);
""")

    def test_rejects_malformed_proto_unknown_roles_and_external_return(self):
        self.node(r"""
for(const raw of [{champion:'Caitlyn',position:'ADC'},{champion:'__proto__',position:'BOTTOM'},JSON.parse('{"champion":"Caitlyn","position":"BOTTOM","__proto__":{}}'),{champion:'Caitlyn',position:'BOTTOM',return_state:{target:'https://evil.test'}},{champion:'Caitlyn',position:'BOTTOM',opponent_position:'MID'}])assert.throws(()=>D.createIntent(raw));
for(const hash of ['#handoff=%',' #handoff={}','#handoff='+encodeURIComponent('null')])assert.throws(()=>D.decodeIntent(hash));
for(const value of [null,{},[],{allies:[]}])assert.throws(()=>D.decodeDraft('#draft='+encodeURIComponent(JSON.stringify(value))));
assert.equal({}.polluted,undefined);
""")

    def test_blank_slots_and_unknown_positions_survive_roundtrip(self):
        self.node(r"""
const d=blank();assert.equal(d.input.allies.length,5);assert.deepEqual(d.input.allies[3],{champion:null,position:null});
assert.equal(D.toCompleteInput(d),null);const hash=D.encodeDraft(d);assert.deepEqual(D.decodeDraft(hash),d);
assert.equal(d.input.side,'RED');assert.equal(d.input.preferences.risk,'LOSS_LIMIT');
""")

    def test_preview_never_mutates_and_ambiguous_slot_requires_choice(self):
        self.node(r"""
const d=blank(),before=JSON.stringify(d),p=D.previewTransfer(D.createIntent({champion:'Caitlyn',position:'BOTTOM'}),d);
assert.equal(p.changes[0].target,null);assert.equal(p.changes[0].candidates.length,5);
assert.throws(()=>D.applyTransfer(p,{},0),/TARGET_REQUIRED/);
const next=D.applyTransfer(p,{targets:{own:'allies:3'}},0);
assert.equal(JSON.stringify(d),before);assert.deepEqual(next.input.allies[3],{champion:'Caitlyn',position:'BOTTOM'});
assert.equal(next.input.allies.filter(p=>p.champion).length,1);assert.equal(next.revision,1);
""")

    def test_occupied_target_requires_explicit_replacement_and_preserves_rest(self):
        self.node(r"""
const d=D.fromInput(complete(),4),p=D.previewTransfer(D.createIntent({champion:'Ezreal',position:'BOTTOM'}),d);
assert.equal(p.changes[0].target,'allies:3');assert.equal(p.changes[0].previous.champion,'Caitlyn');
assert.throws(()=>D.applyTransfer(p,{},4),/REPLACEMENT_REQUIRED/);
const n=D.applyTransfer(p,{replacements:['allies:3']},4);
assert.equal(n.input.allies[3].champion,'Ezreal');assert.deepEqual(n.input.enemies,d.input.enemies);
assert.deepEqual(n.input.allies[0],d.input.allies[0]);assert.equal(n.input.own_champion,'Ezreal');
assert.equal(E.analyze(D.toCompleteInput(n),catalog).input.own_champion,'Ezreal');
""")

    def test_duplicate_across_teams_blocks_without_auto_deleting(self):
        self.node(r"""
const d=D.fromInput(complete()),p=D.previewTransfer(D.createIntent({champion:'Kaisa',position:'BOTTOM'}),d),before=JSON.stringify(d);
assert.equal(p.status,'BLOCKED');assert.throws(()=>D.applyTransfer(p,{replacements:['allies:3']},0),/DUPLICATE/);
assert.equal(JSON.stringify(d),before);assert.equal(d.input.enemies[3].champion,'Kaisa');
""")

    def test_stale_revision_and_invalid_targets_are_rejected(self):
        self.node(r"""
const p=D.previewTransfer(D.createIntent({champion:'Caitlyn',position:'BOTTOM'}),blank());
assert.throws(()=>D.applyTransfer(p,{targets:{own:'allies:3'}},1),/STALE_REVISION/);
for(const target of ['enemies:3','allies:5','allies:__proto__'])assert.throws(()=>D.applyTransfer(p,{targets:{own:target}},0));
""")

    def test_multi_transfer_shows_old_new_and_preserves_v4_context(self):
        self.node(r"""
let input=E.analyze(complete(),catalog).input;input.schema_version='lol-coach-loading-input-v4';
input.scenario=require('./web_r4/loading-coach.js').defaultScenario();input.planning=require('./web_r4/loading-planboard.js').defaults();
const d=D.fromInput(input),p=D.previewTransfer(D.createIntent({champion:'Ezreal',position:'BOTTOM',opponent:'Ashe',opponent_position:'BOTTOM',ally_support:'Lulu',enemy_support:'Alistar'}),d);
assert.equal(p.changes.length,4);assert.equal(p.changes[1].previous.champion,'Kaisa');assert.equal(p.changes[1].next.champion,'Ashe');
const n=D.applyTransfer(p,{replacements:['allies:3','enemies:3','allies:4','enemies:4']},0);
assert.deepEqual(n.input.scenario,input.scenario);assert.deepEqual(n.input.planning,input.planning);
assert.equal(n.input.schema_version,'lol-coach-loading-input-v4');assert.equal(E.analyze(D.toCompleteInput(n),catalog).input.own_champion,'Ezreal');
""")

    def test_unknown_existing_position_requires_explicit_slot_and_keeps_other_picks(self):
        self.node(r"""
const d=blank();const raw=JSON.parse(JSON.stringify(d.input));raw.allies[1]={champion:'Ahri',position:null};
const p=D.previewTransfer(D.createIntent({champion:'Caitlyn',position:'BOTTOM'}),D.fromInput(raw));
assert.equal(p.changes[0].target,null);const n=D.applyTransfer(p,{targets:{own:'allies:3'}},0);
assert.deepEqual(n.input.allies[1],{champion:'Ahri',position:null});
""")

    def test_storage_failure_leaves_prior_draft_unchanged(self):
        self.node(r"""
const old=blank(),next=D.applyTransfer(D.previewTransfer(D.createIntent({champion:'Caitlyn',position:'BOTTOM'}),old),{targets:{own:'allies:3'}},0);
const storage={getItem:()=>D.encodeDraft(old),setItem:()=>{throw Error('quota')}};
assert.equal(D.saveDraft(storage,next).ok,false);assert.deepEqual(D.loadDraft(storage),old);
""")

    def test_return_link_is_local_and_restores_state(self):
        self.node(r"""
const i=D.createIntent({champion:'Caitlyn',position:'BOTTOM',return_state:{target:'champion.html',champion:'Caitlyn',position:'BOTTOM',opponent:'Kaisa'}});
const link=D.returnLink(i);assert.ok(link.startsWith('./champion.html#'));assert.ok(link.includes('Kaisa'));
assert.equal(D.returnLink(D.createIntent({champion:'Caitlyn',position:'BOTTOM'})),null);
""")

    def browser(self, body):
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT / 'web_r4')))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        script = PRELUDE + """
const {chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
try{const page=await browser.newPage();const base='http://127.0.0.1:PORT/loading.html';
""".replace('PORT', str(server.server_port)) + body + """
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
"""
        try:
            result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True, timeout=70)
            self.assertEqual(result.returncode, 0, result.stderr[-7000:])
        finally:
            server.shutdown()
            server.server_close()

    def test_browser_cancel_partial_apply_and_refresh(self):
        self.browser(r"""
const hash=D.encodeIntent({champion:'Caitlyn',position:'BOTTOM',return_state:{champion:'Caitlyn',position:'BOTTOM'}});
await page.goto(base+hash);await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
assert.equal(await page.locator('#handoff-preview').isVisible(),true);
assert.equal(await page.locator('#pick-ALLY-3').inputValue(),'');
await page.locator('#handoff-cancel').click();assert.equal(new URL(page.url()).hash,hash);
assert.equal(await page.evaluate(()=>sessionStorage.getItem('lol-coach-gameplan-draft-v1')),null);
await page.reload();await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
await page.locator('select[data-handoff-target]').selectOption('allies:3');await page.locator('#handoff-apply').click();
await page.waitForFunction(()=>location.hash.startsWith('#draft='));
assert.equal(await page.locator('#pick-ALLY-3').inputValue(),'케이틀린');assert.equal(await page.locator('#pick-ALLY-0').inputValue(),'');
assert.equal(await page.locator('#loading-results').isHidden(),true);
await page.reload();await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
assert.equal(await page.locator('#pick-ALLY-3').inputValue(),'케이틀린');assert.equal(await page.locator('#loading-results').isHidden(),true);
""")

    def test_browser_complete_replacement_clears_form_and_keeps_context(self):
        self.browser(r"""
const P=require('./web_r4/loading-presentation.js'),C=require('./web_r4/loading-coach.js'),B=require('./web_r4/loading-planboard.js');
let input=E.analyze(complete(),catalog).input;input.schema_version='lol-coach-loading-input-v4';input.scenario=C.defaultScenario();input.planning=B.defaults();
await page.goto(base+P.encode(input));await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
assert.equal(await page.locator('#loading-results').isVisible(),true);
await page.evaluate(hash=>location.hash=hash,D.encodeIntent({champion:'Ezreal',position:'BOTTOM'}));
await page.waitForSelector('#handoff-preview:not([hidden])');
assert.equal(await page.locator('#pick-ALLY-3').inputValue(),'케이틀린');
await page.locator('#handoff-apply').click();assert.ok(new URL(page.url()).hash.startsWith('#handoff='));
await page.locator('input[data-handoff-replace]').check();await page.locator('#handoff-apply').click();
await page.waitForFunction(()=>location.hash.startsWith('#plan='));
const route=P.decode(new URL(page.url()).hash);assert.equal(route.input.own_champion,'Ezreal');assert.deepEqual(route.input.scenario,input.scenario);assert.deepEqual(route.input.planning,input.planning);
assert.deepEqual(route.input.enemies,input.enemies);
const partial=D.fromInput({allies:[{champion:'Ahri',position:null}],enemies:[]});
await page.evaluate(hash=>location.hash=hash,D.encodeDraft(partial));await page.waitForFunction(()=>document.querySelector('#pick-ALLY-0').value==='아리');
assert.equal(await page.locator('#pick-ALLY-3').inputValue(),'');assert.equal(await page.locator('#pick-ENEMY-3').inputValue(),'');
""")

    def test_return_state_and_draft_version_must_be_well_formed(self):
        self.node(r"""
for(const return_state of [{unknown:'injected'},{position:'ADC'},{scroll:-1},{filter:'BAD'}])assert.throws(()=>D.createIntent({champion:'Caitlyn',position:'BOTTOM',return_state}));
for(const raw of [{schema_version:'lol-coach-loading-input-v4',allies:[],enemies:[]},{schema_version:'lol-coach-loading-input-v2',allies:[],enemies:[],scenario:{}}])assert.throws(()=>D.fromInput(raw));
""")

    def test_browser_storage_revision_race_regenerates_without_applying(self):
        self.browser(r"""
await page.goto(base+D.encodeIntent({champion:'Caitlyn',position:'BOTTOM'}));await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
await page.locator('[data-handoff-target]').selectOption('allies:3');
await page.evaluate(hash=>sessionStorage.setItem('lol-coach-gameplan-draft-v1',hash),D.encodeDraft(D.fromInput({allies:[{champion:'Ahri',position:null}],enemies:[]},7)));
await page.locator('#handoff-apply').click();assert.ok(new URL(page.url()).hash.startsWith('#handoff='));
assert.equal(await page.locator('#pick-ALLY-0').inputValue(),'아리');assert.equal(await page.locator('#pick-ALLY-3').inputValue(),'');
assert.equal(await page.locator('[data-handoff-target]').inputValue(),'');
assert.ok((await page.locator('#handoff-message').innerText()).includes('미리보기'));
await page.locator('[data-handoff-target]').selectOption('allies:3');await page.locator('#handoff-apply').click();
await page.waitForFunction(()=>location.hash.startsWith('#draft='));
const next=D.decodeDraft(new URL(page.url()).hash);assert.equal(next.revision,8);assert.equal(next.input.allies[0].champion,'Ahri');assert.equal(next.input.allies[3].champion,'Caitlyn');
""")

    def test_browser_handoff_preserves_coach_edited_scenario(self):
        self.browser(r"""
const P=require('./web_r4/loading-presentation.js');await page.goto(base+P.encode(E.analyze(complete(),catalog).input));await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
await page.locator('[data-plan-area="lane"]').click();await page.locator('summary').filter({hasText:'상황 바꾸기'}).click();await page.locator('[data-coach-focus="quick-KEY_SPENT"]').click();
await page.waitForFunction(()=>JSON.parse(decodeURIComponent(location.hash.slice(6))).input.scenario?.overrides.enemy_key==='SPENT');
await page.evaluate(hash=>location.hash=hash,D.encodeIntent({champion:'Ezreal',position:'BOTTOM'}));await page.waitForSelector('#handoff-preview:not([hidden])');
await page.locator('[data-handoff-replace]').check();await page.locator('#handoff-apply').click();await page.waitForFunction(()=>location.hash.startsWith('#plan='));
const input=P.decode(new URL(page.url()).hash).input;assert.equal(input.scenario.overrides.enemy_key,'SPENT');assert.equal(input.schema_version,'lol-coach-loading-input-v4');
""")

    def test_browser_resolving_duplicate_regenerates_preview(self):
        self.browser(r"""
const P=require('./web_r4/loading-presentation.js');await page.goto(base+P.encode(E.analyze(complete(),catalog).input));await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
await page.evaluate(hash=>location.hash=hash,D.encodeIntent({champion:'Kaisa',position:'BOTTOM'}));await page.waitForSelector('#handoff-preview:not([hidden])');
assert.equal(await page.locator('#handoff-apply').isDisabled(),true);
await page.locator('#input-panel').evaluate(el=>el.open=true);await page.locator('#pick-ENEMY-3').fill('Ashe');
assert.equal(await page.locator('#handoff-apply').isEnabled(),true);
await page.locator('[data-handoff-replace]').check();await page.locator('#handoff-apply').click();await page.waitForFunction(()=>location.hash.startsWith('#plan='));
const input=P.decode(new URL(page.url()).hash).input;assert.equal(input.own_champion,'Kaisa');assert.equal(input.enemies[3].champion,'Ashe');
""")

    def test_return_state_preserves_detail_scroll_and_section(self):
        self.node(r"""
const S=require('./web_r4/champion-state.js'),state=S.clean({champion:'Caitlyn',position:'BOTTOM',scroll:500,detail_scroll:620,section:'skills'});
const intent=D.createIntent({champion:'Caitlyn',position:'BOTTOM',return_state:state});
const restored=S.decode(D.returnLink(intent).split('champion.html')[1]);assert.equal(restored.scroll,500);assert.equal(restored.detail_scroll,620);assert.equal(restored.section,'skills');
for(const return_state of [{detail_scroll:-1},{detail_scroll:Infinity},{section:'unknown'}])assert.throws(()=>D.createIntent({champion:'Caitlyn',position:'BOTTOM',return_state}));
""")

    def test_browser_restored_plan_survives_champion_roundtrip_and_cancel(self):
        self.browser(r"""
const P=require('./web_r4/loading-presentation.js'),S=require('./web_r4/champion-state.js');
const input=E.analyze(complete(),catalog).input;input.schema_version='lol-coach-loading-input-v4';input.scenario=require('./web_r4/loading-coach.js').defaultScenario();input.planning=require('./web_r4/loading-planboard.js').defaults();input.side='RED';input.preferences.risk='LOSS_LIMIT';
const hash=P.encode(input);await page.goto(base+hash);await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
assert.equal(new URL(page.url()).hash,hash);assert.equal(await page.locator('#pick-ALLY-0').inputValue(),'오른');
await page.goto(base.replace('loading.html','champion.html')+S.encode({champion:'Ezreal',position:'BOTTOM'}));await page.waitForSelector('#champion-detail:not([hidden])');
await page.locator('#gameplan-own').click();await page.waitForSelector('#handoff-preview:not([hidden])');
assert.equal(await page.locator('#pick-ALLY-0').inputValue(),'오른');assert.equal(await page.locator('#pick-ALLY-3').inputValue(),'케이틀린');assert.equal(await page.locator('[data-handoff-target]').count(),0);
const before=await page.evaluate(()=>({url:location.href,draft:sessionStorage.getItem('lol-coach-gameplan-draft-v1'),plan:sessionStorage.getItem('lol-coach-loading-plan-v1')}));
await page.locator('#handoff-cancel').click();assert.deepEqual(await page.evaluate(()=>({url:location.href,draft:sessionStorage.getItem('lol-coach-gameplan-draft-v1'),plan:sessionStorage.getItem('lol-coach-loading-plan-v1')})),before);
await page.reload();await page.waitForSelector('#handoff-preview:not([hidden])');await page.locator('[data-handoff-replace]').check();await page.locator('#handoff-apply').click();await page.waitForFunction(()=>location.hash.startsWith('#plan='));
const next=P.decode(new URL(page.url()).hash).input;assert.equal(next.own_champion,'Ezreal');assert.deepEqual(next.allies[0],input.allies[0]);assert.deepEqual(next.enemies,input.enemies);assert.deepEqual(next.scenario,input.scenario);assert.deepEqual(next.planning,input.planning);assert.equal(next.side,'RED');assert.equal(next.preferences.risk,'LOSS_LIMIT');
""")

    def test_browser_back_from_detail_keeps_updated_assumptions(self):
        self.browser(r"""
const P=require('./web_r4/loading-presentation.js');await page.goto(base+P.encode(E.analyze(complete(),catalog).input));await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
await page.locator('[data-plan-area="lane"]').click();await page.locator('summary').filter({hasText:'상황 바꾸기'}).click();await page.locator('[data-coach-focus="quick-KEY_SPENT"]').click();
await page.waitForFunction(()=>JSON.parse(decodeURIComponent(location.hash.slice(6))).input.scenario?.overrides.enemy_key==='SPENT');
await page.goBack();await page.waitForFunction(()=>JSON.parse(decodeURIComponent(location.hash.slice(6))).detail===null);
const route=P.decode(new URL(page.url()).hash);assert.equal(route.input.scenario?.overrides.enemy_key,'SPENT');assert.equal(route.input.schema_version,'lol-coach-loading-input-v4');
""")

    def test_browser_pc_import_invalidates_preview_without_session_storage(self):
        self.browser(r"""
await page.addInitScript(()=>{Storage.prototype.getItem=function(key){return key==='lol-coach-dev-token'?'synthetic-test-token':null;};Storage.prototype.setItem=function(){throw Error('blocked');};});
const input=E.exampleInput(catalog,1),pc={phase:'PRE_GAME',my_champion:input.own_champion,my_position:input.own_position,patch:input.patch,slots:['allies','enemies'].flatMap((team,t)=>input[team].map((p,i)=>({side:t?'ENEMY':'ALLY',slot:i+1,...p})))};
await page.route('**/dev/v1/pregame/pc-status',route=>route.fulfill({json:{connection:{status:'CONNECTED',phase:'ChampSelect',input:pc}}}));
await page.goto(base+D.encodeIntent({champion:'Caitlyn',position:'BOTTOM'}));await page.waitForSelector('#handoff-preview:not([hidden])');await page.locator('[data-handoff-target]').selectOption('allies:3');
await page.locator('#pc-import').click();await page.waitForFunction(()=>location.hash.startsWith('#plan='));
assert.equal(await page.locator('#pick-ALLY-0').inputValue(),'피오라');assert.equal(await page.locator('#handoff-preview').isHidden(),true);
await page.locator('#handoff-apply').evaluate(el=>el.click());assert.ok(new URL(page.url()).hash.startsWith('#plan='));assert.equal(await page.locator('#pick-ALLY-0').inputValue(),'피오라');assert.equal(await page.locator('#pick-ENEMY-0').inputValue(),'말파이트');
""")

    def test_browser_late_pc_import_does_not_replace_newer_form(self):
        self.browser(r"""
await page.addInitScript(()=>sessionStorage.setItem('lol-coach-dev-token','synthetic-test-token'));
const input=E.exampleInput(catalog,1),pc={phase:'PRE_GAME',my_champion:input.own_champion,my_position:input.own_position,patch:input.patch,slots:['allies','enemies'].flatMap((team,t)=>input[team].map((p,i)=>({side:t?'ENEMY':'ALLY',slot:i+1,...p})))};
let held,announce;const pending=new Promise(resolve=>announce=resolve);await page.route('**/dev/v1/pregame/pc-status',async route=>{held=route;announce();});
await page.goto(base);await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);await page.locator('#pc-import').click();await pending;
await page.locator('#example-0').click();assert.equal(await page.locator('#pick-ALLY-0').inputValue(),'오른');
await held.fulfill({json:{connection:{status:'CONNECTED',phase:'ChampSelect',input:pc}}});await page.waitForFunction(()=>!document.querySelector('#pc-import').disabled);
assert.equal(await page.locator('#pick-ALLY-0').inputValue(),'오른');assert.ok(!new URL(page.url()).hash.startsWith('#plan='));
""")

    def test_browser_late_pc_import_does_not_replace_newer_coach_assumptions(self):
        self.browser(r"""
await page.addInitScript(()=>sessionStorage.setItem('lol-coach-dev-token','synthetic-test-token'));
const P=require('./web_r4/loading-presentation.js'),input=E.exampleInput(catalog,1),pc={phase:'PRE_GAME',my_champion:input.own_champion,my_position:input.own_position,patch:input.patch,slots:['allies','enemies'].flatMap((team,t)=>input[team].map((p,i)=>({side:t?'ENEMY':'ALLY',slot:i+1,...p})))};
let held,announce;const pending=new Promise(resolve=>announce=resolve);await page.route('**/dev/v1/pregame/pc-status',async route=>{held=route;announce();});
await page.goto(base+P.encode(E.analyze(complete(),catalog).input));await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);await page.locator('#input-panel').evaluate(el=>el.open=true);await page.locator('#pc-import').click();await pending;
await page.locator('[data-plan-area="lane"]').click();await page.locator('summary').filter({hasText:'상황 바꾸기'}).click();await page.locator('[data-coach-focus="quick-KEY_SPENT"]').click();await page.waitForFunction(()=>JSON.parse(decodeURIComponent(location.hash.slice(6))).input.scenario?.overrides.enemy_key==='SPENT');
await held.fulfill({json:{connection:{status:'CONNECTED',phase:'ChampSelect',input:pc}}});await page.waitForFunction(()=>!document.querySelector('#pc-import').disabled);
const next=P.decode(new URL(page.url()).hash).input;assert.equal(next.own_champion,'Caitlyn');assert.equal(next.scenario?.overrides.enemy_key,'SPENT');
""")

    def test_browser_explicit_plan_priority_and_invalid_restore_preserve_saved_input(self):
        self.browser(r"""
const P=require('./web_r4/loading-presentation.js'),input=E.analyze(complete(),catalog).input,hash=P.encode(input);
await page.goto(base);await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
await page.evaluate(hash=>sessionStorage.setItem('lol-coach-gameplan-draft-v1',hash),D.encodeDraft(D.fromInput({allies:[{champion:'Annie',position:'MID'}],enemies:[]},40)));
await page.goto(base+hash);await page.waitForFunction(()=>!document.querySelector('#analyze').disabled);
assert.equal(new URL(page.url()).hash,hash);const current=await page.evaluate(()=>({draft:sessionStorage.getItem('lol-coach-gameplan-draft-v1'),plan:sessionStorage.getItem('lol-coach-loading-plan-v1')}));
const saved=D.decodeDraft(current.draft);assert.equal(saved.input.allies[0].champion,'Ornn');assert.ok(saved.revision>40);assert.deepEqual(P.decode(current.plan).input,input);
const invalid=structuredClone(input);invalid.enemies[0].champion='Ornn';await page.goto(base+P.encode(invalid));await page.waitForFunction(()=>document.querySelector('#loading-message').classList.contains('is-error'));
assert.deepEqual(await page.evaluate(()=>({draft:sessionStorage.getItem('lol-coach-gameplan-draft-v1'),plan:sessionStorage.getItem('lol-coach-loading-plan-v1')})),current);
""")

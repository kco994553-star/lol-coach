"""Real pure learning-room behavior, including provenance and private return boundaries."""
import json
import pathlib
import subprocess
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]

class LearningFrontendTests(unittest.TestCase):
    def node(self, body):
        prelude = """const assert=require('node:assert/strict'),fs=require('node:fs');assert(fs.existsSync('web_r4/learning-engine.js'),'learning engine is implemented');const E=require('./web_r4/learning-engine.js');
const knowledge={matchups:[{claims:[{id:'A-WAVE',text:'원문 행동',conditions:['필수 조건'],counterexamples:['중단 조건']}]}]};
const data={taxonomy:{groups:[{id:'lane',label:'라인전',topics:[{id:'wave',label:'웨이브',leaves:[{id:'push',label:'선푸시'}]}]}]},sources:[],videos:[],segments:[],lessons:[{lesson_id:'lesson-A',title:'케이틀린 선푸시',question:'왜 기다릴까요?',primary_topic_id:'push',secondary_topic_ids:[],champions:['Caitlyn'],roles:['BOTTOM'],opponents:['Kaisa'],situation_tags:['정글 미확인'],claim_ids:['A-WAVE'],action:{claim_id:'A-WAVE',field:'text'},evidence_state:'CLAIM_REFERENCE',patch_state:'UNKNOWN',source_patches:[],coaching_enabled:false}]};
"""
        result = subprocess.run(['node','-e',prelude+body],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_url_state_whitelist_roundtrip_and_bounded_context(self):
        self.node("""const s=E.stateFromURL('?q=웨이브&leaf=push&champion=Caitlyn&role=BOTTOM&opponent=Kaisa&claim=A-WAVE&lesson=lesson-A&private_match=secret&return=abcdefgh12345678',data,knowledge);assert.equal(s.leaf,'push');assert.equal(s.role,'BOTTOM');assert.equal(s.claim,'A-WAVE');assert(!E.stateToSearch(s).includes('secret'));assert.deepEqual(E.stateFromURL(E.stateToSearch(s),data,knowledge),s);const bad=E.stateFromURL('?champion=../../x&role=FAKE&claim=unknown&topic=nope&q='+('a'.repeat(400)),data,knowledge);assert.equal(bad.champion,'');assert.equal(bad.role,'');assert.equal(bad.claim,'');assert.equal(bad.topic,'nope');assert.equal(bad.q.length,100);assert.equal(bad.invalid,'context');assert.equal(E.filterLessons(data,knowledge,bad).length,0);""")

    def test_invalid_context_never_broadens_after_serialization_and_return_survives(self):
        self.node("""const memory={},storage={getItem:k=>memory[k]||null,setItem:(k,v)=>memory[k]=v},original='./loading.html#plan=private-return',token=E.storeReturn(original,storage);for(const context of [{role:'FAKE'},{role:'../MID'},{champion:'../../x'},{champion:'<script>'},{claim:'unknown'},{claim:'../../A-WAVE'},{group:'../../lane'},{topic:'<bad>'},{leaf:'../push'}]){const first=E.stateFromURL(E.stateToSearch({...context,return:token}),data,knowledge);assert.equal(first.invalid,'context',JSON.stringify(context));assert.equal(E.filterLessons(data,knowledge,first).length,0,JSON.stringify(context));const second=E.stateFromURL(E.stateToSearch(first),data,knowledge);assert.equal(second.invalid,'context');assert.equal(E.filterLessons(data,knowledge,second).length,0);assert.equal(E.restoreReturn(second.return,storage),original);const url=E.createLearningURL(context,{storage,returnURL:original});assert(!url.includes('private-return'));assert.equal(E.filterLessons(data,knowledge,E.stateFromURL(new URL(url,'https://app.test').hash,data,knowledge)).length,0);}const empty=E.stateFromURL(E.stateToSearch({}),data,knowledge);assert.equal(empty.invalid,'');assert.equal(E.filterLessons(data,knowledge,empty).length,1);""")

    def test_filter_search_taxonomy_condition_and_unknown_patch(self):
        self.node("""for(const q of ['선푸시','필수 조건','원문 행동','케이틀린','조건 케이틀린'])assert.equal(E.filterLessons(data,knowledge,{q}).length,1,q);assert.equal(E.filterLessons(data,knowledge,{group:'lane',role:'BOTTOM',opponent:'Kaisa',claim:'A-WAVE',situation:'정글 미확인',patch_state:'UNKNOWN'}).length,1);assert.equal(E.filterLessons(data,knowledge,{role:'TOP'}).length,0);assert.equal(E.filterLessons(data,knowledge,{patch_state:'MISMATCH'}).length,0);assert.equal(E.resolveRef(data.lessons[0].action,knowledge),'원문 행동');assert.equal(E.resolveRef({claim_id:'A-WAVE',field:'__proto__'},knowledge),null);assert.equal(E.resolveRef({claim_id:'absent',field:'text'},knowledge),null);assert.equal(E.taxonomy(data).length,1);""")

    def test_source_urls_reject_injection_and_segments_need_validated_time(self):
        self.node("""for(const url of ['javascript:alert(1)','http://youtube.com/watch?v=abc','https://youtube.com.evil.test/watch?v=abc','https://user:pass@youtube.com/watch?v=abc','https://evil.test','data:text/html,x'])assert.equal(E.safeSourceURL(url),null,url);const video={video_id:'abcdefghijk',canonical_url:'https://www.youtube.com/watch?v=abcdefghijk'};const permitted={video_id:'abcdefghijk',timestamp_state:'VALIDATED',video_start_ms:32000,video_end_ms:45000,access_state:'PERMITTED',license_or_access_state:'PERMITTED',evidence_kind:'TRANSCRIPT',scene_verified:false,transcript_cue_ids:['cue:1'],source_hash:'a'.repeat(64)};assert(E.safeSourceURL(video.canonical_url));assert.equal(E.segmentURL(video,{video_start_ms:32000,timestamp_state:'UNKNOWN'}),null);assert.equal(E.segmentURL(video,{video_start_ms:32000,timestamp_verified:true}),null,'boolean alone cannot manufacture scene verification');assert.equal(E.segmentURL(video,{video_start_ms:-1,timestamp_state:'VALIDATED'}),null);assert.equal(new URL(E.segmentURL(video,permitted)).searchParams.get('t'),'32s');assert.equal(E.segmentURL(video,{...permitted,video_start_ms:45000,video_end_ms:32000}),null);for(const change of [{access_state:'UNKNOWN'},{license_or_access_state:'UNKNOWN'},{source_hash:null},{video_id:'zzzzzzzzzzz'},{evidence_kind:'VISUAL',scene_verified:false},{transcript_cue_ids:[]}])assert.equal(E.segmentURL(video,{...permitted,...change}),null,JSON.stringify(change));""")

    def test_return_token_preserves_private_gameplan_only_in_session(self):
        self.node("""const memory={},storage={getItem:k=>memory[k]||null,setItem:(k,v)=>memory[k]=v};const original='./loading.html?private_match=secret#private-state';const url=E.createLearningURL({champion:'Caitlyn',role:'BOTTOM',claim:'A-WAVE',account:'private'},{storage,returnURL:original});assert(!url.includes('secret'));assert(!url.includes('private'));assert(url.includes('#learn='));const token=new URLSearchParams(new URL(url,'https://app.test/').hash.slice(7)).get('return');assert(token);assert.equal(E.restoreReturn(token,storage),original);const review=E.storeReturn('/lol-coach/dashboard.html#review-private',storage);assert(review);assert.equal(E.restoreReturn(review,storage),'/lol-coach/dashboard.html#review-private');assert.equal(E.restoreReturn('invalid',storage),null);assert.equal(E.storeReturn('https://evil.test/steal',storage),null);assert.equal(E.storeReturn('//evil.test/loading.html',storage),null);assert.equal(E.storeReturn('./loading.html\\nfoo',storage),null);assert.doesNotThrow(()=>E.createLearningURL({champion:'Caitlyn'},{storage:{setItem(){throw Error('blocked')}},returnURL:original}));""")

    def test_source_patch_filter_is_independent_of_patch_state(self):
        self.node("""data.lessons[0].source_patches=['9.14'];data.lessons[0].patch_state='DECLARED_UNVERIFIED';assert.equal(E.filterLessons(data,knowledge,{patch:'9.14',patch_state:'DECLARED_UNVERIFIED'}).length,1);assert.equal(E.filterLessons(data,knowledge,{patch:'16.20'}).length,0);assert.equal(E.filterLessons(data,knowledge,{patch_state:'UNKNOWN'}).length,0);const state=E.stateFromURL('#learn=patch=9.14&patch_state=DECLARED_UNVERIFIED',data,knowledge);assert.equal(state.patch,'9.14');assert.equal(state.patch_state,'DECLARED_UNVERIFIED');""")

    def test_actual_taxonomy_dotted_ids_and_fragment_state(self):
        self.node("""const real=JSON.parse(fs.readFileSync('web_r4/learning-room.json','utf8')),k=JSON.parse(fs.readFileSync('web_r4/loading-knowledge.json','utf8'));assert.equal(E.taxonomy(real).length,80);const s=E.stateFromURL('#learn=leaf=topic%3A1.1.1&patch_state=DECLARED_UNVERIFIED',real,k);assert.equal(s.leaf,'topic:1.1.1');assert.equal(s.group,'topic:1');assert.equal(s.topic,'topic:1.1');assert.equal(s.patch_state,'DECLARED_UNVERIFIED');assert(E.filterLessons(real,k,s).length>0);""")

    def test_url_normalizes_known_identity_and_preserves_unknown_filter_constraints(self):
        self.node("""const real=JSON.parse(fs.readFileSync('web_r4/learning-room.json','utf8')),k=JSON.parse(fs.readFileSync('web_r4/loading-knowledge.json','utf8'));const state=E.stateFromURL(E.stateToSearch({champion:'caitlyn',role:'bottom'}),real,k);assert.equal(state.champion,'Caitlyn');assert.equal(state.role,'BOTTOM');assert.equal(E.filterLessons(real,k,state).length,8);assert.equal(E.filterLessons(real,k,{champion:'caitlyn'}).length,8);for(const field of ['patch','patch_state','evidence','group','topic','leaf','situation','champion','opponent']){const unknown=E.stateFromURL(E.stateToSearch({[field]:'unregistered'}),real,k);assert.equal(unknown[field],'unregistered',field);assert.equal(E.filterLessons(real,k,unknown).length,0,field);}assert.equal(E.filterLessons(real,k,E.stateFromURL('#learn=patch=DECLARED_UNVERIFIED',real,k)).length,0);knowledge.matchups[0].claims[0].alternative_or_recovery='명시적 회복 원문';assert.equal(E.resolveRef({claim_id:'A-WAVE',field:'alternative_or_recovery'},knowledge),'명시적 회복 원문');""")

    def test_source_patch_labels_with_spaces_survive_url_roundtrip(self):
        self.node("""const real=JSON.parse(fs.readFileSync('web_r4/learning-room.json','utf8'));const patch='12.1 / Season 12';const state=E.stateFromURL(E.stateToSearch({patch}),real,knowledge);assert.equal(state.patch,patch);assert(E.filterLessons(real,knowledge,state).length>0);""")

    def test_python_and_browser_search_projection_match_real_registry(self):
        from coach_v1.learning_room import search_index
        data=json.loads((ROOT/'web_r4/learning-room.json').read_text())
        knowledge=json.loads((ROOT/'web_r4/loading-knowledge.json').read_text())
        cases=[{'q':q} for q in ('','미니언','정글','조건 케이틀린','위협 먼저','Ａ－ＷＡＶＥ','A-WAVE','웨이브 관리','귀환 합류','unknown-no-result')]
        cases += [{'patch':p} for p in sorted({p for l in data['lessons'] for p in l['source_patches']})]
        cases += [{'champion':'caitlyn'},{'opponent':'kaisa'},{'role':'bottom'},{'evidence':'source_reference'},{'patch_state':'unknown'},{'patch':'DECLARED_UNVERIFIED'},{'group':'unregistered'},{'patch_state':'unregistered'},{'patch_state':'UNKNOWN'},{'patch_state':'DECLARED_UNVERIFIED'},{'role':'BOTTOM','opponent':'Kaisa','q':'조건'},{'leaf':'topic:1.1.1'},{'group':'topic:2'},{'leaf':'UNCLASSIFIED'},{'evidence':'LINK_ONLY'}]
        script="const E=require('./web_r4/learning-engine.js'),d=require('./web_r4/learning-room.json'),k=require('./web_r4/loading-knowledge.json');const cases="+json.dumps(cases)+";console.log(JSON.stringify(cases.map(s=>[E.filterLessons(d,k,s).map(l=>l.lesson_id),E.filterLessons(d,k,E.stateFromURL(E.stateToSearch(s),d,k)).map(l=>l.lesson_id)])))"
        result=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True,check=True)
        browser=json.loads(result.stdout)
        for state,actual in zip(cases,browser):
            args={}
            for key,value in state.items():
                if key=='q':continue
                args[{'leaf':'topic_id','group':'topic_id','topic':'topic_id','evidence':'evidence_state'}.get(key,key)]=value
            expected=search_index(data,state.get('q',''),knowledge=knowledge,**args)
            for result_path in actual:
                self.assertEqual(result_path,[l['lesson_id']for l in expected['lessons']],state)

    def test_html_has_accessible_independent_learning_and_existing_scene_link(self):
        html=(ROOT/'web_r4/learning.html').read_text() if (ROOT/'web_r4/learning.html').exists() else ''
        for text in ('id="learning-status"','aria-live="polite"','id="learning-search"','id="learning-results"','./directions.html','./learning-engine.js','./learning.js'):
            self.assertIn(text,html)

if __name__=='__main__': unittest.main()

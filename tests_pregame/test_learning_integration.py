"""Public learning projection and private search preserve existing boundaries."""
import http.client
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

from scripts.build_directions_web import FILES, ROOT
from scripts.launch_pc import create_server


class LearningIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.server = create_server(Path(cls.temp.name) / 'private', port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()
        cls.temp.cleanup()

    def request(self, method, path, value=None, authorized=False):
        headers = {'Content-Type': 'application/json'}
        if authorized:
            headers['Authorization'] = 'Bearer ' + self.server.token
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=15)
        conn.request(method, path, json.dumps(value) if value is not None else None, headers)
        response = conn.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        conn.close()
        return result

    def test_new_projection_is_explicit_and_private_routes_stay_private(self):
        for name in ('learning.html', 'learning.css', 'learning.js', 'learning-engine.js', 'learning-room.json', 'loading-situation.js'):
            with self.subTest(name=name):
                self.assertIn(name, FILES)
                status, body, headers = self.request('GET', '/' + name)
                self.assertEqual(status, 200)
                self.assertEqual(body, (ROOT / 'web_r4' / name).read_bytes())
                self.assertIn("script-src 'self'", headers['Content-Security-Policy'])
                self.assertEqual(self.request('GET', '/' + name + '?token=bad')[0], 400)
        self.assertEqual(self.request('GET', '/dev/v1/pregame/pc-status')[0], 401)
        for name in ('config/user_lesson_candidates.json', 'private/notes.json', 'coach_v1/learning_room.py'):
            self.assertIn(self.request('GET', '/' + name)[0], (401, 404))

    def test_search_api_requires_auth_and_matches_static_projection(self):
        self.assertEqual(self.request('POST', '/dev/v1/learning/search', {})[0], 401)
        status, body, _ = self.request('POST', '/dev/v1/learning/search', {'query': '웨이브', 'role': 'BOTTOM'}, True)
        self.assertEqual(status, 200)
        from coach_v1.learning_room import search_index
        index = json.loads((ROOT / 'web_r4/learning-room.json').read_text())
        self.assertEqual(json.loads(body), search_index(index, '웨이브', role='BOTTOM', knowledge=json.loads((ROOT / 'web_r4/loading-knowledge.json').read_text())))
        self.assertEqual(len(self.server.research.list()), 0)

    def test_search_rejects_unknown_private_and_unbounded_input(self):
        for value in ({'riot_id': 'private-value'}, {'query': 'a' * 101}, {'role': 'ADC'}, {'limit': True}, {'limit': 501}, {'offset': -1}, {'topic_id': '../private'}):
            self.assertEqual(self.request('POST', '/dev/v1/learning/search', value, True)[0], 422, value)
        self.assertEqual(self.request('POST', '/dev/v1/learning/search?token=bad', {}, True)[0], 400)

    def test_search_api_uses_real_source_labels_and_role_normalization(self):
        from coach_v1.learning_room import search_index
        index = json.loads((ROOT / 'web_r4/learning-room.json').read_text())
        knowledge = json.loads((ROOT / 'web_r4/loading-knowledge.json').read_text())
        for value in ({'role': 'bottom'}, {'patch': '12.1 / Season 12'}, {'query': '같은 레벨'}, {'patch_state': 'DECLARED_UNVERIFIED'}):
            with self.subTest(value=value):
                status, body, _ = self.request('POST', '/dev/v1/learning/search', value, True)
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body), search_index(index, knowledge=knowledge, **value))

    def test_existing_learning_and_context_entrypoints_are_retained(self):
        shell = (ROOT / 'web_r4/coach-shell.js').read_text()
        self.assertIn("'./learning.html'", shell)
        directions = (ROOT / 'web_r4/directions.html').read_text()
        self.assertIn('id="scenes"', directions)
        self.assertIn('loading-study.js', directions)
        self.assertIn('./learning.html', directions)
        for name in ('champion.html', 'dashboard.html'):
            self.assertIn('./learning-engine.js', (ROOT / 'web_r4' / name).read_text())
        self.assertIn('LearningRoom.createLearningURL', (ROOT / 'web_r4/champion-page.js').read_text())
        self.assertIn('LearningRoom.createLearningURL', (ROOT / 'web_r4/dashboard.js').read_text())


class SituationDraftCompatibilityTests(unittest.TestCase):
    def test_partial_transfer_preserves_v5_and_rejects_other_schema_extras(self):
        source = r"""
const assert=require('node:assert/strict'),D=require('./web_r4/loading-draft.js'),E=require('./web_r4/loading-engine.js'),C=require('./web_r4/loading-coach.js'),P=require('./web_r4/loading-planboard.js'),c=require('./web_r4/loading-data.json');
const situation=require('./web_r4/loading-situation.js').defaultState(),fields=situation.fields;
const raw={...E.exampleInput(c),schema_version:'lol-coach-loading-input-v5',preferences:{risk:'BALANCED'},scenario:C.defaultScenario(),planning:P.defaults(),situation};
const d=D.fromInput(raw), before=JSON.stringify(d), preview=D.previewTransfer({champion:'Ezreal',position:'BOTTOM'},d);
const next=D.applyTransfer(preview,{replacements:['allies:3']},d.revision);
assert.equal(JSON.stringify(d),before);assert.deepEqual(next.input.situation,raw.situation);assert.deepEqual(next.input.planning,raw.planning);assert.deepEqual(next.input.scenario,raw.scenario);assert.equal(next.input.schema_version,'lol-coach-loading-input-v5');assert.equal(D.toCompleteInput(next).own_champion,'Ezreal');assert.deepEqual(D.decodeDraft(D.encodeDraft(next)),next);
assert.throws(()=>D.fromInput({...raw,schema_version:'lol-coach-loading-input-v4'}));
assert.throws(()=>D.fromInput({...raw,situation:{...raw.situation,fields:{...fields,enemy_position:'TOP'}}}));
"""
        result = subprocess.run(['node', '-e', source], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr[-6000:])

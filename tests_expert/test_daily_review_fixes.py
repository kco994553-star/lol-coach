"""Independent review counterexamples; no real provider/metadata calls."""
from copy import deepcopy
import json,os,tempfile,unittest
from unittest.mock import patch
from tests_expert import test_gemini_daily as fixtures
from scripts import run_gemini_daily as cli

class ReviewFixTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.DailyTests();self.f.setUp();self.d=self.f.m
    def response(self,value):
        return dict(candidates=[dict(finishReason='STOP',content=dict(parts=[dict(text=json.dumps(value))]))])
    def test_empty_expert_and_pov_are_not_nonempty_extractions(self):
        source=self.f.source()
        output=self.d.safe_video_output(self.response({'claims':[]}),source)
        self.assertFalse(output['valid_extraction']);self.assertEqual(output['extraction_status'],'EMPTY')
        source['purpose']='POV_OBSERVATION'
        output=self.d.safe_video_output(self.response({'observations':[]}),source)
        self.assertFalse(output['valid_extraction'])
    def test_wrong_schema_is_malformed_not_empty(self):
        with self.assertRaises(ValueError):self.d.safe_video_output(self.response({'not_claims':'text'}),self.f.source())
    def test_rejected_or_outside_interval_has_no_valid_extraction(self):
        for claims in [[{'timestamp':'00:01'}],[dict(timestamp='10:00',paraphrase='test',champion='UNKNOWN',position='UNKNOWN',stage='UNKNOWN',conditions=[],context='EXPLANATION',measurable=False)]]:
            output=self.d.safe_video_output(self.response({'claims':claims}),self.f.source())
            self.assertFalse(output['valid_extraction'])
    def test_preparation_permission_payment_arguments_block_next_day_but_not_quota(self):
        completed=self.d.complete(self.f.reserve(),'TEXT',self.f.now,200)
        for status in [401,403,402,400,429]:
            state=self.d.preparation_failure(completed,self.f.config,self.f.now,'42','VIDEO_METADATA',status)
            if status!=429:
                with self.assertRaisesRegex(ValueError,'PERSISTENT_CONFIGURATION_BLOCK'):
                    self.f.reserve(state,now=self.f.now+86400)
            else:self.assertEqual(len(self.f.reserve(state,now=self.f.now+86400)['events']),4)
    def test_ack_rejects_nonexistent_wrong_run_wrong_state_before_dispatch(self):
        state=self.f.reserve();q=self.f.ledger
        run=dict(id=42,run_attempt=1,status='in_progress',head_branch='main',event='workflow_dispatch',path='.github/workflows/expert-video-collection.yml')
        artifact=dict(id=7,name='gemini-daily-state-42-TEXT',expired=False,workflow_run=dict(id=42))
        def invoke(a=artifact,s=state):
            return cli.verify_ack('7','TEXT',state,q,'42',api=lambda p:deepcopy(run if '/actions/runs/' in p else a),download_pair=lambda a:(s,q))
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':'kco994553-star/lol-coach'}):
            self.assertTrue(invoke())
            for wrong in [dict(artifact,id=8),dict(artifact,workflow_run=dict(id=43)),dict(artifact,name='unrelated'),dict(artifact,expired=True)]:
                with self.assertRaises(ValueError):invoke(wrong)
            bad=deepcopy(state);bad['events']=[]
            with self.assertRaises(ValueError):invoke(s=bad)
    def test_claim_root_does_not_change_with_output_or_runner_temp(self):
        with patch.dict(os.environ,{'RUNNER_TEMP':'/tmp/a'}):a=cli.claim_root('42')
        with patch.dict(os.environ,{'RUNNER_TEMP':'/tmp/b'}):b=cli.claim_root('42')
        self.assertEqual(a,b)

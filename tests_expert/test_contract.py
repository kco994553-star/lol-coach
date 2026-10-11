import copy
import importlib
import unittest


def model_claim(**changes):
    return dict(dict(timestamp='01:30',paraphrase='TEST conditional expert paraphrase',champion='Caitlyn',
        position='BOTTOM',stage='LATE',conditions=['TEST visible condition'],context='EXPLANATION',measurable=False),**changes)


def artifact():
    return dict(schema_version='expert.claims.v1',video=dict(id='abcdefghijk',url='https://www.youtube.com/watch?v=abcdefghijk',
        title='TEST video',channel_id=None,channel_name='TEST channel',speaker='UNKNOWN',speaker_verified=False,
        published_at=None,upload_date=None,duration_seconds=600,language='ko'),
        processing=dict(method='MANUAL_SUMMARY',model='UNKNOWN',processed_at='2026-10-11T00:00:00Z',input_sha256='a'*64),
        claims=[dict(model_claim(),timestamp_seconds=90,patch_range='UNKNOWN',counterexamples=['TEST exception'],
            limitations=['TEST unverified source'],measurement=None,independent_group_id='YOUTUBE:abcdefghijk')],
        rejections=[],visual_verified=False,coaching_accuracy=None)


class ExpertContractTests(unittest.TestCase):
    def setUp(self):self.module=importlib.import_module('coach_v1.expert_contract')

    def test_valid_copy_does_not_mutate_and_manual_is_not_video_verification(self):
        original=artifact();result=self.module.validate_expert_artifact(original)
        self.assertEqual(result,original);result['claims'][0]['paraphrase']='changed'
        self.assertNotEqual(result,original);self.assertFalse(original['visual_verified'])

    def test_exact_keys_privacy_utf8_and_nonfinite_rejected(self):
        for mutate in [lambda a:a.update(transcript='PRIVATE'),lambda a:a['video'].update(puuid='PRIVATE'),
                       lambda a:a['claims'][0].update(quote='PRIVATE'),lambda a:a['processing'].update(api_key='PRIVATE'),
                       lambda a:a['claims'][0].update(paraphrase='\ud800'),lambda a:a.update(coaching_accuracy=.9),
                       lambda a:a.update(visual_verified=True),lambda a:a['claims'][0].update(measurable=1),
                       lambda a:a['claims'][0].update(paraphrase='x'*501)]:
            bad=artifact();mutate(bad)
            with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)

    def test_timestamps_required_canonical_consistent_inside_duration(self):
        for timestamp in [None,'1:30','01:60','-01:30','00:00:30','10:00']:
            bad=artifact();bad['claims'][0]['timestamp']=timestamp
            with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)
        bad=artifact();bad['claims'][0]['timestamp_seconds']=91
        with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)
        bad=artifact();bad['claims'][0].pop('timestamp')
        with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)
        good=artifact();good['video']['duration_seconds']=7200
        good['claims'][0].update(timestamp='65:01',timestamp_seconds=3901)
        self.module.validate_expert_artifact(good)

    def test_identity_dates_speaker_and_duplicates_are_explicit(self):
        for mutate in [lambda a:a['video'].update(url='https://youtu.be/abcdefghijk'),
                       lambda a:a['video'].update(id='../unsafe'),lambda a:a['video'].update(channel_id='invalid'),
                       lambda a:a['video'].update(speaker='Named but unverified'),
                       lambda a:a['video'].update(published_at='2026-10-11T00:00:00+09:00'),
                       lambda a:a['video'].update(upload_date='2026-02-30'),
                       lambda a:a['processing'].update(model='invented'),
                       lambda a:a['claims'][0].update(independent_group_id='YOUTUBE:other'),
                       lambda a:a['claims'].append(copy.deepcopy(a['claims'][0]))]:
            bad=artifact();mutate(bad)
            with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)
        good=artifact();good['video'].update(speaker='TEST attested speaker',speaker_verified=True,upload_date='2026-10-10')
        self.module.validate_expert_artifact(good)

    def test_measurement_numeric_criterion_only_and_scope_bounded(self):
        good=artifact();good['claims'][0]['measurement']=dict(kind='MOVEMENT_MEAN_DISTANCE',cohort_id='b'*64,
            patch='16.19',tier='GOLD',minute=25,operator='LE',threshold=200.0,
            criterion_source_url='https://example.org/criterion',rationale='TEST explicit criterion',origin='MANUAL')
        self.module.validate_expert_artifact(good)
        for changes in [dict(threshold=float('nan')),dict(threshold=-1),dict(minute=True),dict(operator='EQ'),
                        dict(criterion_source_url='https://secret:password@example.org/x'),dict(origin='AI')]:
            bad=copy.deepcopy(good);bad['claims'][0]['measurement'].update(changes)
            with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)

    def test_empty_or_operationally_oversized_artifacts_fail(self):
        for claims in [[],[artifact()['claims'][0]]*101]:
            bad=artifact();bad['claims']=claims
            with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)
        bad=artifact();bad['rejections']=[dict(index=0,reason='INVALID_CLAIM')]*101
        with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)
        bad=artifact();bad['rejections']=[dict(index=0,reason='RAW_PRIVATE_ERROR')]
        with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)
        bad=artifact();bad['claims']=[]
        for i in range(60):
            c=copy.deepcopy(artifact()['claims'][0]);c.update(timestamp=f'{i//60:02d}:{i%60:02d}',timestamp_seconds=i,
                paraphrase='가'*500,conditions=['가'*200]*10)
            bad['claims'].append(c)
        with self.assertRaises(ValueError):self.module.validate_expert_artifact(bad)

    def test_automatic_uploader_never_attests_segment_speaker(self):
        automatic=artifact();automatic['processing'].update(method='GEMINI_YOUTUBE',model='gemini-3.8-flash')
        automatic['video']['channel_id']='UC'+'a'*22
        self.module.validate_expert_artifact(automatic)
        automatic['video'].update(speaker='TEST uploader',speaker_verified=True)
        with self.assertRaises(ValueError):self.module.validate_expert_artifact(automatic)
        automatic['video'].update(speaker='UNKNOWN',speaker_verified=False,channel_id=None)
        with self.assertRaises(ValueError):self.module.validate_expert_artifact(automatic)

    def test_normalizer_nonfinite_utf8_unknown_fields_and_oversize_fail_safely(self):
        for value in [dict(claims=[model_claim(paraphrase='\ud800')]),dict(claims=[model_claim(measurable=float('nan'))]),
                      dict(claims=[model_claim()]*101),dict(claims=[model_claim(paraphrase='x'*501)]),
                      dict(claims=[model_claim(paraphrase='AIza'+'x'*35)])]:
            claims,rejections=self.module.normalize_gemini_claims(value,600)
            self.assertEqual(claims,[]);self.assertTrue(rejections)
            self.assertTrue(all(r['reason'] in self.module.REJECTION_REASONS for r in rejections))
        for duration in [None,True,0,28801]:
            self.assertEqual(self.module.normalize_gemini_claims(dict(claims=[model_claim()]),duration)[0],[])

    def test_normalizer_strictly_separates_summary_from_fact_and_predicate(self):
        claims,rejections=self.module.normalize_gemini_claims(dict(claims=[model_claim()]),600)
        self.assertEqual(rejections,[]);self.assertEqual(len(claims),1)
        c=claims[0];self.assertEqual(c['timestamp_seconds'],90);self.assertNotIn('independent_group_id',c)
        self.assertEqual(c['patch_range'],'UNKNOWN');self.assertIsNone(c['measurement'])
        self.assertEqual(c['limitations'],['AI_SUMMARY_NOT_FACT_CHECKED','VIDEO_CONTEXT_REQUIRES_USER_REVIEW'])
        self.assertEqual(c['counterexamples'],['COUNTEREXAMPLE_NOT_ESTABLISHED'])

    def test_normalizer_missing_timestamp_duplicates_and_out_of_range_safe_reasons(self):
        missing=model_claim();missing.pop('timestamp')
        inputs=[model_claim(),model_claim(),missing,model_claim(timestamp='10:00'),model_claim(quote='PRIVATE')]
        claims,rejections=self.module.normalize_gemini_claims(dict(claims=inputs),600)
        self.assertEqual(len(claims),1)
        self.assertEqual({r['reason'] for r in rejections},{'DUPLICATE_CLAIM','INVALID_TIMESTAMP','OUT_OF_RANGE_TIMESTAMP','INVALID_CLAIM'})
        for value in [None,{},dict(claims=[]),dict(claims=[missing]),dict(claims=[model_claim()],transcript='PRIVATE')]:
            claims,rejections=self.module.normalize_gemini_claims(value,600)
            self.assertEqual(claims,[]);self.assertTrue(rejections)
            self.assertTrue(all(set(r)=={'index','reason'} for r in rejections));self.assertNotIn('PRIVATE',str(rejections))


if __name__=='__main__':unittest.main()

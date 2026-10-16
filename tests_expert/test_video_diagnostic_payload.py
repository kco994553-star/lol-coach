"""Offline diagnostic payload contracts; no provider or media access."""
import copy
import importlib
import importlib.util
import json
import unittest


MODULE = 'coach_v1.video_diagnostic_payload'
m = importlib.import_module(MODULE) if importlib.util.find_spec(MODULE) else None


def source(stage=1, duration=360):
    video_id = 'ixRanV-rdAQ' if stage == 1 else 'brQaUDGnXTs'
    return dict(schema_version='evidence.source-plan.v2', purpose='VIDEO_API_DIAGNOSTIC',
        video=dict(id=video_id, url='https://www.youtube.com/watch?v=' + video_id,
            title='TEST public video', channel_id='UC' + 'a' * 22, channel_name='TEST channel',
            speaker='UNKNOWN', speaker_verified=False, published_at='2026-10-01T00:00:00Z',
            upload_date=None, duration_seconds=duration, language='UNKNOWN'),
        start_seconds=0, end_seconds=duration if stage < 3 else min(120, duration),
        diagnostic=dict(session='video-api-20261017', stage=stage, revision='TEST-r1', reference_sha256='a' * 64))


def answer(text=None, finish='STOP'):
    if text is None:
        text = ('At 00:05 a presenter opens the presentation. '
                'At 00:15 the screen displays a demonstration. '
                'At 00:30 the presenter discusses the visible results.')
    return dict(candidates=[dict(finishReason=finish, content=dict(role='model', parts=[dict(text=text)]))])


def structured():
    return dict(summary='A presentation shows a demonstration and its visible results.', observations=[
        dict(timestamp='00:05', detail='A presenter opens the presentation.'),
        dict(timestamp='00:15', detail='The screen displays a demonstration.')])


class VideoDiagnosticPayloadTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(m, 'diagnostic payload module must implement the offline contract')

    def test_source_is_strict_detached_and_keeps_original_duration(self):
        value = source()
        result = m.validate_source(value)
        self.assertEqual(result, value)
        result['video']['title'] = 'changed'
        self.assertEqual(value['video']['title'], 'TEST public video')
        for stage in range(1, 5):
            for duration in (80, 360, 1200):
                with self.subTest(stage=stage, duration=duration):
                    result = m.validate_source(source(stage, duration))
                    self.assertEqual(result['video']['duration_seconds'], duration)
                    self.assertEqual(result['end_seconds'], duration if stage < 3 else min(120, duration))

    def test_invalid_source_fails_closed(self):
        changes = [lambda s: s.update(purpose='OTHER'), lambda s: s.update(extra=True),
            lambda s: s.update(start_seconds=True), lambda s: s.update(end_seconds=120),
            lambda s: s['video'].update(speaker_verified=True),
            lambda s: s['video'].update(url='https://youtu.be/ixRanV-rdAQ'),
            lambda s: s['diagnostic'].update(stage=True), lambda s: s['diagnostic'].update(stage=0),
            lambda s: s['diagnostic'].update(stage=5), lambda s: s['diagnostic'].update(extra=True),
            lambda s: s['diagnostic'].update(session='another-session'),
            lambda s: s['diagnostic'].update(revision=' '), lambda s: s['diagnostic'].update(revision='x' * 81),
            lambda s: s['diagnostic'].update(reference_sha256='x' * 64),
            lambda s: s['video'].update(duration_seconds=0)]
        for change in changes:
            value = source(); change(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.validate_source(value)
        for value in (None, [], 'bad', source(2, 120)):
            if isinstance(value, dict): value['video'] = source()['video']
            with self.subTest(value=value), self.assertRaises(ValueError): m.validate_source(value)
        for stage in (3, 4):
            value = source(stage); value['end_seconds'] = 360
            with self.assertRaises(ValueError): m.validate_source(value)

    def test_body_sequence_changes_exactly_url_then_offsets_then_json_config(self):
        bodies = [m.build_body(source(stage)) for stage in range(1, 5)]
        baseline = dict(contents=[dict(parts=[dict(text=m.PROMPT), dict(fileData=dict(
            fileUri='https://www.youtube.com/watch?v=ixRanV-rdAQ'))])])
        self.assertEqual(m.PURPOSE, 'VIDEO_API_DIAGNOSTIC')
        self.assertEqual(m.SESSION, 'video-api-20261017')
        self.assertEqual(m.PROMPT, 'Summarize this video in three sentences and include timestamps for concrete details.')
        self.assertEqual(bodies[0], baseline)
        expected = copy.deepcopy(baseline)
        expected['contents'][0]['parts'][1]['fileData']['fileUri'] = 'https://www.youtube.com/watch?v=brQaUDGnXTs'
        self.assertEqual(bodies[1], expected)
        expected['contents'][0]['parts'][1]['videoMetadata'] = dict(startOffset='0s', endOffset='120s')
        self.assertEqual(bodies[2], expected)
        expected['generationConfig'] = dict(responseMimeType='application/json', responseJsonSchema=m.SIMPLE_SCHEMA)
        self.assertEqual(bodies[3], expected)
        self.assertEqual(m.build_body(source(3, 80))['contents'][0]['parts'][1]['videoMetadata']['endOffset'], '80s')
        bodies[3]['generationConfig']['responseJsonSchema']['properties'].clear()
        self.assertTrue(m.SIMPLE_SCHEMA['properties'])

    def test_schema_is_small_strict_and_uses_only_documented_keywords(self):
        allowed = {'type', 'properties', 'required', 'additionalProperties', 'items', 'minItems', 'maxItems'}
        def check(schema):
            self.assertLessEqual(set(schema), allowed)
            for child in schema.get('properties', {}).values(): check(child)
            if 'items' in schema: check(schema['items'])
        check(m.SIMPLE_SCHEMA)
        schema = m.SIMPLE_SCHEMA
        self.assertEqual(schema['additionalProperties'], False)
        self.assertEqual(set(schema['required']), {'summary', 'observations'})
        observations = schema['properties']['observations']
        self.assertIn(observations['maxItems'], (3, 4, 5))
        self.assertEqual(observations['items']['additionalProperties'], False)
        self.assertEqual(set(observations['items']['required']), {'timestamp', 'detail'})

    def test_plain_response_is_bounded_unreviewed_content_not_extraction(self):
        for stage in (1, 2, 3):
            result = m.evaluate_response(json.dumps(answer()).encode(), source(stage))
            self.assertEqual(result, dict(evidence_status='DIAGNOSTIC_ONLY_UNREVIEWED',
                blind_evaluation_eligible=False, input_isolation=(
                    'FULL_VIDEO_DIAGNOSTIC_EXCLUDED_FROM_EVALUATION' if stage < 3 else 'API_OFFSETS_REQUESTED_UNPROVEN'),
                diagnostic_content=dict(stage=stage, content_candidate_valid=True,
                    notes=[
                        'At 00:05 a presenter opens the presentation.',
                        'At 00:15 the screen displays a demonstration.',
                        'At 00:30 the presenter discusses the visible results.'], source_review='NOT_REVIEWED'),
                valid_extraction=False))
        response = answer('At 00:05 ' + 'visible words ' * 100 + '. Another visible detail. Third visible detail. Fourth omitted.')
        result = m.evaluate_response(response, source())
        notes = result['diagnostic_content']['notes']
        self.assertEqual(len(notes), 3)
        self.assertTrue(all(len(note) <= 300 for note in notes))
        self.assertNotIn('Fourth omitted', json.dumps(result))

    def test_invalid_or_refusal_response_fails_closed(self):
        invalid = [None, [], 'broken', b'\xff', dict(candidates=[]), answer('', 'STOP'),
            answer('x' * 39), answer(finish='MAX_TOKENS'),
            answer('I cannot access or watch this video. Please provide a transcript to summarize.'),
            answer("I'm sorry, but I cannot help with this request. Please share a transcript instead."),
            answer('The video is unavailable and I am unable to view its contents directly.'),
            answer('0' * 100), dict(answer(), promptFeedback=dict(blockReason='SAFETY'))]
        blocked = answer(); blocked['candidates'][0]['safetyRatings'] = [dict(blocked=True)]; invalid.append(blocked)
        multi = answer(); multi['candidates'] *= 2; invalid.append(multi)
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError): m.evaluate_response(value, source())

    def test_thought_and_signature_are_never_retained(self):
        raw = answer()
        raw['candidates'][0]['content']['parts'].insert(0, dict(text='PRIVATE_THOUGHT', thought=True, thoughtSignature='PRIVATE_SIGNATURE'))
        raw['candidates'][0]['content']['parts'][1]['thoughtSignature'] = 'PRIVATE_FINAL_SIGNATURE'
        result = m.evaluate_response(raw, source())
        for marker in ('PRIVATE_', 'thought', 'signature', 'claims', 'speaker_verified'):
            self.assertNotIn(marker, json.dumps(result))

    def test_stage4_checks_exact_json_shape_and_local_bounds(self):
        result = m.evaluate_response(answer(json.dumps(structured())), source(4))
        self.assertEqual(result['diagnostic_content']['notes'], [structured()['summary']] + [
            row['timestamp'] + ': ' + row['detail'] for row in structured()['observations']])
        self.assertEqual(result['input_isolation'], 'API_OFFSETS_REQUESTED_UNPROVEN')
        invalid = [dict(structured(), claims=[]), dict(summary='ok', observations=[]),
            dict(summary='x' * 301, observations=structured()['observations']),
            dict(summary=True, observations=structured()['observations']),
            dict(summary='A summary.', observations=[dict(timestamp='00:05', detail='x' * 301)]),
            dict(summary='A summary.', observations=[dict(timestamp='02:00', detail='outside interval')]),
            dict(summary='A summary.', observations=[dict(timestamp='bad', detail='A detail.')]),
            dict(summary='A summary.', observations=[dict(timestamp='00:05', detail='A detail.', extra=True)]),
            dict(summary='A summary.', observations=structured()['observations'] * 3)]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.evaluate_response(answer(json.dumps(value)), source(4))
        for text in ('```json\n' + json.dumps(structured()) + '\n```',
                     '{"summary":"duplicate","summary":"duplicate","observations":[]}', '[]', 'null'):
            with self.assertRaises(ValueError): m.evaluate_response(answer(text), source(4))

    def test_error_details_preserve_only_typed_safe_fields(self):
        raw = dict(error=dict(code=400, status='INVALID_ARGUMENT', message='PRIVATE_PERSON TEST_SECRET test@example.com', details=[
            {'@type':'type.googleapis.com/google.rpc.BadRequest', 'fieldViolations':[
                dict(field='contents[0].parts[1].videoMetadata.endOffset', description='Invalid value TEST_SECRET test@example.com'),
                dict(field='PRIVATE_PERSON', description='PRIVATE_PERSON TEST_SECRET')]},
            {'@type':'type.googleapis.com/google.rpc.ErrorInfo', 'reason':'API_KEY_INVALID',
             'domain':'googleapis.com', 'metadata':dict(key='TEST_SECRET')},
            {'@type':'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay':'15s'},
            {'@type':'PRIVATE_TYPE_TEST_SECRET', 'payload':'TEST_SECRET PRIVATE_PERSON'}]))
        result = m.safe_error_details(raw, secrets=('TEST_SECRET',))
        self.assertEqual(result['error_status'], 'INVALID_ARGUMENT')
        self.assertEqual(result['rejected_field'], 'contents[0].parts[1].videoMetadata.endOffset')
        self.assertEqual(result['error_details'][0]['fieldViolations'][0], dict(
            field='contents[0].parts[1].videoMetadata.endOffset', description_category='INVALID_VALUE'))
        self.assertEqual(result['error_details'][0]['fieldViolations'][1]['field'], 'UNKNOWN')
        self.assertEqual(result['error_details'][1], dict(type='google.rpc.ErrorInfo', reason='API_KEY_INVALID', domain='googleapis.com'))
        self.assertEqual(result['error_details'][2], dict(type='google.rpc.RetryInfo', retryDelay='15s'))
        self.assertEqual(result['error_details'][3], dict(type='UNKNOWN', count=1, redacted=True))
        for marker in ('TEST_SECRET', 'PRIVATE_PERSON', 'test@example.com', 'PRIVATE_TYPE', 'payload', 'metadata'):
            self.assertNotIn(marker, json.dumps(result))

    def test_generic_invalid_argument_does_not_infer_rejected_field(self):
        result = m.safe_error_details(dict(error=dict(status='INVALID_ARGUMENT', message='Request contains an invalid argument.')))
        self.assertEqual(result['rejected_field'], 'UNKNOWN')
        self.assertEqual(result['error_details'], [])
        self.assertEqual(result['error_message'], 'Request contains an invalid argument.')

    def test_allowlisted_error_symbols_still_redact_credential_substrings(self):
        raw = {'error': {'status': 'INVALID_ARGUMENT', 'details': [
            {'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID',
             'domain': 'generativelanguage.googleapis.com'},
            {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '15.123s'}]}}
        result = m.safe_error_details(raw, secrets=('API_KEY', 'generativelanguage', '15.12'))
        self.assertNotIn('reason', result['error_details'][0])
        self.assertNotIn('domain', result['error_details'][0])
        self.assertNotIn('retryDelay', result['error_details'][1])

    def test_errors_are_robust_to_malformed_nested_data_and_credentials(self):
        malformed = [None, [], 'bad', b'\xff', {'error':[]}, {'error':{'details':None}},
            {'error':{'details':[None, [], 3, {'@type':[]}, {'@type':'type.googleapis.com/google.rpc.BadRequest','fieldViolations':[None, [], {'field':[]}]}]}},
            {'error':{'status':'PRIVATE_PERSON', 'message':'PRIVATE_PERSON', 'details':[
                {'@type':'type.googleapis.com/google.rpc.ErrorInfo','reason':[], 'domain':[]},
                {'@type':'type.googleapis.com/google.rpc.RetryInfo','retryDelay':{}},
                {'@type':'type.googleapis.com/google.rpc.RetryInfo','retryDelay':'999999999999s'}]}}]
        for raw in malformed:
            with self.subTest(raw=raw):
                result = m.safe_error_details(raw, secrets=('SENTINEL',))
                self.assertIsInstance(result, dict)
                self.assertEqual(result['rejected_field'], 'UNKNOWN')
                self.assertNotIn('PRIVATE_PERSON', json.dumps(result))
        raw = {'error':{'details':[{'@type':'type.googleapis.com/google.rpc.BadRequest','fieldViolations':[
            {'field':'generationConfig.responseJsonSchema.SENTINEL', 'description':'Bearer SENTINEL'}]}]}}
        self.assertNotIn('SENTINEL', json.dumps(m.safe_error_details(json.dumps(raw), secrets=('SENTINEL',))))


if __name__ == '__main__': unittest.main()

"""Offline generateContent candidates, never reviewed or evaluation evidence.

The official route-specific example is translated to REST camelCase. Original
snake_case aliases and protobuf Duration strings are also documented as valid;
this spelling does not establish the cause of an earlier generic HTTP400.
Stage1 uses a neutral summary prompt instead of the sample's Sundar-specific
question so stage2 can change only its video URL. No media is retained here.
Offsets are request metadata, not proof of provider-side input isolation.
"""
from copy import deepcopy
import re

from . import expert_collector as collector
from .api_diagnostics import MAX_ERROR_BYTES, safe_http_error


PURPOSE = 'VIDEO_API_DIAGNOSTIC'
SESSION = 'video-api-20261017'
REFERENCE_ID = 'ixRanV-rdAQ'
TARGET_ID = 'brQaUDGnXTs'
PROMPT = 'Summarize this video in three sentences and include timestamps for concrete details.'
SIMPLE_SCHEMA = {
    'type': 'object',
    'properties': {
        'summary': {'type': 'string'},
        'observations': {'type': 'array', 'minItems': 1, 'maxItems': 3,
            'items': {'type': 'object', 'properties': {
                'timestamp': {'type': 'string'}, 'detail': {'type': 'string'}},
                'required': ['timestamp', 'detail'], 'additionalProperties': False}}},
    'required': ['summary', 'observations'], 'additionalProperties': False}


def _require(condition):
    if not condition:
        raise ValueError('invalid video diagnostic payload')


def _keys(value, keys):
    _require(type(value) is dict and set(value) == set(keys))


def _text(value, maximum=300):
    return (isinstance(value, str) and bool(value.strip()) and len(value) <= maximum
            and not any(ord(char) < 32 or ord(char) == 127 for char in value))


def validate_source(source):
    """Validate the stage-specific source, retaining full original duration."""
    _keys(source, {'schema_version', 'purpose', 'video', 'start_seconds', 'end_seconds', 'diagnostic'})
    _require(source['schema_version'] == 'evidence.source-plan.v2' and source['purpose'] == PURPOSE)
    diagnostic = source['diagnostic']
    _keys(diagnostic, {'session', 'stage', 'revision', 'reference_sha256'})
    stage = diagnostic['stage']
    _require(diagnostic['session'] == SESSION and type(stage) is int and 1 <= stage <= 4)
    _require(_text(diagnostic['revision'], 80))
    sha = diagnostic['reference_sha256']
    _require(isinstance(sha, str) and re.fullmatch(r'[a-fA-F0-9]{64}', sha) is not None)
    video = source['video']
    _require(type(video) is dict)
    collector._video(video)
    _require(video['id'] == (REFERENCE_ID if stage == 1 else TARGET_ID))
    start, end = source['start_seconds'], source['end_seconds']
    _require(type(start) is int and type(end) is int and start == 0)
    expected_end = video['duration_seconds'] if stage < 3 else min(120, video['duration_seconds'])
    _require(end == expected_end and (stage < 3 or 0 < end <= 600))
    return deepcopy(source)


def build_body(source):
    """Build one of four bodies whose successive changes are isolated."""
    source = validate_source(source)
    stage = source['diagnostic']['stage']
    file_part = {'fileData': {'fileUri': source['video']['url']}}
    body = {'contents': [{'parts': [{'text': PROMPT}, file_part]}]}
    if stage >= 3:
        file_part['videoMetadata'] = {'startOffset': '0s', 'endOffset': str(source['end_seconds']) + 's'}
    if stage == 4:
        body['generationConfig'] = {'responseMimeType': 'application/json',
                                    'responseJsonSchema': deepcopy(SIMPLE_SCHEMA)}
    return body


_REFUSAL = re.compile(
    r"\b(?:cannot|can't|unable to|do not have access|don't have access|not able to)\b.{0,100}"
    r'\b(?:access|watch|view|process|analy[sz]e|summari[sz]e|help|video)\b'
    r'|\b(?:video is unavailable|provide a transcript|share a transcript|cannot help|refuse)\b'
    r'|(?:영상을?\s*(?:볼|시청|접근|분석).{0,30}(?:없|불가)|요청.{0,20}도와드릴 수 없)', re.I | re.S)


def _candidate_text(text):
    _require(isinstance(text, str) and len(text.strip()) >= 40 and not _REFUSAL.search(text))
    _require(sum(char.isalpha() for char in text) >= 20 and len(set(text.lower().split())) >= 4)


def _note(text):
    # Reuse the established credential/URL redactor before any truncation.
    safe = safe_http_error('GEMINI', None, {'error': {'message': text}})['error_message'] or ''
    safe = re.sub(r'\b[^\s@]+@[^\s@]+\.[^\s@]+\b', '[REDACTED_EMAIL]', safe)
    return ' '.join(safe.split())[:300]


def _timestamp(value, source):
    _require(_text(value, 20) and re.fullmatch(r'(?:\d{1,3}:)?\d{1,2}:\d{2}(?:\.\d{1,3})?', value) is not None)
    parts = value.split(':')
    _require(float(parts[-1]) < 60 and (len(parts) == 2 or int(parts[-2]) < 60))
    seconds = float(parts[-1]) + 60 * int(parts[-2]) + (3600 * int(parts[0]) if len(parts) == 3 else 0)
    _require(source['start_seconds'] <= seconds < source['end_seconds'])


def evaluate_response(raw, source):
    """Return bounded functional content candidates; independent review is needed."""
    source = validate_source(source)
    stage = source['diagnostic']['stage']
    try:
        response = collector._json(raw) if isinstance(raw, (str, bytes)) else raw
        _require(type(response) is dict)
        text = collector._generated_text(response)
        _candidate_text(text)
        if stage == 4:
            parsed = collector._json(text)
            _keys(parsed, {'summary', 'observations'})
            _require(_text(parsed['summary']) and not _REFUSAL.search(parsed['summary']))
            observations = parsed['observations']
            _require(type(observations) is list and 1 <= len(observations) <= 3)
            notes = [_note(parsed['summary'])]
            for observation in observations:
                _keys(observation, {'timestamp', 'detail'})
                _timestamp(observation['timestamp'], source)
                _require(_text(observation['detail']) and not _REFUSAL.search(observation['detail']))
                notes.append(_note(observation['timestamp'] + ': ' + observation['detail']))
            notes = notes[:3]
        else:
            sentences = re.split(r'(?<=[.!?。！？])\s+|[\r\n]+', text.strip())
            notes = [_note(sentence) for sentence in sentences if sentence.strip()][:3]
        _require(bool(notes) and all(notes))
    except (TypeError, AttributeError, KeyError, UnicodeError, RecursionError, OverflowError):
        raise ValueError('invalid video diagnostic response') from None
    return dict(evidence_status='DIAGNOSTIC_ONLY_UNREVIEWED', blind_evaluation_eligible=False,
        input_isolation=('FULL_VIDEO_DIAGNOSTIC_EXCLUDED_FROM_EVALUATION' if stage < 3
                         else 'API_OFFSETS_REQUESTED_UNPROVEN'),
        diagnostic_content=dict(stage=stage, content_candidate_valid=True, notes=notes, source_review='NOT_REVIEWED'),
        valid_extraction=False)


_STATUSES = frozenset({'INVALID_ARGUMENT', 'UNAUTHENTICATED', 'PERMISSION_DENIED', 'RESOURCE_EXHAUSTED',
    'NOT_FOUND', 'FAILED_PRECONDITION', 'OUT_OF_RANGE', 'UNIMPLEMENTED', 'INTERNAL', 'UNAVAILABLE',
    'DEADLINE_EXCEEDED', 'CANCELLED', 'UNKNOWN', 'DATA_LOSS', 'ALREADY_EXISTS', 'ABORTED'})
_REASONS = frozenset({'API_KEY_INVALID', 'API_KEY_EXPIRED', 'API_KEY_SERVICE_BLOCKED',
    'API_KEY_HTTP_REFERRER_BLOCKED', 'API_KEY_IP_ADDRESS_BLOCKED', 'API_KEY_ANDROID_APP_BLOCKED',
    'API_KEY_IOS_APP_BLOCKED', 'SERVICE_DISABLED', 'BILLING_DISABLED', 'RATE_LIMIT_EXCEEDED',
    'QUOTA_EXCEEDED', 'RESOURCE_EXHAUSTED', 'MODEL_NOT_FOUND', 'ACCESS_TOKEN_EXPIRED',
    'ACCESS_TOKEN_SCOPE_INSUFFICIENT', 'CONSUMER_INVALID'})
_DOMAINS = frozenset({'googleapis.com', 'generativelanguage.googleapis.com'})
_TYPES = frozenset({'google.rpc.BadRequest', 'google.rpc.ErrorInfo', 'google.rpc.RetryInfo'})
_FIELDS = re.compile(
    r'(?:contents(?:\[[0-9]\])?(?:\.parts(?:\[[0-9]\])?(?:\.(?:text|'
    r'(?:fileData|file_data)(?:\.(?:fileUri|file_uri|mimeType|mime_type))?|'
    r'(?:videoMetadata|video_metadata)(?:\.(?:startOffset|start_offset|endOffset|end_offset|fps))?))?)?'
    r'|generationConfig(?:\.(?:responseMimeType|responseJsonSchema|candidateCount|maxOutputTokens))?'
    r'|generation_config(?:\.(?:response_mime_type|response_json_schema|candidate_count|max_output_tokens))?)')


def _safe_field(value, secrets):
    return (value if isinstance(value, str) and len(value) <= 160 and _FIELDS.fullmatch(value)
            and not any(secret and secret in value for secret in secrets if isinstance(secret, str)) else 'UNKNOWN')


def _description_category(value):
    if not isinstance(value, str):
        return 'REDACTED'
    value = value[:2048].lower()
    for needle, category in (('unknown field', 'UNKNOWN_FIELD'), ('cannot find field', 'UNKNOWN_FIELD'),
                             ('missing', 'MISSING_REQUIRED_FIELD'), ('required', 'MISSING_REQUIRED_FIELD'),
                             ('invalid', 'INVALID_VALUE'), ('expected', 'TYPE_MISMATCH'),
                             ('out of range', 'OUT_OF_RANGE')):
        if needle in value:
            return category
    return 'REDACTED'


def _retry_delay(value):
    if not isinstance(value, str) or re.fullmatch(r'\d{1,5}(?:\.\d{1,9})?s', value) is None:
        return None
    return value if float(value[:-1]) <= 86400 else None


def safe_error_details(raw, secrets=()):
    """Retain typed allowlisted error facts; never arbitrary provider messages.

    Only BadRequest fieldViolations identify a reported rejected field. A generic
    INVALID_ARGUMENT status does not identify any payload feature or its cause.
    The existing safe_http_error performs its redaction first; output messages
    below are categorical because even redacted provider text can contain PII.
    """
    secrets = tuple(secrets) if isinstance(secrets, (tuple, list)) else ()
    base = safe_http_error('GEMINI', None, raw, secrets=secrets)
    status = base['error_status'] if base['error_status'] in _STATUSES else None
    result = dict(error_code=base['error_code'] if type(base['error_code']) is int else None, error_status=status, error_message=(
        'Provider reported ' + status + '; message redacted.' if status else None),
        error_details=[], rejected_field='UNKNOWN')
    if base['error_message'] == 'Request contains an invalid argument.':
        result['error_message'] = base['error_message']
    try:
        if isinstance(raw, (str, bytes)):
            if len(raw) > MAX_ERROR_BYTES:
                return result
            raw = collector._json(raw)
        if not isinstance(raw, dict) or not isinstance(raw.get('error'), dict):
            return result
        details = raw['error'].get('details', [])
        if not isinstance(details, list):
            return result
        for detail in details[:10]:
            raw_type = detail.get('@type') if isinstance(detail, dict) else None
            kind = raw_type.removeprefix('type.googleapis.com/') if isinstance(raw_type, str) else None
            if kind not in _TYPES:
                result['error_details'].append(dict(type='UNKNOWN', count=1, redacted=True))
                continue
            safe = {'type': kind}
            if kind == 'google.rpc.BadRequest':
                violations = detail.get('fieldViolations', [])
                safe['fieldViolations'] = []
                if isinstance(violations, list):
                    for violation in violations[:10]:
                        violation = violation if isinstance(violation, dict) else {}
                        field = _safe_field(violation.get('field'), secrets)
                        safe['fieldViolations'].append(dict(field=field,
                            description_category=_description_category(violation.get('description'))))
                        if result['rejected_field'] == 'UNKNOWN' and field != 'UNKNOWN':
                            result['rejected_field'] = field
            elif kind == 'google.rpc.ErrorInfo':
                reason, domain = detail.get('reason'), detail.get('domain')
                if (isinstance(reason, str) and reason in _REASONS
                        and not any(secret and secret in reason for secret in secrets if isinstance(secret, str))):
                    safe['reason'] = reason
                if (isinstance(domain, str) and domain in _DOMAINS
                        and not any(secret and secret in domain for secret in secrets if isinstance(secret, str))):
                    safe['domain'] = domain
            else:
                delay = _retry_delay(detail.get('retryDelay'))
                if (delay is not None
                        and not any(secret and secret in delay for secret in secrets if isinstance(secret, str))):
                    safe['retryDelay'] = delay
            result['error_details'].append(safe)
        if len(details) > 10:
            result['error_details'].append(dict(type='UNKNOWN', count=len(details) - 10, redacted=True))
    except (ValueError, TypeError, AttributeError, UnicodeError, RecursionError, OverflowError):
        pass
    return result

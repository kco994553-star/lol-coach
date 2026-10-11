"""Selected safe acquisition diagnostics. No key values or full response retention."""
import json
import re
from urllib.parse import quote, quote_plus

MAX_ERROR_BYTES=65536
MAX_MESSAGE_CHARS=512
_KEY=re.compile(r'RGAPI-[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}')


def inspect_riot_key(value):
    raw=value if isinstance(value,str) else ''
    normalized=raw.strip()
    shape=dict(raw_length=len(raw),normalized_length=len(normalized),raw_has_prefix=raw.startswith('RGAPI-'),
        normalized_has_prefix=normalized.startswith('RGAPI-'),has_outer_whitespace=raw!=normalized,
        contains_line_break='\n' in raw or '\r' in raw,valid_shape=bool(_KEY.fullmatch(normalized)))
    return (normalized if shape['valid_shape'] else None),shape


def _message(value,secrets):
    if not isinstance(value,str):return None
    # Redact before truncating: a truncated credential can otherwise leak.
    variants=set()
    for secret in secrets:
        if isinstance(secret,str) and secret:
            for s in (secret,secret.strip()):
                if s:variants.update((s,quote(s,safe=''),quote_plus(s,safe='')))
    for secret in sorted(variants,key=len,reverse=True):value=value.replace(secret,'[REDACTED_KEY]')
    value=re.sub(r'https?://[^\s<>"\']+','[REDACTED_URL]',value,flags=re.I)
    value=re.sub(r'RGAPI-[A-Za-z0-9_-]+|AIza[A-Za-z0-9_-]+','[REDACTED_KEY]',value)
    value=re.sub(r'(?i)\b(?:api[_ -]?key|x-goog-api-key|x-riot-token|authorization|key)\s*[:=]\s*["\']?[^\s,"\';]+',
                 '[REDACTED_CREDENTIAL]',value)
    value=re.sub(r'[\x00-\x1f\x7f]', ' ', value)
    return value[:MAX_MESSAGE_CHARS] or None


def _symbol(value,secrets=()):
    return value if _message(value,secrets)==value and isinstance(value,str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}',value) else None


def safe_http_error(provider,http_status,body,*,secrets=()):
    result=dict(http_status=http_status if type(http_status) is int and 100<=http_status<=599 else None,
                error_status=None,error_code=None,error_message=None)
    try:
        if isinstance(body,(str,bytes)):
            if len(body)>MAX_ERROR_BYTES:return result
            def reject(_):raise ValueError('nonfinite JSON')
            body=json.loads(body,parse_constant=reject)
        if not isinstance(body,dict):return result
        error=body.get('status' if provider=='RIOT' else 'error')
        if not isinstance(error,dict):return result
        result['error_message']=_message(error.get('message'),secrets)
        if provider!='RIOT':
            result['error_status']=_symbol(error.get('status'),secrets)
            code=error.get('code')
            result['error_code']=code if type(code) is int and 0<=code<=999 else _symbol(code,secrets)
    except (ValueError,TypeError,UnicodeError,RecursionError,OverflowError):pass
    return result

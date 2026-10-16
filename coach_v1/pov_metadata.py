"""Bounded public YouTube metadata, separate from inference and expert intake."""
from datetime import datetime, timezone
import hashlib
import json
import re
import socket
import time
import urllib.error
from urllib.parse import urlencode

from coach_v1 import expert_collector

BASE_URL = 'https://www.googleapis.com/youtube/v3/'
MAX_REQUESTS = 12
MAX_UPLOADS = 3
MAX_BYTES = 1_000_000
TIMEOUT = 30


class MetadataFailure(Exception):
    """A fixed diagnostic code, never provider text."""


def _stamp(now):
    value = now() if callable(now) else now
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace('+00:00', 'Z')


def _text(value, secret, maximum=300):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or secret and secret in value:
        raise MetadataFailure('MALFORMED_PUBLIC_METADATA')
    return value


def _items(data):
    if not isinstance(data, dict) or not isinstance(data.get('items'), list):
        raise MetadataFailure('MALFORMED_RESPONSE')
    return data['items']


def _channel(data, expected_id, expected_handle, secret):
    rows = _items(data)
    if not rows:
        raise MetadataFailure('CHANNEL_NOT_FOUND')
    if len(rows) != 1 or not isinstance(rows[0], dict) or rows[0].get('id') != expected_id:
        raise MetadataFailure('CHANNEL_ID_MISMATCH')
    try:
        row = rows[0]; snippet = row['snippet']
        custom_url = _text(snippet['customUrl'], secret, 100)
        if custom_url.casefold() != expected_handle.casefold():
            raise MetadataFailure('HANDLE_MISMATCH')
        playlist = row['contentDetails']['relatedPlaylists']['uploads']
        if not isinstance(playlist, str) or not re.fullmatch(r'UU[A-Za-z0-9_-]{22}', playlist):
            raise MetadataFailure('MALFORMED_CHANNEL_METADATA')
        return dict(channel_id=expected_id, title=_text(snippet['title'], secret),
                    custom_url=custom_url, uploads_playlist_id=playlist)
    except (KeyError, TypeError):
        raise MetadataFailure('MALFORMED_CHANNEL_METADATA') from None


def _video(row, requested, channel_id, secret):
    try:
        if not isinstance(row, dict) or row.get('id') not in requested:
            return None
        snippet = row['snippet']; status = row['status']
        if (snippet['channelId'] != channel_id or status['privacyStatus'] != 'public'
                or status['uploadStatus'] != 'processed' or snippet.get('liveBroadcastContent', 'none') != 'none'):
            return None
        duration = row['contentDetails']['duration']
        match = re.fullmatch(r'P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match is None:
            return None
        seconds = sum(int(part or 0) * scale for part, scale in zip(match.groups(), (86400, 3600, 60, 1)))
        if seconds <= 0:
            return None
        published = _text(snippet['publishedAt'], secret, 40)
        date = datetime.fromisoformat(published.replace('Z', '+00:00'))
        if date.utcoffset() is None or date.utcoffset().total_seconds() != 0:
            return None
        return dict(video_id=row['id'], url='https://www.youtube.com/watch?v=' + row['id'],
                    channel_id=channel_id, title=_text(snippet['title'], secret),
                    duration_iso8601=duration, duration_seconds=seconds, published_at=published,
                    published_at_meaning='UPLOAD_PUBLICATION_NOT_GAME_DATE',
                    **{key: 'UNKNOWN' for key in ('game_date', 'patch', 'opponent', 'game_link', 'view_type', 'continuity', 'intent')})
    except (KeyError, TypeError, ValueError, OverflowError, MetadataFailure):
        return None


def verify_channels(config, api_key, transport=None, now=time.time):
    """Verify canonical channel metadata and discover at most three uploads each.

    Channel verification does not verify POV, ownership, affiliation or gameplay.
    Responses are hashed transiently and only public allowlisted metadata survives.
    """
    report = dict(schema_version='pov.metadata.v1', category='POV', expert_source=False,
                  checked_at=_stamp(now), status='BLOCKED_EXTERNAL', reason=None,
                  request_counts=dict(METADATA=0, TEXT_PROBE=0, VIDEO_CLIP=0),
                  channels=[], sources=[], diagnostics=[], matched_games=0, evaluated_scenes=0,
                  media_downloads=0, transcript_downloads=0, retries=0)
    try:
        rows = config['channels']
        if (config.get('format') != 'lol-coach-pov-channels-v1' or config.get('category') != 'POV'
                or not isinstance(rows, list) or not 1 <= len(rows) <= MAX_REQUESTS // 4):
            raise ValueError
        ids = set(); handles = set()
        for row in rows:
            channel_id = row['channel_id']; handle = row['handle']
            if (not isinstance(channel_id, str) or not re.fullmatch(r'UC[A-Za-z0-9_-]{22}', channel_id)
                    or not isinstance(handle, str) or not re.fullmatch(r'@[^\s/?&#]{1,100}', handle)
                    or channel_id in ids or handle.casefold() in handles):
                raise ValueError
            ids.add(channel_id); handles.add(handle.casefold())
    except (KeyError, TypeError, ValueError):
        report['reason'] = 'INVALID_CONFIG'
        return report
    if not isinstance(api_key, str) or not api_key.strip() or any(c in api_key for c in '\r\n'):
        report['reason'] = 'MISSING_API_KEY'
        return report
    transport = transport or expert_collector._transport

    def request(endpoint, **params):
        if report['request_counts']['METADATA'] >= MAX_REQUESTS:
            raise MetadataFailure('REQUEST_BUDGET_EXHAUSTED')
        url = BASE_URL + endpoint + '?' + urlencode(params)
        source = dict(url=url, checked_at=_stamp(now), endpoint=endpoint,
                      response_sha256=None, hash_scope='TRANSIENT_RAW_RESPONSE_BYTES', http_status=None, reason=None)
        report['sources'].append(source)
        report['request_counts']['METADATA'] += 1
        try:
            code, _, raw = transport('GET', url, {'x-goog-api-key': api_key, 'Accept': 'application/json'}, None, TIMEOUT, MAX_BYTES)
            source['http_status'] = code if type(code) is int else None
            if not isinstance(raw, bytes):
                raise MetadataFailure('MALFORMED_RESPONSE')
            source['response_sha256'] = hashlib.sha256(raw).hexdigest()
            if len(raw) > MAX_BYTES:
                raise MetadataFailure('RESPONSE_TOO_LARGE')
            if code != 200:
                raise MetadataFailure('HTTP_FAILURE')
            try:
                data = json.loads(raw)
                if not isinstance(data, dict): raise ValueError
            except (ValueError, UnicodeError, RecursionError):
                raise MetadataFailure('MALFORMED_RESPONSE') from None
            return data
        except MetadataFailure as error:
            source['reason'] = str(error)
            raise
        except (TimeoutError, socket.timeout):
            source['reason'] = 'NETWORK_TIMEOUT'
        except urllib.error.URLError as error:
            source['reason'] = 'NETWORK_TIMEOUT' if isinstance(error.reason, (TimeoutError, socket.timeout)) else 'NETWORK_FAILURE'
        except expert_collector._External as error:
            source['reason'] = 'RESPONSE_TOO_LARGE' if error.reason == 'RESPONSE_TOO_LARGE' else 'NETWORK_FAILURE'
            source['http_status'] = error.http_status if type(error.http_status) is int else None
        except Exception:
            source['reason'] = 'NETWORK_FAILURE'
        raise MetadataFailure(source['reason']) from None

    for provided in rows:
        channel_id = provided['channel_id']; handle = provided['handle']
        channel = dict(provided_channel_id=channel_id, provided_handle=handle,
                       verification_status='UNVERIFIED', reason=None, metadata=None, videos=[],
                       official_status='UNKNOWN', channel_owner_is_player='UNKNOWN',
                       view_type='UNKNOWN', continuity='UNKNOWN', expert_source=False)
        report['channels'].append(channel)
        try:
            params = dict(part='snippet,contentDetails', fields='items(id,snippet(title,customUrl),contentDetails(relatedPlaylists(uploads)))')
            by_id = _channel(request('channels', id=channel_id, **params), channel_id, handle, api_key)
            by_handle = _channel(request('channels', forHandle=handle, **params), channel_id, handle, api_key)
            if by_id['uploads_playlist_id'] != by_handle['uploads_playlist_id']:
                raise MetadataFailure('CHANNEL_METADATA_CONFLICT')
            channel['metadata'] = by_handle
            channel['verification_status'] = 'CANONICAL_CHANNEL_METADATA_VERIFIED'
            playlist = request('playlistItems', part='contentDetails', playlistId=by_handle['uploads_playlist_id'],
                               maxResults=MAX_UPLOADS, fields='items(contentDetails(videoId))')
            video_ids = []
            for item in _items(playlist)[:MAX_UPLOADS]:
                video_id = item.get('contentDetails', {}).get('videoId') if isinstance(item, dict) and isinstance(item.get('contentDetails'), dict) else None
                if isinstance(video_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id) and video_id not in video_ids:
                    video_ids.append(video_id)
            if not video_ids:
                raise MetadataFailure('NO_UPLOAD_CANDIDATES')
            data = request('videos', part='snippet,contentDetails,status', id=','.join(video_ids),
                           fields='items(id,snippet(channelId,title,publishedAt,liveBroadcastContent),contentDetails(duration),status(privacyStatus,uploadStatus))')
            seen = set()
            for item in _items(data)[:MAX_UPLOADS]:
                video = _video(item, video_ids, channel_id, api_key)
                if video and video['video_id'] not in seen:
                    seen.add(video['video_id']); channel['videos'].append(video)
            if not channel['videos']:
                raise MetadataFailure('NO_PUBLIC_PROCESSED_CANDIDATES')
        except MetadataFailure as error:
            channel['reason'] = str(error)
            report['diagnostics'].append(dict(channel_id=channel_id, reason=str(error)))
    complete = all(c['verification_status'] == 'CANONICAL_CHANNEL_METADATA_VERIFIED' and not c['reason'] for c in report['channels'])
    report['status'] = 'VERIFIED_METADATA' if complete else 'PARTIAL'
    report['reason'] = None if complete else 'ONE_OR_MORE_CHANNELS_INCOMPLETE'
    return report

"""Index public timestamped speech as review candidates, never visual facts."""
import re
import unicodedata
from .io import sha

TOPICS={
    'WAVE':('wave','minion','cs'),
    'ROAM':('roam','roaming','roams'),
    'JUNGLE':('jungle','jungler','gank','ganked'),
    'VISION':('vision','ward','wards'),
    'TRADE':('trade','trades','trading'),
}

# Literal search aliases, not a vocabulary for interpreting an expert's claim.
# Keep English aliases unchanged; newly added topic keys are Korean-only.
KOREAN_TOPICS={
    'WAVE':('웨이브','미니언'),
    'ROAM':('로밍',),
    'JUNGLE':('정글','갱','갱킹'),
    'VISION':('시야','와드'),
    'TRADE':('딜교','딜교환'),
    'LANE':('라인',),
    'TEAMFIGHT':('한타',),
    'MACRO':('운영',),
    'SIDE':('사이드',),
    'MAIN_BODY':('본대',),
    'OBJECTIVE':('오브젝트',),
}
KOREAN_PARTICLES=frozenset(('은','는','이','가','을','를','의','에','에서','에게',
    '로','으로','와','과','도','만','부터','까지','보다','처럼','마다','랑','이랑',
    '이나','나','라도','이라도','은요','는요','요','들'))
TOPIC_ORDER=tuple(dict.fromkeys((*TOPICS,*KOREAN_TOPICS)))


def _korean_topics(speech):
    words=set(re.findall(r'[가-힣]+',unicodedata.normalize('NFC',speech)))
    return {topic for topic,terms in KOREAN_TOPICS.items()
        if any(word==term or (word.startswith(term) and word[len(term):] in KOREAN_PARTICLES)
            for word in words for term in terms)}


def index_transcript(raw,video_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',video_id):raise ValueError('INVALID_VIDEO_ID')
    lines=raw.decode('utf-8-sig').splitlines()
    if len(lines)<5 or lines[0]!='YouTube transcript' or lines[1]!='Video ID: '+video_id:raise ValueError('TRANSCRIPT_ID_MISMATCH')
    if not lines[2].startswith('Language: ') or lines[3] not in ('Captions: auto-generated','Captions: manual'):raise ValueError('TRANSCRIPT_METADATA')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,24}',lines[2][10:]):raise ValueError('TRANSCRIPT_LANGUAGE')
    count=0;prior=-1;candidates=[]
    for line in lines[4:]:
        if not line.strip():continue
        m=re.fullmatch(r'\[(\d+):(\d{2})(?::(\d{2}))?\] (.+)',line)
        if not m:raise ValueError('INVALID_CUE')
        a,b,c,speech=m.groups();a=int(a);b=int(b)
        if b>=60 or (c is not None and int(c)>=60):raise ValueError('INVALID_TIMESTAMP')
        seconds=a*60+b if c is None else a*3600+b*60+int(c)
        if seconds<prior:raise ValueError('NONMONOTONIC_CUES')
        prior=seconds;count+=1
        words=set(re.findall(r'[a-z]+',speech.lower()))
        korean_topics=_korean_topics(speech)
        topics=[topic for topic in TOPIC_ORDER if words.intersection(TOPICS.get(topic,())) or topic in korean_topics]
        if topics:candidates.append(dict(cue_index=count,video_time_ms=seconds*1000,game_time_ms=None,topics=topics,kind='SPEECH_REVIEW_CANDIDATE',visual_verified=False,decision_eligible=False))
    if count==0:raise ValueError('EMPTY_TRANSCRIPT')
    return dict(format='lol-coach-video-index-v1',video_id=video_id,transcript_sha256=sha(raw),
        language=lines[2][10:],captions=lines[3][10:],cue_count=count,last_cue_video_time_ms=prior*1000,
        source_kind='PUBLIC_VIDEO_TRANSCRIPT',source_authenticity_verified=False,game_clock_mapping_verified=False,
        player_perspective_verified=False,patch_verified=False,visual_frames_reviewed=0,
        candidates=candidates,coaching_enabled=False,
        limitations=['KEYWORD_SEARCH_IS_NOT_EVENT_DETECTION','SPEECH_IS_NOT_VISUAL_EVIDENCE','AUTO_CAPTIONS_MAY_BE_WRONG','NO_GLOBAL_VIDEO_TO_GAME_TIME_OFFSET','NO_FUTURE_OUTCOME_AS_PRIOR_KNOWLEDGE'])

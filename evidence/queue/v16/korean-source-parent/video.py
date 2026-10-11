"""Index public timestamped speech as review candidates, never visual facts."""
import re
from .io import sha

TOPICS={
    'WAVE':('wave','minion','cs'),
    'ROAM':('roam','roaming','roams'),
    'JUNGLE':('jungle','jungler','gank','ganked'),
    'VISION':('vision','ward','wards'),
    'TRADE':('trade','trades','trading'),
}

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
        topics=[topic for topic,terms in TOPICS.items() if words.intersection(terms)]
        if topics:candidates.append(dict(cue_index=count,video_time_ms=seconds*1000,game_time_ms=None,topics=topics,kind='SPEECH_REVIEW_CANDIDATE',visual_verified=False,decision_eligible=False))
    if count==0:raise ValueError('EMPTY_TRANSCRIPT')
    return dict(format='lol-coach-video-index-v1',video_id=video_id,transcript_sha256=sha(raw),
        language=lines[2][10:],captions=lines[3][10:],cue_count=count,last_cue_video_time_ms=prior*1000,
        source_kind='PUBLIC_VIDEO_TRANSCRIPT',source_authenticity_verified=False,game_clock_mapping_verified=False,
        player_perspective_verified=False,patch_verified=False,visual_frames_reviewed=0,
        candidates=candidates,coaching_enabled=False,
        limitations=['KEYWORD_SEARCH_IS_NOT_EVENT_DETECTION','SPEECH_IS_NOT_VISUAL_EVIDENCE','AUTO_CAPTIONS_MAY_BE_WRONG','NO_GLOBAL_VIDEO_TO_GAME_TIME_OFFSET','NO_FUTURE_OUTCOME_AS_PRIOR_KNOWLEDGE'])

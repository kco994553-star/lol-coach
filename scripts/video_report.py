"""Render speech candidate timestamps as a portable report without transcript text."""
import argparse,html,json,re
from pathlib import Path

def render(index):
    vid=index['video_id']
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid):raise ValueError('Invalid video id')
    labels={'ROAM':'로밍','WAVE':'웨이브','JUNGLE':'정글','VISION':'시야','TRADE':'교환'}
    rows=[]
    for c in index['candidates']:
        sec=c['video_time_ms']//1000
        tags=', '.join(labels.get(t,t) for t in c['topics'])
        rows.append(f'<tr><td><a href="https://www.youtube.com/watch?v={vid}&amp;t={sec}s" target="_blank" rel="noopener noreferrer">{sec//60:02}:{sec%60:02} ↗</a></td><td>{html.escape(tags)}</td><td>해설 언급 · 화면 미검증</td></tr>')
    return '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LoL Coach 영상 복기 후보</title><style>body{font-family:system-ui,sans-serif;background:#101925;color:#e8eef5;max-width:850px;margin:auto;padding:26px;line-height:1.65}a{color:#8ee1cb}h1{line-height:1.3}p{color:#b9c8d8}.callout{border-left:3px solid #8ee1cb;padding-left:18px}table{width:100%;border-collapse:collapse}td,th{padding:12px 8px;border-bottom:1px solid #344155;text-align:left}small{overflow-wrap:anywhere}</style><p>LoL Coach · R5</p><h1>영상에서 복기할 구간 찾기</h1><p class="callout">공개 영상의 자동자막에서 찾은 주제별 후보입니다. 실제 장면·게임 시간·패치를 확인하기 전에는 실수 판정이나 코칭 근거로 사용하지 않습니다.</p>'''+f'<p>자막 {index["cue_count"]:,}구간 · 후보 {len(index["candidates"])}개<br>출처: <a href="https://www.youtube.com/watch?v={vid}">공개 영상 원문</a></p>'+'''<p>아래 시간은 영상 시간입니다. 클릭하면 해당 시점의 YouTube 페이지를 엽니다. 편집·일시정지·다른 경기가 포함될 수 있어 게임 시간으로 자동 환산하지 않습니다.</p><table><thead><tr><th>영상 시간</th><th>주제</th><th>증거 상태</th></tr></thead><tbody>'''+''.join(rows)+'</tbody></table><p><small>원본 자막 SHA-256: '+html.escape(index['transcript_sha256'])+'</small></p></html>'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('index',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    with a.out.open('x',encoding='utf-8') as f:f.write(render(json.loads(a.index.read_text())))

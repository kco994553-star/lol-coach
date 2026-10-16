"""PC projection of source-bound observed resource samples; never tactical advice."""
from functools import lru_cache
from pathlib import Path
from .resource_recovery import load_bound_report,SOURCE_FILES

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'data/resource_recovery/2026-10-16'


def render_cards(report,binding,draft):
    if draft.get('phase')!='PRE_GAME':return []
    position=draft.get('my_position')
    enemies=[s.get('champion') for s in draft.get('slots',[]) if s.get('side')=='ENEMY' and s.get('position')==position]
    if len(enemies)!=1 or not enemies[0]:return []
    match=next((c for c in report['cohorts'] if all(c[k]==draft.get(v) for k,v in
        [('patch','patch'),('champion','my_champion'),('position','my_position')]) and c['opponent_champion']==enemies[0]),None)
    if match is None:return []
    title=f"프로 참고 자원 · {match['champion']} 대 {match['opponent_champion']}"
    detail=[f"패치 {match['patch']} · 포지션 {match['position']} · 선택 참가자 관측 {match['participant_observations']}개 / 서로 다른 경기 {match['matches']}개",
        '사용자 명단에서 수집한 프로 참고 표본입니다. 참가자 전원의 프로 신분은 검증하지 않았습니다.',
        '같은 포지션 상대와 같은 프레임에서 뺀 값입니다. 포지션 전체로 대체하지 않습니다.',
        '10분 구간은 10:00 이상 11:00 미만, 15분 구간은 15:00 이상 16:00 미만입니다. 그 구간의 마지막 수신 관측이며 보간하지 않습니다.',
        '실제 관측 시각 분포는 주변 요약입니다. 개별 장면을 복원하거나 행동의 우열을 판단할 수 없습니다.']
    lines=[f"{match['patch']} · {match['position']} · 경기 {match['matches']}개"]
    any_value=False
    for m in match['measurements']:
        exact=m['mode']=='EXACT_TIMESTAMP';prefix=f"정확히 {m['minute']}분" if exact else f"{m['minute']}분 구간"
        if not exact:
            times=m['timestamp_ms'];detail.append(prefix+' 실제 관측 시각(ms) · 중앙값 '+str(times['median'])+' · 범위 '+str(times['minimum'])+'~'+str(times['maximum'])+' · 누락 '+str(times['missing_n']))
        for metric,label in [('gold','골드'),('xp','경험치'),('level','레벨')]:
            values=m['metrics'][metric];v=values['difference'];known=v['n_valid']>0
            mean=f"{v['mean']:.2f}" if known else '미확인'
            detail.append(f"{prefix} {label} · 내 평균 {values['own']['mean']} / 상대 평균 {values['opponent']['mean']} · 짝 차이 {mean} · 유효 {v['n_valid']} · 누락 {v['missing_n']} · 경기 {v['match_n']}")
            if v['missing_n']:detail.append('누락 사유: '+str({k:n for k,n in v['missing_reasons'].items() if n}))
            if not exact and ((m['minute']==10 and metric=='gold') or (m['minute']==15 and metric=='xp')):
                lines.append(f"{prefix} {label} 차이 {mean} · n={v['n_valid']}, 누락={v['missing_n']}")
            if not exact and known:any_value=True
    level='STATISTICS' if any_value else 'UNKNOWN'
    return [dict(id='resource-observed-matchup',title=title,evidence_level=level,
        evidence_label='통계' if any_value else '미확인',patch_status='MATCHING_ARCHIVE',lines=lines[:3],details='\n'.join(detail),section='PROFILE',
        sources=[dict(url='https://developer.riotgames.com/apis#match-v5',title='기존 프로 참고 원본 · 실제 시각 자원 관측',
            patch=match['patch'],sha256=binding['report_sha256'],locator=match['champion']+' / '+match['position']+' / '+match['opponent_champion'])])]


@lru_cache(maxsize=4)
def _snapshot(directory,stamp):
    return load_bound_report(Path(directory))


def cards_for_draft(draft,directory=DEFAULT):
    folder=Path(directory)
    try:
        paths=[folder/'resources.json',folder/'source-binding.json',*[ROOT/p for p in SOURCE_FILES]]
        stamp=tuple((p.stat().st_mtime_ns,p.stat().st_size) for p in paths)
        report,binding=_snapshot(str(folder),stamp)
        return render_cards(report,binding,draft)
    except (OSError,ValueError):return []

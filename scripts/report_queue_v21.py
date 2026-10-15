"""Reproducible offline counts. Fixture inputs are never saved as user choices."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def report():
    from coach_v1.auto_review import assess,load_bundle
    from coach_v1.official_catalog import facts_response
    from coach_v1.pc_coach import preview,review_store
    from coach_v1.pc_runtime import load_pc_default_datasets
    from coach_v1.review_queue import GOLDEN,_coverage
    from coach_v1.pregame_contract import POSITIONS
    from scripts.launch_pc import create_server
    source=dict(kind='MANUAL',reference='Golden10 합성 예시 · 실제 경기 아님',observed_at=None,verification='UNVERIFIED')
    slots=[dict(side=side,slot=i+1,champion=champion,position=position,position_candidates=[],uncertainty='합성 예시',champion_source=source,position_source=source,runes=dict(status='UNKNOWN',values=[],source=source),summoners=dict(status='UNKNOWN',values=[],source=source)) for side,team in GOLDEN.items() for i,(position,champion) in enumerate(team.items())]
    with tempfile.TemporaryDirectory(prefix='v21-report-') as t:
        server=create_server(Path(t),port=0)
        try:
            load_pc_default_datasets(server);views=[]
            for position in POSITIONS:
                draft=dict(title='Golden10 합성 예시',patch='16.20',phase='PRE_GAME',observed_at=None,my_position=position,my_champion=GOLDEN['ALLY'][position],my_slot=POSITIONS.index(position)+1,slots=slots,source=source,original_capture=None)
                view=preview(server,dict(input=draft))
                views.append(dict(position=position,counts=view['counts'],filled_cards=len(view['cards']),advice_ids=[c['candidate_id'] for c in view['cards'] if c.get('candidate_id')]))
            review=assess();weekly=review_store(server).weekly(review['rows'])
            official=facts_response()
            initial=json.loads((ROOT/'evidence/queue/v21/history/initial/counter-review.json').read_text())
            return dict(schema_version='queue-v21.report.v1',created_at=datetime.now(timezone.utc).isoformat(),scope='Golden10 synthetic projection; REAL anonymous Q15 and actual official archive; no actual game-PC proof',patch='16.20',
                auto_review={k:review[k] for k in ('passed','held','reasons','user_decisions_created')},
                history=dict(initial_counter_held=sum(r['verdict']=='HOLD' for r in initial['reviews']),initial_evidence_held=1,improvements=['수동 무효 조건을 아군 미니맵 관측과 분리','유나라의 인용 밖 원인·용어 제거','럭스 조합 적용 조건 명시']),
                official=dict(source_patch=official['source_patch'],champions=len(official['champions']),abilities=sum(len(c['facts']) for c in official['champions'])),
                example_views=views,example_total=dict(Counter({level:sum(v['counts'].get(level,0) for v in views) for level in ('OFFICIAL','STATISTICS','USER','AUTO_VERIFIED','HYPOTHESIS')})),
                legacy_user_approved_tactical_slots=dict(filled=_coverage([],patch='16.20'),total=45,reason='Legacy45 conclusion slots remain REVIEWED-only; separate PC evidence cards are counted above, not coerced into conclusions.'),
                weekly_random_five=weekly,actual_windows_lcu='BLOCKED_EXTERNAL',coaching_accuracy=None)
        finally:server.server_close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    value=report();raw=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(raw,encoding='utf-8')
    else:print(raw,end='')


if __name__=='__main__':main()

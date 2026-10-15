"""New V6 projections with existing completed v2.1 evidence reused verbatim."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def report():
    from coach_v1.recall_candidates import assess_candidates
    from coach_v1.recall_pc import load_datasets
    from coach_v1.pc_coach import preview
    from coach_v1.pc_runtime import load_pc_default_datasets
    from coach_v1.official_items import items_response
    from coach_v1.review_queue import GOLDEN
    from coach_v1.pregame_contract import POSITIONS
    from scripts.launch_pc import create_server
    prior_path = ROOT / 'evidence/queue/v21/report.json'
    prior = json.loads(prior_path.read_text())
    source = dict(kind='MANUAL', reference='Golden10 합성 픽 · 실제 경기 입력 아님', observed_at=None, verification='UNVERIFIED')
    slots = [dict(side=side,slot=i+1,champion=champion,position=position,position_candidates=[],uncertainty='합성 예시',champion_source=source,position_source=source,
        runes=dict(status='UNKNOWN',values=[],source=source),summoners=dict(status='UNKNOWN',values=[],source=source))
        for side,team in GOLDEN.items() for i,(position,champion) in enumerate(team.items())]
    with tempfile.TemporaryDirectory(prefix='v23-report-') as t:
        server = create_server(Path(t), port=0)
        try:
            load_pc_default_datasets(server);load_datasets(server)
            views=[]
            for position in POSITIONS:
                draft=dict(title='Golden10 합성 픽',patch='16.20',phase='PRE_GAME',observed_at=None,my_position=position,my_champion=GOLDEN['ALLY'][position],my_slot=POSITIONS.index(position)+1,slots=slots,source=source,original_capture=None)
                view=preview(server, dict(input=draft))
                views.append(dict(position=position, counts=view['counts'], filled_cards=sum(c['evidence_level']!='UNKNOWN' for c in view['cards']),
                    unknown_cards=sum(c['evidence_level']=='UNKNOWN' for c in view['cards']), sections=dict(Counter(c['section'] for c in view['cards']))))
            new=assess_candidates();old=prior['auto_review']
            return dict(schema_version='queue-v23.report.v1',created_at=datetime.now(timezone.utc).isoformat(),
                previous_evidence=dict(path=str(prior_path.relative_to(ROOT)),sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest(),reused_without_revalidation=True),
                auto_review=dict(passed=old['passed']+new['passed'],held=old['held']+new['held'],existing_completed=old,new_candidates=new,user_decisions_created=0),
                official_items={k:v for k,v in items_response('16.20').items() if k!='items'},
                recall_datasets={p:d.summary() for p,d in server.recall_datasets.items()},
                example_views=views,example_total={level:sum(v['counts'].get(level,0) for v in views) for level in ('OFFICIAL','STATISTICS','USER','AUTO_VERIFIED','HYPOTHESIS','UNKNOWN')},
                actual_user_decisions_created=len(server.research.list()),actual_windows_lcu='BLOCKED_EXTERNAL',
                coaching_accuracy=None,scope='Golden10 synthetic picks, original official archives and available REAL anonymous datasets. No actual game-PC proof.')
        finally:
            server.server_close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    raw=json.dumps(report(),ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(raw,encoding='utf-8')
    else:print(raw,end='')


if __name__=='__main__':main()

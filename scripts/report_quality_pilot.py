"""Report existing observations and complete before/after text, never efficacy."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
Q15='data/riot/2026-10-13/archives/full-power-16.20-CHALLENGER.json.gz'


def matchup_bins(data,champion,opponent,position):
    rows=[c for c in data['cohorts'] if (c['champion'],c['opponent_champion'],c['position'],c['comparison'],c['metric'],c['patch'],c['tier'])==(champion,opponent,position,'MATCHUP','gold_delta','16.20','CHALLENGER')]
    if len(rows)>1:raise ValueError('AMBIGUOUS_MATCHUP_COHORT')
    return dict(champion=champion,opponent_champion=opponent,position=position,patch='16.20',population='Q15_CHALLENGER_SEED_275',
        status='EXISTING_AGGREGATE_ONLY' if rows else 'UNKNOWN_NO_MATCHUP_COHORT',
        unit='GOLD_ABSOLUTE_DIFFERENCE_SAMPLED_MINUTE_BIN',
        points=[p for p in rows[0]['points'] if p['minute'] in (10,15)] if rows else [],
        missing_n=None,missing_reason='AGGREGATE_DOES_NOT_RETAIN_MATCHUP_ELIGIBLE_TOTAL',
        limitation='Bin frame times are not exact10:00/15:00. No pooled fallback. Existing precision omissions retained. Not advice efficacy.')


def report():
    from coach_v1.pilot_advice import load_packet,review_receipts
    from coach_v1.pilot_observations import load_bound_report
    packet=load_packet();reviews=review_receipts(packet)
    full=json.loads(gzip.decompress((ROOT/Q15).read_bytes()))
    offline=ROOT/'data/coaching_quality/2026-10-16/observations.json'
    observations,binding=load_bound_report(offline.parent) if offline.exists() else (None,None)
    return dict(schema_version='quality-pilot.report.v1',base_main='9da650ae1ec000f3bb66d90be351174fe3c731f3',
        existing_inventory=json.loads((ROOT/'evidence/quality-pilot/inventory.json').read_text()),
        previous_reports_reused=['evidence/queue/v23/report.json','evidence/queue/v23/actual-data-audit.json','evidence/queue/v21/report.json'],
        packet_sha256=hashlib.sha256((ROOT/'knowledge_candidates/coaching-quality-pilot.json').read_bytes()).hexdigest(),
        improvements=[dict(id=r['id'],legacy_id=r['legacy_id'],topic=r['topic'],evidence_level=r['evidence_level'],
            before=r['previous_advice'],after=dict(scenario=r['scenario'],actions=r['actions'],opponent_right=r['opponent_right']),
            change=r['change_explanation'],source_facts=r['source_facts'],needed_evidence=r['needed_evidence'],
            factual_review='PASS',conditional_wording_review='PASS',tactical_interpretation='HOLD',real_game_effect='NOT_ASSESSED') for r in packet['rows']],
        old_hold20='UNCHANGED; no ranking/wave/recall safety inferred from skill descriptions',
        q15_source=dict(path=Q15,sha256=hashlib.sha256((ROOT/Q15).read_bytes()).hexdigest(),matches=275),
        q15_matchup_bins=[matchup_bins(full,*query) for query in [('Ornn','Fiora','TOP'),('Ahri','Zed','MID'),('Caitlyn','Ezreal','BOTTOM')]],
        q15_to_advice_gap='Sampled resource differences do not observe parry/charm/net/scouting choices; no action endorsement inferred.',
        offline_observations=observations,offline_source_binding=binding,offline_status='AVAILABLE' if observations else 'PENDING_TRUSTED_EXISTING_CACHE_AUDIT',
        scene_evaluation=dict(eligible=0,executed=0,selected_individual_scenes=0,unassessable_scene_count=None,
            reason='No matched player-known-view/POV receipt; do not turn89matches into89identified scenes',
            action_agreement=None,proxy_action_agreement=None,generator_executed=False,evaluator_executed=False),
        user_decisions_created=0,approval_inherited=False,new_match_requests=0,paid_calls=0,coaching_accuracy=None)


def comparison_markdown(data):
    out=['# 7개 조언 소규모 개선 — 원문 비교','',
        '원문·기존 승인·보류 이력은 보존한다. 새 문장은 모두 미검토 가설이며 전술 해석은 HOLD다.',
        '문장 조건 검토·출처 사실 확인은 숙련자 검증이나 실경기 효과 검증이 아니다.','']
    for row in data['improvements']:
        out+=['## '+row['legacy_id']+' → '+row['id'],'','주제: 스킬 상호작용 / 근거 수준: 미검토 가설','',
              '### 개선 전 — 원문','']
        out += [k+': '+v+'  ' for k,v in row['before'].items()]
        out+=['','### 개선 후 — 원문','','상황: '+row['after']['scenario'],'']
        for action in row['after']['actions']:
            out += ['선택 '+action['id']+': '+action['text'],'',
                '선택 조건(모두): '+' / '.join(action['choose_if']),'',
                '중단 조건(하나라도): '+' / '.join(action['stop_if']),'',
                '불확실할 때 대안: '+' / '.join(action['uncertain_alternative']),'']
        out+=['상대 권리: '+row['after']['opponent_right'],'','달라진 점: '+row['change'],'',
              '보류 해소에 필요한 자료: '+' / '.join(row['needed_evidence']),'']
    return '\n'.join(out)+'\n'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--comparison',type=Path);args=parser.parse_args()
    data=report();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    if args.comparison:args.comparison.write_text(comparison_markdown(data))


if __name__=='__main__':main()

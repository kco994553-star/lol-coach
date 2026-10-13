#!/usr/bin/env python3
"""Trusted job entrypoint: env key in, validated anonymous aggregate out."""
import argparse
from datetime import datetime, timezone
import json
import gzip
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.power_stats import TIERS, validate_power_dataset
from coach_v1.riot_collector import RiotCollector, collection_tier
from coach_v1.power_accumulator import PowerAccumulator
from coach_v1.collection_progress import validate_progress


def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+'\n')
    os.replace(temporary,path)


def publish_accumulator(accumulator,directory):
    if not directory:return
    state=accumulator.to_dict()
    keys={(d['source']['patch'],d['source']['tier']) for d in state['legacy']+state['buckets']}
    for patch,tier in sorted(keys):
        if patch is None:continue
        dataset=accumulator.dataset(patch,tier)
        write_json(Path(directory)/('power-'+patch+'-'+tier+'.json'),dataset)
        progress=validate_progress(accumulator.progress(patch,tier),dataset)
        write_json(Path(directory)/('progress-'+patch+'-'+tier+'.json'),progress)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--movement-output',help='optional anonymous movement companion; absent on blocked collection')
    parser.add_argument('--outcome-output',help='optional anonymous ending-duration outcome companion; absent on blocked collection')
    parser.add_argument('--diagnostics-output',help='safe key-shape and selected HTTP error metadata only')
    parser.add_argument('--tier',choices=TIERS)
    parser.add_argument('--rotation',type=int,default=0,help='default CHALLENGER/GRANDMASTER/MASTER seed rotation')
    parser.add_argument('--user-tier',choices=TIERS,help='explicit U2-confirmed user-tier cohort')
    parser.add_argument('--accumulator',help='anonymous sufficient-state JSON or JSON.gz; atomically preserved across runs')
    parser.add_argument('--aggregate-directory',help='write patch/tier power and digest-bound progress companions')
    parser.add_argument('--seed-data',help='retained legacy summary reusable as evidence, never blindly merged')
    parser.add_argument('--publish-only',action='store_true',help='restore/publish existing state; makes no provider call')
    parser.add_argument('--user-reported-key-expired',action='store_true',help='separate user attribution, not HTTP-inferred expiry')
    parser.add_argument('--division',choices=('I','II','III','IV'),default='I')
    parser.add_argument('--patch',help='exact gameplay patch; omitted pins first eligible match patch')
    parser.add_argument('--start-time',type=int)
    parser.add_argument('--end-time',type=int)
    parser.add_argument('--lookback-days',type=int,default=7)
    for option,default in [('max-matches',300),('max-requests',650),('max-pages',1),('max-players',40),('max-retries',2),('deadline-seconds',900)]:
        parser.add_argument('--'+option,type=int,default=default)
    parser.add_argument('--no-item-markers',action='store_true')
    parser.add_argument('--max-gold-ci-width',type=float)
    parser.add_argument('--max-xp-ci-width',type=float)
    parser.add_argument('--max-cs-ci-width',type=float)
    args=parser.parse_args(argv)
    paths=[Path(p).resolve() for p in (args.output,args.movement_output,args.outcome_output,args.diagnostics_output,args.accumulator) if p]
    if len(paths)!=len(set(paths)):
        parser.error('aggregate and diagnostics outputs must be different paths')
    if args.lookback_days<1:parser.error('lookback-days must be positive')
    try:
        tier=args.tier or collection_tier(args.rotation,args.user_tier)
        accumulator=PowerAccumulator.load(args.accumulator) if args.accumulator and Path(args.accumulator).exists() else PowerAccumulator()
        if args.seed_data:
            path=Path(args.seed_data)
            with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as input_file:
                accumulator.seed_legacy(json.load(input_file))
        if args.publish_only:
            if not args.accumulator:parser.error('publish-only requires an accumulator')
            publish_accumulator(accumulator,args.aggregate_directory);accumulator.save(args.accumulator)
            state=accumulator.to_dict();available=state['legacy']+state['buckets']
            if available:
                representative=max(available,key=lambda d:d['source'].get('retrieved_at') or '')['source']
                write_json(args.output,accumulator.dataset(representative['patch'],representative['tier']))
            print(json.dumps(dict(status='RESTORED_DERIVED_STATE',request_count=0,coaching_accuracy=None)))
            return 0
    except (ValueError,OSError,EOFError,json.JSONDecodeError):
        parser.error('invalid retained accumulator or seed; no provider call made')
    end=args.end_time if args.end_time is not None else int(datetime.now(timezone.utc).timestamp())
    start=args.start_time if args.start_time is not None else max(0,end-args.lookback_days*86400)
    limits={name:getattr(args,name) for name in ('max_matches','max_requests','max_pages','max_players','max_retries','deadline_seconds')}
    overrides={metric:value for metric,value in [('gold_delta',args.max_gold_ci_width),('xp_delta',args.max_xp_ci_width),('cs_delta',args.max_cs_ci_width)] if value is not None}
    first_receipt_emitted=False
    def first_http_receipt(status_code):
        nonlocal first_receipt_emitted
        print('RIOT_FIRST_HTTP_RECEIPT_JSON='+json.dumps({'status_code':status_code}),flush=True)
        first_receipt_emitted=True
    def key_shape_receipt(shape):
        print('RIOT_KEY_SHAPE_RECEIPT_JSON='+json.dumps(shape),flush=True)
    def http_error_receipt(diagnostic):
        print('RIOT_HTTP_ERROR_RECEIPT_JSON='+json.dumps(diagnostic),flush=True)
    def front_error_receipt(observation):
        print('RIOT_FRONT_HTTP_ERROR_RECEIPT_JSON='+json.dumps(observation),flush=True)
    try:
        collector=RiotCollector(**limits,on_first_http_response=first_http_receipt,
            on_key_shape=key_shape_receipt,on_http_error=http_error_receipt,on_front_error=front_error_receipt)
        result=collector.collect(tier=tier,division=args.division,patch=args.patch,
            start_time=start,end_time=end,collect_items=not args.no_item_markers,ci_width_limits=overrides or None,
            collect_movement=bool(args.movement_output),collect_outcome=bool(args.outcome_output),
            known_match_hashes=accumulator.known_hashes(args.patch,tier) if args.accumulator else ())
        result=validate_power_dataset(result)
    except ValueError:
        parser.error('invalid collection arguments or unsafe aggregate; no output written')
    if not first_receipt_emitted:first_http_receipt(None)
    if args.diagnostics_output:
        diagnostics=dict(schema_version='riot.diagnostics.v2',key_shape=collector.key_shape,
            first_http_status=collector.first_http_status,http_errors=collector.http_errors,front_errors=collector.front_errors,
            collection_status=result['status'],collection_reason=result['source']['collection']['reason'],
            user_key_expiry_attribution='USER_REPORTED_EXPIRED' if args.user_reported_key_expired else 'UNKNOWN',
            request_count=collector.requests,retry_count=collector.retries,coaching_accuracy=None)
        path=Path(args.diagnostics_output);path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_name(path.name+'.tmp')
        temporary.write_text(json.dumps(diagnostics,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+'\n')
        os.replace(temporary,path)
    if args.accumulator:
        if result['source']['patch'] is not None:
            cumulative=accumulator.add_records(collector.sufficient_records,source=result['source'])
            # Acquisition status remains in diagnostics; usable retained history
            # remains visible even when this run stopped on its first auth error.
            if cumulative['samples']['real_matches']+cumulative['samples']['synthetic_matches']>0:result=cumulative
        accumulator.save(args.accumulator)
        publish_accumulator(accumulator,args.aggregate_directory)
    if not collector.key_shape['valid_shape']:
        # A malformed or missing credential creates only a diagnostic receipt.
        # Remove requested stale aggregates so old values cannot be uploaded.
        for value in (args.output,args.movement_output,args.outcome_output):
            if value:Path(value).unlink(missing_ok=True)
        print(json.dumps(dict(status='BLOCKED_EXTERNAL',collection_reason=result['source']['collection']['reason'],
            request_count=0,coaching_accuracy=None,movement_status=collector.movement_status,outcome_status=collector.outcome_status)))
        return 0
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+'.tmp')
    temporary.write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+'\n')
    os.replace(temporary,output)
    if args.movement_output:
        movement_output=Path(args.movement_output)
        if collector.movement_data is None:
            movement_output.unlink(missing_ok=True)
        else:
            from coach_v1.movement import validate_movement_dataset
            movement=validate_movement_dataset(collector.movement_data)
            movement_output.parent.mkdir(parents=True,exist_ok=True)
            temporary=movement_output.with_name(movement_output.name+'.tmp')
            temporary.write_text(json.dumps(movement,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+'\n')
            os.replace(temporary,movement_output)
    if args.outcome_output:
        outcome_output=Path(args.outcome_output)
        if collector.outcome_data is None:
            outcome_output.unlink(missing_ok=True)
        else:
            from coach_v1.outcome_stats import validate_outcome_dataset
            outcome=validate_outcome_dataset(collector.outcome_data)
            outcome_output.parent.mkdir(parents=True,exist_ok=True)
            temporary=outcome_output.with_name(outcome_output.name+'.tmp')
            temporary.write_text(json.dumps(outcome,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+'\n')
            os.replace(temporary,outcome_output)
    # Do not echo paths or response text; only fixed metadata and aggregate counts.
    print(json.dumps(dict(status=result['status'],samples=result['samples']['real_matches'],
        coaching_accuracy=None,collection_reason=result['source']['collection']['reason'],movement_status=collector.movement_status,
        outcome_status=collector.outcome_status)))
    return 0


if __name__=='__main__':sys.exit(main())

"""Recheck pinned R7 source fields; does not import real data into the coach."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coach_audit.extraction import extract
from coach_intake.io import strict_json, write_json


def verify(match_path, timeline_path):
    reference_path = ROOT / 'fixtures/r7-continuation/structured-source-reference.json'
    receipts_path = ROOT / 'evidence/r7-continuation/source-range-receipts.json'
    reference = strict_json(reference_path.read_bytes())
    receipts = strict_json(receipts_path.read_bytes())
    canonical_fields = json.dumps(reference['fields'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    if hashlib.sha256(canonical_fields).hexdigest() != reference['fields_canonical_sha256']:
        raise ValueError('REFERENCE_FIELDS_CHANGED')
    records, diagnostics = {}, {}
    for kind, path in (('match', match_path), ('timeline', timeline_path)):
        receipt = next(r for r in receipts if r['source'] == kind)
        with path.open('rb') as handle:
            raw = handle.read(receipt['bytes'] + 1)
        if len(raw) != receipt['bytes'] or hashlib.sha256(raw).hexdigest() != receipt['sha256']:
            raise ValueError('SOURCE_BYTES_CHANGED:' + kind)
        records[kind] = strict_json(raw)
        diagnostic = extract(raw, expected_sha=receipt['sha256'])
        diagnostics[kind] = dict(selected_paths=len(diagnostic['raw']),
            present=sum(r['state'] == 'PRESENT' for r in diagnostic['raw']),
            status='UNSUPPORTED_MATCH_TIMELINE_SCHEMA',
            derived=diagnostic['derived'], player_state=diagnostic['player_information_state'])
    if records['match']['metadata'] != records['timeline']['metadata']:
        raise ValueError('MATCH_METADATA_JOIN_REJECTED')
    compared = []
    for field in reference['fields']:
        value = records[field['source']]
        for part in field['pointer'].split('/')[1:]:
            part = part.replace('~1', '/').replace('~0', '~')
            value = value[int(part)] if isinstance(value, list) else value[part]
        equal = type(value) is type(field['expected']) and value == field['expected']
        compared.append(dict(source=field['source'], pointer=field['pointer'], equal=equal))
    if not all(r['equal'] for r in compared):
        raise ValueError('SOURCE_REFERENCE_MISMATCH')
    return dict(schema_version='r7.source-reference-recheck.v1',
        reference_status='ESTABLISHED_SOURCE_FIELD_REFERENCE', scope='POST_GAME_DATASET',
        source_origin='PUBLISHER_ATTESTED_RIOT_COLLECTION_NOT_INDEPENDENTLY_AUTHENTICATED',
        source_field_checks=compared, source_field_matches=len(compared),
        current_extractor=diagnostics,
        player_information_state_verified=False, verified_player_state_variables=0,
        engine_executed=False, coaching_validation_N=0, coaching_accuracy=None,
        input_sha256={str(reference_path.relative_to(ROOT)): hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                      str(receipts_path.relative_to(ROOT)): hashlib.sha256(receipts_path.read_bytes()).hexdigest(),
                      'scripts/verify_r7_source_reference.py': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--match', type=Path, required=True)
    parser.add_argument('--timeline', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.match, args.timeline)
    write_json(args.out, result)
    print(json.dumps(dict(source_field_matches=result['source_field_matches'],
                         scope=result['scope'], verified_player_state_variables=0, coaching_N=0)))

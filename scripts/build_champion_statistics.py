"""Deterministic public champion statistics from manifest-bound local snapshots."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coach_v1.champion_stats import build_champion_statistics
from coach_v1.state import digest

OUTCOME = Path('data/riot/2026-10-11/outcome-data.json.gz')
POWER = Path('data/riot/2026-10-13/archives/full-power-16.20-CHALLENGER.json.gz')


def _read_bound(path, encoded_digest, decoded_digest, canonical_digest):
    encoded = (ROOT / path).read_bytes()
    if hashlib.sha256(encoded).hexdigest() != encoded_digest:
        raise ValueError('snapshot gzip hash mismatch: ' + str(path))
    decoded = gzip.decompress(encoded)
    if hashlib.sha256(decoded).hexdigest() != decoded_digest:
        raise ValueError('snapshot decoded hash mismatch: ' + str(path))
    value = json.loads(decoded)
    if digest(value) != canonical_digest:
        raise ValueError('snapshot canonical digest mismatch: ' + str(path))
    return value


def project():
    manifest = json.loads((ROOT / 'data/riot/2026-10-11/manifest.json').read_text())
    entry = manifest['files']['outcome-data.json']
    outcome = _read_bound(OUTCOME, entry['gzip_sha256'], entry['sha256'], entry['dataset_digest'])
    for key, expected in (('patch', '16.20'), ('platform', 'KR'), ('queue_id', 420),
                          ('tier', 'CHALLENGER'), ('sample_kind', 'REAL')):
        if outcome['source'][key] != expected:
            raise ValueError('outcome snapshot scope mismatch')
    if outcome['samples']['real_matches'] != manifest['real_matches']:
        raise ValueError('outcome snapshot match count mismatch')
    power_manifest = json.loads((ROOT / 'data/riot/2026-10-13/manifest.json').read_text())
    power_entry = next(row for row in power_manifest['datasets'] if row['patch'] == '16.20')
    power = _read_bound(POWER, power_entry['archive_sha256'],
                        power_entry['original_file_sha256'], power_entry['original_canonical_sha256'])
    # Validation proves the archive's actual contract. It has no cohort-member
    # hashes, so per-minute n cannot establish exact champion-role union counts.
    result = build_champion_statistics(outcome, growth_dataset=power)
    result['growth_source'].update(local_source=POWER.as_posix(), sha256=power_entry['archive_sha256'])
    result['source'].update(local_source=OUTCOME.as_posix(), sha256=entry['gzip_sha256'])
    result['position_source'].update(
        local_source=OUTCOME.as_posix(), sha256=entry['gzip_sha256'],
        fallback_reason='POWER_ARCHIVE_HAS_NO_COHORT_MEMBER_HASHES_FOR_UNIQUE_ROLE_COUNTS',
        considered_source=POWER.as_posix(),
        considered_source_digest=power_entry['original_canonical_sha256'],
        considered_source_matches=power['samples']['real_matches'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'web_r4/champion-stats.json')
    args = parser.parse_args()
    value = project()
    args.output.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')
    print(f'Wrote {args.output}: {len(value["champions"])} champions; '
          f'{value["source"]["matches"]} outcome matches; '
          f'{value["position_source"]["matches"]} coverage matches')


if __name__ == '__main__':
    main()

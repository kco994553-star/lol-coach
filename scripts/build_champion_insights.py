"""Build aggregate-only tier/opponent insights from bounded local evidence.

No credential access or acquisition. The default legacy snapshot is bound to
its checked-in manifest; explicit local companions pass strict validators.
"""
import argparse
import gzip
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coach_v1.champion_insights import build_champion_insights
from scripts.build_champion_statistics import OUTCOME, _read_bound


def _load(path):
    path = Path(path)
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('local evidence exceeds input size bound')
    encoded = path.read_bytes()
    maximum = 128 * 1024 * 1024
    if path.suffix == '.gz':
        with gzip.GzipFile(fileobj=io.BytesIO(encoded)) as stream:
            decoded = stream.read(maximum + 1)
    else:
        decoded = encoded
    if len(decoded) > maximum:
        raise ValueError('decoded local evidence exceeds input size bound')
    return json.loads(decoded)


def project(*, outcome_paths=None, result_paths=()):
    if outcome_paths is None:
        manifest = json.loads((ROOT / 'data/riot/2026-10-11/manifest.json').read_text())
        entry = manifest['files']['outcome-data.json']
        outcome = _read_bound(OUTCOME, entry['gzip_sha256'], entry['sha256'], entry['dataset_digest'])
        if any(outcome['source'][key] != value for key, value in
               (('patch', '16.20'), ('platform', 'KR'), ('queue_id', 420), ('tier', 'CHALLENGER'), ('sample_kind', 'REAL'))):
            raise ValueError('manifest outcome scope mismatch')
        if outcome['samples']['real_matches'] != manifest['real_matches']:
            raise ValueError('manifest outcome count mismatch')
        outcomes = [outcome]
    else:
        outcomes = [_load(path) for path in outcome_paths]
    return build_champion_insights(outcomes, result_datasets=[_load(path) for path in result_paths])


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'web_r4/champion-insights.json')
    parser.add_argument('--outcome', type=Path, action='append', default=None,
                        help='Explicit validated local outcome snapshot; repeat for disjoint inputs')
    parser.add_argument('--results', '--result', type=Path, action='append', default=[],
                        help='Private anonymous result companion; only aggregates are emitted')
    parser.add_argument('--check', action='store_true', help='Compare deterministic output without writing')
    args = parser.parse_args()
    content = encoded(project(outcome_paths=args.outcome, result_paths=args.results))
    if args.check:
        if not args.output.is_file() or args.output.read_text() != content:
            raise SystemExit('champion insights projection is stale')
        print('Champion insights projection matches local validated evidence')
    else:
        args.output.write_text(content)
        print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()

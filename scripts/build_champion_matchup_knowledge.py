"""Build the public qualitative guide projection without network or raw guide text."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coach_v1.champion_matchup_knowledge import build_knowledge


def project():
    read = lambda path: json.loads((ROOT / path).read_text())
    return build_knowledge(read('config/champion_matchup_references.json'),
                           read('web_r4/loading-data.json'), read('web_r4/loading-knowledge.json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'web_r4/champion-matchup-knowledge.json')
    args = parser.parse_args()
    encoded = json.dumps(project(), ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if args.check:
        if not args.output.exists() or args.output.read_text() != encoded:
            print('Champion matchup knowledge artifact is missing or stale.', file=sys.stderr)
            return 1
        print('Champion matchup knowledge artifact matches curated references.')
    else:
        args.output.write_text(encoded)
        print('Wrote ' + str(args.output))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

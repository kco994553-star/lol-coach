#!/usr/bin/env python3
"""Build/check the public, offline-only learning-room reference index."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coach_v1.learning_room import build_index  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if checked-in projection differs')
    args = parser.parse_args()
    output = ROOT / 'web_r4/learning-room.json'
    rendered = json.dumps(build_index(ROOT), ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if args.check:
        if not output.exists() or output.read_text() != rendered:
            print('learning-room.json is stale; run python scripts/build_learning_room.py', file=sys.stderr)
            return 1
        print('learning-room.json is current')
    else:
        output.write_text(rendered)
        print('Wrote web_r4/learning-room.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

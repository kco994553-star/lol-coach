#!/usr/bin/env python3
"""Build/check the public, offline-only learning-room reference index."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coach_v1.learning_room import build_index  # noqa: E402


def same_destination(first, second):
    return first.resolve() == second.resolve() or (first.exists() and second.exists() and first.samefile(second))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if checked-in projection differs')
    parser.add_argument('--accepted-inputs', type=Path, help='explicit permitted offline transcript manifest; no network')
    parser.add_argument('--output', type=Path, default=ROOT / 'web_r4/learning-room.json', help='metadata projection destination')
    args = parser.parse_args()
    accepted = []
    if args.accepted_inputs:
        manifest = json.loads(args.accepted_inputs.read_text(encoding='utf-8'))
        for record in manifest['transcripts']:
            raw_path = (args.accepted_inputs.resolve().parent / record['path']).resolve()
            if same_destination(raw_path, args.output):
                parser.error('output must not overwrite protected transcript raw input')
            accepted.append(dict(raw_bytes=raw_path.read_bytes(), video_id=record['video_id'],
                access_state=record['access_state'], license_or_access_state=record['license_or_access_state'],
                source_provenance=record['source_provenance'], topic_assignments=record.get('topic_assignments')))
    output = args.output
    if args.accepted_inputs and same_destination(output, args.accepted_inputs):
        parser.error('output must not overwrite the accepted-input manifest')
    for source in ['web_r4/loading-knowledge.json', 'config/user_lesson_candidates.json', 'config/learning_topics.json']:
        if same_destination(output, ROOT / source):
            parser.error('output must not overwrite an existing source registry input')
    rendered = json.dumps(build_index(ROOT, accepted_transcripts=accepted), ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if args.check:
        if not output.exists() or output.read_text(encoding='utf-8') != rendered:
            print('learning-room.json is stale; run python scripts/build_learning_room.py', file=sys.stderr)
            return 1
        print('learning-room.json is current')
    else:
        output.write_text(rendered, encoding='utf-8')
        print('Wrote learning-room metadata projection')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

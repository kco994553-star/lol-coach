#!/usr/bin/env python3
"""Write public metadata and a source binding; never modify channel config."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coach_v1.expert_collector import atomic_json
from coach_v1.pov_metadata import verify_channels


def main(argv=None, *, clock=time.time):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/pov_channels.json'))
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    raw = None
    try:
        raw = args.config.read_bytes()
        if len(raw) > 200_000: raise ValueError
        config = json.loads(raw)
    except (OSError, ValueError, UnicodeError):
        config = None
    report = verify_channels(config, os.environ.get('YOUTUBE_API_KEY'), now=clock)
    report_path = args.output_dir / 'pov-metadata.json'
    atomic_json(report_path, report)
    binding = dict(schema_version='pov.metadata-binding.v1', category='POV', expert_source=False,
                   checked_at=report['checked_at'], status=report['status'], reason=report['reason'],
                   source_commit=None, source_sha256={}, report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
                   request_counts=report['request_counts'], diagnostics=report['diagnostics'],
                   media_downloads=0, transcript_downloads=0, retries=0)
    result = 0
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, stderr=subprocess.DEVNULL, timeout=10).decode().strip()
        if len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit): raise ValueError
        binding['source_commit'] = commit
        sources = [ROOT/'coach_v1/pov_metadata.py', ROOT/'scripts/verify_pov_metadata.py',
                   args.config.resolve(), ROOT/'contracts/actual-evidence-v1.md']
        for path in sources:
            label = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
            content = raw if path == args.config.resolve() and raw is not None else path.read_bytes()
            binding['source_sha256'][label] = hashlib.sha256(content).hexdigest()
    except (OSError, ValueError, subprocess.SubprocessError):
        binding.update(status='BLOCKED_EXTERNAL', reason='SOURCE_BINDING_UNAVAILABLE')
        result = 1
    atomic_json(args.output_dir/'metadata-binding.json', binding)
    print('POV_METADATA_JSON=' + json.dumps({key: binding[key] for key in ('status', 'reason', 'request_counts')}, sort_keys=True))
    return result


if __name__ == '__main__':
    raise SystemExit(main())

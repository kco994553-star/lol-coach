"""Refresh complete public Korean champion facts without credentials."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coach_v1.official_catalog import refresh_if_due


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='check CDN even if refreshed recently')
    parser.add_argument('--max-age-seconds', type=int, default=86400)
    args = parser.parse_args()
    result = refresh_if_due(force=args.force, max_age_seconds=args.max_age_seconds)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['state'] in ('UPDATED', 'UNCHANGED', 'FRESH', 'OFFLINE_FALLBACK') else 1


if __name__ == '__main__':
    raise SystemExit(main())

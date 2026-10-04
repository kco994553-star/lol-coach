"""Offline diagnostic only. Uses existing exclusive output and strict JSON handling."""
import argparse
from pathlib import Path
from coach_intake.io import write_json
from .extraction import extract

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--max-bytes',type=int,required=True)
    args=parser.parse_args()
    if args.max_bytes <= 0:parser.error('max-bytes must be positive')
    with args.input.open('rb') as handle:raw=handle.read(args.max_bytes+1)
    if len(raw)>args.max_bytes:parser.error('SIZE_LIMIT')
    write_json(args.out,extract(raw))
    print('Diagnostic written; player reference and real coaching remain unverified.')
if __name__=='__main__':main()

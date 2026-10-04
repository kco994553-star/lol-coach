import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError
from .models import ReviewInput
from .engine import run_review, ModeBlocked


def main(argv=None):
    parser=argparse.ArgumentParser(description='R3 offline synthetic review runner')
    parser.add_argument('fixture',type=Path)
    parser.add_argument('--synthetic',action='store_true',help='Explicitly enable development-only TEST mode')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    try:
        case=ReviewInput.model_validate_json(args.fixture.read_text(encoding='utf-8'))
        report=run_review(case,allow_synthetic=args.synthetic)
        text=json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
        if args.output:
            if args.output.resolve()==args.fixture.resolve():
                raise ValueError('input/output paths must differ')
            args.output.parent.mkdir(parents=True,exist_ok=True)
            # Refuse silent evidence overwrite; each report path is a new artifact.
            with args.output.open('x',encoding='utf-8') as f:f.write(text)
        else:sys.stdout.write(text)
        return 0
    except (ValidationError,ModeBlocked,ValueError,OSError) as e:
        # Error content may contain private field values in validation errors.
        sys.stderr.write(json.dumps({'error_code':type(e).__name__,'message':'Input rejected or output unavailable. Validate contract, mode and file paths.','retryable':False})+'\n')
        return 2


if __name__=='__main__':
    raise SystemExit(main())

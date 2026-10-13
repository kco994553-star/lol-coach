#!/usr/bin/env python3
"""Encrypt/decrypt private runner storage without printing any identity or Secret."""
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.private_pro_bundle import encrypt_directory,decrypt_directory

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=['encrypt','decrypt'])
    p.add_argument('--directory',required=True);p.add_argument('--bundle',required=True)
    args=p.parse_args()
    try:
        seed=os.environ.get('PRO_REFERENCE_ENCRYPTION_SEED','')
        operation=encrypt_directory if args.phase=='encrypt' else decrypt_directory
        result=operation(args.directory,args.bundle,seed) if args.phase=='encrypt' else operation(args.bundle,args.directory,seed)
        print(json.dumps(result));return 0
    except (ValueError,OSError,ImportError):
        print(json.dumps({'status':'BLOCKED_EXTERNAL','reason':'PRIVATE_CACHE_RECOVERY_OR_KEY_UNAVAILABLE'}));return 2

if __name__=='__main__':raise SystemExit(main())

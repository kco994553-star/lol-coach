"""Import registered user issue comments into the normal local workbench DB."""
import argparse
import json
from pathlib import Path
import secrets
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from coach_v1.practical_review import sync_github
from coach_v1.pregame_server import PregameWorkbench
from coach_v1.server import Limits


def main():
    parser=argparse.ArgumentParser(description='GitHub 사용자 결정 댓글 읽기·반영')
    parser.add_argument('--db',type=Path,required=True,help='서버에서 사용하는 --db와 같은 경로; 서버를 먼저 종료하세요.')
    args=parser.parse_args()
    server=PregameWorkbench(args.db,secrets.token_hex(32),Limits(1_000_000,100,100,100,100,10))
    try:print(json.dumps(sync_github(server.research),ensure_ascii=False,indent=2))
    finally:server.server_close()


if __name__=='__main__':main()

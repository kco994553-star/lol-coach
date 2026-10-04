"""Windows/macOS/Linux manual one-shot entrypoint; requires no pip dependencies."""
from datetime import datetime,timezone
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
if sys.version_info<(3,10):raise SystemExit('Python 3.10+ required. No data collected.')
from coach_intake.__main__ import acquire

if __name__=='__main__':
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'private'/('capture-'+stamp)
    print('One local capture. No account, API key, payment, upload, or gameplay advice.')
    print('Start a LoL game on this computer before running this tool.')
    result=acquire(out,'local',2_000_000,10)
    print('Result directory:',out)
    print('OK' if result['passed'] else 'Capture unavailable: '+result.get('error_code','UNKNOWN'))
    print('Only audit.json is intended as an identifier-free diagnostic; raw.json stays private.')
    raise SystemExit(0 if result['passed'] else 1)

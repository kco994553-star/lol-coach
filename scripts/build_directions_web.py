"""Export an explicit public allowlist. Never export the PC app or private data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'dashboard.html':'index.html','dashboard.js':'dashboard.js','dashboard.css':'dashboard.css','pro-dashboard.json':'pro-dashboard.json',
    'loading-wave.js':'loading-wave.js','loading-wave-view.js':'loading-wave-view.js',
    'loading-exploration.js':'loading-exploration.js','loading-interactive.js':'loading-interactive.js',
    'skill-data.js':'skill-data.js','skill-display.js':'skill-display.js',
    'loading.html':'loading.html', 'loading.js':'loading.js',
    'loading.css':'loading.css', 'loading-engine.js':'loading-engine.js',
    'loading-map.js':'loading-map.js', 'loading-data.json':'loading-data.json',
    'pregame-icon.svg':'pregame-icon.svg',
    **{'loading-assets/champion'+str(i)+'.png':'loading-assets/champion'+str(i)+'.png' for i in range(6)},
    'directions.html':'directions.html', 'directions.js':'directions.js',
    'directions.css':'directions.css', 'directions-engine.js':'directions-engine.js',
    'directions-data.json':'directions-data.json', 'directions-status.json':'directions-status.json',
    'status.html':'status.html', 'directions-status.js':'directions-status.js',
    **{'direction-assets/'+p:'direction-assets/'+p for p in ('map11.png','Caitlyn.png','Fiora.png','Ornn.png')},
}


def build(output):
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('EXPORT_DIRECTORY_MUST_BE_EMPTY')
    output.mkdir(parents=True,exist_ok=True)
    hashes={}
    for source,destination in FILES.items():
        p=ROOT/'web_r4'/source
        if p.is_symlink() or not p.is_file():raise ValueError('PUBLIC_SOURCE_NOT_REGULAR')
        target=output/destination;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,target)
        if source=='dashboard.html':
            target.write_text(target.read_text().replace('data-account-backend="PC_LOOPBACK"','data-account-backend="PUBLIC_STATIC"'))
        hashes[destination]=hashlib.sha256(target.read_bytes()).hexdigest()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    manifest=dict(format='lol-coach-loading-public-export-v1',source_commit=commit,
        built_at=datetime.now(timezone.utc).isoformat(),sha256=hashes,
        inputs='Manual ten-pick loading analysis and optional hypothetical scenarios; no persistent inputs or public PC service',
        strategy_level='DESIGN_HYPOTHESIS',live_game_connection=False,coaching_accuracy=None)
    (output/'build-info.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (output/'.nojekyll').write_text('')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    print(json.dumps(build(parser.parse_args().output),ensure_ascii=False))

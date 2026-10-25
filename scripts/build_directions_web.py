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
    **{p:p for p in ('champion-insights.js', 'champion-insights.json', 'champion-matchup-knowledge.json')},
    **{p:p for p in ('learning.html', 'learning.css', 'learning-engine.js', 'learning.js', 'learning-room.json', 'loading-situation.js')},
    **{p:p for p in ('champions.html', 'champion.html', 'champion.css', 'champion-state.js', 'champion-picker.js', 'champion-page.js', 'champion-stats.json', 'loading-draft.js')},
    **{p:p for p in ("loading-presentation.js","loading-presentation.css")},
    'formation-ranges.js':'formation-ranges.js',
    'loading-formation.js':'loading-formation.js',
    **{p:p for p in ('game-info.html','game-info.js','game-info-engine.js','game-info.css','game-info-items.json')},
    'riot.txt':'riot.txt',  # Public Riot app ownership proof; not an API credential.
    'loading-direction-profiles.js':'loading-direction-profiles.js',
    'loading-champion-baseline.js':'loading-champion-baseline.js',
    'loading-planboard.js':'loading-planboard.js','loading-coach.js':'loading-coach.js','loading-coach-view.js':'loading-coach-view.js','loading-coach.css':'loading-coach.css','loading-knowledge.json':'loading-knowledge.json','loading-study.js':'loading-study.js',
    'coach-theme.css':'coach-theme.css','coach-shell.js':'coach-shell.js','hero-art.json':'hero-art.json','home-assets/strategy-panels.webp':'home-assets/strategy-panels.webp',
    **{'home-assets/'+p:'home-assets/'+p for p in ('Ahri.jpg','Caitlyn.jpg','AhriSkin27.jpg','LuxSkin7.jpg','Moonlit.webp','strategy-objectives.webp','lane.jpg','fight.jpg')},
    **{'home-assets/'+p:'home-assets/'+p for p in ('AsheBase.jpg', 'AsheSkin17.jpg', 'KaisaBase.jpg', 'KaisaSkin14.jpg', 'JinxBase.jpg', 'JinxSkin4.jpg', 'EzrealBase.jpg', 'EzrealSkin21.jpg', 'LuxBase.jpg', 'LuxSkin17.jpg', 'YasuoBase.jpg', 'YasuoSkin9.jpg', 'YoneBase.jpg', 'YoneSkin1.jpg', 'IreliaBase.jpg', 'IreliaSkin37.jpg', 'VayneBase.jpg', 'VayneSkin25.jpg', 'LeonaBase.jpg', 'LeonaSkin10.jpg', 'game-lane.webp', 'game-operations.webp', 'game-fight.webp')},
    'dashboard.html':'index.html','dashboard.js':'dashboard.js','dashboard.css':'dashboard.css','pro-dashboard.json':'pro-dashboard.json',
    'loading-exchange.js':'loading-exchange.js','loading-exchange-view.js':'loading-exchange-view.js',
    'loading-engagement.js':'loading-engagement.js','loading-engagement-view.js':'loading-engagement-view.js',
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
        if source in ('loading.html', 'champions.html', 'champion.html'):
            # The PC server rejects queries; cache versioning belongs only to public export.
            html=target.read_text()
            for asset in (name for name in FILES if name.endswith(('.js', '.css'))):
                version=hashlib.sha256((ROOT/'web_r4'/asset).read_bytes()).hexdigest()[:16]
                html=html.replace('src="./'+asset+'"','src="./'+asset+'?v='+version+'"').replace('href="./'+asset+'"','href="./'+asset+'?v='+version+'"')
            target.write_text(html)
        if source=='dashboard.html':
            target.write_text(target.read_text().replace('data-account-backend="PC_LOOPBACK"','data-account-backend="PUBLIC_STATIC"'))
        if source=='game-info.html':
            target.write_text(target.read_text().replace('data-game-backend="PC_LOOPBACK"','data-game-backend="PUBLIC_STATIC"'))
        hashes[destination]=hashlib.sha256(target.read_bytes()).hexdigest()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    manifest=dict(format='lol-coach-loading-public-export-v1',source_commit=commit,
        built_at=datetime.now(timezone.utc).isoformat(),sha256=hashes,
        inputs='Champion reference exploration and manual partial/ten-pick drafts; explicit browser-session storage, no public PC service',
        strategy_level='DESIGN_HYPOTHESIS',live_game_connection=False,coaching_accuracy=None)
    (output/'build-info.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (output/'.nojekyll').write_text('')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    print(json.dumps(build(parser.parse_args().output),ensure_ascii=False))

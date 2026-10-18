"""Official base attack ranges and provenance; no combat or threat assertions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / 'scripts/build_formation_ranges.py'
PATCH = '16.20.1'


class FormationRangeTests(unittest.TestCase):
    def builder(self):
        self.assertTrue(BUILDER.is_file(), 'offline formation range builder is missing')
        spec = importlib.util.spec_from_file_location('build_formation_ranges', BUILDER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def node(self, code):
        result = subprocess.run(['node', '-e', code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_every_champion_has_original_source_value_hash_and_locator(self):
        data = self.builder().build_data()
        catalog = json.loads((ROOT / 'web_r4/loading-data.json').read_text())
        self.assertEqual(data['format'], 'lol-coach-formation-ranges-v1')
        self.assertEqual(data['source_patch'], PATCH)
        self.assertEqual(set(data['champions']), set(catalog['champions']))
        for champion, entry in data['champions'].items():
            with self.subTest(champion=champion):
                local = f'data/official_catalog/versions/{PATCH}/{champion}-{PATCH}.ko_KR.json'
                raw = (ROOT / local).read_bytes()
                source = entry['source']
                self.assertEqual(source['local_source'], local)
                self.assertEqual(source['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(source['patch'], PATCH)
                self.assertEqual(source['url'], f'https://ddragon.leagueoflegends.com/cdn/{PATCH}/data/ko_KR/champion/{champion}.json')
                self.assertEqual(source['locator'], f'data.{champion}.stats.attackrange')
                self.assertEqual(entry['base_attack_range'], json.loads(raw)['data'][champion]['stats']['attackrange'])
                self.assertIsNone(entry['missing_reason'])
        self.assertEqual(data['champions']['Caitlyn']['base_attack_range'], 650)
        self.assertEqual(data['champions']['Kaisa']['base_attack_range'], 525)

    def test_missing_stat_and_missing_source_stay_null_with_reason(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'web_r4').mkdir()
            (root / 'web_r4/loading-data.json').write_text(json.dumps({'source_patch': PATCH, 'champions': {'MissingStat': {}, 'MissingSource': {}, 'InvalidStat': {}}}))
            folder = root / 'data/official_catalog/versions' / PATCH
            folder.mkdir(parents=True)
            for champion, stats in [('MissingStat', {}), ('InvalidStat', {'attackrange': 0})]:
                (folder / f'{champion}-{PATCH}.ko_KR.json').write_text(json.dumps({'version': PATCH, 'data': {champion: {'id': champion, 'stats': stats}}}))
            entries = builder.build_data(root)['champions']
            for entry in entries.values():
                self.assertIsNone(entry['base_attack_range'])
                self.assertTrue(entry['missing_reason'])
            self.assertIsNotNone(entries['MissingStat']['source']['sha256'])
            self.assertIsNone(entries['MissingSource']['source']['sha256'])

    def test_curated_profile_with_missing_source_keeps_unknown(self):
        builder=self.builder()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'web_r4').mkdir();(root/'config').mkdir()
            (root/'web_r4/loading-data.json').write_text(json.dumps({'source_patch':PATCH,'champions':{'Sejuani':{}}}))
            (root/'config/formation_threat_profiles.json').write_text((ROOT/'config/formation_threat_profiles.json').read_text())
            entry=builder.build_data(root)['champions']['Sejuani'];self.assertIsNone(entry['base_attack_range']);self.assertIsNone(entry['threat']['direct']);self.assertIsNone(entry['threat']['approach']);self.assertIn('미확인',entry['threat']['scope'])

    def test_present_source_must_match_retained_hash(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'web_r4').mkdir()
            local = f'data/official_catalog/versions/{PATCH}/Caitlyn-{PATCH}.ko_KR.json'
            path = root / local
            path.parent.mkdir(parents=True)
            path.write_bytes((ROOT / local).read_bytes())
            catalog = {'source_patch': PATCH, 'champions': {'Caitlyn': {'facts': [{'local_source': local, 'sha256': '0' * 64}]}}}
            (root / 'web_r4/loading-data.json').write_text(json.dumps(catalog))
            with self.assertRaisesRegex(ValueError, 'SOURCE_HASH_MISMATCH'):
                builder.build_data(root)

    def test_generated_bytes_are_deterministic_and_umd_matches_python(self):
        builder = self.builder()
        generated = ROOT / 'web_r4/formation-ranges.js'
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT / f'data/official_catalog/versions/{PATCH}').glob('*.json')}
        self.assertEqual(builder.build(), builder.build())
        self.assertEqual(generated.read_text(), builder.build())
        result = subprocess.run(['python', str(BUILDER), '--check'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        values = self.node("const fs=require('node:fs'),vm=require('node:vm'),data=require('./web_r4/formation-ranges.js'),context={};vm.runInNewContext(fs.readFileSync('./web_r4/formation-ranges.js','utf8'),context);console.log(JSON.stringify([data,context.FormationRanges]));")
        self.assertEqual(values, [builder.build_data(), builder.build_data()])
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before})

    def test_korean_limits_state_reference_units_and_unsupported_factors(self):
        text = ' '.join(self.builder().build_data()['limits'])
        for term in ('기본 공격 사거리', '게임 단위', '위협', '스킬', '버프', '아이템', '충돌', '지형', '대상', '가상'):
            self.assertIn(term, text)


if __name__ == '__main__':
    unittest.main()

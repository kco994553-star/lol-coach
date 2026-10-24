"""Read-only authored direction registry, binding audit and snapshot comparison.

No collection, tactical authoring, approval, or rollback writes occur here.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_loading_catalog import located, sha256

ROLES = ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT')
PROFILE = 'web_r4/loading-direction-profiles.js'
CATALOG = 'web_r4/loading-data.json'
CORE = (PROFILE, CATALOG, 'web_r4/loading-planboard.js', 'web_r4/loading-formation.js',
        'scripts/build_loading_catalog.py', 'scripts/gameplan_registry.py')


def repo_path(root, value):
    """Resolve only repository-relative paths, including symlink containment."""
    if not isinstance(value, str) or not value or ':' in value or '\\' in value:
        raise ValueError('INVALID_REPOSITORY_PATH')
    path = Path(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('INVALID_REPOSITORY_PATH')
    resolved = (Path(root).resolve() / path).resolve()
    if not resolved.is_relative_to(Path(root).resolve()):
        raise ValueError('INVALID_REPOSITORY_PATH')
    return resolved


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def load_runtime(root=ROOT):
    """Use production validation/resolution, rather than a second profile parser."""
    for path in CORE:
        repo_path(root, path)
    code = """
const d=require('./web_r4/loading-direction-profiles.js');
const c=require('./web_r4/loading-data.json');
const p=require('./web_r4/loading-planboard.js');
const r=Object.fromEntries(Object.entries(d.champions).map(([id,e])=>[id,p.resolveDirectionProfiles(d,id,e.role,c)]));
console.log(JSON.stringify([d,c,r]));
"""
    result = subprocess.run(['node', '-e', code], cwd=root, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def seal_snapshot(snapshot):
    result = copy.deepcopy(snapshot)
    result.setdefault('manifest', {}).pop('snapshot_sha256', None)
    result['manifest']['snapshot_sha256'] = sha256(canonical(result))
    return result


def validate_snapshot(snapshot):
    if snapshot.get('schema_version') != 'gameplan-registry-v1':
        raise ValueError('INVALID_SNAPSHOT_SCHEMA')
    if snapshot.get('manifest', {}).get('snapshot_sha256') != seal_snapshot(snapshot)['manifest']['snapshot_sha256']:
        raise ValueError('SNAPSHOT_HASH_MISMATCH')


def build_registry(root=ROOT, *, catalog=None, profiles=None, resolved=None):
    root = Path(root).resolve()
    if catalog is None or profiles is None or resolved is None:
        profiles, catalog, resolved = load_runtime(root)
    files, documents = {}, {}

    def read(path):
        actual = repo_path(root, path)
        if path not in files:
            raw = actual.read_bytes()
            files[path] = {'sha256': sha256(raw), 'bytes': len(raw)}
            documents[path] = raw
        return documents[path]

    for path in CORE:
        read(path)
    champions = {}
    for champion, row in sorted(catalog['champions'].items()):
        skills = []
        for fact in row.get('facts', []):
            path = fact.get('local_source')
            issues = []
            # Unsafe references fail closed rather than being followed.
            repo_path(root, path)
            try:
                raw = read(path)
                if sha256(raw) != fact.get('sha256'):
                    issues.append('SOURCE_HASH_MISMATCH')
                if located(json.loads(raw), fact.get('locator', '')) != fact.get('raw_excerpt'):
                    issues.append('SOURCE_EXCERPT_MISMATCH')
            except FileNotFoundError:
                issues.append('SOURCE_MISSING')
            except (KeyError, IndexError, TypeError, ValueError):
                issues.append('SOURCE_LOCATOR_INVALID')
            if fact.get('patch') != catalog['source_patch']:
                issues.append('SOURCE_PATCH_MISMATCH')
            skills.append({'id': fact['id'], 'slot': fact['slot'], 'name': fact['name'],
                           'source_path': path, 'locator': fact.get('locator'),
                           'url': fact.get('url'), 'patch': fact.get('patch'),
                           'binding': {'status': 'BOUND' if not issues else 'SOURCE_REVIEW_REQUIRED', 'issues': issues}})
        profile = profiles['champions'].get(champion)
        by_slot = {s['slot']: s for s in skills}
        bound = bool(profile) and all(by_slot.get(k, {}).get('binding', {}).get('status') == 'BOUND' for k in profile['required_slots'])
        scopes = {}
        for role in ROLES:
            status = ('MISSING_PROFILE' if not profile else 'UNSUPPORTED_ROLE' if role != profile['role'] else
                      'SOURCE_REVIEW_REQUIRED' if not bound or not resolved.get(champion) else 'AUTHORED_CONDITIONAL')
            scopes[role] = {'status': status, 'phases': {p: status for p in ('lane', 'operations', 'fight')},
                            'matchup_coverage': 'NOT_INDEXED', 'composition_coverage': 'NOT_INDEXED'}
        rules = []
        if profile:
            for phase, content in sorted(profile['phases'].items()):
                rules.append({'id': f"{profile['role'].lower()}-direction:{champion}:{phase}", 'phase': phase,
                              'role': profile['role'], 'version': profiles['version'],
                              'source_path': PROFILE, 'locator': f'champions.{champion}.phases.{phase}',
                              'skill_ids': [by_slot[k]['id'] for k in content['keys'] if k in by_slot],
                              'gate_skill_ids': [by_slot[k]['id'] for k in profile['required_slots'] if k in by_slot],
                              'output_path': 'delivery.phases.' + phase,
                              'runtime_gate': 'resolveDirectionProfiles + directionRuleTrace + attachDirectionHierarchy',
                              'provenance': copy.deepcopy(profile.get('provenance')), 'content': copy.deepcopy(content)})
        champions[champion] = {'scopes': scopes, 'skills': skills, 'rules': rules}
    return seal_snapshot({'schema_version': 'gameplan-registry-v1', 'coverage': 'AUTHORED_DIRECTION_BASELINES_ONLY',
                          'observation': False, 'review_state': profiles['review_state'],
                          'source_patch': catalog['source_patch'], 'profile_patch': profiles['source_patch'],
                          'missing_coverage': ['matchup rules', 'composition rules', 'state reconciliation rules',
                                               'non-profile role principles', 'runtime output overrides'],
                          'champions': champions, 'manifest': {'profile_version': profiles['version'],
                                                              'files': dict(sorted(files.items()))}})


def patch_impact(registry, changed_ids):
    validate_snapshot(registry)
    changed = set(changed_ids)
    found, affected = set(), []
    for champion, row in registry['champions'].items():
        for rule in row['rules']:
            dependencies = {champion, rule['id'], rule['source_path'], CATALOG,
                            'web_r4/loading-planboard.js', *rule['skill_ids'], *rule['gate_skill_ids']}
            dependencies.update(s['source_path'] for s in row['skills'] if s['id'] in rule['gate_skill_ids'])
            hits = sorted(changed & dependencies)
            if hits:
                found.update(hits)
                affected.append({'champion': champion, 'rule_id': rule['id'], 'output_path': rule['output_path'], 'changed_dependencies': hits})
    return {'coverage': registry['coverage'], 'complete': False, 'affected': affected,
            'untracked': sorted(changed - found), 'missing_coverage': registry['missing_coverage']}


def compare_snapshots(before, after):
    for snapshot in (before, after):
        validate_snapshot(snapshot)
    a, b = before['manifest']['files'], after['manifest']['files']
    def rules(snapshot):
        return {rule['id']: rule for row in snapshot['champions'].values() for rule in row['rules']}
    old, new = rules(before), rules(after)
    return {'before': before['manifest']['snapshot_sha256'], 'after': after['manifest']['snapshot_sha256'],
            'changed_files': sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k)),
            'changed_rules': sorted(k for k in old.keys() | new.keys() if old.get(k) != new.get(k)),
            'changed_scopes': sorted(k for k in before['champions'].keys() | after['champions'].keys()
                                    if before['champions'].get(k, {}).get('scopes') != after['champions'].get(k, {}).get('scopes')),
            'rollback': 'Restore the matching authored profile and retained source/catalog/code files from one reviewed git revision; rebuild catalog, rerun registry and focused tests. This command does not restore files.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('tree', 'impact', 'compare'))
    parser.add_argument('values', nargs='*', help='changed IDs/paths, or two repository-relative snapshots')
    args = parser.parse_args(argv)
    if args.command == 'compare':
        if len(args.values) != 2:
            parser.error('compare requires two snapshot paths')
        result = compare_snapshots(*(json.loads(repo_path(ROOT, p).read_text()) for p in args.values))
    else:
        registry = build_registry()
        result = patch_impact(registry, args.values) if args.command == 'impact' else registry
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

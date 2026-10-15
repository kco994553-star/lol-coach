"""Bind Queue v2.1 successors while rerunning unchanged predecessor assertions.

``--prepare`` prints a candidate amendment; it never seals or writes authority.
The normal entrypoint requires a separately finalized exact-byte amendment.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import verify_mvp_reference as prior

AMENDMENT='contracts/amendments/2026-10-15-queue-v21.json'
PARENT_AMENDMENT='contracts/amendments/2026-10-14-reference-first.json'
PARENT_DIRECTORY='evidence/queue/v21/parent'
PARENT_RECEIPT=PARENT_DIRECTORY+'/git-head.json'
PARENT_GIT_HEAD='7e4c92c894ff48ce15d4bd8163b3cef95b0c4550'
CONTRACT='contracts/queue-v21.md'
HISTORICAL_VERIFIERS={'scripts/verify_mvp.py','scripts/verify_mvp_experts.py',
                      'scripts/verify_mvp_practical.py','scripts/verify_mvp_reference.py'}
FROZEN_LOGIC={'FREEZE_MANIFEST.json','coach_v1/knowledge.py','coach_v1/practical_review.py',
              'coach_v1/pregame_contract.py','coach_v1/pregame_evaluator.py','coach_v1/pregame_store.py',
              'knowledge_candidates/executable-v1.json','knowledge_candidates/executable-expanded-v1.json',
              'knowledge_candidates/initiative-v2.json','knowledge_candidates/initiative-expansion-v2.json',
              'knowledge_candidates/practical-review-v1.json'}
CURRENT_PATHS={
    'coach_v1/pregame_server.py','coach_v1/auto_review.py','coach_v1/pc_coach.py','coach_v1/lcu_draft.py',
    'coach_v1/pc_runtime.py','coach_v1/official_catalog.py',
    'web_r4/pc.html','web_r4/pc.js','web_r4/pc.css','Start-LoL-Coach.cmd','Start-LoL-Coach.ps1',
    'scripts/launch_pc.py','scripts/update_official_catalog.py','scripts/browser_pc_v21.py',
    'scripts/verify_mvp_v21.py','scripts/verify_pregame.py',
    'tests_pregame/test_auto_review_v21.py','tests_pregame/test_pc_coach.py','tests_pregame/test_lcu_draft.py',
    'tests_pregame/test_pc_launcher.py','tests_pregame/test_official_catalog.py',
    'tests_pregame/test_pc_runtime.py','scripts/report_queue_v21.py',
    'tests_pregame/test_reference_binding.py','tests_pregame/test_v21_binding.py',
    '.github/workflows/private-mvp-ci.yml','.github/workflows/pregame-ci.yml',
    'docs/queue/V21_LCU.md','docs/queue/V21_OFFICIAL_CATALOG.md','docs/queue/V21_PC_START.md',
    'docs/queue/V21_OPERATION.md','.gitignore','config/riot_collection_policy.json',
    'evidence/queue/v21/packet.json','evidence/queue/v21/evidence-review.json',
    'evidence/queue/v21/counter-review.json','evidence/queue/v21/author-revision.json',
    'evidence/queue/v21/review-manifest.json'}
_REFERENCE_BINDING=prior.reference_binding


def sha(path):
    value=Path(path)
    if value.is_absolute() or '..' in value.parts or (ROOT/value).is_symlink():
        raise ValueError('unsafe binding path')
    return hashlib.sha256((ROOT/value).read_bytes()).hexdigest()


def _read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def _parents():
    reference=_read(PARENT_AMENDMENT)
    practical=_read(reference['parent_amendment'])
    return reference,practical


def _preserved_paths():
    reference,practical=_parents()
    return (set(reference['current_sha256'])|set(practical['current_sha256'])|
            set(reference['official_source_sha256'])|HISTORICAL_VERIFIERS|FROZEN_LOGIC)-CURRENT_PATHS


def _historical_paths():
    reference,practical=_parents()
    return (set(reference['current_sha256'])|set(reference['official_source_sha256'])|
            set(practical['current_sha256'])|{PARENT_AMENDMENT,reference['parent_amendment'],reference['contract'],'FREEZE_MANIFEST.json'}|
            {reference['parent_directory']+'/'+p for p in practical['current_sha256']})


def _catalog_sources(version):
    if not isinstance(version,str) or not re.fullmatch(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',version):
        raise ValueError('catalog version')
    directory='data/official_catalog/versions/'+version
    manifest_path=directory+'/manifest.json'
    manifest=_read(manifest_path)
    if manifest['source_patch']!=version:raise ValueError('catalog manifest version')
    rows=[manifest['discovery'],manifest['roster'],*manifest['sources']]
    expected={directory+'/'+row['file']:row['sha256'] for row in rows}
    if len(expected)!=len(rows) or not 170<=len(manifest['sources'])<=300:
        raise ValueError('catalog source coverage')
    expected[manifest_path]=sha(manifest_path)
    return expected


def required_paths():
    """Files needed by the isolated binding regression fixture."""
    receipt=_read(PARENT_RECEIPT)
    current=_read('data/official_catalog/current.json')
    return (CURRENT_PATHS|_preserved_paths()|_historical_paths()|
            {PARENT_RECEIPT,CONTRACT,'data/official_catalog/current.json'}|
            {PARENT_DIRECTORY+'/'+p for p in receipt['sha256']}|
            set(_catalog_sources(current['source_patch'])))


def prepare_binding():
    """Return an unpersisted candidate. Main seals only after sources stop changing."""
    receipt=_read(PARENT_RECEIPT)
    catalog=_read('data/official_catalog/current.json')
    reference,_=_parents()
    return dict(schema_version='queue-v21.source-amendment.v1',authority='USER_QUEUE_V2.1_2026-10-15',
                parent_amendment=PARENT_AMENDMENT,parent_amendment_sha256=sha(PARENT_AMENDMENT),
                parent_directory=PARENT_DIRECTORY,parent_receipt_sha256=sha(PARENT_RECEIPT),
                parent_git_head=PARENT_GIT_HEAD,parent_freeze_sha256=reference['parent_freeze_sha256'],
                contract=CONTRACT,contract_sha256=sha(CONTRACT),
                current_sha256={p:sha(p) for p in sorted(CURRENT_PATHS)},
                preserved_sha256={p:sha(p) for p in sorted(_preserved_paths())},
                parent_archive_sha256=dict(receipt['sha256']),
                official_catalog_source_patch=catalog['source_patch'],
                official_catalog_source_sha256=_catalog_sources(catalog['source_patch']),
                automatic_user_approval=False,auto_verified_to_user_reviewed=False,
                user_decisions_created=0,existing_user_decisions_mutated=False,
                existing_sql_schema_change=False,additive_local_auto_review_store=True,
                engine_activation=False,real_match_coaching_accuracy=None)


def historical_reference_binding():
    """Execute the unchanged original checks against exact reference ancestors."""
    try:
        reference,_=_parents()
        with tempfile.TemporaryDirectory(prefix='v21-reference-parent-') as td:
            root=Path(td)
            for p in _historical_paths():
                source=ROOT/PARENT_DIRECTORY/p if p in reference['current_sha256'] else ROOT/p
                if p in reference['current_sha256'] and hashlib.sha256(source.read_bytes()).hexdigest()!=reference['current_sha256'][p]:
                    raise ValueError('reference ancestor integrity')
                destination=root/p;destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,destination)
            previous=prior.ROOT
            prior.ROOT=root
            try:return _REFERENCE_BINDING()
            finally:prior.ROOT=previous
    except (OSError,ValueError,KeyError,TypeError):
        return dict(status='FAIL',checks={'historical_reference_bytes':False})


def v21_binding():
    try:
        binding=_read(AMENDMENT)
        reference,_=_parents()
        receipt=_read(PARENT_RECEIPT)
        archive=binding['parent_archive_sha256']
        preserved=binding['preserved_sha256']
        expected_archives=set(reference['current_sha256'])|HISTORICAL_VERIFIERS|FROZEN_LOGIC|{
            'tests_pregame/test_reference_binding.py','scripts/verify_pregame.py',
            '.github/workflows/private-mvp-ci.yml','.github/workflows/pregame-ci.yml',
            '.gitignore','config/riot_collection_policy.json'}
        catalog=_catalog_sources(binding['official_catalog_source_patch'])
        checks=dict(
            explicit_user_authority=binding['schema_version']=='queue-v21.source-amendment.v1' and binding['authority']=='USER_QUEUE_V2.1_2026-10-15',
            parent_contract_unchanged=binding['parent_amendment']==PARENT_AMENDMENT and sha(PARENT_AMENDMENT)==binding['parent_amendment_sha256'],
            exact_parent_directory=binding['parent_directory']==PARENT_DIRECTORY,
            exact_parent_commit=binding['parent_git_head']==receipt['source_git_head']==PARENT_GIT_HEAD,
            exact_current_paths=set(binding['current_sha256'])==CURRENT_PATHS,
            current_bytes=all(sha(p)==h for p,h in binding['current_sha256'].items()),
            parent_receipt_bound=sha(PARENT_RECEIPT)==binding['parent_receipt_sha256'],
            exact_parent_archive_paths=set(archive)==set(receipt['sha256'])==expected_archives,
            archived_parent_bytes=archive==receipt['sha256'] and all(sha(PARENT_DIRECTORY+'/'+p)==h for p,h in archive.items()),
            reference_ancestors_unchanged=all(archive[p]==h for p,h in reference['current_sha256'].items()),
            exact_preserved_paths=set(preserved)==_preserved_paths(),
            preserved_bytes=all(sha(p)==h for p,h in preserved.items()),
            frozen_unchanged=sha('FREEZE_MANIFEST.json')==binding['parent_freeze_sha256']==reference['parent_freeze_sha256'],
            historical_verifiers_unchanged=all(sha(p)==archive[p] for p in HISTORICAL_VERIFIERS),
            frozen_logic_unchanged=all(sha(p)==archive[p] for p in FROZEN_LOGIC),
            contract_bound=binding['contract']==CONTRACT and sha(CONTRACT)==binding['contract_sha256'],
            official_catalog_exact_sources=binding['official_catalog_source_sha256']==catalog,
            official_catalog_original_bytes=all(sha(p)==h for p,h in catalog.items()),
            auto_never_promotes_user=binding['automatic_user_approval'] is False and binding['auto_verified_to_user_reviewed'] is False
                and type(binding['user_decisions_created']) is int and binding['user_decisions_created']==0
                and binding['existing_user_decisions_mutated'] is False,
            existing_sql_and_engine_preserved=binding['existing_sql_schema_change'] is False and binding['additive_local_auto_review_store'] is True and binding['engine_activation'] is False,
            no_accuracy_claim=binding['real_match_coaching_accuracy'] is None,
            original_reference_assertions=historical_reference_binding()['status']=='PASS')
        return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks)
    except (OSError,ValueError,KeyError,TypeError):
        return dict(status='FAIL',checks={'binding_readable':False})


def main():
    if sys.argv[1:]==['--prepare']:
        print(json.dumps(dict(state='UNSEALED_CANDIDATE',binding=prepare_binding()),ensure_ascii=False,indent=2))
        return 0
    base=prior.reference_binding
    def chained_reference():
        historical=historical_reference_binding();successor=v21_binding()
        checks=dict(historical['checks'],queue_v21_successor=successor['status']=='PASS')
        return dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,
                    historical_result=historical,queue_v21_source_binding=successor)
    prior.reference_binding=chained_reference
    try:return prior.main()
    finally:prior.reference_binding=base


if __name__=='__main__':raise SystemExit(main())

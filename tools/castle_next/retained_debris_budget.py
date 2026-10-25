"""Count retained native landmark stamp debris without assuming lifecycle visibility.

Reads the Release 050 private-binding receipt, Castle lifecycle source contract,
existing decoded stock-static model manifests and two current landmark handoffs.
It does not cook, edit assets, or mutate the private binding evidence.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import CFG, EXTERNAL, OUT, ROOT, guarded, read, sha, write

sys.path.insert(0, str(ROOT / 'tools/release_010'))
import integration_native as native_read  # noqa: E402
NativeTree = native_read.NativeTree
sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import relic_chunky as rc  # noqa: E402

PRIVATE = EXTERNAL / 'output/release_050/integration/dryrun-real-identities/private-bindings.json'
FINAL_PRIVATE = EXTERNAL / 'output/release_050/integration/private-bindings.json'
if FINAL_PRIVATE.is_file():PRIVATE=FINAL_PRIVATE
LIFECYCLE = OUT / 'lifecycle/source-contract.json'
DECODE_ROOT = OUT / 'inventory/model-decode'
HANDOFF_ROOT = OUT / 'landmarks'
TARGET = OUT / 'landmarks/retained-debris-budget.json'
REFLECT = ROOT / 'output/release_010/integration/schema'

MODELS = {
    'art/civilizations/common/structures/debris/debris_med_a_01/debris_med_a_01',
    'art/civilizations/common/structures/debris/debris_med_a_stone_01/debris_med_a_stone_01',
    'art/civilizations/common/structures/debris/debris_med_a_wood_01/debris_med_a_wood_01',
    'art/civilizations/common/structures/debris/debris_med_b_01/debris_med_b_01',
}
EXPECTED_INSTANCES = {'imperial_citadel': 29, 'resistance_hq': 15}


def _json_hash(path: Path) -> str:
    return sha(path)


def _manifest_by_model() -> dict[str, tuple[Path, dict]]:
    result = {}
    for path in DECODE_ROOT.glob('**/decoded-static.json'):
        doc = read(path)
        logical = doc.get('request', {}).get('logical_path', '').replace('\\', '/').removesuffix('.rgm')
        if logical in MODELS:
            if logical in result:
                raise RuntimeError(f'Duplicate decoded stock-static manifest for {logical}')
            result[logical] = (path, doc)
    if set(result) != MODELS:
        raise FileNotFoundError(f'Missing retained debris model decode manifests: {sorted(MODELS - set(result))}')
    return result


def _stamp_semantics(path: Path, *, expected_count: int) -> dict:
    """Inspect reflected stamp visual fields; do not infer runtime visibility."""
    native_read.WORK = REFLECT
    tree = NativeTree(path)
    root = next(obj for obj in tree.objects.values()
                if obj['type'] == 'StampBlueprint' and not obj['owner'])
    rows = []
    for obj in tree.objects.values():
        if obj['type'] != 'VisualStampBlueprint':
            continue
        field = obj['fields'].get('m_blueprint')
        if field is None:
            continue
        model = tree.field(obj, field)['text'].replace('\\', '/')
        if '/structures/debris/' not in model:
            continue
        selectable = tree.field(obj, obj['fields']['m_isSelectable']) if 'm_isSelectable' in obj['fields'] else None
        rows.append({'id': str(obj['id']), 'model': model,
                     'is_selectable': selectable,
                     'visual_fields': sorted(obj['fields']),
                     'transform_raw': tree.field(obj, obj['fields']['m_transform'])['raw']})
    if len(rows) != expected_count:
        raise RuntimeError(f'{path}: expected {expected_count} debris visuals, found {len(rows)}')
    visibility_names = ('visible', 'visibility', 'state', 'lifecycle', 'life_cycle', 'condition', 'stage', 'enable')
    conditional_fields = sorted({name for row in rows for name in row['visual_fields']
                                 if any(token in name.lower() for token in visibility_names)})
    return {
        'sha256': sha(path),
        'stamp_root_visual_array_count': tree.field(root, root['fields']['m_blueprints'])['count'],
        'retained_debris_count': len(rows),
        'debris_visual_field_names': rows[0]['visual_fields'] if rows else [],
        'per_visual_lifecycle_or_visibility_fields': conditional_fields,
        'debris_visuals': rows,
    }


def _decode_model(model: str, manifests: dict[str, tuple[Path, dict]], owners: dict) -> dict:
    manifest_path, doc = manifests[model]
    if doc.get('status') != 'decoded' or doc.get('completeness', {}).get('status') != 'complete':
        raise RuntimeError(f'Incomplete native decode for {model}: {manifest_path}')
    groups = doc.get('geometry', {}).get('groups', [])
    triangles = sum(int(group.get('triangle_count', -1)) for group in groups)
    planned = int(doc['animated_asset_import_plan']['layers']['geometry']['triangle_count'])
    if triangles != planned or not groups or any(int(g.get('triangle_count', -1)) < 0 for g in groups):
        raise RuntimeError(f'Geometry triangle count mismatch for {model}: groups={triangles}, plan={planned}')
    if len(groups) != 1:
        raise RuntimeError(f'Expected single native render group for static debris model {model}, got {len(groups)}')
    for key in ('model', 'geometry', 'material'):
        resource = doc['resources'][key]
        native_path = Path(resource['cache_path'])
        if not native_path.is_file() or sha(native_path) != resource['sha256']:
            raise RuntimeError(f'Native closure source hash mismatch: {native_path}')
    model_tree = rc.load(Path(doc['resources']['model']['cache_path']))
    root_chunks = [chunk.tag.decode('ascii', 'replace') for chunk in model_tree.roots]
    child_chunks = [chunk.tag.decode('ascii', 'replace') for root in model_tree.roots
                    for chunk in root.children]
    if root_chunks != ['MODL']:
        raise RuntimeError(f'Unexpected native RGM root chunks for {model}: {root_chunks}')
    owner = owners.get(model)
    if not owner:
        raise RuntimeError(f'No native RGO owner hash/action evidence for {model}')
    texture_rows = []
    for texture in doc.get('textures', []):
        if isinstance(texture, dict):
            texture_rows.append({k: texture.get(k) for k in ('logical_path', 'sha256', 'status', 'cache_path') if k in texture})
    return {
        'model': model,
        'triangle_count': triangles,
        'geometry_group_count': len(groups),
        'vertex_count': sum(int(group.get('vertex_count', 0)) for group in groups),
        'geometry_semantics': 'One decoded native static render group; RGM is one MODL root and contains no separate LOD model reference. Count is the complete single render group, with no inferred lower-detail or alternate state geometry.',
        'decode_manifest': str(manifest_path),
        'decode_manifest_sha256': sha(manifest_path),
        'native_closure': {
            key: {'logical_path': doc['resources'][key]['logical_path'],
                  'path': doc['resources'][key]['cache_path'],
                  'sha256': doc['resources'][key]['sha256'],
                  'archive_id': doc['resources'][key].get('archive_id')}
            for key in ('model', 'geometry', 'material')
        },
        'native_rgm_chunk_tags': {'root': root_chunks, 'model_children': child_chunks},
        'native_rgo': owner,
        'texture_dependency_count': len(doc.get('material', {}).get('texture_dependencies', [])),
        'decoded_texture_count': doc.get('completeness', {}).get('decoded_textures'),
        'completeness': doc.get('completeness'),
    }


def build() -> dict:
    guarded()
    if not (REFLECT / 'reflect.db').is_file():
        raise FileNotFoundError(f'Native reflection schema required for stamp readback: {REFLECT}')
    private = read(PRIVATE)
    lifecycle = read(LIFECYCLE)
    if private.get('status') != 'passed' or lifecycle.get('status') != 'passed_static_native_graph':
        raise RuntimeError('Required Release 050 private bindings or lifecycle source contract are not passed')
    manifests = _manifest_by_model()
    actors = {row['key']: row for row in lifecycle['actors']}
    result_rows = []
    input_hashes = {str(PRIVATE): _json_hash(PRIVATE), str(LIFECYCLE): _json_hash(LIFECYCLE)}
    for key, expected in EXPECTED_INSTANCES.items():
        binding = private['bindings'][key]
        proofs = binding.get('private_stamp_proofs', [])
        default_proofs = [row for row in proofs if row['output'].replace('\\', '/').endswith(f'{key}_base_default.bin')]
        campaign_proofs = [row for row in proofs if row['output'].replace('\\', '/').endswith(f'{key}_base_campaign.bin')]
        if len(default_proofs) != 1:
            raise RuntimeError(f'{key}: expected exactly one private default stamp proof, found {len(default_proofs)}')
        branch_proofs = [('default', default_proofs[0])]
        if key == 'imperial_citadel':
            if len(campaign_proofs) != 1:
                raise RuntimeError('Citadel campaign branch proof is missing or duplicated')
            branch_proofs.append(('campaign_alternative_not_summed', campaign_proofs[0]))
        elif campaign_proofs:
            raise RuntimeError(f'{key}: unexpected campaign-specific stamp copy')

        row_actor = actors[key]
        owner_by_model = row_actor.get('owners', {})
        counts = collections.Counter()
        default_debris: list[dict] = []
        branch_receipts = []
        for branch, proof in branch_proofs:
            source_stamp, private_stamp = Path(proof['source']), Path(proof['output'])
            if sha(source_stamp) != proof['source_sha256'] or sha(private_stamp) != proof['sha256']:
                raise RuntimeError(f'{key}/{branch}: stamp byte/hash evidence mismatch')
            after_debris = [v for v in proof['after'] if '/structures/debris/' in v['model']]
            before_debris = [v for v in proof['before'] if '/structures/debris/' in v['model']]
            retained_ids = set(map(str, proof.get('retained_ruin_debris_visual_ids', [])))
            after_ids = {str(v['id']) for v in after_debris}
            if len(after_debris) != expected or retained_ids != after_ids:
                raise RuntimeError(f'{key}/{branch}: retained debris ID/count mismatch')
            if collections.Counter((v['model'], tuple(v['transform'])) for v in before_debris) != \
                    collections.Counter((v['model'], tuple(v['transform'])) for v in after_debris):
                raise RuntimeError(f'{key}/{branch}: native debris model/transform instances were not preserved exactly')
            for visual in after_debris:
                if visual['model'] not in MODELS:
                    raise RuntimeError(f'{key}: retained model lacks an exact decoded source closure: {visual["model"]}')
                if branch == 'default':
                    counts[visual['model']] += 1
            semantics = _stamp_semantics(private_stamp, expected_count=expected)
            input_hashes[str(source_stamp)] = proof['source_sha256']
            input_hashes[str(private_stamp)] = proof['sha256']
            receipt = {'branch': branch,
                       'source_stamp': str(source_stamp), 'source_stamp_sha256': proof['source_sha256'],
                       'private_stamp': str(private_stamp), 'private_stamp_sha256': proof['sha256'],
                       'preserved_debris_instances': len(after_debris),
                       'debris_model_distribution': dict(sorted(collections.Counter(v['model'] for v in after_debris).items())),
                       'native_stamp_semantics': semantics}
            branch_receipts.append(receipt)
            if branch == 'default':
                default_debris = after_debris

        # The actor's RGO source proves these static models have no lifecycle
        # actions, while the stamp record exposes no state predicate. This is
        # deliberately not treated as proof that the engine hides the stamp.
        owners = {}
        for model in sorted(counts):
            owner = owner_by_model.get(model)
            if not owner:
                raise RuntimeError(f'{key}: lifecycle source contract lacks RGO evidence for {model}')
            owners[model] = owner
        native_geometry = {}
        for model, quantity in sorted(counts.items()):
            details = _decode_model(model, manifests, owners)
            details['retained_instance_count'] = quantity
            details['aggregate_triangles_if_drawn'] = quantity * details['triangle_count']
            native_geometry[model] = details
        native_total = sum(v['aggregate_triangles_if_drawn'] for v in native_geometry.values())
        if sum(v['retained_instance_count'] for v in native_geometry.values()) != expected:
            raise RuntimeError(f'{key}: model closure instance count does not match retained stamp instances')

        handoff_path = HANDOFF_ROOT / key / 'handoff.json'
        handoff = read(handoff_path)
        custom_healthy = int(handoff['healthy_triangles'])
        custom_ruins = int(handoff['ruin_triangles'])
        input_hashes[str(handoff_path)] = sha(handoff_path)
        result_rows.append({
            'key': key,
            'native_instance_count': expected,
            'private_stamp_branches': branch_receipts,
            'native_model_closure': native_geometry,
            'native_debris_triangles_if_drawn_once_per_instance': native_total,
            'visibility_qualification': {
                'status': 'not_proven_false_for_healthy; native state visibility unresolved',
                'evidence': [
                    'The private/default attachment-list branch references the primary stamp; Citadel also has a separate campaign alternative that is not summed.',
                    'Decoded VisualStampBlueprint debris entries have no lifecycle/visibility/state/construction-progress fields.',
                    'The retained debris RGO owners expose no bhv_set_lifecycle_ruins, bhv_collapse_ruins, or bhv_repair_to_healthy actions.',
                    'Static source evidence does not establish whether the engine suppresses default stamp props in healthy or ruined states.'
                ],
                'consequence': 'Keep native debris separate from custom healthy/ruin counts; present full-compound intervals rather than claiming the debris is hidden in healthy state.'
            },
            'custom_source_counts': {
                'handoff': str(handoff_path),
                'handoff_sha256': sha(handoff_path),
                'source_blend': handoff['source_blend'],
                'source_blend_sha256': handoff['source_blend_sha256'],
                'healthy_triangles': custom_healthy,
                'ruin_triangles': custom_ruins,
                'custom_ruin_parts': handoff.get('ruin_parts', []),
            },
            'complete_compound_bounds': {
                'healthy_triangles': {
                    'lower_if_native_stamp_hidden': custom_healthy,
                    'upper_if_all_retained_native_debris_drawn': custom_healthy + native_total,
                    'exact_count': None,
                },
                'ruins_triangles': {
                    'lower_if_native_stamp_hidden': custom_ruins,
                    'upper_if_all_retained_native_debris_drawn': custom_ruins + native_total,
                    'exact_count': None,
                },
                'mutually_exclusive_branch_policy': 'Only the one default stamp contributes to the default target; Citadel campaign stamp proof is reported as an alternative and never added to the default compound.',
            },
        })

    report = {
        'schema': 'community-civilization-pack/castle-retained-native-debris-budget/v1',
        'status': 'native_debris_geometry_closed_visibility_bounded',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'sources': {
            'release050_private_bindings': str(PRIVATE),
            'lifecycle_source_contract': str(LIFECYCLE),
            'stock_decode_root': str(DECODE_ROOT),
            'landmark_handoffs': str(HANDOFF_ROOT),
            'read_only_reflection_schema': str(REFLECT),
        },
        'input_sha256': dict(sorted(input_hashes.items())),
        'methods': {
            'stamp_instances': 'Native VisualStampBlueprint records from the Release 050 private-binding proof; preserve each object ID, model string, and transform. Exact before/after model+transform multisets are required.',
            'draw_geometry': 'Existing Garrison decoded-static native stock manifests; triangle_count from the single native decoded render group and cross-checked against animated_asset_import_plan geometry total.',
            'render_lod_semantics': 'Each debris RGM decodes to one render group, one MODL root, no alternate LOD model reference in the source graph. Count is that complete mesh; no separate LOD0/LOD1 contribution is invented.',
            'custom_counts': 'Current Castle landmark handoff counts remain separate from retained stock stamp debris.',
            'visibility': 'No state visibility selector was found in debris VisualStampBlueprints or their static RGO action sets. Healthy/ruins full-compound totals are bounded by including/excluding all retained native debris, not guessed.',
            'branching': 'Default and campaign are mutually exclusive actor/attachment branches. The campaign Citadel stamp is evidence only; its instances are never added to default totals.',
        },
        'landmarks': result_rows,
        'limits': [
            'No in-game render/state test was run; therefore healthy visibility false cannot be claimed from the available static native files.',
            'The full-compound healthy and ruins totals are intervals, not exact counts, until native stamp lifecycle visibility is observed or proven by a state contract.',
            'Native stamp object placement is counted as separate instances even when model paths repeat.',
        ],
    }
    # Make the evidence fingerprint deterministic despite the audit timestamp.
    stable = dict(report)
    stable.pop('generated_utc')
    report['evidence_sha256'] = __import__('hashlib').sha256(
        json.dumps(stable, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true', help='Recompute and verify the saved receipt without writing it')
    args = parser.parse_args()
    report = build()
    if args.verify_only:
        saved = read(TARGET)
        if saved.get('evidence_sha256') != report['evidence_sha256']:
            raise SystemExit('retained debris budget evidence hash differs from current native sources')
        print(json.dumps({'status': 'verified', 'receipt': str(TARGET),
                          'evidence_sha256': report['evidence_sha256']}, indent=2))
    else:
        write(TARGET, report)
        print(json.dumps({'status': report['status'], 'receipt': str(TARGET),
                          'evidence_sha256': report['evidence_sha256'],
                          'landmarks': [{
                              'key': row['key'],
                              'native_instances': row['native_instance_count'],
                              'native_debris_triangles_if_drawn': row['native_debris_triangles_if_drawn_once_per_instance'],
                              'custom_healthy': row['custom_source_counts']['healthy_triangles'],
                              'custom_ruins': row['custom_source_counts']['ruin_triangles'],
                              'healthy_bounds': row['complete_compound_bounds']['healthy_triangles'],
                              'ruin_bounds': row['complete_compound_bounds']['ruins_triangles'],
                          } for row in report['landmarks']]}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

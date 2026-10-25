"""Hash-pinned Chinese villager I vs supported English villager I rig probe.

Read-only comparison of Garrison decoded-stock-static manifests and a
Garrison-core unit-prototype manifest. No scene, source asset, cook, or game
resource is modified. The output belongs to output/release_060/inventory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from common import CFG, OUT, STAGING, guard, owned, sha, write

PINNED_MANIFESTS = {
    'chinese_male_villager_i': {
        'path': 'pilots/male_villager1/decoded/e5ce7670942848a6269a/decoded-static.json',
        'sha256': 'e7c79f39b4325ca346b6504d3c5d2dac622b806ddd43a615486ce46e8814f1ba',
        'model_sha256': 'd5b541dea88960b93e9f9a164bd95c4f5cc31155797fa8794550c76db241c4ad',
        'geometry_sha256': 'cb8796307c4cb4fbf9d3643f774f81e39618823c6105b96cf999a224f5dc7a4d',
    },
    'chinese_female_villager_i': {
        'path': 'pilots/female_villager1/decoded/64a1992b4502e6ae79ba/decoded-static.json',
        'sha256': '272f2bce037274cd461792b91fa58ba1d5104466a9c05563485ec304f9ba6ce8',
        'model_sha256': '2586f30049289cb3cbe061b521f9c276de3c84173473dd3c254e2db846fd8b0a',
        'geometry_sha256': 'd650c597c61abccd5e04fc5f4d6d9bf2082cf55b710e1f42fe9a9d236b79afda',
    },
}
ENGLISH_PROTOTYPE_RELATIVE = Path('inventory/english-villager-1-prototype')
ENGLISH_FINGERPRINT = 'd6e6f7ac6055646a045e077d16bed7a3ba5ab84bc7007aee5c34ae9c2df0d871'
ENGLISH_MANIFEST_SHA256 = 'fb8ad76da0f2b1dbd7d0355d3c3273acb39c6e6e2a941b5d9a2dc5a28c7379c2'
OFFICIAL_CLOSURE_MANIFEST = OUT / 'inventory' / 'official_rgd_closure_03b8e431c91920535fa65cdae340ee206f31bbdfbb1740feddb4a0430625a977.json'
OFFICIAL_CLOSURE_SHA256 = 'b6a437f6db28ddc67d8c9732cd8f6279e3150d81a299b377c6d8e6b03b48d881'
LAND_UNITS_REPORT = OUT / 'inventory' / 'land_units.json'
LOCAL_ACTOR_ID = r'ebps\vietnam\vn_unit_villager_1_chi'
LOCAL_ACTOR_SOURCE = 'assets/attrib/instances/ebps/vietnam/vn_unit_villager_1_chi.xml'
TIER1_ATTACHMENT_ID = r'attachments\attachment_lists\civilizations\chinese\units\tier1_villager_chi'
TIER1_MEMBER = 'attrib/attachments/attachment_lists/civilizations/chinese/units/tier1_villager_chi.rgd'
EXPECTED_BODY_PATHS = {
    'male': r'art\civilizations\chinese\humans\chi_villager_male_age01\chi_villager_male_age01',
    'female': r'art\civilizations\chinese\humans\chi_villager_female_age01\chi_villager_female_age01',
}


def canonical_hash(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def exact_fields(a, b, fields):
    mismatch = []
    for index in range(max(len(a), len(b))):
        if index >= len(a) or index >= len(b):
            mismatch.append({'index': index, 'left_present': index < len(a), 'right_present': index < len(b)})
            continue
        changed = [field for field in fields if a[index].get(field) != b[index].get(field)]
        if changed:
            mismatch.append({'index': index, 'left_name': a[index].get('name'),
                             'right_name': b[index].get('name'), 'fields': changed})
    return mismatch


def max_numeric_delta(a, b):
    """Return a max absolute delta over identically shaped numeric JSON trees."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b))
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return max((max_numeric_delta(x, y) for x, y in zip(a, b)), default=0.0)
    if isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
        return max((max_numeric_delta(a[k], b[k]) for k in a), default=0.0)
    return None


def load_manifest(path: Path, expected_sha: str | None):
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_sha = sha(path)
    if expected_sha and actual_sha != expected_sha:
        raise RuntimeError(f'Input manifest hash changed: {path} expected={expected_sha} actual={actual_sha}')
    data = json.loads(path.read_text(encoding='utf-8'))
    decoded_contract = data.get('status') in {'decoded', 'hierarchy_decoded'}
    prototype_contract = data.get('schema') == 'garrison.unit-prototype/v1'
    if not decoded_contract and not prototype_contract:
        raise RuntimeError(f'Input manifest is not a successful decoded result: {path} status={data.get("status")}')
    return data, actual_sha


def input_evidence(data, manifest_path, manifest_sha, label, expected):
    skeleton = data['skeleton']
    geometry = data.get('geometry', {}).get('source', {})
    model_path = Path(skeleton['source'])
    geometry_path = Path(geometry['path']) if geometry.get('path') else None
    model_sha = sha(model_path)
    geometry_sha = sha(geometry_path) if geometry_path and geometry_path.is_file() else None
    if model_sha != skeleton['source_sha256'] or model_sha != expected['model_sha256']:
        raise RuntimeError(f'{label} model source SHA mismatch: {model_path}')
    if geometry_sha != geometry.get('sha256') or geometry_sha != expected['geometry_sha256']:
        raise RuntimeError(f'{label} geometry source SHA mismatch: {geometry_path}')
    if data.get('skeleton_error'):
        raise RuntimeError(f'{label} skeleton decode reports error: {data["skeleton_error"]}')
    if not skeleton.get('skin_palettes') or any(p.get('status') != 'bind_palette_decoded'
                                                for p in skeleton['skin_palettes']):
        raise RuntimeError(f'{label} does not have decoded skin-palette records')
    return {
        'manifest_path': manifest_path.as_posix(), 'manifest_sha256': manifest_sha,
        'model_source_path': model_path.as_posix(), 'model_source_sha256': model_sha,
        'geometry_source_path': geometry_path.as_posix() if geometry_path else None,
        'geometry_source_sha256': geometry_sha,
        'decoder_fingerprint': data.get('decoder_fingerprint', {}).get('sha256'),
        'skeleton_chunk_sha256': skeleton.get('chunk_sha256'),
        'skeleton_bone_count': skeleton.get('bone_count'),
        'palette_chunk_sha256': [p.get('chunk_sha256') for p in skeleton['skin_palettes']],
        'palette_bone_counts': [p.get('bone_count') for p in skeleton['skin_palettes']],
        'palette_lod_counts': [len(p.get('lod_palettes', [])) for p in skeleton['skin_palettes']],
        'animation_projection': {
            'status': data.get('animation_projection', {}).get('status'),
            'resolution_status': data.get('animation_projection', {}).get('resolution', {}).get('status'),
            'template_id': data.get('animation_projection', {}).get('template', {}).get('template_id'),
            'template_role': data.get('animation_projection', {}).get('template', {}).get('role'),
            'source_logical_path': data.get('animation_projection', {}).get('template', {}).get('source_logical_path'),
            'clip_inventory_status': data.get('animation_projection', {}).get('template', {}).get('clip_inventory_status'),
            'gameplay_action_mapping_status': data.get('animation_projection', {}).get('template', {}).get('gameplay_action_mapping_status'),
        },
    }


def skeleton_records(skeleton):
    return [{k: b.get(k) for k in ('index', 'name', 'parent_index', 'parent_name',
                                      'local_reference_transform', 'global_reference_transform')}
            for b in skeleton['bones']]


def palette_records(palette):
    return [{k: b.get(k) for k in ('palette_index', 'name', 'parent_index', 'parent_name',
                                      'skeleton_index', 'global_reference_transform', 'inverse_bind_transform')}
            for b in palette['bones']]


def compare_skeleton(left, right):
    a, b = skeleton_records(left), skeleton_records(right)
    mismatch = exact_fields(a, b, ('index', 'name', 'parent_index', 'parent_name',
                                   'local_reference_transform', 'global_reference_transform'))
    return {
        'left_bone_count': len(a), 'right_bone_count': len(b),
        'ordered_bone_record_sha256_left': canonical_hash(a),
        'ordered_bone_record_sha256_right': canonical_hash(b),
        'ordered_bone_records_exact_equal': not mismatch,
        'ordered_names': [x['name'] for x in a],
        'ordered_parent_names': [x['parent_name'] for x in a],
        'max_local_transform_numeric_delta_by_index': max((max_numeric_delta(x.get('local_reference_transform'),
                                                                             y.get('local_reference_transform')) or 0.0
                                                           for x, y in zip(a, b)), default=None),
        'max_global_transform_numeric_delta_by_index': max((max_numeric_delta(x.get('global_reference_transform'),
                                                                              y.get('global_reference_transform')) or 0.0
                                                            for x, y in zip(a, b)), default=None),
        'mismatches': mismatch,
    }


def compare_palette(left, right):
    a, b = palette_records(left), palette_records(right)
    ordered_mismatch = exact_fields(a, b, ('palette_index', 'name', 'parent_index', 'parent_name',
                                            'skeleton_index', 'global_reference_transform', 'inverse_bind_transform'))
    a_by_name = {x['name']: x for x in a}
    b_by_name = {x['name']: x for x in b}
    common = sorted(set(a_by_name) & set(b_by_name))
    bind_transform_fields = ('skeleton_index', 'global_reference_transform', 'inverse_bind_transform')
    parent_fields = ('parent_name',)
    common_transform_mismatches = []
    common_parent_mismatches = []
    for name in common:
        changed = [f for f in bind_transform_fields if a_by_name[name].get(f) != b_by_name[name].get(f)]
        if changed:
            common_transform_mismatches.append({'name': name, 'fields': changed})
        parent_changed = [f for f in parent_fields if a_by_name[name].get(f) != b_by_name[name].get(f)]
        if parent_changed:
            common_parent_mismatches.append({'name': name, 'fields': parent_changed,
                'left_parent_name': a_by_name[name].get('parent_name'),
                'right_parent_name': b_by_name[name].get('parent_name')})
    return {
        'left_palette_bone_count': len(a), 'right_palette_bone_count': len(b),
        'ordered_palette_record_sha256_left': canonical_hash(a),
        'ordered_palette_record_sha256_right': canonical_hash(b),
        'ordered_palette_records_exact_equal': not ordered_mismatch,
        'ordered_palette_names_left': [x['name'] for x in a],
        'ordered_palette_names_right': [x['name'] for x in b],
        'common_names_by_set': len(common),
        'left_only_names': sorted(set(a_by_name) - set(b_by_name)),
        'right_only_names': sorted(set(b_by_name) - set(a_by_name)),
        'common_named_palette_bind_transforms_exact_equal': not common_transform_mismatches,
        'common_named_palette_transform_mismatches': common_transform_mismatches,
        'common_named_palette_parent_links_exact_equal': not common_parent_mismatches,
        'common_named_palette_parent_link_mismatches': common_parent_mismatches,
        'ordered_palette_mismatches': ordered_mismatch,
    }


def compare_lods(left, right):
    result = []
    for index in range(max(len(left), len(right))):
        if index >= len(left) or index >= len(right):
            result.append({'lod_index': index, 'left_present': index < len(left), 'right_present': index < len(right),
                           'exact_skin_indices_equal': False})
            continue
        a, b = left[index], right[index]
        ai, bi = a.get('skin_indices', []), b.get('skin_indices', [])
        result.append({'lod_index': index + 1, 'left_name': a.get('name'), 'right_name': b.get('name'),
                       'left_material': a.get('material'), 'right_material': b.get('material'),
                       'left_skin_index_count': len(ai), 'right_skin_index_count': len(bi),
                       'left_skin_indices': ai, 'right_skin_indices': bi,
                       'exact_skin_indices_equal': ai == bi,
                       'left_skin_indices_sha256': canonical_hash(ai),
                       'right_skin_indices_sha256': canonical_hash(bi),
                       'left_only_indices': sorted(set(ai) - set(bi)),
                       'right_only_indices': sorted(set(bi) - set(ai))})
    return result


def numbered_xml_path(root, target):
    """Create a stable XPath-like location including same-key sibling indexes."""
    parents = {child: parent for parent in root.iter() for child in parent}
    parts = []
    node = target
    while node is not None:
        key = node.get('Key')
        tag = node.tag
        if key is not None:
            peers = [x for x in (parents.get(node).findall(tag) if parents.get(node) is not None else [node])
                     if x.get('Key') == key]
            suffix = f'[{peers.index(node) + 1}]' if len(peers) > 1 else ''
            parts.append(f'{tag}[@Key={json.dumps(key)}]{suffix}')
        else:
            parts.append(tag)
        node = parents.get(node)
    return '/' + '/'.join(reversed(parts))


def actor_visual_binding_evidence():
    """Tie the native Chinese bodies to the local Vietnamese tier-1 actor."""
    if not LAND_UNITS_REPORT.is_file():
        raise FileNotFoundError(LAND_UNITS_REPORT)
    land_sha = sha(LAND_UNITS_REPORT)
    land = json.loads(LAND_UNITS_REPORT.read_text(encoding='utf-8'))
    if land.get('schema') is None:
        raise RuntimeError('land_units.json lacks a schema')
    actor_rows = [row for row in land.get('units_and_entities', []) if row.get('id') == LOCAL_ACTOR_ID]
    if len(actor_rows) != 1:
        raise RuntimeError(f'Expected one land-unit record for {LOCAL_ACTOR_ID}, found {len(actor_rows)}')
    actor = actor_rows[0]
    if actor.get('source_file') != LOCAL_ACTOR_SOURCE:
        raise RuntimeError('Local actor source path differs from the expected frozen path')
    actor_source = STAGING / 'preparation-source' / actor['source_file']
    actor_sha = sha(actor_source)
    if actor_sha != actor.get('sha256'):
        raise RuntimeError(f'Frozen local actor hash differs from inventory record: {actor_source}')
    target_edges = [edge for edge in actor.get('attachments', []) if edge.get('target') == TIER1_ATTACHMENT_ID]
    if not target_edges:
        raise RuntimeError('Local Vietnamese Villager I does not reference the expected Chinese tier-1 attachment list')

    closure_sha = sha(OFFICIAL_CLOSURE_MANIFEST)
    closure = json.loads(OFFICIAL_CLOSURE_MANIFEST.read_text(encoding='utf-8'))
    if closure_sha != OFFICIAL_CLOSURE_SHA256:
        raise RuntimeError(f'Official closure manifest hash changed: {closure_sha}')
    official_attrib_sha = closure.get('official_attrib_sha256')
    if official_attrib_sha != '03b8e431c91920535fa65cdae340ee206f31bbdfbb1740feddb4a0430625a977':
        raise RuntimeError(f'Official Attrib archive hash differs from expected decoded closure: {official_attrib_sha}')
    members = [member for member in closure.get('members', []) if member.get('member') == TIER1_MEMBER]
    if len(members) != 1:
        raise RuntimeError(f'Expected one official closure entry for {TIER1_MEMBER}, found {len(members)}')
    member = members[0]
    decoded_path = OUT / member['decoded_output']
    decoded_sha = sha(decoded_path)
    if decoded_sha != member.get('decoded_sha256'):
        raise RuntimeError('Decoded tier-1 attachment bytes do not match the closure manifest')
    if member.get('raw_sha256') != '92cc6d69e7629b6bccc44bea4f533804b6ff5b16bddbfcc2f95374dae379f6ad':
        raise RuntimeError('Tier-1 raw official RGD hash differs from the recorded verified input')

    root = ET.parse(decoded_path).getroot()
    body_nodes = []
    for node in root.iter('RGDNode'):
        if node.get('Key') == 'animator0':
            value = node.get('Value')
            if value in EXPECTED_BODY_PATHS.values():
                body_nodes.append({'value': value, 'xpath': numbered_xml_path(root, node)})
    by_value = {}
    for row in body_nodes:
        by_value[row['value']] = by_value.get(row['value'], 0) + 1
    actual_body_paths = sorted(by_value)
    expected_body_paths = sorted(EXPECTED_BODY_PATHS.values())
    exact_body_paths_present = actual_body_paths == expected_body_paths and all(by_value.get(x, 0) > 0 for x in expected_body_paths)
    if not exact_body_paths_present:
        raise RuntimeError(f'Official tier-1 list does not contain exactly the expected Chinese male/female body paths: {by_value}')

    return {
        'status': 'source_and_official_attachment_reference_confirmed',
        'local_actor': {
            'id': LOCAL_ACTOR_ID, 'source_file': actor['source_file'],
            'source_sha256': actor_sha, 'frozen_source_path': actor_source.as_posix(),
            'reachability': actor.get('reachability'), 'land_units_record_sha256': land_sha,
            'land_units_report_path': LAND_UNITS_REPORT.as_posix(),
            'tier1_attachment_edges': [{k: edge.get(k) for k in ('source_file', 'xpath', 'target', 'status', 'variant')}
                                       for edge in target_edges],
        },
        'official_attachment_list': {
            'logical_id': TIER1_ATTACHMENT_ID, 'archive_member': TIER1_MEMBER,
            'official_attrib_archive_sha256': official_attrib_sha,
            'closure_manifest_path': OFFICIAL_CLOSURE_MANIFEST.as_posix(),
            'closure_manifest_sha256': closure_sha,
            'raw_rgd_sha256': member['raw_sha256'], 'decoded_xml_sha256': decoded_sha,
            'decoded_xml_path': decoded_path.as_posix(),
            'expected_chinese_body_paths_present': exact_body_paths_present,
            'animator0_body_path_counts': by_value,
            'animator0_body_path_locations': body_nodes,
        },
        'interpretation': 'The frozen local Vietnamese Villager I actor references the official Chinese tier-1 attachment list. That decoded official list contains male and female Chinese Villager I animator mesh paths. This establishes static visual-reference reachability only; it does not prove effective runtime inheritance, animation playback, or cooked appearance.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT / 'inventory' / 'villager-rig-comparison.json')
    args = parser.parse_args()
    guard()
    output = owned(args.output)
    external = Path(CFG['external_root']) / 'output' / 'release_060'

    loaded, evidence = {}, {}
    for label, pin in PINNED_MANIFESTS.items():
        path = external / pin['path']
        data, manifest_sha = load_manifest(path, pin['sha256'])
        loaded[label] = data
        evidence[label] = input_evidence(data, path, manifest_sha, label, pin)

    prototype_root = OUT / ENGLISH_PROTOTYPE_RELATIVE / ENGLISH_FINGERPRINT
    prototype_path = prototype_root / 'prototype.json'
    prototype, prototype_manifest_sha = load_manifest(prototype_path, ENGLISH_MANIFEST_SHA256)
    if prototype.get('prototype', {}).get('key') != 'english-villager-1':
        raise RuntimeError('Prototype key is not english-villager-1')
    if prototype.get('fingerprint') != ENGLISH_FINGERPRINT:
        raise RuntimeError('English prototype fingerprint differs from pinned expected value')
    prototype_skeleton = prototype['skeleton']
    prototype_model = Path(prototype_skeleton['source'])
    prototype_model_sha = sha(prototype_model)
    expected_proto_hash = prototype_skeleton.get('source_sha256')
    model_rel = prototype['prototype']['bind_model'].replace('\\', '/').lower() + '.rgm'
    manifest_model_hash = next((value for path, value in prototype.get('sources', {}).items()
                                if path.lower() == model_rel), None)
    if prototype_model_sha != expected_proto_hash or manifest_model_hash != expected_proto_hash:
        raise RuntimeError('English prototype bind model hash does not match its prototype source manifest')
    if prototype_skeleton.get('status') != 'hierarchy_decoded':
        raise RuntimeError('English prototype hierarchy was not decoded')
    if not prototype_skeleton.get('skin_palettes') or any(p.get('status') != 'bind_palette_decoded'
                                                          for p in prototype_skeleton['skin_palettes']):
        raise RuntimeError('English prototype skin palette is not decoded')
    evidence['english_supported_prototype'] = {
        'prototype_manifest_path': prototype_path.as_posix(),
        'prototype_manifest_sha256': prototype_manifest_sha,
        'prototype_fingerprint': prototype['fingerprint'],
        'prototype_key': prototype['prototype']['key'],
        'prototype_status': prototype['prototype']['status'],
        'bind_model': prototype['prototype']['bind_model'],
        'animator_owner': prototype['prototype']['owner'],
        'skeleton_source_path': prototype_model.as_posix(),
        'skeleton_source_sha256': prototype_model_sha,
        'garrison_core_path': CFG['garrison_core'],
        'garrison_core_sha256': sha(Path(CFG['garrison_core'])),
        'bone_count_catalogue': prototype['prototype']['bone_count'],
        'lod_counts_catalogue': prototype['prototype']['lod_counts'],
        'status_interpretation': 'Build supported in the installed prototype catalogue; that does not qualify Chinese native animation ownership.'}

    comparisons = {}
    for label, data in loaded.items():
        gender = label.removeprefix('chinese_').removesuffix('_villager_i')
        native_skeleton = data['skeleton']
        native_palette = native_skeleton['skin_palettes'][0]
        english_palette = prototype_skeleton['skin_palettes'][0]
        comparisons[label] = {
            'native_gender': gender,
            'skeleton_vs_english': compare_skeleton(native_skeleton, prototype_skeleton),
            'skin_palette_vs_english': compare_palette(native_palette, english_palette),
            'lod_skin_index_arrays_vs_english': compare_lods(native_palette.get('lod_palettes', []),
                                                               english_palette.get('lod_palettes', [])),
            'lod_skin_index_arrays_all_exact': all(x.get('exact_skin_indices_equal', False)
                                                   for x in compare_lods(native_palette.get('lod_palettes', []),
                                                                         english_palette.get('lod_palettes', []))),
        }

    visual_binding_evidence = actor_visual_binding_evidence()

    male = loaded['chinese_male_villager_i']['skeleton']
    female = loaded['chinese_female_villager_i']['skeleton']
    male_palette, female_palette = male['skin_palettes'][0], female['skin_palettes'][0]
    within_chinese = {
        'male_female_skeleton_records': compare_skeleton(male, female),
        'male_female_skin_palette': compare_palette(male_palette, female_palette),
        'male_female_lod_skin_index_arrays': compare_lods(male_palette['lod_palettes'], female_palette['lod_palettes']),
    }
    skeleton_exact = all(x['skeleton_vs_english']['ordered_bone_records_exact_equal']
                         for x in comparisons.values())
    palette_exact = all(x['skin_palette_vs_english']['ordered_palette_records_exact_equal']
                        and x['lod_skin_index_arrays_all_exact'] for x in comparisons.values())
    result = {
        'schema': 'ccp-release060-villager-rig-comparison/v1',
        'status': 'hash_pinned_static_rig_and_palette_comparison_complete',
        'generated_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'input_evidence': evidence,
        'actor_visual_binding_evidence': visual_binding_evidence,
        'chinese_male_and_female': within_chinese,
        'native_gender_vs_supported_english_prototype': comparisons,
        'summary': {
            'full_ordered_skeleton_records_equal_for_both_chinese_genders': skeleton_exact,
            'full_ordered_palette_and_all_lod_arrays_equal_for_both_genders': palette_exact,
            'model_only_cook_probe_candidate': 'candidate_for_separate_model_only_probe; the full 73-bone ordered hierarchy/rest transforms and common named palette bind transforms match, but the Chinese palette has one extra neck2 bone, the head palette parent differs, and every LOD skin-index array differs. Treat palette remapping/cooked readback as an explicit probe gate before integration.',
            'native_animation_qualification': 'not established; decoded Chinese records resolve to the base_civilian animation library with metadata-only clip inventory and no gameplay action mapping. Matching owner and hierarchy do not prove animation playback or a native animation replacement.',
            'runtime_qualification': 'not performed',
        },
        'limits': [
            'The English Garrison prototype is an authoring/build catalogue entry, not the Chinese unit animation contract.',
            'This compares decoded skeleton, skin-palette bind records, and three LOD skin-index arrays; it does not compare mesh positions, weights, UVs, materials, attachment offsets, or cooked output.',
            'No Blender scene, cook, Content Editor source, active resource, or native game state was modified.',
        ],
    }
    write(output, result)
    print(f'output={output.as_posix()}')
    print(f'skeleton_exact={skeleton_exact} palette_and_lods_exact={palette_exact}')


if __name__ == '__main__':
    main()

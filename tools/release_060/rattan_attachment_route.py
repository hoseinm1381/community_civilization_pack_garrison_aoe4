"""Selective read-only inspection of six stock Chinese tier attachment RGDs."""
from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

from common import OUT, guard, owned, sha, write

INVENTORY_DIR = OUT / 'inventory'
OUT_DIR = OUT / 'rattan-probe'
CLOSURE_PATH = INVENTORY_DIR / 'official_rgd_closure_03b8e431c91920535fa65cdae340ee206f31bbdfbb1740feddb4a0430625a977.json'
CLOSURE_SHA256 = 'b6a437f6db28ddc67d8c9732cd8f6279e3150d81a299b377c6d8e6b03b48d881'
PROBE_REPORT_PATH = OUT_DIR / 'report.json'
PROBE_REPORT_SHA256 = '2fcd7eae0c2e347beed099dd57f8b03533988b818b9d7f31ad21cd3cd161f556'
OFFICIAL_ATTRIB_SHA256 = '03b8e431c91920535fa65cdae340ee206f31bbdfbb1740feddb4a0430625a977'
ATTACHMENT_IDS = (
    'tier2_archer_chi', 'tier3_archer_chi', 'tier4_archer_chi',
    'tier3_crossbowman_chi', 'tier4_crossbowman_chi', 'tier4_handcannon_chi',
)
PAVISE_UPGRADE_MEMBER = 'attrib/upgrade/races/japanese_ha_sen/research/clan_upgrades/upgrade_tanegashima_pavise_jpn_ha_sen.rgd'
PAVISE_ABILITY_MEMBER = 'attrib/abilities/always_on_abilities/japanese_ha_sen/tanegashima_tate_ability_jpn_ha_sen.rgd'
PAVISE_UPGRADE_SHA256 = 'c631f359e621c7d7fcccb434fd182202b62cebc5b7e3f348a11863045b4af612'
PAVISE_ABILITY_SHA256 = '8d824c1f32afc5f64745fa815d2160f0b7a89af2f979fa385bfbe8f897717fbb'


def indexed_path(root: ET.Element, target: ET.Element) -> str:
    parents = {child: parent for parent in root.iter() for child in parent}
    parts = []
    node = target
    while node is not None:
        key = node.get('Key')
        parent = parents.get(node)
        if key is None:
            parts.append(node.tag)
        else:
            peers = [x for x in (parent.findall(node.tag) if parent is not None else [node])
                     if x.get('Key') == key]
            index = f'[{peers.index(node)+1}]' if len(peers) > 1 else ''
            parts.append(f'{node.tag}[@Key={json.dumps(key)}]{index}')
        node = parent
    return '/' + '/'.join(reversed(parts))


def children(node: ET.Element | None, key: str):
    return [x for x in (list(node) if node is not None else []) if x.get('Key') == key]


def node_value(node: ET.Element | None, key: str):
    found = next(iter(children(node, key)), None)
    return found.get('Value') if found is not None else None


def pbg_ref(node: ET.Element | None):
    if node is None:
        return None
    name, path = node_value(node, '$PBGNAME'), node_value(node, '$PBGMAP')
    if not name and not path:
        return None
    return (path.rstrip('\\') + '\\' if path else '') + (name or '')


def list_attachment_evidence(xml_path: Path, member: dict):
    if sha(xml_path) != member['decoded_sha256']:
        raise RuntimeError(f"Decoded attachment XML hash mismatch: {member['member']}")
    root = ET.parse(xml_path).getroot()
    variants = []
    for variant_name in ('default', 'cordoba', 'campaign'):
        variant = next((x for x in root if x.get('Key') == variant_name), None)
        lists = next(iter(children(variant, 'attachment_lists')), None)
        collection = next(iter(children(lists, 'attachment_lists')), None)
        entries = []
        for entry in children(collection, 'attachment_list'):
            attachments = next(iter(children(entry, 'attachment_list')), None)
            mesh_attachment = next(iter(children(attachments, 'animator_merge_mesh_attachment')), None)
            meshes = next(iter(children(mesh_attachment, 'meshes')), None)
            animator_refs = [{'value': x.get('Value'), 'path': indexed_path(root, x)} for x in children(meshes, 'animator0')]
            entries.append({
                'attachment_category': node_value(entry, 'attachment_category'),
                'inventory_category': node_value(entry, 'inventory_category'),
                'attachment_template_ref': node_value(entry, '$REF'),
                'mesh_attachment_template_ref': node_value(mesh_attachment, '$REF'),
                'animator_mesh_refs': animator_refs,
                'is_selectable': node_value(mesh_attachment, 'is_selectable'),
                'speaker_code': node_value(entry, 'attachment_speaker_code'),
            })
        variant_root_ref = next(iter(children(lists, '$REF')), None)
        parent = next(iter(children(variant, 'parent_pbg')), None)
        variants.append({
            'variant': variant_name,
            'parent_animator': node_value(lists, 'parent_animator'),
            'attachment_lists_template_ref': variant_root_ref.get('Value') if variant_root_ref is not None else None,
            'parent_pbg': pbg_ref(parent),
            'entry_count': len(entries),
            'entries': entries,
        })
    sensitive_nodes = []
    for node in root.iter('RGDNode'):
        key = (node.get('Key') or '').lower()
        if node.get('Value') is not None and any(term in key for term in
                ('require', 'condition', 'visible', 'visibility', 'upgrade', 'age', 'tier', 'filter')):
            sensitive_nodes.append({'key': node.get('Key'), 'value': node.get('Value'),
                                    'path': indexed_path(root, node)})
    return {
        'member': member['member'], 'raw_sha256': member['raw_sha256'], 'decoded_xml_path': xml_path.as_posix(),
        'decoded_xml_sha256': sha(xml_path), 'root_parent_pbg': pbg_ref(next(iter(children(next(iter(children(root, 'default')), None), 'parent_pbg')), None)),
        'variant_count': len(variants), 'variants': variants,
        'requirement_or_visibility_condition_fields': sensitive_nodes,
        'no_explicit_condition_fields_in_record': len(sensitive_nodes) == 0,
    }


def probe_record(report: dict, member: str, expected_sha: str):
    record = next((x for x in report.get('records', []) if x.get('member') == member), None)
    if record is None or record.get('rgd_sha256') != expected_sha:
        raise RuntimeError(f'Pinned Rattan probe member missing or changed: {member}')
    xml = Path(record['xml'])
    if not xml.is_file():
        raise FileNotFoundError(xml)
    return record, xml


def selected_probe_fields(xml_path: Path):
    root = ET.parse(xml_path).getroot()
    fields = []
    for node in root.iter('RGDNode'):
        key = node.get('Key') or ''
        value = node.get('Value')
        if value is None:
            continue
        low = key.lower()
        path = indexed_path(root, node)
        path_low = path.lower()
        tokens = ('requirement', 'upgrade', 'state_tree', 'filter', 'unit_class', 'attachment',
                  'animator', 'visible', 'condition', 'apply_to_future', 'apply_to_application',
                  'apply_to_target', 'ability_activate')
        if any(token in low or token in path_low for token in tokens):
            fields.append({'key': key, 'value': value, 'type': node.get('Type'), 'path': path})
    return fields


def main():
    guard()
    closure_bytes = sha(CLOSURE_PATH)
    if closure_bytes != CLOSURE_SHA256:
        raise RuntimeError(f'Official closure manifest changed: {closure_bytes}')
    closure = json.loads(CLOSURE_PATH.read_text(encoding='utf-8'))
    if closure.get('official_attrib_sha256') != OFFICIAL_ATTRIB_SHA256:
        raise RuntimeError('Official archive SHA differs from the pinned closure')
    report_hash = sha(PROBE_REPORT_PATH)
    if report_hash != PROBE_REPORT_SHA256:
        raise RuntimeError(f'Pinned Rattan probe report changed: {report_hash}')
    probe = json.loads(PROBE_REPORT_PATH.read_text(encoding='utf-8'))

    attachment_rows = []
    for attachment_id in ATTACHMENT_IDS:
        member_name = f'attrib/attachments/attachment_lists/civilizations/chinese/units/{attachment_id}.rgd'
        members = [x for x in closure.get('members', []) if x.get('member') == member_name]
        if len(members) != 1:
            raise RuntimeError(f'Expected one official closure member for {member_name}; found {len(members)}')
        member = members[0]
        raw_path = OUT / member['raw_output']
        if sha(raw_path) != member['raw_sha256']:
            raise RuntimeError(f'Official raw attachment RGD hash mismatch: {member_name}')
        xml_path = OUT / member['decoded_output']
        attachment_rows.append(list_attachment_evidence(xml_path, member))

    upgrade, upgrade_xml = probe_record(probe, PAVISE_UPGRADE_MEMBER, PAVISE_UPGRADE_SHA256)
    ability, ability_xml = probe_record(probe, PAVISE_ABILITY_MEMBER, PAVISE_ABILITY_SHA256)
    upgrade_fields = selected_probe_fields(upgrade_xml)
    ability_fields = selected_probe_fields(ability_xml)
    upgrade_attachments = [x for x in upgrade_fields if any(k in x['key'].lower() for k in ('attachment', 'animator', 'visible'))]
    ability_activation = [x for x in ability_fields if 'ability_activate' in x['key']]
    Pavise_evidence = {
        'upgrade': {'member': upgrade['member'], 'raw_sha256': upgrade['rgd_sha256'],
                    'decoded_xml_path': upgrade_xml.as_posix(), 'decoded_xml_sha256': sha(upgrade_xml),
                    'selected_fields': upgrade_fields,
                    'filter_fields': [x for x in upgrade_fields if 'filter' in x['path'].lower() or 'unit_class' in x['key']],
                    'attachment_or_visibility_fields': upgrade_attachments},
        'always_on_ability': {'member': ability['member'], 'raw_sha256': ability['rgd_sha256'],
                              'decoded_xml_path': ability_xml.as_posix(), 'decoded_xml_sha256': sha(ability_xml),
                              'selected_fields': ability_fields, 'activation_fields': ability_activation},
    }
    every_tier_is_static_single_body_ref = all(
        v['entry_count'] == 1 and all(len(e['animator_mesh_refs']) == 1 for e in v['entries'])
        for row in attachment_rows for v in row['variants'])
    no_condition_fields = all(row['no_explicit_condition_fields_in_record'] for row in attachment_rows)
    japanese_is_attachment_example = any(x.get('value') for x in upgrade_attachments + ability_activation)
    result = {
        'schema': 'ccp-release060-rattan-attachment-route/v1',
        'status': 'selective_official_attachment_and_upgrade_probe_complete_route_unresolved',
        'official_attrib_archive_sha256': OFFICIAL_ATTRIB_SHA256,
        'closure_manifest_path': CLOSURE_PATH.as_posix(), 'closure_manifest_sha256': closure_bytes,
        'rattan_probe_report_path': PROBE_REPORT_PATH.as_posix(), 'rattan_probe_report_sha256': report_hash,
        'six_official_chinese_tier_attachment_records': attachment_rows,
        'japanese_tanegashima_pavise_probe': Pavise_evidence,
        'finding': {
            'six_records_have_only_single_static_body_mesh_entry': every_tier_is_static_single_body_ref,
            'six_records_have_no_explicit_requirement_or_visibility_fields': no_condition_fields,
            'observed_variants': ['default', 'cordoba', 'campaign'],
            'body_reference_patterns': 'Each record has one default-category/default-inventory attachment entry per variant, animator_merge_mesh_attachment, one animator0 body mesh reference, selectable=true, and no explicit requirement/visibility condition field in the attachment RGD itself.',
            'pavise_example_supports_research_added_carried_equipment': False,
            'pavise_reason': 'The upgrade has a class filter and entity action-tree reference but no attachment/visibility fields in the inspected RGD. The always-on ability activation tree fields are empty. These two records do not establish a carried-equipment addition after research without actor replacement.',
            'route': 'unresolved; stop before proposing a tier-group or attachment overlay. The six Chinese records supply stock tier body references, not a demonstrated conditional equipment route. Do not infer behavior from the Japanese filter or an unresolved action-tree name.',
            'next_evidence_needed': ['official Attribute Editor structure or current official compiled records for a concrete research-conditioned carried-equipment example, including its action tree and target actor attachment path',
                                     'native-match observation proving actor/orders persist and the new equipment appears after research'],
        },
        'preservation': {'actual_upgrade_id': 'upgrade\\vietnam\\vn_ratten_shield_vit',
                         'rattan_armor_scar_path': 'scar\\vietnam\\rattan_armor.scar',
                         'instruction': 'Keep existing +1 armor behavior unchanged; this probe is read-only.'},
        'limits': ['Only six exact Chinese tier attachment-list RGDs plus the already-extracted Japanese upgrade and always-on ability were inspected.',
                   'No broad archive decode, new source edits, Content Editor build, cook, or native match was performed.'],
    }
    output = owned(OUT_DIR / 'attachment-route.json')
    write(output, result)
    print(f'output={output.as_posix()}')
    print(f'attachments={len(attachment_rows)} static_single_mesh={every_tier_is_static_single_body_ref} no_conditions={no_condition_fields}')
    print(f'pavise_example_support={japanese_is_attachment_example}')


if __name__ == '__main__':
    main()

"""Read-only tier/attachment compatibility matrix for the 0.6.0 rattan visual probe.

Inputs are frozen source XML, source-parity-matched 0.5.2 diagnostic compiled
records, and a pinned stock Chinese Villager I compiled record. Outputs are
limited to output/release_060/rattan-probe.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from common import OUT, STAGING, guard, owned, sha, write

OUT_DIR = OUT / 'rattan-probe'
COMPILED_MANIFEST_PATH = OUT / 'inventory' / 'compiled_052_diagnostic_b_6553fb4b40f65fb7be8f8386f50f74a9826de8ebbe4eddac6e561ee06774221f.json'
COMPILED_MANIFEST_SHA256 = '3fcb93acb3de40491ba4c97fec88753a8b9ac2760dfac92b9e55552d731303a2'
DIAGNOSTIC_SGA_SHA256 = '6553fb4b40f65fb7be8f8386f50f74a9826de8ebbe4eddac6e561ee06774221f'
RATTAN_PROBE_REPORT = OUT_DIR / 'report.json'
RATTAN_PROBE_REPORT_SHA256 = '2fcd7eae0c2e347beed099dd57f8b03533988b818b9d7f31ad21cd3cd161f556'
NATIVE_VILLAGER_RGD_SHA256 = 'd21187f5505bd254929767d1d712db2fb7cdc453bac92d841c9a853b4139bfaa'
NATIVE_VILLAGER_XML_SHA256 = '0567f8845c4d12a6c1632d0c3cee7dc07af4cc24b9707c4b57938392f16fc3b9'
ACTORS = {
    'vn_unit_archer_2_vit': ('eb239e9ef3636ea66bef6dd9b1642b02be3aa09213d819e29d9f58e621826ccf', 'd9055e5df3cbb82aa72e7bbb8b9b41b419eb38c23cf7c3b00f16af0166f1aa9e'),
    'vn_unit_archer_3_vit': ('cd7a04649428521e9768900d598327892bec55a857c57c0d47bdf67d8a533532', '419897e69582758c701c383a42e43689f71e94680e5e6b99d02a90a898493ae4'),
    'vn_unit_archer_4_vit': ('43a5483ca2d4e38f41cf030a4c288eb77a7cbf48172ba8224dbe069680ed0885', '86e6e85f54dec697c44d12b12f26ce5f3e1de8de4a561e1edd3f4700d48d4928'),
    'vn_unit_crossbowman_3_chi': ('049a5b999f9f68e4e3f7122c4f88f396828f180d16c6a6ed0012fc8e4c2fa655', '20df568c912ef2575e74e877dbdd10e21793c2fe4d173e2433ae6a09ad4acd19'),
    'vn_unit_crossbowman_4_chi': ('9c51b28ed4feffb5ff228c7f5b865785ed61cf4f64b8b9fa7d5ff9db13c134c2', '02ff1b2febcfddf030c2de46f0d9f9ba480e95efbe725329e419f37c22ec47ec'),
    'vn_unit_handcannon_4_chi': ('4d4fa5dfb581856d3edb0e43c27d55e70fd2cf56cb22d3a3049c1b796ce71d39', 'b5d0fe57c6e05fe2d62312aaa078752a5bb5e06f111685a8fd3c025e9351b580'),
}
RANGED_BUILDING = 'ebps\\vietnam\\vn_building_unit_ranged_control_chi'
ACTOR_PREFIX = 'ebps\\vietnam\\'
SQUAD_PREFIX = 'sbps\\vietnam\\'
CHEAP_HANDCANNON = 'sbps\\vietnam\\vn_unit_handcannon_4_chi_cheap'
ACTUAL_RATTAN_UPGRADE = 'upgrade\\vietnam\\vn_ratten_shield_vit'
LOOKALIKE_RATTAN_UPGRADE = 'upgrade\\vietnam\\vn_upgrade_rattan_shields_vit'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, expected_sha: str | None = None):
    actual = sha(path)
    if expected_sha and actual != expected_sha:
        raise RuntimeError(f'Pinned JSON changed: {path} expected={expected_sha} actual={actual}')
    return json.loads(path.read_text(encoding='utf-8')), actual


def find_named(node: ET.Element, tag: str, name: str):
    return next((x for x in node.iter(tag) if x.get('name') == name), None)


def source_tier_refs(path: Path):
    root = ET.parse(path).getroot()
    variants = [('base', root)]
    variants.extend((x.get('name') or 'unnamed_variant', x) for x in root.findall('variant'))
    results = {}
    for variant, parent in variants:
        tier_list = parent.find("list[@name='extensions']/template_reference[@name='exts']/list[@name='tier_group_list']")
        if tier_list is None:
            continue
        groups = []
        for group in [x for x in tier_list if x.tag == 'list' and x.get('name') == 'tier_group']:
            tiers = []
            for tier in [x for x in group if x.tag == 'group' and x.get('name') == 'tier']:
                def val(name):
                    n = next((y for y in tier if y.get('name') == name), None)
                    return n.get('value') if n is not None else None
                action = find_named(tier, 'template_reference', 'statetree_tier_reached_actions')
                action_node = next((x for x in action.iter('state_tree_node')), None) if action is not None else None
                tiers.append({
                    'item_id': tier.get('List.ItemID'), 'parent_item_id': tier.get('List.ParentItemID'),
                    'list_action': tier.get('List.ListAction'), 'attachments': val('attachments'),
                    'requirement': val('statetree_tier_requirements_pbg'),
                    'upgrade_target_entity': val('statetree_tier_pgb_upgrade_target_entity'),
                    'upgrade_target_squad': val('statetree_tier_pgb_upgrade_target_squad'),
                    'reached_action': action_node.get('value') if action_node is not None else None,
                    'tier_attachment_action': val('tier_attachment_action'),
                    'inventory_category_to_refresh': val('inventory_category_to_refresh_on_tier_up'),
                })
            groups.append({'item_id': group.get('List.ItemID'), 'parent_item_id': group.get('List.ParentItemID'),
                           'list_action': group.get('List.ListAction'), 'tiers': tiers})
        results[variant] = {
            'list_attributes': dict(tier_list.attrib),
            'groups': groups,
        }
    return results


def compiled_ref(node: ET.Element, key: str):
    ref = next((x for x in node if x.get('Key') == key), None)
    if ref is None:
        return None
    if ref.get('Type') == 'List':
        name = next((x.get('Value') for x in ref if x.get('Key') == '$PBGNAME'), None)
        path = next((x.get('Value') for x in ref if x.get('Key') == '$PBGMAP'), None)
        if not name and not path:
            return None
        return (path.rstrip('\\') + '\\' if path else '') + (name or '')
    return ref.get('Value')


def compiled_tier_refs(path: Path):
    root = ET.parse(path).getroot()
    results = {}
    for variant_name in ('default', 'campaign'):
        variant = next((x for x in root if x.get('Key') == variant_name), None)
        if variant is None:
            continue
        ext = next((x for x in variant if x.get('Key') == 'tier_ext'), None)
        if ext is None:
            results[variant_name] = {'tier_ext_present': False, 'groups': []}
            continue
        tier_list = next((x for x in ext if x.get('Key') == 'tier_group_list'), None)
        groups = []
        for group in [x for x in (tier_list if tier_list is not None else []) if x.get('Key') == 'tier_group']:
            tiers = []
            for tier in [x for x in group if x.get('Key') == 'tier']:
                action = next((x for x in tier if x.get('Key') == 'statetree_tier_reached_actions'), None)
                tiers.append({
                    'attachments': compiled_ref(tier, 'attachments'),
                    'requirement': compiled_ref(tier, 'statetree_tier_requirements_pbg'),
                    'upgrade_target_entity': compiled_ref(tier, 'statetree_tier_pgb_upgrade_target_entity'),
                    'upgrade_target_squad': compiled_ref(tier, 'statetree_tier_pgb_upgrade_target_squad'),
                    'reached_action': next((n.get('Value') for n in (action if action is not None else [])
                                            if n.get('Key') == 'ActionTree_OpeningBranch'), None),
                })
            groups.append({'tiers': tiers})
        results[variant_name] = {'tier_ext_present': True, 'groups': groups}
    return results


def normalize_tiers(tier_data):
    def leaf(value):
        if value is None or value == '':
            return None
        return value.rsplit('\\', 1)[-1].rsplit(':', 1)[-1]
    normalized = {}
    for variant, value in tier_data.items():
        target_variant = 'default' if variant == 'base' else variant
        normalized[target_variant] = [[{k: leaf(tier.get(k)) for k in ('attachments', 'requirement',
                                                                          'upgrade_target_entity', 'upgrade_target_squad')}
                                       for tier in group['tiers']] for group in value.get('groups', [])]
    return normalized


def source_xpath(root: ET.Element, target: ET.Element):
    parents = {child: parent for parent in root.iter() for child in parent}
    parts, node = [], target
    while node is not None:
        pred = ''
        if node.get('name') is not None:
            pred = f"[@name='{node.get('name')}']"
        elif node.get('value') is not None:
            pred = f"[@value='{node.get('value')}']"
        parent = parents.get(node)
        same = [x for x in parent if x.tag == node.tag and x.get('name') == node.get('name')] if parent is not None and node.get('name') else []
        if len(same) > 1:
            pred += f'[{same.index(node)+1}]'
        parts.append(f'{node.tag}{pred}')
        node = parent
    return '/' + '/'.join(reversed(parts))


def inbound_references(source_root: Path):
    targets = {SQUAD_PREFIX + key for key in ACTORS} | {CHEAP_HANDCANNON, ACTUAL_RATTAN_UPGRADE, LOOKALIKE_RATTAN_UPGRADE}
    found = []
    for path in sorted(source_root.rglob('*.xml')):
        root = ET.parse(path).getroot()
        relative = path.relative_to(source_root).as_posix()
        for node in root.iter():
            target = node.get('value')
            if target in targets:
                found.append({'source_file': relative, 'source_sha256': sha(path), 'xpath': source_xpath(root, node),
                              'tag': node.tag, 'reference_name': node.get('name'), 'target': target,
                              'override_parent': node.get('overrideParent'), 'list_item_id': node.get('List.ItemID')})
    return found


def native_stock_villager(probe_report):
    record = next(x for x in probe_report['records'] if x.get('member') == 'attrib/ebps/races/chinese/units/unit_villager_1_chi.rgd')
    raw = Path(record['xml']).with_suffix('.rgd')
    xml = Path(record['xml'])
    if sha(raw) != NATIVE_VILLAGER_RGD_SHA256:
        raise RuntimeError('Pinned native Chinese Villager I RGD raw bytes changed')
    if sha(xml) != NATIVE_VILLAGER_XML_SHA256:
        raise RuntimeError('Pinned native Chinese Villager I decoded XML hash changed')
    root = ET.parse(xml).getroot()
    result = []
    for variant in ('default', 'cordoba', 'campaign'):
        ext_parent = next((x for x in root if x.get('Key') == variant), None)
        ext = next((x for x in (ext_parent if ext_parent is not None else []) if x.get('Key') == 'tier_ext'), None)
        groups = []
        tier_list = next((x for x in (ext if ext is not None else []) if x.get('Key') == 'tier_group_list'), None)
        for group in [x for x in (tier_list if tier_list is not None else []) if x.get('Key') == 'tier_group']:
            tiers = []
            for tier in [x for x in group if x.get('Key') == 'tier']:
                tiers.append({'attachment': compiled_ref(tier, 'attachments'),
                              'requirement': compiled_ref(tier, 'statetree_tier_requirements_pbg'),
                              'target_entity': compiled_ref(tier, 'statetree_tier_pgb_upgrade_target_entity'),
                              'target_squad': compiled_ref(tier, 'statetree_tier_pgb_upgrade_target_squad')})
            groups.append(tiers)
        if ext is not None:
            result.append({'variant': variant, 'group_count': len(groups), 'tier_counts': [len(x) for x in groups], 'groups': groups})
    return {'member': record['member'], 'raw_sha256': record['rgd_sha256'], 'decoded_xml_path': xml.as_posix(),
            'decoded_xml_sha256': sha(xml), 'tier_ext_variants': result}


def rattan_preservation_evidence(source_root: Path):
    actual_path = source_root / 'upgrade' / 'vietnam' / 'vn_ratten_shield_vit.xml'
    lookalike_path = source_root / 'upgrade' / 'vietnam' / 'vn_upgrade_rattan_shields_vit.xml'
    scar_path = STAGING / 'preparation-source' / 'assets' / 'scar' / 'vietnam' / 'rattan_armor.scar'
    actual = ET.parse(actual_path).getroot()
    lookalike = ET.parse(lookalike_path).getroot()
    scar_text = scar_path.read_text(encoding='utf-8')
    in_roster = scar_text.split('local roster = {', 1)[-1].split('}', 1)[0]
    roster = re.findall(r'"([^"]+)"', in_roster)
    def identity(root):
        uid = next((x.get('value') for x in root if x.tag == 'uniqueid' and x.get('name') == 'pbgid'), None)
        parent = next((x.get('value') for x in root if x.tag == 'instance_reference' and x.get('name') == 'parent_pbg'), None)
        requirements = [{'path': source_xpath(root, node), 'value': node.get('value'), 'mod': node.get('mod')}
                        for node in root.iter('instance_reference') if node.get('name') == 'upgrade_name']
        return {'pbgid': uid, 'parent_pbg': parent, 'upgrade_name_requirements': requirements}
    required_literals = [
        'BP_GetUpgradeBlueprint("b7fcea91257b408fb9e8ae4d8bc402e1:vn_ratten_shield_vit")',
        '"armor_scalar_for_ranged_damage"', 'MUT_Addition, false, 1',
    ]
    if len(roster) != 6 or not all(x in scar_text for x in required_literals):
        raise RuntimeError('Rattan armor source no longer has its pinned upgrade/stat/roster contract')
    return {
        'actual_upgrade_source': {'path': actual_path.as_posix(), 'sha256': sha(actual_path), **identity(actual)},
        'lookalike_upgrade_source': {'path': lookalike_path.as_posix(), 'sha256': sha(lookalike_path), **identity(lookalike)},
        'scar_source': {
            'path': scar_path.as_posix(), 'sha256': sha(scar_path),
            'upgrade_blueprint': 'b7fcea91257b408fb9e8ae4d8bc402e1:vn_ratten_shield_vit',
            'modifier_property': 'armor_scalar_for_ranged_damage', 'modifier_operation': 'MUT_Addition',
            'modifier_value': 1, 'roster': roster,
            'cleanup_removes_applied_modifiers': 'function VietnamRattanArmor_Cleanup' in scar_text,
        },
        'preservation_interpretation': 'The existing actual upgrade ID, +1 ranged-damage armor SCAR modifier, and exact six-unit roster remain the preservation contract. The similarly named vn_upgrade_rattan_shields_vit is a distinct lookalike and is not the SCAR-trigger ID.',
    }


def main():
    guard()
    source_root = STAGING / 'preparation-source' / 'assets' / 'attrib' / 'instances'
    if not source_root.is_dir():
        raise FileNotFoundError(source_root)
    manifest, manifest_sha = read_json(COMPILED_MANIFEST_PATH,
                                       COMPILED_MANIFEST_SHA256 if COMPILED_MANIFEST_SHA256 != 'TODO' else None)
    if manifest.get('diagnostic_sga_sha256') != DIAGNOSTIC_SGA_SHA256:
        raise RuntimeError('Diagnostic SGA hash differs from the source-parity evidence ledger')
    parity = manifest.get('source_parity', {})
    if not parity.get('all_314_frozen_asset_hashes_and_sizes_match') or parity.get('mismatched_paths'):
        raise RuntimeError('Diagnostic compiled data lacks clean 0.6.0 source parity')
    report, report_sha = read_json(RATTAN_PROBE_REPORT, RATTAN_PROBE_REPORT_SHA256)

    records = {x['actor_id'].split('\\')[-1]: x for x in manifest.get('compiled_producer_lists', [])
               if x.get('actor_id', '').startswith(ACTOR_PREFIX)}
    actor_rows = []
    for actor_id, (source_sha_expected, decoded_sha_expected) in ACTORS.items():
        record = records.get(actor_id)
        if not record or not record.get('source_hash_parity') or record.get('source_sha256') != source_sha_expected:
            raise RuntimeError(f'{actor_id} is not covered by the pinned source-parity producer ledger')
        if record.get('decoded_xml_sha256') != decoded_sha_expected:
            raise RuntimeError(f'{actor_id} compiled decoded XML SHA differs from its pinned evidence')
        source_path = source_root / record['source_file'].removeprefix('attrib/instances/')
        if sha(source_path) != source_sha_expected:
            raise RuntimeError(f'{actor_id} frozen source XML hash changed')
        source_tiers = source_tier_refs(source_path)
        compiled_path = Path(record['decoded_xml_path'])
        if sha(compiled_path) != decoded_sha_expected:
            raise RuntimeError(f'{actor_id} decoded diagnostic XML hash changed')
        compiled_tiers = compiled_tier_refs(compiled_path)
        source_normalized = normalize_tiers(source_tiers)
        compiled_normalized = normalize_tiers(compiled_tiers)
        actor_rows.append({
            'actor_id': ACTOR_PREFIX + actor_id, 'source_file': record['source_file'],
            'source_sha256': source_sha_expected, 'compiled_member': record['compiled_member'],
            'compiled_raw_sha256': record['compiled_raw_sha256'], 'compiled_decoded_xml_sha256': decoded_sha_expected,
            'source_hash_parity': True, 'source_tier_ext': source_tiers, 'compiled_tier_ext': compiled_tiers,
            'normalized_source_vs_compiled_tiers_equal': source_normalized == compiled_normalized,
            'local_source_declares_list_override': all(v['list_attributes'].get('overrideParent') == 'True'
                                                       for v in source_tiers.values()),
            'interpretation': 'The Vietnamese actor serializes a complete tier_group_list override; its explicit Chinese attachment references are the tiers represented in the source-parity compiled child. This verifies static serialization, not animation or in-game visual composition.',
        })

    native = native_stock_villager(report)
    rattan_behavior = rattan_preservation_evidence(source_root)
    all_refs = inbound_references(source_root)
    consumer_matrix = {
        'six_visual_actor_ids': [ACTOR_PREFIX + x for x in ACTORS],
        'cheap_handcannon_squad': CHEAP_HANDCANNON,
        'rattan_upgrade_actual': ACTUAL_RATTAN_UPGRADE,
        'rattan_upgrade_lookalike': LOOKALIKE_RATTAN_UPGRADE,
        'inbound_reference_edges': all_refs,
    }
    group_set = {len(v.get('groups', [])) for actor in actor_rows for v in actor['compiled_tier_ext'].values()}
    sequence_matches = all(row['normalized_source_vs_compiled_tiers_equal'] for row in actor_rows)
    conclusion = {
        'source_list_override': 'The source XML explicitly marks tier_group_list overrideParent=True for base and campaign on all six visual actors. The list supplies one complete group with the actor’s intended stock Chinese tier attachment references. Treat this as replacement of the inherited list at this property; preserving a visual progression means preserving the entire desired tier sequence in the override.',
        'attachment_selection': 'Each serialized tier entry has one attachments instance reference to one named attachment-list resource. No source evidence says a second tier_group composes its meshes with the first group, or that a second attachment reference is merged. An additional group therefore is not statically established as a visual overlay mechanism.',
        'recommendation_for_art_scope': 'Do not add a parallel tier_group as a presumed overlay. Inspect the exact official Chinese attachment-list RGD for each affected tier and its mesh/material entries; any overlay approach must preserve the referenced tier list(s) and be proven in Attribute Editor serialization plus a native match. Keep the existing +1 armor upgrade and rattan_armor.scar path unchanged.',
        'static_support': 'Source declaration and diagnostic compiled child structures match for all six actors under complete frozen-source parity. The matching stock Chinese Villager I example has one tier group with four sequential tier attachment references in default, cordoba, and campaign variants.',
        'unresolved_runtime_cases': ['whether the engine evaluates multiple tier_group entries additively, alternatively, or with another rule',
                                    'whether an attachment list can display an additional armor mesh without replacing the base unit mesh set',
                                    'visual result through tier-up conversion, SCAR armor grant, model cooked output, and native animation'],
    }
    result = {
        'schema': 'ccp-release060-rattan-tier-attachment-compatibility/v1',
        'status': 'static_source_and_source_parity_compiled_reconciliation_complete_runtime_unqualified',
        'input_evidence': {
            'compiled_manifest_path': COMPILED_MANIFEST_PATH.as_posix(), 'compiled_manifest_sha256': manifest_sha,
            'diagnostic_sga_path': manifest.get('diagnostic_sga'), 'diagnostic_sga_sha256': manifest['diagnostic_sga_sha256'],
            'source_parity': parity, 'compiled_producer_ledger_count': len(manifest.get('compiled_producer_lists', [])),
            'rattan_probe_report_path': RATTAN_PROBE_REPORT.as_posix(), 'rattan_probe_report_sha256': report_sha,
            'official_archive_path_from_probe': report.get('archive'),
        },
        'actor_tier_matrix': actor_rows,
        'stock_chinese_villager_i_example': native,
        'rattan_armor_preservation_evidence': rattan_behavior,
        'consumers_and_rattan_upgrade_references': consumer_matrix,
        'summary': {
            'six_actor_source_parity_confirmed': len(actor_rows) == 6,
            'source_to_diagnostic_compiled_tier_sequences_match': sequence_matches,
            'compiled_group_counts_observed': sorted(group_set),
            'actor_count': len(actor_rows), 'consumer_reference_edge_count': len(all_refs),
            **conclusion,
        },
        'limits': ['The 0.5.2 diagnostic SGA is only a compiled-record probe, not a 0.6.0 release baseline.',
                   'This matrix is static tuning evidence; no Content Editor build, Garrison cook, native match, or runtime visual test was run.',
                   'Rattan armor stat / SCAR behavior is preserved by scope and not changed or runtime-tested here.'],
    }
    json_path = owned(OUT_DIR / 'compatibility-matrix.json')
    write(json_path, result)
    md_path = owned(OUT_DIR / 'compatibility-matrix.md')
    lines = [
        '# Rattan tier and attachment compatibility matrix', '',
        f"Status: `{result['status']}`. Six actors source-match the compiled 0.5.2 diagnostic records under the unchanged 314-file source parity receipt.", '',
        '| Actor | Base tier attachments | Campaign tier attachments | Groups | Source list override | Source/compiled match |',
        '|---|---|---|---:|---|---|',
    ]
    for row in actor_rows:
        def refs(variant):
            group_list = row['source_tier_ext'].get(variant, {}).get('groups', [])
            return ', '.join(t['attachments'].split('\\')[-1] for group in group_list for t in group['tiers']) or '—'
        compiled_base = row['compiled_tier_ext'].get('default', {}).get('groups', [])
        actor_label = row['actor_id'].rsplit('\\', 1)[-1]
        lines.append(f"| `{actor_label}` | {refs('base')} | {refs('campaign')} | {len(compiled_base)} | {row['local_source_declares_list_override']} | {row['normalized_source_vs_compiled_tiers_equal']} |")
    lines.extend(['', '## Finding', '', conclusion['source_list_override'], '', conclusion['attachment_selection'], '', conclusion['recommendation_for_art_scope'], '',
                  '## Stock example', '', 'The pinned official Chinese Villager I compiled record has one `tier_group` and four ordered attachment references (tier1–tier4) in default, cordoba, and campaign variants. This illustrates a tier progression; it does not demonstrate that parallel groups compose.', '',
                  '## Static consumer references', '', f"Scanned frozen instance XML for six tier actors, the discounted handcannon squad, and both similar rattan upgrade IDs; recorded {len(all_refs)} inbound reference edges in the JSON ledger.", '',
                  'The real ranged-building upgrade reference is `upgrade\\vietnam\\vn_ratten_shield_vit`; `upgrade\\vietnam\\vn_upgrade_rattan_shields_vit` is a separate lookalike. No source, SCAR, or gameplay behavior was changed.', '',
                  '## Limits', '', '- Additional `tier_group` runtime evaluation and attachment-list overlay behavior remain unresolved.', '- No cook, Content Editor build, or native match qualification was performed.', '- The existing +1 armor and `rattan_armor.scar` behavior remains an explicit preservation constraint.'])
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'json={json_path.as_posix()}')
    print(f'markdown={md_path.as_posix()}')
    print(f'actors={len(actor_rows)} source_compiled_match={sequence_matches} reference_edges={len(all_refs)}')


if __name__ == '__main__':
    main()

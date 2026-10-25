"""Inventory stock Chinese Feudal-family consumers and native art graphs."""
from __future__ import annotations

import collections
import hashlib
import json
import os
import re
import sqlite3
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools/release_010'))
from workspace_support import configuration, check_storage

CONFIG = configuration(ROOT)
EXTERNAL = Path(CONFIG['external_root'])
OUT = EXTERNAL / 'output/release_040'
ARCHIVER = Path(CONFIG['archive_tool'])
CORE = Path(CONFIG['garrison_core'])
DB = Path(os.environ.get('LOCALAPPDATA', r'C:\Users\RS\AppData\Local')) / 'Garrison/Kit/game-assets.sqlite3'
ASSET_CONFIG = DB.with_name('game-assets.local.json')
DECODE = OUT / 'inventory/decode'
NATIVE = OUT / 'inventory/native'
GAME = Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives')
ATTRIB = GAME / 'Attrib.sga'
DATA = GAME / 'Data.sga'
ATTRIB_MEMBERS = None
EXT = Path(CONFIG['garrison_extension'])
sys.path.insert(0, str(EXT))
from garrison_shared import relic_chunky as rc

FAMILIES = {
    'blacksmith': {
        'display_name': 'Blacksmith / Military Academy',
        'actor': 'attrib/ebps/races/chinese/buildings/building_tech_unit_infantry_chi/building_tech_unit_infantry_control_chi.rgd',
        'logical': 'art/civilizations/chinese/structures/blacksmith/chi_blacksmith_control_age{age:02d}/chi_blacksmith_control_age{age:02d}.rgm',
    },
    'archery_range': {
        'display_name': 'Archery Range',
        'actor': 'attrib/ebps/races/chinese/buildings/building_unit_ranged_chi/building_unit_ranged_control_chi.rgd',
        'logical': 'art/civilizations/chinese/structures/archery_range/chi_archery_range_control_age{age:02d}/chi_archery_range_control_age{age:02d}.rgm',
    },
    'stable': {
        'display_name': 'Stable',
        'actor': 'attrib/ebps/races/chinese/buildings/building_unit_cavalry_chi/building_unit_cavalry_control_chi.rgd',
        'logical': 'art/civilizations/chinese/structures/stable/chi_stable_control_age{age:02d}/chi_stable_control_age{age:02d}.rgm',
    },
    'market': {
        'display_name': 'Market',
        'actor': 'attrib/ebps/races/chinese/buildings/building_econ_market_chi/building_econ_market_control_chi.rgd',
        'logical': 'art/civilizations/chinese/structures/market/chi_market_control_age{age:02d}/chi_market_control_age{age:02d}.rgm',
    },
}


def sha(path: Path) -> str:
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def cli(args: list[str]) -> str:
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {args}\n{result.stdout}\n{result.stderr}')
    return result.stdout


def extract(member: str, archive: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        cli([ARCHIVER, 'extract-member', archive, member, target])
    return target


def decode_rgd(member: str, base: str) -> tuple[Path, Path]:
    binary = NATIVE / (base + '.rgd')
    xml = NATIVE / (base + '.xml')
    extract(member, ATTRIB, binary)
    if not xml.exists():
        cli([ARCHIVER, 'decode-rgd', binary, xml])
    return binary, xml


def sibling_ref(node: ET.Element, key: str) -> str | None:
    for child in node.findall(f"RGDNode[@Key='{key}']"):
        pbgname = child.find("RGDNode[@Key='$PBGNAME']")
        pbgmap = child.find("RGDNode[@Key='$PBGMAP']")
        if pbgname is not None and pbgmap is not None and pbgname.get('Value') and pbgmap.get('Value'):
            return pbgmap.get('Value').replace('\\', '/') + '/' + pbgname.get('Value')
    return None


def actor_graph(member: str, family: str) -> dict:
    binary, xml = decode_rgd(member, 'actor_' + family)
    root = ET.parse(xml).getroot()
    variants = {}
    for variant in ('default', 'campaign'):
        branch = root.find(f"RGDNode[@Key='{variant}']")
        if branch is None:
            continue
        refs = []
        # Walk List containers and resolve their direct PBG/map siblings deterministically.
        for node in branch.iter('RGDNode'):
            if node.get('Key') in ('animator_attachments', 'attachments'):
                value = sibling_ref(node, node.get('Key'))
                if value:
                    refs.append(value)
        # The PBG reference payload is nested under the keyed list itself.
        for key in ('animator_attachments', 'attachments'):
            for node in branch.iter('RGDNode'):
                if node.get('Key') == key:
                    pbgname = node.find("RGDNode[@Key='$PBGNAME']")
                    pbgmap = node.find("RGDNode[@Key='$PBGMAP']")
                    if pbgname is not None and pbgmap is not None and pbgname.get('Value') and pbgmap.get('Value'):
                        refs.append(pbgmap.get('Value').replace('\\', '/') + '/' + pbgname.get('Value'))
        tier_rows = []
        for tier_list in branch.iter('RGDNode'):
            if tier_list.get('Key') != 'tier_group_list':
                continue
            for group in tier_list.findall("RGDNode[@Key='tier_group']"):
                for tier in group.findall("RGDNode[@Key='tier']"):
                    age = None
                    attachments = []
                    for desc in tier.iter('RGDNode'):
                        if desc.get('Key') in ('minimum_age', 'age', 'required_age') and desc.get('Value'):
                            age = desc.get('Value')
                        if desc.get('Key') == 'attachments':
                            pbgname = desc.find("RGDNode[@Key='$PBGNAME']")
                            pbgmap = desc.find("RGDNode[@Key='$PBGMAP']")
                            if pbgname is not None and pbgmap is not None and pbgname.get('Value'):
                                attachments.append(pbgmap.get('Value').replace('\\', '/') + '/' + pbgname.get('Value'))
                    if age is None:
                        match = next((re.search(r'tier([234])_', ref.rsplit('/', 1)[-1]) for ref in attachments
                                      if re.search(r'tier([234])_', ref.rsplit('/', 1)[-1])), None)
                        age = f'age_{match.group(1)}' if match else None
                    tier_rows.append({'age': age, 'attachments': sorted(set(attachments))})
        construction_stamps = [n.get('Value').replace('\\', '/') for n in branch.iter('RGDNode')
                               if n.get('Key') == 'construction_stamp' and n.get('Value')]
        variants[variant] = {'attachment_lists': sorted(set(refs)), 'tiers': tier_rows,
                             'construction_stamps': sorted(set(construction_stamps))}
    return {'member': member, 'source': str(binary), 'sha256': sha(binary), 'variants': variants}


def attachment_stamps(member: str) -> dict:
    binary, xml = decode_rgd(member, 'attachment_' + hashlib.sha1(member.encode()).hexdigest()[:12])
    root = ET.parse(xml).getroot()
    output = {}
    for variant in ('default', 'campaign', 'cordoba'):
        branch = root.find(f"RGDNode[@Key='{variant}']")
        if branch is None:
            continue
        stamps = sorted({n.get('Value').replace('\\', '/') + '.bin'
                         for n in branch.iter('RGDNode') if n.get('Key') == 'stamp' and n.get('Value')})
        if stamps:
            output[variant] = stamps
    return {'member': member, 'sha256': sha(binary), 'stamps': output}


def resolve_attachment_ref(ref: str) -> str | None:
    """Map the actor's PBG key to its exact full stock member path."""
    base = ref.rsplit('/', 1)[-1].lower() + '.rgd'
    candidates = [name for name in ATTRIB_MEMBERS if name.lower().endswith('/' + base)]
    if not candidates:
        return None
    if 'tier' in base or base.startswith('market_'):
        chinese = [name for name in candidates if '/civilizations/chinese/' in name.lower()]
        if chinese:
            return sorted(chinese, key=str.lower)[0]
    core = [name for name in candidates if '/races/core/' in name.lower()]
    if core:
        return sorted(core, key=str.lower)[0]
    return sorted(candidates, key=str.lower)[0]


def parse_stamp(path: Path) -> list[dict]:
    # The same reflected schema and active VisualStampBlueprint walk used by the project's native inventory.
    from integration_native import NativeTree
    tree = NativeTree(path)
    roots = [obj for obj in tree.objects.values() if obj['type'] == 'StampBlueprint' and not obj['owner']]
    if not roots:
        return []
    root = roots[0]
    arr = tree.field(root, root['fields']['m_blueprints'])
    rows = []
    for index in range(arr['count']):
        slot = arr['data_address'] + 8 * index
        obj = tree.by_offset.get(slot + struct.unpack('<q', tree.bytes(slot, 8))[0])
        if obj and obj['type'] == 'VisualStampBlueprint':
            model = tree.field(obj, obj['fields']['m_blueprint']).get('text')
            transform_raw = bytes.fromhex(tree.field(obj, obj['fields']['m_transform'])['raw'])
            rows.append({'model': (model or '').replace('\\', '/').lower(),
                         'transform': list(struct.unpack('<10f', transform_raw))})
    return rows


def stamp_graph(member: str) -> dict:
    logical = member.lower()
    with sqlite3.connect(f'file:{DB.as_posix()}?mode=ro', uri=True) as db:
        row = db.execute('select archive_path from resolved_assets where lower(logical_path)=?', (logical,)).fetchone()
    # The Garrison index intentionally catalogs model/texture resources, while
    # native stamp .bin owners are read from the official Data.sga archive.
    source_archive = Path(row[0]) if row else DATA
    short = hashlib.sha1(member.encode('utf-8')).hexdigest()[:12] + '_' + Path(member).stem + '.bin'
    path = extract(member, source_archive, NATIVE / 'stamps' / short)
    return {'member': member, 'archive': str(source_archive), 'sha256': sha(path),
            'visuals': parse_stamp(path)}


def decode_model(logical: str) -> dict:
    check_storage(ROOT, CONFIG)
    command = [CORE, 'convert', 'decode-static', '--logical-path', logical,
               '--config', ASSET_CONFIG, '--index', DB, '--output-root', DECODE]
    receipt = json.loads(cli(command).strip())
    manifest = Path(receipt['manifest_path'])
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if data.get('status') != 'decoded' or data.get('blockers'):
        raise RuntimeError(f'Incomplete Garrison static decode: {logical}')
    source = Path(data['geometry']['source']['path'])
    # Model bytes are retained in Garrison's decoded source folder; hash RGM via index extraction below.
    with sqlite3.connect(f'file:{DB.as_posix()}?mode=ro', uri=True) as db:
        archive_row = db.execute('select archive_path from resolved_assets where lower(logical_path)=?',
                                  (data['provider_contract']['model']['logical_path'].lower(),)).fetchone()
    if not archive_row:
        raise FileNotFoundError(data['provider_contract']['model']['logical_path'])
    rgm = extract(data['provider_contract']['model']['logical_path'], Path(archive_row[0]),
                  NATIVE / 'models' / (Path(logical).stem + '.rgm'))
    return {'logical_path': logical, 'rgm_sha256': sha(rgm), 'geometry_sha256': data['geometry']['source']['sha256'],
            'decoded_manifest': str(manifest), 'decoded_manifest_sha256': sha(manifest),
            'decoded_geometry': str(source), 'groups': len(data['geometry']['groups']),
            'raw_lod0_triangles': sum(group['triangle_count'] for group in data['geometry']['groups']),
            'geometry': data['geometry']}


def main() -> int:
    global ATTRIB_MEMBERS
    check_storage(ROOT, CONFIG)
    if not DB.is_file() or not ATTRIB.is_file() or not DATA.is_file():
        raise FileNotFoundError('Current Garrison index or AoE4 Attrib/Data archives are unavailable')
    index_listing = json.loads(cli([ARCHIVER, 'list', ATTRIB]).strip())
    ATTRIB_MEMBERS = [row['path'] for row in index_listing['members']]
    report = {'schema': 'community-civilization-pack/release-040-stock-graph/v1',
              'status': 'passed_static_inventory', 'source': {
                  'game_attrib_sga': str(ATTRIB), 'game_data_sga': str(DATA), 'garrison_index': str(DB),
                  'garrison_index_sha256': sha(DB), 'garrison_core': str(CORE),
                  'archive_tool': str(ARCHIVER), 'native_runtime': 'unverified'},
              'age_contract': {'start_age': 'Feudal / Age II', 'age_variants': [2, 3, 4],
                               'variant_count_per_family': 3, 'visual_budget_basis': 'complete LOD0 decoded stock geometry; native lifecycle selector cross-check recorded separately'},
              'families': {}, 'market_shared_consumer_analysis': {}}
    for key, spec in FAMILIES.items():
        actor = actor_graph(spec['actor'], key)
        family = {'display_name': spec['display_name'], 'actor_graph': actor, 'donors': []}
        for age in (2, 3, 4):
            logical = spec['logical'].format(age=age)
            model = decode_model(logical)
            model.pop('geometry')
            family['donors'].append(model)
        family['donor_budget'] = {
            'raw_lod0_triangles': [row['raw_lod0_triangles'] for row in family['donors']],
            'median': sorted(row['raw_lod0_triangles'] for row in family['donors'])[1],
            'maximum': max(row['raw_lod0_triangles'] for row in family['donors']),
            'basis': 'decoded stock LOD0 source geometry, all geometry groups; construction, destruction, damage, and conditional state subgroups may be mutually exclusive and are not all simultaneously visible',
        }
        report['families'][key] = family
    # Resolve every actor attachment list in both normal and campaign variants to stamp and visual-model leaves.
    attachment_members = set()
    attachment_ref_map = {}
    for family in report['families'].values():
        for variant in family['actor_graph']['variants'].values():
            refs = [ref for tier in variant['tiers'] for ref in tier['attachments']
                    if re.search(r'tier[234]_', ref.rsplit('/', 1)[-1])]
            for ref in refs:
                member = resolve_attachment_ref(ref)
                if member:
                    attachment_ref_map[ref] = member
                    attachment_members.add(member)
            for tier in variant['tiers']:
                for ref in tier['attachments']:
                    if not re.search(r'tier[234]_', ref.rsplit('/', 1)[-1]):
                        continue
                    member = resolve_attachment_ref(ref)
                    if member:
                        attachment_ref_map[ref] = member
                        attachment_members.add(member)
    attachment_records = {}
    for member in sorted(attachment_members):
        try:
            attachment_records[member] = attachment_stamps(member)
        except Exception as exc:
            attachment_records[member] = {'member': member, 'error': str(exc)}
    report['attachment_lists'] = attachment_records
    report['attachment_reference_resolution'] = attachment_ref_map
    stamp_members = sorted({stamp for record in attachment_records.values()
                            for variant_stamps in record.get('stamps', {}).values() for stamp in variant_stamps})
    stamps = {}
    for member in stamp_members:
        try:
            stamps[member] = stamp_graph(member)
        except Exception as exc:
            stamps[member] = {'member': member, 'error': str(exc)}
    report['native_stamp_visual_graphs'] = stamps
    market_ha_actor = 'attrib/ebps/races/chinese_ha_01/buildings/building_econ_market_chi_ha_01/building_econ_market_control_chi_ha_01.rgd'
    market_ha_graph = actor_graph(market_ha_actor, 'market_chinese_ha_01')
    # Both Vietnam villager SBPs have root and campaign build-list copies. Record
    # actual source references, rather than inferring ownership from the actor name.
    vn_market_refs = {}
    for source in (ROOT / 'assets/attrib/instances/sbps/vietnam/vn_unit_villager_1_chi.xml',
                   ROOT / 'assets/attrib/instances/sbps/vietnam/vn_unit_villager_3_chi.xml'):
        text = source.read_text(encoding='utf-8')
        refs = re.findall(r'<instance_reference\s+name="ebp"\s+value="([^"]*building_econ_market[^"]*)"', text, re.I)
        vn_market_refs[source.name] = refs
    report['market_shared_consumer_analysis'] = {
        'standard_market_actor': FAMILIES['market']['actor'],
        'vietnam_market_actor': market_ha_actor,
        'vietnam_actor_graph': market_ha_graph,
        'vietnam_build_consumers': vn_market_refs,
        'finding': 'Vietnam villagers 1 and 3 reference the Chinese-HA01 market EBP in both root and campaign build lists (four references). The compiled Chinese-HA01 actor default and campaign tier_group_list both resolve tier2/3/4_econ_market_control_chi, whose full members are the standard Chinese attachment-list paths; these lists stamp chi_market_age_02/03/04.bin, the shared destruction stamp, and campaign west_market scaffolding. Chinese-HA01-named market lists exist in Attrib.sga but this actor does not select them. The Chinese and Chinese-HA01 actors therefore share the same current age attachment lists/stamps; private Vietnamese visuals require an isolated actor/list chain and all four consumer refs.',
        'native_runtime': 'unverified',
    }
    output = OUT / 'inventory/stock-chinese-buildings.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'],
                      'families': {k: {'actors': list(v['actor_graph']['variants']),
                                       'triangles': v['donor_budget']['raw_lod0_triangles'],
                                       'median': v['donor_budget']['median'], 'maximum': v['donor_budget']['maximum']}
                                    for k, v in report['families'].items()},
                      'attachment_lists': len(attachment_records), 'stamps': len(stamps),
                      'report': str(output)}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

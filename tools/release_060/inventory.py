"""Reproducible, read-only land-unit consumer inventory for release 0.6.0.

The inventory follows local XML references, preserves each XPath, and selectively
decodes hash-pinned official RGD through Garrison's archive tool for native
inheritance evidence. It does not establish runtime eligibility.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import subprocess
import sys
import json
from collections import defaultdict, deque
from pathlib import Path
from xml.etree import ElementTree as ET

from common import ARCH, CFG, OUT, STAGING, guard, owned, read, sha, write

DEFAULT_SOURCE = STAGING / 'preparation-source' / 'assets'
ARMY_ID = r'army\vietnam\vn_normal_chinese'
ARMY_FILE = Path('attrib/instances/army/vietnam/vn_normal_chinese.xml')
LOCAL_MOD = 'b7fcea91257b408fb9e8ae4d8bc402e1'
OFFICIAL_ATTRIB = Path(CFG['content_editor']).parent / 'cardinal' / 'archives' / 'Attrib.sga'
ARCHIVER = Path(CFG['archive_tool'])

REF_TAGS = {'instance_reference', 'template_reference'}
VARIANT_NAMES = {'campaign', 'normal', 'xp1', 'xp2', 'xp3', 'expansion1', 'expansion2'}
UNIT_CATEGORIES = {'sbps', 'ebps'}
OFFICIAL_RGD_CATEGORIES = {'sbps', 'ebps', 'weapon', 'projectile', 'upgrade', 'abilities',
                           'attachments', 'attachment_lists', 'animator', 'animation',
                           'racebps', 'statemodel_schema'}
NON_UNIT_WORDS = (
    'building', 'projectile', 'trap', 'wall', 'foundation', 'ruin', 'debris',
    'resource', 'tree', 'fish', 'ship', 'boat', 'water', 'animal', 'sheep',
    'deer', 'boar', 'wolf', 'gaia_herdable',
)


def key(value: str) -> str:
    return re.sub(r'[/\\]+', r'\\', value.strip().strip('\\')).lower()


def local_id(category: str, relative: Path) -> str:
    return key(category + '\\' + relative.with_suffix('').as_posix())


def xname(el: ET.Element) -> str:
    return el.attrib.get('name', '')


def xpath_part(el: ET.Element) -> str:
    name = xname(el)
    return el.tag + (f"[@name='{name}']" if name else '')


def iter_with_paths(root: ET.Element, path: str = ''):
    here = (path + '/' + xpath_part(root)) if path else '/' + xpath_part(root)
    yield root, here
    for child in root:
        yield from iter_with_paths(child, here)


def variant_for(path: str) -> str:
    match = re.search(r"/variant\[@name='([^']+)'\]", path, re.I)
    return match.group(1) if match else 'base'


def spawn_item_context(root: ET.Element, wanted: ET.Element):
    parents = {child: parent for parent in root.iter() for child in parent}
    cursor = wanted
    while cursor in parents and not (cursor.tag == 'group' and xname(cursor) == 'spawn_item'):
        cursor = parents[cursor]
    if cursor.tag != 'group' or xname(cursor) != 'spawn_item':
        return {}
    values = {}
    for el in cursor.iter():
        name = xname(el)
        if name and el is not cursor and el.tag in {'bool', 'int', 'float', 'enum', 'locstring'}:
            if 'value' in el.attrib:
                values[name] = el.attrib['value']
    values['reference_requirements'] = [
        {'tag': el.tag, 'name': el.attrib.get('name', ''),
         'value': el.attrib.get('value', ''), 'mod': el.attrib.get('mod', ''),
         'xpath': xp}
        for el, xp in iter_with_paths(cursor)
        if el is not cursor and el.tag in REF_TAGS and el.attrib.get('value')
    ]
    return values


def construction_item_context(root: ET.Element, wanted: ET.Element):
    parents = {child: parent for parent in root.iter() for child in parent}
    cursor = wanted
    while cursor in parents and not (cursor.tag == 'group' and xname(cursor) == 'construction_item'):
        cursor = parents[cursor]
    if cursor.tag != 'group' or xname(cursor) != 'construction_item':
        return {}
    return {
        'values': {xname(el): el.attrib.get('value', '') for el in cursor.iter()
                   if el is not cursor and xname(el) and 'value' in el.attrib},
        'references': [{'tag': el.tag, 'name': el.attrib.get('name', ''),
                        'value': el.attrib.get('value', ''), 'mod': el.attrib.get('mod', ''),
                        'xpath': xp}
                       for el, xp in iter_with_paths(cursor)
                       if el is not cursor and el.tag in REF_TAGS and el.attrib.get('value')],
    }


def parse_index(attrib_root: Path):
    docs, parse_errors, file_hashes = {}, [], {}
    instances = attrib_root / 'instances'
    for category_dir in sorted(p for p in instances.iterdir() if p.is_dir()):
        category = category_dir.name.lower()
        for path in sorted(category_dir.rglob('*.xml')):
            rel = path.relative_to(instances)
            ident = local_id(category, path.relative_to(category_dir))
            try:
                before = path.stat()
                digest = sha(path)
                root = ET.parse(path).getroot()
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise RuntimeError('source changed while reading')
                file_hashes[path.relative_to(attrib_root.parent.parent).as_posix()] = digest
                docs[ident] = {'id': ident, 'category': category, 'path': path,
                               'relative': path.relative_to(attrib_root.parent.parent).as_posix(),
                               'root': root, 'hash': digest}
            except Exception as exc:  # keep malformed source visible in the report
                parse_errors.append({'file': path.as_posix(), 'error': str(exc)})
    return docs, parse_errors, file_hashes


def ref_edges(doc):
    edges = []
    for el, xpath in iter_with_paths(doc['root']):
        if el.tag not in REF_TAGS:
            continue
        value = el.attrib.get('value', '').strip()
        if not value:
            continue
        value = key(value)
        category = value.split('\\', 1)[0]
        if category not in {'ebps', 'sbps', 'weapon', 'upgrade', 'abilities', 'army',
                            'racebps', 'projectile', 'squad_type', 'statemodel_schema',
                            'attachments', 'attachment_lists', 'animator', 'animation',
                            'actions', 'options'}:
            continue
        edges.append({'source_id': doc['id'], 'source_file': doc['relative'],
                      'xpath': xpath, 'tag': el.tag, 'name': el.attrib.get('name', ''),
                      'target': value, 'target_category': category,
                      'mod': el.attrib.get('mod', ''), 'variant': variant_for(xpath),
                      'item_id': el.attrib.get('List.ItemID', ''),
                      'list_action': el.attrib.get('List.ListAction', ''),
                      'status': ''})
    return edges


def refs_in_list(doc, list_name: str, ref_name: str | None = None):
    found = []
    for el, xpath in iter_with_paths(doc['root']):
        if el.tag not in REF_TAGS or not el.attrib.get('value'):
            continue
        if el.attrib.get('name') != ref_name and ref_name is not None:
            continue
        if f"list[@name='{list_name}']" not in xpath:
            continue
        found.append((el, xpath))
    return found


def resolve_status(edge, docs):
    edge['status'] = 'resolved_local' if edge['target'] in docs else 'external_or_unresolved'
    if edge['mod'] and key(edge['mod']) == LOCAL_MOD:
        edge['reference_scope'] = 'this_pack'
    elif edge['status'] == 'resolved_local':
        edge['reference_scope'] = 'local_without_mod_field'
    else:
        edge['reference_scope'] = 'native_or_other_external'


def unitish(identifier: str) -> bool:
    base = identifier.rsplit('\\', 1)[-1]
    return not any(word in base for word in NON_UNIT_WORDS)


def actor_kind(doc):
    if doc['category'] == 'sbps':
        return 'squad'
    if doc['category'] == 'ebps':
        name = doc['id'].rsplit('\\', 1)[-1]
        return 'entity'
    return doc['category']


def is_building_actor(identifier: str, edges) -> bool:
    name = identifier.rsplit('\\', 1)[-1]
    return ('\\buildings\\' in f'\\{identifier}\\' or name.startswith('building_')
            or '\\vn_building_' in f'\\{identifier}\\'
            or any(e['name'] == 'parent_pbg' and '\\buildings\\' in f"\\{e['target']}\\"
                   for e in edges))


def is_unit_actor(identifier: str, doc, edges) -> bool:
    if doc['category'] == 'sbps':
        return unitish(identifier)
    if doc['category'] != 'ebps' or not unitish(identifier):
        return False
    parents = [e['target'] for e in edges if e['name'] == 'parent_pbg']
    if any('\\buildings\\' in f'\\{parent}\\' for parent in parents):
        return False
    if any('\\units\\' in f'\\{parent}\\' for parent in parents):
        return True
    return identifier.rsplit('\\', 1)[-1].startswith('vn_unit_')


def rattan_evidence(source_root: Path):
    scar_path = source_root / 'scar' / 'vietnam' / 'rattan_armor.scar'
    upgrade_path = source_root / 'attrib' / 'instances' / 'upgrade' / 'vietnam' / 'vn_ratten_shield_vit.xml'
    lookalike_path = source_root / 'attrib' / 'instances' / 'upgrade' / 'vietnam' / 'vn_upgrade_rattan_shields_vit.xml'
    scar = scar_path.read_text(encoding='utf-8-sig') if scar_path.exists() else ''
    roster_match = re.search(r'local\s+roster\s*=\s*\{(.*?)\}', scar, re.S)
    roster = re.findall(r'"([^"]+)"', roster_match.group(1)) if roster_match else []
    actual = bool(re.search(r'BP_GetUpgradeBlueprint\([^\n]*:vn_ratten_shield_vit', scar))
    lookalike_used = bool(re.search(r'BP_GetUpgradeBlueprint\([^\n]*:vn_upgrade_rattan_shields_vit', scar))
    expected = {
        'vn_unit_archer_2_vit', 'vn_unit_archer_3_vit', 'vn_unit_archer_4_vit',
        'vn_unit_crossbowman_3_chi', 'vn_unit_crossbowman_4_chi', 'vn_unit_handcannon_4_chi'}
    return {
        'source_file': scar_path.as_posix(), 'source_sha256': sha(scar_path) if scar_path.exists() else None,
        'actual_upgrade': 'upgrade\\vietnam\\vn_ratten_shield_vit',
        'actual_upgrade_xml_present': upgrade_path.exists(),
        'separate_lookalike_upgrade': 'upgrade\\vietnam\\vn_upgrade_rattan_shields_vit',
        'lookalike_xml_present': lookalike_path.exists(),
        'scar_uses_actual_upgrade': actual, 'scar_uses_lookalike_upgrade': lookalike_used,
        'scar_roster': roster, 'scar_roster_matches_plan': set(roster) == expected,
        'elephant_excluded': not any('elephant' in name for name in roster),
    }


def official_member_index():
    """Read the installed official Attrib SGA member index without extraction."""
    if not OFFICIAL_ATTRIB.is_file() or not ARCHIVER.is_file():
        return {'status': 'unavailable', 'reason': 'official Attrib.sga or configured sga-archiver is missing',
                'archive': OFFICIAL_ATTRIB.as_posix(), 'members': {}}
    result = subprocess.run([str(ARCHIVER), 'list', str(OFFICIAL_ATTRIB)],
                            check=True, capture_output=True, text=True, timeout=180)
    payload = json.loads(result.stdout)
    members = {item['path'].lower(): item for item in payload.get('members', [])}
    return {'status': 'read_only_indexed', 'archive': OFFICIAL_ATTRIB.as_posix(),
            'archive_sha256': sha(OFFICIAL_ATTRIB), 'archive_version': payload.get('archive', {}).get('version'),
            'archive_member_count': payload.get('archive', {}).get('file_count'),
            'index_member_count': len(members), 'members': members}


def official_member_for(identifier: str, member_index):
    member_path = 'attrib/' + key(identifier).replace('\\', '/') + '.rgd'
    member = member_index.get('members', {}).get(member_path.lower())
    return {'expected_member_path': member_path, 'present_in_official_attrib': member is not None,
            'member_size': member.get('size') if member else None,
            'member_sha1_verified_by_archive_metadata': member.get('verification') if member else None}


def official_closure_seed_members(inv):
    members = set()
    relevant = []
    for edge in inv['consumer_edges']:
        if edge['status'] == 'resolved_local' or edge['target_category'] not in OFFICIAL_RGD_CATEGORIES:
            continue
        native = edge.get('official_archive', {})
        path = native.get('expected_member_path')
        if path and native.get('present_in_official_attrib'):
            members.add(path.replace('\\', '/'))
            relevant.append(edge)
    # Candidate-only Chinese Imperial Official: it is present in the current
    # native archive but has no source-reachable Vietnam production route.
    members.add('attrib/sbps/races/chinese/unit_official_1_chi.rgd')
    return sorted(members), relevant


def _rgd_parent_targets(xml_path: Path, source_member: str, member_index):
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        return [], [{'source_member': source_member, 'error': str(exc)}]
    resolved, unresolved = [], []
    by_path = member_index['members']
    for node in root.iter('RGDNode'):
        if node.attrib.get('Key') != 'parent_pbg' or node.attrib.get('Type') != 'List':
            continue
        values = {child.attrib.get('Key'): child.attrib.get('Value', '')
                  for child in node.findall('./RGDNode')}
        pbg, category = values.get('$PBGNAME', '').strip(), values.get('$PBGMAP', '').strip().lower()
        if not pbg or not category:
            continue
        # ``$PBGMAP`` is a native map name, not always a filesystem category.
        # Attachment-list inheritance uses the shared core civilization map;
        # the direct archive path therefore has an extra
        # ``civilizations/core/units`` segment.
        if category == 'attachments\\attachment_lists':
            source_dir = source_member.lower().rsplit('/', 1)[0]
            sibling_candidates = [path for path in by_path if path.rsplit('/', 1)[0] == source_dir
                                  and path.rsplit('/', 1)[-1].lower().removesuffix('.rgd')
                                  in {pbg.lower(), *(pbg.lower() + '_' + suffix
                                                       for suffix in ('chi', 'chi_ha_01', 'abb', 'abb_ha_01',
                                                                      'byz', 'eng', 'fre', 'hre', 'jpn', 'mal',
                                                                      'mon', 'ott', 'rus', 'sul', 'del'))}]
            relative = source_member.lower().split('/attachment_lists/', 1)[-1]
            parts = relative.split('/')
            core_paths = []
            if len(parts) >= 3 and parts[0] == 'civilizations':
                core_paths.append('attrib/attachments/attachment_lists/civilizations/core/'
                                  + '/'.join(parts[2:-1]) + f'/{pbg.lower()}.rgd')
            if len(parts) >= 4 and parts[0] == 'races':
                core_paths.append('attrib/attachments/attachment_lists/races/core/'
                                  + '/'.join(parts[2:-1]) + f'/{pbg.lower()}.rgd')
            candidates = (sibling_candidates if sibling_candidates else
                          [path for path in core_paths if path in by_path])
        else:
            prefix = f'attrib/{category}/'
            suffix = '/' + pbg.lower() + '.rgd'
            candidates = [p for p in by_path if p.startswith(prefix) and p.endswith(suffix)]
        source_parts = source_member.lower().split('/')
        same_folder = [p for p in candidates if p.rsplit('/', 1)[0] == '/'.join(source_parts[:-1])]
        core_folder = [p for p in candidates if '/races/core/' in p]
        chosen = same_folder if len(same_folder) == 1 else core_folder if len(core_folder) == 1 else candidates
        fact = {'pbg_name': pbg, 'pbg_map': category, 'candidate_members': sorted(candidates)}
        if len(chosen) == 1:
            resolved.append({**fact, 'member': chosen[0]})
        else:
            unresolved.append({**fact, 'reason': 'no exact matching official member' if not chosen else 'ambiguous PBG name in official archive'})
    return resolved, unresolved


def _rgd_squad_loadout_targets(xml_path: Path, source_member: str, member_index):
    """Resolve squad loadout body EBPs as actor links, separate from inheritance."""
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        return [], [{'source_member': source_member, 'error': str(exc)}]
    by_path = member_index['members']
    source_lower = source_member.lower()
    race = source_lower.split('/races/', 1)[1].split('/', 1)[0] if '/races/' in source_lower else ''
    resolved, unresolved = [], []
    for ext in root.iter('RGDNode'):
        if ext.attrib.get('Key') != 'squad_loadout_ext' or ext.attrib.get('Type') != 'List':
            continue
        for typ in ext.iter('RGDNode'):
            if typ.attrib.get('Key') != 'type' or typ.attrib.get('Type') != 'List':
                continue
            values = {child.attrib.get('Key'): child.attrib.get('Value', '')
                      for child in typ.findall('./RGDNode')}
            pbg, category = values.get('$PBGNAME', '').strip(), values.get('$PBGMAP', '').strip().lower()
            if not pbg or category != 'ebps':
                continue
            preferred = f'attrib/ebps/races/{race}/units/{pbg.lower()}.rgd' if race else ''
            candidates = ([preferred] if preferred in by_path else
                          [path for path in by_path if path.startswith('attrib/ebps/')
                           and path.endswith('/' + pbg.lower() + '.rgd')])
            fact = {'pbg_name': pbg, 'pbg_map': category, 'candidate_members': candidates,
                    'relation': 'squad_loadout_body'}
            if len(candidates) == 1:
                resolved.append({**fact, 'member': candidates[0]})
            else:
                unresolved.append({**fact, 'reason': 'no exact matching official member' if not candidates
                                   else 'ambiguous PBG name in official archive'})
    return resolved, unresolved


def _rgd_entity_visual_links(xml_path: Path, source_member: str, member_index):
    """Resolve EBP animator-attachment lists and hardpoint weapon/list refs."""
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        return [], [{'source_member': source_member, 'error': str(exc)}]
    by_path = member_index['members']
    source_lower = source_member.lower()
    race = source_lower.split('/races/', 1)[1].split('/', 1)[0] if '/races/' in source_lower else ''
    links, unresolved = [], []
    default = root.find("./RGDNode[@Key='default']")
    if default is None:
        return links, unresolved
    for ext_name, link_name in (('entity_blueprint_ext', 'animator_attachments'),
                                ('combat_ext', 'hardpoints')):
        ext = default.find(f"./RGDNode[@Key='{ext_name}']")
        link_root = ext.find(f"./RGDNode[@Key='{link_name}']") if ext is not None else None
        if link_root is None:
            continue
        for node in link_root.iter('RGDNode'):
            if node.attrib.get('Type') != 'List':
                continue
            values = {child.attrib.get('Key'): child.attrib.get('Value', '')
                      for child in node.findall('./RGDNode')}
            pbg, category = values.get('$PBGNAME', '').strip(), values.get('$PBGMAP', '').strip().lower()
            if not pbg or not category:
                continue
            if category == 'attachments\\attachment_lists':
                prefix = 'attrib/attachments/attachment_lists/'
                candidates = [path for path in by_path if path.startswith(prefix)
                              and path.endswith('/' + pbg.lower() + '.rgd')]
                if race:
                    race_matches = [path for path in candidates
                                    if f'/races/{race}/' in path or f'/civilizations/{race}/' in path]
                    core_matches = [path for path in candidates if '/races/core/' in path
                                    or '/civilizations/core/' in path]
                    candidates = race_matches if len(race_matches) == 1 else core_matches if len(core_matches) == 1 else candidates
            else:
                prefix = f'attrib/{category}/'
                candidates = [path for path in by_path if path.startswith(prefix)
                              and path.endswith('/' + pbg.lower() + '.rgd')]
            related = {}
            for child in link_root.iter('RGDNode'):
                key_name, value = child.attrib.get('Key', ''), child.attrib.get('Value', '')
                if key_name in {'marker_name_parent', 'marker_name', 'x', 'y', 'z'} and value:
                    related.setdefault(key_name, value)
            fact = {'pbg_name': pbg, 'pbg_map': category,
                    'source_field': f'{ext_name}/{link_name}', 'candidate_members': sorted(candidates),
                    'socket_or_position': related}
            if len(candidates) == 1:
                links.append({**fact, 'member': candidates[0]})
            else:
                unresolved.append({**fact, 'reason': 'no exact matching official member' if not candidates
                                   else 'ambiguous PBG name in official archive'})
    return links, unresolved


def _native_spawn_item_rows(xml_path: Path, source_member: str, actor_id: str,
                            source_file: str, local_variant: str, member_index):
    """Read spawn items from one exact native parent RGD variant."""
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        return [], [{'source_member': source_member, 'error': str(exc)}]
    wanted = 'campaign' if local_variant.lower() == 'campaign' else 'default'
    variant_node = root.find(f"./RGDNode[@Key='{wanted}']")
    if variant_node is None and wanted == 'campaign':
        variant_node = root.find("./RGDNode[@Key='default']")
    if variant_node is None:
        return [], []
    rgd_paths = {}
    def add_paths(node, path=''):
        key_name = node.attrib.get('Key', '')
        base = f"RGDNode[@Key='{key_name}']" if key_name else 'RGDNode'
        here = f'{path}/{base}' if path else f'/{base}'
        rgd_paths[id(node)] = here
        occurrence = defaultdict(int)
        siblings = list(node)
        for child in siblings:
            child_key = child.attrib.get('Key', '')
            token = (child.tag, child_key)
            occurrence[token] += 1
            child_base = f"{child.tag}[@Key='{child_key}']" if child_key else child.tag
            if sum(1 for sib in siblings if sib.tag == child.tag and sib.attrib.get('Key', '') == child_key) > 1:
                child_base += f'[{occurrence[token]}]'
            add_paths(child, here + '/' + child_base)
    add_paths(root)
    spawn_lists = [node for node in variant_node.iter('RGDNode')
                   if node.attrib.get('Key') == 'spawn_items' and node.attrib.get('Type') == 'List']
    if not spawn_lists:
        return [], []
    rows, unresolved = [], []
    for spawn_list in spawn_lists:
        for item in spawn_list.iter('RGDNode'):
            if item.attrib.get('Key') != 'spawn_item' or item.attrib.get('Type') != 'List':
                continue
            pbg = {}
            for node in item.iter('RGDNode'):
                if node.attrib.get('Key') not in {'squad', 'entity'}:
                    continue
                vals = {child.attrib.get('Key'): child.attrib.get('Value', '')
                        for child in node.findall('./RGDNode')}
                if vals.get('$PBGNAME') and vals.get('$PBGMAP'):
                    pbg = vals
                    pbg['reference_name'] = node.attrib.get('Key')
                    break
            if not pbg:
                continue
            category = pbg['$PBGMAP'].replace('\\', '/').lower()
            name = pbg['$PBGNAME'].lower()
            candidates = [path for path in member_index['members']
                          if path.startswith(f'attrib/{category}/') and path.endswith('/' + name + '.rgd')]
            race = source_member.lower().split('/races/', 1)[1].split('/', 1)[0] if '/races/' in source_member.lower() else ''
            if race:
                race_candidates = [path for path in candidates if f'/races/{race}/' in path]
                if len(race_candidates) == 1:
                    candidates = race_candidates
            props = {node.attrib.get('Key'): node.attrib.get('Value', '')
                     for node in item.iter('RGDNode') if node.attrib.get('Value')}
            requirements = []
            for node in item.iter('RGDNode'):
                if node.attrib.get('Key') == '$REF' and node.attrib.get('Value', '').startswith('requirements'):
                    requirements.append(node.attrib.get('Value'))
            row = {'source_member': source_member, 'local_actor_id': actor_id,
                   'source_file': source_file, 'local_variant': local_variant,
                   'native_variant': wanted, 'native_spawn_item_reference': pbg,
                   'native_source_xpath': rgd_paths.get(id(item)),
                   'item_values': props, 'requirement_refs': sorted(set(requirements)),
                   'classification': 'native_parent_spawn_item_candidate',
                   'list_merge_semantics': 'Native parent list is exact. Local child list state is recorded separately; engine override/merge semantics, item gates, and runtime eligibility are unverified.'}
            if len(candidates) == 1:
                row['expected_member_path'] = candidates[0]
                row['target_id'] = candidates[0].removeprefix('attrib/').removesuffix('.rgd').replace('/', '\\')
                row['official_member_present'] = True
                row['land_scope'] = ('excluded_non_land' if any(token in row['target_id'].lower()
                    for token in ('\\ship', '\\boat', 'fishing_boat', 'unit_naval_', 'water', '\\fish'))
                    else 'land_candidate')
                rows.append(row)
            else:
                unresolved.append({**row, 'candidate_members': sorted(candidates),
                                   'reason': 'no exact official member' if not candidates else 'ambiguous exact official member'})
    return rows, unresolved


def _native_spawn_list_state(xml_path: Path, local_variant: str):
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError:
        return 'parse_error'
    wanted = 'campaign' if local_variant.lower() == 'campaign' else 'default'
    variant_node = root.find(f"./RGDNode[@Key='{wanted}']")
    if variant_node is None and wanted == 'campaign':
        variant_node = root.find("./RGDNode[@Key='default']")
    if variant_node is None:
        return 'variant_missing'
    lists = [node for node in variant_node.iter('RGDNode')
             if node.attrib.get('Key') == 'spawn_items' and node.attrib.get('Type') == 'List']
    if not lists:
        return 'absent_on_immediate_native_parent'
    count = sum(1 for node in lists for child in node.iter('RGDNode')
                if child.attrib.get('Key') == 'spawn_item' and child.attrib.get('Type') == 'List')
    return 'populated' if count else 'present_empty'


def _scan_native_parent_spawn_chains(scans, parent_edges, decoded_root, member_index,
                                     existing_rows, visited_members):
    parents = defaultdict(set)
    for edge in parent_edges:
        parents[edge['source_member'].lower()].add(edge['member'].lower())
    rows = list(existing_rows)
    unresolved = []
    for scan in scans:
        start = scan['native_parent_member'].lower()
        queue = [(start, 0)]
        seen = set()
        checked = []
        while queue:
            member, depth = queue.pop(0)
            if member in seen:
                continue
            seen.add(member)
            xml_file = decoded_root / Path(member).with_suffix('.xml')
            if not xml_file.is_file():
                checked.append({'member': member, 'depth': depth, 'status': 'parent_member_not_decoded'})
                continue
            state = _native_spawn_list_state(xml_file, scan['local_variant'])
            checked.append({'member': member, 'depth': depth, 'spawn_list_state': state})
            if state == 'populated':
                found, failures = _native_spawn_item_rows(xml_file, member, scan['actor_id'],
                    scan['source_file'], scan['local_variant'], member_index)
                unresolved.extend(failures)
                for row in found:
                    row['native_parent_depth'] = depth
                    row['child_spawn_list_state'] = scan['local_spawn_list']
                    row['list_merge_status'] = (
                        'parent_candidate_child_list_absent_merge_unverified'
                        if scan['local_spawn_list'] == 'absent'
                        else 'parent_candidate_child_list_present_override_or_merge_unverified')
                    key = (row['local_actor_id'], row['target_id'], row['local_variant'], row['source_member'])
                    if not any((old['local_actor_id'], old['target_id'], old['local_variant'], old['source_member']) == key
                               for old in rows):
                        rows.append(row)
                    if row.get('expected_member_path') not in visited_members:
                        unresolved.append({'source_member': member, 'target_id': row['target_id'],
                            'reason': 'native parent spawn target found; actor RGD closure not yet decoded'})
            if depth < 6:
                queue.extend((parent, depth + 1) for parent in sorted(parents.get(member, [])))
            elif parents.get(member):
                unresolved.append({'source_member': member, 'reason': 'native parent spawn scan depth limit reached',
                                   'remaining_parent_members': sorted(parents[member])})
        scan['native_parent_chain_scan'] = checked
    return rows, unresolved


def extract_official_rgd_closure(inv):
    """Extract and officially decode a hash-pinned reference/parent closure.

    Decoded XML is retained as read-only evidence from sga-archiver. It is not
    used as editable tuning XML or as a serialization template.
    """
    archive = Path(inv['official_archive_resolution']['archive'])
    expected_archive_sha = inv['official_archive_resolution']['sha256']
    if sha(archive) != expected_archive_sha:
        raise RuntimeError('Official Attrib.sga changed after the inventory index pass')
    tool_info = {'path': ARCH.as_posix(), 'sha256': sha(ARCH)}
    archive_root = owned(OUT / 'inventory' / 'official_rgd' / expected_archive_sha)
    raw_root = owned(archive_root / 'raw')
    decoded_root = owned(archive_root / 'decoded')
    raw_root.mkdir(parents=True, exist_ok=True)
    decoded_root.mkdir(parents=True, exist_ok=True)
    members, _ = official_closure_seed_members(inv)
    member_index = official_member_index()
    if member_index['status'] != 'read_only_indexed' or member_index['archive_sha256'] != expected_archive_sha:
        raise RuntimeError('Could not revalidate current official Attrib.sga member index')
    candidate_seed = 'attrib/sbps/races/chinese/unit_official_1_chi.rgd'
    if candidate_seed not in member_index['members']:
        raise RuntimeError('Candidate-only Chinese Imperial Official seed is absent from current Attrib.sga')

    # Scan every reached building's native parent chain, including actors with
    # local spawn_items. Without engine-proven list override/merge semantics,
    # native parent entries remain candidates even when the local child has a
    # populated list; they are not promoted to an obtainable roster.
    source_root = Path(inv['source']['path'])
    reachable_buildings = set(inv.get('reachable_building_actor_ids', []))
    parent_spawn_owners = defaultdict(list)
    parent_spawn_scans = []
    source_edges = {}
    for edge in inv['consumer_edges']:
        if edge['source_id'] in reachable_buildings and edge['name'] == 'parent_pbg':
            source_edges.setdefault((edge['source_id'], edge['source_file']), []).append(edge)
    for (actor_id, source_file), parent_edges in source_edges.items():
        rel = source_file.replace('assets/', '', 1).replace('/', '\\')
        local_path = source_root / rel
        if not local_path.is_file():
            continue
        try:
            local_root = ET.parse(local_path).getroot()
        except ET.ParseError:
            continue
        for edge in parent_edges:
            variant = edge.get('variant', 'base')
            has_list = any(el.tag == 'list' and el.attrib.get('name') == 'spawn_items'
                           and variant_for(xp).lower() == variant.lower()
                           for el, xp in iter_with_paths(local_root))
            expected = edge.get('official_archive', {}).get('expected_member_path')
            if not expected or not edge.get('official_archive', {}).get('present_in_official_attrib'):
                continue
            owner = {'actor_id': actor_id, 'source_file': source_file, 'local_variant': variant,
                     'local_spawn_list': 'present' if has_list else 'absent',
                     'native_parent_member': expected.lower()}
            parent_spawn_scans.append(owner)
            parent_spawn_owners[expected.lower()].append(owner)

    # Add exact official parent_pbg files recursively. The extractor is the
    # installed official archive tool; no binary fields are guessed.
    pending = set(members)
    visited = set()
    parent_edges, unresolved_parents = [], []
    loadout_edges, unresolved_loadouts = [], []
    visual_links, unresolved_visual_links = [], []
    inherited_spawn_items, unresolved_inherited_spawn_items = [], []
    depth = 0
    while pending and depth < 6:
        batch = sorted(pending - visited)
        pending = set()
        if not batch:
            break
        missing_raw = [member for member in batch
                       if not owned(raw_root / Path(member)).is_file()]
        for offset in range(0, len(missing_raw), 40):
            chunk = missing_raw[offset:offset + 40]
            args = [str(ARCH), 'extract', str(archive), str(raw_root)]
            for member in chunk:
                args.extend(['--member', member])
            result = subprocess.run(args, check=True, capture_output=True, text=True, timeout=180)
            details = json.loads(result.stdout)
            if details.get('written_count') != len(chunk):
                raise RuntimeError(f"Official extract wrote {details.get('written_count')} of {len(chunk)} members")
        if sha(archive) != expected_archive_sha:
            raise RuntimeError('Official Attrib.sga changed during selective extraction')
        for member in batch:
            visited.add(member)
            raw_file = owned(raw_root / Path(member))
            if not raw_file.is_file():
                raise FileNotFoundError(f'Official extractor omitted {member}')
            xml_file = owned(decoded_root / Path(member).with_suffix('.xml'))
            xml_file.parent.mkdir(parents=True, exist_ok=True)
            if not xml_file.is_file():
                decoded = subprocess.run([str(ARCH), 'decode-rgd', str(raw_file), str(xml_file)],
                                         check=True, capture_output=True, text=True, timeout=60)
                decode_meta = json.loads(decoded.stdout)
                if decode_meta.get('schema') != 'sga-archiver.decode-rgd/v1':
                    raise RuntimeError(f'Unexpected RGD decode contract for {member}')
            source_category = member.split('/')[1] if len(member.split('/')) > 2 else ''
            if source_category in {'ebps', 'sbps', 'weapon', 'attachments', 'attachment_lists'}:
                parents, unresolved = _rgd_parent_targets(xml_file, member, member_index)
                for parent in parents:
                    parent_edges.append({'source_member': member, **parent})
                    pending.add(parent['member'])
                unresolved_parents.extend({'source_member': member, **record} for record in unresolved)
            if source_category == 'sbps':
                bodies, unresolved = _rgd_squad_loadout_targets(xml_file, member, member_index)
                for body in bodies:
                    loadout_edges.append({'source_member': member, **body})
                    pending.add(body['member'])
                unresolved_loadouts.extend({'source_member': member, **record} for record in unresolved)
            if source_category == 'ebps':
                links, unresolved = _rgd_entity_visual_links(xml_file, member, member_index)
                for link in links:
                    visual_links.append({'source_member': member, **link})
                    pending.add(link['member'])
                unresolved_visual_links.extend({'source_member': member, **record} for record in unresolved)
                for owner in parent_spawn_owners.get(member.lower(), []):
                    owner['immediate_native_spawn_list_state'] = _native_spawn_list_state(
                        xml_file, owner['local_variant'])
                    rows, unresolved = _native_spawn_item_rows(
                        xml_file, member, owner['actor_id'], owner['source_file'],
                        owner['local_variant'], member_index)
                    for row in rows:
                        row['native_parent_depth'] = 0
                        row['child_spawn_list_state'] = owner['local_spawn_list']
                        row['list_merge_status'] = (
                            'parent_candidate_child_list_absent_merge_unverified'
                            if owner['local_spawn_list'] == 'absent'
                            else 'parent_candidate_child_list_present_override_or_merge_unverified')
                        inherited_spawn_items.append(row)
                        pending.add(row['expected_member_path'])
                    unresolved_inherited_spawn_items.extend(unresolved)
        depth += 1

    if pending:
        unresolved_parents.append({'reason': 'parent closure depth limit reached',
                                  'remaining_members': sorted(pending)})
    inherited_spawn_items, chain_unresolved = _scan_native_parent_spawn_chains(
        parent_spawn_scans, parent_edges, decoded_root, member_index,
        inherited_spawn_items, visited)
    unresolved_inherited_spawn_items.extend(chain_unresolved)
    if sha(archive) != expected_archive_sha:
        raise RuntimeError('Official Attrib.sga changed before closure manifest write')
    file_records = []
    for member in sorted(visited):
        raw_file = raw_root / Path(member)
        xml_file = decoded_root / Path(member).with_suffix('.xml')
        file_records.append({'member': member,
                             'archive_member': member_index['members'].get(member.lower()),
                             'raw_output': raw_file.relative_to(OUT).as_posix(),
                             'raw_sha256': sha(raw_file), 'raw_bytes': raw_file.stat().st_size,
                             'decoded_output': xml_file.relative_to(OUT).as_posix(),
                             'decoded_sha256': sha(xml_file), 'decoded_bytes': xml_file.stat().st_size})
    return {'schema': 'community-civilization-pack.release060.official-rgd-closure/v1',
            'official_attrib_archive': archive.as_posix(), 'official_attrib_sha256': expected_archive_sha,
            'archive_tool': tool_info, 'seed_member_count': len(members),
            'candidate_only_native_seed_members': [candidate_seed],
            'decoded_member_count': len(visited), 'parent_edges': parent_edges,
            'unresolved_parent_edges': unresolved_parents,
            'squad_loadout_body_edges': loadout_edges,
            'unresolved_squad_loadout_body_edges': unresolved_loadouts,
            'entity_visual_attachment_and_weapon_links': visual_links,
            'unresolved_entity_visual_links': unresolved_visual_links,
            'reachable_building_parent_spawn_scans': parent_spawn_scans,
            'inherited_native_spawn_item_candidates': inherited_spawn_items,
            'unresolved_inherited_native_spawn_items': unresolved_inherited_spawn_items,
            'members': file_records,
            'limits': 'Exact compiled members from this Attrib.sga and the installed official RGD decoder. The decoded XML is evidence only, not editable tuning source. Parent_pbg links and squad loadout body links are resolved only when PBG name/category identify one exact indexed member.'}


def visual_asset_refs(doc):
    result = []
    tokens = ('animator', 'animation', 'skeleton', 'rig', 'motion', 'model', 'mesh', 'visual')
    for el, xpath in iter_with_paths(doc['root']):
        name = el.attrib.get('name', '')
        value = el.attrib.get('value', '')
        if el.tag not in {'file', 'string', 'instance_reference', 'template_reference'}:
            continue
        if not value or not any(token in name.lower() for token in tokens):
            continue
        result.append({'tag': el.tag, 'name': name, 'value': value,
                       'xpath': xpath, 'variant': variant_for(xpath),
                       'mod': el.attrib.get('mod', '')})
    return result


def make_inventory(source_root: Path):
    attrib_root = source_root / 'attrib'
    if not attrib_root.is_dir():
        raise FileNotFoundError(f'Frozen source attrib directory missing: {attrib_root}')
    docs, parse_errors, file_hashes = parse_index(attrib_root)
    edge_index = {ident: ref_edges(doc) for ident, doc in docs.items()}
    for edges in edge_index.values():
        for edge in edges:
            resolve_status(edge, docs)

    army = docs.get(key(ARMY_ID))
    if not army:
        raise FileNotFoundError(f'Vietnam army blueprint not in frozen source: {ARMY_FILE}')

    # Proven roots are direct army starting squads. Campaign has its own list and
    # is kept as separate provenance even when it names the same squad.
    roots = defaultdict(list)
    start_records = []
    for el, xpath in iter_with_paths(army['root']):
        if el.tag not in REF_TAGS or el.attrib.get('name') != 'squad':
            continue
        if "list[@name='starting_units']" not in xpath:
            continue
        target = key(el.attrib.get('value', ''))
        ambient = any(token in target for token in ('gaia_herdable', 'gaia_animal', 'gaia_sheep'))
        record = {'target': target, 'source_file': army['relative'], 'xpath': xpath,
                  'variant': variant_for(xpath), 'mod': el.attrib.get('mod', ''),
                  'list_item_id': el.attrib.get('List.ItemID', ''),
                  'classification': ('excluded_ambient_animal_starting_force' if ambient
                                     else 'confirmed_starting_force')}
        start_records.append(record)
        if not ambient:
            roots[target].append(record)

    start_building_records = []
    for el, xpath in iter_with_paths(army['root']):
        if el.tag not in REF_TAGS or el.attrib.get('name') != 'building':
            continue
        if "list[@name='starting_buildings']" not in xpath:
            continue
        target = key(el.attrib.get('value', ''))
        record = {'target': target, 'source_file': army['relative'], 'xpath': xpath,
                  'variant': variant_for(xpath), 'mod': el.attrib.get('mod', ''),
                  'list_item_id': el.attrib.get('List.ItemID', ''),
                  'classification': 'confirmed_starting_building_source'}
        start_building_records.append(record)
        roots[target].append(record)

    init_path = source_root / 'scar' / 'vietnam' / 'initialization.scar'
    init_text = init_path.read_text(encoding='utf-8-sig') if init_path.exists() else ''
    converted = re.findall(r'BP_Get(?:Entity|Squad)Blueprint\("' + LOCAL_MOD + r':([^"]+)"\)', init_text)
    init_evidence = {'source_file': init_path.relative_to(source_root).as_posix() if init_path.exists() else None,
                     'sha256': sha(init_path) if init_path.exists() else None,
                     'converted_private_blueprints': converted,
                     'starting_tc_selected_by_native_blueprint_name': 'building_town_center_capital_chi' in init_text,
                     'starting_tc_conversion': ('vn_building_town_center_capital_chi' in converted and
                                                'Entity_ConvertBlueprint(capitals[1], tc)' in init_text),
                     'starting_villager_and_scout_conversion': ('vn_unit_villager_1_chi' in converted and
                                                               'vn_unit_scout_1_chi' in converted),
                     'private_builder_note': 'initialization.scar documents the private Vietnamese builder and explicitly removes the native ranged-control building from player production.'}

    # Local building spawn-item lists often implement unit menus. They are
    # candidate routes pending proof that the building actor is activated by
    # the army/building graph; they are never silently promoted to confirmed.
    spawn_records = []
    for ident, doc in sorted(docs.items()):
        if doc['category'] != 'ebps':
            continue
        for el, xpath in iter_with_paths(doc['root']):
            if el.tag not in REF_TAGS or el.attrib.get('name') != 'squad':
                continue
            if not el.attrib.get('value', '').strip():
                continue
            if "list[@name='spawn_items']" not in xpath:
                continue
            target = key(el.attrib.get('value', ''))
            record = {'target': target, 'source_file': doc['relative'], 'source_id': ident,
                      'xpath': xpath, 'variant': variant_for(xpath),
                      'mod': el.attrib.get('mod', ''), 'list_item_id': el.attrib.get('List.ItemID', ''),
                      'classification': 'unresolved_spawn_item_actor_activation_or_item_gate',
                      'spawn_item_context': spawn_item_context(doc['root'], el)}
            record['item_eligibility_evidence'] = {
                'classification': 'source_gate_requirements_preserved_but_not_evaluated',
                'observer_type_interpretation': 'recorded_as_ui/observer metadata; not treated as a production lock',
                'reference_requirements': record['spawn_item_context'].get('reference_requirements', []),
            }
            spawn_records.append(record)
            roots[target].append(record)

    # Reached local squads/entities form the inspectable consumer closure.
    reached = set()
    confirmed_reached = set()
    candidate_reached = set()
    processed = set()
    queue = deque((r['target'], 'confirmed') for r in start_records
                  if r['classification'] == 'confirmed_starting_force')
    queue.extend((r['target'], 'confirmed') for r in start_building_records)
    upgrade_edges = []
    ability_edges = []
    buildable_records = []
    reachable_spawn_records = []
    reached_building_ids = set()
    while queue:
        raw_ident, confidence = queue.popleft()
        ident = key(raw_ident)
        marker = (ident, confidence)
        if marker in processed:
            continue
        processed.add(marker)
        reached.add(ident)
        (confirmed_reached if confidence == 'confirmed' else candidate_reached).add(ident)
        doc = docs.get(ident)
        if not doc:
            continue
        if doc['category'] == 'sbps':
            for edge in edge_index[ident]:
                # Only unit composition, attachments, and tier targets extend
                # the unit graph. Other named references remain in full edges.
                if edge['target_category'] == 'ebps' and edge['name'] in {'type', 'ebp'}:
                    queue.append((edge['target'], confidence))
                if (edge['target_category'] == 'ebps' and edge['name'] == 'ebp'
                        and "list[@name='construction_groups']" in edge['xpath']):
                    item_el = next((e for e, xp in iter_with_paths(doc['root']) if xp == edge['xpath']), None)
                    buildable = {**edge,
                                 'construction_item_context': construction_item_context(doc['root'], item_el)
                                 if item_el is not None else {},
                                 'classification': 'reachable_buildable_actor_from_starting_squad'}
                    buildable_records.append(buildable)
                    if edge['target'] in docs:
                        queue.append((edge['target'], confidence))
                if edge['target_category'] == 'sbps' and edge['name'] in {
                    'type', 'squad', 'statetree_tier_pgb_upgrade_target_squad'}:
                    queue.append((edge['target'], confidence))
                if edge['target_category'] == 'abilities':
                    ability_edges.append(edge)
                    if edge['target'] in docs:
                        queue.append((edge['target'], confidence))
                if edge['target_category'] == 'upgrade':
                    upgrade_edges.append(edge)
        elif doc['category'] == 'ebps':
            if is_building_actor(ident, edge_index[ident]):
                reached_building_ids.add(ident)
                for spawned in spawn_records:
                    if spawned['source_id'] != ident:
                        continue
                    spawned['actor_reachability'] = 'source_confirmed_reachable_building_actor'
                    spawned['classification'] = 'reachable_actor_spawn_with_item_gate_recorded'
                    reachable_spawn_records.append(spawned)
                    if spawned['target'] in docs:
                        queue.append((spawned['target'], confidence))
            for edge in edge_index[ident]:
                if edge['target_category'] == 'sbps' and edge['name'] in {
                    'statetree_tier_pgb_upgrade_target_squad', 'squad', 'squad_name'}:
                    upgrade_edges.append(edge)
                    # The Abbey of Kings selection reference may name a unit
                    # for UI/civ-wide wiring without being a production route.
                    if 'statetree_tier_pgb_upgrade_target_squad' in edge['xpath']:
                        queue.append((edge['target'], confidence))
                if edge['target_category'] == 'abilities':
                    ability_edges.append(edge)
                    if edge['target'] in docs:
                        queue.append((edge['target'], confidence))
                if edge['target_category'] == 'upgrade':
                    upgrade_edges.append(edge)
        elif doc['category'] == 'abilities':
            for edge in edge_index[ident]:
                if edge['target_category'] in UNIT_CATEGORIES and edge['name'] in {
                    'squad', 'type', 'ebp', 'spawn_squad', 'summoned_squad'}:
                    queue.append((edge['target'], confidence))

    # Ability-owned unit spawns are an additional candidate only where the
    # ability is referenced by a reached local unit. Record exact source refs.
    ability_spawn_records = []
    for edge in list(ability_edges):
        ability = docs.get(edge['target'])
        if not ability:
            continue
        for spawned in edge_index[ability['id']]:
            if spawned['target_category'] in UNIT_CATEGORIES and spawned['name'] in {
                'squad', 'type', 'ebp', 'spawn_squad', 'summoned_squad'}:
                record = {'target': spawned['target'], 'source_file': ability['relative'],
                          'source_id': ability['id'], 'xpath': spawned['xpath'],
                          'ability_ref': edge,
                          'variant': spawned['variant'], 'mod': spawned['mod'],
                          'classification': 'source_confirmed_unit_ability_spawn_reference'
                          if edge['source_id'] in confirmed_reached else
                          'unresolved_candidate_unit_ability_spawn_reference'}
                ability_spawn_records.append(record)
                roots[spawned['target']].append(record)

    # Local spawn targets from unactivated actors remain candidate records,
    # while source-confirmed production targets join the reachable roster.
    all_referenced_actor_ids = reached | {r['target'] for r in spawn_records if r['target'] in docs}

    # Full outgoing reference ledger for each local reached record.
    closure_edges = []
    for ident in sorted(reached):
        if ident in docs:
            closure_edges.extend(edge_index[ident])
    # Some unit ability definitions aren't reached as unit records; include
    # their own exact edges in the ledger for the next closure pass.
    for edge in ability_edges:
        if edge['target'] in docs:
            closure_edges.extend(edge_index[edge['target']])
    unique_edges, seen = [], set()
    for edge in closure_edges:
        sig = (edge['source_id'], edge['xpath'], edge['target'], edge['name'])
        if sig not in seen:
            seen.add(sig)
            unique_edges.append(edge)

    # Candidate entities from active Vietnam-attributed sources are listed but
    # not treated as reached unless they originate in starting/building spawns.
    actor_rows = []
    for ident in sorted(all_referenced_actor_ids):
        if ident not in docs or docs[ident]['category'] not in UNIT_CATEGORIES:
            continue
        doc = docs[ident]
        if not is_unit_actor(ident, doc, edge_index[ident]):
            continue
        incoming = [edge for source_edges in edge_index.values() for edge in source_edges
                    if edge['target'] == ident]
        actor_rows.append({'id': ident, 'category': doc['category'],
                           'kind': actor_kind(doc), 'source_file': doc['relative'],
                           'sha256': doc['hash'],
                           'reachability': ('confirmed_starting_or_tier_chain' if ident in confirmed_reached
                                            else 'unresolved_candidate_only'),
                           'provenance': roots.get(ident, []),
                           'incoming_refs': incoming,
                           'local_reference_count': len(edge_index[ident]),
                           'parent_refs': [e for e in edge_index[ident] if e['name'] == 'parent_pbg'],
                           'tier_targets': [e for e in edge_index[ident]
                                            if e['name'] == 'statetree_tier_pgb_upgrade_target_squad'],
                           'attachments': [e for e in edge_index[ident]
                                           if 'attachment' in e['xpath'].lower() or e['name'] == 'unit_attachments'],
                           'weapon_refs': [e for e in edge_index[ident]
                                           if e['target_category'] in {'weapon', 'projectile'}],
                           'animator_and_attachment_refs': [e for e in edge_index[ident]
                                                            if e['target_category'] in {'attachments', 'attachment_lists', 'animator', 'animation'}
                                                            or 'animator' in e['name'].lower()
                                                            or 'animation' in e['name'].lower()],
                           'visual_asset_refs': visual_asset_refs(doc),
                           'ability_refs': [e for e in edge_index[ident]
                                            if e['target_category'] == 'abilities'],
                           'upgrade_refs': [e for e in edge_index[ident]
                                            if e['target_category'] == 'upgrade']})

    # Stable source digest across the frozen XML inputs.
    digest_data = ''.join(f'{path}\0{digest}\n' for path, digest in sorted(file_hashes.items()))
    source_digest = hashlib.sha256(digest_data.encode('utf-8')).hexdigest()
    confirmed_actor_rows = [r for r in actor_rows if r['reachability'] == 'confirmed_starting_or_tier_chain']
    candidate_actor_rows = [r for r in actor_rows if r['reachability'] == 'unresolved_candidate_only']
    all_local_squads = sorted(i for i, d in docs.items()
                              if d['category'] == 'sbps' and '\\vietnam\\' in i and unitish(i))
    linked_squads = {r['id'] for r in actor_rows if r['category'] == 'sbps'}
    unlinked_squads = []
    for ident in all_local_squads:
        if ident not in linked_squads:
            doc = docs[ident]
            unlinked_squads.append({'id': ident, 'source_file': doc['relative'], 'sha256': doc['hash'],
                                    'classification': 'local_blueprint_no_start_spawn_or_tier_path_in_snapshot',
                                    'references': edge_index[ident]})
    all_local_unit_ebps = sorted(i for i, d in docs.items()
                                 if d['category'] == 'ebps' and '\\vietnam\\' in i
                                 and is_unit_actor(i, d, edge_index[i]))
    linked_ebps = {r['id'] for r in actor_rows if r['category'] == 'ebps'}
    unlinked_ebps = []
    for ident in all_local_unit_ebps:
        if ident not in linked_ebps:
            doc = docs[ident]
            unlinked_ebps.append({'id': ident, 'source_file': doc['relative'], 'sha256': doc['hash'],
                                  'classification': 'local_unit_entity_no_start_spawn_or_tier_path_in_snapshot',
                                  'references': edge_index[ident]})
    reachable_ids = {row['id'] for row in confirmed_actor_rows}
    direct_local = sorted({r['target'] for r in start_records if r['target'] in docs})
    missing_start = sorted({r['target'] for r in start_records if r['target'] not in docs})
    external_refs = [e for e in unique_edges if e['status'] != 'resolved_local']
    candidate_external_ids = sorted({r['target'] for r in spawn_records if r['target'] not in docs})
    rattan = rattan_evidence(source_root)
    landmark_scar = source_root / 'scar' / 'vietnam' / 'landmarks.scar'
    landmark_text = landmark_scar.read_text(encoding='utf-8-sig') if landmark_scar.exists() else ''
    landmark_unlock_evidence = {
        'source_file': landmark_scar.relative_to(source_root).as_posix() if landmark_scar.exists() else None,
        'sha256': sha(landmark_scar) if landmark_scar.exists() else None,
        'headquarters_gate': 'vn_building_landmark_age2_headquarter_vit' in landmark_text,
        'ability_unlocked_by_gate': 'vn_activate_stealth_forvills_vit' if 'vn_activate_stealth_forvills_vit' in landmark_text else None,
        'buildable_landmark_actor_ids': sorted({r['target'] for r in buildable_records
                                                if 'landmark' in r['target']}),
        'buildable_unlock_is_source_eligibility_only': True,
    }
    official_index = official_member_index()
    non_rgd_refs = [e for e in unique_edges if e['status'] != 'resolved_local' and
                    (e['target_category'] == 'options' or e['target'] in {
                        'attachments\\attach_data', 'attachments\\attach_data_entity'})]
    rgd_external = [e for e in unique_edges if e['status'] != 'resolved_local' and e not in non_rgd_refs]
    if official_index['status'] == 'read_only_indexed':
        for edge in unique_edges:
            if edge['status'] != 'resolved_local' and edge not in non_rgd_refs:
                edge['official_archive'] = official_member_for(edge['target'], official_index)
            elif edge in non_rgd_refs:
                edge['official_archive'] = {'expected_member_path': None,
                                            'present_in_official_attrib': None,
                                            'classification': 'native template/option contract, not an RGD path'}
        official_external = rgd_external
        official_absent = sorted({e['target'] for e in official_external
                                  if not e['official_archive']['present_in_official_attrib']})
        official_found = sorted({e['target'] for e in official_external
                                 if e['official_archive']['present_in_official_attrib']})
        candidate_external = [{'id': ident, **official_member_for(ident, official_index),
                               'classification': 'spawn_item_candidate_still_unresolved_for_actor_and_item_gate'}
                              for ident in candidate_external_ids]
    else:
        official_external = rgd_external
        official_absent, official_found = [], []
        candidate_external = [{'id': ident, 'classification': 'spawn_item_candidate_official_lookup_unavailable'}
                              for ident in candidate_external_ids]

    inventory = {
        'schema': 'community-civilization-pack.release060-unit-inventory/v1',
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'source': {'path': source_root.as_posix(), 'frozen_snapshot': True,
                   'xml_instance_count': len(docs), 'parse_errors': parse_errors,
                   'instance_manifest_sha256': source_digest,
                   'file_hashes': dict(sorted(file_hashes.items()))},
        'scope': {'included': 'Vietnamese land-unit routes through starting forces, starting-building spawns, starting-villager construction menus, buildable production/landmark actors, building spawn entries, upgrades and unit abilities.',
                  'excluded': ['ships/naval units', 'buildings', 'unrelated campaign-only records', 'ambient animals'],
                  'policy': 'Reachability through local starting squad construction_groups and local building spawn_items is source-confirmed; construction and item eligibility requirements are recorded separately and are not runtime proof. Unactivated actor spawn_items remain candidates. Local references preserve exact XPath. Missing native/official source closure is unresolved.'},
        'army': {'id': ARMY_ID, 'source_file': army['relative'],
                 'sha256': army['hash'], 'starting_units': start_records,
                 'starting_buildings': start_building_records,
                 'initialization_scar': init_evidence,
                 'production_buildings_list': {'xpath': "/instance/group[@name='army_bag']/list[@name='production_buildings']",
                                               'local_entries': len(refs_in_list(army, 'production_buildings')),
                                               'note': 'Empty in the frozen XML; effective inherited production-building set requires native army inheritance resolution.'}},
        'candidate_building_spawn_refs': spawn_records,
        'reachable_buildable_actor_refs': buildable_records,
        'reachable_actor_spawn_refs': reachable_spawn_records,
        'unit_ability_spawn_refs': ability_spawn_records,
        'reachable_building_actor_ids': sorted(reached_building_ids),
        'landmark_unlock_evidence': landmark_unlock_evidence,
        'unresolved_external_spawn_targets': candidate_external,
        'units_and_entities': confirmed_actor_rows,
        'unresolved_candidate_units_and_entities': candidate_actor_rows,
        'unlinked_local_vietnam_squads': unlinked_squads,
        'unlinked_local_vietnam_unit_entities': unlinked_ebps,
        'consumer_edges': unique_edges,
        'official_archive_resolution': {
            'status': official_index['status'], 'archive': official_index.get('archive'),
            'sha256': official_index.get('archive_sha256'),
            'archive_version': official_index.get('archive_version'),
            'member_count': official_index.get('archive_member_count'),
            'external_refs_checked': len(official_external),
            'native_template_refs_not_rgd_indexed': len(non_rgd_refs),
            'non_rgd_contract_breakdown': {
                'options': sum(1 for e in non_rgd_refs if e['target_category'] == 'options'),
                'attachment_templates': sum(1 for e in non_rgd_refs if e['target_category'] == 'attachments'),
            },
            'refs_found_by_exact_rgd_path': len(official_found),
            'unique_external_ids_found_by_exact_rgd_path': len(set(official_found)),
            'refs_absent_from_official_archive': official_absent,
            'limits': 'Archive membership confirms exact current native RGD paths; parent closure and selected inherited production lists are decoded separately below, but do not prove runtime merge behavior, item eligibility, or availability.'},
        'coverage': {'local_confirmed_unit_or_entity_ids': len(reachable_ids),
                     'local_confirmed_squad_ids': sum(1 for r in confirmed_actor_rows if r['category'] == 'sbps'),
                     'local_confirmed_entity_ids': sum(1 for r in confirmed_actor_rows if r['category'] == 'ebps'),
                     'unresolved_candidate_local_unit_or_entity_ids': len(candidate_actor_rows),
                     'unlinked_local_vietnam_squad_blueprints': len(unlinked_squads),
                     'unlinked_local_vietnam_unit_entities': len(unlinked_ebps),
                     'starting_refs': len(start_records), 'local_starting_squad_ids': len(direct_local),
                     'external_starting_refs': missing_start,
                     'building_spawn_candidate_refs': len(spawn_records),
                     'reachable_local_building_actor_ids': len(reached_building_ids),
                     'reachable_buildable_actor_refs': len(buildable_records),
                     'reachable_actor_spawn_refs': len(reachable_spawn_records),
                     'spawn_item_gate_evaluations_deferred': len(spawn_records),
                     'external_or_unresolved_closure_refs': len(external_refs),
                     'source_parse_errors': len(parse_errors),
                     'complete_official_inheritance_closure': False},
        'official_closure_next_step': [
            {'id': e['target'], 'referenced_from': e['source_file'], 'xpath': e['xpath'],
             'reference_name': e['name'], 'mod': e['mod'],
             'classification': ('exact official RGD path found; parent/body closure and item eligibility are separate'
                                if e.get('official_archive', {}).get('present_in_official_attrib')
                                else 'unresolved: no exact local source or official RGD path')} 
            for e in external_refs],
        'rattan_check': rattan,
        'classification_notes': [
            'A stock squad_name or UI target reference alone does not qualify as production reachability.',
            'A stock Abbey of Kings reference present in a spawn_items list remains unresolved until the owning actor and item gates are qualified; a squad token alone is not proof of trainability.',
            'The local army has no parent_pbg and an empty production_buildings list; its Chinese comparison is not treated as inherited. Every reached building actor parent chain is traced for compiled native spawn lists, including when the local child has its own spawn_items list.',
            'Starting villagers lead through source-local construction_groups into buildable actors. Local spawn lists are source-confirmed references. Exact native parent-list entries are retained as candidates for both absent and populated local child lists; the compiled values do not establish whether the engine replaces or merges inherited lists, nor do they prove age/resource/requirement eligibility.',
        ],
    }
    return inventory


def official_actor_roster_candidates(inv):
    """Compact exact-current-RGD view of directly referenced stock actor candidates."""
    native = {edge['target']: edge.get('official_archive', {})
              for edge in inv['consumer_edges'] if edge.get('official_archive', {}).get('present_in_official_attrib')}
    by_target = {}
    for relation, records in (('spawn_item', inv.get('reachable_actor_spawn_refs', [])),
                              ('builder_construction_item', inv.get('reachable_buildable_actor_refs', []))):
        for record in records:
            target = record.get('target', '')
            category = target.split('\\', 1)[0].lower()
            if category not in {'sbps', 'ebps'} or not unitish(target):
                continue
            official = native.get(target)
            if not official:
                continue
            row = by_target.setdefault(target, {'id': target, 'category': category,
                'expected_member_path': official.get('expected_member_path'),
                'relation_evidence': [], 'item_gate_evaluation': 'not_evaluated'})
            row['relation_evidence'].append({
                'relation': relation, 'source_id': record.get('source_id'),
                'source_file': record.get('source_file'), 'xpath': record.get('xpath'),
                'variant': record.get('variant'),
                'item_eligibility_evidence': record.get('item_eligibility_evidence'),
            })
    for row in by_target.values():
        row['relation_evidence'] = sorted(row['relation_evidence'],
            key=lambda item: (item.get('relation', ''), item.get('source_id') or '', item.get('variant') or ''))
    return [by_target[k] for k in sorted(by_target)]


def squad_family_tiers(rows):
    groups = defaultdict(list)
    pattern = re.compile(r'^(?P<family>.+)_(?P<tier>\d+)_(?P<civ>chi|vit|mon_for_vit)(?:_(?P<variant>.+))?$', re.I)
    for row in rows:
        identifier = row.get('id', '').rsplit('\\', 1)[-1]
        match = pattern.match(identifier)
        if match:
            family, tier = match.group('family'), int(match.group('tier'))
            variant = match.group('civ').lower() + (('_' + match.group('variant')) if match.group('variant') else '')
            groups[family].append({'tier': tier, 'variant': variant, 'id': row['id']})
        else:
            groups[identifier].append({'tier': None, 'variant': '', 'id': row['id']})
    return [{'family': family, 'tiers': sorted({r['tier'] for r in entries if r['tier'] is not None}),
             'variants_and_ids': sorted(entries, key=lambda r: (r['tier'] or 0, r['variant'], r['id']))}
            for family, entries in sorted(groups.items())]


def native_actor_visual_summary(inv, closure, output_root: Path):
    """Link reached native squads/entities to body, parent, weapon and animator data."""
    members = {row['member']: row for row in closure['members']}
    parents = defaultdict(list)
    for edge in closure['parent_edges']:
        parents[edge['source_member']].append(edge['member'])
    bodies = defaultdict(list)
    for edge in closure['squad_loadout_body_edges']:
        bodies[edge['source_member']].append(edge['member'])
    visuals = defaultdict(list)
    for edge in closure['entity_visual_attachment_and_weapon_links']:
        visuals[edge['source_member']].append(edge)
    actors = []
    for row in inv.get('official_actor_roster_candidates', []):
        relations = {e.get('relation') for e in row.get('relation_evidence', [])}
        compiled_confirmed = any(
            edge.get('compiled_list_qualification') == 'compiled_child_contains_native_parent_item'
            for edge in row.get('relation_evidence', []))
        status = ('compiled_native_parent_list_item_gates_unverified' if compiled_confirmed else
                  'native_parent_list_candidate_merge_unverified'
                  if relations == {'inherited_native_parent_spawn_item'} else
                  'source_local_relation_gate_unverified')
        actors.append((row['id'], row['expected_member_path'], status))
    actors += [(row['id'], row.get('expected_member_path'), row['classification'])
               for row in inv.get('candidate_only_actor_refs', [])
               if row.get('expected_member_path')]
    result = []
    for actor_id, member_path, status in actors:
        if not member_path:
            continue
        member_path = member_path.lower()
        chain, seen, pending = [], set(), [member_path]
        while pending:
            node = pending.pop(0)
            if node in seen:
                continue
            seen.add(node)
            chain.append(node)
            pending.extend(x for x in parents.get(node, []) if x not in seen)
        actor_bodies = sorted(set(bodies.get(member_path, [])))
        if member_path.startswith('attrib/ebps/'):
            actor_bodies = sorted(set(actor_bodies + [member_path]))
        visual_rows = []
        attachments = set()
        for body in actor_bodies:
            for link in visuals.get(body, []):
                visual_rows.append({k: link.get(k) for k in (
                    'source_field', 'pbg_name', 'pbg_map', 'member', 'socket_or_position')})
                if link.get('pbg_map') == 'attachments\\attachment_lists' and link.get('member'):
                    attachments.add(link['member'])
        animator_assets, model_refs, material_refs = set(), set(), set()
        for attachment in sorted(attachments):
            record = members.get(attachment)
            if not record:
                continue
            xml_file = output_root / record['decoded_output']
            if not xml_file.is_file():
                continue
            try:
                root = ET.parse(xml_file).getroot()
            except ET.ParseError:
                continue
            for node in root.iter('RGDNode'):
                key_name, value = node.attrib.get('Key', '').lower(), node.attrib.get('Value', '')
                if not value:
                    continue
                if key_name == 'parent_animator':
                    animator_assets.add(value)
                if key_name in {'animator0', 'animator1', 'mesh', 'model'} or value.startswith('art\\'):
                    model_refs.add(value)
                if 'material' in key_name or value.lower().endswith('.material'):
                    material_refs.add(value)
        result.append({'id': actor_id, 'current_official_member': member_path,
            'reachability_status': status, 'official_parent_chain_members': chain,
            'loadout_body_members': actor_bodies, 'body_visual_weapon_links': visual_rows,
            'attachment_list_members': sorted(attachments),
            'animator_asset_refs': sorted(animator_assets), 'model_asset_refs': sorted(model_refs),
            'material_refs_in_decoded_RGD': sorted(material_refs),
            'material_scope_note': 'No material file path was present in the decoded attachment-list RGD values scanned; this does not prove the referenced model lacks materials.'})
    return result


def compiled_diagnostic_052_building_lists(inv, closure):
    """Decode matching 0.5.2 diagnostic building RGDs as source-parity evidence only."""
    external = Path(CFG['external_root'])
    release052 = external / 'output' / 'release_052'
    freeze060_path = OUT / 'baseline' / 'preparation-freeze.json'
    freeze052_path = release052 / 'baseline' / 'freeze.json'
    receipt_path = release052 / 'diagnostic-b' / 'receipt.json'
    package_path = release052 / 'diagnostic-b' / 'package-verification.json'
    freeze060, freeze052 = read(freeze060_path), read(freeze052_path)
    assets060 = freeze060['inputs']['assets']
    assets052 = freeze052['inputs']['assets']
    parity = sorted(path for path in set(assets060) | set(assets052)
                    if assets060.get(path) != assets052.get(path))
    if parity:
        raise RuntimeError(f'0.5.2 diagnostic source parity failed for {len(parity)} frozen assets')
    receipt, package = read(receipt_path), read(package_path)
    archive = Path(receipt['archive'])
    if receipt.get('status') != 'passed_diagnostic_package_preparation' or receipt.get('is_final_release'):
        raise RuntimeError('Retained 0.5.2 archive is not the expected diagnostic-only artifact')
    if sha(archive) != receipt['archive_sha256'] or receipt['archive_sha256'] != package['sga_sha256']:
        raise RuntimeError('Retained diagnostic SGA hash does not match its receipt and package verification')
    zip_path = Path(package['zip'])
    if sha(zip_path) != package['zip_sha256']:
        raise RuntimeError('Retained diagnostic ZIP hash does not match package verification')
    indexed = json.loads(subprocess.run([str(ARCH), 'list', str(archive)],
        check=True, capture_output=True, text=True, timeout=180).stdout)
    member_index = {row['path'].lower(): row for row in indexed.get('members', [])}
    if not receipt.get('all_other_members_byte_identical'):
        raise RuntimeError('Diagnostic receipt does not attest byte identity for unchanged SGA members')
    if receipt.get('unchanged_members') != len(member_index) - len(receipt.get('changed_members', [])):
        raise RuntimeError('Diagnostic receipt unchanged-member count does not reconcile to archive index')
    changed_members = {str(x).lower() for x in receipt.get('changed_members', [])}
    if any(name not in member_index for name in changed_members):
        raise RuntimeError('Diagnostic receipt changed-member list contains absent SGA members')

    building_actors = sorted(set(inv.get('reachable_building_actor_ids', [])))
    producer_actors = sorted({row['id'] for row in inv.get('units_and_entities', [])
                              if row.get('id') and row.get('reachability') == 'confirmed_starting_or_tier_chain'})
    actors = [(actor_id, 'reached_local_building') for actor_id in building_actors]
    actors.extend((actor_id, 'confirmed_local_starting_or_tier_producer')
                  for actor_id in producer_actors)
    if not building_actors:
        raise RuntimeError('No reached local building actors were available for compiled-list reconciliation')

    cache = owned(OUT / 'inventory' / 'compiled_052_diagnostic_b' / receipt['archive_sha256'])
    raw_root, decoded_root = owned(cache / 'raw'), owned(cache / 'decoded')
    raw_root.mkdir(parents=True, exist_ok=True)
    decoded_root.mkdir(parents=True, exist_ok=True)
    compiled_rows = []
    replaced_actor_ids = []
    inherited_candidates = closure.get('inherited_native_spawn_item_candidates', [])
    for actor_id, actor_role in actors:
        member = 'attrib/' + actor_id.replace('\\', '/').lower() + '.rgd'
        member_meta = member_index.get(member)
        if not member_meta:
            source_rel = 'attrib/instances/' + actor_id.replace('\\', '/') + '.xml'
            source_file = Path(inv['source']['path']) / source_rel
            source_sha = sha(source_file)
            if assets060.get(source_rel, {}).get('sha256') != source_sha:
                raise RuntimeError(f'Frozen source file changed after 0.6 preparation: {source_rel}')
            compiled_rows.append({'actor_id': actor_id, 'actor_role': actor_role,
                'source_file': source_rel, 'source_sha256': source_sha,
                'matching_052_frozen_source_sha256': assets052[source_rel]['sha256'],
                'source_hash_parity': source_sha == assets052[source_rel]['sha256'],
                'compiled_member': member, 'compiled_member_present': False,
                'compiled_member_absence_reason': 'not present in retained diagnostic SGA index',
                'variants': {}, 'local_parent_defaults_replaced_in_compiled_child': False})
            continue
        relative = Path(member)
        raw_file = owned(raw_root / relative)
        decoded_file = owned(decoded_root / relative.with_suffix('.xml'))
        if not raw_file.is_file():
            subprocess.run([str(ARCH), 'extract', str(archive), str(raw_root),
                            '--member', member], check=True, capture_output=True,
                           text=True, timeout=180)
        if not decoded_file.is_file():
            result = subprocess.run([str(ARCH), 'decode-rgd', str(raw_file), str(decoded_file)],
                                    check=True, capture_output=True, text=True, timeout=60)
            if json.loads(result.stdout).get('schema') != 'sga-archiver.decode-rgd/v1':
                raise RuntimeError(f'Unexpected RGD decoder contract for {member}')
        source_rel = 'attrib/instances/' + actor_id.replace('\\', '/') + '.xml'
        source_file = Path(inv['source']['path']) / source_rel
        source_sha = sha(source_file)
        if assets060.get(source_rel, {}).get('sha256') != source_sha:
            raise RuntimeError(f'Frozen source file changed after 0.6 preparation: {source_rel}')
        local_root = ET.parse(source_file).getroot()
        local_lists = defaultdict(list)
        for element, xpath in iter_with_paths(local_root):
            if element.tag != 'list' or element.attrib.get('name') != 'spawn_items':
                continue
            variant = 'campaign' if variant_for(xpath).lower() == 'campaign' else 'base'
            for group in element.findall("./group[@name='spawn_item']"):
                refs = [node.attrib.get('value', '') for node in group.iter('instance_reference')
                        if node.attrib.get('name') in {'squad', 'entity'} and node.attrib.get('value')]
                local_lists[variant].extend(refs)
            local_lists.setdefault(variant, [])

        rgd_root = ET.parse(decoded_file).getroot()
        compiled_lists = defaultdict(list)
        for branch in rgd_root.findall('./RGDNode'):
            branch_key = branch.attrib.get('Key', '').lower()
            if branch_key not in {'default', 'campaign'}:
                continue
            variant = 'campaign' if branch_key == 'campaign' else 'base'
            for spawn_list in branch.iter('RGDNode'):
                if spawn_list.attrib.get('Key') != 'spawn_items' or spawn_list.attrib.get('Type') != 'List':
                    continue
                for item in spawn_list.findall("./RGDNode[@Key='spawn_item'][@Type='List']"):
                    refs = {}
                    for ref_name in ('squad', 'entity'):
                        ref = item.find(f"./RGDNode[@Key='{ref_name}']")
                        if ref is None:
                            continue
                        values = {n.attrib.get('Key'): n.attrib.get('Value', '') for n in ref.findall('./RGDNode')}
                        if values.get('$PBGNAME'):
                            refs[ref_name] = {'pbg_name': values['$PBGNAME'], 'pbg_map': values.get('$PBGMAP', '')}
                    number_node = item.find("./RGDNode[@Key='number_to_spawn']")
                    if refs:
                        compiled_lists[variant].append({'actor_ref': refs,
                            'number_to_spawn': number_node.attrib.get('Value') if number_node is not None else None,
                            'requirements': sorted({n.attrib.get('Value', '') for n in item.iter('RGDNode')
                                if n.attrib.get('Key') == '$REF' and n.attrib.get('Value', '').startswith('requirements')})})

        variant_records = {}
        actor_replacement_proven = bool(local_lists)
        for variant in sorted(set(local_lists) | set(compiled_lists)):
            source_expected = local_lists.get(variant)
            if source_expected is not None:
                source_expected = list(source_expected)
            compiled_refs = [
                ref.get('pbg_name', '').split(':', 1)[-1].rsplit('\\', 1)[-1]
                for item in compiled_lists.get(variant, [])
                for ref in item['actor_ref'].values()]
            source_refs_normalized = [value.split(':', 1)[-1].rsplit('\\', 1)[-1]
                                      for value in (source_expected or [])]
            local_spawn_lists = []
            for element, xpath in iter_with_paths(local_root):
                if element.tag == 'list' and element.attrib.get('name') == 'spawn_items' and (
                    ('campaign' if variant_for(xpath).lower() == 'campaign' else 'base') == variant):
                    local_spawn_lists.append(element)
            states = [{'overrideParent': element.attrib.get('overrideParent'),
                       'item_count': len(element.findall("./group[@name='spawn_item']"))}
                      for element in local_spawn_lists]
            override = bool(states) and all(x['overrideParent'] == 'True' for x in states)
            matches = source_expected is not None and compiled_refs == source_refs_normalized
            if source_expected is None:
                semantic = ('compiled_parent_list_entries_present' if compiled_refs
                            else 'no_compiled_spawn_items')
            elif override and matches:
                semantic = 'explicit_child_list_override_matches_compiled_list_parent_defaults_replaced'
            elif matches:
                semantic = 'child_list_matches_compiled_list_item_merge_semantics_retained'
            else:
                semantic = 'source_compiled_list_relation_unresolved'
            if source_expected is not None and (not override or not matches):
                actor_replacement_proven = False
            variant_records[variant] = {'source_list_state': 'absent' if source_expected is None else ('populated' if source_expected else 'present_empty'),
                'source_list_attributes': states, 'source_actor_refs': source_expected,
                'compiled_actor_refs': compiled_lists.get(variant, []),
                'compiled_ref_names_normalized': compiled_refs,
                'source_compiled_refs_equal_in_order': matches,
                'semantic_status': semantic}
        expected_native = sorted({row['target_id'] for row in inherited_candidates
                                  if row.get('local_actor_id') == actor_id and row.get('target_id')})
        compiled_names = sorted({ref.get('pbg_name', '').split(':', 1)[-1]
            for rows in compiled_lists.values() for item in rows for ref in item['actor_ref'].values()})
        source_parents = [node.attrib.get('value', '') for node in local_root.iter('instance_reference')
                          if node.attrib.get('name') == 'parent_pbg']
        if actor_replacement_proven:
            replaced_actor_ids.append(actor_id)
        compiled_rows.append({'actor_id': actor_id, 'actor_role': actor_role,
            'source_file': source_rel,
            'source_sha256': source_sha, 'matching_052_frozen_source_sha256': assets052[source_rel]['sha256'],
            'source_hash_parity': source_sha == assets052[source_rel]['sha256'],
            'source_parent_pbg_refs': source_parents, 'compiled_member': member,
            'compiled_member_present': True,
            'compiled_raw_path': raw_file.as_posix(), 'decoded_xml_path': decoded_file.as_posix(),
            'compiled_member_sga_sha1_metadata': member_meta.get('verification'),
            'compiled_raw_sha256': sha(raw_file), 'compiled_raw_bytes': raw_file.stat().st_size,
            'decoded_xml_sha256': sha(decoded_file), 'variants': variant_records,
            'native_parent_candidate_ids': expected_native,
            'compiled_names_matching_native_candidates': sorted(set(compiled_names) & {x.rsplit('\\', 1)[-1] for x in expected_native}),
            'local_parent_defaults_replaced_in_compiled_child': actor_replacement_proven})

    # Reconcile candidates with the source-parity compiled child list. For
    # overrideParent=True children the local list replaces parent defaults. For
    # absent child lists, keep only native parent entries actually serialized
    # in the compiled child RGD (e.g. Monk III and Trade Cart).
    roster = {row['id']: row for row in inv.get('official_actor_roster_candidates', [])}
    removed_links = []
    compiled_by_actor = {row['actor_id']: row for row in compiled_rows}
    for target, row in list(roster.items()):
        retained = []
        for edge in row.get('relation_evidence', []):
            if edge.get('relation') != 'inherited_native_parent_spawn_item' or edge.get('source_id') not in compiled_by_actor:
                retained.append(edge)
                continue
            actor = compiled_by_actor[edge['source_id']]
            if not actor.get('compiled_member_present'):
                edge['compiled_list_qualification'] = 'unresolved_compiled_actor_member_absent'
                retained.append(edge)
                continue
            compiled_names = {ref.get('pbg_name', '').split(':', 1)[-1].rsplit('\\', 1)[-1]
                for data in actor['variants'].values()
                for item in data['compiled_actor_refs'] for ref in item['actor_ref'].values()}
            target_name = target.rsplit('\\', 1)[-1]
            if actor['local_parent_defaults_replaced_in_compiled_child'] or target_name not in compiled_names:
                removed_links.append({'target_id': target, **edge,
                    'reason': ('compiled child spawn_items is an explicit override matching the frozen local list'
                               if actor['local_parent_defaults_replaced_in_compiled_child']
                               else 'native parent candidate is absent from the source-parity compiled child spawn_items')})
            else:
                edge['compiled_list_qualification'] = 'compiled_child_contains_native_parent_item'
                edge['compiled_list_evidence'] = {
                    'diagnostic_sga_sha256': receipt['archive_sha256'],
                    'source_hash_parity': actor['source_hash_parity'],
                    'compiled_member': actor['compiled_member'],
                    'compiled_raw_sha256': actor['compiled_raw_sha256'],
                    'decoded_xml_sha256': actor['decoded_xml_sha256'],
                    'compiled_variants': sorted(actor['variants']),
                    'runtime_and_item_gates': 'unverified'}
                retained.append(edge)
        row['relation_evidence'] = retained
        if not retained:
            del roster[target]
    inv['official_actor_roster_candidates'] = [roster[k] for k in sorted(roster)]
    return {'schema': 'community-civilization-pack.release060.compiled-052-diagnostic-spawner-evidence/v1',
        'status': 'source_parity_confirmed_diagnostic_compiled_lists_only',
        'diagnostic_version': '0.5.2-diagnostic-b', 'diagnostic_is_final_release': False,
        'diagnostic_sga': archive.as_posix(), 'diagnostic_sga_sha256': receipt['archive_sha256'],
        'diagnostic_zip': zip_path.as_posix(), 'diagnostic_zip_sha256': package['zip_sha256'],
        'diagnostic_receipt': receipt_path.as_posix(), 'diagnostic_receipt_sha256': sha(receipt_path),
        'package_verification': package_path.as_posix(), 'package_verification_sha256': sha(package_path),
        'baseline_sga_sha256': receipt.get('baseline_sga_sha256'),
        'archive_tool': ARCH.as_posix(), 'archive_tool_sha256': sha(ARCH),
        'official_attrib_sha256': closure.get('official_attrib_sha256'),
        'source_parity': {'060_freeze': freeze060_path.as_posix(), '052_freeze': freeze052_path.as_posix(),
            'asset_file_count_060': len(assets060), 'asset_file_count_052': len(assets052),
            'mismatched_paths': parity, 'all_314_frozen_asset_hashes_and_sizes_match': not parity},
        'unchanged_member_evidence': {'diagnostic_receipt_all_other_members_byte_identical': receipt['all_other_members_byte_identical'],
            'diagnostic_receipt_unchanged_member_count': receipt['unchanged_members'],
            'diagnostic_archive_index_member_count': len(member_index),
            'diagnostic_receipt_changed_member_count': len(changed_members),
            'diagnostic_baseline_sga_sha256': receipt['baseline_sga_sha256'],
            'reconciliation': 'receipt unchanged count equals indexed members minus receipt changed members; changed member names all exist in SGA index'},
        'compiled_building_lists': [row for row in compiled_rows if row['actor_role'] == 'reached_local_building'],
        'compiled_producer_lists': [row for row in compiled_rows if row['actor_role'] != 'reached_local_building'],
        'replaced_local_building_parent_defaults': replaced_actor_ids,
        'removed_candidate_links': removed_links,
        'limits': 'The 0.5.2 diagnostic SGA is used only as a compiled-data probe because all 314 frozen source asset paths, SHA-256 values, and byte sizes match the 0.6 preparation freeze. It is not the 0.6 integration baseline, not a final package, and does not prove native runtime availability or item-gate eligibility.'}


def markdown(inv):
    c = inv['coverage']
    lines = [
        '# Release 0.6.0 Vietnamese Land Unit Inventory', '',
        'Static inventory of the frozen editable snapshot. This is not a native runtime roster proof.', '',
        f"- Source snapshot: `{inv['source']['path']}`",
        f"- XML instances indexed: {inv['source']['xml_instance_count']}",
        f"- Source manifest SHA-256: `{inv['source']['instance_manifest_sha256']}`",
        f"- Source-confirmed local unit/entity records through starting, construction, production, and tier paths: {c['local_confirmed_unit_or_entity_ids']} ({c['local_confirmed_squad_ids']} squads, {c['local_confirmed_entity_ids']} entities)",
        f"- Local candidates with unresolved actor activation: {c['unresolved_candidate_local_unit_or_entity_ids']}",
        f"- Local Vietnamese squads with no starting/spawn/tier path in this snapshot: {c['unlinked_local_vietnam_squad_blueprints']}",
        f"- Local Vietnamese unit entities with no starting/spawn/tier path in this snapshot: {c['unlinked_local_vietnam_unit_entities']}",
        f"- Starting-force refs: {c['starting_refs']} occurrences ({c['local_starting_squad_ids']} unique local IDs; {len(c['external_starting_refs'])} unique external IDs)",
        f"- Ambient animal entries retained for accounting but excluded from art: {sum(1 for x in inv['army']['starting_units'] if x['classification'].startswith('excluded_'))}",
        f"- Starting villager buildable actor refs: {c['reachable_buildable_actor_refs']} ({c['reachable_local_building_actor_ids']} local reachable building actors)",
        f"- Spawn-item references on reached building actors: {c['reachable_actor_spawn_refs']} / {c['building_spawn_candidate_refs']} total actor entries; gate evaluation remains separate",
        f"- Exact-current-Attrib stock actor IDs referenced by local spawn/construction or native parent-list candidates: {len(inv.get('official_actor_roster_candidates', []))}; parent-list merge and item gates remain unverified",
        f"- Native parent spawn-item candidates across reached building parent chains: {len(inv.get('inherited_native_spawn_item_candidates', []))} item/variant rows; {len({x.get('target_id') for x in inv.get('inherited_native_spawn_item_candidates', []) if x.get('land_scope') == 'land_candidate'})} unique land-scope actor IDs and {len({x.get('target_id') for x in inv.get('inherited_native_spawn_item_candidates', []) if x.get('land_scope') == 'excluded_non_land'})} unique non-land IDs",
        (f"- Source-matching diagnostic compiled evidence: {sum(bool(x.get('compiled_member_present')) for x in inv['compiled_building_list_evidence']['compiled_building_lists'])}/{len(inv['compiled_building_list_evidence']['compiled_building_lists'])} reached local buildings and {sum(bool(x.get('compiled_member_present')) for x in inv['compiled_building_list_evidence']['compiled_producer_lists'])}/{len(inv['compiled_building_list_evidence']['compiled_producer_lists'])} confirmed local starting/tier producers indexed; {len(inv['compiled_building_list_evidence']['removed_candidate_links'])} parent-list links excluded by compiled child data; {len(inv.get('official_actor_roster_candidates', []))} stock actor IDs remain linked to effective/candidate production." if inv.get('compiled_building_list_evidence') else '- No retained diagnostic compiled-list comparison was run.'),
        f"- Vietnamese landmark actor IDs reached through construction menus: {len(inv['landmark_unlock_evidence']['buildable_landmark_actor_ids'])}",
        f"- External/unresolved outgoing refs in reached closure: {c['external_or_unresolved_closure_refs']}",
        f"- Current official Attrib.sga: {inv['official_archive_resolution']['status']}; {inv['official_archive_resolution'].get('member_count', 0)} members; {inv['official_archive_resolution']['unique_external_ids_found_by_exact_rgd_path']} unique external identifiers have exact RGD paths; {len(inv['official_archive_resolution']['refs_absent_from_official_archive'])} referenced RGD paths are absent.",
        f"- Non-RGD contract references: {inv['official_archive_resolution']['non_rgd_contract_breakdown']['options']} option/template refs and {inv['official_archive_resolution']['non_rgd_contract_breakdown']['attachment_templates']} attachment-template refs; these are not missing official RGD members.",
        (f"- Selectively decoded current official closure: {inv['native_rgd_closure']['decoded_member_count']} RGD members from Attrib SHA-256 `{inv['native_rgd_closure']['official_attrib_sha256']}`; {len(inv['native_rgd_closure']['parent_edges'])} exact parent links, {len(inv['native_rgd_closure']['squad_loadout_body_edges'])} exact squad-to-body links, and {len(inv['native_rgd_closure']['entity_visual_attachment_and_weapon_links'])} exact EBP visual/weapon attachment links; unresolved counts are {len(inv['native_rgd_closure']['unresolved_parent_edges'])} parent, {len(inv['native_rgd_closure']['unresolved_squad_loadout_body_edges'])} squad body, and {len(inv['native_rgd_closure']['unresolved_entity_visual_links'])} EBP visual links. See `{inv['native_rgd_closure_manifest']}`." if inv.get('native_rgd_closure') else '- Current official RGD decoding has not been run.'),
        f"- Parse errors: {c['source_parse_errors']}", '',
        '## Coverage boundary', '',
        'The local chain begins at the Vietnamese army starting squads and building. `initialization.scar` selects and converts the native starting Town Center plus its villagers/scout to private Vietnam blueprints. Starting-villager squad `construction_groups` point to local production and landmark actors; their `spawn_items` point to local unit squads/entities. The army XML production-building list is explicitly empty and the local army has no `parent_pbg`; therefore no Chinese army production-building set is inferred. For every reached local building, the official parent chain is scanned for exact native `spawn_items`, whether the local child list is absent, empty, or populated. Parent values stay conditional candidates unless source list semantics and source-matching compiled data resolve them; age/resource/requirement gates and runtime availability remain separate.', '',
        'External stock references and unresolved official parent inheritance remain listed rather than inferred. The stock Abbey King stays a candidate because its owner (`vn_building_landmark_age3_new_imperial_garden`) is not in the starting-villager reachable buildable actor set; its presence in a spawn list alone does not make it obtainable. Consult the JSON ledger for every reference path, variant, list item ID, mod marker, actor tier target, attachment, weapon, ability, and official closure item.', '',
    ]
    compiled = inv.get('compiled_building_list_evidence')
    if compiled:
        parity = compiled['source_parity']
        lines += ['## Compiled spawner-list evidence (diagnostic only)', '',
            f"The retained `{compiled['diagnostic_version']}` archive was used only because all {parity['asset_file_count_060']} frozen source assets match the 0.6 snapshot by path, SHA-256, and byte size. The diagnostic SGA SHA-256 is `{compiled['diagnostic_sga_sha256']}`; its verified ZIP SHA-256 is `{compiled['diagnostic_zip_sha256']}`. This is not a final package or 0.6 integration baseline.", '',
            '| Reached local actor | Variant | Source list | overrideParent | Compiled item count | Interpretation |',
            '|---|---|---|---|---|---|']
        for actor in compiled['compiled_building_lists']:
            for variant, data in sorted(actor['variants'].items()):
                item_count = len(data['compiled_actor_refs'])
                attrs = ','.join(str(x.get('overrideParent')) for x in data['source_list_attributes']) or 'no local list'
                lines.append(f"| `{actor['actor_id']}` | {variant} | {data['source_list_state']} | {attrs} | {item_count} | {data['semantic_status']} |")
        absent_buildings = [x['actor_id'] for x in compiled['compiled_building_lists'] if not x.get('compiled_member_present')]
        absent_producers = [x['actor_id'] for x in compiled['compiled_producer_lists'] if not x.get('compiled_member_present')]
        lines += ['',
            f"The archive index lists {compiled['unchanged_member_evidence']['diagnostic_archive_index_member_count']} SGA members. The retained diagnostic receipt says {compiled['unchanged_member_evidence']['diagnostic_receipt_unchanged_member_count']} unchanged members are byte-identical to baseline, and this count reconciles against the {compiled['unchanged_member_evidence']['diagnostic_receipt_changed_member_count']} named changed members. Source parity is independently checked against all frozen asset paths, hashes, and sizes. This establishes a source-matched compiled-data probe, not an engine runtime proof.",
            f"Compiled members absent for reached buildings: {', '.join(f'`{x}`' for x in absent_buildings) or 'none'}. Compiled members absent for confirmed local producers: {', '.join(f'`{x}`' for x in absent_producers) or 'none'}. Absent members remain unresolved and are not used to delete inherited candidates.",
            'The exact effective compiled spawn lists show the retained production actors, including stock Monk III from the monastery and Trade Cart from the private market when serialized in the compiled child. Local child overrides are reconciled per actor and variant. These static lists do not evaluate all item requirements, age, resource, map-mode, or runtime availability.', '']
        lines += ['', '## Local spawn items and eligibility evidence', '',
            'Rows below preserve source actor, target, variant, item XPath, spawn count, resource costs, and linked upgrade references. UI menu references are not interpreted as locks. This source inventory records gate data but does not statically solve all engine requirement trees; unproven age or eligibility remains explicit.', '',
            '| Producer | Variant | Unit/squad target | Count | Costs (F/W/S/G) | Linked upgrade refs |',
            '|---|---|---|---:|---|---|']
        seen_items = set()
        for item in inv.get('reachable_actor_spawn_refs', []):
            context = item.get('spawn_item_context', {})
            target = item['target']
            identity = (item['source_id'], item['variant'], target, item['xpath'])
            if identity in seen_items:
                continue
            seen_items.add(identity)
            refs = context.get('reference_requirements', [])
            linked = [f"{r.get('value')} ({r.get('xpath')})" for r in refs if r.get('name') == 'linked']
            costs = '/'.join(context.get(name, '?') for name in ('food', 'wood', 'stone', 'gold'))
            count = context.get('number_to_spawn', '?')
            lines.append(f"| `{item['source_id']}` | {item['variant']} | `{target}` | {count} | {costs} | {'; '.join(f'`{x}`' for x in linked) or 'none serialized'} |")
        lines += ['',
            f"Source provides {len(seen_items)} local producer-item records across {len({x['source_id'] for x in inv.get('reachable_actor_spawn_refs', [])})} reached building actors. Exact source XPaths, requirement references, and all scalar item fields are in the JSON ledger. Starting units are separately anchored to `army/vietnam/vn_normal_chinese` and the `initialization.scar` TC conversion. Age, technology, player-state, and native runtime gates not directly resolved from these item records remain `unknown/not evaluated`; no candidate is promoted to runtime-available from UI or observer metadata.", '']
    lines += [
        '## Unit and entity records', '',
        'This art-scope ledger records exact local parent, tier, weapon, and attachment-list targets. Variants and exact source paths remain in JSON.', '',
        '| Kind | Local blueprint | Native parent(s) | Tier target(s) | Weapon ref(s) | Attachment-list ref(s) | Ability ref(s) |',
        '|---|---|---|---|---|---|---|',
    ]
    for row in inv['units_and_entities']:
        def targets(field):
            return ', '.join(f"`{value}`" for value in sorted({x.get('target', '') for x in row.get(field, []) if x.get('target')})) or '—'
        parents = ', '.join(f"`{x.get('target', '')}`" for x in row.get('parent_refs', []) if x.get('target')) or '—'
        lines.append(f"| {row['kind']} | `{row['id']}` | {parents} | {targets('tier_targets')} | {targets('weapon_refs')} | {targets('attachments')} | {targets('ability_refs')} |")
    lines += ['', '## Rattan cross-check', '',
              'The inventory records `vn_ratten_shield_vit` as the applied upgrade and keeps `vn_upgrade_rattan_shields_vit` separate. The six plan-listed actor tiers are archer II/III/IV, crossbow III/IV, and handcannon IV. Elephants are not included in that armor upgrade scope.', '',
        '## Reachable local squad families and tiers', '',
    ]
    for family in inv.get('representative_art_scope', {}).get('source_confirmed_local_squad_families', []):
        tier_text = ', '.join(str(t) for t in family['tiers']) or 'no numeric tier'
        variants = ', '.join(x['id'].rsplit('\\', 1)[-1] for x in family['variants_and_ids'])
        lines.append(f"- `{family['family']}`: tiers {tier_text} ({variants})")
    lines += ['', '## Native stock bodies and visual references', '']
    for actor in inv.get('native_actor_visual_summary', []):
        body_names = ', '.join(x.rsplit('/', 1)[-1].removesuffix('.rgd') for x in actor['loadout_body_members']) or 'entity body'
        animator_names = ', '.join(actor['animator_asset_refs']) or 'not explicit in selected attachment-list RGD'
        weapon_names = ', '.join(sorted({x['pbg_name'] for x in actor['body_visual_weapon_links']
                                         if x.get('pbg_map') == 'weapon'})) or 'none recorded'
        lines.append(f"- `{actor['id']}` ({actor['reachability_status']}): body `{body_names}`; animator `{animator_names}`; weapons `{weapon_names}`; decoded RGD material refs {len(actor['material_refs_in_decoded_RGD'])}.")
    lines += ['', '## Native parent production candidates', '',
        '| Reachable local building | Exact official parent RGD | Native RGD XPath | Native spawn actor | Local variant | Child list | Parent depth | Land scope |',
        '|---|---|---|---|---|---|---:|---|']
    seen_production = set()
    for edge in inv.get('inherited_native_spawn_item_candidates', []):
        key_tuple = (edge['local_actor_id'], edge['target_id'], edge['local_variant'], edge['source_member'], edge.get('native_parent_depth'), edge['land_scope'])
        if key_tuple in seen_production:
            continue
        seen_production.add(key_tuple)
        lines.append(f"| `{edge['local_actor_id']}` | `{edge['source_member']}` | `{edge.get('native_source_xpath', 'n/a')}` | `{edge['target_id']}` | {edge['local_variant']} | {edge.get('child_spawn_list_state', 'unknown')} | {edge.get('native_parent_depth', 0)} | {edge['land_scope']} |")
    official_effective_targets = {x['id'] for x in inv.get('official_actor_roster_candidates', [])}
    monk_targets = [x for x in sorted(official_effective_targets) if 'monk' in x.rsplit('\\', 1)[-1].lower()]
    trade_targets = [x for x in sorted(official_effective_targets) if 'trade' in x.rsplit('\\', 1)[-1].lower() or 'cart' in x.rsplit('\\', 1)[-1].lower()]
    official_status = ('candidate only; no effective reached local compiled production edge' if not any('official' in x.rsplit('\\', 1)[-1].lower() for x in official_effective_targets)
                       else 'linked by compiled/source production evidence; item gates unresolved')
    lines += ['', f"Monk candidate IDs retained after compiled-list reconciliation: {', '.join(f'`{x}`' for x in monk_targets) or 'none'}. Trader/cart candidates retained: {', '.join(f'`{x}`' for x in trade_targets) or 'none'}. Imperial Official status: {official_status}; a precache-only local/private RDO reference remains non-production evidence. Body/animator/model links above are exact RGD references; zero decoded RGD material paths means the asset/material archive closure is not established by this report.", '', '## Evidence limits', '',
        'The installed Garrison SGA tool read-only indexed and selectively decoded the current official `Attrib.sga` RGD closure under its exact SHA-256. Decoded parent, squad-body, weapon, visual attachment, inherited parent spawn-item, source-parity diagnostic compiled lists, and unchanged-member receipt evidence are retained in hash-keyed manifests. Decoded RGD is evidence only, not editable tuning XML. Item age/technology/resource requirement trees are not fully evaluated, and no source data establishes runtime availability. RDO/SCAR precache references are not treated as production. Package/import/native-match acceptance remains separate.', '']
    return '\n'.join(lines)


def run(source_root: Path, decode_official_rgd: bool = False):
    guard()
    inv = make_inventory(source_root.resolve())
    inv['official_actor_roster_candidates'] = official_actor_roster_candidates(inv)
    out = OUT / 'inventory'
    if decode_official_rgd:
        closure = extract_official_rgd_closure(inv)
        manifest_path = out / f"official_rgd_closure_{closure['official_attrib_sha256']}.json"
        write(manifest_path, closure)
        inherited = closure['inherited_native_spawn_item_candidates']
        inv['inherited_native_spawn_item_candidates'] = inherited
        inv['unresolved_inherited_native_spawn_items'] = closure['unresolved_inherited_native_spawn_items']
        roster = {row['id']: row for row in inv['official_actor_roster_candidates']}
        for edge in inherited:
            target = edge.get('target_id')
            if not target or not edge.get('official_member_present'):
                continue
            if edge.get('land_scope') != 'land_candidate':
                continue
            row = roster.setdefault(target, {'id': target, 'category': target.split('\\', 1)[0],
                'expected_member_path': edge['expected_member_path'], 'relation_evidence': [],
                'item_gate_evaluation': 'not_evaluated'})
            row['relation_evidence'].append({'relation': 'inherited_native_parent_spawn_item',
                'source_id': edge['local_actor_id'], 'source_file': edge['source_file'],
                'variant': edge['local_variant'], 'native_parent_member': edge['source_member'],
                'native_spawn_item_reference': edge['native_spawn_item_reference'],
                'native_source_xpath': edge.get('native_source_xpath'),
                'child_spawn_list_state': edge.get('child_spawn_list_state'),
                'native_parent_depth': edge.get('native_parent_depth'),
                'list_merge_semantics': edge['list_merge_semantics']})
        inv['official_actor_roster_candidates'] = [roster[k] for k in sorted(roster)]
        local_official_squad = next((x for x in inv['unlinked_local_vietnam_squads']
                                     if x['id'] == r'sbps\vietnam\vn_unit_official_1_chi'), None)
        local_official_entity = next((x for x in inv['unlinked_local_vietnam_unit_entities']
                                      if x['id'] == r'ebps\vietnam\vn_unit_official_1_chi'), None)
        rdo_path = source_root / 'scar' / 'winconditions' / 'VietnamMode.rdo'
        rdo_text = rdo_path.read_text(encoding='utf-8-sig') if rdo_path.is_file() else ''
        inv['candidate_only_actor_refs'] = [
            {'id': r'sbps\races\chinese\unit_official_1_chi',
             'expected_member_path': 'attrib/sbps/races/chinese/unit_official_1_chi.rgd',
             'classification': 'candidate_only_native_actor_not_source_reachable',
             'evidence': 'Exact current native RGD exists, but no reached local spawn/construction/ability edge points to it.'},
            {'id': local_official_squad['id'] if local_official_squad else r'sbps\vietnam\vn_unit_official_1_chi',
             'entity_id': local_official_entity['id'] if local_official_entity else r'ebps\vietnam\vn_unit_official_1_chi',
             'classification': 'unlinked_local_blueprint_precache_only',
             'rdo_precache_reference_occurrences': rdo_text.count('vn_unit_official_1_chi'),
             'evidence': 'No reachable local production/spawn/ability edge; RDO references occur in precache records and do not establish production.'},
        ]
        compiled_evidence = compiled_diagnostic_052_building_lists(inv, closure)
        compiled_manifest = out / f"compiled_052_diagnostic_b_{compiled_evidence['diagnostic_sga_sha256']}.json"
        write(compiled_manifest, compiled_evidence)
        inv['compiled_building_list_evidence'] = compiled_evidence
        inv['compiled_building_list_manifest'] = compiled_manifest.as_posix()
        inv['representative_art_scope'] = {
            'source_confirmed_local_squad_families': squad_family_tiers(
                [row for row in inv['units_and_entities'] if row['category'] == 'sbps']),
            'unlinked_local_candidate_squad_families': squad_family_tiers(inv['unlinked_local_vietnam_squads']),
            'native_stock_land_actor_candidate_ids': [row['id'] for row in inv['official_actor_roster_candidates']],
            'limits': 'Family/tier grouping summarizes source-confirmed local squads and exact official stock actor references; it is not an engine eligibility or visual-completeness claim.'}
        inv['native_actor_visual_summary'] = native_actor_visual_summary(inv, closure, OUT)
        inv['native_rgd_closure'] = {k: closure[k] for k in (
            'official_attrib_sha256', 'seed_member_count', 'decoded_member_count',
            'parent_edges', 'unresolved_parent_edges', 'squad_loadout_body_edges',
            'unresolved_squad_loadout_body_edges',
            'entity_visual_attachment_and_weapon_links', 'unresolved_entity_visual_links',
            'inherited_native_spawn_item_candidates', 'unresolved_inherited_native_spawn_items',
            'reachable_building_parent_spawn_scans', 'limits')}
        inv['native_rgd_closure_manifest'] = manifest_path.as_posix()
    write(out / 'land_units.json', inv)
    report = out / 'land_units.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(markdown(inv), encoding='utf-8')
    return inv, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--decode-official-rgd', action='store_true',
                        help='extract and decode the hash-pinned official RGD closure into the owned inventory output')
    args = parser.parse_args(argv)
    inv, report = run(args.source_root, args.decode_official_rgd)
    print(f"inventory={OUT / 'inventory' / 'land_units.json'}")
    print(f'report={report}')
    print(f"confirmed={inv['coverage']['local_confirmed_unit_or_entity_ids']} "
          f"starting={inv['coverage']['starting_refs']} "
          f"spawn_candidates={inv['coverage']['building_spawn_candidate_refs']} "
          f"external={inv['coverage']['external_or_unresolved_closure_refs']}")
    return 0 if not inv['source']['parse_errors'] else 2


if __name__ == '__main__':
    raise SystemExit(main())

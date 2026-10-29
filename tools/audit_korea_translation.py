"""Compare all migrated tuning values and donor SCAR dispatch routes read-only.

Requires the preserved donor only for this audit; ordinary builds do not.
Identity metadata is audited separately by the inherited-extension checker.
"""
import argparse
import collections
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def values(tree):
    result = {}
    def visit(node, path):
        if node.tag == 'uniqueid':
            return
        if 'value' in node.attrib:
            result[path] = node.get('value')
        seen = collections.Counter()
        for child in node:
            token = child.tag + ':' + child.get('name', '')
            seen[token] += 1
            visit(child, path + '/' + token + '[' + str(seen[token]) + ']')
    visit(tree, '')
    return result


def audit(source, official_cache):
    ledger = json.loads((ROOT/'docs/korea-import.json').read_text())
    construction = {row['blueprint']: row for row in
                    json.loads((ROOT/'docs/korea-construction.json').read_text())['changes']}
    paths = {row['source']: row['private'] for row in ledger['instances']}
    aliases = {(k.split('\\')[0], k.split('\\')[-1]): k for k in paths}
    icons = set(ledger['icons'])
    official = json.loads(official_cache.read_text(encoding='utf-8'))
    defaults = {
        ('enum', 'statetree_tier_requirements_pbg_owner'): 'player',
        ('bool', 'available_production_count_is_shared'): 'False',
        ('enum', 'available_production_count_statemodel'): '',
        ('state_tree_node', 'cost_openingbranch'): '',
        ('enum', 'targeting_and_bandbox_selection_priority_controller'): '',
        ('bool', 'force_square_attack'): 'False',
        ('float', 'critical_damage_chance'): '0.02',
        ('float', 'critical_damage_factor'): '5',
        ('bool', 'trade_only_economical_rally'): 'False',
        ('bool', 'destroy_stamps'): 'True',
        ('bool', 'on_loaded_squad_action_tree_reapply_on_bp_conversion'): 'False'}
    evidence = {}
    for key, xml in official.items():
        if not any('name="'+name+'"' in xml for tag, name in defaults if (tag, name) not in evidence):
            continue
        for node in E.fromstring(xml).iter():
            token = (node.tag, node.get('name'))
            if token in defaults and node.get('value') == defaults[token]:
                evidence.setdefault(token, key)
        if len(evidence) == len(defaults):
            break
    assert defaults.keys() <= evidence.keys(), 'Current official schema evidence is incomplete'
    assert not any('name="point_blank"' in xml for xml in official.values())
    errors = []
    scalar_count = 0
    schema_counts = collections.Counter()
    inherited = []
    def parent_value(tree, path):
        seen = set()
        while True:
            parent = tree.find("instance_reference[@name='parent_pbg']")
            if parent is None or not parent.get('value') or parent.get('value') in seen:
                return None, None, None
            key = parent.get('value')
            seen.add(key)
            if parent.get('mod') == ledger['destination_guid']:
                tree = E.parse(ROOT/'assets/attrib/instances'/(key.replace('\\','/')+'.xml')).getroot()
            elif not parent.get('mod') and key in official:
                tree = E.fromstring(official[key])
            else:
                return None, None, None
            value = values(tree).get(path)
            if value is not None:
                item = tree.find("group/list[@name='target_type_table']/group")
                return key, value, item.get('List.ItemID') if item is not None else None
    for row in ledger['instances']:
        original = source/'assets/attrib/instances'/(row['source'].replace('\\', '/')+'.xml')
        raw = original.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['source_sha256'], 'Donor changed: '+str(original)
        tree = E.fromstring(raw)
        for owner in tree.iter():
            legacy = owner.find("list[@name='tier_requirements']")
            if legacy is not None and len(legacy):
                upgrade = legacy.find("template_reference/instance_reference[@name='upgrade_name']")
                modern = owner.find("instance_reference[@name='statetree_tier_requirements_pbg']")
                assert len(legacy) == 1 and upgrade is not None and modern is not None
                assert upgrade.get('value') == modern.get('value'), 'Legacy tier condition is not redundant'
                owner.remove(legacy)
                schema_counts['redundant_legacy_tier_requirement_lists'] += 1
            for node in list(owner):
                if node.tag == 'bool' and node.get('name') == 'point_blank' and node.get('value') == 'False':
                    owner.remove(node)
                    schema_counts['obsolete_false_point_blank_fields'] += 1
        for node in tree.iter():
            value = node.get('value', '')
            mod = node.get('mod', '').replace('-', '')
            if node.tag == 'locstring' and mod == ledger['source_guid']:
                node.set('value', ledger['localization_map'][value])
            elif node.tag == 'file' and value.lower() in icons:
                node.set('value', 'korea\\'+value.lower())
            elif node.tag == 'instance_reference' and value:
                if value == 'abilities\\always_on_abilities\\shaolin_monk_passive_heal_self':
                    value = 'abilities\\always_on_abilities\\chinese_ha_01\\shaolin_monk_passive_heal_self'
                    node.set('value', value)
                target = value if value in paths else aliases.get((value.split('\\')[0], value.split('\\')[-1]))
                if target == row['source'] and node.get('name') == 'parent_pbg' and mod != ledger['source_guid']:
                    target = None
                if target in paths and mod in ('', ledger['source_guid']):
                    node.set('value', paths[target])
        repair = construction.get(row['private'])
        if repair:
            field = tree.find(repair['xpath'])
            assert field is not None and field.get('value') == repair['before']
            field.set('value', repair['after'])
        actual = E.parse(ROOT/'assets/attrib/instances'/(row['private'].replace('\\', '/')+'.xml')).getroot()
        expected, current = values(tree), values(actual)
        scalar_count += len(expected)
        for path in sorted(expected.keys() | current.keys()):
            if expected.get(path) != current.get(path):
                leaf = path.split('/')[-1].split('[')[0].split(':', 1)
                token = tuple(leaf)
                if path not in expected and token in defaults and current[path] == defaults[token]:
                    schema_counts['current_official_default_fields'] += 1
                    continue
                if current.get(path) is None and token == ('float', 'base_damage_modifier'):
                    parent, value, identity = parent_value(actual, path)
                    old_item = tree.find("group/list[@name='target_type_table']/group")
                    if value == expected[path] and old_item is not None and identity == old_item.get('List.ItemID'):
                        inherited.append({'blueprint': row['private'], 'parent': parent,
                                          'path': path, 'value': expected[path], 'target_list_item_id': identity})
                        continue
                errors.append({'blueprint': row['private'], 'path': path,
                               'expected': expected.get(path), 'actual': current.get(path)})

    # Rebuild the ability->queued-upgrade dispatch from the donor independently
    # of its obsolete numeric IDs and compare the committed runtime catalog.
    import import_korea
    expected_routes = import_korea.research_map(source)
    sys.path.insert(0, str(ROOT/'.tools/python'))
    from lupa.lua51 import LuaRuntime
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute((ROOT/'assets/scar/korea/catalog.scar').read_text(encoding='utf-8-sig'))
    catalog = lua.globals().KoreaResearchCatalog
    rows_by_id = {str(row['source_pbg_id']): row for row in ledger['instances'] if row['source'].startswith('abilities\\')}
    actual_routes = {row['ability']: row for row in catalog.values()}
    for old_id, route in expected_routes.items():
        name = ledger['destination_guid']+':'+rows_by_id[old_id]['private'].split('\\')[-1]
        current = actual_routes.get(name)
        if current is None or current['upgrade'] != route['upgrade'] or bool(current['foreign']) != route['foreign']:
            errors.append({'dispatch': old_id, 'ability': name, 'expected': route})
    assert len(actual_routes) == len(expected_routes) == 91
    return {'private_definitions': len(paths), 'compared_tuning_values': scalar_count,
            'intentional_construction_repairs': len(construction),
            'research_dispatch_routes': len(expected_routes), 'errors': errors,
            'editor_schema_migrations': dict(schema_counts), 'inherited_redundant_damage_values': inherited,
            'official_default_evidence': {tag+':'+name: {'value': defaults[(tag,name)], 'source': key}
                                          for (tag,name),key in evidence.items()},
            'scope': 'All serialized gameplay values, references, icons and loc IDs, classifying proven current editor schema changes and four inherited values separately. Inheritance audit covers extension identities. Static parity does not prove native mechanics.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--official-cache', type=Path, default=ROOT/'work/korea_port/official.json')
    args = parser.parse_args()
    result = audit(args.source, args.official_cache)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({**result, 'errors': result['errors'][:10]}, indent=2))
    raise SystemExit(bool(result['errors']))

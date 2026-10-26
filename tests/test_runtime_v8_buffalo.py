"""Native-parent identity regression; compiled evidence is readback, not a burn."""
from pathlib import Path
import json
import sys
import unittest
import xml.etree.ElementTree as E
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/vietnam_redesign/runtime_v8_20261023/buffalo'
REL = 'assets/attrib/instances/ebps/vietnam/buildings/economy/rice_paddies/vn_building_resource_farm2_chi.xml'
sys.path.insert(0, str(ROOT / 'tools'))
from check_extension_inheritance import Resolver


def scopes(root):
    return [root, *root.findall('variant')]


def official_parent_extensions(variant):
    records = json.loads((OUT / 'official-extensions.json').read_text())['records']
    return Resolver({}, records).effective(r'ebps\races\core\buildings\building_house', variant, False)


def identity_errors(root):
    errors = []
    for scope in scopes(root):
        variant = scope.get('name', 'default')
        parents = {x['value']: x for x in official_parent_extensions(variant)}
        extlist = scope.find("list[@name='extensions']")
        removed = set(extlist.get('removedIds', '').split(','))
        for ext in extlist:
            value = ext.get('value')
            if value in parents:
                native = parents[value]['List.ItemID']
                if ext.get('List.ItemID') != native or ext.get('List.ParentItemID') != native or native in removed or ext.get('List.ListAction') == 'Append':
                    errors.append((variant, value, 'inherited extension identity does not override the native item'))
            elif ext.get('List.ListAction') != 'Append':
                errors.append((variant, value, 'new extension has no Append action'))
            # Full farm-owned subtrees must not partially merge their original
            # farm list item IDs into different native house list identities.
            if value != r'ebpextensions\impass_ext' and ext.get('overrideParent') != 'True':
                errors.append((variant, value, 'full authored subtree not explicitly replaced'))
    return errors


def semantic(node):
    return node.tag, tuple(sorted(node.attrib.items())), tuple(semantic(x) for x in node)


class BuffaloV8(unittest.TestCase):
    def before(self):
        with zipfile.ZipFile(OUT.parent / 'before.zip') as z:
            return E.fromstring(z.read(REL))

    def test_actual_v7_target_reproduces_unbound_native_identities(self):
        errors = identity_errors(self.before())
        self.assertEqual(sum('inherited extension' in x[2] for x in errors), 48)
        self.assertEqual(sum('no Append' in x[2] for x in errors), 2)

    def test_current_target_binds_every_extension_to_native_parent(self):
        self.assertEqual(identity_errors(E.parse(ROOT / REL).getroot()), [])

    def test_actual_packaged_target_lost_construction_ui_and_cost(self):
        file = OUT / 'readback/attrib__ebps__vietnam__buildings__economy__rice_paddies__vn_building_resource_farm2_chi.xml'
        root = E.parse(file).getroot()
        for variant in ['default', 'campaign']:
            keys = {x.get('Key') for x in root.find("RGDNode[@Key='" + variant + "']")}
            self.assertEqual(keys, {'impass_ext', 'pbgid', 'parent_pbg'})

    def test_all_gameplay_values_and_nested_list_identities_preserved(self):
        before, after = self.before(), E.parse(ROOT / REL).getroot()
        for old, new in zip(scopes(before), scopes(after)):
            old_list, new_list = old.find('list'), new.find('list')
            new_list.attrib.clear(); new_list.attrib.update(old_list.attrib)
            self.assertEqual(len(old_list), len(new_list))
            for a, b in zip(old_list, new_list):
                self.assertEqual(a.get('value'), b.get('value'))
                b.attrib.clear(); b.attrib.update(a.attrib)
        self.assertEqual(semantic(before), semantic(after))

    def test_buffalo_model_command_card_and_completed_paddy_unchanged(self):
        with zipfile.ZipFile(OUT.parent / 'before.zip') as z:
            files = [p for p in z.namelist() if p.endswith(('vn_unit_water_buffalo_vit.xml', 'vn_unit_war_elephant_1_vit.xml', 'vn_building_resource_farm_chi.xml'))]
            self.assertGreaterEqual(len(files), 5)
            for rel in files:
                self.assertEqual((ROOT / rel).read_bytes(), z.read(rel), rel)


if __name__ == '__main__':
    unittest.main()

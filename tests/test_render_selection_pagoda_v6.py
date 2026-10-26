"""Actual failed v5 values versus approved v6 tuning, plus preservation gates."""
from pathlib import Path
import hashlib, unittest, zipfile, xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
SNAP=ROOT/'work/vietnam_redesign/runtime_v6_20261023/before.zip'
BUFF='assets/attrib/instances/ebps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.xml'
FARM='assets/attrib/instances/ebps/vietnam/buildings/economy/rice_paddies/vn_building_resource_farm2_chi.xml'
PAG='assets/attrib/instances/ebps/vietnam/buildings/landmarks/feudal/vn_building_landmark_age1_vit_one_pilar_pagoda.xml'
def scopes(root):return [root,*root.findall('variant')]
def ext(root,name):return root.find("list[@name='extensions']/template_reference[@value='ebpextensions\\"+name+"']")
class V6TuningTests(unittest.TestCase):
    def test_worker_elephant_rollback_inherits_matching_native_presentation(self):
        with zipfile.ZipFile(SNAP) as z:old=E.fromstring(z.read(BUFF))
        for scope in scopes(old):
            self.assertIsNone(ext(scope,'entity_blueprint_ext').find("instance_reference[@name='animator_attachments']").get('overrideParent'))
        donor=ROOT/'assets/attrib/instances/ebps/vietnam/units/economy/water_buffalo/vn_unit_war_elephant_1_vit.xml'
        native=E.parse(ROOT/'work/vietnam_redesign/worker_elephant_rollback_20261023/official-worker-elephant.xml').getroot()
        for scope, parent in zip(scopes(E.parse(ROOT/BUFF).getroot()),scopes(E.parse(donor).getroot())):
            self.assertEqual(scope.find("instance_reference[@name='parent_pbg']").get('value'),
                             r'ebps\vietnam\units\economy\water_buffalo\vn_unit_war_elephant_1_vit')
            for name in ['entity_blueprint_ext','tier_ext','animation_action_tree_ext','hit_react_tree_ext','ui_ext']:
                self.assertIsNone(ext(scope,name),name)
            # Inheriting the retained donor restores its real Worker Elephant tier.
            tier_ext=ext(parent,'tier_ext')
            if tier_ext is None:
                self.assertEqual(parent.find("instance_reference[@name='parent_pbg']").get('value'),
                                 r'ebps\races\sultanate_ha_tug\units\unit_worker_elephant_2_sul_ha_tug')
                tier_ext=ext(native,'tier_ext')
            tier=tier_ext.find("list[@name='tier_group_list']")
            self.assertEqual(tier.find('.//instance_reference').get('value'),
                             ext(native,'tier_ext').find('.//instance_reference').get('value'))
            self.assertEqual(scope.find("list[@name='extensions']").get('overrideParent'),None)
            speed=ext(scope,'moving_ext').find("enum_table[@name='speed_scaling_table']/float[@name='default_speed']")
            self.assertEqual(speed.get('value'),'2.5')
    def test_foundation_has_plot_selection_volume_and_construction_collision(self):
        with zipfile.ZipFile(SNAP) as z:old=E.fromstring(z.read(FARM))
        for scope in scopes(old):self.assertEqual(ext(scope,'ui_ext').find("enum[@name='selection_method']").get('value'),'obb_adjusted_to_terrain')
        for scope in scopes(E.parse(ROOT/FARM).getroot()):
            ui=ext(scope,'ui_ext')
            self.assertEqual(ui.find("enum[@name='selection_method']").get('value'),'obb_size')
            self.assertEqual([float(x.get('value')) for x in ui.find("group[@name='selection_obb_size']")],[12,2,12])
            self.assertEqual(ext(scope,'impass_ext').find("group[@name='impass_simboxes']/bool[@name='default_simbox']").get('value'),'True')
            self.assertIsNone(ext(scope,'resource_deposit_ext'))
    def test_foundation_effectively_blocks_infantry_and_vehicle_without_other_house_extensions(self):
        import sys,json
        sys.path.insert(0,str(ROOT/'tools'))
        from check_extension_inheritance import Resolver,load_local
        records=json.loads((ROOT/'work/vietnam_redesign/runtime_v6_20261023/official-extensions.json').read_text())['records']
        resolver=Resolver(load_local(ROOT),records)
        donor=E.parse(ROOT/'work/vietnam_redesign/runtime_v6_20261023/official/ebps__building_house.xml').getroot()
        current=E.parse(ROOT/FARM).getroot()
        prior=E.parse(ROOT/'work/vietnam_redesign/runtime_v6_20261023/supervision/foundation-before-collision.xml').getroot()
        for variant,scope,old in [('default',current,prior),('campaign',current.find("variant[@name='campaign']"),prior.find("variant[@name='campaign']"))]:
            native=donor if variant=='default' else donor.find("variant[@name='campaign']")
            parent=scope.find("instance_reference[@name='parent_pbg']")
            self.assertEqual(parent.get('value'),r'ebps\races\core\buildings\building_house')
            block=ext(scope,'impass_ext');nativeblock=ext(native,'impass_ext')
            self.assertEqual(block.get('List.ItemID'),nativeblock.get('List.ItemID'))
            self.assertEqual(block.get('List.ParentItemID'),nativeblock.get('List.ItemID'))
            paths=block.find("list[@name='block_path']")
            self.assertEqual({n.get('value') for n in paths},{r'pass_types\infantry',r'pass_types\vehicle'})
            for node in paths:
                original=next(n for n in nativeblock.find("list[@name='block_path']") if n.get('value')==node.get('value'))
                self.assertEqual(node.get('List.ItemID'),original.get('List.ItemID'))
                self.assertEqual(node.get('List.ParentItemID'),original.get('List.ItemID'))
                self.assertIsNone(node.get('List.ListAction'))
            effective=resolver.effective(FARM.split('assets/attrib/instances/')[1][:-4].replace('/','\\'),variant)
            self.assertEqual({x.get('value') for x in effective},{x.get('value') for x in old.find("list[@name='extensions']")})
            # Every previous authored non-impass value and identity survives.
            def content(node):return [(n.tag,n.attrib) for n in node.iter()]
            for previous in old.find("list[@name='extensions']"):
                if previous.get('value')==r'ebpextensions\impass_ext':continue
                after=next(n for n in scope.find("list[@name='extensions']") if n.get('value')==previous.get('value'))
                self.assertEqual(content(previous),content(after),previous.get('value'))

    def test_both_pagoda_hooks_replaced_without_other_gameplay_changes(self):
        with zipfile.ZipFile(SNAP) as z:old=E.fromstring(z.read(PAG))
        new=E.parse(ROOT/PAG).getroot()
        path=".//group[@name='on_construction_complete_state_tree_refs']/string[@name='while_construction_complete_entity_state_tree_ref']"
        self.assertEqual(len(new.findall(path)),2)
        for a,b in zip(old.findall(path),new.findall(path)):
            self.assertEqual(a.get('value'),'meinwerk_palace_construction_complete_hre')
            self.assertEqual(b.get('value'),r'building_construction_complete\buildings\landmark_construction_complete')
            a.set('value',b.get('value'));a.set('overrideParent','True')
        # Ignore whitespace, compare every tag, attribute and identity.
        def nodes(r):return [(x.tag,x.attrib) for x in r.iter()]
        self.assertEqual(nodes(old),nodes(new))
    def test_completed_paddy_starting_stealth_and_producers_preserved(self):
        protected=['assets/attrib/instances/ebps/vietnam/buildings/economy/rice_paddies/vn_building_resource_farm_chi.xml',
                   'assets/scar/vietnam/starting_units.scar','assets/scar/vietnam/headquarters.scar']
        with zipfile.ZipFile(SNAP) as z:
            for name in protected:
                if name in z.namelist():self.assertEqual((ROOT/name).read_bytes(),z.read(name),name)
            for name in z.namelist():
                if name.startswith('assets/attrib/instances/sbps/'):
                    self.assertEqual((ROOT/name).read_bytes(),z.read(name),name)
    def test_every_existing_root_pbg_identity_preserved(self):
        with zipfile.ZipFile(SNAP) as z:
            for name in z.namelist():
                if not name.startswith('assets/attrib/instances/') or not name.endswith('.xml'):continue
                old=E.fromstring(z.read(name));new=E.parse(ROOT/name).getroot()
                self.assertEqual(old.find("uniqueid[@name='pbgid']").attrib,new.find("uniqueid[@name='pbgid']").attrib,name)

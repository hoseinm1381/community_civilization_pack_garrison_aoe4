"""Native data contracts. These do not replace Content Editor/game tests."""
from pathlib import Path
import unittest, xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets/attrib/instances'
WORK=ROOT/'work/vietnam_redesign/farm_repair_20261022'
NAME='vn_unit_war_elephant_1_vit'

def ext(scope,name):
    return scope.find("list/template_reference[@value='"+name+"']")

def assert_campaign_worker(case, scope):
    """The official worker has no campaign parent: require a complete native copy."""
    case.assertEqual(scope.find("instance_reference[@name='parent_pbg']").get('value'), '')
    extensions=scope.find("list[@name='extensions']")
    values=[n.get('value') for n in extensions]
    case.assertEqual(len(values),31)
    case.assertEqual(len(values),len(set(values)))
    for n in extensions.iter():
        case.assertNotIn('List.ParentItemID',n.attrib)
        case.assertNotIn('List.ListAction',n.attrib)
    worker=E.parse(WORK/'ebps__unit_worker_elephant_2_sul_ha_tug.xml').getroot()
    war=E.parse(WORK/'ebps__unit_war_elephant.xml').getroot()
    def contains(actual, expected, outer=False):
        case.assertIsNotNone(actual)
        for key,value in expected.attrib.items():
            if key in ['overrideParent','List.ParentItemID','List.ListAction'] or (outer and key=='List.ItemID'):continue
            case.assertEqual(actual.get(key),value,(expected.attrib,key))
        for child in expected:
            identity=child.get('List.ItemID')
            candidates=[n for n in actual if n.tag==child.tag and n.get('name')==child.get('name') and (identity is None or n.get('List.ItemID')==identity)]
            case.assertEqual(len(candidates),1,child.attrib)
            contains(candidates[0],child)
    for name in ['tier_ext','entity_blueprint_ext','action_tree_ext','statemodel_ext','hit_react_tree_ext']:
        native=ext(worker,'ebpextensions\\'+name)
        if native is None:native=ext(war,'ebpextensions\\'+name)
        contains(ext(scope,'ebpextensions\\'+name),native,True)
    case.assertEqual(ext(scope,r'ebpextensions\holdable_ext').find("enum[@name='holdable']").get('value'),'hold_cattle')

class FarmRepairTests(unittest.TestCase):
    def test_private_buffalo_inherits_complete_official_worker(self):
        for category,parent in [('ebps',r'ebps\races\sultanate_ha_tug\units\unit_worker_elephant_2_sul_ha_tug'),('sbps',r'sbps\races\sultanate_ha_tug\unit_worker_elephant_2_sul_ha_tug')]:
            current=E.parse(next((A/category).rglob(NAME+'.xml'))).getroot()
            for s in [current,*current.findall('variant')]:
                if category=='ebps' and s.get('name')=='campaign':assert_campaign_worker(self,s)
                else:self.assertEqual(s.find("instance_reference[@name='parent_pbg']").get('value'),parent)
            if category=='ebps':
                for s in [current,*current.findall('variant')]:
                    if s.get('name')=='campaign':continue # Complete native visual/controller contract checked above.
                    self.assertIsNone(ext(s,r'ebpextensions\tier_ext'),'Visuals must inherit the complete native worker')
                    self.assertEqual(ext(s,r'ebpextensions\animation_action_tree_ext').find("state_tree_node[@name='ActionTree_OpeningBranch']").get('value'),'infantry')

    def test_buffalo_uses_native_construct_track_and_hold_instead_of_food_gather(self):
        current=E.parse(next((A/'ebps').rglob(NAME+'.xml'))).getroot()
        for s in [current,*current.findall('variant')]:
            gather=ext(s,r'ebpextensions\resource_gatherer_ext')
            self.assertEqual(len(gather.find("list[@name='gather_types']")),0)
            physical=ext(s,r'ebpextensions\animation_action_tree_ext')
            self.assertEqual(physical.find("state_tree_node[@name='ActionTree_OpeningBranch']").get('value'),'infantry')
            self.assertEqual(ext(s,r'ebpextensions\holdable_ext').find("enum[@name='holdable']").get('value'),'hold_cattle')

    def test_native_farm_interactions_are_inherited(self):
        for p in (A/'ebps/vietnam/buildings/economy/rice_paddies').glob('*.xml'):
            r=E.parse(p).getroot()
            for s in [r,*r.findall('variant')]:
                self.assertIsNone(ext(s,r'ebpextensions\interactive_object_ext'))
                self.assertEqual(ext(s,r'ebpextensions\construction_ext').find("float[@name='max_engineers']").get('value'),'1')

    def test_original_root_identities_are_preserved(self):
        import zipfile
        with zipfile.ZipFile(WORK/'before.zip') as z:
            for category in ['ebps','sbps']:
                p=next((A/category).rglob(NAME+'.xml'))
                old=E.fromstring(z.read(p.relative_to(ROOT).as_posix()))
                self.assertEqual(E.parse(p).find("uniqueid[@name='pbgid']").get('value'),old.find("uniqueid[@name='pbgid']").get('value'))

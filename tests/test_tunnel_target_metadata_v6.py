"""Effective inherited target geometry and topology-preservation regressions."""
from pathlib import Path
import importlib.util,json,unittest,zipfile,xml.etree.ElementTree as E
from test_runtime_repairs import ROOT
PATH=ROOT/'work/vietnam_redesign/runtime_v6_20261023/tunnels/generate_target_footprints.py'
spec=importlib.util.spec_from_file_location('tunnel_target_geometry_v6',PATH)
generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)

def tree(body):return E.fromstring('<instance>'+body+'</instance>')
def extension(identity,body='',kind='site_ext',attrs=''):
    return f'<template_reference value="ebpextensions\\{kind}" List.ItemID="{identity}" {attrs}>{body}</template_reference>'
def site(x=None,z=None):
    return '<group name="footprint_scale">'+''.join(f'<float name="{axis}" value="{v}"/>' for axis,v in [('x',x),('y',z)] if v is not None)+'</group>'

class TargetMetadataV6(unittest.TestCase):
    def test_partial_site_override_retains_inherited_other_axis(self):
        parent=tree('<list name="extensions">'+extension('1',site(8,6))+'</list>')
        child=tree('<instance_reference name="parent_pbg" value="parent"/><list name="extensions">'+extension('1',site(4),attrs='List.ParentItemID="1"')+'</list>')
        result=generator.Resolver({},dict(parent=parent,child=child)).geometry('child')
        self.assertEqual((result['hx'],result['hz']),(4,6))

    def test_removed_site_identity_does_not_leave_an_inherited_footprint(self):
        parent=tree('<list name="extensions">'+extension('1',site(8,6))+'</list>')
        child=tree('<instance_reference name="parent_pbg" value="parent"/><list name="extensions" removedIds="1"/>')
        result=generator.Resolver({},dict(parent=parent,child=child)).geometry('child')
        self.assertNotIn('hx',result)

    def test_campaign_chain_uses_its_native_variant_identity(self):
        parent=tree('<list name="extensions">'+extension('1',site(8,6))+'</list><variant name="campaign"><list name="extensions">'+extension('9',site(12,10))+'</list></variant>')
        child=tree('<instance_reference name="parent_pbg" value="parent"/><list name="extensions">'+extension('1',site(4),attrs='List.ParentItemID="1"')+'</list><variant name="campaign"><list name="extensions">'+extension('9',site(5),attrs='List.ParentItemID="9"')+'</list></variant>')
        r=generator.Resolver({},dict(parent=parent,child=child))
        self.assertEqual(r.geometry('child')['hx'],4)
        self.assertEqual((r.geometry('child',variant='campaign')['hx'],r.geometry('child',variant='campaign')['hz']),(5,10))

    def test_actual_private_foundation_and_mongol_house_have_exact_geometry(self):
        j=json.loads((PATH.parent/'target-footprints.json').read_text())
        records={r['key'].split('\\')[-1]:r for r in j['records'] if r['private']}
        self.assertEqual(records['vn_building_resource_farm2_chi']['geometry']['hx'],6)
        self.assertEqual(records['vn_building_house_mon']['geometry']['hx'],4)
        self.assertFalse([r for r in j['unresolved_obb'] if r['private']])
        self.assertGreater(j['counts']['official'],1000)

    def test_supported_network_topology_is_byte_preserved(self):
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v6_20261023/before.zip') as z:
            for name in ['tunnel_buildings.scar','tunnel_core.scar']:
                relative='assets/scar/vietnam/'+name
                self.assertEqual((ROOT/relative).read_bytes(),z.read(relative))

    def test_unknown_obb_is_recorded_instead_of_zero_radius_guess(self):
        j=json.loads((PATH.parent/'target-footprints.json').read_text())
        self.assertGreater(len(j['unresolved_obb']),0)
        self.assertTrue(all('OBB' in r['reason'] for r in j['unresolved_obb']))

if __name__=='__main__':unittest.main()

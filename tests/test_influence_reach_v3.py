from test_runtime_repairs import RuntimeFixture, ROOT
import xml.etree.ElementTree as E

class InfluenceReachTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        for f in ['tunnel_core.scar','tunnel_buildings.scar']:
            self.runlua((ROOT/'assets/scar/vietnam'/f).read_text())

    def test_native_overlay_and_script_metadata_match(self):
        files={p.stem:p for p in (ROOT/'assets/attrib/instances/ebps/vietnam/buildings').rglob('*.xml')}
        for name,meta in self.g.VietnamTunnelBuildings.items():
            expected=8 if 'town_center' in name else 4
            self.assertEqual(meta.reach,expected,name)
            t=E.parse(files[name]).getroot()
            ranges=t.findall('.//template_reference[@value="ebpextensions\\district_generator_ext"]/float[@name="range_metres"]')
            self.assertTrue(ranges,name)
            for value in ranges:self.assertEqual(float(value.get('value')),expected,name)

    def test_tc_two_tiles_hq_one_tile_without_summing_influence_radii(self):
        self.runlua('''
        function n(id,x,reach,root) return {id=id,x=x,z=0,hx=4,hz=4,reach=reach,root=root} end
        tc=n(1,0,8,true); house=n(2,16,4,false); outside=n(3,28.01,4,false)
        VietnamTunnelCore.Build({tc,house,outside})
        ''')
        self.assertEqual(self.g.house.component,1)
        self.assertIsNone(self.g.outside.component)
        self.runlua('hq=n(1,0,4,true);house=n(2,12.01,4,false);VietnamTunnelCore.Build({hq,house})')
        self.assertIsNone(self.g.house.component)
        self.runlua('house.x=12;VietnamTunnelCore.Build({hq,house})')
        self.assertEqual(self.g.house.component,1)

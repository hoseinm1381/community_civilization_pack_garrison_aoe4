"""0711 regressions: reproduce native cap=0 and off-screen tutorial tags."""
import importlib.util, re, sys, unittest
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.tools/python'))
from lupa.lua51 import LuaRuntime
spec=importlib.util.spec_from_file_location('oldhud',ROOT/'tests/test_hud_0710.py')
oldhud=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldhud)

class Runtime(oldhud.HUDRuntime):
    def setUp(self):
        data=ROOT/'assets/scar/vietnam/presentation_data.scar'
        original=oldhud.LuaRuntime
        def factory(**kwargs):
            lua=LuaRuntime(**kwargs)
            if data.exists():lua.execute(data.read_text())
            return lua
        oldhud.LuaRuntime=factory
        try:super().setUp()
        finally:oldhud.LuaRuntime=original
    def test_counts_cap_preserves_shared_context(self):
        self.check('cap=0;VietnamPresentation_Update();assert(p1.scarModel.vietnam_buffalo_count==3);assert(p1.scarModel.vietnam_buffalo_cap==15);assert(p1.scarModel.vietnam_buffalo_text=="3/15");assert(p1.scarModel.keep==42);assert(not p2.scarModel.vietnam_hud)')
        self.check('VietnamPresentationData.buffaloCap=19;VietnamPresentation_Update();assert(p1.scarModel.vietnam_buffalo_text=="3/19")')

class Marker(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''function import(x) end
        onscreen=true;replay=false;owner=1;created=0;destroyed=0
        function Player_GetID(x) return x end
        function Game_GetLocalPlayer() return owner end
        function UI_IsReplay() return replay end
        function Entity_GetPosition(e) return {x=10,y=0,z=20} end
        function World_Pos(x,y,z) return {x=x,y=y,z=z} end
        function Misc_IsPosOnScreen(p,percent) assert(percent<=1);return onscreen end
        function UI_CreateTagForPosition(p,data) created=created+1;lastData=data end
        function UI_DestroyTagForPosition(p) destroyed=destroyed+1 end
        watch={owner=1,paddy=10}
        ''')
        text=(ROOT/'assets/scar/vietnam/paddy_wood.scar').read_text()
        start=text.index('local function setWorkingMarker(')
        end=text.index('local function clearAssignment(',start)
        self.lua.execute(text[start:end].replace('local function setWorkingMarker','function setWorkingMarker',1))
    def test_camera_pan_removes_and_restores(self):
        self.lua.execute('setWorkingMarker(watch,10);assert(created==1);onscreen=false;setWorkingMarker(watch,10);assert(destroyed==1 and watch.marker==nil);onscreen=true;setWorkingMarker(watch,10);assert(created==2)')
    def test_owner_replay_and_work_end_cleanup(self):
        self.lua.execute('owner=2;setWorkingMarker(watch,10);assert(created==0);owner=1;replay=true;setWorkingMarker(watch,10);assert(created==0);replay=false;setWorkingMarker(watch,10);setWorkingMarker(watch,nil);assert(created==1 and destroyed==1)')
    def test_quiet_route_flag(self):
        self.lua.execute('setWorkingMarker(watch,10);assert(lastData.VietnamQuietSupervision==true)')

class UI(unittest.TestCase):
    def test_badge_loading_calls_only_private_ui_overrides(self):
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''seen={};n=0
        function EBP_Exists(name) return true end
        function SBP_Exists(name) return true end
        function BP_GetEntityBlueprint(name) return "entity:"..name end
        function BP_GetSquadBlueprint(name) return "squad:"..name end
        function UI_OverrideUIProperty(pbg,key,value)
            assert(string.find(pbg,"b7fcea91257b408fb9e8ae4d8bc402e1:",1,true))
            assert(key=="flag_icon" and value=="images\\\\vietnam_0710\\\\dai_viet_dragon")
            assert(not seen[pbg]);seen[pbg]=true;n=n+1
        end''')
        lua.execute((ROOT/'assets/scar/vietnam/presentation_badges.scar').read_text())
        self.assertEqual(lua.globals().n,177)
    def test_marker_bypasses_tutorial_adorner(self):
        page=(ROOT/'assets/ui/hud/pages/cardinalhudpage.xaml').read_text()
        region=page.split('<!--  Position tags  -->')[1].split('<!--  Hint Points')[0]
        self.assertIn('TagData.Data[VietnamQuietSupervision]',region)
        self.assertIn('Property="esControls:TagAdorner.IsTagged" Value="False"',region)
        self.assertIn('ContentTemplate="{StaticResource VietnamBuffaloSupervisionTemplate}"',region)
        res=ET.parse(ROOT/'assets/ui/resources/hudresources.xaml').getroot()
        x='{http://schemas.microsoft.com/winfx/2006/xaml}Key'
        marker=next(n for n in res if n.get(x)=='VietnamBuffaloSupervisionTemplate')
        self.assertEqual(marker[0].get('Width'),'14')
        self.assertFalse(any('Animation' in n.tag or 'Storyboard' in n.tag for n in marker.iter()))
    def test_cap_comes_from_native_squad_requirement(self):
        doc=ET.parse(ROOT/'assets/attrib/instances/sbps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.xml')
        caps={int(float(n.get('value'))) for n in doc.findall('.//float[@name="max_squad_cap"]')}
        self.assertEqual(caps,{15})
        data=ROOT/'assets/scar/vietnam/presentation_data.scar'
        self.assertTrue(data.exists())
        self.assertRegex(data.read_text(),r'buffaloCap\s*=\s*15')
    def test_private_badges_have_full_roster_and_no_stock_override(self):
        data=ROOT/'assets/scar/vietnam/presentation_badges.scar'
        self.assertTrue(data.exists())
        text=data.read_text();self.assertIn('UI_OverrideUIProperty',text)
        names=re.findall(r'"b7fcea91257b408fb9e8ae4d8bc402e1:([^"]+)"',text)
        self.assertGreater(len(names),150)
        self.assertIn('vn_unit_water_buffalo_vit',names)
        self.assertIn('vn_building_defense_outpost_chi_fortified',names)
        self.assertNotRegex(text,r'"(?:ebps|sbps)\\\\races')
        self.assertIn('"flag_icon"',text)

if __name__=='__main__':unittest.main(verbosity=2)

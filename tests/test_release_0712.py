"""0712 timing, counter, visibility and edge-based tunnel regressions."""
import importlib.util,sys,unittest,re,zipfile
from pathlib import Path
from decimal import Decimal
from xml.etree import ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.tools/python'))
from lupa.lua51 import LuaRuntime
spec=importlib.util.spec_from_file_location('hud0711',ROOT/'tests/test_hud_0711.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class Counter(old.Runtime):
    def setUp(self):
        super().setUp()
        self.lua.execute('''focused={}
        function Squad_GetPosition(s) return {x=s.id,y=0,z=20} end
        function Camera_FocusOnPosition(p) table.insert(focused,p.x) end''')
    def test_click_enabled_for_owner_and_disabled_for_replay_zero(self):
        self.check('assert(p1.scarModel.vietnam_buffalo_can_cycle==true);replay=true;VietnamPresentation_Update();assert(not p1.scarModel.vietnam_buffalo_can_cycle);replay=false;units={};VietnamPresentation_Update();assert(not p1.scarModel.vietnam_buffalo_can_cycle)')
    def test_click_cycles_selection_and_camera_without_orders(self):
        self.check('for i=1,4 do VietnamPresentation_CycleBuffalo() end;assert(#focused==4);assert(focused[1]==10 and focused[2]==20 and focused[3]==30 and focused[4]==10);assert(selected[4]==10)')
    def test_equivalent_native_player_handles_allow_clicking(self):
        self.check('''function Player_GetID(x) if type(x)=="table" then return x.nativeID end;return x end
        function Game_GetLocalPlayer() return {nativeID=101} end
        VietnamPresentation_Update();assert(p1.scarModel.vietnam_buffalo_can_cycle==true)
        VietnamPresentation_CycleBuffalo();assert(selected[1]==10 and focused[1]==10)''')
    def test_actual_official_command_wrapper_dispatches_global_callback(self):
        ui=(ROOT/'output/release_0712/official/ui.scar').read_text()
        a=ui.index('UI_TYPE_COMMAND =');b=ui.index('--? @shortdesc Create a table that will be interpreted as a data context',a)
        self.lua.execute(ui[a:b])
        self.check('VietnamPresentation_Restore();local c=VietnamPresentationState.command;assert(c.__Type==1 and c.__Value=="VietnamPresentation_CycleBuffalo");_G[c.__Value]();assert(selected[1]==10 and focused[1]==10)')

class Source(unittest.TestCase):
    def test_timing_transfer_all_tiers(self):
        with zipfile.ZipFile(ROOT/'output/release_0712/baseline/source.zip') as z:
            for age in (2,3,4):
                p=f'assets/attrib/instances/weapon/vietnam/vn_weapon_skirmisher_{age}_vit.xml'
                before=E.fromstring(z.read(p));after=E.parse(ROOT/p).getroot()
                paths=["group[@name='weapon_bag']/group[@name='fire']/float[@name='wind_up']",
                    "group[@name='weapon_bag']/group[@name='reload']/group[@name='duration']/float[@name='min']",
                    "group[@name='weapon_bag']/group[@name='reload']/group[@name='duration']/float[@name='max']"]
                oldvalues=[Decimal(before.find(s).get('value')) for s in paths]
                newvalues=[Decimal(after.find(s).get('value')) for s in paths]
                self.assertEqual(newvalues,[oldvalues[0]+Decimal('.25'),oldvalues[1]-Decimal('.25'),oldvalues[2]-Decimal('.25')])
                self.assertEqual(oldvalues[0]+oldvalues[1],newvalues[0]+newvalues[1])
    def test_widget_and_large_static_marker(self):
        root=E.parse(ROOT/'assets/ui/resources/hudresources.xaml').getroot();x='{http://schemas.microsoft.com/winfx/2006/xaml}Key'
        counter=next(n for n in root if n.get(x)=='VietnamBuffaloCounter');s=E.tostring(counter,encoding='unicode')
        self.assertIn('vietnam_buffalo_can_cycle',s);self.assertNotIn('Path="IsReplay"',s)
        marker=next(n for n in root if n.get(x)=='VietnamBuffaloSupervisionTemplate')
        self.assertGreaterEqual(int(marker[0].get('Width')),48)
        self.assertGreaterEqual(int(marker[0][0].get('Width')),40)
        self.assertFalse(any('Animation' in n.tag for n in marker.iter()))
    def test_influence_ranges_and_network_increase_two_metres(self):
        import json
        rows=json.loads((ROOT/'output/release_0712/range-inventory.json').read_text())['rows']
        self.assertEqual(len({r['key'] for r in rows}),36)
        for row in rows:
            doc=E.parse(ROOT/('assets/attrib/instances/'+row['key'].replace('\\','/')+'.xml')).getroot()
            scope=doc if row['variant']=='default' else doc.find("variant[@name='"+row['variant']+"']")
            ext=next(n for n in scope.find("list[@name='extensions']") if n.get('value')=='ebpextensions\\district_generator_ext')
            self.assertEqual(float(ext.find("float[@name='range_metres']").get('value')),row['before']+2)
        with zipfile.ZipFile(ROOT/'output/release_0712/baseline/source.zip') as z:
            name='assets/scar/vietnam/tunnel_buildings.scar'
            before=list(map(int,re.findall(r'reach=(\d+)',z.read(name).decode())))
            after=list(map(int,re.findall(r'reach=(\d+)',(ROOT/name).read_text())))
            self.assertEqual(after,[n+2 for n in before])

class Tunnel(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT/'assets/scar/vietnam/tunnel_core.scar').read_text())
        self.lua.execute('''buildings={};destroyed=0
        function EGroup_CreateUnique() return buildings end
        function Player_GetEntitiesEGroup(owner,g) end
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        function EGroup_Destroy(g) destroyed=destroyed+1 end
        function Entity_GetID(e) return e.id end
        function Entity_IsValid(id) return true end
        function Entity_IsBuilding(e) return true end
        function World_OwnsEntity(e) return false end
        function Entity_GetPlayerOwner(e) return e.owner or 1 end
        function sameOwner(a,b) return a==b end
        function metadata(e,target) return e.geometry end
        function Entity_GetPosition(e) return {x=e.x or 0,y=0,z=e.z or 0} end
        function Entity_GetHeading(e) return {x=0,z=1} end
        function targetStatus(s,id)
          for _,e in ipairs(buildings) do if e.id==id then return e.rejection end end
        end
        s={owner=1};geometry={hx=8,hz=8,axis=true}
        ''')
        text=(ROOT/'assets/scar/vietnam/tunnels.scar').read_text()
        a=text.index('local function nearestOwned(');b=text.index('-- Current official native ProcessAbilityCommand',a)
        self.lua.execute(text[a:b].replace('local function nearestOwned','function nearestOwned',1))
    def test_eight_metres_from_large_tc_edge_not_center(self):
        self.lua.execute('buildings={{id=1,geometry=geometry}};assert(nearestOwned(s,{x=16,z=0})==1);local id=nearestOwned(s,{x=16.01,z=0});assert(id==nil);assert(destroyed==2)')
    def test_foundation_cannot_steal_nearby_valid_destination(self):
        self.lua.execute('buildings={{id=1,x=7,geometry=geometry,rejection="foundation"},{id=2,x=0,geometry=geometry}};assert(nearestOwned(s,{x=14,z=0})==2)')
    def test_unrelated_unknown_building_does_not_block_valid_exit(self):
        self.lua.execute('buildings={{id=1,x=100},{id=2,x=0,geometry=geometry}};assert(nearestOwned(s,{x=14,z=0})==2)')
    def test_enemy_disconnected_and_ties(self):
        self.lua.execute('buildings={{id=1,owner=2,geometry=geometry},{id=2,geometry=geometry,rejection="disconnected"},{id=50,geometry=geometry},{id=20,geometry=geometry}};assert(nearestOwned(s,{x=14,z=0})==20)')

if __name__=='__main__':unittest.main(verbosity=2)

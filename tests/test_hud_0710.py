import re, sys, unittest
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.tools/python'))
from lupa.lua51 import LuaRuntime

class HUDRuntime(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
        function import(x) end
        CT_Medic=3
        p1={index=1,id=101,isHuman=true,scarModel={keep=42}}
        p2={index=2,id=202,isHuman=true,scarModel={show_actual_score=true}}
        PLAYERS={p1,p2}; localID=101; replay=false; cap=19; calls=0; selected={}; cleared=0
        VietnamModeState={civilizations={[1]='vietnam',[2]='china'},selection={closed=true}}
        bp='b7fcea91257b408fb9e8ae4d8bc402e1:vn_unit_water_buffalo_vit'
        units={{id=30,owner=101,bp=bp},{id=10,owner=101,bp=bp},{id=20,owner=101,bp=bp},
          {id=40,owner=101,bp=bp,dead=true},{id=50,owner=202,bp=bp},
          {id=60,owner=101,bp='decoration'},{id=70,owner=101,bp=bp,despawned=true}}
        function SBP_Exists(x) return true end
        function BP_GetSquadBlueprint(x) return x end
        function Player_GetSquads(p) return units end
        function Player_GetID(p) return p end
        function SGroup_ForEachEx(g,f,spawned,despawned)
          assert(spawned and not despawned)
          for i,s in ipairs(g) do if not s.despawned then f(g,i,s) end end
        end
        function Squad_IsAlive(s) return not s.dead end
        function Squad_GetPlayerOwner(s) assert(not s.despawned);return s.owner end
        function Squad_GetBlueprint(s) return s.bp end
        function Squad_GetID(s) return s.id end
        function Game_GetLocalPlayer() return localID end
        function Core_GetPlayersTableEntry(id) for _,p in ipairs(PLAYERS) do if p.id==id then return p end end end
        function Player_IsAlive(id) return not defeated end
        function UI_IsReplay() return replay end
        function UI_CreateCommand(name) calls=calls+1;return {callback=name} end
        function UI_SetPlayerDataContext(id,m) end
        function Player_GetCurrentPopulationCap(id,ct) assert(ct==CT_Medic);return cap end
        function Misc_ClearSelection() cleared=cleared+1 end
        function Misc_SelectSquad(s,b) assert(b);table.insert(selected,s.id) end
        ''')
        self.lua.execute((ROOT/'assets/scar/vietnam/presentation.scar').read_text())
        self.g=self.lua.globals()
        self.g.VietnamPresentation_Start()
    def check(self,code): self.lua.execute(code)
    def test_counts_cap_preserves_shared_context(self):
        self.check('assert(p1.scarModel.vietnam_buffalo_count==3);assert(p1.scarModel.vietnam_buffalo_cap==19);assert(p1.scarModel.keep==42);assert(not p2.scarModel.vietnam_hud);assert(p2.scarModel.show_actual_score)')
        self.check('cap=23;VietnamPresentation_Update();assert(p1.scarModel.vietnam_buffalo_cap==23);assert(calls==1)')
    def test_cycle_stable_wrap_and_no_orders(self):
        self.check('for i=1,4 do VietnamPresentation_CycleBuffalo() end;assert(selected[1]==10 and selected[2]==20 and selected[3]==30 and selected[4]==10)')
    def test_death_between_clicks_revalidates(self):
        self.check('VietnamPresentation_CycleBuffalo();units[3].dead=true;VietnamPresentation_CycleBuffalo();assert(selected[2]==30)')
    def test_zero_keeps_selection(self):
        self.check('units={};VietnamPresentation_CycleBuffalo();assert(cleared==0 and #selected==0)')
    def test_china_observer_replay_defeat_noop(self):
        self.check('localID=202;VietnamPresentation_CycleBuffalo();localID=999;VietnamPresentation_CycleBuffalo();localID=101;replay=true;VietnamPresentation_CycleBuffalo();replay=false;defeated=true;VietnamPresentation_CycleBuffalo();assert(#selected==0)')
    def test_switch_restore_cleanup(self):
        self.check('VietnamPresentation_CycleBuffalo();localID=202;VietnamPresentation_Update();localID=101;VietnamPresentation_Update();VietnamPresentation_CycleBuffalo();assert(selected[2]==10)')
        self.check('VietnamPresentation_Restore();VietnamPresentation_CycleBuffalo();assert(selected[3]==10);VietnamPresentation_Cleanup();VietnamPresentation_CycleBuffalo();assert(#selected==3);assert(not p1.scarModel.vietnam_hud);assert(p1.scarModel.keep==42)')

class HUDXML(unittest.TestCase):
    def test_texture_inputs_follow_native_burn_contract(self):
        burn=(ROOT/'assets/_default.burnproj').read_text(encoding='utf-8-sig')
        self.assertIn('ui\\icons\\**\\*.*;ui\\images\\**\\*.*',burn)
        self.assertIn('RRTextureBurner',burn)
        for name in ('buffalo','dai_viet_dragon'):
            self.assertTrue((ROOT/f'art/authoring/release_0710/hud/{name}.svg').is_file())
            self.assertEqual((ROOT/f'assets/ui/images/vietnam_0710/{name}.png').read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
        self.assertFalse(list((ROOT/'assets/ui/images/vietnam_0710').glob('*.svg')))
    def test_parse(self):
        for p in (ROOT/'assets/ui').rglob('*.xaml'): ET.parse(p)
    def test_china_template_unchanged(self):
        original=(ROOT/'output/release_0710/hud/official/hudresources.xaml').read_text(encoding='utf-8-sig')
        current=(ROOT/'assets/ui/resources/hudresources.xaml').read_text()
        pattern=r'<DataTemplate x:Key="ChineseImperialOfficers".*?</DataTemplate>\s*</ToolTip.ContentTemplate>.*?</DataTemplate>'
        self.assertEqual(re.search(pattern,original,re.S).group(),re.search(pattern,current,re.S).group())
    def test_row_conditional_and_observer_guard(self):
        scores=(ROOT/'assets/ui/hud/controls/playerscores.xaml').read_text()
        self.assertIn('ImageSource="{Binding RaceIcon,',scores)
        self.assertIn('Binding ScarModel[vietnam_hud]',scores)
        resources=(ROOT/'assets/ui/resources/hudresources.xaml').read_text()
        custom=resources.split('x:Key="VietnamBuffaloCounter"')[1]
        self.assertIn('Path="Replay.IsObserver"',custom)
        self.assertIn('Path="IsReplay"',custom)
        self.assertNotIn('DoubleAnimation',custom)
        self.assertNotIn('UnitType="official"',custom)
    def test_native_visibility_conditions_preserved(self):
        old=(ROOT/'output/release_0710/hud/official/cardinalhudpage.xaml').read_text(encoding='utf-8-sig')
        new=(ROOT/'assets/ui/hud/pages/cardinalhudpage.xaml').read_text()
        extract=lambda s: s.split('<!--  Chinese Imperial Officers  -->')[1].split('<ContentControl.Visibility>')[1].split('</ContentControl.Visibility>')[0]
        self.assertEqual(extract(old),extract(new))
    def test_marker_only_change_and_lifecycle(self):
        p=(ROOT/'assets/scar/vietnam/paddy_wood.scar').read_text()
        self.assertIn('DataTemplate = "VietnamBuffaloSupervisionTemplate"',p)
        self.assertIn('not UI_IsReplay()',p)
        self.assertIn('UI_DestroyTagForPosition(watch.marker)',p)
        mode=(ROOT/'assets/scar/winconditions/VietnamMode.scar').read_text()
        for hook in ['Start','Update','Restore','Cleanup']:self.assertIn('VietnamPresentation_'+hook+'()',mode)

if __name__=='__main__':unittest.main(verbosity=2)

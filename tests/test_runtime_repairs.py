"""Lua behavior fixtures; these do not establish native engine behavior."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools/python'))
from lupa.lua51 import LuaRuntime

PREFIX = 'b7fcea91257b408fb9e8ae4d8bc402e1:'
FIXTURE = r'''
now=0; logs={}; network={}; rules={}; globals={}; properties={}; moves={}; upgrades={}
PLAYERS={{id=11,index=1},{id=22,index=2},{id=33,index=3}}
localPlayer=11; races={[11]='chinese',[22]='chinese',[33]='english'}
entities={}; squads={}; selected={}; registry={}; phaseCallback=nil; liveGroups=0
TP_Issued=3; OT_Enemy=2; GE_ConstructionComplete=1
local prefix='b7fcea91257b408fb9e8ae4d8bc402e1:'
function print(s) logs[#logs+1]=s end
function import() end
function Core_RegisterModule() end
function Core_GetPlayersTableEntry(id) for _,p in ipairs(PLAYERS) do if p.id==id then return p end end end
function Game_GetLocalPlayer() return localPlayer end
function Player_GetRaceName(id) return races[id] end
function Player_IsAlive(id) return id~=99 end
function UI_IsReplay() return false end
function World_GetGameTime() return now end
function Rule_AddInterval(f) rules[f]=true end
function Rule_AddOneShot(f) rules[f]=true end
function Rule_Remove(f) rules[f]=nil end
function Rule_AddGlobalEvent(f) globals[f]=true end
function Rule_RemoveGlobalEvent(f) globals[f]=nil end
function Network_RegisterEvent(n) network[n]=true end
function Network_RemoveEvent(n) network[n]=nil end
function Network_CallEvent(n,m) sentMessage=m;_G[n](localPlayer,m) end
function UI_SetModalAbilityPhaseCallback(f) phaseCallback=f end
function UI_ClearModalAbilityPhaseCallback() phaseCallback=nil end
function UI_SetPropertyValue(e,p,v) properties[e]=properties[e] or {};properties[e][p]=v end
function DynastyUI_Show(v) dynastyFlag=v end
function DynastyUI_HideDropdown() dropdown=false end
function BP_GetEntityBlueprint(n) return n end
function BP_GetAbilityBlueprint(n) return n end
function BP_GetUpgradeBlueprint(n) return n end
function BP_GetName(n) return n end
function Player_HasUpgrade(_,n) return upgrades[n]==true end
function Entity_GetBlueprint(e) return e.bp end
function Entity_ConvertBlueprint(e,bp) e.bp=bp;e.conversions=(e.conversions or 0)+1 end
function Entity_GetID(e) return e.id end
function Entity_IsValid(id) assert(type(id)=='number');return registry[id]~=nil end
function Entity_FromID(id) return registry[id] end
function Entity_IsAlive(e) return not e.dead end
function Entity_GetHealth(e) return e.health or 100 end
function Entity_GetHealthMax(e) return e.maximum or 100 end
function Entity_SetHealth(e,fraction) e.health=fraction*Entity_GetHealthMax(e) end
function Entity_CanCurrentlyBeDamaged(e) return not e.invulnerable end
function Entity_Kill(e) e.dead=true;e.health=0 end
function Entity_IsBuilding(e) return e.building==true end
function Entity_IsInHold(e) return e.held==true end
function Entity_GetSquad(e) return e.squad end
function Entity_IsUnderConstruction(e) return e.incomplete==true end
function Entity_GetBuildingProgress(e) return e.progress or 1 end
function Entity_ForceConstruct(e) e.incomplete=false;e.progress=1 end
function Entity_GetPosition(e) return {x=e.x or 0,y=0,z=e.z or 0} end
function Entity_IsOfType(e,t) return e.types and e.types[t] or false end
function World_Pos(x,y,z) return {x=x,y=y,z=z,native=true} end
function EGroup_CreateUnique() liveGroups=liveGroups+1;return {} end
function EGroup_Destroy(g) liveGroups=liveGroups-1 end
function EGroup_Count(g) return #g end
function EGroup_GetEntityAt(g,i) return g[i] end
function Player_GetEntitiesEGroup(id,g) for _,e in ipairs(entities) do if e.owner==id then g[#g+1]=e end end end
function World_GetEntitiesNearPoint(id,g,pos,radius,relation)
 assert(relation==OT_Enemy)
 for _,e in ipairs(entities) do
  if e.owner==22 and ((e.x or 0)-pos.x)^2+((e.z or 0)-pos.z)^2<=radius^2 then g[#g+1]=e end
 end
end
function SGroup_CreateUniqueWithPrefix() liveGroups=liveGroups+1;return {} end
function SGroup_Destroy() liveGroups=liveGroups-1 end
function SGroup_Count(g) return #g end
function SGroup_GetSquadAt(g,i) return g[i] end
function Misc_GetSelectedSquads(g) for _,s in ipairs(selected) do g[#g+1]=s end end
function Misc_GetMouseOverEntity() return hovered end
function Misc_IsMouseOverEntity() return hovered~=nil end
function Misc_GetMouseOnTerrain() return {x=500,y=0,z=500} end
function Player_GetSquads(id) local g={};for _,s in ipairs(squads) do if s.owner==id then g[#g+1]=s end end;return g end
function Squad_GetID(s) return s.id end
function Squad_IsAlive(s) return not s.dead end
function Squad_IsOfType(s,t) return s.siege==true and t=='siege' end
function Squad_HasAbility(s) return s.ability~=false end
function Squad_GetFirstEntity(s) return s.entity end
function World_GetSpawnablePosition(p,e) assert(p.native);if blocked then return nil end;return World_Pos(p.x,p.y,p.z) end
function Squad_SetPosition(s,p,toward) moves[#moves+1]={id=s.id,x=p.x,z=p.z};s.entity.x=p.x;s.entity.z=p.z end
function building(id,name,x,owner)
 local e={id=id,bp=prefix..name,x=x,owner=owner or 11,building=true}
 registry[id]=e;entities[#entities+1]=e;return e
end
function unit(id,x,owner)
 local e={id=id,x=x,owner=owner or 11,squad={}}
 registry[id]=e;entities[#entities+1]=e;return e
end
function squad(id,x,owner)
 local e=unit(id+1000,x,owner);local s={id=id,entity=e,owner=owner or 11}
 e.squad=s;squads[#squads+1]=s;return s
end
'''


class RuntimeFixture(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        for name in ('blueprints', 'traps'):
            self.lua.execute((ROOT / f'assets/scar/vietnam/{name}.scar').read_text())
        self.g = self.lua.globals()

    def runlua(self, source):
        return self.lua.execute(source)

    def has_log(self, text):
        return any(text in self.g.logs[i] for i in range(1, len(self.g.logs)+1))

    def tearDown(self):
        self.assertEqual(self.g.liveGroups, 0, 'temporary group leaked')


class DynastyRepairTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.lua.execute((ROOT / 'assets/scar/winconditions/VietnamMode.scar').read_text())

    def test_vietnam_collapses_parent_and_closes_dropdown(self):
        self.runlua("VietnamModeState.civilizations[1]='vietnam';dropdown=true;VietnamMode_RefreshDynastyUI()")
        self.assertIsNotNone(self.g.properties['DynastyUI'])
        self.assertEqual(self.g.properties['DynastyUI'].Visibility, 'Collapsed')
        self.assertFalse(self.g.properties['DynastyUI'].IsHitTestVisible)
        self.assertFalse(self.g.dropdown)

    def test_china_view_restores_parent_and_dynasty(self):
        self.runlua("VietnamModeState.civilizations[1]='vietnam';VietnamMode_RefreshDynastyUI();localPlayer=22;VietnamModeState.civilizations[2]='china';VietnamMode_RefreshDynastyUI()")
        self.assertIsNotNone(self.g.properties['DynastyUI'])
        self.assertEqual(self.g.properties['DynastyUI'].Visibility, 'Visible')
        self.assertTrue(self.g.dynastyFlag)

    def test_ui_recreation_gets_collapsed_again(self):
        self.runlua("VietnamModeState.civilizations[1]='vietnam';VietnamMode_RefreshDynastyUI();properties={};VietnamMode_RefreshDynastyUI()")
        self.assertIsNotNone(self.g.properties['DynastyUI'])
        self.assertEqual(self.g.properties['DynastyUI'].Visibility, 'Collapsed')

    def test_non_chinese_view_releases_override_without_forcing_dynasty_on(self):
        self.runlua("VietnamModeState.civilizations[1]='vietnam';VietnamMode_RefreshDynastyUI();localPlayer=33;VietnamMode_RefreshDynastyUI()")
        self.assertEqual(self.g.properties['DynastyUI'].Visibility, 'Visible')
        self.assertFalse(self.g.dynastyFlag)

    def test_controller_dropdown_closes_without_selected_town_center(self):
        # Match the guard in the official ToggleDropdown/HideDropdown helpers.
        self.runlua('''
            _dynasty={is_ui_created=true,data_context={is_dropdown_visible=true}}
            cancelHandler=true
            function UI_IsXboxControllerUI() return true end
            function Game_HasOnlySelectedEntitiesOfType() return false end
            function UI_RemoveEventHandler(e,event,callback)
                assert(e=='Scar' and event=='HUDPageBase.Cancel' and callback=='DynastyUI_HideDropdown')
                cancelHandler=false
            end
            function DynastyUI_ToggleDropdown()
                local tc=Game_HasOnlySelectedEntitiesOfType('town_center')
                if not UI_IsXboxControllerUI() or tc then
                    _dynasty.data_context.is_dropdown_visible=not _dynasty.data_context.is_dropdown_visible
                end
            end
            function DynastyUI_HideDropdown()
                if _dynasty.data_context.is_dropdown_visible then DynastyUI_ToggleDropdown() end
            end
            VietnamModeState.civilizations[1]='vietnam'
            VietnamMode_RefreshDynastyUI()
        ''')
        self.assertFalse(self.g._dynasty.data_context.is_dropdown_visible)
        self.assertFalse(self.g.cancelHandler)
        self.runlua("localPlayer=22;VietnamModeState.civilizations[2]='china';VietnamMode_RefreshDynastyUI()")
        self.assertFalse(self.g._dynasty.data_context.is_dropdown_visible)






class PackageVerificationTests(unittest.TestCase):
    def test_normalization_allows_only_bom_and_line_ending_differences(self):
        from tools.verify_runtime_package import normalized
        self.assertEqual(normalized(b'\xef\xbb\xbfa\r\nb\r\n'), normalized(b'a\nb\n'))
        self.assertNotEqual(normalized(b'a\nb'), normalized(b'a\nc'))

    def test_comparison_handles_case_and_detects_changed_or_missing_scripts(self):
        import contextlib
        import io
        import tempfile
        from types import SimpleNamespace
        from tools.verify_runtime_package import compare_runtime
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root/'assets/scar'
            folder.mkdir(parents=True)
            (folder/'VietnamMode.scar').write_text('new\n')
            data = {'/SCAR/vietnammode.scar': b'new\r\n'}
            archive = SimpleNamespace(walk=SimpleNamespace(files=lambda: data), readbytes=lambda p: data[p])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(compare_runtime(archive,root), [])
                data['/SCAR/vietnammode.scar'] = b'old\n'
                self.assertEqual(compare_runtime(archive,root), ['scar/VietnamMode.scar'])
                data.clear()
                self.assertEqual(compare_runtime(archive,root), ['scar/VietnamMode.scar'])


if __name__ == '__main__':
    unittest.main()

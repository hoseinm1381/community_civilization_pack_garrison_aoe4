import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    import lupa.lua51
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / '.tools/python'))
from lupa.lua51 import LuaRuntime

FIXTURE = r'''
now=0; localPlayer=11; exists=true; conversions={}; network={}; rules={}; commands={}; ai={}; warnings={}; ui={}; protected={};messages={};production={}
ITEM_LOCKED=1; ITEM_DEFAULT=0; ITEM_REMOVED=2; DB_Button1=1; DB_Button2=2; DC_Default=0
PLAYERS={{index=1,id=11,isHuman=true},{index=2,id=22,isHuman=true},{index=3,id=33,isHuman=false}}
alive={[11]=true,[22]=true,[33]=true}; races={[11]='chinese',[22]='chinese',[33]='english'}
function import() end
function Core_RegisterModule() end
function Core_GetPlayersTableEntry(id) for _,p in ipairs(PLAYERS) do if p.id==id then return p end end end
function Player_IsAlive(id) return alive[id] end
function Player_GetRaceName(id) return races[id] end
function World_GetGameTime() return now end
function Game_GetLocalPlayer() return localPlayer end
function UI_IsReplay() return false end
local utf8_mt={__concat=function() error('attempt to concatenate a utf8_mt value') end}
function Loc_GetString(s) return setmetatable({value=s},utf8_mt) end
function Loc_ToAnsi(s) assert(getmetatable(s)==utf8_mt);return s.value end
function EBP_Exists(name)
    if string.find(name,'vn_',1,true) then
        return exists and string.sub(name,1,33)=='b7fcea91257b408fb9e8ae4d8bc402e1:'
    end
    return exists
end
function SBP_Exists(name) return exists end
function Network_RegisterEvent(name) network[name]=true end
function Network_RemoveEvent(name) network[name]=nil end
function Network_CallEvent(name,message) _G[name](localPlayer,message) end
function Player_SetAllCommandAvailability(id,value,reason) commands[id]=value end
function Player_SetEntityProductionAvailability(id,bp,value,reason)
    production[id]=production[id] or {};production[id][bp]={value=value,reason=reason}
end
function AI_IsEnabled(id) return ai[id]~=false end
function AI_Enable(id,value) ai[id]=value end
function Rule_AddInterval(fn) rules[fn]=true end
function Rule_AddOneShot(fn) rules[fn]=true end
function Rule_Remove(fn) rules[fn]=nil end
function Rule_AddGlobalEvent() end
function Rule_RemoveGlobalEvent() end
function Game_GetLocalPlayer() return localPlayer end
function DynastyUI_Show() end
function DynastyUI_HideDropdown() end
function UI_SetPropertyValue() end
function VietnamLifecycle_Start() end
function VietnamLifecycle_Cleanup() end
function UI_SystemMessageShow(s) assert(type(s)=='string');ui.banner=s;messages[s]=true end
function UI_SystemMessageHide(s) assert(type(s)=='string');messages[s]=nil;if ui.banner==s then ui.banner=nil end end
function UIWarning_Show(s) warnings[#warnings+1]=s end
function UI_MessageBoxReset() end
function UI_MessageBoxSetText(title,body) ui.title=title;ui.body=body end
function UI_MessageBoxSetButton() end
function UI_MessageBoxShow(_,callback) ui.callback=callback end
function UI_MessageBoxHide() ui.callback=nil end
function BP_GetEntityBlueprint(name) return name end
function BP_GetSquadBlueprint(name) return name end
function BP_GetName(bp) return bp end
function Entity_GetID(e) assert(type(e)=='table' and type(e.id)=='number');return e.id end
function Entity_IsValid(id) assert(type(id)=='number','Entity_IsValid requires a numeric ID');return entityRegistry[id]~=nil end
function Entity_FromID(id) assert(type(id)=='number');return entityRegistry[id] end
function Entity_GetPlayerOwner(e) return e.owner end
function Entity_GetInvulnerableMinCap(e) return e.cap or 0 end
function Entity_GetHealthPercentage(e) return 1 end
function Entity_SetInvulnerableMinCap(e,value) e.cap=value end
function Entity_GetBlueprint(e) return e.bp end
function Entity_GetPosition(e) return {x=10,y=0,z=10} end
function World_Pos(x,y,z) return {x=x,y=y,z=z} end
function Squad_CreateAndSpawnToward() end
RT_Food=1
function Player_GetResource() return 200 end
function Player_SetResource() end
function Entity_GetFilledHoldSquadSlots(e) return e.hold or 0 end
function Entity_IsUnderConstruction(e) return e.incomplete or false end
function Entity_ConvertBlueprint(e,bp) conversions[#conversions+1]={kind='entity',owner=e.owner};e.bp=bp end
function Squad_ConvertBlueprint(s,bp) conversions[#conversions+1]={kind='squad',owner=s.owner};s.bp=bp end
function Squad_GetBlueprint(s) return s.bp end
function Squad_GetFirstEntity(s) return s.entity end
entities={{id=101,owner=11,bp='building_town_center_capital_chi'},{id=102,owner=22,bp='building_town_center_capital_chi'}}
squads={{owner=11,bp='unit_villager_1_chi',entity={id=201,owner=11,bp='unit_villager_1_chi'}},{owner=22,bp='unit_villager_1_chi',entity={id=202,owner=22,bp='unit_villager_1_chi'}}}
entityRegistry={[101]=entities[1],[102]=entities[2],[201]=squads[1].entity,[202]=squads[2].entity}
function EGroup_CreateUnique() return {} end
function EGroup_Destroy() end
function EGroup_Count(g) return #g end
function EGroup_GetEntityAt(g,i) return g[i] end
function World_GetAllEntities(g) for _,e in ipairs(entities) do g[#g+1]=e end;for _,s in ipairs(squads) do g[#g+1]=s.entity end end
function Player_GetEntitiesEGroup(id,g)
    for _,e in ipairs(entities) do if e.owner==id then g[#g+1]=e end end
    for _,s in ipairs(squads) do if s.entity.owner==id then g[#g+1]=s.entity end end
end
function Player_GetSquads(id) local g={};for _,s in ipairs(squads) do if s.owner==id then g[#g+1]=s end end;return g end
function SGroup_Count(g) return #g end
function SGroup_GetSquadAt(g,i) return g[i] end
'''


class EngineAdapterTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        for path in ['assets/scar/vietnam/selection_core.scar', 'assets/scar/vietnam/initialization.scar', 'assets/scar/winconditions/VietnamMode.scar']:
            self.lua.execute((ROOT / path).read_text())
        self.g = self.lua.globals()

    def test_missing_tuning_does_not_lock_or_resolve_custom_blueprints(self):
        self.g.exists = False
        self.g.VietnamMode_OnInit()
        self.assertEqual(len(list(self.g.commands.keys())), 0)
        self.assertEqual(len(self.g.conversions), 0)
        self.assertEqual(len(list(self.g.network.keys())), 0)

    def test_sender_identity_controls_conversion_and_china_is_untouched(self):
        self.lua.execute('''
            for i=1,5 do
                local e={id=300+i,owner=11,bp='unit_villager_1_chi'}
                entityRegistry[e.id]=e
                squads[#squads+1]={owner=11,bp='unit_villager_1_chi',entity=e}
            end
            local scout={id=310,owner=11,bp='unit_scout_1_chi'}
            entityRegistry[scout.id]=scout
            squads[#squads+1]={owner=11,bp='unit_scout_1_chi',entity=scout}
        ''')
        self.g.VietnamMode_OnInit()
        self.g.VietnamMode_NetChoose(11, 'vietnam')
        self.g.VietnamMode_NetChoose(22, 'china')
        self.g.VietnamMode_Tick()
        self.assertGreater(len(self.g.conversions), 0)
        for i in range(1, len(self.g.conversions)+1):
            self.assertEqual(self.g.conversions[i].owner, 11)
        self.assertEqual(self.g.entities[2].bp, 'building_town_center_capital_chi')
        self.assertEqual(self.g.squads[2].bp, 'unit_villager_1_chi')
        self.assertEqual(self.g.commands[11], 0)
        self.assertEqual(self.g.commands[22], 0)
        self.assertTrue(self.g.ai[33])
        self.assertEqual(self.g.production[11]['building_unit_ranged_control_chi'].value, 2)
        self.assertIsNone(self.g.production[22])
        self.g.VietnamMode_OnGameOver()
        self.assertEqual(self.g.production[11]['building_unit_ranged_control_chi'].value, 0)
        self.assertIsNone(self.g.production[22])

    def test_ai_and_non_chinese_humans_cannot_choose(self):
        self.g.races[22] = 'english'
        self.g.VietnamMode_OnInit()
        self.g.VietnamMode_NetChoose(33, 'vietnam')
        self.g.VietnamMode_NetChoose(22, 'vietnam')
        self.assertIsNone(self.g.VietnamModeState.selection.players[1].choice)
        self.assertIsNone(self.g.VietnamModeState.selection.players[2])

    def test_timeout_releases_all_players_and_restores_protection(self):
        self.g.VietnamMode_OnInit()
        self.assertEqual(self.g.entities[1].cap, 1)
        self.assertFalse(self.g.ai[33])
        self.g.now = 30
        self.g.VietnamMode_Tick()
        self.assertEqual(len(self.g.conversions), 0)
        for i in range(1,4):
            self.assertEqual(self.g.commands[self.g.PLAYERS[i].id], 0)
        self.assertTrue(self.g.ai[33])
        self.assertEqual(self.g.entities[1].cap, 0)

    def test_abort_restores_previous_ai_state_and_removes_network_handler(self):
        self.g.ai[33] = False
        self.g.VietnamMode_OnInit()
        self.g.VietnamMode_OnGameOver()
        self.assertFalse(self.g.ai[33])
        self.assertEqual(self.g.commands[11], 0)
        self.assertIsNone(self.g.network['VietnamMode_NetChoose'])
        self.g.VietnamMode_NetChoose(11, 'vietnam')
        self.assertEqual(len(self.g.conversions), 0)

    def test_occupied_starting_tc_is_rejected_before_any_conversion(self):
        self.g.entities[1].hold = 1
        self.assertFalse(self.g.VietnamInitialization_Apply(self.g.PLAYERS[1]))
        self.assertEqual(len(self.g.conversions), 0)

    def test_opening_cleanup_skips_destroyed_entities_without_using_stale_handles(self):
        self.g.VietnamMode_OnInit()
        self.g.entityRegistry[101] = None
        self.g.VietnamMode_OnGameOver()
        self.assertEqual(self.g.entities[2].cap, 0)
        self.assertEqual(self.g.commands[11], 0)
        self.assertEqual(self.g.commands[22], 0)

    def test_no_chinese_humans_does_not_hold_the_match(self):
        self.g.races[11] = 'english'
        self.g.races[22] = 'english'
        self.g.VietnamMode_OnInit()
        self.assertEqual(len(list(self.g.commands.keys())), 0)
        self.assertEqual(len(list(self.g.network.keys())), 0)

    def test_no_eligible_warning_composes_plain_text_from_localization(self):
        self.g.VietnamMode_NoEligibleWarning()
        self.assertIn('chinese', self.g.ui.banner)

    def test_missing_blueprint_warning_uses_plain_system_message(self):
        self.g.VietnamMode_MissingTuningWarning()
        self.assertEqual(self.g.ui.banner, '$b7fcea91257b408fb9e8ae4d8bc402e1:1008')
        self.assertEqual(len(self.g.warnings), 0)
        self.assertTrue(self.g.rules[self.g.VietnamMode_HideWarning])

    def test_countdown_replaces_its_banner_and_cleans_only_its_own_text(self):
        self.g.VietnamMode_OnInit()
        self.g.UI_SystemMessageShow('another module message')
        self.g.now = 1
        self.g.VietnamMode_Tick()
        self.g.now = 2
        self.g.VietnamMode_Tick()
        self.assertEqual(len(list(self.g.messages.keys())), 2)
        self.g.now = 30
        self.g.VietnamMode_Tick()
        self.assertEqual(list(self.g.messages.keys()), ['another module message'])


if __name__ == '__main__':
    unittest.main()

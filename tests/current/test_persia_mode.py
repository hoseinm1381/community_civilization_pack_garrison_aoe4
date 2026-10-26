import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.tools/python'))
from lupa.lua51 import LuaRuntime


class ModePairTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            env = {hold={}, network={}, ai={}, released=0, vn=0, ps=0, clock=0, fail=false, partial=false}
            import=function() end
            print=function() end
            Core_RegisterModule=function() end
            PLAYERS={{id=11,index=1,isHuman=true},{id=22,index=2,isHuman=true},{id=33,index=3,isHuman=false}}
            function Player_GetRaceName(id) return id == 11 and "chinese" or "sultanate" end
            function Player_IsAlive() return true end
            function Core_GetPlayersTableEntry(id) for _,p in ipairs(PLAYERS) do if p.id==id then return p end end end
            function EBP_Exists() return true end
            function SBP_Exists() return true end
            function PersiaBlueprints_Available() return true end
            function World_GetGameTime() return env.clock end
            function Network_RegisterEvent(name) env.network[name]=true end
            function Network_RemoveEvent(name) env.network[name]=nil end
            ITEM_LOCKED=1; ITEM_DEFAULT=0
            function Player_SetAllCommandAvailability(id,value) env.hold[id]=value end
            function AI_IsEnabled() return true end
            function AI_Enable(id,value) env.ai[id]=value end
            function Player_GetEntitiesEGroup() end
            function EGroup_CreateUnique() return {} end
            function EGroup_Destroy() end
            function EGroup_Count() return 0 end
            function Rule_AddOneShot() end
            function Rule_AddInterval() end
            function Rule_AddGlobalEvent() end
            function Rule_RemoveGlobalEvent() end
            function Rule_Remove() end
            function UI_IsReplay() return true end
            function Game_GetLocalPlayer() return 11 end
            function DynastyUI_Show() end
            function DynastyUI_HideDropdown() end
            function UI_SetPropertyValue() end
            function VietnamLifecycle_Start(civs) env.civs=civs end
            function PersiaLifecycle_Start(civs) env.pcivs=civs end
            function VietnamInitialization_Apply() env.vn=env.vn+1; return true end
            function PersiaInitialization_Apply()
                env.ps=env.ps+1
                if env.fail then return false,"injected",env.partial end
                return true,"applied",true
            end
        ''')
        self.lua.execute((ROOT / 'assets/scar/vietnam/selection_core.scar').read_text())
        self.lua.execute((ROOT / 'assets/scar/winconditions/VietnamMode.scar').read_text())

    def test_mixed_pairs_share_one_deadline_and_release_hold(self):
        g = self.lua.globals()
        g.VietnamMode_OnInit()
        self.assertIsNotNone(g.VietnamModeState.selection.players[2], 'Delhi human must receive selection')
        self.assertIsNone(g.VietnamModeState.selection.players[3])
        g.VietnamMode_NetChoose(22, 'vietnam')
        self.assertIsNone(g.VietnamModeState.selection.players[2].choice)
        g.VietnamMode_NetChoose(22, 'persia')
        g.VietnamMode_NetChoose(11, 'vietnam')
        g.VietnamMode_Tick()
        self.assertEqual(g.env.ps, 1)
        self.assertEqual(g.env.vn, 1)
        self.assertEqual(g.env.civs[1], 'vietnam')
        self.assertEqual(g.env.civs[2], 'persia')
        self.assertEqual(g.env.hold[22], 0)
        self.assertTrue(g.env.ai[33])
        self.assertFalse(g.VietnamModeState.held)
        self.assertIsNone(g.env.network['VietnamMode_NetChoose'])

    def test_timeout_retains_delhi_without_conversion(self):
        g = self.lua.globals()
        g.VietnamMode_OnInit()
        g.env.clock = 30
        g.VietnamMode_Tick()
        self.assertEqual(g.env.ps, 0)
        self.assertEqual(g.VietnamModeState.civilizations[2], 'delhi')
        self.assertEqual(g.env.hold[22], 0)

    def test_missing_persia_does_not_disable_chinese_pair(self):
        self.lua.execute('PersiaBlueprints_Available=function() return false end')
        g = self.lua.globals()
        g.VietnamMode_OnInit()
        self.assertIsNotNone(g.VietnamModeState.selection.players[1])
        self.assertIsNone(g.VietnamModeState.selection.players[2])
        self.assertTrue(g.VietnamModeState.unavailable[2])

    def test_missing_vietnam_does_not_disable_delhi_pair(self):
        self.lua.execute('EBP_Exists=function(name) return not string.find(name,"vn_",1,true) end')
        g = self.lua.globals()
        g.VietnamMode_OnInit()
        self.assertIsNone(g.VietnamModeState.selection.players[1])
        self.assertIsNotNone(g.VietnamModeState.selection.players[2])

    def test_exception_during_initialization_releases_hold(self):
        self.lua.execute('PersiaInitialization_Apply=function() error("injected") end')
        g = self.lua.globals()
        g.VietnamMode_OnInit()
        g.VietnamMode_NetChoose(11, 'china')
        g.VietnamMode_NetChoose(22, 'persia')
        g.VietnamMode_Tick()
        self.assertEqual(g.VietnamModeState.civilizations[2], 'initialization_failed')
        self.assertFalse(g.VietnamModeState.held)
        self.assertEqual(g.env.hold[22], 0)

    def test_preflight_rejection_retains_original_and_ai_cannot_choose(self):
        g = self.lua.globals()
        g.VietnamMode_OnInit()
        g.VietnamMode_NetChoose(33, 'persia')
        self.assertIsNone(g.VietnamModeState.selection.players[3])
        g.env.fail = True
        g.VietnamMode_NetChoose(11, 'china')
        g.VietnamMode_NetChoose(22, 'persia')
        g.VietnamMode_Tick()
        self.assertEqual(g.VietnamModeState.civilizations[2], 'delhi')
        self.assertFalse(g.VietnamModeState.held)
        g.VietnamMode_NetChoose(22, 'persia')
        self.assertEqual(g.env.ps, 1)

    def test_partial_initialization_failure_releases_hold_and_does_not_claim_delhi(self):
        g = self.lua.globals()
        g.VietnamMode_OnInit()
        g.env.fail = True
        g.env.partial = True
        g.VietnamMode_NetChoose(11, 'china')
        g.VietnamMode_NetChoose(22, 'persia')
        g.VietnamMode_Tick()
        self.assertEqual(g.VietnamModeState.civilizations[2], 'initialization_failed')
        self.assertFalse(g.VietnamModeState.held)
        self.assertIsNone(g.env.network['VietnamMode_NetChoose'])
        self.assertEqual(g.env.hold[22], 0)


if __name__ == '__main__':
    unittest.main()

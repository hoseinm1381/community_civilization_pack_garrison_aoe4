from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.tools/python'))
from lupa.lua51 import LuaRuntime


class LandmarkLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            print=function() end
            PLAYERS={{id=11,index=1},{id=22,index=2},{id=33,index=3}}
            PersiaInitializationState={applied={}}
            env={markers={},completed=0,removed=0,groups=0,rules=0}
            entities={{id=1,owner=11,bp="ps_building_landmark_age1_military_divan_persia",alive=true,progress=1,active=true}}
            function EGroup_CreateUnique() env.groups=env.groups+1;return {} end
            function EGroup_Destroy() env.groups=env.groups-1 end
            function Player_GetEntitiesEGroup(id,g) for _,e in ipairs(entities) do if e.owner==id then table.insert(g,e) end end end
            function EGroup_Count(g) return #g end
            function EGroup_GetEntityAt(g,i) return g[i] end
            function Entity_GetID(e) return e.id end
            function Entity_IsValid(id) return id>0 end
            function Entity_IsAlive(e) return e.alive end
            function Entity_GetHealth(e) return e.alive and 100 or 0 end
            function Entity_IsUnderConstruction(e) return e.progress<1 end
            function Entity_GetBuildingProgress(e) return e.progress end
            function Entity_GetStateModelBool(e,key) assert(key=="landmark_active");return e.active end
            function Entity_GetBlueprint(e) return e.bp end
            function BP_GetName(bp) return bp end
            function BP_GetUpgradeBlueprint(bp) assert(string.find(bp,"ps_gundeshapur_functioning",1,true));return bp end
            function Player_IsAlive() return true end
            function Player_HasUpgrade(id) return env.markers[id] or false end
            function Player_CompleteUpgrade(id) env.markers[id]=true;env.completed=env.completed+1 end
            function Player_RemoveUpgrade(id) env.markers[id]=false;env.removed=env.removed+1 end
            function Rule_AddInterval() env.rules=env.rules+1 end
            function Rule_Remove() env.rules=env.rules-1 end
        ''')
        self.lua.execute((ROOT/'assets/scar/persia/lifecycle.scar').read_text())
        self.g=self.lua.globals()

    def start(self):
        self.g.PersiaLifecycle_Start(self.lua.table_from({1:'persia',2:'persia',3:'delhi'}))

    def test_ruin_repair_and_repeated_updates_are_idempotent(self):
        self.start();self.g.PersiaLifecycle_Tick()
        self.assertEqual(self.g.env.completed,1)
        self.g.entities[1].active=False
        self.g.PersiaLifecycle_Tick();self.g.PersiaLifecycle_Tick()
        self.assertEqual(self.g.env.removed,1)
        self.g.entities[1].active=True
        self.g.PersiaLifecycle_Tick()
        self.assertEqual(self.g.env.completed,2)
        self.assertEqual(self.g.env.groups,0)

    def test_foundations_never_unlock_and_second_source_prevents_revocation(self):
        self.g.entities[1].progress=.5;self.start()
        self.assertEqual(self.g.env.completed,0)
        self.g.entities[1].progress=1
        self.lua.execute('entities[2]={id=2,owner=11,bp=entities[1].bp,alive=true,active=true,progress=1}')
        self.g.PersiaLifecycle_Tick()
        self.g.entities[1].alive=False
        self.g.PersiaLifecycle_Tick()
        self.assertEqual(self.g.env.removed,0)

    def test_capture_recomputes_both_owners_and_delhi_never_receives_marker(self):
        self.start();self.g.entities[1].owner=22;self.g.PersiaLifecycle_Tick()
        self.assertFalse(self.g.env.markers[11]);self.assertTrue(self.g.env.markers[22])
        self.g.entities[1].owner=33;self.g.PersiaLifecycle_Tick()
        self.assertFalse(self.g.env.markers[22]);self.assertIsNone(self.g.env.markers[33])

    def test_cleanup_removes_only_private_marker_and_interval(self):
        self.start();self.start();self.assertEqual(self.g.env.rules,1)
        self.g.PersiaLifecycle_Cleanup()
        self.assertEqual(self.g.env.rules,0);self.assertEqual(self.g.env.removed,1)


if __name__=='__main__':unittest.main()

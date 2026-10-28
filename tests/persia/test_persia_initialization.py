import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.tools/python'))
from lupa.lua51 import LuaRuntime


class PersiaInitializationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / 'assets/scar/persia/initialization.scar').exists(), 'Persia initializer must exist')
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            print = function() end
            env = {missing=false, later=false, mutations=0, groups=0, fail=false, noop=false}
            player = {id=1, index=1, isHuman=true}
            entities = {{id=1, bp="building_town_center_capital_sul"}}
            squads = {}
            for i=1,7 do
                local name = i == 7 and "unit_scout_1_sul" or "unit_villager_1_sul"
                local e = {id=i+1,bp=name}
                table.insert(entities,e)
                table.insert(squads,{bp=name,entity=e})
            end
            function Player_GetRaceName() return "sultanate" end
            function Player_IsAlive() return true end
            function EBP_Exists() return not env.missing end
            function SBP_Exists() return not env.missing end
            function BP_GetEntityBlueprint(name) return name end
            function BP_GetSquadBlueprint(name) return name end
            function BP_GetUpgradeBlueprint(name) return name end
            function Player_HasUpgrade() return env.later end
            function BP_GetName(name) return string.match(name,"[^:]+$") end
            function EGroup_CreateUnique() env.groups=env.groups+1; return {} end
            function EGroup_Destroy() env.groups=env.groups-1 end
            function Player_GetEntitiesEGroup(_,g) for _,e in ipairs(entities) do table.insert(g,e) end end
            function EGroup_Count(g) return #g end
            function EGroup_GetEntityAt(g,i) return g[i] end
            function Entity_GetID(e) return e.id end
            function Entity_IsValid(id) return id ~= 999 end
            function Entity_GetBlueprint(e) return e.bp end
            function Entity_IsUnderConstruction(e) return e.constructing or false end
            function Entity_GetFilledHoldSquadSlots(e) return e.occupied or 0 end
            function Player_GetSquads() return squads end
            function SGroup_Count(g) return #g end
            function SGroup_GetSquadAt(g,i) return g[i] end
            function Squad_GetBlueprint(s) return s.bp end
            function Squad_GetFirstEntity(s) return s.entity end
            function Entity_ConvertBlueprint(e,bp)
                env.mutations=env.mutations+1
                if env.fail then error("injected engine error") end
                if not env.noop then e.bp=bp end
            end
            function Squad_ConvertBlueprint(s,bp) env.mutations=env.mutations+1; s.bp=bp end
        ''')
        self.lua.globals()['import'] = lambda name: self.lua.execute((ROOT / 'assets/scar' / name).read_text())
        self.lua.execute((ROOT / 'assets/scar/persia/blueprints.scar').read_text().replace('Scar_AddInit(PersiaPrecache_Init)', ''))
        self.lua.execute((ROOT / 'assets/scar/persia/initialization.scar').read_text())

    def apply(self):
        return self.lua.globals().PersiaInitialization_Apply(self.lua.globals().player)

    def test_success_converts_entities_and_squads_and_rejects_duplicate(self):
        self.assertEqual(self.apply(), (True, 'applied', True))
        g = self.lua.globals()
        self.assertEqual(g.env.mutations, 15)
        self.assertEqual(g.env.groups, 0)
        self.assertIn('ps_unit_villager_1_sul', g.squads[1].bp)
        self.assertIn('ps_unit_villager_1_sul', g.squads[1].entity.bp)
        self.assertEqual(self.apply(), (False, 'already-applied', False))
        self.assertEqual(g.env.mutations, 15)

    def test_missing_blueprints_reject_before_mutation(self):
        self.lua.globals().env.missing = True
        self.assertEqual(self.apply(), (False, 'blueprints-unavailable', False))
        self.assertEqual(self.lua.globals().env.mutations, 0)

    def test_later_age_rejected_without_mutation(self):
        self.lua.globals().env.later = True
        self.assertEqual(self.apply(), (False, 'unsupported-age', False))
        self.assertEqual(self.lua.globals().env.mutations, 0)

    def test_occupied_tc_and_wrong_starting_counts_rejected(self):
        self.lua.globals().entities[1].occupied = 1
        self.assertEqual(self.apply(), (False, 'occupied-or-unfinished-capital', False))
        self.lua.globals().entities[1].occupied = 0
        self.lua.execute('table.remove(squads)')
        self.assertEqual(self.apply(), (False, 'unsupported-starting-army', False))
        self.assertEqual(self.lua.globals().env.groups, 0)

    def test_partial_failure_is_explicit_and_not_active(self):
        self.lua.globals().env.fail = True
        result = self.apply()
        self.assertFalse(result[0])
        self.assertTrue(result[2])
        self.assertIn('conversion-error', result[1])
        self.assertIsNone(self.lua.globals().PersiaInitializationState.applied[1])
        self.assertEqual(self.lua.globals().env.groups, 0)

    def test_failed_postcondition_is_partial_failure(self):
        self.lua.globals().env.noop = True
        self.assertEqual(self.apply(), (False, 'conversion-postcondition', True))


if __name__ == '__main__':
    unittest.main()

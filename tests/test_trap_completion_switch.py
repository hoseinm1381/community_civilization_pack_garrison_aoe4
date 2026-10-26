"""Exercise completion gating and timer continuity; native conversion needs game testing."""
import unittest

from test_runtime_repairs import RuntimeFixture, PREFIX


class TrapCompletionSwitchTests(RuntimeFixture):
    def test_firing_probe_reports_inactive_hardpoint_once_after_conversion(self):
        self.runlua("trap=building(499,'vn_building_bambo_outpost_chi',0);trap.hpactive=false")
        self.update(0)
        self.assertFalse(self.has_log('TRAP_WEAPON_PROBE'))
        self.update(1)
        self.assertTrue(self.has_log('hardpoints=1 hp0active=false'))
        count = sum('TRAP_WEAPON_PROBE' in self.g.logs[i] for i in range(1, len(self.g.logs)+1))
        self.update(2)
        self.assertEqual(count, sum('TRAP_WEAPON_PROBE' in self.g.logs[i] for i in range(1, len(self.g.logs)+1)))

    def setUp(self):
        super().setUp()
        self.runlua('function Entity_IsAttacking(e,duration) return e.attacked==true end')

    def update(self, now=0):
        self.g.VietnamTraps_Update(self.g.PLAYERS[1], self.lua.table_from([self.g.trap]), now)
        self.g.VietnamTraps_Tick(now)

    def test_unfinished_traps_keep_builder_blueprint_until_construction_finishes(self):
        for name in ('vn_building_bambo_outpost_chi', 'vn_building_defense_outpost_bambo_chi'):
            with self.subTest(name=name):
                self.runlua(f"trap=building(401,'{name}',15);trap.incomplete=true")
                self.update()
                self.assertEqual(self.g.trap.bp, PREFIX + name)
                self.assertIsNone(self.g.trap.conversions)
                self.g.trap.incomplete = False
                self.update(0.25)
                self.assertEqual(self.g.trap.bp, PREFIX + name + '_passable')

    def test_conversion_happens_once_and_does_not_replace_or_reposition_entity(self):
        self.runlua("trap=building(402,'vn_building_bambo_outpost_chi',15,22);trap.health=37;trap.z=29")
        self.update()
        self.update(10)
        self.assertEqual(self.g.trap.bp, PREFIX + 'vn_building_bambo_outpost_chi_passable')
        self.assertEqual(self.g.trap.conversions, 1)
        self.assertEqual((self.g.trap.id, self.g.trap.owner, self.g.trap.x, self.g.trap.z, self.g.trap.health),
                         (402, 22, 15, 29, 37))
        self.assertFalse(bool(self.g.trap.dead))

    def test_completed_passable_trap_retains_non_resetting_attack_lifetime(self):
        self.runlua("trap=building(403,'vn_building_defense_outpost_bambo_chi_passable',0);trap.attacked=true")
        self.update(10)
        self.update(13.99)
        self.assertFalse(bool(self.g.trap.dead))
        self.update(14)
        self.assertTrue(self.g.trap.dead)
        self.assertIsNone(self.g.trap.conversions)

    def test_first_attack_seen_on_completion_is_not_lost_by_conversion(self):
        self.runlua("trap=building(404,'vn_building_bambo_outpost_chi',0);trap.attacked=true")
        # Native conversion may clear attack history; capture it before converting.
        self.runlua('function Entity_ConvertBlueprint(e,bp) e.bp=bp;e.attacked=false end')
        self.update(2)
        self.assertEqual(self.g.trap.bp, PREFIX + 'vn_building_bambo_outpost_chi_passable')
        self.update(6)
        self.assertTrue(self.g.trap.dead)

    def test_dead_traps_and_unrelated_buildings_are_never_converted(self):
        self.runlua("trap=building(405,'vn_building_bambo_outpost_chi',0);trap.dead=true")
        self.update()
        self.assertIsNone(self.g.trap.conversions)
        self.runlua("trap=building(406,'vn_building_house_control_chi',0)")
        self.update()
        self.assertIsNone(self.g.trap.conversions)


if __name__ == '__main__':
    unittest.main()

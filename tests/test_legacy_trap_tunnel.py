"""Parity with the explicitly selected donor plus the only SCAR exception: lifetime."""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from test_runtime_repairs import RuntimeFixture, PREFIX

ROOT = Path(__file__).resolve().parents[1]
OLD = Path(json.loads((ROOT/'workspace.json').read_text())['donor_root'])/'assets/attrib/instances'
NEW = ROOT/'assets/attrib/instances'
RECORDS = json.loads((ROOT/'docs/migration-map.json').read_text())['instances']
MAPPING = {r['source']:r['destination'] for r in RECORDS}


def record(name):
    return next(r for r in RECORDS if r['destination'].endswith('\\'+name))


def original(name):
    return ET.parse(OLD/(record(name)['source']+'.xml')).getroot()


def current(name):
    return ET.parse(NEW/(record(name)['destination']+'.xml')).getroot()


def gameplay(node):
    """Compare every gameplay value, ignoring only project/locale identity."""
    attrs = dict(node.attrib)
    if node.tag == 'instance_reference' and attrs.get('value') in MAPPING:
        attrs['value'] = MAPPING[attrs['value']]
        attrs['mod'] = PREFIX[:-1]
    children = [gameplay(c) for c in node if c.tag != 'locstring' and not (c.tag == 'uniqueid' and c.get('name') == 'pbgid')]
    return node.tag, attrs, children


def combat(scope):
    return next(ex for ex in scope.findall('./list/template_reference') if ex.get('value') == 'ebpextensions\\combat_ext')


class OriginalTuningParityTests(unittest.TestCase):
    def test_both_traps_have_original_native_combat_in_every_variant(self):
        for name in ('vn_building_bambo_outpost_chi','vn_building_defense_outpost_bambo_chi'):
            a,b = original(name),current(name)
            for variant in (None,'campaign'):
                with self.subTest(name=name,variant=variant):
                    aa,bb = (a,b) if variant is None else (a.find(f"variant[@name='{variant}']"),b.find(f"variant[@name='{variant}']"))
                    self.assertEqual(gameplay(combat(aa)),gameplay(combat(bb)))

    def test_native_tunneling_and_weapon_data_match_original(self):
        for name in ('vn_vietnam_unit_mov_vit','vn_weapon_outpost_handcannon_bambo_alarm_chi','vn_weapon_outpost_handcannon_bambo_chi','vn_upgrade_trap_range_vit','vn_upgrade_trap_roller_trigger'):
            with self.subTest(name=name):
                self.assertEqual(gameplay(original(name)),gameplay(current(name)))

    def test_scar_no_longer_owns_tunneling_or_trap_damage(self):
        mode = (ROOT/'assets/scar/winconditions/VietnamMode.scar').read_text()
        lifecycle = (ROOT/'assets/scar/vietnam/lifecycle.scar').read_text()
        self.assertNotIn('vietnam/tunneling.scar',mode)
        self.assertNotIn('VietnamTunneling_',lifecycle)
        trap = (ROOT/'assets/scar/vietnam/traps.scar').read_text()
        for removed in ('World_GetEntitiesNearPoint','Entity_SetHealth','Player_HasUpgrade','Entity_ForceConstruct','TRAP_ARMED'):
            self.assertNotIn(removed,trap)
        self.assertIn('VietnamTraps_Tick(now)',lifecycle)


class FourSecondTrapLifetimeTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua('function Entity_IsAttacking(e,duration) assert(duration==0.5);return e.attacked==true end')

    def make_trap(self, name='vn_building_defense_outpost_bambo_chi'):
        self.runlua(f"trap=building(201,'{name}',0);enemy=unit(202,0,22)")

    def observe(self, now):
        self.g.VietnamTraps_Update(self.g.PLAYERS[1],self.lua.table_from([self.g.trap]),now)
        self.g.VietnamTraps_Tick(now)

    def test_both_types_die_four_seconds_after_first_attack_without_scripted_damage(self):
        for name in ('vn_building_bambo_outpost_chi','vn_building_defense_outpost_bambo_chi'):
            with self.subTest(name=name):
                self.make_trap(name)
                self.g.trap.attacked = True
                self.observe(10)
                self.g.trap.attacked = False
                self.observe(13.99)
                self.assertIsNone(self.g.trap.dead)
                self.observe(14)
                self.assertTrue(self.g.trap.dead)
                self.assertIsNone(self.g.enemy.health)
                self.g.VietnamTraps_Cleanup()

    def test_idle_or_incomplete_trap_does_not_start_timer(self):
        self.make_trap()
        self.observe(0)
        self.observe(100)
        self.assertIsNone(self.g.trap.dead)
        self.g.trap.incomplete = True
        self.g.trap.attacked = True
        self.observe(101)
        self.g.VietnamTraps_Tick(110)
        self.assertIsNone(self.g.trap.dead)

    def test_repeated_attacks_do_not_restart_timer(self):
        self.make_trap()
        self.g.trap.attacked = True
        self.observe(0)
        self.observe(3)
        self.observe(4)
        self.assertTrue(self.g.trap.dead)

    def test_timer_survives_loss_from_owner_group_but_never_kills_replacement_blueprint(self):
        self.make_trap()
        self.g.trap.attacked = True
        self.observe(0)
        self.g.trap.owner = 22
        self.g.VietnamTraps_Tick(4)
        self.assertTrue(self.g.trap.dead)
        self.make_trap()
        self.g.trap.attacked = True
        self.observe(5)
        self.g.trap.bp = PREFIX+'vn_building_defense_keep_chi'
        self.g.VietnamTraps_Tick(9)
        self.assertIsNone(self.g.trap.dead)

    def test_destroyed_id_and_cleanup_cancel_safely(self):
        self.make_trap()
        self.g.trap.attacked = True
        self.observe(0)
        self.g.registry[201] = None
        self.g.VietnamTraps_Tick(4)
        self.assertEqual(len(list(self.g.VietnamTrapsState.pending.keys())),0)
        self.make_trap()
        self.g.trap.attacked = True
        self.observe(5)
        self.g.VietnamTraps_Cleanup()
        self.g.VietnamTraps_Tick(9)
        self.assertIsNone(self.g.trap.dead)

    def test_captured_trap_first_attack_also_gets_lifetime_from_real_lifecycle(self):
        self.make_trap()
        self.g.trap.owner = 22
        self.g.trap.attacked = True
        self.runlua('''
            function VietnamTowerTraining_BeginTick() end
            function VietnamTowerTraining_EndTick() end
            function VietnamTowerTraining_Update() end
            function VietnamRattanArmor_Update() end
            function VietnamDynasty_Update() end
            function VietnamLandmarks_Update() end
        ''')
        self.lua.execute((ROOT/'assets/scar/vietnam/lifecycle.scar').read_text())
        self.runlua("VietnamLifecycleState.active=true;VietnamLifecycleState.civilizations={[1]='vietnam',[2]='china'};now=0;VietnamLifecycle_Tick();now=4;VietnamLifecycle_Tick()")
        self.assertTrue(self.g.trap.dead)


if __name__ == '__main__':
    unittest.main()

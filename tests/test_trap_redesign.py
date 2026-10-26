from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools/python'))
from lupa import LuaRuntime

NAMES = ('vn_building_bambo_outpost_chi', 'vn_building_defense_outpost_bambo_chi')
ATTR = ROOT / 'assets/attrib/instances'

class TrapSourceTests(unittest.TestCase):
    def test_completed_forms_inherit_native_attached_weapon_without_r2_override(self):
        for name in NAMES:
            root = parse_current_xml(ATTR / 'ebps/vietnam' / (name + '_passable.xml')).getroot()
            for scope in [root, *root.findall('variant')]:
                combat = scope.find("list/template_reference[@value='ebpextensions\\combat_ext']")
                self.assertIsNone(combat, name)

    def test_private_relay_uses_native_weapon_ai_template_and_poison_weapon(self):
        path = ATTR / 'ebps/vietnam/vn_wpn_siege_outpost_handcannon_new_chi.xml'
        root = parse_current_xml(path).getroot()
        for scope in [root, *root.findall('variant')]:
            self.assertEqual(scope.find("instance_reference[@name='parent_pbg']").get('value'),
                             'ebps\\races\\core\\weapons\\wpn_ebps_template_ai')
            ref = scope.find("list/template_reference[@value='ebpextensions\\weapon_ext']/instance_reference[@name='weapon']")
            self.assertEqual(ref.get('value'), 'weapon\\vietnam\\vn_weapon_outpost_handcannon_bambo_chi')

    def test_build_cost_and_single_arrow_path_in_both_scopes(self):
        for name in NAMES:
            root = parse_current_xml(ATTR / 'ebps/vietnam' / (name + '.xml')).getroot()
            for scope in [root, *root.findall('variant')]:
                cost = scope.find("list/template_reference[@value='ebpextensions\\cost_ext']/group[@name='time_cost']")
                self.assertEqual(cost.find("enum_table/float[@name='wood']").get('value'), '0')
                self.assertEqual(cost.find("float[@name='time_seconds']").get('value'), '60')
                combat = scope.find("list/template_reference[@value='ebpextensions\\combat_ext']")
                hardpoints = combat.find("list[@name='hardpoints']")
                self.assertEqual(hardpoints.get('overrideParent'), 'True')
                self.assertEqual(len(hardpoints), 1)
                refs = [n.get('value') for n in hardpoints.iter('instance_reference')]
                self.assertIn('ebps\\vietnam\\emplacement_weapon_actors\\vn_wpn_siege_outpost_handcannon_new_chi', refs)
                self.assertFalse(any('alarrm' in ref or 'garrison' in ref for ref in refs))
                attachment = hardpoints.find("group/list/group/template_reference[@name='weapon_entity_attachment']")
                self.assertEqual(attachment.get('value'), 'options\\attachment_types\\entity_create_attachment')
                wrapper = hardpoints.find("group/list/group/template_reference[@name='non_entity_weapon_wrapper']")
                self.assertEqual(wrapper.get('value'), '')

    def test_working_outpost_baseline_has_approved_damage_range_burst_and_poison(self):
        root = parse_current_xml(ATTR / 'weapon/vietnam/vn_weapon_outpost_handcannon_bambo_chi.xml').getroot()
        for scope in [root, *root.findall('variant')]:
            self.assertEqual(scope.find("instance_reference[@name='parent_pbg']").get('value'),
                             'weapon\\races\\common\\ranged\\weapon_outpost_arrows')
            bag = scope.find('group')
            self.assertEqual({n.get('name') for n in bag}, {'range', 'burst', 'reload', 'damage'})
            for key in ('min', 'max'):
                self.assertEqual(bag.find(f"group[@name='reload']/group[@name='duration']/float[@name='{key}']").get('value'), '5')
            damage = bag.find("group[@name='damage']")
            self.assertEqual(len(damage), 3)
            self.assertEqual(damage.find("float[@name='min']").get('value'), '1')
            self.assertEqual(damage.find("float[@name='max']").get('value'), '1')
            self.assertEqual(damage.find('list/group/string').get('value'), 'malian_poison_arrows')
            duration = float(bag.find("group[@name='burst']/group[@name='duration']/float[@name='min']").get('value'))
            rate = float(bag.find("group[@name='burst']/group[@name='rate_of_fire']/float[@name='min']").get('value'))
            self.assertEqual(duration * rate, 12)
            self.assertEqual(bag.find("group[@name='range']/float[@name='max']").get('value'), '8')

class TrapSlowTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            now=0; applied={}; removed={}; registrations=0; print=function() end
            GE_DamageReceived=123; MAT_Entity=1; MUT_Multiplication=2
            function import() end
            function Entity_GetID(e) return e.id end
            function Entity_IsValid(id) return id ~= 999 end
            function Entity_IsAlive(e) return e.alive ~= false end
            function VietnamBlueprints_Matches(e,n) return e.name == n end
            function World_GetGameTime() return now end
            function Rule_AddGlobalEvent(f,event) registrations=registrations+1 end
            function Rule_RemoveGlobalEvent(f) registrations=registrations-1 end
            function Modifier_Create(kind,name,usage,exclusive,value,target)
                return {kind=kind,name=name,usage=usage,exclusive=exclusive,value=value}
            end
            function Modifier_ApplyToEntity(m,e,duration)
                local handle=#applied+1
                applied[handle]={modifier=m,target=e.id,duration=duration,time=now}
                return handle
            end
            function Modifier_Remove(handle) removed[handle]=true end
            attacker={id=1,name='vn_building_bambo_outpost_chi_passable'}
            victim={id=2,name='enemy'}
        ''')
        self.lua.execute((current_path(ROOT / 'assets/scar/vietnam/traps.scar')).read_text())

    def test_each_hit_gets_independent_nonexclusive_timed_modifier(self):
        self.lua.execute('''
            VietnamTraps_Start(); VietnamTraps_Start()
            VietnamTraps_OnDamageReceived({attacker=attacker,victim=victim})
            now=2
            VietnamTraps_OnDamageReceived({attacker=attacker,victim=victim})
        ''')
        self.assertEqual(self.lua.eval('registrations'), 1)
        self.assertEqual(self.lua.eval('#applied'), 2)
        for index in (1, 2):
            effect = self.lua.globals().applied[index]
            self.assertEqual(effect.duration, 0)  # Each handle is explicitly removed at its five-second deadline.
            self.assertEqual(effect.modifier.value, 0.8)
            self.assertFalse(effect.modifier.exclusive)
            self.assertEqual(effect.modifier.name, 'speed_maximum_modifier')
        self.assertEqual(self.lua.eval('applied[2].time-applied[1].time'), 2)

    def test_nontrap_repair_and_invalid_damage_are_ignored(self):
        self.lua.execute('''
            VietnamTraps_Start()
            VietnamTraps_OnDamageReceived({attacker={id=4,name='archer'},victim=victim})
            VietnamTraps_OnDamageReceived({victim=victim})
            VietnamTraps_OnDamageReceived({attacker=attacker,victim=victim,isRepairing=true})
            VietnamTraps_OnDamageReceived({attacker=attacker,victim={id=999}})
        ''')
        self.assertEqual(self.lua.eval('#applied'), 0)

    def test_private_trap_relay_damage_slows_but_shared_keep_relay_does_not(self):
        self.lua.execute('''
            VietnamTraps_Start()
            VietnamTraps_OnDamageReceived({attacker={id=8,name='vn_wpn_siege_outpost_handcannon_new_chi'},victim=victim})
            VietnamTraps_OnDamageReceived({attacker={id=9,name='wpn_range_keep_arrows_a'},victim=victim})
        ''')
        self.assertEqual(self.lua.eval('#applied'), 1)

    def test_cleanup_removes_our_live_handles_without_inverse_speed_change(self):
        self.lua.execute('''
            VietnamTraps_Start()
            VietnamTraps_OnDamageReceived({attacker=attacker,victim=victim})
            VietnamTraps_Cleanup()
        ''')
        self.assertTrue(self.lua.eval('removed[1]'))
        self.assertEqual(self.lua.eval('registrations'), 0)

    def test_expiry_tracking_survives_trap_death_and_drops_only_finished_handles(self):
        self.lua.execute('''
            VietnamTraps_Start()
            VietnamTraps_OnDamageReceived({attacker=attacker,victim=victim})
            now=2
            VietnamTraps_OnDamageReceived({attacker=attacker,victim=victim})
            attacker.alive=false
            now=5
            VietnamTraps_Tick(now)
        ''')
        self.assertEqual(self.lua.eval('#VietnamTrapsState.slows'), 1)
        self.assertEqual(self.lua.eval('VietnamTrapsState.slows[1].handle'), 2)
        self.assertEqual(self.lua.eval('VietnamTrapsState.slows[1].expires'), 7)
        self.assertTrue(self.lua.eval('removed[1] == true'))
        self.lua.execute('now=7;VietnamTraps_Tick(now)')
        self.assertEqual(self.lua.eval('#VietnamTrapsState.slows'),0)
        self.assertTrue(self.lua.eval('removed[2]'))
        self.lua.execute('VietnamTraps_Cleanup()')
        self.assertTrue(self.lua.eval('removed[2]'))

if __name__ == '__main__':
    unittest.main()

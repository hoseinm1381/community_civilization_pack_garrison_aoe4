"""Native refund ownership/source regression; no simulated engine-success claim."""
import json
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = 'assets/attrib/instances/abilities/vietnam/vn_vietnam_unit_mov_vit.xml'
EVIDENCE = ROOT / 'work/vietnam_redesign/runtime_v8_20261023/cooldown'
PAYLOAD = "group[@name='ability_bag']/group[@name='ability_active_state_tree_group']/state_tree_node[@name='ability_activate_deferred_tree']"
NATIVE = 'reveal_enemy_ayy'


class TunnelCooldownV8(unittest.TestCase):
    def test_native_trace_matches_current_installed_simulation(self):
        trace = json.loads((EVIDENCE / 'native-cooldown-trace.json').read_text())
        proof = json.loads((EVIDENCE / 'current-official-proof.json').read_text())
        self.assertEqual([r['sha256'] for r in proof if r.get('matches_trace')], [trace['source_sha256']])
        self.assertEqual(trace['validated_objects'], 410924)

    def test_schema_documents_deferred_refund_ownership(self):
        schema = ET.parse(EVIDENCE / 'refund-reflection-schema.xml').getroot()
        kind = schema.find("ReflectType[@Name='StateTree::StateTreeType']")
        self.assertEqual(kind.find("Fields/ReflectField[@Name='DeferredEntity']").get('EnumValue'), '7')
        deny = schema.find("ReflectType[@Name='StateTree::Track_TargetAbilityDenyRefund']")
        self.assertIn('DEFERRED ENTITY TREE AFTER', deny.find("Attributes/Attr[@Name='Description']").get('Value'))
        self.assertIn('Recharge refunding disabled', deny.find("Fields/ReflectField[@Name='m_applyToRecharge']/Attributes/Attr[@Name='Description']").get('Value'))
        template = ET.parse(EVIDENCE / 'EngineRef__abilities.xml').getroot()
        self.assertEqual(template.find(PAYLOAD).get('state_tree_type'), 'DeferredEntity')

    def test_tunnel_has_native_refund_commit_payload(self):
        self.assertEqual(ET.parse(ROOT / REL).find(PAYLOAD).get('value'), NATIVE)

    def test_actual_failed_v7_source_has_no_commit_payload(self):
        with zipfile.ZipFile(EVIDENCE.parent / 'before.zip') as archive:
            before = ET.fromstring(archive.read(REL))
        self.assertEqual(before.find(PAYLOAD).get('value'), '')
        self.assertFalse(any(n.get('value') for n in before.iter('state_tree_node')))

    def test_only_the_commit_payload_changes_from_actual_v7_source(self):
        with zipfile.ZipFile(EVIDENCE.parent / 'before.zip') as archive:
            before = ET.fromstring(archive.read(REL))
        current = ET.parse(ROOT / REL).getroot()
        current.find(PAYLOAD).set('value', '')
        self.assertEqual(ET.tostring(before), ET.tostring(current))

    def test_commit_tree_is_deferred_and_has_only_one_unconditional_refund_track(self):
        trace = json.loads((EVIDENCE / 'native-cooldown-trace.json').read_text())
        rows = [r for r in trace['objects'] if r['path'] == NATIVE or r['path'].startswith(NATIVE + '/')]
        self.assertEqual(len(rows), 6)
        self.assertCountEqual([r['type'] for r in rows], [
            'StateTree::StateNodeRoot', 'StateTree::StateNodePlayable',
            'StateTree::ConditionGroup', 'StateTree::ConditionGroup',
            'StateTree::TrackGroup', 'StateTree::Track_TargetAbilityDenyRefund'])
        root = next(r for r in rows if r['type'] == 'StateTree::StateNodeRoot')
        blink = next(r for r in trace['objects'] if r['type'] == 'StateTree::StateNodeRoot' and r['path'] == 'shinobi_blink_jpn')
        self.assertEqual(root['fields']['m_StateTreeType'], blink['fields']['m_StateTreeType'])
        for row in rows:
            fields = row['fields']
            if row['type'] == 'StateTree::ConditionGroup':
                self.assertEqual(fields['m_conditions']['count'], 0)
            if row['type'] == 'StateTree::TrackGroup':
                self.assertEqual(fields['m_tracks']['count'], 1)
            if row['type'] == 'StateTree::Track_TargetAbilityDenyRefund':
                self.assertTrue(fields['m_applyToRecharge'])
                self.assertTrue(fields['m_applyToCost'])
                self.assertEqual(fields['m_timeBegin'], 0)
                self.assertFalse(fields['m_master'])

    def test_generic_native_targeted_payload_manages_its_own_refund(self):
        rows = json.loads((EVIDENCE / 'native-cooldown-trace.json').read_text())['objects']
        track = next(r for r in rows if r['path'] == 'entity_ability_root/execute_ability_payload' and r['type'] == 'StateTree::EntityTrack_SpawnAndActivateAbility')
        self.assertTrue(track['fields']['m_manuallyManageRefund'])
        self.assertFalse(track['fields']['m_skipCost'])

    def test_30_seconds_player_wide_and_group_cast_are_preserved(self):
        bag = ET.parse(ROOT / REL).find("group[@name='ability_bag']")
        for name, value in {'recharge_time':'30', 'shared_timer':'', 'shared_timer_player_wide':'True',
                            'activation':'targeted', 'target':'tp_position', 'ui_group_cast_type':'multi'}.items():
            self.assertEqual(bag.find(f"*[@name='{name}']").get('value'), value)


if __name__ == '__main__':
    unittest.main()

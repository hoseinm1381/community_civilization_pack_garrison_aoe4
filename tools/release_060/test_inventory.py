"""Focused smoke checks for the read-only release 0.6.0 inventory."""
import unittest
from pathlib import Path

from inventory import DEFAULT_SOURCE, make_inventory


class InventorySmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = make_inventory(DEFAULT_SOURCE.resolve())

    def test_frozen_source_parses_and_has_provenance(self):
        self.assertEqual([], self.inventory['source']['parse_errors'])
        self.assertEqual(64, len(self.inventory['source']['instance_manifest_sha256']))
        self.assertTrue(self.inventory['army']['starting_units'])
        self.assertTrue(all(x['source_file'] and x['xpath'] for x in self.inventory['army']['starting_units']))

    def test_stock_abbey_reference_stays_unresolved(self):
        abbey = [x for x in self.inventory['candidate_building_spawn_refs']
                 if x['target'] == r'sbps\races\english\unit_abbey_king_2']
        self.assertTrue(abbey)
        confirmed = {x['id'] for x in self.inventory['units_and_entities']}
        self.assertNotIn(r'sbps\races\english\unit_abbey_king_2', confirmed)
        self.assertIn('ui_screen_name', abbey[0]['spawn_item_context'])
        self.assertNotIn(r'ebps\vietnam\vn_building_landmark_age3_new_imperial_garden',
                         self.inventory['reachable_building_actor_ids'])
        self.assertEqual('source_gate_requirements_preserved_but_not_evaluated',
                         abbey[0]['item_eligibility_evidence']['classification'])

    def test_starting_villager_build_and_production_chain_is_traced(self):
        self.assertTrue(self.inventory['army']['initialization_scar']['starting_tc_conversion'])
        self.assertTrue(self.inventory['army']['initialization_scar']['starting_villager_and_scout_conversion'])
        self.assertGreater(self.inventory['coverage']['reachable_buildable_actor_refs'], 0)
        self.assertGreater(self.inventory['coverage']['reachable_local_building_actor_ids'], 0)
        self.assertGreater(self.inventory['coverage']['reachable_actor_spawn_refs'], 0)
        self.assertTrue(self.inventory['landmark_unlock_evidence']['headquarters_gate'])
        self.assertIn(r'ebps\vietnam\vn_building_landmark_age2_headquarter_vit',
                      self.inventory['landmark_unlock_evidence']['buildable_landmark_actor_ids'])

    def test_rattan_upgrade_and_roster_match_plan(self):
        result = self.inventory['rattan_check']
        self.assertTrue(result['actual_upgrade_xml_present'])
        self.assertTrue(result['scar_uses_actual_upgrade'])
        self.assertFalse(result['scar_uses_lookalike_upgrade'])
        self.assertTrue(result['scar_roster_matches_plan'])
        self.assertTrue(result['elephant_excluded'])

    def test_local_unlinked_records_are_not_silently_dropped(self):
        self.assertTrue(self.inventory['unlinked_local_vietnam_squads'])
        self.assertTrue(self.inventory['unlinked_local_vietnam_unit_entities'])
        self.assertFalse(self.inventory['coverage']['complete_official_inheritance_closure'])


if __name__ == '__main__':
    unittest.main()

import unittest
from audit_production_routes import active_route


class ProductionRouteTests(unittest.TestCase):
    def test_associated_ebps_are_not_build_targets(self):
        root='default/squad_engineer_ext/construction_groups/construction_group/construction_items/construction_item/'
        self.assertTrue(active_route('sbps',root+'ebp','ebps'))
        self.assertFalse(active_route('sbps',root+'associated_ebps/ebp','ebps'))

    def test_only_default_instantiating_edges_are_followed(self):
        self.assertTrue(active_route('ebps','default/spawner_ext/spawn_items/spawn_item/squad','sbps'))
        self.assertFalse(active_route('ebps','campaign/spawner_ext/spawn_items/spawn_item/squad','sbps'))
        self.assertFalse(active_route('ebps','default/spawner_ext/requirements/required_squad','sbps'))

    def test_tier_squad_replacement_is_an_actual_upgrade_route(self):
        root='default/tier_ext/tier_group_list/tier_group/tier/'
        self.assertTrue(active_route('ebps',root+'statetree_tier_pgb_upgrade_target_squad','sbps'))
        self.assertFalse(active_route('ebps',root+'statetree_tier_requirements_pbg','sbps'))


if __name__=='__main__':unittest.main()

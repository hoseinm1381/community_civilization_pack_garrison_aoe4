import unittest
from references import reference_category, active_speaker_edge


class ReferenceTests(unittest.TestCase):
    def test_attachment_map_uses_native_full_category(self):
        self.assertEqual(reference_category('attachments\\attachment_lists'),'attachments')

    def test_builder_buildings_and_effective_parent_are_not_actor_attachments(self):
        self.assertFalse(active_speaker_edge('sbps','default/squad_engineer_ext/items/entity','ebps'))
        self.assertFalse(active_speaker_edge('ebps','default/parent_pbg','ebps'))
        self.assertTrue(active_speaker_edge('sbps','default/squad_loadout_ext/unit_list/type','ebps'))
        self.assertTrue(active_speaker_edge('ebps','default/tier_ext/tier/attachments','attachments'))


if __name__=='__main__':unittest.main()

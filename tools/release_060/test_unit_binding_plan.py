import unittest
from unit_binding_plan import select_slots, prepare_plan


class PrivateBodyPlanTests(unittest.TestCase):
    def slot(self,field='animator0',role='render_model_slot'):
        return {'field':field,'role':role,'before_value':r'art\body\model'}

    def test_animation_owner_is_never_selected(self):
        resources={'attrib/attachments/attachment_lists/a.rgd':{'slots':[
            self.slot('parent_animator','protected_native_animation_or_parent_owner'),
            self.slot()]}}
        member,slots=select_slots(resources,'art/body/model.rgm')
        self.assertEqual(len(slots),1)
        self.assertEqual(slots[0]['field'],'animator0')

    def test_duplicate_body_owners_fail_closed(self):
        resources={f'attrib/attachments/attachment_lists/{key}.rgd':{'slots':[self.slot()]}
                   for key in ('a','b')}
        with self.assertRaises(ValueError):select_slots(resources,'art/body/model')

    def test_entity_path_cannot_be_treated_as_body_attachment(self):
        with self.assertRaises(ValueError):
            select_slots({'attrib/ebps/shared.rgd':{'slots':[self.slot()]}},'art/body/model')

    def test_live_plan_covers_tiers_without_art_or_gameplay_edits(self):
        plan=prepare_plan()
        self.assertEqual({x['slug'] for x in plan['entries']},
                         {'archer2','archer3','archer4','crossbow3','crossbow4',
                          'handcannon4','spear1','spear2','spear3','spear4'})
        for row in plan['entries']:
            self.assertIsNone(row['private_model'])
            self.assertTrue(row['actor_consumers'])
            self.assertTrue(all(s['field']!='parent_animator' for s in row['stock_slots']))
            self.assertTrue(all(s['edit_policy']=='visual_override_reference_only'
                                for s in row['actor_consumers']))


if __name__=='__main__':unittest.main()

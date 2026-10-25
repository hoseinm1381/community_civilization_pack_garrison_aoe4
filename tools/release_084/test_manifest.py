import unittest
from manifest import recording_identity, supported_contexts


class ManifestTests(unittest.TestCase):
    def test_same_performance_can_alias_context_but_never_actor_age_take(self):
        row=dict(role='INFANTRY',age='A2',text='Tiến lên!',take='T1',direction='urgent',event='attack')
        self.assertEqual(recording_identity(row),recording_identity(dict(row,event='attack_move')))
        for field,value in [('age','A3'),('take','T2'),('role','GUNNER'),('direction','quiet'),('casting',dict(provider='other',model='m',voice='v'))]:
            self.assertNotEqual(recording_identity(row),recording_identity(dict(row,**{field:value})))

    def test_civilian_and_ship_events_have_capability_boundaries(self):
        self.assertNotIn('naval_attack',supported_contexts('NAVAL_FISH'))
        self.assertNotIn('wood',supported_contexts('INFANTRY'))
        self.assertIn('wood',supported_contexts('CIV_M'))
        self.assertNotIn('bow',supported_contexts('SKIRMISHER'))


if __name__=='__main__':unittest.main()

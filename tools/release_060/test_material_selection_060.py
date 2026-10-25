import unittest
from common import OUT, EXPORT
from pin_remaining_materials_060 import expand_lod_materials, pin_model


def material(name,ref):
    return {'name':name,'blocks':[{'textures':[{'name':'albedoTexture','logical_path':ref}]}]}


class MaterialSelectionTests(unittest.TestCase):
    def test_same_role_and_same_native_atlas_extend_across_lods(self):
        donor={'material':{'materials':[material('rider_lod1','rider'),material('rider_lod2','rider'),
            material('horse_lod1','horse'),material('horse_lod2','horse')]}}
        inputs={'rider_lod1':{'albedo':'r.png','slot':'albedoTexture'},
                'horse_lod1':{'albedo':'h.png','slot':'albedoTexture'}}
        result=expand_lod_materials(donor,inputs)
        self.assertEqual(result['rider_lod2'],inputs['rider_lod1'])
        self.assertEqual(result['horse_lod2'],inputs['horse_lod1'])

    def test_shared_image_never_crosses_roles_or_explicit_retained_material(self):
        donor={'material':{'materials':[material('rider_lod1','same'),material('rider_lod2','same'),
            material('goods_lod2','same')]}}
        inputs={'rider_lod1':{'albedo':'r.png','slot':'albedoTexture'}}
        result=expand_lod_materials(donor,inputs,{'rider_lod2'})
        self.assertEqual(result,inputs)

    def test_different_native_atlas_not_assumed_compatible(self):
        donor={'material':{'materials':[material('rider_lod1','first'),material('rider_lod2','second')]}}
        with self.assertRaisesRegex(ValueError,'atlas'):
            expand_lod_materials(donor,{'rider_lod1':{'albedo':'r.png','slot':'albedoTexture'}})

    def test_actual_corrected_structure_map_is_pinned_separately_from_old_authoring(self):
        receipt=OUT/'qualification/remaining_roster/nonhumanoid/siege_tower3/v1/authoring.json'
        if not receipt.exists():self.skipTest('Native fixture is unavailable')
        row={'key':'siege_tower3','source_receipt':str(receipt),
             'material_map':str(EXPORT/'remaining_roster/nonhumanoid/siege_tower3/v1/material-map-v3.json'),
             'material_map_receipt':str(receipt.parent/'material-map-v3-receipt.json'),
             'geometry_scope':'compatible stock remix; mechanisms retained'}
        result=pin_model(row)
        self.assertTrue(result['material_map_receipt_sha256'])
        self.assertEqual({v['slot'] for v in result['materials'].values()},{'albedoTex'})
        row.pop('material_map_receipt')
        with self.assertRaisesRegex(ValueError,'map changed'):pin_model(row)


if __name__=='__main__':unittest.main()

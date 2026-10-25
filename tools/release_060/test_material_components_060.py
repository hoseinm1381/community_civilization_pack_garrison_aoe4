"""Native codec fixture tests; not native-cook or appearance acceptance."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import OUT,read
from material_components_060 import compose,material_roots,rc,model_variants,validate_component_texture,merge_texture_payload


class MaterialComponentsTests(unittest.TestCase):
    def setUp(self):
        self.contract=read(OUT/'qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json')

    def material(self,kind):
        donor=read(self.contract['donors'][kind]['donor_manifest'])
        return Path(donor['material']['source']['path']).read_bytes()

    def test_mount_and_rider_components_keep_distinct_albedos(self):
        raw=self.material('horseman2');roots=material_roots(rc.parse(raw))
        rider=model_variants.rewrite_material(raw,{'albedoTexture':r'art\probe\rider.rrtex'}, {})
        horse=model_variants.rewrite_material(raw,{'albedoTexture':r'art\probe\horse.rrtex'}, {})
        result=compose(raw,{name:rider if name.startswith('rider') else horse for name in roots})
        actual=material_roots(rc.parse(result))
        for name in roots:
            expected=material_roots(rc.parse(rider if name.startswith('rider') else horse))[name]
            self.assertEqual(actual[name].payload,expected.payload)

    def test_other_texture_change_is_rejected(self):
        raw=self.material('horseman2');name=next(iter(material_roots(rc.parse(raw))))
        altered=model_variants.rewrite_material(raw,{'normalMap':r'art\probe\wrong.rrtex'}, {})
        with self.assertRaisesRegex(ValueError,'beyond native albedo'):
            compose(raw,{name:altered})

    def test_structure_albedo_slot_preserves_complete_native_components(self):
        raw=self.material('siege_mangonel3');roots=material_roots(rc.parse(raw))
        changed=model_variants.rewrite_material(raw,{'albedoTex':r'art\probe\timber.rrtex'}, {})
        self.assertNotEqual(raw,changed)
        result=compose(raw,{name:changed for name in roots},albedo_slot='albedoTex')
        self.assertEqual(result,changed)

    def test_component_must_reference_the_emitted_texture_member(self):
        raw=self.material('horseman2');name=next(iter(material_roots(rc.parse(raw))))
        changed=model_variants.rewrite_material(raw,{'albedoTexture':r'art\probe\rider.rrtex'}, {})
        validate_component_texture(changed,name,'art/probe/rider.rrtex','albedoTexture')
        with self.assertRaisesRegex(ValueError,'emitted texture'):
            validate_component_texture(changed,name,'art/probe/wrong.rrtex','albedoTexture')

    def test_duplicate_texture_members_cannot_hide_different_bytes(self):
        rows={};first={'member':'art/probe/texture.rrtex','sha256':'a'*64}
        merge_texture_payload(rows,first)
        merge_texture_payload(rows,dict(first))
        with self.assertRaisesRegex(ValueError,'Conflicting'):
            merge_texture_payload(rows,{**first,'sha256':'b'*64})


if __name__=='__main__':unittest.main()

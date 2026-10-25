import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import OUT
from ranged_media_pairs_060 import qualify_geometry_material_pair,variant_rgm_stock_except_path


class MediaPairingTests(unittest.TestCase):
    def test_exact_qualified_archer_pair_can_use_explicit_geometry_key(self):
        result=qualify_geometry_material_pair('archer2-v3',OUT/'qualification/albedo-variants/v60a2/material-verification.json')
        self.assertEqual(result['geometry_attempt_slug'],'archer2-v3')
        self.assertEqual(result['rig']['palette_bones'],46)
        self.assertEqual(result['native_lod_triangle_counts'],[1484,522,155])
        self.assertTrue(result['diagnostic_geometry_cook_rgo_rrmaterial_actor_rhka_excluded'])

    def test_unrelated_stock_donor_material_cannot_pair_with_geometry(self):
        with self.assertRaisesRegex(RuntimeError,'geometry/material qualification incomplete'):
            qualify_geometry_material_pair('archer2-v3',OUT/'qualification/albedo-variants/v60spm/material-verification.json')

    def test_native_model_path_lengths_may_change_multiple_header_bytes(self):
        from common import read
        spec=read(OUT/'authored-geometry/crossbow3-v5b/spec.json')
        result=variant_rgm_stock_except_path(read(spec['stock_manifest']),
            read(OUT/'qualification/albedo-variants/v60mr3/material-verification.json'))
        self.assertTrue(result['supported_native_path_rewrite_exact'])


if __name__=='__main__':unittest.main()

import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import OUT,read
from verify_unit_albedo_variant import select_variant_resources


class VariantBatchTests(unittest.TestCase):
    def setUp(self):
        report=read(OUT/'qualification/albedo-variants/v60ms1/material-verification.json')
        self.rows=[{'path':v['member']} for v in report['extracted'].values()]
        self.prefix='art/scenario/garrison/v60ms1/body/'

    def test_batch_readback_selects_only_one_explicit_private_variant(self):
        rows=self.rows+[{'path':r['path'].replace('/v60ms1/','/unrelated/')} for r in self.rows]
        chosen=select_variant_resources(rows,self.prefix)
        self.assertEqual(set(chosen),{r['path'] for r in self.rows})

    def test_single_variant_default_rejects_unexpected_extra_art(self):
        with self.assertRaisesRegex(RuntimeError,'resource set'):
            select_variant_resources(self.rows+[{'path':'art/unrelated/other.rgm'}])

    def test_prefix_cannot_escape_or_select_partial_directory(self):
        for prefix in ('art/scenario/../','art/scenario/garrison/v60ms1/bod','attrib/'):
            with self.assertRaises(ValueError):select_variant_resources(self.rows,prefix)


if __name__=='__main__':unittest.main()

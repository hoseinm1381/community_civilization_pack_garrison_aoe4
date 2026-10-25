"""Regression fixtures are the actual official and failed 0.7.6 cooked models."""
import unittest
from common import *
from rig_contract import read_contract, rig_text, validate_contract

class RigContractTests(unittest.TestCase):
    def test_official_contracts(self):
        donors=read(ROOT/'output/release_076/donors.json')
        for family in ('buffalo','skirmisher2'):
            d=read(donors[family]['manifest']);c=read_contract(Path(d['skeleton']['source']).read_bytes())
            validate_contract(c,c)
            expected=['default'] if family=='buffalo' else ['lowerbody','upperbody']
            self.assertEqual([p['name'] for p in c['groups']],expected)
            self.assertIn('[PARTITION START]',rig_text(c))
    def test_actual_failed_076_models_rejected(self):
        donors=read(ROOT/'output/release_076/donors.json')
        for family in ('buffalo','skirmisher2'):
            d=read(donors[family]['manifest']);official=read_contract(Path(d['skeleton']['source']).read_bytes())
            raw=(BASE/'readback/art/scenario/garrison/cc076'/family/'model.rgm').read_bytes()
            with self.assertRaisesRegex(ValueError,'partition|LOD'):
                validate_contract(read_contract(raw),official)
    def test_reject_changed_bone_order(self):
        d=read(read(ROOT/'output/release_076/donors.json')['buffalo']['manifest'])
        c=read_contract(Path(d['skeleton']['source']).read_bytes());bad=json.loads(json.dumps(c))
        bad['bones'][1]['name']='wrong'
        with self.assertRaisesRegex(ValueError,'bone'):validate_contract(bad,c)
    def test_lod_folding_uses_native_ancestor_and_preserves_weight(self):
        from rig_contract import fold_weights
        d=read(read(ROOT/'output/release_076/donors.json')['skirmisher2']['manifest'])
        c=read_contract(Path(d['skeleton']['source']).read_bytes())
        weights={'metarig_larmindex3':0.6,'metarig_larmmiddle3':0.4}
        out=fold_weights(weights,c,3)
        self.assertAlmostEqual(sum(out.values()),1)
        allowed={b['name'] for b in c['bones'][:26]}
        self.assertTrue(set(out)<=allowed)
        self.assertNotIn('metarig_larmindex3',out)

if __name__=='__main__':unittest.main()

import unittest,json,hashlib,zipfile
from pathlib import Path
from freeze import ROOT,NORMAL,OUT,GUID,OLD
class PortContracts(unittest.TestCase):
    def test_live_gameplay_scripts_are_normal_v12(self):
        for p in (NORMAL/'assets/scar').rglob('*.scar'):
            if p.name in ('prematch_precache.scar','tunnel_ability_squads.scar'):continue
            expected=p.read_text(encoding='utf-8-sig').replace(OLD,GUID).replace('20261023-runtime-v12','20261023-runtime-v12-garrison-072')
            self.assertEqual((ROOT/p.relative_to(NORMAL)).read_text(encoding='utf-8-sig'),expected,str(p))
    def test_new_buffalo_and_no_legacy_army(self):
        files=list((ROOT/'assets/attrib/instances').rglob('*.xml'))
        self.assertEqual(len([p for p in files if p.stem=='vn_unit_water_buffalo_vit']),2)
        self.assertFalse(any(p.stem=='vn_normal_chinese' for p in files))
    def test_parity_and_visual_binding_receipts(self):
        p=OUT/'source-port.json';self.assertTrue(p.exists(),'Port must supply per-field visual and gameplay proof')
        d=json.loads(p.read_text());self.assertEqual(d['normal_instances'],246)
        self.assertTrue(d['visual_edits']);self.assertEqual(d['unresolved'],[])
    def test_normal_snapshot_unchanged(self):
        hashes=json.loads((OUT/'freeze/normal.json').read_text())
        for name,expected in hashes.items():self.assertEqual(hashlib.sha256((NORMAL/name).read_bytes()).hexdigest(),expected,name)
if __name__=='__main__':unittest.main(verbosity=2)

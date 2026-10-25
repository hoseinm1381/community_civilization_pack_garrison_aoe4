"""Independent semantic parity: discard only visual fields, undo art aliases."""
from port import *
import unittest
VISUAL={'attachments','animator_attachments','animator_scale','entity_scale'}
def canonical(root,reverse):
    root=copy.deepcopy(root)
    def rec(x):
        x.text=None;x.tail=None
        for c in list(x):
            if c.get('name')in VISUAL:x.remove(c);continue
            if c.tag=='instance_reference'and c.get('value')in reverse:
                c.set('value',reverse[c.get('value')]);c.attrib.pop('mod',None)
            had_children=bool(len(c));rec(c)
            if len(c)==0 and (had_children or c.get('value')is None) and c.tag not in ('uniqueid',):x.remove(c)
    rec(root)
    return E.tostring(root,encoding='unicode')
class SemanticParity(unittest.TestCase):
    def test_all_normal_gameplay_fields_preserved(self):
        receipt=json.loads((OUT/'source-port.json').read_text());reverse={v:k for k,v in receipt['redirects'].items()}
        with zipfile.ZipFile(OUT/'freeze/normal.zip')as z:
            for name in z.namelist():
                if not name.startswith('assets/attrib/instances/'):continue
                a=E.fromstring(translated(z.read(name),name));b=E.parse(STAGE/renamed(name)).getroot()
                self.assertEqual(canonical(a,{}),canonical(b,reverse),name)
    def test_identity_translation_and_only_data_list_adaptations(self):
        adaptations={'assets/scar/vietnam/prematch_precache.scar','assets/scar/vietnam/tunnel_ability_squads.scar'}
        with zipfile.ZipFile(OUT/'freeze/normal.zip')as z:
            for name in z.namelist():
                if not name.startswith('assets/')or name.startswith('assets/attrib/instances/')or name in adaptations:continue
                self.assertEqual((STAGE/renamed(name)).read_bytes(),translated(z.read(name),name),name)
        data=(STAGE/'assets/scar/vietnam/tunnel_ability_squads.scar').read_text()
        with zipfile.ZipFile(OUT/'freeze/normal.zip')as z:base=translated(z.read('assets/scar/vietnam/tunnel_ability_squads.scar'),'x.scar').decode()
        prefix=data.split('-- Equivalent private visual identities')[0].rstrip()
        self.assertEqual(prefix,base.replace('\r\n','\n').rstrip().removesuffix('}').rstrip())
    def test_no_private_visual_reference_missing_source_or_native_definition(self):
        native=Path(CFG['external_root'])/'staging/r72/baseline-native/attrib/attachments'
        names={p.stem for p in native.rglob('*.rgd')}
        for p in (STAGE/'assets/attrib/instances').rglob('*.xml'):
            for x in E.parse(p).iter('instance_reference'):
                if x.get('mod')==GUID and x.get('name')in ('attachments','animator_attachments'):
                    self.assertIn(x.get('value').rsplit('\\',1)[-1],names,str(p))
    def test_native_no_than_accuracy_all_variants(self):
        for p in (STAGE/'assets/attrib/instances/weapon').rglob('vn_weapon_no_than_vit.xml'):
            t=E.parse(p).getroot()
            for scope in [t,*t.findall('variant')]:
                self.assertEqual(scope.find("group[@name='weapon_bag']/group[@name='scatter']/float[@name='angle_scatter']").get('value'),'3')
if __name__=='__main__':unittest.main(verbosity=2)

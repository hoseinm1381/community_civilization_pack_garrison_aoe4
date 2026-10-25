"""Media bytes are insufficient: production/loadout links must activate them."""
from native import *
import unittest
class ActivationGraph(unittest.TestCase):
    def test_all_retained_private_identity_edges_activate_custom_actors(self):
        label=sys.argv[1]if len(sys.argv)>1 and not sys.argv[1].startswith('-')else'v4'
        back=STAGING/('assemble-'+label)/'readback'
        aliases={v.rsplit('\\',1)[-1]:k.rsplit('\\',1)[-1]for k,v in json.loads((OUT/'source-port.json').read_text())['redirects'].items()}
        count=0
        for kind in ('ebps','sbps'):
            current={p.stem:p for p in (back/('attrib/'+kind)).rglob('*.rgd')}
            fresh={p.stem:p for p in (back.parent/'fresh'/('attrib/'+kind)).rglob('*.rgd')}
            for old in (BASE/('attrib/'+kind)).rglob('*.rgd'):
                if old.stem not in current:continue
                before=rgd.read(old.read_bytes());after=rgd.read(current[old.stem].read_bytes())
                source=rgd.read(fresh[old.stem].read_bytes())
                for path,node in rgd.flatten(before.nodes):
                    if node.key!='$PBGNAME'or not str(node.value).startswith(GUID+':'):continue
                    if node.value.split(':',1)[1]not in aliases:continue
                    initial=rgd.find(source.nodes,path)
                    if initial is None:continue
                    # The new normal roster wins where production changed.
                    expected_donor=aliases[node.value.split(':',1)[1]]
                    if initial.value not in (expected_donor,node.value):
                        self.assertNotIn(old.stem,aliases,(old.stem,path,'unexpected retained-donor drift'));continue
                    target=rgd.find(after.nodes,path)
                    self.assertIsNotNone(target,(old.stem,path))
                    self.assertEqual(target.value,node.value,(old.stem,path))
                    count+=1
        self.assertGreaterEqual(count,39)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ActivationGraph));sys.exit(not result.wasSuccessful())

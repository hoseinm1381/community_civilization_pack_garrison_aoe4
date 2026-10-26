"""Catch actual extension overrides that the native compiler silently dropped."""
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_extension_inheritance import Resolver,load_local,summarize
REL='assets/attrib/instances/ebps/vietnam/buildings/economy/rice_paddies/vn_building_resource_farm2_chi.xml'
KEY=REL.removeprefix('assets/attrib/instances/').removesuffix('.xml').replace('/','\\')
OUT=ROOT/'work/vietnam_redesign/runtime_v8_20261023'

class ExplicitMergeV8(unittest.TestCase):
    def setUp(self):
        self.official=json.loads((OUT/'buffalo/official-extensions.json').read_text())['records']

    def test_actual_native_dropped_overrides_are_rejected(self):
        local=load_local()
        with zipfile.ZipFile(OUT/'before.zip') as z:local[KEY]=summarize(z.read(REL))
        errors=Resolver(local,self.official).audit()
        dropped=[e for e in errors if e.get('error')=='unmatched-extension-override']
        self.assertEqual(len(dropped),50)
        self.assertEqual({e['variant'] for e in dropped},{'default','campaign'})
        self.assertTrue(all(e['blueprint']==KEY for e in dropped))

    def test_corrected_native_ids_and_explicit_append_pass(self):
        self.assertEqual(Resolver(load_local(),self.official).audit(),[])

    def test_no_parent_match_cannot_be_hidden_by_duplicate_checker(self):
        local=load_local()
        item=next(i for i in local[KEY]['default']['items'] if i['value']==r'ebpextensions\construction_ext')
        item['List.ItemID']='-99999999';item['List.ParentItemID']='-99999999'
        errors=Resolver(local,self.official).audit()
        self.assertTrue(any(e.get('error')=='unmatched-extension-override' and e['extension']==item['value'] for e in errors))


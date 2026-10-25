import hashlib
from pathlib import Path
import tempfile
import unittest

from assemble_payload_archive_060 import validate_payload_rows


class PayloadArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'payload';self.path.write_bytes(b'new')
        self.digest=hashlib.sha256(b'new').hexdigest()
        self.member='attrib/ebps/vietnam/vn_unit_archer_2_vit.rgd'
        self.before={self.member:{'sha256':'a'*64,'bytes':4}}
        self.row={'member':self.member,'path':str(self.path),'sha256':self.digest,
                  'bytes':3,'before_sha256':'a'*64}

    def test_expected_baseline_and_payload_hash_produce_exact_allowlist(self):
        result=validate_payload_rows([self.row],self.before,set())
        self.assertEqual(result,[{'member':self.member,'before_sha256':'a'*64,'after_sha256':self.digest}])

    def test_stale_payload_wrong_baseline_and_protected_resource_refused(self):
        for changes,protected in [({'sha256':'b'*64},set()),({'before_sha256':'c'*64},set()),({}, {self.member})]:
            with self.subTest(changes=changes,protected=protected):
                with self.assertRaises(ValueError):validate_payload_rows([{**self.row,**changes}],self.before,protected)

    def test_native_private_namespace_addition_valid_but_stock_override_refused(self):
        row={**self.row,'member':'attrib/ebps/vietnam/release_060/new.rgd','before_sha256':None}
        self.assertIsNone(validate_payload_rows([row],{},set())[0]['before_sha256'])
        row['member']='attrib/ebps/races/chinese/units/unit_monk_3_chi.rgd'
        with self.assertRaises(ValueError):validate_payload_rows([row],{},set())

    def test_duplicate_payload_and_undeclared_baseline_refused(self):
        with self.assertRaises(ValueError):validate_payload_rows([self.row,self.row],self.before,set())
        row=dict(self.row);row.pop('before_sha256')
        with self.assertRaises(ValueError):validate_payload_rows([row],self.before,set())


if __name__=='__main__':unittest.main()

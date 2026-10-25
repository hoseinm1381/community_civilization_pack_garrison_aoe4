"""Fail closed on conflicting overlays, unexpected mounts or stale payloads."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from package_policy import merge_payloads, verify_inventory, verify_static_source

class PackagePolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/'x';self.p.write_bytes(b'new')
        self.h=hashlib.sha256(b'new').hexdigest()
    def row(self,member='art/test.rgm',toc='data'):
        return dict(member=member,file=str(self.p),sha256=self.h,toc=toc)
    def test_duplicate_payload_rejected(self):
        with self.assertRaises(ValueError):merge_payloads([[self.row()],[self.row()]])
    def test_static_receipt_must_match_current_source(self):
        verify_static_source({'source_policy_sha256':'current'},'current')
        with self.assertRaises(ValueError):verify_static_source({'source_policy_sha256':'old'},'current')
        with self.assertRaises(ValueError):verify_static_source({},'current')
    def test_stale_payload_rejected(self):
        self.p.write_bytes(b'stale')
        with self.assertRaises(ValueError):merge_payloads([[self.row()]])
    def test_tuning_under_data_rejected(self):
        with self.assertRaises(ValueError):merge_payloads([[self.row('attrib/ebps/x.rgd')]])
    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):merge_payloads([[self.row('../art/x')]])
    def test_untouched_member_and_mount_must_match(self):
        payload=merge_payloads([[self.row()]])
        before={'keep':'old','art/test.rgm':'prior'};mounts={'keep':'data','art/test.rgm':'data'}
        actual={'keep':'old','art/test.rgm':self.h}
        verify_inventory(before,mounts,actual,mounts,payload)
        with self.assertRaises(ValueError):verify_inventory(before,mounts,{**actual,'keep':'wrong'},mounts,payload)
        with self.assertRaises(ValueError):verify_inventory(before,mounts,actual,{**mounts,'keep':'attrib'},payload)
    def test_addition_requires_exact_allowlist(self):
        payload=merge_payloads([[self.row()]])
        verify_inventory({'keep':'old'},{'keep':'data'},{'keep':'old','art/test.rgm':self.h},{'keep':'data','art/test.rgm':'data'},payload)
        with self.assertRaises(ValueError):verify_inventory({'keep':'old'},{'keep':'data'},{'keep':'old','art/test.rgm':self.h,'extra':'x'},{'keep':'data','art/test.rgm':'data','extra':'data'},payload)

if __name__=='__main__':unittest.main()

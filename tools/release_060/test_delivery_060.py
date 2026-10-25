import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from common import CFG
from pin_final053 import SGA_SHA
from inspect_delivery_060 import inspect_delivery


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/(CFG['package_key']+'-0.6.0.zip')
        self.addCleanup(self.temp.cleanup)
        self.sga = b'test-native-archive-inspection-is-a-separate-gate'
        self.digest = hashlib.sha256(self.sga).hexdigest()
        self.manifest = {'schema':'garrison.mod/v1','bundle_key':CFG['package_key'],
            'members':[{'mod_key':CFG['package_key'],'role':'tuning',
                'path':CFG['package_key']+'.sga','sha256':self.digest}],
            'details':{'id':CFG['package_key'],'version':'0.6.0',
                'author':'hosein81 and chilly5','content_types':['game-mode','tuning-pack']}}
        self.evidence = {'schema':'ccp.release060.evidence/v1','version':'0.6.0',
            'is_final_release':True,'sga_sha256':self.digest,'baseline_sga_sha256':SGA_SHA,
            'credits':'hosein81 and chilly5','gates':{
                'export_cook_readback':True,'archive_preservation':True,'static_model_binding_coverage':True,
                'import':False,'native_appearance':False,'native_gameplay':False,'multiplayer':False}}

    def save(self, extra=None):
        with zipfile.ZipFile(self.path,'w') as z:
            z.writestr('garrison.json',json.dumps(self.manifest))
            z.writestr(CFG['package_key']+'.sga',self.sga)
            z.writestr('START-HERE.txt','Credits: hosein81 and chilly5\nRollback: final 0.5.3\n')
            z.writestr('EVIDENCE.json',json.dumps(self.evidence))
            if extra:z.writestr(*extra)

    def test_exact_four_members_and_hashes_pass_only_package_gate(self):
        self.save()
        result=inspect_delivery(self.path)
        self.assertEqual(result['sga_sha256'],self.digest)
        self.assertFalse(result['native_acceptance'])

    def test_strict_version_and_exact_credit(self):
        for field,value in [('version','0.6.0.1'),('author','hosein81')]:
            with self.subTest(field=field):
                original=copy.deepcopy(self.manifest)
                self.manifest['details'][field]=value;self.save()
                with self.assertRaises(ValueError):inspect_delivery(self.path)
                self.manifest=original

    def test_evidence_cannot_claim_different_archive_or_baseline(self):
        for field in ('sga_sha256','baseline_sga_sha256'):
            with self.subTest(field=field):
                original=self.evidence[field];self.evidence[field]='0'*64;self.save()
                with self.assertRaises(ValueError):inspect_delivery(self.path)
                self.evidence[field]=original

    def test_extra_member_and_case_collision_refused(self):
        for extra in [('other.sga',b'foreign'),('GARRISON.JSON',b'{}')]:
            with self.subTest(extra=extra[0]):
                self.save(extra)
                with self.assertRaises(ValueError):inspect_delivery(self.path)

    def test_unrun_native_gates_remain_explicit(self):
        self.evidence['gates']['multiplayer']=True;self.save()
        with self.assertRaises(ValueError):inspect_delivery(self.path)

    def test_broad_roster_label_does_not_substitute_for_scoped_static_gate(self):
        self.evidence['gates'].pop('static_model_binding_coverage')
        self.evidence['gates']['roster_coverage']=True;self.save()
        with self.assertRaises(ValueError):inspect_delivery(self.path)


if __name__=='__main__':unittest.main()

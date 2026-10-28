import copy,tempfile,unittest,zipfile
from pathlib import Path
from complete_package import check_policy
from current_package import write_package

class CompletePackageTests(unittest.TestCase):
    def fixture(self):
        prior={'member_sha256':{'keep':'a','replace':'b','remove':'c'}}
        expected={'member_sha256':{'keep':'a','replace':'d','new':'e'},'mounts':{'keep':'data','replace':'data','new':'data'}}
        policy={'assembly_mode':'complete-members','deleted_members_vs090':['remove'],'payloads':[{'member':k,'sha256':h,'mount':'data'} for k,h in [('replace','d'),('new','e')]]}
        return policy,expected,prior
    def test_exact_changed_and_omitted_closure(self):
        p,e,b=self.fixture();self.assertEqual(set(check_policy(p,e,b)),{'replace','new'})
    def test_omissions_and_changed_payloads_cannot_escape_policy(self):
        for mutation in ('omit_delete','extra_delete','missing_payload','extra_payload','wrong_hash','wrong_mount','duplicate'):
            p,e,b=self.fixture()
            if mutation=='omit_delete':p['deleted_members_vs090']=[]
            elif mutation=='extra_delete':p['deleted_members_vs090'].append('keep')
            elif mutation=='missing_payload':p['payloads'].pop()
            elif mutation=='extra_payload':p['payloads'].append({'member':'unapproved','sha256':'x','mount':'data'})
            elif mutation=='wrong_hash':p['payloads'][0]['sha256']='x'
            elif mutation=='wrong_mount':p['payloads'][0]['mount']='attrib'
            else:p['payloads'].append(copy.deepcopy(p['payloads'][0]))
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):check_policy(p,e,b)
    def test_zip_level_nine_recreates_original_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);data=b'accepted current data'*10000;original=root/'original.zip'
            info=zipfile.ZipInfo('community_civilization_pack.sga',(2026,10,28,16,14,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0x20
            with zipfile.ZipFile(original,'x') as z:z.writestr(info,data,compresslevel=9)
            fields=('filename','date_time','compress_type','create_system','create_version','extract_version','external_attr','internal_attr')
            with zipfile.ZipFile(original) as z:row={k:getattr(z.infolist()[0],k) for k in fields}
            source=root/'data';source.write_bytes(data);target=root/'rebuilt.zip';write_package(target,[row],{'community_civilization_pack.sga':source},9)
            self.assertEqual(target.read_bytes(),original.read_bytes())

if __name__=='__main__':unittest.main()

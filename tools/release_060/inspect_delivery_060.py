"""Verify strict final 060 ZIP metadata and bytes; never infer native acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from common import CFG, sha
from pin_final053 import SGA_SHA

CREDITS='hosein81 and chilly5'
EXPECTED_GATES={'export_cook_readback':True,'archive_preservation':True,'static_model_binding_coverage':True,
                'import':False,'native_appearance':False,'native_gameplay':False,'multiplayer':False}


def inspect_delivery(path):
    path=Path(path);key=CFG['package_key'];sga=key+'.sga'
    if path.name!=key+'-0.6.0.zip':raise ValueError('Expected exact final 0.6.0 ZIP filename')
    before=sha(path)
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if (len(names)!=4 or len({n.casefold() for n in names})!=4
                or set(names)!={'garrison.json',sga,'START-HERE.txt','EVIDENCE.json'}):
            raise ValueError('Expected four exact final delivery members')
        if z.testzip() is not None:raise ValueError('ZIP failed full CRC/readability check')
        manifest=json.loads(z.read('garrison.json'));details=manifest.get('details',{})
        if (manifest.get('schema')!='garrison.mod/v1' or manifest.get('bundle_key')!=key
                or details.get('id')!=key or details.get('version')!='0.6.0'
                or details.get('author')!=CREDITS
                or details.get('content_types')!=['game-mode','tuning-pack']):
            raise ValueError('Strict version, identity, content types or credits differ')
        with z.open(sga) as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if manifest.get('members')!=[{'mod_key':key,'role':'tuning','path':sga,'sha256':digest}]:
            raise ValueError('Expected one owning tuning SGA with exact embedded SHA256')
        evidence=json.loads(z.read('EVIDENCE.json'))
        if (evidence.get('schema')!='ccp.release060.evidence/v1' or evidence.get('version')!='0.6.0'
                or evidence.get('is_final_release') is not True or evidence.get('sga_sha256')!=digest
                or evidence.get('baseline_sga_sha256')!=SGA_SHA or evidence.get('credits')!=CREDITS):
            raise ValueError('Evidence must identify this final archive and exact final 053 baseline')
        gates=evidence.get('gates',{})
        if any(gates.get(k) is not v for k,v in EXPECTED_GATES.items()):
            raise ValueError('Keep verified release gates separate from unrun native acceptance gates')
        instructions=z.read('START-HERE.txt').decode('utf-8')
        if CREDITS not in instructions or '0.5.3' not in instructions or 'rollback' not in instructions.lower():
            raise ValueError('Missing exact credits or final 053 rollback instructions')
    if sha(path)!=before:raise ValueError('Delivery ZIP changed while verifying')
    return {'schema':'ccp-060-package-verification/v1','status':'zip_metadata_members_crc_and_embedded_sga_hash_verified',
            'zip':str(path.resolve()),'zip_sha256':before,'sga_sha256':digest,'version':'0.6.0',
            'credits':CREDITS,'members':names,'gates':gates,'native_acceptance':False,
            'qualification_limit':'Requires separately verified archive, bindings and roster reports; ZIP checks do not prove them'}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('zip',type=Path)
    print(json.dumps(inspect_delivery(ap.parse_args().zip),indent=2))

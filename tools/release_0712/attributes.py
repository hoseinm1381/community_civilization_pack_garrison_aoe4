"""Overlay only native-compiled approved scalars onto accepted actor documents."""
import copy,math
from common import *
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd

def flat(doc):return dict(rgd.flatten(doc.nodes))

def assemble(native_label):
    receipt=read(OUT/f'native/{native_label}/receipt.json');back=Path(receipt['readback'])
    assert receipt['status']=='native_compile_passed' and sha(receipt['archive'])==receipt['sha256']
    updates={}
    for row in read(OUT/'range-inventory.json')['rows']:
        updates.setdefault(row['member'],{})[row['native_path']]=(row['before'],row['after'])
    for age in (2,3,4):
        member=f'attrib/weapon/vietnam/vn_weapon_skirmisher_{age}_vit.rgd'
        old=rgd.read((BASE/'readback'/member).read_bytes())
        fields={}
        for p,n in rgd.flatten(old.nodes):
            if p.endswith('/weapon_bag/fire/wind_up'):
                assert n.value==0.25;fields[p]=(n.value,n.value+0.25)
            elif '/weapon_bag/reload/duration/' in p and n.key in ('min','max'):
                assert n.value==1.375;fields[p]=(n.value,n.value-0.25)
        assert len(fields)>=3;updates[member]=fields
    payload=[];proof=[]
    for member,fields in sorted(updates.items()):
        old=rgd.read((BASE/'readback'/member).read_bytes());new=rgd.read((back/member).read_bytes())
        oldflat,newflat=flat(old),flat(new);result=copy.deepcopy(old);changes=[]
        for path,(before,after) in sorted(fields.items()):
            assert oldflat[path].value==before,(member,path,oldflat[path].value,before)
            assert math.isclose(newflat[path].value,after,abs_tol=1e-6),(member,path,newflat[path].value,after)
            assert oldflat[path].kind==newflat[path].kind
            rgd.find(result.nodes,path).value=newflat[path].value
            changes.append({'path':path,'before':before,'after':newflat[path].value})
        reverted=copy.deepcopy(result)
        for path,(before,_) in fields.items():rgd.find(reverted.nodes,path).value=before
        assert rgd.write(reverted)==rgd.write(old),'Unrelated actor metadata changed'
        p=OUT/'attrib-payload'/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(rgd.write(result))
        payload.append({'member':member,'file':str(p),'sha256':sha(p),'toc':'attrib'})
        proof.append({'member':member,'changes':changes,'native_sha256':sha(back/member),
            'baseline_sha256':sha(BASE/'readback'/member),'full_reversal_exact':True,'baseline_keys_preserved':True})
    write(OUT/'attribute-proof.json',{'native_label':native_label,'members':proof,'method':'Only exact native-compiled authorized float values copied into accepted baseline documents; compiled-only overlays retained.'})
    return payload

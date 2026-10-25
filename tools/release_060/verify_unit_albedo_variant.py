"""Read back albedo-only variants; use Python 3.13 for installed Garrison reader.

Compare every material chunk and parameter, allowing only the albedoTexture
reference to change. No binary material editing or shader substitutions.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
from common import ARCH, CFG, OUT, guard, owned, read, sha, write


def select_variant_resources(members,private_prefix=None):
    if private_prefix is not None and (not private_prefix.startswith('art/scenario/garrison/')
            or not private_prefix.endswith('/') or '..' in private_prefix.split('/')
            or '\\' in private_prefix or ':' in private_prefix):
        raise ValueError('Expected exact private variant directory prefix')
    selected=[m for m in members if m['path'].startswith(private_prefix or 'art/')]
    if len({m['path'].casefold() for m in selected})!=len(selected):
        raise RuntimeError('Duplicate private variant resource set')
    art={m['path']:m for m in selected}
    if len(art)!=5 or sorted(Path(s).suffix for s in art)!=['.rgm','.rgo','.rrgeom','.rrmaterial','.rrtex']:
        raise RuntimeError('Unexpected private variant resource set')
    return art


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--cook',type=Path,required=True)
    p.add_argument('--donor',type=Path,required=True)
    p.add_argument('--private-prefix',help='Exact private variant directory in a shared multi-variant cook')
    args=p.parse_args()
    guard()
    cook=read(owned(args.cook)); donor=read(owned(args.donor))
    albedo_slot=cook.get('only_overridden_slot','albedoTexture')
    if albedo_slot not in ('albedoTexture','albedoTex'):raise ValueError('Unsupported native albedo slot')
    if cook['status']!='cooked_archive_verified_material_readback_pending':
        raise ValueError('Fresh successful variant cook required')
    archive=owned(Path(cook['archive']))
    if sha(archive)!=cook['archive_sha256']:
        raise RuntimeError('Archive changed')
    dest=owned(args.cook.parent/'readback')
    dest.mkdir(exist_ok=True)
    report=owned(args.cook.parent/'material-verification.json')
    if report.exists():
        raise FileExistsError(report)
    listing=json.loads(subprocess.check_output([str(ARCH),'list','--verify',str(archive)],text=True))
    art=select_variant_resources(listing['members'],args.private_prefix)
    extracted={}
    for member in art:
        target=owned(dest/Path(member).name)
        if not target.exists():
            subprocess.run([str(ARCH),'extract-member',str(archive),member,str(target)],
                           capture_output=True,text=True,check=True)
        else:
            # Verify pre-existing readback against fresh extraction, never trust
            # its own hash receipt as proof of the current archive member.
            check=owned(dest/(Path(member).name+'.check'))
            if check.exists():raise FileExistsError(check)
            subprocess.run([str(ARCH),'extract-member',str(archive),member,str(check)],
                           capture_output=True,text=True,check=True)
            if sha(target)!=sha(check):raise RuntimeError('Existing readback changed')
            check.unlink()
        extracted[Path(member).suffix]={'member':member,'path':str(target),'sha256':sha(target)}
    sys.path.insert(0,CFG['garrison_extension'])
    from garrison_shared import relic_chunky as rc
    stock=Path(donor['material']['source']['path'])
    if sha(stock)!=donor['material']['source']['sha256']:
        raise RuntimeError('Pinned donor material changed')
    changes=[]
    source_albedo_count=[0]
    def canonical(chunk,variant):
        payload=chunk.payload
        if chunk.children:
            payload=tuple(canonical(c,variant) for c in chunk.children)
        elif chunk.tag==b'PbTe':
            n=struct.unpack_from('<I',payload)[0]; pos=4; pairs=[]
            for _ in range(n):
                name,pos=rc.read_lp_string(payload,pos)
                value,pos=rc.read_lp_string(payload,pos)
                if name==albedo_slot:
                    if variant:
                        expected=extracted['.rrtex']['member'].replace('/','\\')
                        if value!=expected:raise RuntimeError('Unexpected compiled albedo binding')
                        changes.append({'material_path':[x.decode('ascii','replace') for x in chunk.path],
                                        'slot':name,'new_value':value})
                    else:source_albedo_count[0]+=1
                    value='<ALBEDO_ONLY>'
                pairs.append((name,value))
            if pos!=len(payload):raise RuntimeError('Unsupported material texture table suffix')
            payload=tuple(pairs)
        return (chunk.kind,chunk.tag,chunk.version,chunk.name,payload)
    a=rc.load(stock); b=rc.load(extracted['.rrmaterial']['path'])
    if (a.version,a.flags)!=(b.version,b.flags):raise RuntimeError('Material document header changed')
    if tuple(canonical(c,False) for c in a.roots)!=tuple(canonical(c,True) for c in b.roots):
        raise RuntimeError('Material changed beyond its albedoTexture reference')
    if not source_albedo_count[0] or len(changes)!=source_albedo_count[0]:
        raise RuntimeError('Override count differs from exact native albedo slot count')
    if extracted['.rrgeom']['sha256']!=donor['geometry']['source']['sha256']:
        raise RuntimeError('Stock variant unexpectedly changed geometry')
    write(report,{'schema':'ccp-060-albedo-material-verification/v1',
                  'status':'albedo_only_all_other_material_chunks_exact',
                  'archive':str(archive),'archive_sha256':sha(archive),
                  'cook_receipt_sha256':sha(args.cook),'donor_manifest_sha256':sha(args.donor),
                  'extracted':extracted,'changes':changes,
                  'native_albedo_slot_count':source_albedo_count[0],
                  'stock_geometry_byte_identical':True,
                  'normal_metal_owner_pattern_skin_lut_and_other_params_exact':True,
                  'limits':'Texture reference/cook/readback proof, not pixel fidelity, client import, appearance or gameplay acceptance.'})
    print(json.dumps({'status':'albedo_only_all_other_material_chunks_exact','report':str(report)}))


if __name__=='__main__':main()

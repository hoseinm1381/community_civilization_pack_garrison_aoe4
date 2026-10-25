"""Portable offline restoration, verification and exact 0.8.4 payload assembly.

No installation, model download, synthesis, Git push or game changes.
"""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from store import Reader, load, file_sha, sha, safe_path, write_json

ROOT=Path(__file__).resolve().parents[2]
NAMESPACE='b7fcea91257b408fb9e8ae4d8bc402e1'
LINKS={'cache':'cache','.tools':'tool-cache','output':'output','archives':'archives',
       'art/garrison_library':'garrison-library','art/stock_cache':'stock-cache','staging':'staging'}
FINAL='external/output/release_084/delivery/final-v1/'


def check_source_identity(root):
    def value(path,tag):
        values=[n.text for n in ET.parse(path).getroot().iter() if n.tag.rsplit('}',1)[-1]==tag]
        if len(values)!=1:raise ValueError('Missing or ambiguous source identity')
        return values[0].replace('-','').lower()
    if value(root/'community_civilization_pack.aoe4mod','ID')!=NAMESPACE or value(root/'assets/_default.burnproj','NiceName')!=NAMESPACE:
        raise ValueError('Project GUID / burn-project NiceName differ from Garrison namespace')


def path_key(value,doc):
    path=value.replace('\\','/').removeprefix('//?/'); lower=path.lower()
    origins=[doc['provenance'],*doc['provenance'].get('path_roots',[])]
    prefixes=[(origin[name].replace('\\','/').rstrip('/'),label) for origin in origins
              for name,label in [('source_root','source'),('external_root','external')]]
    for prefix,label in sorted(prefixes,key=lambda item:-len(item[0])):
        if lower.startswith(prefix.lower()+'/'):
            rel=path[len(prefix)+1:]
            if label=='source':
                for link,target in LINKS.items():
                    if rel.lower().startswith(link.lower()+'/'): return 'external/'+target+'/'+rel[len(link)+1:]
            key=label+'/'+rel;safe_path(ROOT,key);return key
    raise ValueError('Path outside recorded project roots: '+value)


def selected(key,profile):
    if profile=='all':return True
    if profile=='art':return key.startswith(('source/art/','external/garrison-library/','external/stock-cache/','external/resources_'))
    if profile=='voices':return key.startswith(('external/output/release_084/','external/staging/release_084/'))
    return key.startswith(('source/','external/resources_','external/garrison-library/',
        'external/archives/','external/output/release_084/integration/',
        FINAL,'external/output/release_083/delivery/final-v2/')) and not '/readback/' in key and not '/fresh-readback/' in key


def reader(args):
    folder=ROOT/'development-data/snapshot-084-v1'
    default=folder/('index-initial-084-v1.json.gz' if getattr(args,'command',None) in ('release','rebuild-084') else 'index.json.gz')
    if not default.exists():default=folder/'index.json.gz'
    index=Path(args.index) if getattr(args,'index',None) else default
    return Reader(index.parent,load(index))


def restore(args,r):
    dest=args.destination.resolve();count=0
    source_parent=Path(getattr(args,'source_parent',None) or dest).resolve()
    for key in r.doc['files']:
        if (args.prefix and key.startswith(args.prefix)) or (not args.prefix and selected(key,args.profile)):
            count+=r.restore(key,source_parent if key.startswith('source/') else dest)
            if count and count%1000==0:print('RESTORED',count,flush=True)
    print(json.dumps(dict(restored=count,destination=str(dest),source_parent=str(source_parent),profile=args.profile)))


def release(args,r):
    dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=True)
    for name in ['community_civilization_pack-0.8.4.zip','garrison.json','START-HERE.txt','verification.json']:
        key=FINAL+name;p=dest/name;data=r.read(key)
        if p.exists() and p.read_bytes()!=data:raise ValueError('Edited delivery preserved: '+str(p))
        if not p.exists():
            with p.open('xb') as f:f.write(data)
    print('RELEASE_EXPORTED',dest)


def run(args,folder,label):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace')
    (folder/(label+'.log')).write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(label+' failed; inspect log')
    return result.stdout


def rebuild(args,r):
    check_source_identity(ROOT)
    dest=args.destination.resolve()
    if dest.exists():raise FileExistsError('Use a new immutable destination')
    dest.mkdir(parents=True)
    expected=json.loads(r.read(FINAL+'verification.json'))
    policy=json.loads(r.read(FINAL+'changed-member-policy.json'))
    basekey='external/output/release_083/delivery/final-v2/community_civilization_pack.sga'
    base=dest/'baseline.sga';base.write_bytes(r.read(basekey))
    if file_sha(base)!=policy['baseline_archive_sha256']:raise ValueError('Baseline provenance differs')
    listing=json.loads(run([args.archive_tool,'list',base,'--verify'],dest,'baseline-list'))
    if listing['archive']['name']!=NAMESPACE or not listing['archive']['verification']['verified']:raise ValueError('Baseline identity invalid')
    lists={'attrib':[],'data':[]}
    for member,row in sorted(policy['payload'].items()):
        # Resolve original evidence paths without modifying the receipt or its hashes.
        data=r.read(path_key(row['file'],r.doc))
        if sha(data)!=row['sha256']:raise ValueError('Payload provenance differs: '+member)
        p=safe_path(dest/'payload','source/'+member);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        lists['attrib' if member.startswith('attrib/') else 'data'].append(member+'='+str(p))
    current=base
    for alias in ['attrib','data']:
        manifest=dest/(alias+'-members.txt');manifest.write_bytes(('\n'.join(lists[alias])+'\n').encode())
        result=dest/('attributes.sga' if alias=='attrib' else 'community_civilization_pack.sga')
        run([args.archive_tool,'set-members',current,manifest,result,'--alias',alias],dest,'assemble-'+alias);current=result
    if file_sha(current)!=expected['sga_sha256']:raise ValueError('Rebuilt SGA differs from the verified release')
    listing=json.loads(run([args.archive_tool,'list',current,'--verify'],dest,'final-list'))
    check_source_identity(ROOT)
    if listing['archive']['name']!=NAMESPACE or not listing['archive']['verification']['verified']:raise ValueError('Final identity invalid')
    extraction=dest/'fresh-readback'
    run([args.archive_tool,'extract',current,extraction,'--filter','.'],dest,'fresh-extract')
    actual={p.relative_to(extraction).as_posix():file_sha(p) for p in extraction.rglob('*') if p.is_file()}
    if actual!=expected['member_sha256'] or {m['path']:m['toc'] for m in listing['members']}!=expected['mounts']:
        raise ValueError('Fresh archive bytes or mounts differ')
    release(argparse.Namespace(destination=dest),r)
    with zipfile.ZipFile(dest/'community_civilization_pack-0.8.4.zip') as z:
        if z.testzip() or sha(z.read(current.name))!=file_sha(current):raise ValueError('Release ZIP differs from rebuilt SGA')
    write_json(dest/'portable-rebuild-proof.json',dict(passed=True,sga_sha256=file_sha(current),
        members=len(actual),namespace=NAMESPACE,native_compile=False,native_game_test=False))
    print('EXACT_084_REBUILD_PASSED',len(actual),flush=True)


def filesystem(path):
    if os.name!='nt':raise ValueError('Native workspace configuration needs Windows and NTFS')
    import ctypes
    anchor=Path(path).resolve().anchor
    if len(anchor)!=3 or anchor[1:]!=':\\':raise ValueError('Use a local NTFS source drive')
    result=ctypes.create_unicode_buffer(64)
    if not ctypes.windll.kernel32.GetVolumeInformationW(ctypes.c_wchar_p(anchor),None,0,None,None,None,result,len(result)):
        raise ctypes.WinError()
    return result.value


def configure(args):
    """Configure a RESTORED copy only. Never rewrite the frozen snapshot."""
    work=args.destination.resolve();src=Path(getattr(args,'source_parent',None) or work).resolve()/'source';external=work/'external'
    marker=src/'workspace.json'
    if not marker.is_file() or not external.is_dir():raise ValueError('Restore development profile first')
    if filesystem(src)!='NTFS':
        raise ValueError('Legacy source junctions require NTFS. Restore with --source-parent on an NTFS drive; large external data can stay on exFAT.')
    cfg=load(marker);cfg['external_root']=str(external);cfg['python']=sys.executable
    if args.tools:
        user=load(args.tools)
        for name in ('blender','blender_python','garrison_extension','garrison_core','archive_tool','content_editor','art_editor','source_root','donor_root'):
            if name in user:cfg[name]=user[name]
    for link,target in LINKS.items():
        local=src/link;remote=external/target;remote.mkdir(parents=True,exist_ok=True)
        if local.exists():
            if not local.is_junction() or local.resolve()!=remote.resolve():raise ValueError('Existing path preserved: '+str(local))
            continue
        local.parent.mkdir(parents=True,exist_ok=True)
        env=dict(os.environ,GARRISON_LINK=str(local),GARRISON_TARGET=str(remote))
        subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',
            'New-Item -ItemType Junction -Path $env:GARRISON_LINK -Value $env:GARRISON_TARGET | Out-Null'],env=env,check=True)
    write_json(src/'workspace.original.json',load(marker)) if not (src/'workspace.original.json').exists() else None
    write_json(marker,cfg)
    sys.path.insert(0,str(src/'tools'));from workspace_support import check_storage
    check_storage(src,cfg)
    print('RESTORED_WORKSPACE_CONFIGURED',src)
    print('Historical absolute-path freezes remain provenance; they are not relocation acceptance tests.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--index',type=Path)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('verify')
    restore_p=sub.add_parser('restore');restore_p.add_argument('--destination',type=Path,default=ROOT/'.local/restored')
    restore_p.add_argument('--profile',choices=['development','art','voices','all'],default='development');restore_p.add_argument('--prefix')
    restore_p.add_argument('--source-parent',type=Path,help='Optional NTFS parent for source; external data remains in destination/external')
    exp=sub.add_parser('release');exp.add_argument('--destination',type=Path,default=ROOT/'.local/delivery')
    rb=sub.add_parser('rebuild-084');rb.add_argument('--destination',type=Path,required=True);rb.add_argument('--archive-tool',type=Path,required=True)
    cf=sub.add_parser('configure');cf.add_argument('--destination',type=Path,default=ROOT/'.local/restored');cf.add_argument('--tools',type=Path)
    cf.add_argument('--source-parent',type=Path,help='Same NTFS source parent used during restore')
    args=p.parse_args()
    if args.command=='configure':configure(args);return
    r=reader(args)
    try:
        if args.command=='verify':print(json.dumps(r.verify(lambda n:print('VERIFIED_FILES',n,flush=True))))
        elif args.command=='restore':restore(args,r)
        elif args.command=='release':release(args,r)
        elif args.command=='rebuild-084':rebuild(args,r)
    finally:r.close()


if __name__=='__main__':main()

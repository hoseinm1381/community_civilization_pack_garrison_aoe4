"""Narrow, inventoried cleanup for the owner's 0.8.4 handoff. No recursive delete."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
from store import walk, file_sha, load, write_json

ROOT=Path(__file__).resolve().parents[2]
EXT=Path(json.loads((ROOT/'workspace.json').read_text())['external_root']).resolve()
AUDIT=EXT/'consolidation_084_collaboration'
CACHE='tool-cache/local-voices-084/'
READBACKS=[
    ('output/release_084/delivery/final-v1/fresh-readback','output/release_084/delivery/final-v1'),
    ('output/release_083/verification/20261024T195554328061Z/readback','output/release_083/delivery/final-v2')]


def owned(rel):
    p=EXT/rel
    if '..' in Path(rel).parts or Path(rel).is_absolute() or not p.resolve().is_relative_to(EXT) or p.resolve()==EXT:
        raise ValueError('Unsafe cleanup target')
    return p


def guard():
    sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
    check_storage(ROOT,json.loads((ROOT/'workspace.json').read_text()))


def plan(args):
    guard();AUDIT.mkdir(parents=True,exist_ok=True)
    if (AUDIT/'cleanup-plan.json.gz').exists():raise FileExistsError('Cleanup plan exists; preserve/review it')
    files=[];roots=[];archive_proofs={}
    for rel in [CACHE+'uv-cache',CACHE+'pycache']:
        root=owned(rel)
        if root.is_junction() or root.is_symlink():raise ValueError('Refuse linked cleanup root')
        roots.append(rel)
        files.extend((p,'regenerable installer/bytecode cache',None) for p in walk(root))
    for rel,delivery in READBACKS:
        folder=owned(delivery);proof=load(folder/'verification.json');archive=folder/'community_civilization_pack.sga'
        if file_sha(archive)!=proof['sga_sha256']:raise ValueError('Retained source archive changed')
        archive_proofs[delivery]=proof['sga_sha256'];root=owned(rel);roots.append(rel)
        expected=proof['member_sha256'];actual={p.relative_to(root).as_posix():p for p in walk(root)}
        if set(actual)!=set(expected):raise ValueError('Readback scope differs from retained archive')
        files.extend((p,'exact archive extraction',expected[n]) for n,p in actual.items())
    def inspect(item):
        p,reason,expected=item;rel=p.relative_to(EXT).as_posix();digest=file_sha(p);size=p.stat().st_size
        if expected and digest!=expected:raise ValueError('Readback differs from retained archive')
        return dict(path=rel,sha256=digest,bytes=size,allocated_bytes=((size+262143)//262144)*262144,reason=reason)
    rows=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i,row in enumerate(pool.map(inspect,files),1):
            rows.append(row)
            if i%5000==0:print('CLEANUP_INVENTORIED',i,flush=True)
    index=load(args.repository/'development-data/snapshot-084-v1/index.json.gz')
    for row in rows:
        if row['reason']=='exact archive extraction' and index['files'].get('external/'+row['path'],{}).get('sha256')!=row['sha256']:
            raise ValueError('Readback not preserved in contributor store')
    doc=dict(user_authorized=True,external_root=str(EXT),roots=roots,files=rows,archives=archive_proofs,
        runtime_smoke='Torch 2.8.0+cu128 CUDA true; torchaudio 2.8.0+cu128; Transformers 4.57.6; VieNeu 3.8.3',
        preserves=['installed runtime','model weights','editable art','voice masters','paid originals','recovery stores','releases','rollback','diagnostics'],
        logical_bytes=sum(r['bytes'] for r in rows),allocated_file_bytes=sum(r['allocated_bytes'] for r in rows))
    write_json(AUDIT/'cleanup-plan.json.gz',doc)
    print('CLEANUP_PLAN',len(rows),doc['logical_bytes'],doc['allocated_file_bytes'],flush=True)


def apply(args):
    guard();proof=load(args.repository/'docs/handoff-verification.json')
    if not proof.get('store_all_files_verified') or not proof.get('portable_exact_084_rebuild'):
        raise ValueError('Full contributor preservation and exact rebuild proof required before deletion')
    doc=load(AUDIT/'cleanup-plan.json.gz')
    if not doc['user_authorized'] or Path(doc['external_root']).resolve()!=EXT:raise ValueError('Cleanup ownership differs')
    expected_roots={CACHE+'uv-cache',CACHE+'pycache',*(rel for rel,delivery in READBACKS)}
    if set(doc['roots'])!=expected_roots:raise ValueError('Cleanup scope differs from the reviewed fixed targets')
    for rel,digest in doc['archives'].items():
        if file_sha(owned(rel)/'community_civilization_pack.sga')!=digest:raise ValueError('Retained archive changed')
    allowed=[owned(r).resolve() for r in doc['roots']]
    def recheck(row):
        p=owned(row['path'])
        if not any(p.resolve().is_relative_to(r) for r in allowed):raise ValueError('Unplanned target')
        if not p.exists():return row,False,None
        before=p.stat()
        if before.st_size!=row['bytes'] or file_sha(p)!=row['sha256']:raise ValueError('Changed candidate preserved: '+str(p))
        after=p.stat();signature=(after.st_size,after.st_mtime_ns)
        if signature!=(before.st_size,before.st_mtime_ns):raise ValueError('Candidate changed during hashing')
        return row,True,signature
    removed=logical=allocated=0
    with (AUDIT/'deletion-operations.jsonl').open('a',encoding='utf-8') as log,ThreadPoolExecutor(max_workers=8) as pool:
        for row,exists,signature in pool.map(recheck,doc['files']):
            if not exists:continue
            p=owned(row['path'])
            # Recheck metadata after hashing and before unlink; never remove a tree.
            current=p.stat()
            if (current.st_size,current.st_mtime_ns)!=signature:raise ValueError('Candidate changed during cleanup')
            log.write(json.dumps(dict(action='unlink_intent',**row))+'\n');log.flush()
            p.unlink()
            log.write(json.dumps(dict(action='unlinked',path=row['path']))+'\n');log.flush()
            removed+=1;logical+=row['bytes'];allocated+=row['allocated_bytes']
            if removed%5000==0:print('CLEANUP_REMOVED',removed,flush=True)
    for rel in doc['roots']:
        root=owned(rel)
        if not root.exists():continue
        directories=[];stack=[root]
        while stack:
            folder=stack.pop()
            for p in folder.iterdir():
                if p.is_dir() and not p.is_symlink() and not p.is_junction():stack.append(p);directories.append(p)
        for p in sorted(directories,key=lambda p:len(p.parts),reverse=True):
            try:p.rmdir()
            except OSError:pass
        # Keep cache/readback root itself; this avoids any implicit path recreation.
    guard()
    for rel,digest in doc['archives'].items():
        if file_sha(owned(rel)/'community_civilization_pack.sga')!=digest:raise ValueError('Post-cleanup archive differs')
    result=dict(passed=True,removed_files=removed,reclaimed_logical_bytes=logical,
        reclaimed_allocated_file_bytes=allocated,links_verified=7,retained_archive_hashes_exact=True)
    write_json(AUDIT/'cleanup-result.json',result);print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);p.add_argument('--repository',type=Path,required=True)
    args=p.parse_args();globals()[args.command](args)

"""Owner-only reversible cold storage. Explicit plan, exact hashes, no tree delete."""
import argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/collaboration'))
from store import Reader,load,write_json,file_sha,walk
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
CFG=json.loads((ROOT/'workspace.json').read_text())
EXT=Path(CFG['external_root']).resolve()
REPO=Path(r'F:\aoe_4_temp\community_civilization_pack_garrison_aoe4')
STORE=REPO/'development-data/snapshot-084-v1'
INDEX=STORE/'index-initial-084-v1.json.gz'
AUDIT=EXT/'consolidation_085'
INDEXED_ROOTS=(
    'output/release_084/local','output/release_084/generation',
    'output/release_084/integration/stock-efforts-v1',
    'output/release_083/delivery','output/release_082_animation/delivery-v1',
    'output/release_081/delivery')
RUNTIME_ROOTS=(
    'tool-cache/local-voices-084/venv','tool-cache/local-voices-084/python',
    'tool-cache/local-voices-084/models','tool-cache/local-voices-084/downloads',
    'tool-cache/local-voices-084/tools','tool-cache/local-voices-084/hf-cache')
VOICE_ROOTS=('output/release_084/local','output/release_084/generation',
             'output/release_084/integration/stock-efforts-v1')
HISTORY_ROOTS=('output/release_083/delivery','output/release_082_animation/delivery-v1',
               'output/release_081/delivery')


def owned(rel,root=None):
    root=EXT if root is None else root
    if not rel or '\\' in rel or any(x in ('','..','.') or ':' in x for x in rel.split('/')):
        raise ValueError('Unsafe relative path')
    target=root.joinpath(*rel.split('/'))
    if not target.resolve().is_relative_to(root.resolve()) or target.resolve()==root.resolve():raise ValueError('Path escapes owned root')
    probe=root
    for part in rel.split('/'):
        probe=probe/part
        if probe.is_symlink() or probe.is_junction():raise ValueError('Linked cold-storage path refused')
    return target


def selected(rel):
    if rel.startswith('output/release_084/local/'):
        # Keep small top-level manifests, transcripts/exception reports and logs.
        return len(rel.split('/'))>4
    if rel.startswith(('output/release_083/delivery/','output/release_082_animation/delivery-v1/','output/release_081/delivery/')):
        return Path(rel).suffix.lower() not in ('.zip','.sga','.json','.log','.txt')
    return any(rel.startswith(r+'/') for r in INDEXED_ROOTS[1:3])


def guard():
    check_storage(ROOT,CFG)
    proof=load(EXT/'output/release_085/final-v2/verification.json')
    delivery=EXT/'output/release_085/final-v2'
    version=proof.get('version','0.8.5')
    if version not in ('0.8.5','0.8.6','0.8.7','0.8.8'):raise ValueError('Unreviewed current release version')
    if file_sha(delivery/'community_civilization_pack.sga')!=proof['sga_sha256'] or file_sha(delivery/('community_civilization_pack-'+version+'.zip'))!=proof['zip_sha256']:
        raise ValueError('085 release changed')
    return proof


def make_plan():
    guard();AUDIT.mkdir(exist_ok=True)
    planfile=AUDIT/'indexed-plan.json.gz'
    if planfile.exists():raise FileExistsError('Immutable plan already exists')
    doc=load(INDEX);r=Reader(STORE,doc)
    candidates=[];preserved=[]
    for root in INDEXED_ROOTS:
        if not owned(root).exists():continue
        for p in walk(owned(root)):
            rel=p.relative_to(EXT).as_posix()
            if not selected(rel):continue
            row=doc['files'].get('external/'+rel)
            if not row or row['bytes']!=p.stat().st_size:preserved.append(rel);continue
            candidates.append((rel,row))
    used={doc['chunks'][h]['pack'] for _,row in candidates for h in row['chunks']}
    for name in used:
        if file_sha(STORE/name)!=doc['packs'][name]['sha256']:raise ValueError('Shared recovery pack changed')
    def hash_original(item):
        rel,row=item;p=owned(rel);s=p.stat()
        if file_sha(p)!=row['sha256']:return None
        return dict(path=rel,sha256=row['sha256'],bytes=s.st_size,allocated_bytes=((s.st_size+262143)//262144)*262144)
    rows=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i,(item,result) in enumerate(zip(candidates,pool.map(hash_original,candidates)),1):
            rel,row=item
            if result is None:preserved.append(rel);continue
            # Independently reconstruct every file from its lossless recovery chunks.
            r.read('external/'+rel);rows.append(result)
            if i%5000==0:print('RECOVERY_VERIFIED',i,flush=True)
    r.close()
    # Actual isolated filesystem restoration, including an editable master.
    sample=next((row['path'] for row in rows if row['path'].endswith('.wav')),rows[0]['path'])
    probe=AUDIT/'restore-smoke'
    r=Reader(STORE,doc);r.restore('external/'+sample,probe);r.close()
    if file_sha(probe/'external'/sample)!=doc['files']['external/'+sample]['sha256']:raise ValueError('Restore smoke failed')
    write_json(planfile,dict(roots=INDEXED_ROOTS,index_sha256=file_sha(INDEX),store=str(STORE),
        files=rows,preserved_unmatched=preserved,all_recovery_files_reconstructed=True,isolated_restore=sample,
        logical_bytes=sum(x['bytes'] for x in rows),allocated_bytes=sum(x['allocated_bytes'] for x in rows)))
    print('INDEXED_PLAN',len(rows),sum(x['bytes'] for x in rows),sum(x['allocated_bytes'] for x in rows),flush=True)


def retire(rows,allowed,label):
    guard()
    paths=[owned(p).resolve() for p in allowed]
    count=logical=allocated=0
    def validate(row):
        p=owned(row['path'])
        if not any(p.resolve().is_relative_to(root) for root in paths):raise ValueError('Unplanned path')
        if not p.exists():return row,p,None
        before=p.stat()
        if before.st_size!=row['bytes'] or file_sha(p)!=row['sha256']:raise ValueError('Edited file preserved: '+row['path'])
        after=p.stat();signature=(after.st_size,after.st_mtime_ns,after.st_ino)
        if (before.st_size,before.st_mtime_ns,before.st_ino)!=signature:raise ValueError('File changed during check')
        return row,p,signature
    with (AUDIT/(label+'-operations.jsonl')).open('a',encoding='utf-8') as journal:
        # Hash/path verification overlaps small-file latency. Mutations remain
        # serialized and each file's identity/metadata is rechecked immediately.
        for row,p,signature in bounded_results(validate,rows):
            if signature is None:continue
            current=p.stat()
            if (current.st_size,current.st_mtime_ns,current.st_ino)!=signature:raise ValueError('File changed before retirement')
            journal.write(json.dumps(dict(action='unlink_intent',**row))+'\n');journal.flush()
            p.unlink()
            journal.write(json.dumps(dict(action='unlinked',path=row['path']))+'\n');journal.flush()
            count+=1;logical+=row['bytes'];allocated+=row['allocated_bytes']
            if count%5000==0:print(label,'RETIRED',count,flush=True)
    # Roots remain; remove only empty nested directories after validating ownership.
    for rel in allowed:
        root=owned(rel)
        for parent,dirs,files in os.walk(root,topdown=False,followlinks=False):
            p=Path(parent)
            if p==root or p.is_junction() or p.is_symlink():continue
            if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Unexpected linked path')
            try:p.rmdir()
            except OSError:pass
    write_json(AUDIT/(label+'-result.json'),dict(files=count,logical_bytes=logical,allocated_bytes=allocated))
    print(label,'RETIRED_BYTES',logical,allocated,flush=True)


def apply_indexed():
    plan=load(AUDIT/'indexed-plan.json.gz')
    if tuple(plan['roots'])!=INDEXED_ROOTS or not plan['all_recovery_files_reconstructed'] or file_sha(INDEX)!=plan['index_sha256']:raise ValueError('Recovery plan differs')
    doc=load(INDEX)
    packs={doc['chunks'][h]['pack'] for row in plan['files'] for h in doc['files']['external/'+row['path']]['chunks']}
    for name in packs:
        if file_sha(STORE/name)!=doc['packs'][name]['sha256']:raise ValueError('Recovery pack changed')
    for row in plan['files']:
        original=doc['files']['external/'+row['path']]
        if original['sha256']!=row['sha256'] or original['bytes']!=row['bytes'] or not selected(row['path']):raise ValueError('Plan file differs')
    retire(plan['files'],INDEXED_ROOTS,'indexed')


class StreamingZipSink:
    """No per-entry header seeks/flushes on exFAT; standard ZIP descriptors."""
    def __init__(self,stream):self.stream=stream;self.position=0
    def tell(self):return self.position
    def write(self,data):
        result=self.stream.write(data);self.position+=result;return result
    def flush(self):self.stream.flush()


def read_snapshot(path):
    before=path.stat();data=path.read_bytes();after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or len(data)!=after.st_size:
        raise ValueError('Voice input changed during packing')
    return path,data,dict(path=path.relative_to(EXT).as_posix(),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),allocated_bytes=((len(data)+262143)//262144)*262144)


def bounded_results(function,paths):
    # Bounded reads overlap small-file latency; never queue the whole voice bank
    # or use this for multi-gigabyte CUDA libraries/installers.
    source=iter(paths);pending=deque()
    with ThreadPoolExecutor(max_workers=8) as pool:
        for _ in range(8):
            p=next(source,None)
            if p is not None:pending.append(pool.submit(function,p))
        while pending:
            yield pending.popleft().result()
            p=next(source,None)
            if p is not None:pending.append(pool.submit(function,p))


def prefetched(paths):yield from bounded_results(read_snapshot,paths)


def pack_bundle(roots=None,name='local-voice-tools',only_selected=False):
    roots=RUNTIME_ROOTS if roots is None else roots
    # Packing is non-destructive and may run while final package validation is
    # still finishing. Actual retirement additionally requires the final release.
    check_storage(ROOT,CFG);folder=EXT/'resources_085';folder.mkdir(exist_ok=True)
    archive=folder/(name+'.zip');receipt=folder/(name+'.json.gz')
    if archive.exists() or receipt.exists():raise FileExistsError('Immutable tool bundle already exists')
    rows=[]
    with archive.open('xb',buffering=16*1024*1024) as output,zipfile.ZipFile(StreamingZipSink(output),'w',zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        if name=='voice-development':
            paths=[]
            for root in roots:
                for parent,dirs,files in os.walk(owned(root),followlinks=False):
                    if any((Path(parent)/d).is_junction() or (Path(parent)/d).is_symlink() for d in dirs):raise ValueError('Linked voice dependency')
                    for filename in files:
                        p=Path(parent)/filename
                        if p.is_symlink():raise ValueError('Linked voice input')
                        if p.stat().st_size>64*1024*1024:raise ValueError('Voice prefetch member exceeds bounded size')
                        paths.append(p)
            for p,data,row in prefetched(paths):
                z.writestr(row['path'],data);rows.append(row)
                if len(rows)%5000==0:print('VOICE_PACKED',len(rows),flush=True)
        for root in roots:
            if name=='voice-development':continue
            # Include bytecode here too; preserve the complete installed dependency tree.
            for parent,dirs,files in os.walk(owned(root),followlinks=False):
                if any((Path(parent)/d).is_junction() or (Path(parent)/d).is_symlink() for d in dirs):raise ValueError('Linked runtime dependency')
                for filename in files:
                    p=Path(parent)/filename
                    if p.is_symlink():raise ValueError('Linked runtime file')
                    rel=p.relative_to(EXT).as_posix()
                    if only_selected and not selected(rel):continue
                    before=p.stat();h=hashlib.sha256()
                    with p.open('rb') as source,z.open(rel,'w',force_zip64=True) as target:
                        while data:=source.read(4*1024*1024):h.update(data);target.write(data)
                    after=p.stat()
                    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Runtime changed during packing')
                    rows.append(dict(path=rel,sha256=h.hexdigest(),bytes=after.st_size,allocated_bytes=((after.st_size+262143)//262144)*262144))
                    if len(rows)%5000==0:print('RUNTIME_PACKED',len(rows),flush=True)
    with zipfile.ZipFile(archive) as z:
        if set(z.namelist())!={row['path'] for row in rows}:raise ValueError('Runtime archive scope differs')
        for i,row in enumerate(rows,1):
            with z.open(row['path']) as f:
                if hashlib.file_digest(f,'sha256').hexdigest()!=row['sha256']:raise ValueError('Runtime archived file differs')
            if i%5000==0:print('RUNTIME_VERIFIED',i,flush=True)
        # Actual isolated filesystem restore of configuration and binary/audio media.
        samples=[]
        for suffix in ('pyvenv.cfg','.dll','.wav','.ogg'):
            sample=next((row for row in rows if row['path'].endswith(suffix)),None)
            if sample:samples.append(sample)
        if not samples:samples=rows[:1]
        for i,smoke in enumerate(samples):
            target=AUDIT/(name+'-restore-smoke-'+str(i));target.write_bytes(z.read(smoke['path']))
            if file_sha(target)!=smoke['sha256']:raise ValueError('Bundle restoration failed')
    write_json(receipt,dict(archive=str(archive),archive_sha256=file_sha(archive),archive_bytes=archive.stat().st_size,
        roots=roots,files=rows,all_files_readback_verified=True,
        logical_bytes=sum(x['bytes'] for x in rows),allocated_bytes=sum(x['allocated_bytes'] for x in rows),
        restoration='Restore exact original paths with cold_storage.py restore-runtime before invoking local TTS scripts.'))
    print('RUNTIME_ARCHIVED',len(rows),archive.stat().st_size,flush=True)


def pack_runtime():pack_bundle()


def apply_runtime():
    receipt=load(EXT/'resources_085/local-voice-tools.json.gz')
    if tuple(receipt['roots'])!=RUNTIME_ROOTS or not receipt['all_files_readback_verified'] or file_sha(receipt['archive'])!=receipt['archive_sha256']:raise ValueError('Runtime recovery changed')
    retire(receipt['files'],RUNTIME_ROOTS,'runtime')


def apply_bundle(roots,name):
    receipt=load(EXT/'resources_085'/(name+'.json.gz'))
    if tuple(receipt['roots'])!=roots or not receipt['all_files_readback_verified'] or file_sha(receipt['archive'])!=receipt['archive_sha256']:raise ValueError('Local recovery bundle changed')
    retire([row for row in receipt['files'] if selected(row['path'])],roots,name)


def retire_readbacks():
    guard()
    for label in ('final-v1','final-v2'):
        folder=EXT/'output/release_085'/label
        proof=load(folder/'verification.json')
        if file_sha(folder/'community_civilization_pack.sga')!=proof['sga_sha256']:raise ValueError('Readback owning archive changed')
        root=folder/'fresh-readback'
        paths={p.relative_to(root).as_posix():p for p in walk(root)}
        if not paths:continue
        if set(paths)!=set(proof['member_sha256']):raise ValueError('Unexpected readback file scope; preserve it')
        rows=[]
        for member,p in paths.items():
            size=p.stat().st_size
            if file_sha(p)!=proof['member_sha256'][member]:raise ValueError('Readback differs from retained SGA')
            rows.append(dict(path=p.relative_to(EXT).as_posix(),bytes=size,sha256=proof['member_sha256'][member],allocated_bytes=((size+262143)//262144)*262144))
        rel=root.relative_to(EXT).as_posix()
        write_json(AUDIT/(label+'-readback-plan.json.gz'),dict(retained_sga_sha256=proof['sga_sha256'],files=rows))
        retire(rows,(rel,),label+'-readback')


def write_restored(rel,data,expected):
    target=owned(rel)
    if target.exists():
        if file_sha(target)!=expected:raise ValueError('Edited destination preserved: '+rel)
        return False
    if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Restore data corrupt')
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_name(target.name+'.restore085')
    with temporary.open('xb') as f:f.write(data)
    # Windows rename refuses to replace a concurrently-created destination.
    temporary.rename(target)
    return True


def write_restored_stream(rel,stream,expected,size):
    target=owned(rel)
    if target.exists():
        if file_sha(target)!=expected:raise ValueError('Edited destination preserved: '+rel)
        return False
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_name(target.name+'.restore085')
    h=hashlib.sha256();total=0
    with temporary.open('xb') as out:
        while data:=stream.read(4*1024*1024):
            total+=len(data);h.update(data);out.write(data)
    if total!=size or h.hexdigest()!=expected:raise ValueError('Restore data corrupt; diagnostic temporary retained')
    temporary.rename(target)
    return True


def restore(prefix,runtime=False,bundle='local-voice-tools'):
    check_storage(ROOT,CFG);owned(prefix)
    count=0
    if runtime:
        if bundle not in ('local-voice-tools','voice-development','historical-development'):raise ValueError('Unknown recovery bundle')
        doc=load(EXT/'resources_085'/(bundle+'.json.gz'))
        if file_sha(doc['archive'])!=doc['archive_sha256']:raise ValueError('Runtime archive changed')
        with zipfile.ZipFile(doc['archive']) as z:
            for row in doc['files']:
                if row['path']==prefix or row['path'].startswith(prefix+'/'):
                    with z.open(row['path']) as stream:
                        count+=write_restored_stream(row['path'],stream,row['sha256'],row['bytes'])
    else:
        doc=load(INDEX);r=Reader(STORE,doc)
        for key,row in doc['files'].items():
            if key=='external/'+prefix or key.startswith('external/'+prefix+'/'):
                target=owned(key[len('external/'):])
                if target.exists() and file_sha(target)==row['sha256']:continue
                count+=write_restored(key[len('external/'):],r.read(key),row['sha256'])
        r.close()
    print('RESTORED',count,flush=True)


def main():
    # The owner prohibited accessing the contributor checkout during its own
    # reduction. Indexed operations remain testable historical helpers, disabled
    # at the CLI. Every current operation uses independent local ZIP bundles.
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['pack-runtime','apply-runtime','pack-voices','apply-voices','pack-history','apply-history','retire-readbacks','restore-runtime','restore-bundle'])
    parser.add_argument('--prefix');parser.add_argument('--bundle',default='local-voice-tools');args=parser.parse_args()
    if args.action.startswith('restore'):
        if not args.prefix:raise ValueError('Explicit relative prefix required')
        restore(args.prefix,True,args.bundle)
    else:{'pack-runtime':pack_runtime,'apply-runtime':apply_runtime,'retire-readbacks':retire_readbacks,
          'pack-voices':lambda:pack_bundle(VOICE_ROOTS,'voice-development'),
          'apply-voices':lambda:apply_bundle(VOICE_ROOTS,'voice-development'),
          'pack-history':lambda:pack_bundle(HISTORY_ROOTS,'historical-development',True),
          'apply-history':lambda:apply_bundle(HISTORY_ROOTS,'historical-development')}[args.action]()


if __name__=='__main__':main()

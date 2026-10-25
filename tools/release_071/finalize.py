"""Compact completed operation evidence and independently measure both volumes."""
import argparse
import ctypes
import gzip
import json
from pathlib import Path
from consolidate import ROOTS, TX, EXT, ROOT, CFG, dump, walk
from resources import sha


def compact_evidence():
    source=TX/'retirement-plan.json'
    raw=source.read_bytes()
    packed=gzip.compress(raw,compresslevel=6,mtime=0)
    assert gzip.decompress(packed)==raw
    target=TX/'retirement-plan.json.gz'
    target.write_bytes(packed)
    assert gzip.decompress(target.read_bytes())==raw
    dump(TX/'retirement-plan-storage.json',dict(original_sha256=sha(source),gzip_sha256=sha(target),
                                              original_bytes=len(raw),stored_bytes=len(packed),
                                              restore='gzip.decompress(retirement-plan.json.gz) restores exact UTF-8 JSON bytes'))
    print('Verified compact retirement ledger; original plain ledger may now be removed:',str(source))


def measure(projection=False):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    fn=kernel.GetCompressedFileSizeW
    fn.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_uint32)]
    fn.restype=ctypes.c_uint32
    space=kernel.GetDiskFreeSpaceW
    space.argtypes=[ctypes.c_wchar_p]+[ctypes.POINTER(ctypes.c_uint32)]*4
    space.restype=ctypes.c_int
    seen=set();result={};duplicates=0
    excluded=set()
    if projection:
        plan=json.loads((TX/'retirement-plan.json').read_text())
        excluded={str(Path(op['path'])).casefold() for op in plan['operations']}
    for drive,root in ROOTS.items():
        logical=unique=allocated=count=0
        sectors=ctypes.c_uint32();bps=ctypes.c_uint32();free=ctypes.c_uint32();clusters=ctypes.c_uint32()
        if not space(root.anchor,ctypes.byref(sectors),ctypes.byref(bps),ctypes.byref(free),ctypes.byref(clusters)):
            raise ctypes.WinError(ctypes.get_last_error())
        cluster=sectors.value*bps.value
        for p in walk(root):
            if projection and (str(p).casefold() in excluded or p==TX/'retirement-plan.json'):continue
            s=p.stat();count+=1;logical+=s.st_size
            identity=(s.st_dev,s.st_ino)
            if identity in seen:
                duplicates+=1;continue
            seen.add(identity);unique+=s.st_size
            hi=ctypes.c_uint32();ctypes.set_last_error(0)
            lo=fn('\\\\?\\'+str(p),ctypes.byref(hi))
            if lo==0xffffffff and ctypes.get_last_error():raise ctypes.WinError(ctypes.get_last_error())
            disk_size=(hi.value<<32)|lo
            allocated+=((disk_size+cluster-1)//cluster)*cluster
        result[drive]=dict(files=count,logical_named_file_bytes=logical,unique_file_bytes=unique,allocated_disk_bytes=allocated,allocation_unit=cluster)
    if projection:
        ledger=len(gzip.compress((TX/'retirement-plan.json').read_bytes(),compresslevel=6,mtime=0))
        result['F']['unique_file_bytes']+=ledger+2000000
        result['F']['allocated_disk_bytes']+=((ledger+262143)//262144)*262144+5242880
    total=sum(r['unique_file_bytes'] for r in result.values())
    disk=sum(r['allocated_disk_bytes'] for r in result.values())
    doc=dict(roots={k:str(v) for k,v in ROOTS.items()},by_volume=result,unique_file_bytes=total,allocated_disk_bytes=disk,
             hardlink_aliases=duplicates,under_3GB=total<3000000000,allocated_under_3GB=disk<3000000000,
             allocated_under_6GB=disk<6000000000,allocated_budget_bytes=6000000000,
             audit_before_unique_bytes=26557968984,recovered_unique_bytes=26557968984-total,
             note='Both owned roots counted once by actual device/inode; seven junctions excluded. Report written after measurement.')
    dump(TX/('projected-storage.json' if projection else 'final-storage.json'),doc)
    print(json.dumps(doc,indent=2),flush=True)
    if not projection:
        assert total<3000000000,'Unique-byte budget exceeded'
        assert disk<6000000000,'User-approved exFAT allocated-byte budget exceeded'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['compact','measure','project'])
    a=p.parse_args()
    if a.stage=='compact':compact_evidence()
    else:measure(a.stage=='project')

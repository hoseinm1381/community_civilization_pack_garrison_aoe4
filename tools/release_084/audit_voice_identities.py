"""Prove Garrison-derived deltas and check IDs against all current native RGDs."""
import copy
import argparse
import json
from pathlib import Path
import re
import sys
import warnings
from pipeline import guard,digest,save_json
from providers import ROOT,OUT


def main():
    guard();parser=argparse.ArgumentParser();parser.add_argument('--complete',action='store_true');args=parser.parse_args()
    cfg=json.loads((ROOT/'workspace.json').read_text())
    sys.path.insert(0,cfg['garrison_extension']);from garrison_shared import rgd
    receipt_path=OUT/'integration'/('voice-identities-complete.json' if args.complete else 'voice-identities-v1/receipt.json')
    receipt=json.loads(receipt_path.read_text());rows=[];ids={}
    for component in receipt.get('component_receipts',[]):
        if digest(component['file'])!=component['sha256']:raise RuntimeError('Identity component receipt changed')
    guid=cfg['project_guid'].replace('-','')
    rewires={(r['category'],Path(r['source']).stem):guid+':'+r['name'] for r in receipt['identities']}
    for row in receipt['identities']:
        if digest(row['compiled'])!=row['compiled_sha256'] or digest(row['source_file'])!=row['source_sha256']:
            raise RuntimeError('Changed derived identity or donor')
        before=rgd.read(Path(row['source_file']).read_bytes());after=rgd.read(Path(row['compiled']).read_bytes())
        a=list(rgd.flatten(before.nodes));b=list(rgd.flatten(after.nodes));changes=[]
        fields=dict(a)
        if len(a)!=len(b):raise RuntimeError('Derived resource structure changed')
        restored=copy.deepcopy(after);undo=list(rgd.flatten(restored.nodes))
        for (path,node),(other,new),(_,old) in zip(a,b,undo):
            if path!=other or node.kind!=new.kind:raise RuntimeError('Derived resource typing changed')
            if not isinstance(node.value,list) and node.value!=new.value:
                category=fields.get(path.rsplit('/',1)[0]+'/$PBGMAP')
                expected=rewires.get((category.value,node.value)) if node.key=='$PBGNAME' and category else None
                allowed=(node.key=='pbgid' and new.value==row['pbgid']) or (expected is not None and expected==new.value) or (
                    path.endswith(('/parent_pbg/$PBGNAME','/parent_pbg/$PBGMAP')) and new.value=='')
                if not allowed:raise RuntimeError('Unexpected nonidentity derived change '+path)
                changes.append(dict(path=path,before=node.value,after=new.value));old.value=node.value
        if rgd.write(restored)!=Path(row['source_file']).read_bytes():raise RuntimeError('Identity semantic undo did not restore exact donor bytes')
        if row['pbgid'] in ids:raise RuntimeError('Duplicate derived PBGID')
        ids[row['pbgid']]=row['name'];rows.append(dict(name=row['name'],pbgid=row['pbgid'],changes=changes,exact_byte_undo=True))
    official=json.loads((OUT/'inventory/official-lookup.json').read_text())
    archive=Path(official['archive'])
    if digest(archive)!=official['sha256']:raise RuntimeError('Current official archive changed')
    runtime=Path('C:/Users/RS/.codex/cache/aoe4-sga-extractor-session-20260717/_skill_sga_live_runtime')
    if not (runtime/'SGA-V10/src').is_dir():raise RuntimeError('Retained read-only archive reader is unavailable')
    sys.path[:0]=[str(runtime/'site-packages'),str(runtime/'SGA-V10/src')]
    warnings.filterwarnings('ignore')
    from relic.sga.v10 import EssenceFSHandler
    from relic.sga.core.definitions import Version
    EssenceFSHandler.version=Version(10,0)
    found={};count=0
    with archive.open('rb') as stream:
        fs=EssenceFSHandler.read(stream)
        for path in fs.walk.files():
            if not path.endswith('.rgd'):continue
            doc=rgd.read(fs.readbytes(path));count+=1
            for field,node in rgd.flatten(doc.nodes):
                if re.fullmatch(r'[^/]+/pbgid',field) and node.kind=='Int' and node.value in ids:
                    found.setdefault(str(node.value),[]).append(path)
            if count%5000==0:print('CURRENT_NATIVE_IDS_CHECKED',count,flush=True)
    base=ROOT/'output/release_083/delivery/final-v2/readback'
    baseline_hits={}
    for path in (base/'attrib').rglob('*.rgd'):
        for field,node in rgd.flatten(rgd.read(path.read_bytes()).nodes):
            if re.fullmatch(r'[^/]+/pbgid',field) and node.kind=='Int' and node.value in ids:
                baseline_hits.setdefault(str(node.value),[]).append(path.relative_to(base).as_posix())
    result=dict(schema='ccp-084-derived-identity-audit/v1',receipt_sha256=digest(receipt_path),
                official_archive_sha256=official['sha256'],official_rgds_checked=count,
                native_collisions=found,private_083_collisions=baseline_hits,identities=rows,
                source_and_active_archive_unchanged=True,
                native_compile_scope='Garrison cooked empty native attribute bases (0 instances), then derived compiled resource copies.',
                editable_identity_instances_native_compiled=False,full_084_native_compilation=False,
                active_speech_suppressed=False,passed=not found and not baseline_hits)
    target=OUT/'integration'/('voice-identities-complete-audit.json' if args.complete else 'voice-identities-v1/identity-audit.json')
    save_json(target,result)
    if not result['passed']:raise RuntimeError('Allocated identity collision; preserve evidence, do not activate')
    print('VOICE_IDENTITIES_EXACT_UNDO_AND_COLLISION_CHECK',len(rows),count,flush=True)


if __name__=='__main__':main()

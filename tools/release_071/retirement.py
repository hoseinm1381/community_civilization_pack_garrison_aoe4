"""Create a frozen, metadata-checked retirement allowlist after rebuild proof."""
import argparse
import hashlib
import gzip
import json
from pathlib import Path
from consolidate import ROOT, EXT, ROOTS, CFG, AUDIT, TX, STORE, dump, walk, physical
from resources import ResourceStore, deletion_gate, sha
from build import OUT, ROLLBACK, SGA_SHA, ZIP_SHA, KEY, freeze


def checks():
    freeze()
    retained=json.loads((TX/'retained.json').read_text())
    # This transaction authors its own tools/docs after input freezing. They are
    # preserved, never retirement targets; refresh their implementation hashes.
    for p in list((ROOT/'tools/release_071').glob('*.py'))+list((ROOT/'tools/release_071').glob('*.ps1'))+list((ROOT/'docs').glob('RELEASE_071*'))+[ROOT/'tools/build_release_071.ps1',ROOT/'docs/DEVELOPMENT_071.md',ROOT/'README.md',ROOT/'STORAGE.md',ROOT/'workspace.json']:
        k='E/'+p.relative_to(ROOT).as_posix();s=p.stat()
        retained[k]=dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p),canonical=k,reasons=['Current approved 071 implementation/documentation'])
    for p in [p for p in walk(ROOT/'art') if p.suffix.lower()=='.md']+[ROOT/'art/GARRISON_PROJECTS.json']:
        # art contains external junctions; only explicitly owned plain E docs.
        if p.is_file() and p.resolve().is_relative_to(ROOT):
            k='E/'+p.relative_to(ROOT).as_posix();s=p.stat()
            retained.setdefault(k,dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p),canonical=k,reasons=['Art navigation and provenance']))
    dump(TX/'retained.json',retained)
    store=ResourceStore(STORE)
    for k in store.index: store.read(k)
    failures=[]
    for k,r in retained.items():
        if k in ('E/docs/RELEASE_071_LEDGER.md',):
            continue  # Append-only execution notes never enter the retirement set.
        if r.get('packed'): continue
        p=physical(k)
        if not p.is_file() or p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:
            failures.append(k)
    if failures: raise ValueError('Retained file hash mismatch: '+repr(failures[:15]))
    normal=Path(CFG['source_root'])
    now={p.relative_to(normal).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in walk(normal)}
    assert now==json.loads((TX/'normal-before.json').read_text())
    local=TX/'blend-dependencies.json.gz'
    deps=json.loads(gzip.decompress(local.read_bytes())) if local.exists() else json.loads((AUDIT/'blend-dependencies.json').read_text())
    from consolidate import key
    for row in deps:
        assert key(row['blend']) in retained
        for image in row['images']:
            if not image['packed'] and image.get('resolved') and image.get('exists'):
                assert key(image['resolved']) in retained
    package=json.loads((OUT/'package-v1.json').read_text())
    assert package['package_verified'] and package['all_070_native_members_and_mounts_identical']
    assert sha(OUT/'delivery'/f'{KEY}.sga')==package['sga_sha256']
    assert sha(OUT/'delivery'/f'{KEY}-0.7.1.zip')==package['zip_sha256']
    assert json.loads((OUT/'native-source-v1.json').read_text())['passed']
    assert json.loads((OUT/'building-v1.json').read_text())['passed']
    assert json.loads((OUT/'unit-v2/receipt.json').read_text())['passed']
    return retained


def plan():
    retained=checks()
    local_inventory=TX/'pre-clean-inventory.json.gz'
    inventory=(json.loads(gzip.decompress(local_inventory.read_bytes())) if local_inventory.exists()
               else json.loads((AUDIT/'inventory.json').read_text()))
    old={r['drive']+'/'+r['path']:r for r in inventory['files']}
    operations=[]
    skipped=[]
    stored_keys=set(ResourceStore(STORE).index)
    def op(k,r,action,**extra):
        p=physical(k)
        s=p.stat()
        if (s.st_size,s.st_mtime_ns)!=(r['bytes'],r['mtime_ns']):
            if k in retained: raise ValueError('Retained input changed: '+k)
            skipped.append(k);return
        operations.append(dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,action=action,**extra))
    for number,(k,r) in enumerate(old.items()):
        if not physical(k).exists():
            skipped.append(k);continue
        selected=retained.get(k)
        if selected is None:
            op(k,r,'retire')
        elif selected.get('packed'):
            assert k in stored_keys
            op(k,r,'packed')
        elif selected['canonical']!=k:
            op(k,r,'hardlink',canonical=str(physical(selected['canonical'])),sha256=selected['sha256'])
        if number%10000==0: print('Planned audited paths',number,flush=True)
    # New rollback copies share the retained physical 070 payloads, while the
    # designated rollback directory remains independently visible and verified.
    by_hash={(k[0],r['sha256']):k for k,r in retained.items() if not r.get('packed')}
    extra_keep={}
    transient=[EXT/'staging/r71',EXT/'staging/r70/071b-v1',EXT/'output/release_070/integration/garden-071-v1',OUT]
    for folder in transient+[ROLLBACK]:
        for p in walk(folder):
            k='F/'+p.relative_to(EXT).as_posix()
            if k in old or k in retained: continue
            # Keep compact diagnostics and receipts. Inputs/cook/readback scratch
            # from these known attempts is regenerable only after successful proof.
            keep=(folder in (OUT,ROLLBACK) and p.parent==OUT/'delivery') or folder==ROLLBACK
            keep=keep or p.suffix.lower()=='.log' or (p.suffix.lower()=='.json' and p.stat().st_size<1048576)
            s=p.stat()
            if keep:
                digest=sha(p)
                # New receipts and release artifacts have independent identity.
                canonical=None
                if canonical:
                    operations.append(dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,action='hardlink',canonical=str(physical(canonical)),sha256=digest))
                else:
                    extra_keep[k]=dict(bytes=s.st_size,sha256=digest)
                    by_hash[('F',digest)]=k
            else:
                operations.append(dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,action='retire'))
    # Count every currently present non-retired physical file, including unknown
    # concurrent F material. Never rely on an allowance instead of an inventory.
    removed={str(Path(op['path'])).casefold() for op in operations}
    identities=set();remaining=0;unknown=[]
    for drive,root in ROOTS.items():
        for p in walk(root):
            if p==TX/'retirement-plan.json': continue
            if str(p).casefold() in removed: continue
            s=p.stat();identity=(s.st_dev,s.st_ino)
            if identity in identities: continue
            identities.add(identity);remaining+=s.st_size
            k=drive+'/'+p.relative_to(root).as_posix()
            if k not in retained and k not in extra_keep and not k.startswith(('F/resources_071/','F/consolidation_071/')):
                unknown.append(dict(path=k,bytes=s.st_size))
    # Plan/result files and subsequent compact evidence grow during execution.
    projected=remaining+2000000
    dump(TX/'unclassified-retained.json',unknown)
    proof=dict(package=True,rollback=True,native_source=True,asset_cooks=True,resources=True,editable=True,normal_unchanged=True,review=False,
               retained_bytes=projected,all_blends=len([k for k in retained if k.endswith('.blend')]),normal_files=len(json.loads((TX/'normal-before.json').read_text())))
    dump(TX/'retirement-plan.json',dict(roots=[str(ROOT),str(EXT)],operations=operations,skipped_concurrent_files=skipped,
                                     proof=str(TX/'deletion-proof.json'),result=str(TX/'retirement-result.json')))
    # Retain the full operation ledger losslessly compressed after execution;
    # size its real gzip bytes now rather than assuming a small plain JSON file.
    raw_plan=(TX/'retirement-plan.json').read_bytes()
    projected+=len(gzip.compress(raw_plan,compresslevel=6,mtime=0))
    proof['retained_bytes']=projected
    proof['retirement_plan_final_storage']='lossless gzip after successful execution'
    proof['retirement_plan_sha256']=sha(TX/'retirement-plan.json')
    dump(TX/'deletion-proof.json',proof)
    dump(TX/'additional-retained.json',extra_keep)
    print(json.dumps(dict(projected_physical_bytes=projected,operations=len(operations),skipped=len(skipped),proof=proof),indent=2),flush=True)
    assert projected<3000000000, 'Storage budget requires more consolidation before cleanup'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['plan','verify'])
    a=p.parse_args()
    if a.stage=='plan':plan()
    else:checks();print('Retained resources, source, rollback, editable image closure and normal baseline verified')

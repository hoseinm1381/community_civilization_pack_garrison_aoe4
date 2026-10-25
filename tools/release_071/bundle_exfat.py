"""Lossless original-path input store suitable for exFAT (no links required)."""
import gzip
import hashlib
import json
from pathlib import Path
import zipfile
from consolidate import ROOT, EXT, CFG, TX, STORE, physical, key, dump
from resources import ResourceStore, sha


def main():
    rows=json.loads((TX/'retained.json').read_text())
    index=json.loads((STORE/'index.json').read_text())
    name='native-and-diagnostics-v1.zip'
    target=STORE/name
    if target.exists():
        keys=[k for k,r in index['files'].items() if r.get('blob')==name and r.get('codec')=='zip']
        if not keys:raise FileExistsError('Existing unregistered bundle: preserve and inspect before retrying')
        store=ResourceStore(STORE,index['files'])
        for k in keys:store.read(k)
        print('Existing bundle verified; no files rewritten:',len(keys),sha(target),flush=True)
        return
    deps=json.loads(gzip.decompress((TX/'blend-dependencies.json.gz').read_bytes()))
    plain=set()
    for row in deps:
        for img in row['images']:
            if not img['packed'] and img.get('exists') and img.get('resolved'):
                plain.add(key(img['resolved']))
    specs=json.loads((TX/'geometry-specs.json').read_text())
    for item in specs:
        spec=item['inputs']
        for p in Path(spec['template_body']).iterdir():
            if p.is_file():plain.add(key(p))
        plain.add(key(Path(spec['template_project'])/'project/source/_default.burnproj'))
    plain.add('F/output/release_020/native-build.lock')
    for k in rows:
        if k.startswith(('F/archives/release_070_rollback/','F/tool-cache/','F/garrison-library/')):
            plain.add(k)
        if k.startswith('F/output/release_070/art/') and Path(k).suffix=='.json' and rows[k]['bytes']<1048576:
            plain.add(k)
    # Preserve original reviewed operation evidence before the revised plan.
    old_plan=TX/'retirement-plan.json'
    if old_plan.exists() and not (TX/'retirement-v1-exfat-stopped.json.gz').exists():
        raw=old_plan.read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
        assert gzip.decompress(packed)==raw
        (TX/'retirement-v1-exfat-stopped.json.gz').write_bytes(packed)
        old=json.loads(raw)
        completed=sum(not Path(op['path']).exists() for op in old['operations'])
        dump(TX/'exfat-stop.json',dict(filesystem='exFAT',allocation_unit=262144,first_hardlink_failed_before_original_removal=True,
                                      prior_reviewed_plan_sha256=hashlib.sha256(raw).hexdigest(),already_retired_paths=completed,
                                      source_and_rollback_unchanged=True,corrective_action='Lossless indexed ZIP for native inputs and diagnostics; all Blender image paths remain plain.'))
    selected=[k for k,r in rows.items() if k.startswith('F/') and not r.get('packed') and k not in plain]
    temporary=STORE/(name+'.tmp')
    written=set()
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for number,k in enumerate(selected):
            row=rows[k];p=physical(k)
            if row['sha256'] not in written:
                raw=p.read_bytes()
                assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],k
                z.writestr(row['sha256'],raw)
                written.add(row['sha256'])
            index['files'][k]=dict(blob=name,codec='zip',member=row['sha256'],bytes=row['bytes'],sha256=row['sha256'])
            row['packed']=True
            row.pop('canonical',None)
            if number%1000==0:print('Bundled original-path inputs',number,flush=True)
    with zipfile.ZipFile(temporary) as z:assert z.testzip() is None
    temporary.replace(target)
    for k,r in rows.items():
        if not r.get('packed'):r['canonical']=k
    dump(STORE/'index.json',index)
    store=ResourceStore(STORE)
    for k in selected:store.read(k)
    dump(TX/'retained.json',rows)
    dump(TX/'exfat-bundle.json',dict(files=len(selected),unique_members=len(written),zip_bytes=target.stat().st_size,
                                    blob_sha256=sha(target),all_entries_roundtrip_verified=True,plain_image_and_template_paths=len(plain),
                                    no_hardlinks=True))
    print(json.dumps(json.loads((TX/'exfat-bundle.json').read_text()),indent=2),flush=True)


if __name__=='__main__':main()

"""Create an immutable developer snapshot and readable source mirror; never delete."""
import argparse
import collections
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from store import Writer, walk, write_json, check_text, TEXT, file_sha

ROOT=Path(__file__).resolve().parents[2]


def validate_roots(source,external,repository):
    roots=[Path(p).resolve() for p in (source,external,repository)]
    for i,a in enumerate(roots):
        for b in roots[i+1:]:
            if a.is_relative_to(b) or b.is_relative_to(a):raise ValueError('Source, external storage and repository must be separate trees')


def excluded_external(rel):
    parts=rel.parts
    if parts[:1]==('tool-cache',):
        # Installed software/models are machine dependencies, not redistributable mod sources.
        if parts[:2]!=('tool-cache','local-voices-084'): return True
        if len(parts)==3: return Path(parts[-1]).suffix not in TEXT
        if parts[2]=='models': return Path(parts[-1]).name not in ('publisher-manifest.json','verified-downloads.json','README.md','config.json')
        if parts[2]=='VieNeu-TTS': return Path(parts[-1]).suffix not in TEXT and Path(parts[-1]).name not in ('LICENSE','LICENSE.txt')
        return True
    if parts[:2]==('resources_082_animation','runtime'): return True
    return rel.suffix.lower() in ('.pyc','.pyo')


def main():
    p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);args=p.parse_args()
    dest=args.destination.resolve(); cfg=json.loads((ROOT/'workspace.json').read_text())
    ext=Path(cfg['external_root']).resolve()
    validate_roots(ROOT,ext,dest)
    if not (dest/'.git').is_dir() or dest==ext or dest.is_relative_to(ext): raise ValueError('Expected independent existing Git checkout')
    store=dest/'development-data'/'snapshot-084-v1'
    if store.exists(): raise FileExistsError('Snapshot exists; preserve it and use the milestone updater')
    store.mkdir(parents=True)
    writer=Writer(store); summary=collections.defaultdict(lambda:dict(files=0,logical_bytes=0,allocated_bytes=0))
    excluded=collections.defaultdict(lambda:dict(files=0,logical_bytes=0,allocated_bytes=0))
    paths=[]; count=0
    for label,root,cluster in [('source',ROOT,4096),('external',ext,262144)]:
        for path in walk(root):
            rel=path.relative_to(root); size=path.stat().st_size
            if label=='external' and excluded_external(rel):
                group='/'.join(rel.parts[:3]); row=excluded[group];row['files']+=1;row['logical_bytes']+=size;row['allocated_bytes']+=((size+cluster-1)//cluster)*cluster
                continue
            if path.suffix.lower() in ('.pyc','.pyo') or path.name.startswith('.env') or path.suffix in ('.pem','.key'): continue
            data=path.read_bytes(); key=label+'/'+rel.as_posix(); writer.add(key,data)
            group=label+'/'+('/'.join(rel.parts[:2]) if label=='external' else rel.parts[0])
            row=summary[group];row['files']+=1;row['logical_bytes']+=size;row['allocated_bytes']+=((size+cluster-1)//cluster)*cluster
            if label=='source':
                # Editable art and binary exports are losslessly stored, hydrated on demand.
                plain=not rel.parts[:2] in [('art','authoring'),('art','exports')] and rel.parts[0]!='.consolidation_080'
                if plain:
                    target=dest/rel
                    if target.exists() and target.read_bytes()!=data: raise ValueError('Existing contributor file differs: '+str(rel))
                    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                    paths.append(dict(path=rel.as_posix(),sha256=file_sha(target),bytes=size))
            count+=1
            if count%2000==0: print('SNAPSHOT_FILES',count,'PACKS',writer.number,flush=True)
    doc=writer.finish()
    doc['provenance']=dict(created_utc=datetime.now(timezone.utc).isoformat(),source_root=str(ROOT),external_root=str(ext),
        mod_version='0.8.4',normal_edition_included=False,excluded_installed_software=True)
    write_json(store/'index.json.gz',doc)
    write_json(store/'inventory-summary.json',dict(included=dict(summary),excluded_dependencies=dict(excluded),readable_source=paths,
        files=len(doc['files']),chunks=len(doc['chunks']),packs=len(doc['packs']),stored_bytes=sum(v['bytes'] for v in doc['packs'].values())))
    print('SNAPSHOT_COMPLETE',len(doc['files']),sum(v['bytes'] for v in doc['packs'].values()),flush=True)


if __name__=='__main__': main()

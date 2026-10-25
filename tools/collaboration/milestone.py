"""Explicit, append-only milestone export. No deletion, download, commit or push."""
import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path
from prepare_handoff import excluded_external, validate_roots
from store import Writer, load, write_json, walk, file_sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--external',type=Path,required=True)
    p.add_argument('--repository',type=Path,required=True);p.add_argument('--label',required=True)
    args=p.parse_args()
    import re
    if not re.fullmatch('[a-z0-9-]{1,48}',args.label):raise ValueError('Use a short lowercase milestone label')
    repo=args.repository.resolve();source=args.source.resolve();external=args.external.resolve()
    validate_roots(source,external,repo)
    if not (repo/'.git').is_dir() or repo==source or repo.is_relative_to(external):raise ValueError('Expected separate contributor checkout')
    folder=repo/'development-data/snapshot-084-v1';latest=folder/'index.json.gz';previous=load(latest)
    index=folder/('index-'+args.label+'.json.gz')
    if index.exists():raise FileExistsError('Immutable milestone exists')
    # Verify reused physical packs before adding data. Old indexes/packs remain unchanged.
    for name,row in previous['packs'].items():
        if Path(name).name!=name or file_sha(folder/name)!=row['sha256']:raise ValueError('Previous store changed')
    frozen=folder/'index-initial-084-v1.json.gz'
    if not frozen.exists():frozen.write_bytes(latest.read_bytes())
    doc=copy.deepcopy(previous);doc['files']={};writer=Writer(folder,previous=doc)
    count=0;copied=0
    overrides={'README.md','.gitignore','.gitattributes','workspace.json','development.json','AGENTS.md','CONTRIBUTING.md'}
    for label,root in [('source',source),('external',external)]:
        for path in walk(root):
            rel=path.relative_to(root)
            if (label=='external' and excluded_external(rel)) or path.suffix in ('.pyc','.pyo','.pem','.key') or path.name.startswith('.env'):continue
            key=label+'/'+rel.as_posix();data=path.read_bytes();writer.add(key,data);count+=1
            if label=='source' and rel.as_posix() not in overrides and rel.parts[:2] not in [('art','authoring'),('art','exports')] and rel.parts[0]!='.consolidation_080':
                target=repo/rel;old=previous['files'].get(key)
                if target.exists() and target.read_bytes()!=data and (not old or file_sha(target)!=old['sha256']):
                    raise ValueError('Contributor edit needs review: '+str(rel))
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);copied+=1
            if count%2000==0:print('MILESTONE_FILES',count,flush=True)
    doc=writer.finish();doc['provenance']=dict(created_utc=datetime.now(timezone.utc).isoformat(),
        source_root=str(source),external_root=str(external),label=args.label,previous_index_sha256=file_sha(latest),
        path_roots=[{k:previous['provenance'][k] for k in ('source_root','external_root')},*previous['provenance'].get('path_roots',[])],
        normal_edition_included=False,excluded_installed_software=True)
    write_json(index,doc)
    temporary=folder/'index.new.json.gz';temporary.write_bytes(index.read_bytes());temporary.replace(latest)
    print('MILESTONE_EXPORTED',args.label,count,'readable_files',copied)
    print('Run full verification, isolated restoration, release proof and credential checks before commit/push.')


if __name__=='__main__':main()

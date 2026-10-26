"""Write a small current-work Git data delta in the active workspace."""
import copy,hashlib,json,subprocess,sys,zipfile
from pathlib import Path
from current_persia import ROOT,OUT,CFG,VERSION,sha,save
sys.path.insert(0,str(ROOT/'tools/compact'))
import portable
from current_package import apply_verification_delta
from store import Writer,load,write_json

def main():
    git=CFG['git_path']
    config=json.loads(subprocess.check_output([git,'-C',str(ROOT),'show','origin/main:development.json']))
    old_index=ROOT/config['data_index'];old_delta=load(old_index)
    merged=portable.load_index(old_index);r=portable.AliasReader(old_index.parent,merged)
    original=load(old_index.parent/old_delta['base_index'])
    current_index=old_index.parent/'index-current.json.gz'
    previous=portable.load_index(current_index) if current_index.exists() else merged
    writer=Writer(old_index.parent,previous=copy.deepcopy(previous))
    policy=copy.deepcopy(merged['milestone'])
    changed=[]
    def add(key,data):
        if writer.doc['files'].get(key,{}).get('sha256')==hashlib.sha256(data).hexdigest():return
        writer.add(key,data);changed.append(key)
    paths=set(subprocess.check_output([git,'-C',str(ROOT),'ls-files','-z']).decode().split('\0'))-{''}
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'assets').rglob('*') if p.is_file())
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'tests/persia').glob('*.py'))
    paths.update(['tools/current_persia.py','tools/current_mobility.py','tools/current_sync.py','tools/official_archive.py','tools/extension_audit_current.py','tools/verify_current_source.py','docs/CURRENT_WORK.md','docs/PERSIA_GARRISON.md','.github/workflows/current-source.yml'])
    for rel in sorted(paths):
        if rel.startswith('development-data/') or rel in ('workspace.json','development.json') or not (ROOT/rel).is_file():continue
        data=(ROOT/rel).read_bytes();key='source/'+rel
        # Previous reconstruction steps must continue to address their original
        # bytes when a readable source key now acquires newer content.
        for step in policy['steps']:
            for row in step['payloads']:
                if row['key']==key and row['sha256']!=hashlib.sha256(data).hexdigest():
                    previous=r.read(key);assert hashlib.sha256(previous).hexdigest()==row['sha256']
                    keep='external/current/previous-payload/'+row['sha256']+'.bin';add(keep,previous);row['key']=keep
        add(key,data)
    final=load(OUT/'verification.json');delta=load(OUT/'delta.json')
    for step in delta['steps']:
        payloads=[]
        for member,row in step['members'].items():
            path=Path(row['path'])
            key='source/'+path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT/'assets') else 'external/current/payload/'+member
            add(key,path.read_bytes());assert writer.doc['files'][key]['sha256']==row['sha256']
            payloads.append({'member':member,'key':key,'sha256':row['sha256']})
        policy['steps'].append({'alias':step['alias'],'payloads':payloads})
    baseproof=json.loads(r.read(policy['verification']))
    existing=set(baseproof['member_sha256']);assert existing<=set(final['member_sha256'])
    policy['verification_delta']={
        'metadata':{k:v for k,v in final.items() if k not in ('member_sha256','mounts')},
        'member_sha256':{k:v for k,v in final['member_sha256'].items() if k in existing and v!=baseproof['member_sha256'][k]},
        'added_members':{k:{'sha256':v,'mount':final['mounts'][k]} for k,v in final['member_sha256'].items() if k not in existing},
    }
    assert apply_verification_delta(baseproof,policy['verification_delta'])==final
    policy['version']=VERSION
    for name in policy['package_text']:
        key='external/current/metadata/'+name;add(key,(OUT/name).read_bytes());policy['package_text'][name]=key
    with zipfile.ZipFile(OUT/('community_civilization_pack-'+VERSION+'.zip')) as z:
        fields=('filename','date_time','compress_type','create_system','create_version','extract_version','external_attr','internal_attr')
        policy['zip_entries']=[{**{k:getattr(i,k) for k in fields},'extra_hex':i.extra.hex(),'comment_hex':i.comment.hex()} for i in z.infolist()]
    for name in ('import.json','inheritance.json','mobility-proof.json','delta.json'):
        # Input/resource hashes are enough; omit machine-local physical paths.
        if name=='delta.json':continue
        add('external/current/evidence/'+name,(OUT/name).read_bytes())
    doc=writer.finish()
    assert all(doc['packs'][k]==v for k,v in merged['packs'].items())
    current={'schema':doc['schema'],'base_index':old_delta['base_index'],
        'files':{k:v for k,v in doc['files'].items() if original['files'].get(k)!=v},
        'chunks':{k:v for k,v in doc['chunks'].items() if k not in original['chunks']},
        'packs':{k:v for k,v in doc['packs'].items() if k not in original['packs']},'milestone':policy}
    index=old_index.parent/'index-current.json.gz';write_json(index,current)
    fresh=portable.AliasReader(index.parent,portable.load_index(index))
    for key in changed:assert hashlib.sha256(fresh.read(key)).hexdigest()==doc['files'][key]['sha256']
    newpacks={k:v for k,v in doc['packs'].items() if k not in merged['packs']}
    config.update(version=VERSION,baseline_version='0.8.4 compact baseline plus immutable current member deltas',data_index=index.relative_to(ROOT).as_posix(),zip_sha256=final['zip_sha256'],sga_sha256=final['sga_sha256'],entrypoint='tools/current_persia.py',guide='docs/PERSIA_GARRISON.md',package='output/current/community_civilization_pack-'+VERSION+'.zip')
    write_json(ROOT/'development.json',config)
    proof={'version':VERSION,'new_index_bytes':index.stat().st_size,'new_pack_bytes':sum(v['bytes'] for v in newpacks.values()),'new_packs':newpacks,'changed_virtual_files':len(changed),'old_packs_preserved':len(merged['packs']),'full_zip_or_sga_added':False,'source_workspace':str(ROOT),'pushed':False}
    save(OUT/'sync.json',proof);r.close();fresh.close();print(json.dumps(proof,indent=2))

if __name__=='__main__':main()

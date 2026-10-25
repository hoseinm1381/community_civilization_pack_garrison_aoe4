"""Read-only 0.7.3 source/compiled visual graph audit; writes only audit evidence."""
from pathlib import Path
import collections,csv,gzip,hashlib,json,re,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd
OUT=ROOT/'output/asset_audit_073'
BACK=Path(CFG['external_root'])/'staging/r73/v1/readback'
GUID=CFG['project_guid'].replace('-','')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(name,v):(OUT/name).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def norm(v):return str(v).replace('\\','/').lower()
def packed(key):
    store=Path(CFG['external_root'])/'resources_071';entry=json.loads((store/'index.json').read_text())['files'][key]
    if entry['codec']=='gzip':data=gzip.decompress((store/entry['blob']).read_bytes())
    else:
        with zipfile.ZipFile(store/entry['blob']) as z:data=z.read(entry['member'])
    assert hashlib.sha256(data).hexdigest()==entry['sha256']
    return json.loads(data)

registry=packed('F/output/release_060/integration/qualified-media-selection-r1.json')
models={norm(v['private_model']).removesuffix('.rgm'):dict(key=k,kind=v['kind'],stock_model=v.get('stock_model','')) for k,v in registry['models'].items()}
dump('qualified-unit-models.json',models)
proof=json.loads((ROOT/'output/release_073/verification-v1.json').read_text())
assert all(sha(BACK/k)==v for k,v in proof['member_sha256'].items())
local={}; official={}
for p in (BACK/'attrib').rglob('*.rgd'):
    category=p.relative_to(BACK/'attrib').parts[0]
    local[(category,p.stem)]=p
for row in json.loads((OUT/'official-index.json').read_text())['members']:
    parts=row['path'].replace('\\','/').split('/')
    if parts[0]=='attrib':parts=parts[1:]
    if len(parts)>1:official[(parts[0],Path(parts[-1]).stem)]=row['path']
cache={}
def get(key,private=True):
    ck=(private,)+key
    if ck in cache:return cache[ck]
    p=local.get(key) if private else None
    if p is None:
        member=official.get(key)
        if not member:cache[ck]=None;return None
        p=OUT/'official'/key[0]/(key[1]+'.rgd');p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():
            subprocess.run([CFG['archive_tool'],'extract-member',str(Path(CFG['content_editor']).parent/'cardinal/archives/Attrib.sga'),member,str(p)],check=True,capture_output=True)
    t=rgd.read(p.read_bytes());cache[ck]=list(rgd.flatten(t.nodes));return cache[ck]
def refs(nodes,variant='default'):
    out=[]
    for path,n in nodes or []:
        if variant is not None and not path.startswith(variant+'/'):continue
        if n.kind not in ('List','List2'):continue
        fields={v.key:v.value for v in n.children if v.kind not in ('List','List2')}
        if fields.get('$PBGNAME') and fields.get('$PBGMAP'):
            name=str(fields['$PBGNAME']);cat=str(fields['$PBGMAP']).split('\\')[0]
            private=name.startswith(GUID+':')
            out.append(dict(path=path,category=cat,name=name.split(':')[-1],private=private))
    return out
def art(nodes,variant='default'):
    return sorted(set(norm(n.value) for p,n in nodes or [] if (variant is None or p.startswith(variant+'/')) and n.kind=='CString' and norm(n.value).startswith('art/')))
stampcache={}
def resolve_art(path):
    if path in stampcache:return stampcache[path]
    if (BACK/(path+'.rgm')).exists():result=[path]
    elif (BACK/(path+'.bin')).exists():
        values={norm(s.decode('ascii')) for s in re.findall(rb'[\x20-\x7e]{8,}',(BACK/(path+'.bin')).read_bytes()) if s.lower().startswith(b'art')}
        result=sorted(v for v in values if (BACK/(v+'.rgm')).exists())
    else:result=[]
    stampcache[path]=result;return result
def visual(key,private=True,variant='default',seen=None):
    seen=set() if seen is None else seen;ident=(private,)+key
    if ident in seen:return dict(attachments=[],custom_models=[],stock_paths=[])
    seen.add(ident);nodes=get(key,private);paths=art(nodes,variant) if key[0]=='attachments' else [norm(n.value) for p,n in nodes or [] if (variant is None or p.startswith(variant+'/')) and p.endswith('/alternate_sua') and n.value]
    attachments=[]
    for ref in refs(nodes,variant):
        if ref['category']!='attachments':continue
        if key[0]!='attachments' and not any(v in ref['path'] for v in ('entity_blueprint_ext/animator_attachments','/tier_ext/')):continue
        attachments.append(ref)
        # Private lists contain their own resolved native inherited fields.
        child=visual(('attachments',ref['name']),ref['private'],variant,seen)
        paths.extend(child['custom_models']);paths.extend(child['stock_paths'])
    custom=set();stock=set()
    for path in paths:
        resolved=resolve_art(path)
        if resolved:custom.update(resolved)
        else:stock.add(path)
    return dict(attachments=attachments,custom_models=sorted(custom),stock_paths=sorted(stock))
labels={row['ID']:row['Text'] for row in csv.DictReader((ROOT/'assets/locdb/community_civilization_pack_en.csv').open(encoding='utf-8-sig',newline=''))}
def label(nodes):
    v=next((str(n.value) for p,n in nodes or [] if p.startswith('default/') and p.endswith('/screen_name')),'')
    return labels.get(v.split(':')[-1],v)
rows=[];edges=[]
for key,p in local.items():
    nodes=get(key)
    for ref in refs(nodes):
        # Requirements/parents are not proof that something can be produced.
        if any(s in ref['path'] for s in ('construction_items/','spawn_items/','unit_list/','upgrade_target','upgrade_to','/upgrades/','standard_upgrades/','/abilities/','/actions/','/action_list/','spawn_entity','spawn_squad')):
            edges.append(dict(source_category=key[0],source=key[1],**ref))
    if key[0]!='ebps':continue
    if any(v in key[1] for v in ('vn_wpn_','vn_projectile_')):continue
    v=visual(key)
    info=[]
    for m in v['custom_models']:
        info.append(dict(path=m,**models.get(m,dict(key='building-or-trap',kind='building_geometry_or_stamp_compound'))))
    equipment=[]
    for ref in refs(nodes):
        if ref['category']=='attachments' and '/combat_ext/' in ref['path']:
            ev=visual(('attachments',ref['name']),ref['private'])
            equipment.append(dict(**ref,custom_models=ev['custom_models'],stock_paths=ev['stock_paths']))
    variants={branch:visual(key,variant=branch)['custom_models'] for branch in sorted({p.split('/')[0] for p,n in nodes})}
    source=next((p.relative_to(ROOT).as_posix() for p in (ROOT/'assets/attrib/instances/ebps').rglob(key[1]+'.xml')),'')
    rows.append(dict(name=key[1],label=label(nodes),source=source,member=p.relative_to(BACK).as_posix(),body_models=info,variants=variants,equipment=equipment,**v))
dump('actors.json',rows);dump('production-edges.json',edges)
# Every squad loadout is recorded, including private aliases and tower wrappers.
squads=[]
for key,p in local.items():
    if key[0]=='sbps':squads.append(dict(name=key[1],label=label(get(key)),loadout=[v for v in refs(get(key)) if '/squad_loadout_ext/unit_list/' in v['path']]))
dump('squads.json',squads)
# Resolve inherited official loadouts selected by current private production.
inherited=[]
for key in sorted({(x['category'],x['name']) for x in edges if not x['private'] and x['category'] in ('ebps','sbps')}):
    nodes=get(key,False)
    inherited.append(dict(category=key[0],name=key[1],label=label(nodes),loadout=[v for v in refs(nodes) if '/squad_loadout_ext/unit_list/' in v['path']],visual=visual(key,False) if key[0]=='ebps' else None))
dump('inherited-production.json',inherited)
selected={m['path'] for row in rows for m in row['body_models']}
selected.update(m for row in rows for e in row['equipment'] for m in e['custom_models'])
dump('unit-model-selection.json',[dict(path=p,**v,selected_in_local_actor_graph=p in selected) for p,v in models.items()])
dump('audit-inputs.json',dict(version=CFG['version'],sga_sha256=proof['sga_sha256'],verified_packaged_members=len(proof['member_sha256']),source_assets={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()},local_rgd_count=len(local),actor_count=len(rows),unit_model_registry=len(models)))
print(json.dumps(dict(actors=len(rows),squads=len(squads),production_edges=len(edges),registry_models=len(models),official_records_read=sum(not k[0] for k in cache))))

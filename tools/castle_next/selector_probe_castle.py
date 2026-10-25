"""Probe exact stock Castle landmark stamp/RGO/RGM selector closures.

The probe is read-only against game archives/index and writes only under
output/castle_next/inventory and output/castle_next/budget.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, sqlite3, struct, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
from common import ROOT, OUT, CORE, CFG, guarded, sha, write

ARCH=Path(CFG['archive_tool'])
ATTRIB=Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga')
DATA=Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Data.sga')
INDEX=Path(r'C:\Users\RS\AppData\Local\Garrison\Kit\game-assets.sqlite3')
CONFIG=Path(r'C:\Users\RS\AppData\Local\Garrison\Kit\game-assets.local.json')
EXT=Path(CFG['garrison_extension'])
sys.path.insert(0,str(ROOT/'tools/release_010'))
import integration_native as _native
_native.WORK=OUT/'inventory/schema'
NativeTree=_native.NativeTree
sys.path.insert(0,str(EXT))
from garrison_shared import relic_chunky as rc

def cli(argv):
    p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if p.returncode: raise RuntimeError(f'Failed {argv}: {p.stdout[-1000:]} {p.stderr[-1000:]}')
    return p.stdout
def extract(archive,member,target):
    target=Path(target); target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists(): cli([ARCH,'extract-member',archive,member,target])
    return target
def rgd_xml(member, cache, member_names):
    target=Path(cache)/(member.replace('/','__'))
    binary=target.with_suffix('.rgd'); xml=target.with_suffix('.xml')
    if member.lower() not in member_names: raise FileNotFoundError(f'No exact Attrib owner: {member}')
    extract(ATTRIB,member,binary)
    if not xml.exists(): cli([ARCH,'decode-rgd',binary,xml])
    return binary,ET.parse(xml).getroot()
def resolve_attachment(ref,race,member_names):
    leaf=ref.rsplit('/',1)[-1].lower()+'.rgd'
    candidates=sorted(x for x in member_names if x.startswith('attrib/attachments/attachment_lists/') and x.endswith('/'+leaf))
    if len(candidates)==1: return candidates[0]
    race_folder={'delhi':'sultanate','mongols':'mongol'}.get(race,race)
    preferred=[x for x in candidates if f'/civilizations/{race_folder}/' in x or f'/races/{race_folder}/' in x]
    if len(preferred)==1: return preferred[0]
    # Generic race-core lists are official fallbacks where the owning actor names
    # only a PBG and the native PBG map is not embedded in this serializer output.
    core=[x for x in candidates if '/races/core/' in x]
    if len(core)==1: return core[0]
    raise FileNotFoundError(f'Attachment owner {ref} has {len(candidates)} eligible exact Attrib members; candidates={candidates}')
def refs_for_branch(root,variant):
    branches=[n for n in root.findall(f"RGDNode[@Key='{variant}']")]
    if not branches: return []
    refs=[]
    for branch in branches:
        for n in branch.iter('RGDNode'):
            if n.get('Key')!='attachments': continue
            vals={c.get('Key'):c.get('Value') for c in n.findall('RGDNode')}
            name=vals.get('$PBGNAME'); pbgmap=vals.get('$PBGMAP')
            if name and pbgmap:
                ref=pbgmap.replace('\\','/')+'/'+name
                if 'attachment_lists' in ref.lower(): refs.append(ref)
    return sorted(set(refs))
def stamp_members(root,variant):
    # Attachment lists commonly define separate default/campaign/xp3 graphs.
    # Never union them: campaign scaffolds and alternate tiers are not visible
    # simultaneously with the ordinary completed landmark.
    branch=root.find(f"RGDNode[@Key='{variant}']")
    if branch is None: return []
    return sorted({(n.get('Value') or '').replace('\\','/').lower().removesuffix('.bin')+'.bin'
                   for n in branch.iter('RGDNode') if n.get('Key')=='stamp' and n.get('Value')})
def native_stamp_models(path):
    tree=NativeTree(path)
    roots=[o for o in tree.objects.values() if o['type']=='StampBlueprint' and not o['owner']]
    if not roots: return []
    root=roots[0]; arr=tree.field(root,root['fields']['m_blueprints']); out=[]
    for i in range(arr['count']):
        slot=arr['data_address']+8*i
        obj=tree.by_offset.get(slot+struct.unpack('<q',tree.bytes(slot,8))[0])
        if obj and obj['type']=='VisualStampBlueprint':
            model=tree.field(obj,obj['fields']['m_blueprint']).get('text')
            if model: out.append(model.replace('\\','/').lower().removesuffix('.rgm')+'.rgm')
    return out
def index_row(logical):
    with sqlite3.connect('file:'+INDEX.as_posix()+'?mode=ro',uri=True) as db:
        rows=db.execute('select logical_path,archive_path from resolved_assets where lower(logical_path)=?',(logical.lower(),)).fetchall()
    if len(rows)!=1: raise FileNotFoundError(f'Index match count {len(rows)} for {logical}')
    return rows[0]
def decoded_model(logical, cache):
    out=OUT/'inventory'/'model-decode'
    key=hashlib.sha256(logical.encode('utf-8')).hexdigest()[:16]
    output=out/key
    manifests=sorted(output.rglob('decoded-static.json'),key=lambda p:p.stat().st_mtime_ns) if output.exists() else []
    if manifests:
        manifest=manifests[-1]; d=json.loads(manifest.read_text(encoding='utf-8'))
        if d.get('request',{}).get('logical_path','').lower()!=logical.lower(): raise RuntimeError(f'Cached decode identity mismatch: {logical}')
    else:
        cmd=[CORE,'convert','decode-static','--logical-path',logical,'--config',CONFIG,'--index',INDEX,'--output-root',output]
        reply=json.loads(cli(cmd)); manifest=Path(reply['manifest_path']); d=json.loads(manifest.read_text(encoding='utf-8'))
    # Rig projection is animation-only. decode-static has already preserved the
    # complete native draw groups and rest-pose triangles; report this separately
    # and do not treat rest-pose as a newly authored/animated runtime result.
    geometry=d.get('geometry') or {}
    blockers=d.get('blockers') or []
    static_only=[b for b in blockers if b.get('id')=='rig_projection']
    hard=[b for b in blockers if b.get('id')!='rig_projection']
    if d.get('status') not in ('decoded','decoded_with_blockers') or not geometry.get('groups') or hard:
        raise RuntimeError(f'Incomplete static model decode {logical}: {blockers}')
    d['_static_decode_notes']=static_only
    actual=d['provider_contract']['model']['logical_path']; _,archive=index_row(actual)
    rgm=extract(archive,actual,Path(cache)/(key+'.rgm'))
    return manifest,d,rgm

def selectors(model_path,decoded):
    chunks=list(rc.walk(rc.load(model_path).roots))
    def read_lp(data,at):
        return rc.read_lp_string(data,at)
    sets=[]; conditions=[]; unknown_conditions=[]
    for ch in chunks:
        if ch.tag==b'MSD ' and len(ch.payload)>4:
            name,at=read_lp(ch.payload,0); count=struct.unpack_from('<I',ch.payload,at)[0]; at+=4
            vals=[]
            for _ in range(count): v,at=read_lp(ch.payload,at); vals.append(v)
            if at!=len(ch.payload): raise ValueError('MSD trailing bytes')
            sets.append({'name':name,'members':vals})
        elif ch.tag==b'CNBP':
            payload=ch.payload; n=struct.unpack_from('<I',payload)[0]; at=4; rows=[]; unknown=[]
            for _ in range(n):
                op,flag,one=struct.unpack_from('<IBI',payload,at); at+=9
                prop,at=read_lp(payload,at)
                if prop in ('life_cycle_state','has_collapsed_ruins','preview'):
                    val,at=read_lp(payload,at)
                    rows.append({'op':op,'flag':flag,'one':one,'property':prop,'value':val,
                                 'proven_lifecycle':prop=='life_cycle_state'})
                else:
                    # Numeric/other typed conditions are retained as unresolved
                    # because their engine comparison semantics are not derived
                    # from a string-only reader. They must never become an
                    # implicit zero or an unconditional draw.
                    unknown.append({'op':op,'flag':flag,'one':one,'property':prop,
                                    'remaining_payload_hex':payload[at:].hex()})
                    break
            if not unknown and at!=len(payload): unknown.append({'reason':'CNBP trailing typed bytes','remaining_payload_hex':payload[at:].hex()})
            conditions.append(rows); unknown_conditions.append(unknown)
    if len(sets) not in (len(conditions),len(conditions)+1): raise ValueError('Selector set/state predicate count mismatch')
    lower=set(); upper=set(); proven_excluded=set(); allnames=set(); details=[]
    for i,s in enumerate(sets):
        allnames.update(s['members']); cond=conditions[i] if i<len(conditions) else []
        unknown=unknown_conditions[i] if i<len(unknown_conditions) else []
        if not cond and not unknown:
            state='unconditional'; lower.update(s['members']); upper.update(s['members'])
        elif unknown:
            state='unknown'; upper.update(s['members'])
        elif all(c['property']=='life_cycle_state' and c['op']==2 and c['flag']==0 and c['one']==1 for c in cond):
            if any(c['value']=='healthy' for c in cond):
                state='proven_healthy'; lower.update(s['members']); upper.update(s['members'])
            else:
                state='proven_nonhealthy_lifecycle'; proven_excluded.update(s['members'])
        elif any(c['property']!='life_cycle_state' for c in cond):
            state='unknown'; upper.update(s['members'])
        else:
            state='unknown'; upper.update(s['members'])
        details.append({'set':s['name'],'members':s['members'],'classification':state,
                        'predicates':cond,'unknown_predicates':unknown})
    geom=decoded['geometry']; groups=geom['groups']; contract=decoded.get('structure_collection_contract')
    if contract is None:
        group_names={g['name'] for g in groups}
        if not sets and not conditions:
            low=high=sum(g['triangle_count'] for g in groups)
            method='no native selector/predicate chunks; all decoded groups unconditional'
        elif group_names == allnames:
            low=sum(g['triangle_count'] for g in groups if g['name'] in lower)
            high=sum(g['triangle_count'] for g in groups if g['name'] in upper)
            method='exact named RGM draw instances/CNBP healthy union'
        elif len(groups)==1 and allnames:
            # For a single decoded model draw group whose native selectors name
            # subparts the static decoder merged, exact per-selector triangles
            # are unavailable. Bound the entire model once: lower is full only
            # if every possible selector is guaranteed healthy; upper is full
            # if any selector can be healthy or has unresolved visibility.
            raw=groups[0]['triangle_count']
            low=raw if allnames<=lower else 0
            high=raw if (allnames & upper) else 0
            method='single decoded mesh coarse native-selector bound (one model raw upper)'
        elif not allnames and not conditions:
            low=high=sum(g['triangle_count'] for g in groups)
            method='no selector names/predicates; all decoded groups unconditional'
        else:
            raise ValueError(f'RGM selectors do not map exactly to decoded groups (sets={len(allnames)} groups={len(groups)} names={sorted(allnames)[:4]} group_names={sorted(group_names)[:4]})')
        return {'raw':sum(g['triangle_count'] for g in groups),'lower':low,'upper':high,'selector_count':len(allnames),'healthy_selector_count':len(lower),'unknown_selector_count':len(upper-lower),'proven_nonhealthy_selector_count':len(proven_excluded),'selector_sets':details,'method':method}
    mscl=next((c for c in chunks if c.tag==b'MSCL'),None)
    if not mscl or len(mscl.children)!=1 or mscl.children[0].tag!=b'DATA': raise ValueError('Missing native MSCL source-object map')
    payload=mscl.children[0].payload; source_count=struct.unpack_from('<H',payload)[0]
    offsets={n:payload.find(rc.lp_string(n)) for n in allnames}
    if source_count!=len(allnames) or any(o<2 for o in offsets.values()) or len(set(offsets.values()))!=source_count:
        raise ValueError('Native MSCL source order does not match selectors')
    ordered=sorted(allnames,key=offsets.get); total_raw=total_lower=total_upper=0; index=0
    for mapping,span in zip(contract['maps'],contract['geometry_group_spans']):
        if mapping['source_object_count']!=source_count or mapping['geometry_group_span']!=span: raise ValueError('MSCL geometry span mismatch')
        inverse={bone:ordered[i] for i,bone in enumerate(mapping['source_to_local_bone']) if bone>=0}
        for group in groups[index:index+span]:
            used={v for v in group['collection_bone_indices'] if v>=0}
            # Most static draw groups are a single native source object. Count
            # their exact decoded LOD0 triangles in O(1); retain per-triangle
            # verification for mixed-object groups.
            if len(used)==1 and -1 not in group['collection_bone_indices'] and all(v in inverse for v in used):
                source=next(iter(used)); n=group['triangle_count']; name=inverse[source]
                total_raw+=n; total_lower+=n*(name in lower); total_upper+=n*(name in upper)
                continue
            for tri in group['triangles']:
                a,b,c=(group['collection_bone_indices'][k] for k in tri)
                if a!=b or b!=c or a not in inverse: raise ValueError('Triangle does not map to a single native source object')
                total_raw+=1; total_lower+=inverse[a] in lower; total_upper+=inverse[a] in upper
        index+=span
    if index!=len(groups): raise ValueError('Decoded group span sum mismatch')
    return {'raw':total_raw,'lower':total_lower,'upper':total_upper,'selector_count':len(allnames),'healthy_selector_count':len(lower),'unknown_selector_count':len(upper-lower),'proven_nonhealthy_selector_count':len(proven_excluded),'selector_sets':details,'method':'MSCL source-object map + RGM triangles + bounded selector-state union'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--verify-only',action='store_true'); args=ap.parse_args(); guarded()
    choices_path=OUT/'inventory'/'castle-age-choices.json'; choices=json.loads(choices_path.read_text(encoding='utf-8'))
    if choices.get('status')!='qualified' or choices.get('choice_count')!=14: raise RuntimeError('Native 14-choice actor selection is not qualified')
    listing=json.loads(cli([ARCH,'list',ATTRIB])); member_names={r['path'].lower() for r in listing['members']}
    schema_dir=_native.WORK; schema_dir.mkdir(parents=True,exist_ok=True); reflect=schema_dir/'reflect.db'
    if not reflect.exists(): extract(Path(r'E:\Games\steamapps\common\Age of Empires IV\engine\archives\reflect.sga'),'reflect.db',reflect)
    rows=[]; all_models={}; blockers=[]; selector_cache_path=OUT/'inventory'/'native-selector-cache.json'; selector_cache={}
    if selector_cache_path.exists():
        cached=json.loads(selector_cache_path.read_text(encoding='utf-8'))
        if cached.get('schema')=='community-civilization-pack/castle-next-selector-cache/v5': selector_cache=cached.get('models',{})
    for actor in choices['choices']:
        race=actor['race']; actor_member=actor['member']; actor_xml=ET.parse(actor['decoded_xml']).getroot(); entries=[]; actor_lower=actor_upper=0
        lists=refs_for_branch(actor_xml,'default')
        if not lists: blockers.append({'actor':actor_member,'variant':'default','error':'missing default attachment list'})
        for ref in lists:
            m=resolve_attachment(ref,race,member_names); list_lower=list_upper=0; list_blocked=False
            try:
                binary,root=rgd_xml(m,OUT/'inventory'/'closure'/'attrib',member_names); stamp_rows=[]
                for stamp in stamp_members(root,'default'):
                    stamp_path=extract(DATA,stamp,OUT/'inventory'/'closure'/'stamps'/Path(stamp).name); visual=[]; non_rrgeom=[]; stamp_lower=stamp_upper=0
                    for model in native_stamp_models(stamp_path):
                        if model in all_models: entry=all_models[model]
                        elif model in selector_cache: entry=selector_cache[model]; all_models[model]=entry
                        else:
                            try:
                                _,archive=index_row(model); manifest,d,rgm=decoded_model(model,OUT/'inventory'/'closure'/'models')
                            except Exception as model_error:
                                message=str(model_error)
                                if 'no same-stem RRGeometry provider' in message:
                                    non_rrgeom.append({'model':model,'classification':'native_non_rrgeometry_reference','reason':message}); continue
                                raise
                            met=selectors(rgm,d)
                            entry={'model':model,'archive':archive,'rgm':str(rgm),'rgm_sha256':sha(rgm),'decoded_manifest':str(manifest),
                                   'decoded_manifest_sha256':sha(manifest),'rrgeom_sha256':d['geometry']['source']['sha256'],'selectors':met,
                                   'static_decode_notes':d.get('_static_decode_notes',[])}
                            all_models[model]=entry; selector_cache[model]=entry
                            write(selector_cache_path,{'schema':'community-civilization-pack/castle-next-selector-cache/v5','models':selector_cache})
                        met=entry['selectors']; stamp_lower+=met['lower']; stamp_upper+=met['upper']
                        visual.append({'model':model,'lower_triangles':met['lower'],'upper_triangles':met['upper'],'raw_triangles':met['raw'],
                                       'unknown_selector_count':met['unknown_selector_count'],'rgm_sha256':entry['rgm_sha256'],'decoded_manifest':entry['decoded_manifest']})
                    stamp_rows.append({'member':stamp,'sha256':sha(stamp_path),'lower_triangles':stamp_lower,'upper_triangles':stamp_upper,'models':visual,'non_rrgeom_references':non_rrgeom})
                    list_lower+=stamp_lower; list_upper+=stamp_upper
            except Exception as e:
                list_blocked=True; blockers.append({'actor':actor_member,'variant':'default','list':ref,'error':str(e)})
                stamp_rows=[]
            entries.append({'member':m,'sha256':sha(binary) if not list_blocked else None,'stamps':stamp_rows,
                            'lower_healthy_triangles':None if list_blocked else list_lower,'upper_healthy_triangles':None if list_blocked else list_upper,
                            'status':'blocked' if list_blocked else 'bounded'})
            if not list_blocked: actor_lower+=list_lower; actor_upper+=list_upper
        blocked=any(b['actor']==actor_member and b['variant']=='default' for b in blockers)
        rows.append({'race':race,'actor':actor_member,'actor_sha256':actor['actor_sha256'],'castle_requirement':actor['castle_requirement_evidence'],
                     'default':{'status':'blocked' if blocked else 'bounded','lower':None if blocked else actor_lower,'upper':None if blocked else actor_upper,'attachment_lists':entries},
                     'campaign':'separate consumer inventory; excluded from ordinary default budget','native_runtime':'unverified'})
    lower_counts=sorted(r['default']['lower'] for r in rows if r['default']['lower'] is not None)
    upper_counts=sorted(r['default']['upper'] for r in rows if r['default']['upper'] is not None)
    complete=len(rows)==14 and len(lower_counts)==14 and len(upper_counts)==14 and not blockers
    mean_lower=sum(lower_counts)/len(lower_counts) if lower_counts else None; mean_upper=sum(upper_counts)/len(upper_counts) if upper_counts else None
    target_min=.9*mean_upper if complete else None; cap=max(lower_counts) if complete else None
    target_max=min(1.1*mean_lower,cap) if complete else None
    target=(target_min+target_max)/2 if complete and target_min<=target_max else None; qualified=target is not None
    report={'schema':'community-civilization-pack/castle-next-stock-landmark-budget/v1',
      'status':'qualified_conservative_drawgraph_bounds' if qualified else ('blocked_empty_robust_budget_interval' if complete else 'blocked_incomplete_native_mapping'),
      'sources':{'attrib_sga':str(ATTRIB),'attrib_sha256':sha(ATTRIB),'data_sga':str(DATA),'data_sha256':sha(DATA),'asset_index':str(INDEX),'asset_index_sha256':sha(INDEX),'asset_index_mode':'SQLite read-only','garrison_core':str(CORE),'garrison_config':str(CONFIG),'config_sha256':sha(CONFIG),'reflect_schema':str(reflect),'reflect_sha256':sha(reflect),'choice_evidence':str(choices_path),'choice_evidence_sha256':sha(choices_path)},
      'selection_rule':choices['selection_rule'],'metric':'Complete ordinary default/skirmish Castle actor graph. Each native stamp model instance and decoded static LOD0 RRGeom draw is counted; unknown selector visibility is bounded [0, exact mapped raw triangles], pure healthy/unconditional selectors are guaranteed lower, and proven nonhealthy lifecycle selectors contribute zero.',
      'budget':{'measured_choices':len(lower_counts),'expected_choices':14,'choice_lower_counts':lower_counts,'choice_upper_counts':upper_counts,'mean_lower':mean_lower,'mean_upper':mean_upper,
                'guaranteed_target_min':target_min,'guaranteed_target_max':target_max,'maximum_guaranteed_cap':cap,'target_triangles':target,
                'exact_mean':mean_lower if complete and lower_counts==upper_counts else None,
                'proof':'Every target in the robust interval is within ±10% of the true mean for every per-choice count inside these proven bounds; cap does not exceed a proven sample maximum.' if qualified else None},
      'choices':rows,'model_closure':list(all_models.values()),'blockers':blockers,
      'limits':['Campaign/alternate actor graphs are inventoried separately and are excluded from this normal/skirmish reference target.','Static source bounds do not prove runtime visibility, GPU submissions, import, or native-match behavior.','No Blender, native cook, Content Editor build, import or match run was performed.']}
    dest=OUT/'budget'/'castle-stock-landmark-budget.json'; write(dest,report)
    if qualified:
        alias={'schema':'community-civilization-pack/castle-next-landmark-triangle-budget/v1','proof_status':report['status'],'mean_target_triangles':target,'maximum':cap,
               'guaranteed_target_interval':[target_min,target_max],'mean_lower':mean_lower,'mean_upper':mean_upper,'exact_mean':report['budget']['exact_mean'],
               'source_report':str(dest),'source_report_sha256':sha(dest),'criterion':'14 actual Castle-age actors, ordinary default/skirmish complete healthy drawgraph with props and conservative visibility bounds.'}
        write(OUT/'inventory'/'castle-landmark-triangle-budget.json',alias)
    print(json.dumps({'status':report['status'],'report':str(dest),'measured_choices':len(lower_counts),'expected_choices':14,'lower_counts':lower_counts,'upper_counts':upper_counts,
                      'mean_bounds':[mean_lower,mean_upper],'guaranteed_target_interval':[target_min,target_max],'target':target,'max_cap':cap,'blocker_count':len(blockers),'blockers':blockers[:8]},indent=2))
    return 0 if qualified else 2
if __name__=='__main__': raise SystemExit(main())

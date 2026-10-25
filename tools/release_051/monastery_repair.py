"""0.5.1 monastery-only native visual repair, with exact 0.5.0 provenance.

The 0.5.0 model removed roof sources from every native selector while leaving
their MSCL and geometry. Restore the stock selector graph, then compact only
the superseded intact roof/overlap index triangles in the private RRGeom. This
retains native vertex/UV/collection layouts, debris triangles and RGO markers.
The detail stamp receives the exact base visual's transform.
"""
from __future__ import annotations
import collections, json, os, shutil, struct, sys
from pathlib import Path
from common import ROOT, OUT, PRIOR, ART, EXPORT, RECIPES, guarded, read, sha, write
sys.path.insert(0,str(ROOT/'tools/castle_next'))
from building_selectors import rc, source_map, parse_set, parse_state, native_path
sys.path.insert(0,str(ROOT/'tools/release_010'))
from integration_native import NativeTree

MON=OUT/'monastery'
PAYLOAD=MON/'payload'
MEDIA=ROOT/'output/castle_next/integration/building-media.json'
BINDINGS=PRIOR/'integration/private-bindings.json'

def payload_record(member,data):
    target=PAYLOAD/member
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    return {'member':member,'file':str(target),'sha256':sha(target),'bytes':len(data)}

def artifact_sources():
    media=read(MEDIA)
    rows={r['member']:r for r in media['payloads']}
    assert media['status']=='passed'
    return rows

def copy_authoring(age):
    src=ROOT/f'art/authoring/castle_next/buildings/monastery/age{age:02}'
    dst=ART/f'monastery/age{age:02}'
    dst.mkdir(parents=True,exist_ok=True)
    files={'body':(src/f'Vietnam_monastery_Age{age:02}.blend',dst/'body-050-reference.blend'),
           'detail':(src/'details'/f'vn_monastery_details_age{age:02}.blend',dst/'detail-050-reference.blend')}
    report={}
    for key,(source,target) in files.items():
        if not target.exists():shutil.copy2(source,target)
        assert sha(source)==sha(target)
        report[key]={'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size,
                     'provenance':str(source),'role':'unmodified geometry reference; 051 native edits recorded in recipe'}
    exsrc=ROOT/f'art/exports/castle_next/buildings/monastery/age{age:02}/details'
    exdst=EXPORT/f'monastery/age{age:02}/details'
    if not exdst.exists():shutil.copytree(exsrc,exdst)
    assert {p.name:sha(p) for p in exsrc.iterdir() if p.is_file()}=={
        p.name:sha(p) for p in exdst.iterdir() if p.is_file()}
    report['detail_exports']={p.name:{'sha256':sha(p),'bytes':p.stat().st_size}
                              for p in exdst.iterdir() if p.is_file()}
    return report

def repair_rgm(age,source_rows,donor,names):
    member=f'art/scenario/cccastle/monastery_age{age:02}/model.rgm'
    prior=Path(source_rows[member]['file']);assert sha(prior)==source_rows[member]['sha256']
    source=native_path(donor['decoded_static']['resources']['model']['cache_path'])
    assert sha(source)==donor['decoded_static']['resources']['model']['sha256']
    source_chunks=list(rc.walk(rc.load(source).roots))
    prior_doc=rc.load(prior); prior_chunks=list(rc.walk(prior_doc.roots))
    old=[c for c in source_chunks if c.tag==b'MSD ' and len(c.payload)>4]
    new=[c for c in prior_chunks if c.tag==b'MSD ' and len(c.payload)>4]
    assert len(old)==len(new)
    changes={}
    for a,b in zip(old,new):
        oa,ob=parse_set(a.payload),parse_set(b.payload)
        assert oa['name']==ob['name']
        if a.payload!=b.payload:changes[b.offset]=a.payload
    assert changes
    data=rc.rebuild(prior_doc,lambda c:changes.get(c.offset))
    after=[c for c in rc.walk(rc.parse(data).roots) if c.tag==b'MSD ' and len(c.payload)>4]
    assert [c.payload for c in after]==[c.payload for c in old]
    assert [c.payload for c in rc.walk(rc.parse(data).roots) if c.tag==b'CNBP']==[c.payload for c in prior_chunks if c.tag==b'CNBP']
    selected={name for c in after for name in parse_set(c.payload)['members']}
    expected=set(source_map(donor)[1]['all_selector_names'])
    assert selected==expected
    export=EXPORT/f'monastery/age{age:02}/model.rgm';export.parent.mkdir(parents=True,exist_ok=True);export.write_bytes(data)
    row=payload_record(member,data)
    return row,{'restored_selector_sets':len(changes),'all_mscl_names_qualified':selected==expected,
                'selector_name_count':len(selected),'native_conditions_byte_identical_to_050':True,
                'all_other_050_chunks_byte_identical':all(a.payload==b.payload for a,b in zip(prior_chunks,list(rc.walk(rc.parse(data).roots))) if a.offset not in changes and not a.children),
                'original_sha256':sha(prior),'repaired_sha256':sha(export),'export':str(export)}

def suppress(age,group,source_name,triangle):
    if 'disappear' not in source_name or 'debris' in source_name:
        return False
    material=group['preview_material']
    if material=='roof':return True
    if material!='extra':return False
    points=[group['positions'][i] for i in triangle]
    eave=3.24 if age==3 else 4.32
    # Only elevated stock roof/trim faces; wall, supporting body and debris stay.
    if min(p[2] for p in points)<eave-.10:return False
    if max(p[2] for p in points)<eave+.05:return False
    return all(abs(p[0])<=4.8 and -1.45<=p[1]<=6.05 for p in points)

def repair_rrgeom(age,source_rows,donor,names):
    member=f'art/scenario/cccastle/monastery_age{age:02}/model.rrgeom'
    prior=Path(source_rows[member]['file']);assert sha(prior)==source_rows[member]['sha256']
    doc=rc.load(prior)
    geobs=[c for c in rc.walk(doc.roots) if c.tag==b'GEOB']
    groups=donor['decoded_static']['geometry']['groups']
    assert len(geobs)==2*len(groups)
    changes={};reports=[];retained_ordinals=[]
    for gi,(group,group_names) in enumerate(zip(groups,names)):
        vertex,index=geobs[2*gi:2*gi+2]
        vc,_,vs,_=struct.unpack_from('<4I',vertex.payload)
        ic,_,isz,_=struct.unpack_from('<4I',index.payload)
        assert vs==24 and isz==2 and vc==len(group['positions']) and ic==3*len(group['triangles'])
        assert len(group_names)==len(group['triangles'])
        kept=bytearray();removed=[];ordinals=[];original_degenerate=0
        for ti,(triangle,name) in enumerate(zip(group['triangles'],group_names)):
            at=16+6*ti
            indices=struct.unpack_from('<3H',index.payload,at)
            assert sorted(indices)==sorted(triangle),(age,gi,ti,indices,triangle)
            original_degenerate+=len(set(indices))<3
            if suppress(age,group,name,triangle):
                removed.append((ti,name))
            else:
                kept.extend(index.payload[at:at+6]);ordinals.append(ti)
        header=bytearray(index.payload[:16]);struct.pack_into('<I',header,0,3*len(ordinals))
        data=bytes(header)+bytes(kept)
        assert len(data)==16+6*len(ordinals)
        assert struct.unpack_from('<4I',data)==(3*len(ordinals),0,2,0)
        assert all(len(set(struct.unpack_from('<3H',data,16+6*i)))==3 for i in range(len(ordinals)))
        if removed:changes[index.offset]=data
        retained_ordinals.append(ordinals)
        byname=collections.Counter(name for _,name in removed)
        reports.append({'group':gi,'material':group['preview_material'],'triangles_before':len(group['triangles']),
                        'removed_intact_triangles':len(removed),'triangles_after':len(ordinals),
                        'removed_source_names':dict(byname),'baseline_degenerate_triangles':original_degenerate,
                        'final_degenerate_triangles':0,
                        'debris_triangles_retained':sum('debris' in n for n in group_names),
                        'vertex_buffer_byte_identical':True,'index_header_count_updated':len(removed)>0,
                        'index_header_other_fields_byte_identical':data[4:16]==index.payload[4:16]})
    assert sum(r['removed_intact_triangles'] for r in reports)>0
    assert all(r['removed_intact_triangles']==0 for r in reports if r['material']=='main')
    rebuilt=rc.rebuild(doc,lambda c:changes.get(c.offset))
    after=[c for c in rc.walk(rc.parse(rebuilt).roots) if c.tag==b'GEOB']
    assert len(after)==len(geobs)
    assert all(a.payload==b.payload for a,b in zip(geobs,after) if a.offset not in changes)
    for gi,(original,updated) in enumerate(zip(geobs[1::2],after[1::2])):
        assert struct.unpack_from('<I',updated.payload)[0]==3*reports[gi]['triangles_after']
        assert len(updated.payload)==16+6*reports[gi]['triangles_after']
        extracted=[struct.unpack_from('<3H',updated.payload,16+6*i) for i in range(reports[gi]['triangles_after'])]
        expected=[struct.unpack_from('<3H',original.payload,16+6*i) for i in retained_ordinals[gi]]
        assert extracted==expected
    index_map=RECIPES/f'monastery/age{age:02}-retained-triangle-ordinals.json'
    write(index_map,{'age':age,'source_rrgeom_sha256':sha(prior),
                     'retained_triangle_ordinals_by_group':retained_ordinals})
    export=EXPORT/f'monastery/age{age:02}/model.rrgeom';export.parent.mkdir(parents=True,exist_ok=True);export.write_bytes(rebuilt)
    row=payload_record(member,rebuilt)
    return row,{'groups':reports,'removed_intact_triangles':sum(r['removed_intact_triangles'] for r in reports),
                'retained_native_debris_triangles':sum(r['debris_triangles_retained'] for r in reports),
                'native_vertex_buffers_and_collection_bones_byte_identical':True,
                'native_index_buffers_compacted':True,'untouched_chunks_byte_identical':True,
                'retained_ordinals_file':str(index_map),'retained_ordinals_sha256':sha(index_map),
                'new_degenerate_triangles':0,
                'original_sha256':sha(prior),'repaired_sha256':sha(export),'export':str(export)}

def repair_detail_geometry(age,source_rows):
    """Remove exact authored hall/gate canopy components; retain courtyard and shrines.

    The 050 authoring recipe creates one merged mesh per construction stage.
    Every box is 12 triangles and every tiled hip is 320 triangles. The native
    index sequence preserves those source face ranges exactly (verified below).
    """
    member=f'art/scenario/cccastle/monastery_detail_age{age:02}/model.rrgeom'
    prior=Path(source_rows[member]['file']);assert sha(prior)==source_rows[member]['sha256']
    doc=rc.load(prior);geobs=[c for c in rc.walk(doc.roots) if c.tag==b'GEOB']
    assert len(geobs)==2
    vertex,index=geobs
    vc,_,stride,_=struct.unpack_from('<4I',vertex.payload)
    ic,_,width,_=struct.unpack_from('<4I',index.payload)
    assert stride==20 and width==2 and ic//3==1468
    # Face ranges from building_design.py construction order, verified by exact
    # native stage boundaries 132/1008/328 and the primitive triangle counts.
    components=[
      ('courtyard_pavement',0,12,True),('courtyard_edging',12,36,True),
      ('hall_tall_posts',36,84,False),('gate_tall_posts',84,108,False),
      ('bell_shrine_pad',108,120,True),('lotus_plinth',120,132,True),
      ('hall_lintel',132,144,False),('oversized_hall_roof',144,464,False),
      ('gate_lintel',464,476,False),('entry_gate_canopy',476,796,False),
      ('bell_shrine_posts',796,820,True),('bell_shrine_tile_roof',820,1140,True),
      ('hall_ridge',1140,1152,False),('hall_screens',1152,1188,False),
      ('hanging_bell',1188,1280,True),('lotus_basin',1280,1372,True),
      ('lotus_petals',1372,1468,True)]
    assert components[0][1]==0 and components[-1][2]==1468
    assert all(a[2]==b[1] for a,b in zip(components,components[1:]))
    kept_ordinals=[i for _,a,b,keep in components if keep for i in range(a,b)]
    assert len(kept_ordinals)==684
    triples=[]
    for ordinal in kept_ordinals:
        tri=struct.unpack_from('<3H',index.payload,16+6*ordinal)
        assert max(tri)<vc and len(set(tri))==3
        triples.append(index.payload[16+6*ordinal:22+6*ordinal])
    header=bytearray(index.payload[:16]);struct.pack_into('<I',header,0,3*len(triples))
    compact=bytes(header)+b''.join(triples)
    assert len(compact)==16+6*len(triples) and compact[4:16]==index.payload[4:16]
    rebuilt=rc.rebuild(doc,lambda c:compact if c.offset==index.offset else None)
    after=[c for c in rc.walk(rc.parse(rebuilt).roots) if c.tag==b'GEOB']
    assert len(after)==2 and after[0].payload==vertex.payload and after[1].payload==compact
    export=EXPORT/f'monastery/age{age:02}/detail-model.rrgeom'
    export.parent.mkdir(parents=True,exist_ok=True);export.write_bytes(rebuilt)
    row=payload_record(member,rebuilt)
    recipe=RECIPES/f'monastery/age{age:02}-detail-retained-ordinals.json'
    write(recipe,{'age':age,'source_sha256':sha(prior),'components':[
        {'name':name,'start':a,'end':b,'retained':keep} for name,a,b,keep in components],
        'retained_triangle_ordinals':kept_ordinals,
        'source_primitive_contract':'tools/castle_next/building_design.py; box=12 triangles, hipped_tile_roof=320, faceted vessel=92'})
    return row,{'components':[{ 'name':n,'source_triangle_range':[a,b], 'retained':k} for n,a,b,k in components],
                'removed_canopy_and_frame_triangles':1468-len(kept_ordinals),
                'retained_shrine_courtyard_lotus_triangles':len(kept_ordinals),
                'native_vertex_uv_and_collection_buffers_byte_identical':True,
                'native_index_buffer_compacted':True,'new_degenerate_triangles':0,
                'retained_ordinals_file':str(recipe),'retained_ordinals_sha256':sha(recipe),
                'original_sha256':sha(prior),'repaired_sha256':sha(export),'export':str(export)}

def visual_objects(tree):
    root=next(o for o in tree.objects.values() if o['type']=='StampBlueprint' and not o['owner'])
    field=root['fields']['m_blueprints'];array=tree.field(root,field);rows=[]
    for i in range(array['count']):
        slot=array['data_address']+8*i
        obj=tree.by_offset[slot+struct.unpack('<q',tree.bytes(slot,8))[0]]
        if obj['type']=='VisualStampBlueprint':
            model=tree.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/')
            address=obj['offset']+int(obj['fields']['m_transform'].get('Offset'))
            raw=tree.bytes(address,40)
            rows.append({'id':str(obj['id']),'model':model,'offset':address-tree.memory.payload_offset,
                         'raw':raw,'transform':struct.unpack('<10f',raw)})
    return rows

def repair_stamp(age,binding):
    base_member=f'art/stamps/cc050/monastery{age:02}_base_default.bin'
    detail_member=f'art/stamps/cc050/monastery{age:02}_detail.bin'
    base=PRIOR/'integration/payload'/base_member
    detail=PRIOR/'integration/payload'/detail_member
    proofs=binding['private_stamp_proofs']
    branch_paths=[x['path'] for x in binding['rewired_visual_stamps']]
    assert len(branch_paths)==3 and {p.split('/')[0] for p in branch_paths}=={
        'default','cordoba','campaign'}
    assert sha(base)==next(p['sha256'] for p in proofs if p['output']==str(base))
    assert sha(detail)==next(p['sha256'] for p in proofs if p['output']==str(detail))
    base_visuals=visual_objects(NativeTree(base))
    owner=next(v for v in base_visuals if v['model']==f'art/scenario/cccastle/monastery_age{age:02}/model')
    detail_tree=NativeTree(detail)
    detail_visuals=visual_objects(detail_tree)
    assert len(detail_visuals)==1 and detail_visuals[0]['model']==f'art/scenario/cccastle/monastery_detail_age{age:02}/model'
    old=detail_visuals[0]
    assert old['transform']==(0.0,0.0,0.0,1.0,0.0,0.0,0.0,1.0,1.0,1.0)
    memory=bytearray(detail_tree.memory.payload)
    memory[old['offset']:old['offset']+40]=owner['raw']
    rebuilt=rc.rebuild(detail_tree.document,lambda c:bytes(memory) if c.offset==detail_tree.memory.offset else None)
    row=payload_record(detail_member,rebuilt)
    after=visual_objects(NativeTree(row['file']))
    assert len(after)==1 and after[0]['transform']==owner['transform']
    diffs=[i for i,(a,b) in enumerate(zip(detail_tree.memory.payload,NativeTree(row['file']).memory.payload)) if a!=b]
    assert diffs and all(old['offset']<=i<old['offset']+40 for i in diffs)
    return row,{'base_stamp':base_member,'detail_stamp':detail_member,'base_transform':list(owner['transform']),
                'detail_transform_before':list(old['transform']),'detail_transform_after':list(after[0]['transform']),
                'same_transform_all_consumers':{'default':True,'cordoba':True,'campaign':True},
                'consumer_list':binding['private_list'],'changed_memory_bytes':len(diffs),
                'only_visual_transform_changed':True,'object_count_unchanged':len(detail_tree.objects)==len(NativeTree(row['file']).objects)}

def main():
    guarded()
    assert read(OUT/'baseline/freeze.json')['status']=='immutable_pre051'
    media=artifact_sources(); bindings=read(BINDINGS)['bindings']
    donors=read(ROOT/'output/castle_next/donors/donor-manifest.json')['donors']
    payloads=[]; ages=[]
    for age in (3,4):
        donor=donors[f'monastery{age:02}'];names,_=source_map(donor)
        author=copy_authoring(age)
        model,selector=repair_rgm(age,media,donor,names)
        native_roof_member=f'art/scenario/cccastle/monastery_age{age:02}/model.rrgeom'
        native_roof=media[native_roof_member]
        assert sha(native_roof['file'])==native_roof['sha256']
        detail_geometry,geoproof=repair_detail_geometry(age,media)
        stamp,transform=repair_stamp(age,bindings[f'monastery{age:02}'])
        payloads.extend((model,detail_geometry,stamp))
        old_detail=next(x for x in read(ROOT/'output/castle_next/buildings/details/details-validation.json')['models']
                        if x['family']=='monastery' and x['age']==age)
        rgo_member=f'art/scenario/cccastle/monastery_age{age:02}/model.rgo'
        rgo_row=media[rgo_member]
        assert sha(rgo_row['file'])==rgo_row['sha256']
        recipe={'age':age,'baseline_050_sga_sha256':read(OUT/'baseline/freeze.json')['sga050_sha256'],
                'source_blends':author,'selector_proof':selector,'geometry_proof':geoproof,'stamp_proof':transform,
                'original_050_detail_contact_checks_superseded':True,
                'retained_native_roof':{'member':native_roof_member,'sha256':native_roof['sha256'],
                                        'bytes':Path(native_roof['file']).stat().st_size},
                'preserved_native_marker_rgo':{'member':rgo_member,'sha256':rgo_row['sha256'],'bytes':Path(rgo_row['file']).stat().st_size},
                'preserved_native_uv_and_material':'native body RRGeom is exact 050; detail vertex buffers and RRMaterial are byte-identical to 050, only detail index triangles and count changed',
                'roof_design':'restore complete original native donor-shaped roof and structural supports; remove oversized new hall and gate canopies/frame; retain bell shrine and lotus details',
                'native_rgo_markers':'untouched 0.5.0 payload'}
        write(RECIPES/f'monastery/age{age:02}.json',recipe)
        ages.append(recipe)
    result={'schema':'ccp.release051.monastery-repair/v1','status':'source_payload_ready_native_reference_pending',
            'scope':'Castle and Imperial monastery visual resources only',
            'ages':ages,'payloads':payloads,'native_reference_cook':'pending_controller_grant',
            'native_match':'pending','client_import':'pending'}
    write(MON/'receipt.json',result)
    for age in (3,4):
        member=f'art/scenario/cccastle/monastery_age{age:02}/model.rrgeom'
        stale=PAYLOAD/member
        frozen=MON/'diagnostic-canopy-051/payload'/member
        if stale.exists():
            assert frozen.exists() and sha(stale)==sha(frozen)
            stale.unlink()
        for path,diagnostic in ((EXPORT/f'monastery/age{age:02}/model.rrgeom',
                                 MON/f'diagnostic-canopy-051/superseded-export-age{age:02}.rrgeom'),
                                (ART/f'monastery/age{age:02}/body-051-retained-native-local.obj',
                                 MON/f'diagnostic-canopy-051/external-body-051-retained-native-local-age{age:02}.obj'),
                                (RECIPES/f'monastery/age{age:02}-retained-triangle-ordinals.json',
                                 MON/f'diagnostic-canopy-051/superseded-body-ordinals-age{age:02}.json')):
            if path.exists():
                assert not diagnostic.exists();shutil.move(path,diagnostic)
    print('MONASTERY051_PAYLOAD_READY',[(a['age'],a['geometry_proof']['removed_canopy_and_frame_triangles'],
                                    a['selector_proof']['restored_selector_sets']) for a in ages])

if __name__=='__main__':main()

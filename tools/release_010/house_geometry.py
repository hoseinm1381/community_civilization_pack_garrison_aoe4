"""Run in factory-startup Blender: native Chinese donor geometry remodelling.

The common continuous spatial map seats all donor parts at identical interfaces.
Only known half-float positions and packed normal/tangent bytes are patched.
"""
import bpy, copy, hashlib, importlib.util, json, math, os, struct, sys
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
EXT = Path(os.environ['APPDATA']) / 'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0, str(EXT))
spec = importlib.util.spec_from_file_location('garrison_shared', str(EXT/'garrison_shared.cp313-win_amd64.pyd'))
shared = importlib.util.module_from_spec(spec); sys.modules['garrison_shared'] = shared; spec.loader.exec_module(shared)
from garrison_shared import relic_chunky as rc
sys.path.insert(0, str(EXT.parent))
import garrison
sys.modules['garrison.garrison_shared'] = shared
garrison.register()
from garrison.decode_projection import _apply_decoded_static

ART = ROOT/'art/authoring/houses_010'
OUT = ROOT/'output/release_010/houses'
EXPORT = ROOT/'art/exports/houses_010'
for p in [ART, OUT, EXPORT]: p.mkdir(parents=True, exist_ok=True)
sha = lambda data: hashlib.sha256(data).hexdigest()

def smooth(v,a,b):
    t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)

def remodel(p, age):
    x,y,z=p
    # Y runs along the ridge and the domestic three-bay frontage. X is depth.
    # Ground-plane and buried foundation Z stay fixed. Every native fragment uses
    # exactly this map: roof/beam, wall/post and door/threshold seams stay seated.
    if age<4:
        wall=(.84,.88,.91)[age-1]; pitch=(.61,.65,.68)[age-1]
        zz=z if z<0 else z*wall if z<1.8 else 1.8*wall+(z-1.8)*pitch
        # Lower the curved outer eaves while keeping a modest Vietnamese sweep.
        zz-=.065*smooth(abs(x),1.35,2.25)*smooth(z,1.65,2.15)
        xx=x*(.91+.055*smooth(z,1.5,2.0))
        # Extend the original entrance/porch, and widen its posts as one assembly.
        porch=smooth(x,1.15,2.3)
        xx+=.14*porch
        yy=y*(1.06+.055*porch)
    else:
        # Convert the upper floor into a shallow ventilated timber frieze. Native
        # lattice and roof topology remain editable rather than deleting states.
        zz=z if z<0 else z*.89 if z<1.8 else 1.602+(z-1.8)*.19 if z<3.45 else 1.9155+(z-3.45)*.52
        zz-=.075*smooth(abs(x),1.35,2.6)*smooth(z,2.4,4.3)
        porch=smooth(x,1.1,2.8)
        xx=x*(.90+.045*smooth(z,3.0,3.6))+.20*porch
        yy=y*(1.035+.07*porch)
    return Vector((xx,yy,zz))

def jacobian(p,age):
    eps=.00005; cols=[]
    for i in range(3):
        a=list(p); b=list(p);a[i]+=eps;b[i]-=eps
        cols.append((remodel(a,age)-remodel(b,age))/(2*eps))
    return Matrix(cols).transposed()

def bounds(groups):
    pts=[p for g in groups for p in g['positions']]
    lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
    return {'minimum':lo,'maximum':hi,'dimensions':[b-a for a,b in zip(lo,hi)]}

def capture(prefix, groups, scene):
    bb=bounds(groups);lo=Vector(bb['minimum']);hi=Vector(bb['maximum']);center=(lo+hi)/2
    # Same donor framing for each before/after pair is set by caller.
    center=scene.get('house_preview_center',center);span=scene.get('house_preview_span',max(hi-lo))
    scene.render.engine='BLENDER_WORKBENCH';s=scene.display.shading;s.light='STUDIO';s.color_type='MATERIAL';s.show_shadows=True;s.show_cavity=True;s.cavity_type='BOTH'
    scene.render.resolution_x=1100;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    if scene.world is None:scene.world=bpy.data.worlds.new('World')
    scene.world.color=(.16,.16,.16)
    for name,vec in [('iso',(1,-1,.8)),('facade',(1,0,.12)),('back',(-1,0,.12)),('left',(0,-1,.12)),('right',(0,1,.12)),('top',(0,0,1)),('bottom',(0,0,-1))]:
        cam=bpy.data.objects.new('Presentation only',bpy.data.cameras.new('Presentation only'));scene.collection.objects.link(cam)
        cam.location=Vector(center)+Vector(vec).normalized()*span*2;cam.rotation_euler=(Vector(center)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=span*1.45
        scene.camera=cam;scene.render.filepath=str(OUT/f'{prefix}-{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
    scene.camera=None

report={'schema':'ccp.house-native-remodel/v1','status':'running','models':[],
        'native_match_proof':False,'art_claim':'Contemporary Kinh/Red River domestic interpretation; no numeric historical authenticity percentage.',
        'method':'Actual stock mesh deformation; native topology, UV, fragment IDs, material and lifecycle ownership retained.'}
ages=list(map(int,sys.argv[sys.argv.index('--')+1:])) if '--' in sys.argv else [1,2,3,4]
for age in ages:
    source=next((ROOT/f'art/stock_cache/houses_010/age{age:02}').rglob('decoded-static.json'))
    original=json.loads(source.read_text());d=copy.deepcopy(original)
    raw=Path(d['geometry']['source']['path']).read_bytes();doc=rc.parse(raw)
    chunks=[c for c in rc.walk(doc.roots) if c.tag==b'GEOB']
    vchunks=chunks[::2]; assert len(vchunks)==len(d['geometry']['groups'])
    changes={};rows=[]
    for gi,(g,c) in enumerate(zip(d['geometry']['groups'],vchunks)):
        data=bytearray(c.payload); n,_,stride,_=struct.unpack_from('<4I',data)
        assert stride==24 and n==len(g['positions'])
        changed=[];max_error=0
        for i,p in enumerate(g['positions']):
            off=16+i*stride; packed=struct.unpack_from('<4e',data,off)
            assert tuple(p)==(-packed[0],-packed[2],packed[1])
            v=remodel(p,age);J=jacobian(p,age);assert J.determinant()>0
            data[off:off+8]=struct.pack('<4e',-v.x,v.z,-v.y,packed[3])
            q=struct.unpack_from('<4e',data,off);g['positions'][i]=[-q[0],-q[2],q[1]]
            max_error=max(max_error,(Vector(g['positions'][i])-v).length)
            normal=(J.inverted().transposed()@Vector(g['normals'][i])).normalized()
            tn=struct.unpack_from('<3b',data,off+12); tangent=J@Vector((-tn[0]/127,-tn[2]/127,tn[1]/127));tangent=(tangent-normal*tangent.dot(normal)).normalized()
            for delta,norm in [(8,normal),(12,tangent)]:
                data[off+delta:off+delta+3]=struct.pack('<3b',*(max(-127,min(127,round(c*127))) for c in (-norm.x,norm.z,-norm.y)))
            norm=struct.unpack_from('<3b',data,off+8);g['normals'][i]=list(Vector((-norm[0]/127,-norm[2]/127,norm[1]/127)).normalized())
            assert bytes(data[off+16:off+24])==c.payload[off+16:off+24]
            if bytes(data[off:off+16])!=c.payload[off:off+16]:changed.append(i)
        changes[c.offset]=bytes(data)
        rows.append({'group':gi,'material':g['preview_material'],'vertex_count':n,'changed_vertex_count':len(changed),'changed_vertex_indices':changed,'payload_offset':c.offset,'vertex_stride':stride,'max_half_float_error_metres':max_error,'index_buffer_sha256':sha(chunks[2*gi+1].payload),'uv_selector_bytes_preserved':True})
    encoded=rc.rebuild(doc,lambda c:changes.get(c.offset));assert len(raw)==len(encoded)
    target=EXPORT/f'vn_house_age{age:02}.rrgeom';target.write_bytes(encoded)
    projection=ART/f'vn_house_age{age:02}-projection.json';projection.write_text(json.dumps(d))
    # All collection fragments, including construction/damage pieces, receive the
    # same spatial map, so common-contact coordinates remain common. Validate all
    # exactly repeated coordinates instead of trusting the render.
    seen={};contact_count=0;max_contact=0
    for go,gn in zip(original['geometry']['groups'],d['geometry']['groups']):
        for old,new in zip(go['positions'],gn['positions']):
            key=tuple(old)
            if key in seen:contact_count+=1;max_contact=max(max_contact,(Vector(new)-Vector(seen[key])).length)
            else:seen[key]=new
    assert max_contact==0
    bpy.ops.wm.read_factory_settings(use_empty=True)
    proxy=bpy.data.objects.new(f'Chinese A age{age:02} donor',None);bpy.context.scene.collection.objects.link(proxy)
    proxy['garrison_decode_manifest']=str(source);proxy['garrison_logical_path']=original['request']['logical_path'];proxy['garrison_display_name']=f'Chinese A age{age:02}'
    root=_apply_decoded_static(proxy,original,create_controls=False)
    sc=bpy.context.scene;bb=bounds(original['geometry']['groups']);sc['house_preview_center']=[(a+b)/2 for a,b in zip(bb['minimum'],bb['maximum'])];sc['house_preview_span']=max(bb['dimensions'])*1.08
    bpy.ops.file.pack_all();donor_blend=ART/f'Chinese_A_age{age:02}_donor.blend';bpy.ops.wm.save_as_mainfile(filepath=str(donor_blend));capture(f'age{age:02}-before',original['geometry']['groups'],sc)
    for o in [x for x in sc.objects if x.type=='MESH']:
        gi=o.get('garrison_mesh_index');g=d['geometry']['groups'][gi];assert len(o.data.vertices)==len(g['positions'])
        for v,co in zip(o.data.vertices,g['positions']):v.co=co
        o.data.normals_split_custom_set_from_vertices(g['normals']);o.data.update();o['ccp_native_geometry']=str(target);o['ccp_remodel']='lower roof pitch, longer frontage, broader entrance veranda; exact shared-interface spatial map'
    root.name=f'Vietnam_Kinh_House_Age{age:02}'
    capture(f'age{age:02}-after',d['geometry']['groups'],sc)
    blend=ART/f'Vietnam_Kinh_House_Age{age:02}.blend';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    row={'age':age,'name':f'vn_house_age{age:02}','donor':str(source),'native_geometry':str(target),'native_geometry_sha256':sha(encoded),'donor_geometry_sha256':sha(raw),'donor_resources':{k:v for k,v in original['resources'].items() if isinstance(v,dict) and 'sha256' in v},'before_bounds':bounds(original['geometry']['groups']),'after_bounds':bounds(d['geometry']['groups']),'editable_blend':str(blend),'editable_blend_sha256':sha(blend.read_bytes()),'donor_blend':str(donor_blend),'groups':rows,'native_collection_contract':original['structure_collection_contract'],'lod_policy':'All GEOB vertex buffers patched; original has no separate decoded LOD geometry contract. All index buffers and every non-vertex chunk unchanged.','contact_checks':{'repeated_interface_coordinates':contact_count,'max_gap_metres':max_contact,'foundation_ground_z_preserved':True},'requires_rgm_render_bound_refresh':True,'material_policy':'Original stock materials and dynamic owner masks preserved; optional private surface variants added separately.'}
    report['models'].append(row);(OUT/'geometry-validation.json').write_text(json.dumps(report,indent=2));print('HOUSE_NATIVE_READY',age,flush=True)
report['status']='passed';(OUT/'geometry-validation.json').write_text(json.dumps(report,indent=2))
(ROOT/'art/recipes/release_010/houses-native.json').write_text(json.dumps({'schema':'ccp.houses-native-recipe/v1','generator':str(Path(__file__).resolve()),'anatomy':['long low domestic body','stock roof and eave mesh remodelling','original entrance widened as veranda','donor facade and posts mapped together','Age IV upper room compressed to ventilated frieze'],'models':[{k:v for k,v in r.items() if k not in ['groups','native_collection_contract']} for r in report['models']]},indent=2))

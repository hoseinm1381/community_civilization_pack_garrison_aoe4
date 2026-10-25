"""Typed native chunk operations for qualified static landmark output.

All geometry buffers are freshly native-cooked. No vertex/topology fabrication.
"""
import os,sys,struct,hashlib,json
from pathlib import Path
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(EXT));from garrison_shared import relic_chunky as rc,building_project as bp
sha=lambda b:hashlib.sha256(b).hexdigest()
def visibility_evidence(raw,rows):
 d=rc.parse(raw);tables=[];predicates=[]
 for c in rc.walk(d.roots):
  if c.tag==b'MSD ' and len(c.payload)>4:
   name,at=rc.read_lp_string(c.payload,0);count=struct.unpack_from('<I',c.payload,at)[0];at+=4;members=[]
   for i in range(count):value,at=rc.read_lp_string(c.payload,at);members.append(value)
   assert at==len(c.payload);tables.append((name,members))
  if c.tag==b'CNBP':
   count=struct.unpack_from('<I',c.payload)[0];at=4;states=[]
   for i in range(count):
    assert struct.unpack_from('<IBI',c.payload,at)==(2,0,1);at+=9
    prop,at=rc.read_lp_string(c.payload,at);value,at=rc.read_lp_string(c.payload,at);assert prop=='life_cycle_state';states.append(value)
   assert at==len(c.payload);predicates.append(states)
 assert len(tables)==len(predicates)
 source_names={r['name'] for r in rows};enabled={}
 for state in [f'construct_{s:02}' for s in range(0,100,5)]+['healthy']+[f'damage_{i}' for i in range(1,6)]+['ruins']:
  visible={v for (_,members),states in zip(tables,predicates) if state in states for v in members}
  expected={r['name'] for r in rows if r['first_stage']<=int(state.rsplit('_',1)[1])} if state.startswith('construct_') else set() if state=='ruins' else source_names
  assert visible==expected,(state,visible,expected);enabled[state]=sorted(visible)
 return {'all_construction_steps_and_healthy_damage_visibility_exact_expected':True,'no_donor_members':True,'enabled_parts':enabled,'selector_count':len(tables),'condition_encoding':'typed native OR state-comparison records emitted by installed writer'}
def packed(c,payload=None):
 return rc.pack_chunk(c.kind,c.tag,c.payload if payload is None else payload,version=c.version,name=c.name)
def native_single_geometry(raw_levels):
 """Keep the compiler's exact LOD0 geometry/collection partition contract.

 Source LOD1/2 are independently cooked evidence, not merged runtime buffers.
 There is no qualified per-LOD MSCL triangle-membership remapping route.
 """
 assert len(raw_levels)==3
 levels=[]
 for raw in raw_levels:
  doc=rc.parse(raw);assert len(doc.roots)==1 and doc.roots[0].tag==b'RRGO'
  root=doc.roots[0];meshes=[c for c in root.children if c.tag==b'MESH']
  count=[c for c in root.children if c.tag==b'NBME'];assert len(count)==1
  assert struct.unpack('<I',count[0].payload)[0]==len(meshes)
  triangles=vertices=0
  for mesh in meshes:
   assert [c.tag for c in mesh.children]==[b'NBLO',b'LOD ']
   assert struct.unpack('<I',mesh.children[0].payload)==(1,)
   for geometry in [c for c in mesh.children[1].children if c.tag==b'GEOM']:
    buffers=[c for c in rc.walk([geometry]) if c.tag==b'GEOB'];assert len(buffers)==2
    vertex,index=[struct.unpack_from('<4I',c.payload) for c in buffers]
    assert vertex[2]==20 and index[2] in [2,4]
    assert all(len(c.payload)==16+i[0]*i[2] for c,i in zip(buffers,[vertex,index]))
    assert index[0]%3==0
    indices=struct.unpack_from('<'+('H' if index[2]==2 else 'I')*index[0],buffers[1].payload,16)
    assert max(indices)<vertex[0]
    vertices+=vertex[0];triangles+=index[0]//3
  assert triangles>0
  levels.append({'source_sha256':sha(raw),'native_mesh_count':len(meshes),'triangles':triangles,'vertices':vertices})
 assert levels[0]['triangles']>levels[1]['triangles']>levels[2]['triangles']
 return raw_levels[0],{'mode':'native-compatible-single','native_lod_count':1,'authored_lods_three':True,'source_levels':levels,'runtime_geometry_sha256':sha(raw_levels[0]),'runtime_geometry_byte_identical_to_fresh_lod0':True,'limitation':'Lower LOD activation unsupported: per-LOD native collection triangle membership mapping unqualified; source LOD1/2 retained, not installed as runtime geometry.'}

def three_lod_geometry(raw_levels):
 assert len(raw_levels)==3
 documents=[rc.parse(b) for b in raw_levels];levels=[];headers=[];counts=[]
 for d in documents:
  assert len(d.roots)==1 and d.roots[0].tag==b'RRGO' and d.roots[0].version==2
  root=d.roots[0];assert [(c.tag,c.version) for c in root.children]==[(b'NBME',2),(b'MESH',2)]
  assert struct.unpack('<I',root.children[0].payload)==(1,)
  mesh=root.children[1];assert [c.tag for c in mesh.children]==[b'NBLO',b'LOD ']
  assert struct.unpack('<I',mesh.children[0].payload)==(1,)
  lod=mesh.children[1];levels.append(lod)
  assert lod.children[0].tag==b'NBGO';geoms=lod.children[1:]
  assert len(geoms)==struct.unpack('<I',lod.children[0].payload)[0]
  headers.append([next(c.payload for c in g.children if c.tag==b'GOHD') for g in geoms])
  buffers=[c for c in rc.walk(lod.children) if c.tag==b'GEOB']
  assert len(buffers)==2
  info=[struct.unpack_from('<4I',c.payload) for c in buffers]
  vertex,index=info;assert vertex[2]==20 and index[2] in [2,4]
  assert all(len(c.payload)==16+i[0]*i[2] for c,i in zip(buffers,info))
  assert index[0]%3==0
  values=struct.unpack_from('<'+('H' if index[2]==2 else 'I')*index[0],buffers[1].payload,16)
  assert max(values)<vertex[0]
  counts.append({'vertices':vertex[0],'triangles':index[0]//3,'source_sha256':sha(d.raw) if hasattr(d,'raw') else None})
 assert headers[0]==headers[1]==headers[2],'Different native shaders/geometry groups across levels'
 assert counts[0]['triangles']>counts[1]['triangles']>counts[2]['triangles']
 root=documents[0].roots[0];mesh=root.children[1]
 newmesh=packed(mesh,packed(mesh.children[0],struct.pack('<I',3))+b''.join(packed(c) for c in levels))
 result=rc.pack_document([packed(root,packed(root.children[0])+newmesh)],flags=documents[0].flags)
 readback=rc.parse(result);m=readback.roots[0].children[1]
 assert struct.unpack('<I',m.children[0].payload)==(3,)
 assert len(m.children)==4
 for original,new in zip(levels,m.children[1:]):assert original.payload==new.payload
 return result,{'level_count':3,'mesh_count':1,'counts':counts,'level_payloads_byte_identical_to_fresh_cook':True,'all_geometry_material_headers_same':True,'stacked_separate_meshes':False,'routing':'Three typed LOD children under one native MESH; runtime distance selection pending native game'}

def intact_damage_conditions(raw):
 d=rc.parse(raw);edits={};count=0
 for c in rc.walk(d.roots):
  if c.tag!=b'CNBP':continue
  n=struct.unpack_from('<I',c.payload)[0];at=4
  for i in range(n):
   assert struct.unpack_from('<IBI',c.payload,at)==(2,0,1);at+=9
   machine,at=rc.read_lp_string(c.payload,at);state,at=rc.read_lp_string(c.payload,at);assert machine=='life_cycle_state'
  assert at==len(c.payload)
  extra=b''.join(struct.pack('<IBI',2,0,1)+rc.lp_string('life_cycle_state')+rc.lp_string(f'damage_{i}') for i in range(1,6))
  edits[c.offset]=struct.pack('<I',n+5)+c.payload[4:]+extra;count+=1
 result=rc.rebuild(d,lambda c:edits.get(c.offset))
 return result,{'completed_custom_geometry_visible_under_damage_states':list(range(1,6)),'predicate_tables_extended':count,'ruins_geometry':'new intact principal excluded; native auxiliary wreck retained','route':'Known native state comparison OR encoding; no unknown data fields rewritten'}

def copy_native_markers(raw,donor):
 d=rc.parse(raw);s=rc.parse(donor)
 a=[c for c in rc.walk(d.roots) if c.tag==b'MRKS'];b=[c for c in rc.walk(s.roots) if c.tag==b'MRKS']
 assert len(a)==len(b)==1 and a[0].version==b[0].version
 at=4;rows=[];total=struct.unpack_from('<I',b[0].payload)[0]
 for i in range(total):
  name,at=rc.read_lp_string(b[0].payload,at)
  prefix=struct.unpack_from('<II',b[0].payload,at);values=struct.unpack_from('<10f',b[0].payload,at+8);tail=struct.unpack_from('<I',b[0].payload,at+48)[0];at+=52
  assert prefix==(0,0),'Only qualified static model-root-frame marker layout may be copied'
  attributes={}
  for j in range(tail):
   key,at=rc.read_lp_string(b[0].payload,at);kind=b[0].payload[at];at+=1
   if kind==0:value=b[0].payload[at];assert value in [0,1];at+=1
   elif kind==3:value,at=rc.read_lp_string(b[0].payload,at)
   elif kind==2:value=struct.unpack_from('<f',b[0].payload,at)[0];at+=4
   else:raise AssertionError(('Unqualified marker attribute type',key,kind))
   attributes[key]=value
  rows.append({'name':name,'native_translation':list(values[4:7]),'source_frame':'model root; no skeleton or collection bone reference','metadata_attributes':attributes})
 assert at==len(b[0].payload)
 result=rc.rebuild(d,lambda c:b[0].payload if c.offset==a[0].offset else None)
 return result,{'native_marker_payload_sha256':sha(b[0].payload),'marker_count':total,'byte_identical':True,'markers':rows,'root_frame_compatible':True}

def copy_native_skeleton_owner(raw,donor,rows):
 """Retain exact native skeleton/cloth owner while selecting fresh static parts.

 SKMS inline cloth data is retained as an animation/physics dependency; it is
 absent from every visible MSBP membership list, so no obsolete tent mesh is
 selected. No marker or skeleton transform is decoded or fabricated here.
 """
 fresh=rc.parse(raw);native=rc.parse(donor)
 assert len(fresh.roots)==len(native.roots)==1 and fresh.roots[0].tag==native.roots[0].tag==b'MODL'
 source=fresh.roots[0];owner=native.roots[0]
 keep={b'INFO',b'MRKS',b'SKLN',b'SKMS',b'CUAT'}
 assert sum(c.tag==b'SKLN' for c in owner.children)==1
 assert sum(c.tag==b'SKMS' for c in owner.children)==2
 selector=next(c for c in source.children if c.tag==b'MSBP')
 cloth=[c.decoded_name for c in owner.children if c.tag==b'SKMS']
 assert all(name.encode() not in selector.payload for name in cloth)
 assert all(r['name'].encode() in selector.payload for r in rows)
 # The native top-level ordering and count flags accompany the original exact
 # skeleton. Fresh compiler collection buffers/part predicates remain exact.
 replacement={c.tag:c for c in source.children if c.tag not in keep}
 children=[]
 for c in owner.children:
  if c.tag in keep:children.append(packed(c))
  elif c.tag in replacement:children.append(packed(replacement.pop(c.tag)))
 assert not replacement
 result=rc.pack_document([packed(source,b''.join(children))],flags=fresh.flags)
 actual=rc.parse(result).roots[0]
 for tag in keep:
  assert [c.payload for c in actual.children if c.tag==tag]==[c.payload for c in owner.children if c.tag==tag]
 for tag in [b'MSCL',b'MSBP']:
  assert next(c.payload for c in actual.children if c.tag==tag)==next(c.payload for c in source.children if c.tag==tag)
 markers=next(c.payload for c in owner.children if c.tag==b'MRKS')
 return result,{'native_marker_payload_sha256':sha(markers),'marker_count':struct.unpack_from('<I',markers)[0],'byte_identical':True,'root_frame_compatible':False,'native_skeleton_and_physics_owner_retained':True,'exact_native_owner_chunks':[t.decode() for t in keep],'native_skinned_meshes_retained_as_unselected_owner_dependencies':cloth,'obsolete_cloth_names_absent_from_every_fresh_selector_membership':True,'fresh_static_collection_and_selector_payloads_byte_identical':True,'runtime_skeleton_physics_and_culling':'unverified'}

def remove_forge_smoke(raw):
 d=rc.parse(raw);edits={};removed=[]
 for c in rc.walk(d.roots):
  if c.tag!=b'ACTN' or not (b'smoke_blacksmith_stack_small' in c.payload or b'smoke_hotcoal_door' in c.payload):continue
  count=struct.unpack_from('<I',c.payload)[0];at=4;retained=[]
  for i in range(count):
   start=at;action,at=rc.read_lp_string(c.payload,at);n=struct.unpack_from('<I',c.payload,at)[0];at+=4;parameters={}
   for j in range(n):
    name,at=rc.read_lp_string(c.payload,at);value,at=rc.read_lp_string(c.payload,at);parameters[name]=value
   at+=4
   if action=='fx_attach' and any(v in parameters.get('fx','') for v in ['smoke_blacksmith_stack_small','smoke_hotcoal_door']):removed.append(parameters)
   else:retained.append(c.payload[start:at])
  assert at==len(c.payload)
  edits[c.offset]=struct.pack('<I',len(retained))+b''.join(retained)
 assert len(removed)==4
 result=rc.rebuild(d,lambda c:edits.get(c.offset))
 before=[(c.tag,c.payload) for c in rc.walk(d.roots) if c.tag not in [b'MODL',b'ACTC',b'ACTN']]
 after=[(c.tag,c.payload) for c in rc.walk(rc.parse(result).roots) if c.tag not in [b'MODL',b'ACTC',b'ACTN']]
 assert before==after
 return result,{'pure_visual_actions_removed':removed,'all_behavior_conditions_states_nonaction_chunks_byte_identical':True,'omitted_effects':'Donor forge chimney/hot-coal ambient smoke only; custom caravanserai has no forge','native_graph_preserved':'Lifecycle/state contract unchanged; four purely visual effect actions intentionally removed'}

def owner_flag(raw,private_stem):
 d=rc.parse(raw);edits={};found=0
 for c in rc.walk(d.roots):
  if c.tag==b'BANA':
   old,at=rc.read_lp_string(c.payload,0);assert at==len(c.payload);edits[c.offset]=rc.lp_string(private_stem.replace('/','\\'))
  if c.tag==b'CNBP':
   # Preserve native build==1 AND health>=threshold. Only lower health threshold.
   n=struct.unpack_from('<I',c.payload)[0];assert n==2;at=4;data=bytearray(c.payload);values=[]
   for i in range(n):
    assert struct.unpack_from('<IBI',data,at)==(3,0,0);at+=9
    name,at=rc.read_lp_string(data,at);value_at=at;value,comparison=struct.unpack_from('<fI',data,at);at+=8;values.append((name,value,comparison))
    if name=='health':assert abs(value-.85)<1e-6 and comparison==5;struct.pack_into('<f',data,value_at,.0001)
    else:assert name=='build' and value==1 and comparison==0
   assert at==len(data);assert [v[0] for v in values]==['build','health'];edits[c.offset]=bytes(data);found+=1
 assert found==1
 result=rc.rebuild(d,lambda c:edits.get(c.offset))
 return result,{'build_complete_exact_native_predicate_preserved':True,'alive_health_threshold':.0001,'foundation_hidden_by_build_equal_1':True,'ruins_hidden_by_health_zero':True,'native_team_colour_shader_and_geometry_preserved':True,'native_runtime':'pending'}


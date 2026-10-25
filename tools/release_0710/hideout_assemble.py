"""Private fortified shelter media and compiled visual-only RGD deltas."""
import ast,copy,hashlib,struct,types

from common import *
sys.path.insert(0,CFG['garrison_extension']);from garrison_shared import rgd,relic_chunky as rc,building_project as bp,model_variants as mv
sys.path.insert(0,str(ROOT/'tools/release_010'));import integration_native
from integration_codec import copy_native_markers
sys.path.insert(0,str(ROOT/'tools/release_040'));import lifecycle
W=OUT/'hideout';integration_native.WORK=W/'schema'
def loadfunc(file,names):
 tree=ast.parse((ROOT/file).read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(file),'exec'),globals())
loadfunc('tools/release_061/assemble_castle_object_061.py',{'selector_table','rebase_model','rebase_material'})
loadfunc('tools/release_010/integration.py',{'active_visuals'})
native=types.SimpleNamespace(NativeTree=integration_native.NativeTree,active_visuals=active_visuals)
loadfunc('tools/release_020/media.py',{'stamp'})
BASEBACK=BASE/'readback';rows=[];proofs=[]
def put(member,raw):
 p=W/'payload'/member;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);rows.append({'member':member,'file':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'toc':'attrib' if member.startswith('attrib/') else 'data'})
def flat(d):return {p:(n.kind,n.value) for p,n in rgd.flatten(d.nodes) if n.kind not in ('List','List2')}
def main():
 guard();schema=W/'schema/reflect.db';schema.parent.mkdir(parents=True,exist_ok=True)
 if not schema.exists():run('reflect',[CFG['archive_tool'],'extract-member',Path(CFG['content_editor']).parent/'engine/archives/reflect.sga','reflect.db',schema],folder=W/'logs')
 for variant in ['default','stone']:
  cook=read(W/f'cook-{variant}-v1.json');model=Path(cook['model']);folder=model.parent;oldstem='art/scenario/cc020/hideout_shelter_'+variant+'/model';newstem='art/scenario/c710h'+variant[0]+'/model'
  old=(BASEBACK/(oldstem+'.rgm')).read_bytes();parts=read(EXPORT/'hideout'/('shelter_'+variant)/'building.json')['parts']
  raw=bp.construction_model(model.with_suffix('.rgm').read_bytes(),old,parts,profile_id='english-house')
  olddoc=rc.parse(old);newdoc=rc.parse(raw);oldms=next(c for c in rc.walk(olddoc.roots) if c.tag==b'MSBP');newms=next(c for c in rc.walk(newdoc.roots) if c.tag==b'MSBP')
  raw=rc.rebuild(newdoc,lambda c:oldms.payload if c.offset==newms.offset else None);raw,markers=copy_native_markers(raw,old);raw=rebase_model(raw,newstem)
  assert selector_table(raw)==selector_table(old)
  oc=rc.parse(old).roots[0].children;nc=rc.parse(raw).roots[0].children
  assert [(c.tag,c.name,c.version) for c in oc]==[(c.tag,c.name,c.version) for c in nc]
  assert all(a.payload==b.payload for a,b in zip(oc,nc) if a.tag not in (b'MSCL',b'BANA')), 'Native nongeometry model drift'
  put(newstem+'.rgm',raw);put(newstem+'.rrgeom',model.with_suffix('.rrgeom').read_bytes());put(newstem+'.rgo',(BASEBACK/(oldstem+'.rgo')).read_bytes())
  mat,refs=rebase_material(model.with_suffix('.rrmaterial').read_bytes(),f"art/scenario/garrison/{cook['key']}/buildings/hideout",newstem.rsplit('/',1)[0]);put(newstem+'.rrmaterial',mat)
  for leaf,member in refs.items():put(member,(folder/leaf).read_bytes())
  target=W/'stamp-work'/('hideout_'+variant+'.bin');sp=stamp(BASEBACK/('art/stamps/cc020/hideout_shelter_'+variant+'.bin'),target,oldstem,newstem)
  put('art/stamps/c710/hideout_'+variant+'.bin',target.read_bytes());proofs.append({'variant':variant,'selectors_exact':True,'markers':markers,'stamp':sp,'native_rgo_byte_identical':True})
 attachment='attrib/attachments/attachment_lists/vietnam/release_020/vn_020_hideout_visual.rgd';old=rgd.read((BASEBACK/attachment).read_bytes());new=copy.deepcopy(old);changes=[]
 for path,n in rgd.flatten(new.nodes):
  before=n.value
  if n.key=='pbgid':n.value=read(W/'allocated-identity.json')['pbgid']
  elif n.key=='stamp' and isinstance(n.value,str):
   for variant in ['default','stone']:
    if n.value.replace('\\','/')=='art/stamps/cc020/hideout_shelter_'+variant:n.value='art\\stamps\\c710\\hideout_'+variant
  if n.kind not in ('List','List2') and n.value!=before:changes.append({'path':path,'before':before,'after':n.value})
 assert len(changes)==9;revert=copy.deepcopy(new)
 for c in changes:rgd.find(revert.nodes,c['path']).value=c['before']
 assert rgd.write(revert)==rgd.write(old)
 put('attrib/attachments/attachment_lists/vietnam/release_0710/vn_0710_hideout_fortified_visual.rgd',rgd.write(new))
 compile=read(W/'compile-v2.json');back=Path(compile['readback']);bindingproof=[]
 for campaign in ['']:
  for name in ['vn_building_defense_outpost_chi_fortified','vn_building_defense_outpost_2_chi_fortified']:
   member='attrib/'+campaign+'ebps/vietnam/buildings/hideouts/'+name+'.rgd'
   if not (BASEBACK/member).exists():
    member='attrib/ebps/vietnam/buildings/hideouts/'+name+('_campaign' if campaign else '')+'.rgd'
   if not (BASEBACK/member).exists():continue
   old=rgd.read((BASEBACK/member).read_bytes());new=rgd.read((back/member).read_bytes());before=flat(old);after=flat(new)
   assert before.keys()==after.keys();delta=[p for p in before if before[p]!=after[p]]
   assert {p.split('/')[0] for p in delta}=={'default','campaign'}
   assert len(delta)==(4 if '_2_' not in name else 2)
   assert delta and all(('animator_attachments/' in p or '/attachments/' in p) and p.endswith(('$PBGNAME','$MOD')) for p in delta),delta
   reverted=copy.deepcopy(new)
   for path in delta:rgd.find(reverted.nodes,path).value=rgd.find(old.nodes,path).value
   assert reverted.nodes==old.nodes, 'Compiled ordered semantic node drift'
   normalized=copy.deepcopy(old)
   for path in delta:rgd.find(normalized.nodes,path).value=rgd.find(new.nodes,path).value
   reverse=copy.deepcopy(normalized)
   for path in delta:rgd.find(reverse.nodes,path).value=rgd.find(old.nodes,path).value
   assert rgd.write(reverse)==rgd.write(old)
   put(member,rgd.write(normalized));bindingproof.append({'member':member,'changed_fields':delta,'compile_semantics_reversion_exact':True,'baseline_KEYS_preserved':True,'full_typed_reversion_matches_baseline':True,'native_compile_sha256':sha(back/member),'baseline_sha256':sha(BASEBACK/member),'normalization':'exact accepted079 document cloned; only nativev2-verified visual reference values copied; preserves original KEYS ordering'})
 assert len(bindingproof)==2,bindingproof
 write(W/'payload.json',{'status':'native_cook_compile_readback_passed_runtime_unverified','members':rows,'models':proofs,'attachment_changes':changes,'compiled_bindings':bindingproof,'source_policy':str(W/'source-policy.json'),'proof_files':{str(p):sha(p) for p in [W/'source-policy.json',W/'allocated-identity.json',W/'cook-default-v1.json',W/'cook-stone-v1.json',W/'compile-v2.json',W/'inheritance-final.json',W/'visual-review.json',W/'stamp-transforms.json',W/'compound-default-grounded/proof.json',W/'compound-stone-grounded/proof.json']}});print('HIDEOUT_PAYLOAD',len(rows))
if __name__=='__main__':main()



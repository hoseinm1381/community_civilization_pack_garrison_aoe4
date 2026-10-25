"""Prepare a private cattle animator and a narrowly patched visual attachment."""
from native_codec import CFG,OUT,ROOT,sha
import importlib,json,subprocess,sys,re
from pathlib import Path
DEST=OUT/'integration-v2';DEST.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(Path(CFG['garrison_extension']).parent))
variants=importlib.import_module('garrison.model_variants');rgd=importlib.import_module('garrison.rgd')
inventory=json.loads((ROOT/'output/release_081/animation/inventory.json').read_text())
old='art/civilizations/common/animals/archetypes/base_cattle/base_cattle'
new='art/scenario/garrison/cc082/buffalo_animator/animator'
source=DEST/'stock';source.mkdir()
payload=DEST/'payload';payload.mkdir()
records=[]
for row in inventory['official_cattle_animation_resources']['indexed_resources']:
    proc=subprocess.run([CFG['archive_tool'],'extract',row['archive_path'],str(source),'--member',row['logical_path']],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr
    path=source/row['logical_path'];raw=path.read_bytes()
    if path.suffix=='.rhka':
        assert sha(path)=='01faed8fd3db588867b8a6d9539246bf9c5ef3734d5248c32adf7a249ef48fab';continue
    changed=variants.rewrite_model_path(raw,old.replace('/','\\'),new.replace('/','\\')) if path.suffix=='.rgm' else raw
    target=payload/(new+path.suffix);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(changed)
    records.append({'member':new+path.suffix,'file':str(target),'sha256':sha(target),'source':str(path),'source_sha256':sha(path),'bytes_changed':raw!=changed})
attachment='attrib/attachments/attachment_lists/vietnam/release_076/vn076_water_buffalo.rgd'
baseline=ROOT/'output/release_081/delivery/final-v1/community_civilization_pack.sga'
assert sha(baseline)=='a295752f63ad8bcf62b1ca323d0a60c1084d6f6c3c4f380ab52421324ca17a10'
proc=subprocess.run([CFG['archive_tool'],'extract',str(baseline),str(DEST/'baseline'),'--member',attachment],capture_output=True,text=True);assert proc.returncode==0,proc.stderr
original=(DEST/'baseline'/attachment).read_bytes();parsed=rgd.read(original)
assert rgd.write(parsed)==original,'RGD writer must roundtrip original attachment exactly'
before={path:node.value for path,node in rgd.flatten(parsed.nodes) if isinstance(node.value,(str,int,float,bool,type(None)))}
changed_paths=[]
for path,node in rgd.flatten(parsed.nodes):
    if path.endswith('/attachment_lists/parent_animator'):
        assert node.value.replace('\\','/')==old,(path,node.value)
        node.value=new.replace('/','\\');changed_paths.append(path)
assert changed_paths
raw=rgd.write(parsed);target=payload/attachment;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
after={path:node.value for path,node in rgd.flatten(rgd.read(raw).nodes) if isinstance(node.value,(str,int,float,bool,type(None)))}
assert {k for k in before if before[k]!=after[k]}==set(changed_paths)
records.append({'member':attachment,'file':str(target),'sha256':sha(target),'changed_fields':changed_paths,'all_other_fields_exact':True})
recipe={'baseline':str(baseline),'baseline_sha256':sha(baseline),'old_animator':old,'new_animator':new,'attachment':attachment,'records':records}
(DEST/'recipe.json').write_text(json.dumps(recipe,indent=2))
print('PRIVATE_ANIMATOR_PREPARED',[(r['member'],r.get('bytes_changed')) for r in records])

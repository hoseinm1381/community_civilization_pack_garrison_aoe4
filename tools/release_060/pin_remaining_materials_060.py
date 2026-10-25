"""Pin explicit remaining material maps for one reproducible native batch."""
import argparse
from pathlib import Path
import re

from common import RECIPES, guard, owned, read, sha, write


def native_albedo(material,slot):
    refs={t['logical_path'] for b in material['blocks'] for t in b.get('textures',[]) if t['name']==slot}
    if len(refs)!=1:raise ValueError('Expected one exact native albedo slot')
    return refs.pop()


def expand_lod_materials(donor,selected,retained=()):
    result=dict(selected);native={m['name']:m for m in donor['material']['materials']}
    for target in native.keys()-result.keys()-set(retained):
        role=re.sub(r'_lod[123]$','',target)
        candidates=[name for name in selected if name!=role and re.sub(r'_lod[123]$','',name)==role]
        if not candidates:continue
        values=[]
        for name in candidates:
            slot=selected[name]['slot']
            if native_albedo(native[name],slot)!=native_albedo(native[target],slot):
                raise ValueError('Different native albedo atlas cannot share a LOD treatment')
            values.append(selected[name])
        if any(value!=values[0] for value in values):raise ValueError('Ambiguous same-role LOD albedo treatment')
        result[target]=dict(values[0])
    return result


def pin_model(row):
    receipt_path=owned(row['source_receipt']);receipt=read(receipt_path)
    if 'blend' in receipt and sha(receipt['blend'])!=receipt['blend_sha256']:
        raise ValueError('Editable source changed')
    mapping_path=owned(row['material_map']);mapping=read(mapping_path)
    superseding=None
    if row.get('material_map_receipt'):
        superseding_path=owned(row['material_map_receipt']);superseding=read(superseding_path)
        if Path(superseding['map'])!=mapping_path or superseding['map_sha256']!=sha(mapping_path):
            raise ValueError('Separately pinned corrected material map changed')
    elif receipt.get('material_map') and (Path(receipt['material_map'])!=mapping_path or
            receipt['material_map_sha256']!=sha(mapping_path)):raise ValueError('Saved material map changed')
    donor_path=owned(mapping['donor_manifest']);donor=read(donor_path)
    if sha(donor_path)!=mapping['donor_manifest_sha256']:raise ValueError('Native donor manifest changed')
    if (mapping.get('exact_native_model') or mapping.get('exact_donor_model'))!=donor['resources']['model']['logical_path']:
        raise ValueError('Material map belongs to a different native model')
    selected={};retained=set()
    for entry in mapping['groups']:
        name=entry.get('native_material') or entry.get('material_name')
        if entry.get('albedo_png') is None:retained.add(name);continue
        image=owned(entry['albedo_png']);digest=sha(image)
        if entry.get('albedo_sha256',digest)!=digest:raise ValueError('Saved material image changed')
        value={'albedo':str(image),'sha256':digest,'slot':entry['texture_slot']}
        if name in selected and selected[name]!=value:raise ValueError('Conflicting native material assignment')
        selected[name]=value
    if row.get('expand_shared_lod_albedo'):selected=expand_lod_materials(donor,selected,retained)
    native={m['name'] for m in donor['material']['materials']}
    if not selected or not set(selected)<=native or set(selected)&retained:
        raise ValueError('Empty, foreign or explicitly retained native material assignment')
    native_materials={m['name']:m for m in donor['material']['materials']}
    for name,entry in selected.items():native_albedo(native_materials[name],entry['slot'])
    result={'key':row['key'],'geometry_scope':row['geometry_scope'],
        'required_geometry_replacement':row.get('required_geometry_replacement',
            row['geometry_scope'].startswith(('qualified','humanoid'))),
        'donor_manifest':str(donor_path),'donor_manifest_sha256':sha(donor_path),
        'source_receipt':str(receipt_path),'source_receipt_sha256':sha(receipt_path),
        'material_map':str(mapping_path),'material_map_sha256':sha(mapping_path),
        'retained_native_materials':sorted(native-set(selected)),'materials':selected}
    if superseding is not None:
        result.update(material_map_receipt=str(superseding_path),material_map_receipt_sha256=sha(superseding_path))
    if row.get('native_consumer_proof'):
        proof=owned(row['native_consumer_proof'])
        if sha(proof)!=row['native_consumer_proof_sha256']:raise ValueError('Native consumer proof changed')
        result.update(native_consumer_proof=str(proof),native_consumer_proof_sha256=sha(proof))
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--label',required=True);args=ap.parse_args();guard()
    if not re.fullmatch('[a-z0-9]{1,5}',args.label):raise ValueError('Short unique batch label required')
    rows=read(owned(args.inputs));models=[pin_model(row) for row in rows];seen={};jobs=[]
    if len({m['key'] for m in models})!=len(models):raise ValueError('Duplicate model selection')
    for model in models:
        donor=read(model['donor_manifest'])
        for entry in model['materials'].values():
            identity=(model['donor_manifest_sha256'],entry['sha256'],entry['slot'])
            if identity not in seen:
                key='m'+str(len(jobs)+1).zfill(3);seen[identity]=key
                jobs.append({'key':key,'donor_manifest':model['donor_manifest'],
                    'donor_manifest_sha256':model['donor_manifest_sha256'],
                    'model':donor['resources']['model']['logical_path'],'albedo':entry['albedo'],
                    'albedo_sha256':entry['sha256'],'slot':entry['slot']})
            entry['job']=seen[identity]
    outputs={'plan':{'schema':'ccp-060-bulk-material-plan/v1','project_key':'v60'+args.label,'jobs':jobs},
             'selection':{'schema':'ccp-060-bulk-material-selection/v1','inputs':str(args.inputs),
                'inputs_sha256':sha(args.inputs),'models':models,
                'geometry_and_actor_qualification':'separate mandatory gate'}}
    for suffix,data in outputs.items():
        path=RECIPES/('bulk-material-'+args.label+'-'+suffix+'.json')
        if path.exists():
            if read(path)!=data:raise ValueError('Preserve previous pinned batch')
        else:write(path,data)
    print('PINNED',len(models),'models',len(jobs),'distinct native image jobs')


if __name__=='__main__':main()

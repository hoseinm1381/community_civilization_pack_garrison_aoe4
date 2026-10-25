"""Pin already-authored remaining humanoid/mounted/worker material inputs."""
import argparse
from pathlib import Path
from common import CFG, EXPORT, OUT, RECIPES, guard, owned, read, sha, write


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True)
    args=parser.parse_args();guard()
    if not args.label.isalnum() or len(args.label)>5:raise ValueError('Short unique selection label')
    models=[]
    for name,version in [('maa3','v1'),('maa4','v1'),('maa3_female','v1'),('maa4_female','v1'),('monk4','v2'),('repeater4','v1')]:
        receipt=OUT/'qualification/remaining_roster'/name/version/'export.json';d=read(receipt)
        metadata=d if 'donor_manifest' in d else read(d['source_receipt'])
        donor_path=Path(metadata['donor_manifest']);donor=read(donor_path)
        if sha(donor_path)!=metadata['donor_manifest_sha256']:raise ValueError('Humanoid exact donor drift')
        if d['exact_native_body_model']!=donor['resources']['model']['logical_path']:raise ValueError('Corrected body donor differs')
        image=Path(d.get('export') or d['folder'])/'albedo.png'
        if sha(image)!=d['files']['albedo.png']['sha256']:raise ValueError('Humanoid saved albedo drift')
        materials={m['name']:{'albedo':str(image),'sha256':sha(image),'slot':'albedoTexture'} for m in donor['material']['materials']}
        models.append({'key':name,'geometry_scope':'qualified_authored_geometry_required',
                       'donor_manifest':str(donor_path),'materials':materials,
                       'source_receipt':str(receipt),'source_receipt_sha256':sha(receipt)})
    for name in ('armor3','armor4','light3','light4',*[f'scout{i}' for i in range(1,5)],*[f'scout_female{i}' for i in range(1,5)]):
        receipt=OUT/'qualification/remaining_roster/mounted'/name/'v1/authoring.json';d=read(receipt)
        material_map=Path(d['material_map'])
        if sha(material_map)!=d['material_map_sha256']:raise ValueError('Mounted material map drift')
        mapping=read(material_map);materials={}
        if sha(mapping['donor_manifest'])!=mapping['donor_manifest_sha256']:raise ValueError('Mounted exact donor drift')
        for entry in mapping['groups']:
            image=owned(entry['albedo_png']);digest=sha(image)
            if not any(v['sha256']==digest and Path(v['path'])==image for v in d['albedos']):
                raise ValueError('Mounted native image does not belong to saved authoring')
            value={'albedo':str(image),'sha256':digest,'slot':entry['texture_slot']}
            existing=materials.setdefault(entry['native_material'],value)
            if existing!=value:raise ValueError('Ambiguous material image assignment')
        models.append({'key':'mounted_'+name,'geometry_scope':'compatible_stock_remix_native_geometry_unchanged',
                       'unintegrated_source_geometry_parts':True,
                       'donor_manifest':mapping['donor_manifest'],'materials':materials,
                       'source_receipt':str(receipt),'source_receipt_sha256':sha(receipt)})
    folder=EXPORT/'remaining_roster/tug_worker/v6-tug24-cargo';receipt=OUT/'qualification/remaining_roster/tug_worker/v6-tug24-cargo/export.json'
    d=read(receipt);mapping=read(folder/'material-map.json');materials={}
    if sha(folder/'material-map.json')!=d['files']['material-map.json']['sha256']:raise ValueError('Worker material map drift')
    for entry in mapping['groups']:
        if entry.get('native_unmodified_texture'):continue
        image=owned(entry['albedo_png'])
        if sha(image)!=d['files'][image.name]['sha256']:raise ValueError('Worker cargo albedo drift')
        value={'albedo':str(image),'sha256':sha(image),'slot':entry['texture_slot']}
        if entry['material_name'] in materials and materials[entry['material_name']]!=value:raise ValueError('Worker map ambiguity')
        materials[entry['material_name']]=value
    models.append({'key':'tug_worker','geometry_scope':'qualified_24_group_cargo_geometry_required',
                   'donor_manifest':d['donor_manifest'],'materials':materials,
                   'source_receipt':str(receipt),'source_receipt_sha256':sha(receipt)})
    jobs=[];by_image={}
    for model in models:
        donor_path=owned(model['donor_manifest']);donor=read(donor_path);model['donor_manifest_sha256']=sha(donor_path)
        native_names={m['name'] for m in donor['material']['materials']}
        if not set(model['materials'])<=native_names:raise ValueError('Material name absent from exact native donor')
        for name,entry in model['materials'].items():
            identity=(sha(donor_path),entry['sha256'],entry['slot'])
            if identity not in by_image:
                key='m'+str(len(jobs)+1).zfill(3);by_image[identity]=key
                jobs.append({'key':key,'donor_manifest':str(donor_path),'donor_manifest_sha256':sha(donor_path),
                    'model':donor['resources']['model']['logical_path'],'albedo':entry['albedo'],
                    'albedo_sha256':entry['sha256'],'slot':entry['slot']})
            entry['job']=by_image[identity]
    plan={'schema':'ccp-060-bulk-material-plan/v1','project_key':'v60'+args.label,'jobs':jobs}
    registry={'schema':'ccp-060-bulk-material-selection/v1','models':models,
              'geometry_and_actor_qualification':'separate mandatory gate; materials alone do not complete a design'}
    for suffix,value in [('plan',plan),('selection',registry)]:
        path=RECIPES/('bulk-material-'+args.label+'-'+suffix+'.json')
        if path.exists():
            if read(path)!=value:raise ValueError('Preserve prior bulk material selection')
        else:write(path,value)
    print('PINNED',len(models),'models',len(jobs),'distinct exact-donor image jobs')


if __name__=='__main__':main()

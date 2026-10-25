"""Build an explicit context-preserving registry from qualified 060 media receipts."""
import json
from pathlib import Path

from common import OUT, guard, owned, read, sha, write


def payload(item,member=None):
    path=owned(item['path'])
    if sha(path)!=item['sha256']:raise ValueError('Qualified media readback changed')
    return {'member':member or item['member'],'path':str(path),'sha256':item['sha256'],'bytes':path.stat().st_size}


def authored(key,pair,source):
    donor=read(pair['stock_manifest'])
    if sha(pair['stock_manifest'])!=pair['stock_manifest_sha256']:raise ValueError('Qualified donor changed')
    for field,digest in [('geometry_comparison','geometry_comparison_sha256'),
                         ('albedo_material_verification','albedo_material_verification_sha256')]:
        if sha(pair[field])!=pair[digest]:raise ValueError('Qualified geometry/material comparison changed')
    parts=[payload(pair[field]) for field in ('private_supported_variant_rgm','private_supported_variant_rgo',
                                           'private_albedo_only_rrmaterial','private_albedo_rrtex')]
    parts.append(payload(pair['native_qualified_authored_rrgeom'],pair['replacement_rrgeom_logical_path']))
    return {'key':key,'kind':'qualified_authored_humanoid_geometry_and_native_material',
            'stock_model':donor['resources']['model']['logical_path'],
            'private_model':pair['model_logical_path'],'payloads':parts,
            'selection_source':str(source),'selection_source_sha256':sha(source),
            'stock_manifest':pair['stock_manifest'],'stock_manifest_sha256':pair['stock_manifest_sha256'],
            'geometry_scope':'qualified authored native geometry; original native animation data retained',
            'rig':pair['rig'],'geometry_comparison':pair['geometry_comparison'],
            'geometry_comparison_sha256':pair['geometry_comparison_sha256'],
            'native_acceptance':False}


def compatible(key,receipt,expected=None):
    receipt=owned(receipt)
    if expected and sha(receipt)!=expected:raise ValueError('Qualified composition receipt changed')
    data=read(receipt);spec=read(data['spec']);donor=read(spec['stock_manifest'])
    if sha(data['spec'])!=data['spec_sha256'] or sha(spec['stock_manifest'])!=spec['stock_manifest_sha256']:
        raise ValueError('Composition specification or donor changed')
    parts=[payload(item) for item in data['payloads']]
    geom=next(item for item in parts if item['member'].endswith('.rrgeom'))
    if geom['sha256']!=donor['geometry']['source']['sha256']:raise ValueError('Compatible native geometry is not stock')
    return {'key':key,'kind':'qualified_compatible_stock_geometry_native_material_remix',
            'stock_model':donor['resources']['model']['logical_path'],'private_model':data['model_logical_path'],
            'payloads':parts,'selection_source':str(receipt),'selection_source_sha256':sha(receipt),
            'stock_manifest':spec['stock_manifest'],'stock_manifest_sha256':spec['stock_manifest_sha256'],
            'geometry_scope':'stock native geometry, rig, groups, palettes and LODs unchanged; separately cooked material components',
            'unqualified_added_source_geometry_excluded':True,'native_acceptance':False}


def main():
    guard();target=owned(OUT/'integration/qualified-media-selection-r1.json')
    if target.exists():raise FileExistsError('Preserve previous unified qualified selection')
    models={}
    first=OUT/'integration/private-foot-compiled-r1/bindings.json'
    pairs=[(first,read(first)['pairs'])]
    for path in ('civilian-media-primary-r2.json','humanoid-media-b01-r2.json','humanoid-monk3-media-b03-r1.json'):
        source=OUT/'integration'/path;pairs.append((source,read(source)))
    for source,entries in pairs:
        for key,pair in entries.items():
            if key in models:raise ValueError('Ambiguous context-specific humanoid selection')
            models[key]=authored(key,pair,source)
    first_components=read(OUT/'integration/material-components-b01/registry.json')
    for key,entry in first_components.items():
        if key=='tug_worker':continue # Historical custom-cargo requirement superseded explicitly below.
        if entry['required_geometry_replacement']:raise ValueError('Unqualified strong geometry is not a compatible fallback')
        models[key]=compatible(key,entry['receipt'],entry['sha256'])
    for key,entry in read(OUT/'integration/material-components-b03/registry.json')['models'].items():
        if key=='monk3':continue # The qualified authored pair, above, replaces this stock-geometry material source.
        if key in models or entry['required_geometry_replacement']:raise ValueError('Duplicate or unqualified material-only geometry selection')
        models[key]=compatible(key,entry['receipt'],entry['receipt_sha256'])
    tug=OUT/'integration/tug-worker-stock-compatible-r1/media.json';data=read(tug)
    models['tug_worker']=compatible('tug_worker',tug)
    models['tug_worker'].update(target_actor=data['target_actor'],authorization=data['authorization'],
                               custom_crate_geometry=data['custom_crate_geometry'])
    proof_paths=[OUT/'qualification/native-rgo-controls'/name for name in ('proof-first49.json','proof-b03.json')]
    proof_rows=[row for path in proof_paths for row in read(path)['rows']]
    unique={}
    for key,model in models.items():
        rgo=next(p for p in model['payloads'] if p['member'].endswith('.rgo'))
        if not any(r['donor_manifest_sha256']==model['stock_manifest_sha256'] and
                   r['private_rgo']['sha256']==rgo['sha256'] and r['native_rgo_byte_identical'] for r in proof_rows):
            raise ValueError('No independent exact-original RGO proof: '+key)
        for item in model['payloads']:
            previous=unique.get(item['member'].casefold())
            if previous and (previous['member'],previous['sha256'],previous['bytes'])!=(item['member'],item['sha256'],item['bytes']):
                raise ValueError('Conflicting shared native payload identity')
            unique[item['member'].casefold()]=item
    write(target,{'schema':'ccp-060-unified-qualified-media-selection/v1',
        'status':'explicit_qualified_media_ready_for_context_specific_private_binding',
        'models':models,'model_count':len(models),'unique_payload_count':len(unique),
        'independent_rgo_proofs':[{'path':str(p),'sha256':sha(p)} for p in proof_paths],
        'context_rules':['MAA III and IV share stock donor but require distinct authored tier selections',
                         'MAA gender-specific models remain distinct',
                         'Repeater IV requires its own registered list, separate from Crossbow IV',
                         'Only actor2 is authorized to change cow owner to complete native Tugh worker',
                         'No failed custom-crate RRGeom may be selected'],
        'native_appearance_behavior_multiplayer':False,
        'coverage_limit':'Media registry is not full consumer/crew/attachment coverage or activation proof'})
    print(json.dumps({'registry':str(target),'models':len(models),'unique_payloads':len(unique)}))


if __name__=='__main__':main()

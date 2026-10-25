"""Resolve saved English siege art candidates against exact reachable Chinese native slots."""
import json
from pathlib import Path

from common import OUT, RECIPES, TOOLS, guard, owned, read, sha, write
from compiled_visual_delta_060 import rgd


def main():
    guard();input_path=TOOLS/'unresolved-siege-donor-materials.json';rows=read(input_path)
    native_path=OUT/'integration/private-land-graph/native-reference-plan-v1/plan.json';native=read(native_path)
    hash_path=OUT/'inventory/stock-reference-closure-direct-r2/all-member-hashes.json';hashes=read(hash_path)
    target=owned(OUT/'qualification/siege-exact-consumers-r1/report.json')
    if target.exists():raise FileExistsError('Preserve prior siege consumer proof')
    documents=[]
    for resource in native['resources']:
        path=Path(resource['path'])
        if sha(path)!=resource['sha256'] or resource['sha256']!=hashes[resource['member']]['sha256']:
            raise ValueError('Reachable native consumer differs from complete current stock audit')
        data=path.read_bytes();document=rgd.read(data)
        if rgd.write(document)!=data:raise ValueError('Native consumer codec does not roundtrip')
        documents.append((resource,document))
    qualified=[]
    for row in rows:
        mapping_path=owned(row['material_map']);mapping=read(mapping_path)
        donor_path=owned(mapping['donor_manifest']);donor=read(donor_path)
        if sha(donor_path)!=mapping['donor_manifest_sha256']:raise ValueError('Saved exact siege donor changed')
        model=donor['resources']['model']['logical_path'].removesuffix('.rgm').replace('\\','/')
        if (mapping.get('exact_native_model') or mapping.get('exact_donor_model')).removesuffix('.rgm').replace('\\','/')!=model:
            raise ValueError('Saved siege art belongs to a different donor')
        matches=[]
        for resource,document in documents:
            for path,node in rgd.flatten(document.nodes):
                if node.kind!='CString' or not (node.key=='alternate_sua' or node.key.startswith('animator')):
                    continue
                if node.value.replace('\\','/').removesuffix('.rgm')!=model:continue
                matches.append({'member':resource['member'],'member_sha256':resource['sha256'],
                                'leaf':path,'field':node.key,'before_value':node.value})
        if not matches:raise ValueError('Saved siege model has no exact reachable native visual slot: '+row['key'])
        qualified.append({'key':row['key'],'model':model+'.rgm','donor_manifest_sha256':sha(donor_path),
                          'matches':matches,'native_runtime':'unverified'})
    proof={'schema':'ccp-060-siege-exact-consumer-qualification/v1',
        'status':'all_four_saved_models_exactly_match_reachable_native_visual_slots',
        'candidate_registry_sha256':sha(input_path),'native_reference_plan_sha256':sha(native_path),
        'full_stock_member_hashes_sha256':sha(hash_path),'models':qualified,
        'scope':'Private compatible stock material remix; stock geometry, native animation owners and moving mechanisms retained',
        'material_cook_and_private_binding':'separate mandatory gates','native_acceptance':False}
    write(target,proof)
    output=[{**row,'geometry_scope':'compatible stock siege geometry; exact native consumer resolved; mechanisms retained',
             'native_consumer_proof':str(target),'native_consumer_proof_sha256':sha(target)} for row in rows]
    write(RECIPES/'resolved-siege-material-inputs-r1.json',output)
    print(json.dumps({'proof':str(target),'matches':{r['key']:len(r['matches']) for r in qualified}}))


if __name__=='__main__':main()

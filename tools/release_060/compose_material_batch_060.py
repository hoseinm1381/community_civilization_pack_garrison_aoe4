"""Compose exact separately cooked native material components for a pinned batch."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from common import OUT, TOOLS, guard, owned, read, sha, write


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--selection',type=Path,required=True)
    ap.add_argument('--batch',type=Path,required=True);ap.add_argument('--label',required=True)
    args=ap.parse_args();guard()
    if not re.fullmatch('[a-z0-9-]{1,30}',args.label):raise ValueError('Safe unique composition label required')
    selection=read(owned(args.selection));batch=read(owned(args.batch))
    if batch['status']!='all_bulk_variants_independently_readback_qualified':raise ValueError('Fresh successful batch required')
    if sha(batch['archive'])!=batch['archive_sha256']:raise ValueError('Qualified native archive changed')
    plan=read(batch['plan'])
    if sha(batch['plan'])!=batch['plan_sha256']:raise ValueError('Native batch plan changed')
    by_job={j['key']:j for j in plan['jobs']};specs=[]
    folder=owned(OUT/'integration'/('material-components-'+args.label))
    if folder.exists():raise FileExistsError('Preserve previous material composition batch')
    for model in selection['models']:
        if not re.fullmatch('[a-zA-Z0-9_]+',model['key']):raise ValueError('Unsafe model key')
        if sha(model['source_receipt'])!=model['source_receipt_sha256'] or sha(model['donor_manifest'])!=model['donor_manifest_sha256']:
            raise ValueError('Pinned material source/donor changed')
        components={};slots=set()
        for name,entry in model['materials'].items():
            job=by_job[entry['job']];report_ref=batch['reports'][entry['job']]
            report=owned(report_ref['path']);verification=read(report);cook_path=report.parent/'cook.json';cook=read(cook_path)
            if (job['donor_manifest_sha256']!=model['donor_manifest_sha256']
                    or job['albedo_sha256']!=entry['sha256'] or job['slot']!=entry['slot']
                    or sha(entry['albedo'])!=entry['sha256']
                    or sha(report)!=report_ref['sha256'] or sha(cook_path)!=verification['cook_receipt_sha256']
                    or cook['source_image_sha256']!=entry['sha256']):
                raise ValueError('Native component does not belong to selected saved material image')
            components[name]={'verification':str(report),'verification_sha256':sha(report)};slots.add(entry['slot'])
        if len(slots)!=1:raise ValueError('Mixed native albedo slot classes require a separately qualified composer')
        destination=folder/model['key']
        specs.append((model,destination,{'schema':'ccp-060-native-material-components/v1',
            'stock_manifest':model['donor_manifest'],'stock_manifest_sha256':model['donor_manifest_sha256'],
            'albedo_slot':slots.pop(),'materials':components,'base_material':next(iter(components)),
            'output':str(destination/'body.rrmaterial'),'receipt':str(destination/'composition.json')}))
    # Every source/component selection has been checked before any composition write.
    registry={}
    for model,destination,spec in specs:
        spec_path=destination/'spec.json';write(spec_path,spec)
        result=subprocess.run([sys.executable,'-B',str(TOOLS/'material_components_060.py'),'--spec',str(spec_path)],
                              capture_output=True,text=True,timeout=120)
        (destination/'compose.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError('Native material composition failed; diagnostics preserved: '+model['key'])
        receipt=destination/'composition.json';data=read(receipt)
        registry[model['key']]={'receipt':str(receipt),'receipt_sha256':sha(receipt),
            'model_logical_path':data['model_logical_path'],'geometry_scope':model['geometry_scope'],
            'required_geometry_replacement':model.get('required_geometry_replacement',
                model['geometry_scope'].startswith(('qualified','humanoid'))),
            'payloads':data['payloads']}
        print('COMPOSED',model['key'],flush=True)
    write(folder/'registry.json',{'schema':'ccp-060-material-component-registry/v1',
        'selection':str(args.selection),'selection_sha256':sha(args.selection),
        'batch':str(args.batch),'batch_sha256':sha(args.batch),'models':registry,
        'native_acceptance':False})
    print(json.dumps({'registry':str(folder/'registry.json'),'models':len(registry)}))


if __name__=='__main__':main()

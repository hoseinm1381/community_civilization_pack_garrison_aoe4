"""Cook exact-donor albedo variants for retained final source exports.

Run only after explicit native scheduler handoff. Every individual cook also
uses the established byte lock. Existing successful receipts are hash-verified;
failed or incomplete projects are retained and refused rather than overwritten.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from common import CFG, OUT, TOOLS, guard, owned, read, sha, write

TARGET = OUT/'qualification/material-batch-continuation'


def make_plan(group='primary'):
    sources = [('spear'+str(i)+'-v3', 'v60ms'+str(i)) for i in range(1,5)]
    sources += [(slug+'-v5b', 'v60mr'+str(i)) for i,slug in enumerate(
        ('archer3','archer4','crossbow3','crossbow4','handcannon4'),1)]
    sources += [('villager-'+gender+str(i)+'-v2', 'v60mv'+gender[0]+str(i))
                for gender in ('male','female') for i in range(1,5)]
    if group=='remaining-humanoids':
        sources=[('maa3-v1','v60mxm3'),('maa4-v1','v60mxm4'),
                 ('monk4-v2','v60mxmk'),('repeater4-v1','v60mxrp')]
    elif group!='primary':raise ValueError('Unknown material batch group')
    result = []
    for geometry_slug,key in sources:
        spec_path = OUT/'authored-geometry'/geometry_slug/'spec.json'
        spec = read(spec_path)
        donor_path = Path(spec['stock_manifest'])
        donor = read(donor_path)
        if sha(donor_path) != spec['stock_manifest_sha256']:
            raise ValueError('Exact donor changed: '+geometry_slug)
        image = owned(Path(spec['albedo']))
        receipt_path = Path(spec['export_receipt'])
        receipt = read(receipt_path)
        digest = receipt.get('albedo_sha256') or receipt['files']['albedo.png']['sha256']
        if sha(image) != digest:
            raise ValueError('Saved native albedo changed: '+geometry_slug)
        result.append({'geometry_slug':geometry_slug, 'key':key,
                       'donor_manifest':str(donor_path), 'donor_manifest_sha256':sha(donor_path),
                       'model':donor['resources']['model']['logical_path'],
                       'albedo':str(image), 'albedo_sha256':digest,
                       'source_export_receipt':str(receipt_path), 'source_export_receipt_sha256':sha(receipt_path),
                       'verification':str(OUT/'qualification/albedo-variants'/key/'material-verification.json')})
    return {'schema':'ccp-060-material-batch-continuation/v1', 'jobs':result,
            'scope':'native albedo-only cook/readback; no actor activation or final integration'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan','run'))
    parser.add_argument('--group',choices=('primary','remaining-humanoids'),default='primary')
    args=parser.parse_args();guard()
    target=TARGET if args.group=='primary' else TARGET.with_name('material-batch-remaining-humanoids')
    plan=make_plan(args.group);plan_path=target/'plan.json'
    if plan_path.exists():
        if read(plan_path)!=plan:raise ValueError('Preserve existing pinned material plan')
    else:write(plan_path,plan)
    if args.action=='plan':
        print(json.dumps({'plan':str(plan_path),'jobs':len(plan['jobs'])}));return
    for job in plan['jobs']:
        report=Path(job['verification'])
        cook_path=report.with_name('cook.json')
        if report.exists():
            material=read(report);cook=read(cook_path)
            if (material['status']!='albedo_only_all_other_material_chunks_exact' or
                material['donor_manifest_sha256']!=job['donor_manifest_sha256'] or
                cook['source_image_sha256']!=job['albedo_sha256'] or
                sha(material['archive'])!=material['archive_sha256'] or
                any(sha(v['path'])!=v['sha256'] for v in material['extracted'].values())):
                raise ValueError('Existing material verification drift: '+job['key'])
            print('VERIFIED EXISTING '+job['geometry_slug'],flush=True);continue
        if cook_path.exists():raise FileExistsError('Retained incomplete native attempt: '+str(cook_path))
        commands=[
            [CFG['python'],'-B',str(TOOLS/'cook_unit_albedo_variant.py'),'--key',job['key'],
             '--model',job['model'],'--albedo',job['albedo'],'--sha256',job['albedo_sha256']],
            ['py','-3.13','-B',str(TOOLS/'verify_unit_albedo_variant.py'),
             '--cook',str(cook_path),'--donor',job['donor_manifest']]]
        for index,command in enumerate(commands):
            log=owned(target/(job['key']+'-'+str(index)+'.log'))
            if log.exists():raise FileExistsError(log)
            run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1500)
            log.parent.mkdir(parents=True,exist_ok=True)
            log.write_text('EXIT '+str(run.returncode)+'\n'+run.stdout+'\n'+run.stderr,encoding='utf-8')
            if run.returncode:raise RuntimeError('Native material batch stopped; '+str(log))
        print('QUALIFIED '+job['geometry_slug']+' '+str(report),flush=True)
    write(target/'complete.json',{'schema':'ccp-060-material-batch-complete/v1',
        'plan_sha256':sha(plan_path),'status':str(len(plan['jobs']))+'_exact_donor_albedo_variants_qualified',
        'reports':{x['geometry_slug']:{'path':x['verification'],'sha256':sha(x['verification'])} for x in plan['jobs']}})


if __name__=='__main__':main()

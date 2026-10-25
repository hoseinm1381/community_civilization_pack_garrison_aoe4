"""Read-only 0.5.0 monastery selector and geometry anatomy probe."""
from __future__ import annotations
import collections, json, struct, sys
from pathlib import Path
from common import ROOT, OUT, guarded, read, write, sha, PRIOR
sys.path.insert(0, str(ROOT/'tools/castle_next'))
from building_selectors import source_map, rc, parse_set, parse_state

def inspect(age):
    donor=read(ROOT/'output/castle_next/donors/donor-manifest.json')['donors'][f'monastery{age:02}']
    names,meta=source_map(donor)
    groups=donor['decoded_static']['geometry']['groups']
    summary=[]
    for index,(group,source_names) in enumerate(zip(groups,names)):
        byname=collections.defaultdict(lambda:{'triangles':0,'lo':[1e9]*3,'hi':[-1e9]*3})
        for triangle,name in zip(group['triangles'],source_names):
            row=byname[name];row['triangles']+=1
            for vi in triangle:
                p=group['positions'][vi]
                for axis in range(3):row['lo'][axis]=min(row['lo'][axis],p[axis]);row['hi'][axis]=max(row['hi'][axis],p[axis])
        summary.append({'group':index,'material':group['preview_material'],'vertices':len(group['positions']),
                        'triangles':len(group['triangles']),'sources':dict(byname)})
    model=ROOT/f'art/exports/castle_next/buildings/monastery/age{age:02}/vn_model.rgm'
    chunks=list(rc.walk(rc.load(model).roots))
    sets=[parse_set(c.payload) for c in chunks if c.tag==b'MSD ' and len(c.payload)>4]
    states=[parse_state(c.payload) for c in chunks if c.tag==b'CNBP']
    memberships=collections.defaultdict(list)
    for i,row in enumerate(sets):
        for name in row['members']:memberships[name].append({'selector':row['name'],'states':states[i] if i<len(states) else []})
    return {'age':age,'groups':summary,'memberships':dict(memberships),'stock_selector_names':meta['all_selector_names'],
            'private_selector_names':sorted(memberships),'orphaned':sorted(set(meta['all_selector_names'])-set(memberships)),
            'model_sha256':sha(model)}

if __name__=='__main__':
    guarded(); results=[inspect(age) for age in (3,4)]
    write(OUT/'monastery/probe.json',{'ages':results})
    for row in results:
        print('AGE',row['age'],'ORPHANED',len(row['orphaned']),row['orphaned'])
        for group in row['groups']:
            print('GROUP',group['group'],group['material'],group['vertices'],group['triangles'],len(group['sources']))
            for name,stat in group['sources'].items():
                if group['material'] in ('roof','extra'):
                    print(' ',name,stat['triangles'],[round(x,2) for x in stat['lo']],[round(x,2) for x in stat['hi']])

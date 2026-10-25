"""Numerical stage-0 footing and roof-support audit for the 12 private stamps."""
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/release_040/buildings/details'
rows=[]
for family in ('blacksmith','stable','archery_range','market'):
    for age in (2,3,4):
        receipt=json.loads((OUT/family/f'age{age:02}'/'source.json').read_text(encoding='utf8'))
        contacts=receipt['contact']['roof_post_contacts']
        decorative=receipt['contact']['decorative_joints']
        assert len(contacts)>=4 and receipt['contact']['model_translation']==[0.0,0.0,0.0]
        assert len(decorative)>=len(contacts)*3
        assert all(min(j['axis_overlap_m'])>.005 for j in decorative)
        projection=json.loads((ROOT/f'art/authoring/buildings_040/{family}/vn_{family}_age{age:02}-projection.json').read_text(encoding='utf8'))
        points=np.concatenate([np.asarray(g['positions'],dtype=float) for g in projection['geometry']['groups']])
        base_samples=[];ground_near=[]
        for contact in contacts:
            assert .005<=contact['post_support_overlap_m']<=.02
            assert .005<=contact['support_roof_overlap_m']<=.02
            assert contact['support_bottom_z']<=contact['post_top_z']
            assert contact['support_top_z']>=contact['roof_underside_z']
            x,y=contact['x'],contact['y']
            distance=np.linalg.norm(points[:,:2]-[x,y],axis=1)
            nearest=float(distance.min())
            nearby=points[(distance<.55)&(points[:,2]<-.5),2]
            base=float(nearby.min()) if len(nearby) else None
            if base is not None:base_samples.append(base)
            ground_near.append({'post_index':contact['post_index'],'nearest_stock_xy_m':nearest,
                                'stock_facade_base_z':base,'post_bottom_z':contact['post_bottom_z'],
                                'standalone_in_stock_plan':base is None})
        assert base_samples,(family,age,'no donor footing samples')
        donor_base=float(np.median(base_samples))
        post_base=contacts[0]['post_bottom_z']
        delta=post_base-donor_base
        assert abs(delta)<=.20,(family,age,post_base,donor_base)
        rows.append({'family':family,'age':age,'model_translation':[0,0,0],
                     'post_count':len(contacts),'roof_support_contacts_passed':True,
                     'decorative_joint_count':len(decorative),'decorative_joints_passed':True,
                     'minimum_decorative_axis_overlap_m':min(min(j['axis_overlap_m']) for j in decorative),
                     'minimum_post_support_overlap_m':min(c['post_support_overlap_m'] for c in contacts),
                     'minimum_support_roof_overlap_m':min(c['support_roof_overlap_m'] for c in contacts),
                     'post_footing_z':post_base,'adjacent_stock_base_median_z':donor_base,
                     'footing_vs_adjacent_stock_base_m':delta,'stock_proximity':ground_near})
assert len(rows)==12
target=OUT/'contact-audit.json'
target.write_text(json.dumps({'schema':'ccp.release040.building-detail-contact/v1','status':'passed',
                              'limits':{'contact_overlap_m':[.005,.02],'maximum_footing_difference_m':.20},
                              'models':rows},indent=2)+'\n',encoding='utf8')
print('CONTACT_AUDIT_PASS',len(rows),'range',min(r['footing_vs_adjacent_stock_base_m'] for r in rows),
      max(r['footing_vs_adjacent_stock_base_m'] for r in rows))

"""Derive companion flag poses from measured Blender support and native stamps."""
from pathlib import Path
import argparse,hashlib,json,math
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/release_075/owner_colour'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rotate(q,v):
 x,y,z,w=q; n=math.sqrt(sum(a*a for a in q));x,y,z,w=[a/n for a in q]
 a,b,c=v
 return [(1-2*y*y-2*z*z)*a+(2*x*y-2*z*w)*b+(2*x*z+2*y*w)*c,
 (2*x*y+2*z*w)*a+(1-2*x*x-2*z*z)*b+(2*y*z-2*x*w)*c,
 (2*x*z-2*y*w)*a+(2*y*z+2*x*w)*b+(1-2*x*x-2*y*y)*c]
def main(output):
 stamps=json.loads((ROOT/'output/release_075/inspection/stamps.json').read_text())
 current=json.loads((ROOT/'output/release_075/inspection/current-consumers.json').read_text())
 poses={}
 for family in ('citadel','hq','ministry','pho_minh','one_pillar','garden','foundry'):
  path=OUT/'anchors'/f'{family}.json'
  if not path.exists():path=ROOT/'output/release_075/art'/family/({'garden':'r4','foundry':'r5','one_pillar':'r4'}.get(family,'r3'))/'flag-anchor.json'
  anchor=json.loads(path.read_text());assert anchor['no_roof_above']
  if 'source_sha256' in anchor:assert sha(anchor['source'])==anchor['source_sha256']
  p=anchor.get('anchor_source_local',anchor['anchor_model_local']);fit=anchor['export_fit']
  b=[p[i]*fit['scale'][i]+fit['translation'][i] for i in range(3)]
  if 'anchor_source_local' in anchor:assert max(abs(b[i]-anchor['anchor_model_local'][i]) for i in range(3))<1e-7
  n=[-b[0],b[2],-b[1]]
  models=current['families'][family]['all_variant_models']
  vs=[(s,v) for s in stamps[family] for v in s['visuals'] if v['model'] in models]
  assert vs and all(v['transform']==vs[0][1]['transform'] for s,v in vs)
  t=vs[0][1]['transform'];q=t[:4]
  support=[a+t[4+i] for i,a in enumerate(rotate(q,[n[i]*t[7+i] for i in range(3)]))]
  scale=anchor.get('suggested_flag_visual_scale',2.0 if family=='one_pillar' else 1.5)
  # Keep vertical; shared yaw uses Y/W quaternion components only.
  yaw=[0,q[1],0,q[3]];mag=math.sqrt(sum(a*a for a in yaw));yaw=[a/mag for a in yaw]
  translation=[support[0],support[1]+.1484375*scale,support[2]]
  poses[family]={'native_translation':translation,'native_quaternion':yaw,'scale':scale,
   'contact_verified':True,'support_native_y':support[1],'support_native_point':support,
   'support_evidence':str(path),'support_evidence_sha256':sha(path),'source_anchor':p,
   'export_fit':fit,'export_local_blender':b,'export_local_native':n,'body_stamp_transform':t,
   'body_stamps':[{'member':s['member'],'sha256':s['sha256']} for s,v in vs],
   'pole_bottom_native_y':-.1484375,'contact_error':translation[1]-.1484375*scale-support[1],
   'actor_scale':'Inherited by body and companion together, not baked again',
   'native_appearance_and_state_propagation':'Pending final candidate game test'}
 target=OUT/output;assert not target.exists(),'Preserve previous placements'
 target.write_text(json.dumps(poses,indent=2)+'\n');print(target)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',default='placements.json');a=p.parse_args();main(a.output)

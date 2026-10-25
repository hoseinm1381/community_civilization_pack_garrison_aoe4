"""Prepare explicit partial static reference recipes; no Blender execution."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/release_075/comparators'


def main():
 closure=json.loads((OUT/'closure.json').read_text())
 recipes=[]
 for key in ('palace','academy','clocktower','white_tower'):
  choice=next(r for r in closure['choices'] if r['id']==key)
  stamps=[s for a in choice['attachments'] for s in a['stamps']]
  main_stamp=next(s for s in stamps if s['member'].startswith('art/stamps/civ_'))
  principal=next(i for i in main_stamp['visual_instances'] if '/structures/' in i['model'] and '/debris/' not in i['model'])
  included=[];excluded=[]
  for stamp in stamps:
   for instance in stamp['visual_instances']:
    item={**instance,'stamp':stamp['member']}
    model=closure['models'][instance['model']]
    if stamp is not main_stamp:
     excluded.append({**item,'reason':'outskirts attachment placement/selection not proved; omitted rather than visually guessed'});continue
    if model['status']!='bounded_model_geometry':
     excluded.append({**item,'reason':'no qualified geometry mapping'});continue
    metric=model['metric'];is_principal=instance is principal
    if not is_principal and (metric['lower']!=metric['upper'] or metric['lower']==0):
     excluded.append({**item,'reason':'prop lifecycle/visibility ambiguous or no proven healthy triangles'});continue
    manifest=Path(model['decode_manifest'])
    if hashlib.sha256(manifest.read_bytes()).hexdigest()!=model['decode_manifest_sha256']:
     raise ValueError('Decode manifest drift')
    included.append({**item,'principal':is_principal,'manifest':str(manifest),
                     'manifest_sha256':model['decode_manifest_sha256'],
                     'native_rgm':model['native_rgm'],'native_rgm_sha256':model['rgm_sha256'],
                     'selector_metric':metric,'render_triangle_target':metric['lower']})
  if not any(i['principal'] for i in included):raise ValueError('Principal unresolved')
  recipe={'schema':'ccp075-partial-static-reference-render/v1','reference':key,'role':choice['role'],
          'scope':'Principal proven healthy/unconditional triangles plus only unambiguous static props in its main stamp. Ambiguous debris, unknown selectors, and all outskirts omitted.',
          'native_render_proof':False,'material_scope':'Installed Garrison decoded layered preview materials; not native shader parity.',
          'included':included,'excluded':excluded,
          'render_settings':{'resolution':[1100,850],'samples':16,'view_transform':'AgX','world':[.3,.3,.3],
                             'views':{'iso':[1,-1,.9],'gameplay':[1,-1,1.35],'front':[0,-1,.02]},
                             'scale':'Each panel independently normalized to object bounding span; not a physical-size comparison.'}}
  folder=OUT/'render-recipes';folder.mkdir(parents=True,exist_ok=True)
  dest=folder/(key+'.json');dest.write_text(json.dumps(recipe,indent=2)+'\n')
  recipes.append({'reference':key,'recipe':str(dest),'included_instances':len(included),
                  'excluded_instances':len(excluded),'proven_triangles':sum(i['render_triangle_target'] for i in included)})
 (OUT/'render-preparation.json').write_text(json.dumps({'status':'scripts_prepared_not_Blender_executed','recipes':recipes},indent=2)+'\n')
 print(json.dumps(recipes))


if __name__=='__main__':main()

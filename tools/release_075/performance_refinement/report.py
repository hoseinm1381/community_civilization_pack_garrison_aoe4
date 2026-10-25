"""Bounded read-only review of unresolved Garden/Foundry healthy-state costs."""
from pathlib import Path
import collections,hashlib,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
C=ROOT/'output/release_075/comparators'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 b=json.loads((C/'target-bounds.json').read_text());models=json.loads((C/'target-models.json').read_text())
 cases=[]
 for family in ('garden','foundry'):
  for case in b['families'][family]['cases']:
   groups=collections.defaultdict(lambda:{'triangles':0,'instances':0,'models':set(),'unresolved_predicate_properties':set()})
   for inst in case['model_instances']:
    model=inst['model'];category='debris' if '/debris/' in model else ('construction' if '/scaffolding_' in model or '/buildpile_' in model else 'other')
    g=groups[category];g['triangles']+=inst['upper'];g['instances']+=1;g['models'].add(model)
    for selector in models.get(model,{}).get('metric',{}).get('selector_sets',[]):
     for pred in selector.get('unknown_predicates',[]):
      if pred.get('property'):g['unresolved_predicate_properties'].add(pred['property'])
   for g in groups.values():
    g['models']=sorted(g['models']);g['unresolved_predicate_properties']=sorted(g['unresolved_predicate_properties'])
   assert sum(g['triangles'] for g in groups.values())==case['retained_native_mesh_triangle_upper']
   cases.append({'family':family,'actor':case['actor'],'branch':case['branch'],'retained_upper':case['retained_native_mesh_triangle_upper'],'categories':dict(groups),'healthy_exclusions_proven':[]})
 schema=ROOT/'output/release_075/schema/reflect.db';r=ET.parse(schema).getroot()
 enums={x.get('Name'):{f.get('Name'):f.get('EnumValue') for f in x.findall('Fields/ReflectField')} for x in r if x.get('Name') in ('rr::ComparisonFunc','StateModels::ComparisonOperator')}
 result={'status':'unresolved_healthy_state_semantics_no_new_budget_pass','input_hashes':{str(p.relative_to(ROOT)):sha(p) for p in (C/'target-bounds.json',C/'target-models.json',schema)},'cases':cases,'schema_enum_candidates':enums,
 'blockers':['Debris mesh selectors depend on show_debris_piles and remove_debris_piles; their values for each healthy parent actor and state propagation are not established by the RGM selector alone.',
 'Campaign Foundry scaffolding selectors depend on scaffolding_build_stage. No validated mapping from completed parent lifecycle to this variable has been demonstrated.',
 'Current reflected enums include rr::ComparisonFunc and StateModels::ComparisonOperator, but no verified type binding identifies either as the legacy RGM CNBP operand/comparison encoding. Similar numeric values are not a type proof.',
 'A resource name such as debris or scaffolding is not visibility evidence. No native retained geometry is excluded on naming grounds.',
 'Upper target bounds exceeding a principal-only official lower bound neither prove excess nor establish compliance. Exact healthy state evaluation and comparable full compounds remain needed.'],
 'result':'Existing conservative bounds retained unchanged. No subtraction or performance pass is authorized by this read-only refinement.',
 'native_operations':'None; existing decoded evidence and current reflected schema read only.'}
 (HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'cases':[(x['family'],x['branch'],{k:v['triangles'] for k,v in x['categories'].items()}) for x in cases]}))
if __name__=='__main__':main()

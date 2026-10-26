"""Generate a fail-closed speed-probe admission set from current effective EBPS.
No gameplay edits or new engine APIs. Refresh after unit additions or game updates.
"""
import collections,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/release_085';GUID='b7fcea91257b408fb9e8ae4d8bc402e1'
sys.path.insert(0,str(ROOT/'tools/release_072/vendor'));import extension_audit as audit

def generate():
 cache=json.loads((OUT/'088-official-extensions.json').read_text());local=audit.load_local(ROOT)
 # ReferenceAttributes removal IDs contain comma-space delimiters. The
 # historical identity auditor does not trim them; normalize working records
 # without changing its frozen source or the installed official evidence.
 for record in [*cache['records'].values(),*local.values()]:
  for scope in record.values():
   settings=scope.get('list')
   if settings and 'removedIds' in settings:settings['removedIds']=','.join(v.strip() for v in settings['removedIds'].split(','))
 audit.ROOT=ROOT;audit.GUID=GUID;resolver=audit.Resolver(local,cache['records']);assert not resolver.audit()
 names=collections.defaultdict(list);facts=[]
 for key,record in {**cache['records'],**local}.items():
  if not key.startswith('ebps\\'):continue
  values=[]
  for variant in set(record)|{'default','campaign'}:
   present=any(n.get('value')==r'ebpextensions\moving_ext' for n in resolver.effective(key,variant,key in local))
   values.append(present)
  admitted=all(values);stem=key.split('\\')[-1];names[stem].append(admitted)
  if key in local:names[GUID+':'+stem].append(admitted)
  facts.append({'key':key,'moving_in_all_variants':admitted})
 derived=json.loads((ROOT/'output/release_084/integration/voice-identities-complete.json').read_text())
 for row in derived['identities']:
  if row['category']!='ebps':continue
  key=row['source'].removeprefix('attrib/').removesuffix('.rgd').replace('/','\\')
  original=cache['records'].get(key,local.get(key));assert original is not None,key
  admitted=all(any(n.get('value')==r'ebpextensions\moving_ext' for n in resolver.effective(key,v,key in local)) for v in set(original)|{'default','campaign'})
  for name in (row['name'],GUID+':'+row['name']):names[name].append(admitted)
 allowed=sorted(k for k,v in names.items() if all(v));assert 'unit_trade_camel_abb_ha_01_viz' not in allowed
 for name in ('unit_villager_1_chi',GUID+':vn_unit_skirmisher_2_vit',GUID+':vn084_e_unit_culverin_4_chi'):assert name in allowed,name
 block='-- BEGIN GENERATED 088 MOBILITY GUARD\n-- Verified moving_ext in every supported parent/variant; regenerate with\n-- tools/release_088/generate_mobility.py after adding units or updating the game.\n-- Unknown/scenery/weapon blueprints never reach the fatal native speed accessor.\nlocal knownMoving = {}\nfor name in string.gmatch([[\n'+'\n'.join(allowed)+'\n]], "%S+") do knownMoving[name] = true end\n-- END GENERATED 088 MOBILITY GUARD\n'
 evidence={'official_archive':cache['archive'],'official_archive_sha256':cache['archive_sha256'],'admitted_names':len(allowed),'effective_blueprints':len(facts),'derived_identities_sha256':hashlib.sha256((ROOT/'output/release_084/integration/voice-identities-complete.json').read_bytes()).hexdigest(),'catalogue_sha256':hashlib.sha256(block.encode()).hexdigest()}
 return block,evidence
if __name__=='__main__':
 block,evidence=generate();p=ROOT/'assets/scar/vietnam/flooded_citadel.scar';s=p.read_text(encoding='utf-8')
 if '-- BEGIN GENERATED 088 MOBILITY GUARD' in s:s=re.sub(r'-- BEGIN GENERATED 088 MOBILITY GUARD.*?-- END GENERATED 088 MOBILITY GUARD\n',lambda m:block,s,flags=re.S)
 else:s=s.replace('import("modifiers.scar")\n','import("modifiers.scar")\n\n'+block)
 p.write_text(s,encoding='utf-8');(OUT/'088-mobility-proof.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8');print(json.dumps(evidence))

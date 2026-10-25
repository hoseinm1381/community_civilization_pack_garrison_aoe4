from common import *
from inventory import official
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd
BASE=ROOT/'output/release_075/candidates/review-v1'
def main():
 guard();proof=read(BASE/'verification.json');assert sha(BASE/'community_civilization_pack.sga')==proof['sga_sha256']=='aaca1bd8cb3d09a44cbe091816817e5bb247944f204affa5b04e6af52f56b022'
 records={}
 paths=[p for p in (BASE/'readback/attrib').rglob('*.rgd') if any(s in p.name for s in ('skirmisher','water_buffalo','war_elephant_1_vit'))]
 for age in (2,3,4):
  for m in (f'attachments/attachment_lists/races/core/weapons/wpn_range_javelin_{age}',f'attachments/attachment_lists/civilizations/malian/units/tier{age}_javelin_mal',f'weapon/races/common/ranged/weapon_javelin_{age}'):
   paths.append(official('attrib/'+m+'.rgd'))
 paths.append(official('attrib/attachments/attachment_lists/gaia/animals/gaia_herdable_cattle_mal.rgd'))
 for p in paths:
  doc=rgd.read(p.read_bytes());assert rgd.write(doc)==p.read_bytes()
  rows=[{'path':n,'kind':v.kind,'value':v.value} for n,v in rgd.flatten(doc.nodes) if v.kind not in ('List','List2') and (any(s in n for s in ('animator','attachment','projectile','pbgid','parent_pbg','scale','tier_group')) or (v.kind=='CString' and any(s in str(v.value) for s in ('javelin','buffalo'))))]
  records[str(p)]=rows
 write(OUT/'integration/inspection.json',records)
 print(json.dumps(records,indent=2))
if __name__=='__main__':main()

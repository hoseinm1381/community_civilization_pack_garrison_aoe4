"""Freeze the explicitly reviewed revisions; never infer a final from timestamps."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main(flags,placements,target):
 revisions={
  'citadel':('v1','citadel/imperial_citadel.blend','citadel'),
  'hq':('v1','hq/resistance_hq.blend','hq'),
  'ministry':('r3-v1','ministry/r3/ministry.blend','ministry/r3'),
  'pho_minh':('r3-v1','pho_minh/r3/pho_minh.blend','pho_minh/r3'),
  'one_pillar':('r4-v1','one_pillar/r4/one_pillar.blend','one_pillar/r4'),
  'garden':('r4-v1','garden/r4/garden.blend','garden/r4'),
  'foundry':('r5-v1','foundry/r5/foundry.blend','foundry/r5'),
 }
 names=['model.fbx','building.json','albedo.png','normal.png','roughness.png','metalness.png']
 selected={'schema':'ccp075-explicit-final-selection/v1','models':{},'sources':{},
  'flags':str(flags.resolve()),'flag_placements':str(placements.resolve()),'flag_placements_sha256':sha(placements)}
 for family,(label,source_rel,export_rel) in revisions.items():
  payload=ROOT/'output/release_075/payloads'/f'{family}-{label}'/'receipt.json';assert payload.is_file()
  cook=ROOT/'output/release_075/cooks'/f'{family}-{label}'/'receipt.json';assert cook.is_file()
  source=ROOT/'art/authoring/release_075'/source_rel;exports=ROOT/'art/exports/release_075'/export_rel
  selected['models'][family]=str(payload)
  selected['sources'][family]={'blend':str(source),'blend_sha256':sha(source),'export_directory':str(exports),
   'export_sha256':{name:sha(exports/name) for name in names},'cook_receipt':str(cook)}
 assert flags.is_file() and not target.exists()
 target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(selected,indent=2)+'\n',encoding='utf-8');print(target)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('flags',type=Path);p.add_argument('placements',type=Path);p.add_argument('target',type=Path)
 a=p.parse_args();main(a.flags,a.placements,a.target)

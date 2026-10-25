"""Pin exact native structure albedoTex slots without altering v1 art/maps."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from common import EXPORT,OUT,guard,owned,read,sha,write

KEYS=('siege_tower3','ram3_candidate','springald3_candidate',
      'trebuchet4_counterweight_candidate','trebuchet4_traction_candidate','siege_cart3')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--key',choices=KEYS,required=True)
    args=parser.parse_args();guard();result=[]
    for key in (args.key,):
        old=EXPORT/'remaining_roster/nonhumanoid'/key/'v1/material-map.json'
        updated=owned(EXPORT/'remaining_roster/nonhumanoid'/key/'v1/material-map-v3.json')
        receipt=owned(OUT/'qualification/remaining_roster/nonhumanoid'/key/'v1/material-map-v3-receipt.json')
        if updated.exists() or receipt.exists():raise FileExistsError('Preserve corrected mapping')
        data=read(old);manifest=read(Path(data['donor_manifest']))
        native={m['name']:m for m in manifest['material']['materials']}
        for row in data['groups']:
            material=native[row['native_material']]
            slots={t['name'] for block in material['blocks'] for t in block['textures']}
            if 'albedoTex' not in slots:
                raise RuntimeError(f'{key}/{row["native_material"]} lacks native albedoTex')
            row['texture_slot']='albedoTex'
        data['schema']='ccp-060-nonhumanoid-compatible-material-map/3'
        data['supersedes_v1_map']=str(old)
        data['supersedes_v1_map_sha256']=sha(old)
        write(updated,data)
        write(receipt,{'map':str(updated),'map_sha256':sha(updated),
                       'exact_native_structure_slots_verified':True,'native_cook':'not_run'})
        result.append({'key':key,'map':str(updated),'sha256':sha(updated)})
    print(json.dumps(result))

if __name__=='__main__':main()

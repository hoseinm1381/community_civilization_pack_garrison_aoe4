"""Pin Horseman II v4 native rider/horse atlas assignment for material cook."""
from __future__ import annotations
import json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import EXPORT,OUT,guard,owned,read,sha,write

def main():
    guard()
    pilot_path=OUT/'pilots/horseman2/authoring.json'
    art_path=OUT/'representatives/horseman2/v4/authoring.json'
    pilot=read(pilot_path);art=read(art_path)
    blend=Path(art['blend']);manifest=Path(pilot['donor_manifest'])
    if sha(blend)!=art['blend_sha256']:raise RuntimeError('Horseman II art drift')
    native=read(manifest)
    logical=native['request']['logical_path']
    out=owned(EXPORT/'representatives/horseman2/v4/material-map.json')
    receipt=owned(OUT/'qualification/remaining_roster/mounted/horseman2/v4/material-map-receipt.json')
    if out.exists() or receipt.exists():raise FileExistsError('Preserve existing map')
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    rows=[]
    for item in pilot['remix']:
        source=bpy.data.objects.get(item['source'])
        remix=bpy.data.objects.get(item['remix'])
        if source is None or remix is None:raise RuntimeError('Missing native mapped mesh')
        source_material=source.data.materials[0]
        parts=source_material.name.split(' · ')
        if len(parts)<3 or parts[0]!='AoE IV':raise RuntimeError('Native material projection changed')
        native_material=parts[1]
        if not any(g['material']==native_material for g in native['geometry']['groups']):
            raise RuntimeError('Native group/material mismatch')
        material=remix.data.materials[0]
        nodes=[n for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'albedo' in n.name.lower()]
        if len(nodes)!=1:raise RuntimeError('Atlas assignment ambiguous')
        atlas=Path(nodes[0].image.filepath)
        if not atlas.is_file():raise FileNotFoundError(atlas)
        rows.append({'native_material':native_material,'native_group':item['source'],
                     'projection_material':source_material.name,'albedo_png':str(atlas.resolve()),
                     'albedo_sha256':sha(atlas),'texture_slot':'albedoTexture',
                     'role':'horse' if native_material.startswith('horse') else 'rider'})
    write(out,{'schema':'ccp-060-horseman2-v4-native-material-map/1',
               'exact_native_model':logical,'donor_manifest':str(manifest),
               'donor_manifest_sha256':sha(manifest),'groups':rows,
               'geometry_route':'stock geometry + compatible atlas only; added v4 parts excluded'})
    write(receipt,{'map':str(out),'map_sha256':sha(out),'source_blend':str(blend),
                   'source_blend_sha256':sha(blend),'native_cook':'not_run'})
    print(json.dumps({'map':str(out),'groups':rows}))

if __name__=='__main__':main()

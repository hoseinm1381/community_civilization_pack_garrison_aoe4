"""Render stock-geometry mounted fallback with only saved compatible atlas changes."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ART,OUT,guard,owned,read,sha,write
import representative_batch as review

KEYS=('armor3','armor4','light3','light4','scout1','scout2','scout3','scout4',
      'scout_female1','scout_female2','scout_female3','scout_female4',
      'trade2','trade3','trade4','horseman2')

def main(key):
    guard()
    if key=='horseman2':
        receipt_path=OUT/'representatives/horseman2/v4/authoring.json'
        rev='v4'
    else:
        rev='v2' if key=='trade4' else 'v1'
        receipt_path=OUT/'qualification/remaining_roster/mounted'/key/rev/'authoring.json'
    receipt=read(receipt_path)
    blend=Path(receipt['blend'])
    if sha(blend)!=receipt['blend_sha256']:raise RuntimeError('Mounted source changed')
    destination=owned(OUT/'qualification/remaining_roster/mounted'/key/rev/'fallback-review')
    proof=destination/'review.json'
    if proof.exists() or destination.exists():raise FileExistsError(destination)
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    collection_name=('CCP060_horseman2_final_geometry' if key=='horseman2'
                     else 'CCP060_'+key+'_final')
    final=bpy.data.collections[collection_name]
    if key=='horseman2':
        added={p['name'] for p in receipt['parts']}
    else:
        added={p['name'] for p in receipt['parts']}
    if len(added)!=4:raise RuntimeError('Expected four unqualified source details')
    for name in added:
        obj=bpy.data.objects.get(name)
        if obj is None or final.objects.get(name) is None:raise RuntimeError('Missing detail: '+name)
        obj.hide_render=True
        obj.hide_set(True)
    source=max((o for o in bpy.data.objects if o.type=='MESH' and
                'horse_lod1' in o.name and final.objects.get(o.name) is None),
               key=lambda obj:len(obj.data.polygons))
    review._review_folder_override=destination
    game=review.render_match(key,rev,source,final)
    close=review.render_match(key,rev,source,final,extra=True)
    write(proof,{'schema':'ccp-060-mounted-compatible-fallback-review/1',
                 'source_receipt':str(receipt_path),'source_receipt_sha256':sha(receipt_path),
                 'source_blend':str(blend),'source_blend_sha256':sha(blend),
                 'hidden_unqualified_parts':sorted(added),
                 'visible':'exact stock geometry plus saved native material atlas treatment',
                 'game':game,'close':close,'native_match':'unverified'})
    print(json.dumps({'key':key,'proof':str(proof)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--key',choices=KEYS,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    main(args.key)

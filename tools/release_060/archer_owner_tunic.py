"""Put only the new Archer split tunic on the donor's native owner-color chart."""
from pathlib import Path
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, OUT, guard, owned, sha, write

TUNIC='CCP060 · Archer v3 clean split tunic'
STAGES={
    'base': (
        ART/'archer/archer-base-v3i-clean.blend',
        'f6baf5bd9bb623d16fcdd7b4b3bd976ddb094f5d066db8d559fb7ab4f44a145b',
        ART/'archer/archer-base-v3l-owner-tunic.blend',
    ),
    'rattan': (
        ART/'archer/archer-rattan-v3k-contact.blend',
        '6005123ff6cfc22f53318659ab52abfb441b1dc7cefcd7e209ef28644f23d508',
        ART/'archer/archer-rattan-v3m-owner-tunic.blend',
    ),
}


def stage_owner_tunic(which):
    guard()
    source,expected,target=STAGES[which]
    owned(target)
    receipt=owned(OUT/f'qualification/archer-{which}-owner-tunic.json')
    if target.exists() or receipt.exists():
        raise FileExistsError('Preserve existing owner-tunic output')
    if Path(bpy.data.filepath).resolve()!=source.resolve() or sha(source)!=expected:
        raise RuntimeError(f'Open pinned {which} source')
    tunic=bpy.data.objects[TUNIC]
    uv=tunic.data.uv_layers.active
    if len(tunic.data.polygons)!=48 or uv is None:
        raise RuntimeError('Unexpected split tunic mesh or UV')
    before=[tuple(v.uv) for v in uv.data]
    lo_u,hi_u=min(v[0] for v in before),max(v[0] for v in before)
    lo_v,hi_v=min(v[1] for v in before),max(v[1] for v in before)
    if abs(lo_u-.515)>.002 or abs(hi_u-.655)>.002 or abs(lo_v-.145)>.002 or abs(hi_v-.333)>.002:
        raise RuntimeError('Tunic UV differs from inspected donor chart')
    for loop,(u,v) in zip(uv.data,before):
        loop.uv=(.405+.030*(u-lo_u)/(hi_u-lo_u),
                 .330+.070*(v-lo_v)/(hi_v-lo_v))
    bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
    detail={'schema':'ccp-060-archer-owner-tunic/v1','status':'authoring_only',
            'source':str(source),'source_sha256':expected,
            'blend':str(target),'blend_sha256':sha(target),
            'geometry_unchanged':True,'new_split_tunic_faces':48,
            'old_uv_bounds':[lo_u,hi_u,lo_v,hi_v],
            'stock_owner_uv_bounds':[.405,.435,.330,.400],
            'stock_pattern_red_minimum_probed':.882,
            'stock_mask_threshold':.67,
            'stock_metal_texture_red_probed':0.0,
            'native_material_integration':'separate qualification'}
    write(receipt,detail)
    return detail

"""Compare freshly extracted Shrek motion to the actual stock spearman owner."""
from pathlib import Path
import hashlib,json,runpy
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/release_081_animation/showcase-inspection-20261024'
# Reuses the read adapter's source-declared cattle type registration. The
# qualified roundtrip is deterministic and refuses different existing bytes.
adapter=runpy.run_path(str(ROOT/'tools/release_081_animation/roundtrip.py'))
HKX=adapter['HKX']
shrek=HKX.from_path(OUT/'modding_showcase_tuning/art/scenario/a4etk_shrek_fitted_v3/a4etk_shrek_fitted_v3.rhka')
stock=HKX.from_path(next((ROOT/'output/release_081_animation/human-encoder-control').rglob('owner.rhka')))
def motion(x):
    a=x.animationBinding.animation
    return {'duration':a.duration,'frames':a.numFrames,'compressed':a.compressedData,
            'integers':a.intData,'integer_offsets':a.intArrayOffsets,'floats':a.floatData,
            'float_offsets':a.floatArrayOffsets,'tracks':a.numberOfTransformTracks}
def fingerprint(x):return hashlib.sha256(json.dumps(motion(x),sort_keys=True).encode()).hexdigest()
original={x.name:x for x in stock.root.animations}
cheers=[{'index':i,'name':x.name.replace('\u00a5','\\'),'duration':x.animationBinding.animation.duration,
         'frames':x.animationBinding.animation.numFrames,'bones':len(x.skeleton.bones),
         'motion_payload_sha256':fingerprint(x),
         'equals_same_named_stock':fingerprint(x)==fingerprint(original[x.name])}
        for i,x in enumerate(shrek.root.animations) if 'cheering' in x.name]
a=json.loads((OUT/'shrek-cheer-01.json').read_text())
b=json.loads((OUT/'stock-spearman-cheer-01.json').read_text())
assert a['frame_count']==b['frame_count']==225
moving=[];differences=[]
for bone in range(48):
    motion_delta=0;stock_delta=0
    for f,g in zip(a['samples'],b['samples']):
        for key in ['translation_xyz','quaternion_xyzw','scale_xyz']:
            v=f['bones'][bone][key];ref=a['samples'][0]['bones'][bone][key]
            w=g['bones'][bone][key]
            motion_delta=max(motion_delta,max(abs(x-y) for x,y in zip(v,ref)))
            stock_delta=max(stock_delta,max(abs(x-y) for x,y in zip(v,w)))
    if motion_delta>1e-4:moving.append(a['samples'][0]['bones'][bone]['bone_name'])
    differences.append(stock_delta)
report={'shrek_clips':len(shrek.root.animations),'stock_spearman_clips':len(stock.root.animations),
        'cheer_slots':cheers,'all_eight_cheer_payloads_identical':len({x['motion_payload_sha256'] for x in cheers})==1,
        'all_eight_differ_from_matching_stock':all(not x['equals_same_named_stock'] for x in cheers),
        'shrek_additional_clip_names':[x.name.replace('\u00a5','\\') for x in shrek.root.animations if x.name not in original],
        'cheer_01_sampled_motion':{'moving_bones':moving,'count':len(moving),
                                 'max_component_difference_from_stock':max(differences)},
        'authoring_source_or_encoder_identified':False,'fresh_native_playback_tested':False}
(OUT/'motion-comparison.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

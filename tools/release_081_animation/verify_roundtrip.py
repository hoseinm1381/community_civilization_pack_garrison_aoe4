"""Independent Garrison sample comparison of every native cattle clip."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
check_storage(ROOT,CFG)
OUT=ROOT/'output/release_081_animation/retry-1'
result=json.loads((OUT/'roundtrip-result.json').read_text())
assert result['status']=='roundtrip_headers_skeletons_bindings_payloads_equal'
original=Path(result['source']);rewritten=Path(result['output'])
assert hashlib.sha256(rewritten.read_bytes()).hexdigest()==result['output_sha256']
DEST=OUT/'independent-all-clips'
DEST.mkdir(exist_ok=False)
rows=[]
for index in range(11):
    pair=[]
    for label,source in [('native',original),('roundtrip',rewritten)]:
        target=DEST/f'{index:02d}-{label}.json'
        argv=[CFG['garrison_core'],'-m','src.core.animation_clip','--source',str(source),'--clip-index',str(index),'--output',str(target)]
        run=subprocess.run(argv,capture_output=True,text=True,timeout=180)
        (DEST/f'{index:02d}-{label}.log').write_text(run.stdout+run.stderr)
        assert run.returncode==0,(index,label,run.stderr)
        pair.append(json.loads(target.read_text()))
    a,b=pair
    fields=['schema','status','clip_index','name','duration_seconds','frame_count','transform_space','quaternion_completion','samples','root_motion','motion']
    for field in fields:assert a[field]==b[field],(index,field)
    rows.append({'index':index,'name':a['name'],'frame_count':a['frame_count'],
                 'duration_seconds':a['duration_seconds'],'sampled_poses_equal':True,
                 'root_motion_equal':True,'motion_measurement_equal':True})
    print(index,a['name'],'EXACT_READBACK',flush=True)
baseline=Path(CFG['external_root'])/'output/release_081/delivery/final-v1/community_civilization_pack-0.8.1.zip'
assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='75963810d5b241680fad90ff5b4c4f81cb0ba37f550c3b2e65b103f0250fd3e0'
report={'status':'all_11_clips_exact_independent_sample_readback','clips':rows,
        'source_sha256':result['source_sha256'],'roundtrip_sha256':result['output_sha256'],
        'release_081_zip_preserved':True,'authored_motion_encoded':False,
        'new_animation_test_package_created':False,'native_cook':False,
        'native_runtime':False,'save_load':False,'multiplayer':False}
(OUT/'independent-verification.json').write_text(json.dumps(report,indent=2))
print('VERIFIED_ALL_11_AND_RELEASE_PRESERVATION')

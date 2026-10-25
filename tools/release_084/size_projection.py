"""Measured compressed-sample estimate; actual assembled ZIP remains authoritative."""
import json
import math
from pathlib import Path
from local_audition import DEST
from local_bank import local_guard
from pipeline import save_json
from voice_scope import delivery_manifest


def project_size(baseline_bytes,encoded_bytes,clips,required,overhead=10_000_000,stock_bytes=0):
    if clips<=0 or required<clips:raise ValueError('Invalid compressed sample coverage')
    voices=math.ceil(encoded_bytes*required/clips)
    total=baseline_bytes+voices+overhead+stock_bytes
    return dict(baseline_zip_bytes=baseline_bytes,measured_compressed_clips=clips,
        measured_compressed_bytes=encoded_bytes,required_clips=required,
        projected_voice_bytes=voices,overlay_and_container_margin_bytes=overhead,
        stock_effort_encoded_bytes=stock_bytes,
        projected_final_zip_bytes=total,limit_bytes=400_000_000,exceeds_limit=total>400_000_000,
        actual_final_zip_measured=False,
        method='Existing ZIP + measured mean compressed clip bytes extrapolated to delivery coverage + stock efforts + 10 MB margin')


def main():
    local_guard()
    baseline=json.loads((DEST.parent/'baseline.json').read_text())
    manifest=json.loads((DEST/'recording-manifest.json').read_text())
    manifest=delivery_manifest(manifest)
    root=DEST/'compressed-v1';index=root/'index.json'
    info=json.loads((index if index.exists() else root/'checkpoint.json').read_text())
    required={j['id'] for j in manifest['jobs']}
    if 'recordings' in info:
        sample=[r for k,r in info['recordings'].items() if k in required]
        encoded_bytes=sum(r['bytes'] for r in sample);clips=len(sample)
    else:encoded_bytes=info['encoded_bytes'];clips=info['clips']
    stock_file=DEST.parent/'integration/stock-efforts-v1/receipt.json'
    stock_bytes=json.loads(stock_file.read_text())['encoded_bytes'] if stock_file.exists() else 0
    result=project_size(Path(baseline['zip']).stat().st_size,encoded_bytes,clips,len(required),stock_bytes=stock_bytes)
    save_json(DEST/'package-size-projection.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

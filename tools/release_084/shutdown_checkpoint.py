"""Capture a stopped worker's queue without restarting generation."""
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import argparse
from local_bank import local_guard
from local_audition import DEST,RUNTIME
from pipeline import digest,save_json
from voice_scope import delivery_manifest


def main():
    local_guard()
    parser=argparse.ArgumentParser();parser.add_argument('--attempt-ceiling',type=int,choices=[3,5],default=5)
    args=parser.parse_args()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target=DEST/'shutdown-checkpoints'/stamp;target.mkdir(parents=True)
    generation=DEST/'generation'
    full_manifest=json.loads((DEST/'recording-manifest.json').read_text())
    manifest=delivery_manifest(full_manifest)
    state=json.loads((generation/'state.json').read_text())
    attempts=json.loads((generation/'attempts.json').read_text())
    if not (generation/'STOP').exists():raise RuntimeError('Cooperative STOP must remain present')
    missing=[j for j in manifest['jobs'] if j['id'] not in state]
    snapshots={}
    paths=[generation/'state.json',generation/'attempts.json',generation/'checkpoint.json',
           DEST/'recording-manifest.json',DEST/'input-verification.json']
    if (DEST/'delivery-scope.json').exists():paths.append(DEST/'delivery-scope.json')
    for path in paths:
        saved=target/path.name;shutil.copyfile(path,saved)
        if digest(path)!=digest(saved):raise RuntimeError('Checkpoint copy differs')
        snapshots[str(path)]=dict(snapshot=str(saved),sha256=digest(saved))
    for key,row in list(state.items())[-6:]:
        if digest(row['path'])!=row['sha256']:raise RuntimeError('Latest saved playback changed')
    receipts=list((DEST/'compressed-v1').glob('*/attempt-*/receipt.json'))
    compressed=[json.loads(p.read_text()) for p in receipts]
    for row in compressed:
        if digest(row['path'])!=row['sha256']:raise RuntimeError('Saved compressed pilot changed')
    required_ids={j['id'] for j in manifest['jobs']}
    result=dict(status='paused for user laptop shutdown',utc=stamp,accepted=len(set(state)&required_ids),
        archived_accepted=len(state),generation_manifest_jobs=len(full_manifest['jobs']),attempt_ceiling=args.attempt_ceiling,
        accepted_by_kind=dict(Counter(r['metadata']['job']['kind'] for k,r in state.items() if k in required_ids)),
        required=len(manifest['jobs']),remaining=len(missing),
        remaining_by_kind=dict(Counter(j['kind'] for j in missing)),
        unstarted_dialogue=sum(j['kind']=='dialogue' and not attempts.get(j['id']) for j in missing),
        exhausted_dialogue=sum(j['kind']=='dialogue' and attempts.get(j['id'],0)>=args.attempt_ceiling for j in missing),
        complete_pools=sum(set(p['jobs'])<=set(state) for p in manifest['pools']),
        total_pools=len(manifest['pools']),snapshots=snapshots,latest_six_playback_hashes_verified=True,
        compressed_pilot_receipts=len(compressed),compressed_pilot_bytes=sum(r['bytes'] for r in compressed),
        medium_verifier_download_complete=(RUNTIME/'models/phowhisper-medium/verified-downloads.json').exists(),
        final_zip_limit_bytes=400000000,compression='mono48k nominal64kbps Ogg Vorbis candidates; native route unqualified',
        full_release=False,active_source_modified=False,native_voice_integration=False,
        note='Stopped-state snapshot; run only after active workers exit. Original attempts/master audio and completed compressed receipts remain retained. No automation exists.')
    save_json(target/'checkpoint.json',result);save_json(DEST/'SHUTDOWN_CHECKPOINT.json',result)
    save_json(target/'remaining-jobs.json',dict(jobs=missing))
    print(json.dumps({k:v for k,v in result.items() if k!='snapshots'},indent=2),flush=True)


if __name__=='__main__':main()

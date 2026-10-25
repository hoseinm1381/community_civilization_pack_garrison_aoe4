"""Resumable mono 48 kHz Vorbis exports; originals and PCM remain untouched."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
from local_bank import local_guard
from local_audition import DEST,RUNTIME
from local_inputs import verify_completed_recording
from pipeline import digest,save_json,wav_metrics,pcm_wav,AudioError,StateStore

LIMIT=400_000_000


def validate_decode(source_metrics,decoded_metrics):
    if decoded_metrics['sample_rate']!=48000 or abs(source_metrics['duration']-decoded_metrics['duration'])>.03:
        raise AudioError('Compressed playback changes rate or truncates duration')
    ratio=decoded_metrics['rms']/source_metrics['rms']
    if not .7<=ratio<=1.3:raise AudioError('Compressed playback changes speech level excessively')


def enforce_zip_budget(path):
    size=Path(path).stat().st_size
    if size>LIMIT:raise RuntimeError(f'ZIP exceeds the user limit: {size} > {LIMIT} bytes')
    return size


def compressed_recordings(verification,root=None):
    import soundfile as sf
    root=Path(root or DEST/'compressed-v1')
    index=json.loads((root/'index.json').read_text());records={};known=set()
    def inspect_compressed(item):
        key,source=item
        proof=index['recordings'].get(key)
        if not proof or proof['recipe']['source_sha256']!=source['sha256']:
            raise RuntimeError('Missing or changed compressed source identity: '+key)
        recipe=proof['recipe']
        if (recipe['codec'],recipe['bitrate'],recipe['sample_rate'],recipe['channels'])!=('vorbis',64000,48000,1):
            raise RuntimeError('Compressed playback recipe differs')
        path=Path(proof['path'])
        if digest(path)!=proof['sha256']:
            raise RuntimeError('Changed or duplicate compressed performance')
        info=sf.info(path)
        if (info.format,info.subtype,info.channels,info.samplerate)!=('OGG','VORBIS',1,48000):
            raise RuntimeError('Compressed playback container differs')
        audio,rate=sf.read(path,dtype='int16');pcm=pcm_wav(audio.tobytes(),rate)
        if audio.ndim!=1 or len(audio)!=info.frames or hashlib.sha256(pcm).hexdigest()!=proof['decoded_pcm_sha256']:
            raise RuntimeError('Compressed playback decode differs')
        metrics=wav_metrics(pcm)
        if abs(metrics['duration']-source['duration'])>.03:raise RuntimeError('Compressed playback truncates source')
        return key,dict(path=str(path),sha256=proof['sha256'],duration=metrics['duration'],
                          member='audio/voices/'+proof['sha256']+'.ogg',pcm_sha256=source['sha256'])
    with ThreadPoolExecutor(max_workers=8) as readers:
        for count,(key,recording) in enumerate(readers.map(inspect_compressed,verification['recordings'].items()),1):
            if recording['sha256'] in known:raise RuntimeError('Changed or duplicate compressed performance')
            known.add(recording['sha256']);records[key]=recording
            if count%1000==0:print('COMPRESSED_PLAYBACK_RECHECKED',count,flush=True)
    return records


def main():
    import soundfile as sf
    local_guard();parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=20000);args=parser.parse_args()
    encoder=RUNTIME/'tools/ffmpeg.exe'
    if not encoder.is_file():raise RuntimeError('Qualified portable encoder is missing')
    encoder_sha=digest(encoder)
    baseline=json.loads((DEST.parent/'baseline.json').read_text())
    manifest=json.loads((DEST/'recording-manifest.json').read_text());jobs={j['id']:j for j in manifest['jobs']}
    fingerprint=json.loads((DEST/'input-verification.json').read_text())['fingerprint']
    legacy=json.loads((DEST/'legacy-pilot-input-certification.json').read_text())
    state=StateStore(DEST/'generation');root=DEST/'compressed-v1';root.mkdir(exist_ok=True)
    records={};new=0
    for key,row in state.data.items():
        if new>=args.limit:break
        source=Path(row['path']);sha=row['sha256'];job=jobs[key]
        if not state.ready(key,job):raise RuntimeError('PCM source changed')
        verify_completed_recording(row,job,fingerprint,legacy.get('generation_attempts'))
        metrics=None
        recipe=dict(source_sha256=sha,job=key,encoder_sha256=encoder_sha,codec='vorbis',bitrate=64000,
                    channels=1,sample_rate=48000,metadata=False,bitexact=True)
        target=root/sha;target.mkdir(exist_ok=True)
        proof=None
        for attempt in range(1,4):
            folder=target/f'attempt-{attempt}';request=folder/'request.json';receipt=folder/'receipt.json';encoded=folder/'audio.ogg'
            if receipt.exists():
                proof=json.loads(receipt.read_text())
                if proof['recipe']!=recipe or digest(proof['path'])!=proof['sha256']:
                    raise RuntimeError('Compressed export or recipe changed')
                break
            if (folder/'rejected.json').exists():continue
            if not request.exists():
                if new>=args.limit:break
                folder.mkdir(exist_ok=True);save_json(request,recipe)
            elif json.loads(request.read_text())!=recipe:raise RuntimeError('Saved compression request differs')
            # Cached exports already bind identical source and encoded bytes to
            # the successful decode receipt. Re-run waveform analysis only for
            # a fresh/recovered encode; final package validation decodes all.
            if metrics is None:metrics=wav_metrics(source.read_bytes())
            if not encoded.exists():
                command=[str(encoder),'-v','error','-nostdin','-threads','1','-i',str(source),'-map_metadata','-1',
                         '-ac','1','-ar','48000','-c:a','libvorbis','-b:a','64k','-fflags','+bitexact','-n',str(encoded)]
                result=subprocess.run(command,capture_output=True,text=True)
                (folder/'encoder.log').write_text(result.stderr,encoding='utf-8')
                if result.returncode:
                    save_json(folder/'rejected.json',dict(reason='Encoder failed',exit=result.returncode));continue
            try:
                info=sf.info(encoded)
                if (info.format,info.subtype,info.channels,info.samplerate)!=('OGG','VORBIS',1,48000):
                    raise AudioError('Wrong compressed playback format')
                audio,rate=sf.read(encoded,dtype='int16')
                if audio.ndim!=1 or len(audio)!=info.frames:raise AudioError('Incomplete compressed decoding')
                pcm=pcm_wav(audio.tobytes(),rate);decoded=wav_metrics(pcm)
                validate_decode(metrics,decoded)
            except (AudioError,sf.SoundFileError) as error:
                save_json(folder/'rejected.json',dict(reason=str(error)));continue
            proof=dict(recipe=recipe,path=str(encoded.resolve()),sha256=digest(encoded),bytes=encoded.stat().st_size,
                       source=str(source),source_bytes=source.stat().st_size,duration=decoded['duration'],
                       decoded_pcm_sha256=hashlib.sha256(pcm).hexdigest(),decoded_metrics=decoded,
                       native_backend_decoder_qualified=False,native_game=False,audible_quality=False)
            save_json(receipt,proof);new+=1;break
        if proof is not None:records[key]=proof
        if len(records)%100==0:
            print('COMPRESSED_CLIPS',len(records),'of',len(state.data),'new',new,flush=True)
            save_json(root/'checkpoint.json',dict(clips=len(records),source_snapshot=len(state.data),new=new,
                      encoded_bytes=sum(r['bytes'] for r in records.values()),final_zip_limit_bytes=LIMIT,full_release=False))
    total=sum(r['bytes'] for r in records.values())
    save_json(root/'index.json',dict(schema='ccp-084-vorbis-exports/v1',recordings=records,clips=len(records),
              pcm_bytes=sum(r['source_bytes'] for r in records.values()),encoded_bytes=total,
              baseline_zip_bytes=Path(baseline['zip']).stat().st_size,
              final_zip_limit_bytes=LIMIT,full_release=False,native_backend_decoder_qualified=False))
    print('COMPRESSION_FINISHED',len(records),'clips;',total,'bytes; final ZIP cap',LIMIT,flush=True)


if __name__=='__main__':main()

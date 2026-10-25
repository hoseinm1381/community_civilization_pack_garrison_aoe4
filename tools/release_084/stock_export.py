"""Resumable stock effort decode/compression; retains all original media.

Run with the local audio Python. Never installs or edits game files.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import warnings
from local_bank import local_guard
from local_audition import RUNTIME
from local_compress import validate_decode
from pipeline import digest, save_json, AudioError
from providers import OUT


def metrics(path):
    import numpy as np
    import soundfile as sf
    audio,rate=sf.read(path,dtype='int16')
    info=sf.info(path)
    if rate!=48000 or audio.ndim!=1 or len(audio)!=info.frames or not .03<=len(audio)/rate<=25:
        raise AudioError('Stock effort format/duration differs')
    wide=audio.astype(np.int64);rms=float(np.sqrt(np.mean(wide*wide)))
    clipped=int(np.count_nonzero(np.abs(wide)>=32760))
    if rms<12 or clipped>max(2,len(audio)*.0001):raise AudioError('Silent or clipped stock effort')
    return dict(duration=len(audio)/rate,sample_rate=rate,rms=rms,peak=int(np.max(np.abs(wide))),
                clipped_samples=clipped,frames=len(audio),decoded_pcm_sha256=hashlib.sha256(audio.tobytes()).hexdigest())


def main():
    local_guard()
    source=OUT/'integration/stock-effort-inventory-v1/inventory.json'
    inventory=json.loads(source.read_text())
    if digest(inventory['archive'])!=inventory['archive_sha256']:raise RuntimeError('Stock archive changed')
    for row in inventory['profiles'].values():
        if digest(row['file'])!=row['sha256']:raise RuntimeError('Stock profile changed')
    decoder=RUNTIME/'tools/vgmstream-r2117/bin/vgmstream-cli.exe';encoder=RUNTIME/'tools/ffmpeg.exe'
    # Pin every distributed decoder dependency, not only its executable.
    tools={str(p):digest(p) for p in decoder.parent.rglob('*') if p.is_file()}
    tools[str(encoder)]=digest(encoder)
    recipe=dict(inventory_sha256=digest(source),tool_sha256=tools,canonical_gain=.85,
                codec='vorbis-64k-mono-48k',sample_rate=48000,channels=1)
    dest=OUT/'integration/stock-efforts-v1';dest.mkdir(parents=True,exist_ok=True)
    frozen=dest/'recipe.json'
    if frozen.exists():
        if json.loads(frozen.read_text())!=recipe:raise RuntimeError('Stock export recipe changed')
    else:save_json(frozen,recipe)
    runtime=Path('C:/Users/RS/.codex/cache/aoe4-sga-extractor-session-20260717/_skill_sga_live_runtime')
    sys.path[:0]=[str(runtime/'site-packages'),str(runtime/'SGA-V10/src')]
    warnings.filterwarnings('ignore')
    from relic.sga.v10 import EssenceFSHandler
    from relic.sga.core.definitions import Version
    EssenceFSHandler.version=Version(10,0)
    members=sorted({m for p in inventory['profiles'].values() for r in p['records'] for m in r['media']})
    exports={}
    def run(label,command,folder):
        proc=subprocess.run(list(map(str,command)),capture_output=True,text=True,encoding='utf-8',errors='replace')
        (folder/(label+'.log')).write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
        if proc.returncode:raise RuntimeError('Stock effort '+label+' failed; evidence retained')
        return proc.stdout
    with Path(inventory['archive']).open('rb') as stream:
        fs=EssenceFSHandler.read(stream)
        for index,member in enumerate(members,1):
            key=hashlib.sha256(member.encode()).hexdigest();folder=dest/'clips'/key
            folder.mkdir(parents=True,exist_ok=True);receipt=folder/'receipt.json'
            raw=fs.readbytes(member);raw_sha=hashlib.sha256(raw).hexdigest()
            wem=folder/'original.wem';decoded=folder/'decoded-original.wav'
            pcm=folder/'playback.wav';ogg=folder/'playback.ogg'
            if receipt.exists():
                row=json.loads(receipt.read_text())
                if row['source_sha256']!=raw_sha or row['recipe_sha256']!=digest(frozen):
                    raise RuntimeError('Stock effort source/recipe changed')
                for path,sha in row['saved_sha256'].items():
                    if digest(path)!=sha:raise RuntimeError('Stock effort bytes changed')
                actual=metrics(ogg)
                if actual!=row['encoded_metrics']:raise RuntimeError('Stock effort decode changed')
            else:
                if wem.exists():
                    if wem.read_bytes()!=raw:raise RuntimeError('Stock original differs')
                else:wem.write_bytes(raw)
                if not decoded.exists():run('decode',[decoder,'-i','-o',decoded,wem],folder)
                # vgmstream reports exact native sample count. A saved PCM decode
                # must have that many frames; an interrupted file cannot pass.
                log=(folder/'decode.log').read_text()
                counts=re.findall(r'stream total samples: (\d+)',log)
                import soundfile as sf
                original_info=sf.info(decoded)
                if len(counts)!=1 or original_info.frames!=int(counts[0]):
                    raise RuntimeError('Native effort decode frame count differs')
                if not pcm.exists():run('normalize',[encoder,'-v','error','-nostdin','-i',decoded,
                     '-map_metadata','-1','-ac','1','-ar','48000','-af','volume=0.85','-c:a','pcm_s16le','-n',pcm],folder)
                before=metrics(pcm)
                if abs(before['duration']-original_info.duration)>.001:raise RuntimeError('Stock canonical audio truncates source')
                if not ogg.exists():run('encode',[encoder,'-v','error','-nostdin','-threads','1','-i',pcm,
                     '-map_metadata','-1','-ac','1','-ar','48000','-c:a','libvorbis','-b:a','64k','-fflags','+bitexact','-n',ogg],folder)
                after=metrics(ogg);validate_decode(before,after)
                info=sf.info(ogg)
                if (info.format,info.subtype)!=('OGG','VORBIS'):raise RuntimeError('Wrong stock effort encoding')
                row=dict(native_member=member,source_sha256=raw_sha,recipe_sha256=digest(frozen),
                         path=str(ogg),sha256=digest(ogg),duration=after['duration'],bytes=ogg.stat().st_size,
                         member='audio/stock_efforts/'+digest(ogg)+'.ogg',encoded_metrics=after,
                         saved_sha256={str(p):digest(p) for p in [wem,decoded,pcm,ogg]})
                save_json(receipt,row)
            exports[member]=row
            if index%25==0:
                print('STOCK_EFFORT_EXPORTS',index,'of',len(members),flush=True)
                save_json(dest/'checkpoint.json',dict(completed=index,required=len(members),complete=False))
    clips={}
    for speaker,profile in inventory['profiles'].items():
        events={}
        for record in profile['records']:
            events.setdefault(record['event'],[]).extend(exports[m] for m in record['media'])
        # Identical native references deliberately share one encoded performance.
        clips[speaker]={event:list({r['sha256']:r for r in rows}.values()) for event,rows in events.items()}
    aliases=[]
    consumers=inventory['consumers']
    for name,mapping in consumers.items():
        for sex,speaker in list(mapping.items()):
            key=speaker.lower()
            if key not in clips:
                if key!='manatarmsfemale' or 'villagerfemale' not in clips:raise RuntimeError('Unresolved stock effort speaker')
                aliases.append(dict(consumer=name,sex=sex,original=speaker,reuse='villagerfemale',
                    reason='Custom female infantry names an absent Chinese native profile; reuse existing female stock efforts',
                    original_native_assignment_verified=False))
                key='villagerfemale'
            mapping[sex]=key
    save_json(dest/'receipt.json',dict(schema='ccp-084-stock-effort-media/v1',recipe_sha256=digest(frozen),
          inventory_sha256=digest(source),consumer_inventory_sha256=inventory['consumer_inventory_sha256'],
          consumers=consumers,clips=clips,exports=exports,aliases=aliases,encoded_bytes=sum(r['bytes'] for r in exports.values()),
          stock_effort_preservation_complete=True,native_scheduling_preserved=False,
          exact_original_female_infantry_assignment=False,native_playback=False,audible_quality=False,
          note='Original stock effort media replayed by presentation SCAR; native scheduling and the documented female fallback need acceptance.'))
    print('STOCK_EFFORT_EXPORT_COMPLETE',len(exports),'native sources',flush=True)


if __name__=='__main__':main()

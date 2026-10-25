"""Isolated installed-backend codec probe; no game process or installation.

Uses this helper's own PID as the lifetime/pipe namespace and silent output gain.
This does not establish native-game playback or audible quality.
"""
import ctypes
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import struct
import subprocess
import time
from local_bank import local_guard
from local_audition import DEST,RUNTIME
from pipeline import digest,save_json
from providers import ROOT,OUT


def main():
    import msgpack
    local_guard();cfg=json.loads((ROOT/'workspace.json').read_text())
    parser=argparse.ArgumentParser();parser.add_argument('--label',default='codec-probe-v1')
    parser.add_argument('--framing',choices=['length32','raw'],default='length32');args=parser.parse_args()
    if not re.fullmatch('[a-z0-9-]{1,50}',args.label):raise ValueError('Invalid probe label')
    work=DEST/args.label
    if work.exists():raise FileExistsError('Preserve codec probes')
    work.mkdir()
    encoder=RUNTIME/'tools/ffmpeg.exe'
    donor=Path('C:/Users/RS/AppData/Local/Programs/Python/Python313/Scripts/ffmpeg.exe')
    if not encoder.exists():encoder.parent.mkdir(exist_ok=True);shutil.copyfile(donor,encoder)
    if digest(encoder)!=digest(donor):raise RuntimeError('Portable encoder copy differs')
    state=json.loads((DEST/'generation/state.json').read_text())
    source=Path(next(iter(state.values()))['path'])
    valid=work/'valid.ogg'
    command=[str(encoder),'-v','error','-nostdin','-i',str(source),'-map_metadata','-1',
             '-ac','1','-ar','48000','-c:a','libvorbis','-b:a','64k','-fflags','+bitexact',str(valid)]
    subprocess.run(command,check=True)
    invalid=work/'invalid.ogg';invalid.write_bytes(b'Intentionally invalid codec control, not audio.')
    members=work/'members.txt'
    members.write_text(f'audio/probe.wav={source}\naudio/probe.ogg={valid}\naudio/invalid.ogg={invalid}\n',encoding='utf-8')
    base=json.loads((OUT/'integration/voice-identities-v1/receipt.json').read_text())
    if digest(base['archive'])!=base['archive_sha256']:raise RuntimeError('Probe base changed')
    archive=work/'probe.sga'
    pack=subprocess.run([cfg['archive_tool'],'set-members',base['archive'],str(members),str(archive),'--alias','data'],
                         capture_output=True,text=True,check=True)
    (work/'archive-log.json').write_text(pack.stdout)
    backend=Path('C:/Users/RS/AppData/Local/Garrison/current/garrison-audio-backend.exe')
    key='cc084_codec_probe';pipe=rf'\\.\pipe\garrison-{os.getpid()}-audio.{key}'
    log=work/'backend.log'
    with log.open('wb') as output:
        process=subprocess.Popen([str(backend),'--sga',str(archive),'--game-pid',str(os.getpid()),'--mod-key',key],
                                 stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            deadline=time.monotonic()+10
            while True:
                try:stream=open(pipe,'wb',buffering=0);break
                except FileNotFoundError:
                    if time.monotonic()>deadline or process.poll() is not None:raise RuntimeError('Probe backend pipe unavailable')
                    time.sleep(.1)
            with stream:
                started=time.monotonic();seq=0
                def send(method='audio',**fields):
                    nonlocal seq
                    seq+=1
                    message=dict(m=method,v=1,mod=key,epoch=1,seq=seq,t=0 if method=='audio_session' else time.monotonic()-started,**fields)
                    blob=msgpack.packb(message,use_bin_type=True)
                    stream.write((struct.pack('<I',len(blob)) if args.framing=='length32' else b'')+blob)
                send('audio_session')
                for i in range(24):
                    send(kind='pulse')
                    if i in [1,8,15]:send(clip=['audio/probe.wav','audio/probe.ogg','audio/invalid.ogg'][[1,8,15].index(i)],x=0,z=0,gain=.001)
                    time.sleep(.25)
                send(stop=True)
        finally:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
    save_json(work/'receipt.json',dict(backend_sha256=digest(backend),encoder_sha256=digest(encoder),
        encoding_command=command,source_sha256=digest(source),encoded_sha256=digest(valid),
        source_bytes=source.stat().st_size,encoded_bytes=valid.stat().st_size,
        archive_sha256=digest(archive),own_helper_pid=os.getpid(),gain=.001,experimental_framing=args.framing,
        native_game=False,audible_quality=False,decoder_result='Inspect backend.log; no automatic success assertion'))
    print('CODEC_PROBE_LOG',log,flush=True)
    print(log.read_text(errors='replace'),flush=True)


if __name__=='__main__':main()

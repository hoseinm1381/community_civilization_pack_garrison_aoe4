"""Optional NEW local voice work. Never regenerates or modifies the shipped bank.

Run with the configured VieNeu Python environment. No automatic downloads.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def verified_models(root):
    pins = {'vieneu':('pnnbao-ump/VieNeu-TTS-v3-Turbo','61b85e3d937fbbacb387714180e8182823512523'),
            'moss':('OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano','6aa02b01e445cc585582cf0ba480bc3ea6c8dd68')}
    for name,(repo,revision) in pins.items():
        folder = root/name
        doc = json.loads((folder/'verified-downloads.json').read_text())
        if (doc['repo'],doc['revision']) != (repo,revision) or not doc['files']:
            raise ValueError('Wrong/incomplete local model receipt: '+name)
        for row in doc['files']:
            p = (folder/row['file']).resolve()
            if not p.is_relative_to(folder.resolve()) or not p.is_file():
                raise ValueError('Missing/unsafe model input')
            with p.open('rb') as f:
                if hashlib.file_digest(f,'sha256').hexdigest() != row['sha256']:
                    raise ValueError('Changed model input: '+str(p))
    return {name:str(root/name) for name in pins}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--models',type=Path,required=True,help='Local model root with pinned vieneu/moss receipts')
    p.add_argument('--ffmpeg',type=Path,required=True)
    p.add_argument('--text')
    p.add_argument('--voice',help='Installed Northern Vietnamese preset name')
    p.add_argument('--destination',type=Path)
    p.add_argument('--check',action='store_true',help='Validate inputs/dependencies; no model loading or generation')
    p.add_argument('--seed',type=int,default=0)
    args = p.parse_args()
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    if not args.models.is_dir() or not args.ffmpeg.is_file():
        raise ValueError('Install and explicitly select local models/ffmpeg first')
    import importlib.metadata as metadata
    required = {'vieneu':'3.8.3','torch':'2.8.0+cu128','torchaudio':'2.8.0+cu128','transformers':'4.57.6'}
    for name,version in required.items():
        if metadata.version(name) != version:
            raise ValueError('Use the qualified local environment: '+name+'=='+version)
    paths = verified_models(args.models.resolve())
    import numpy as np
    import soundfile as sf
    import torch
    from vieneu import Vieneu
    if not torch.cuda.is_available():
        raise RuntimeError('The qualified local voice route requires CUDA')
    if args.check:
        print('LOCAL_VOICE_INPUTS_VERIFIED; no synthesis performed')
        return
    if not args.text or not args.voice or not args.destination:
        p.error('--text, --voice and --destination are required for a new audition')
    dest = args.destination.resolve()
    dest.mkdir(parents=True,exist_ok=False)
    import random
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    tts = Vieneu(backbone_repo=paths['vieneu'],moss_tokenizer=paths['moss'],device='cuda',
                 backend='pytorch',max_batch_size=1,max_streams=1,babble_retries=0)
    audio = np.asarray(tts.infer(args.text,voice=args.voice,temperature=.8,max_new_frames=300),dtype=np.float32)
    if tts.sample_rate != 48000 or audio.ndim != 1 or not np.isfinite(audio).all() or not len(audio) or np.max(np.abs(audio)) >= 1:
        raise ValueError('Unsupported/nonfinite/clipped candidate')
    sf.write(dest/'candidate.wav',audio,48000,subtype='PCM_16')
    subprocess.run([str(args.ffmpeg),'-nostdin','-v','error','-i',str(dest/'candidate.wav'),
                    '-map_metadata','-1','-ac','1','-ar','48000','-c:a','libvorbis','-b:a','64k',
                    str(dest/'candidate.ogg')],check=True)
    decoded,rate = sf.read(dest/'candidate.ogg')
    if rate != 48000 or decoded.ndim != 1 or abs(len(decoded)-len(audio)) > .03*rate:
        raise ValueError('Compressed candidate duration/format differs')
    receipt = dict(text=args.text,voice=args.voice,seed=args.seed,codec='vorbis-64k-mono-48k',
                   model_revisions={n:json.loads((args.models/n/'verified-downloads.json').read_text())['revision'] for n in paths},
                   sha256=hashlib.sha256((dest/'candidate.ogg').read_bytes()).hexdigest(),
                   qualification='New audition: listening, pronunciation and in-game routing not accepted')
    (dest/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    print('NEW_AUDITION_SAVED',dest)


if __name__ == '__main__':
    main()

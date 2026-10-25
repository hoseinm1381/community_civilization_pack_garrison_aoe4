"""Pinned public model downloads, resumable on F:, with publisher hash readback."""
import hashlib
import argparse
import json
from pathlib import Path
import subprocess
import urllib.request
from pipeline import guard, save_json

DEST = Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/tool-cache/local-voices-084/models')
MODELS = {
    'vieneu': ('pnnbao-ump/VieNeu-TTS-v3-Turbo', '61b85e3d937fbbacb387714180e8182823512523'),
    'moss': ('OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano', '6aa02b01e445cc585582cf0ba480bc3ea6c8dd68'),
    'whisper': ('openai/whisper-large-v3-turbo', '41f01f3fe87f28c78e2fbf8b568835947dd65ed9'),
    'phowhisper': ('vinai/PhoWhisper-small', 'a86b604c346caf7148c37512eafe783a16420adb'),
    'phowhisper-medium': ('vinai/PhoWhisper-medium', '55a7e3eb6c906de891f8f06a107754427dd3be79'),
    'phowhisper-large': ('vinai/PhoWhisper-large', 'b9136a44b5f2ca664bd0b8f74baecf1715f6eeeb'),
}


def selected_file(name, rel):
    if rel == '.gitattributes': return False
    return name != 'vieneu' or rel.startswith('update/') or rel in ['config.json', 'README.md', 'speaker_encoder.onnx', 'denoiser.onnx']


def main():
    guard()
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', choices=list(MODELS))
    args = parser.parse_args()
    for name, (repo, revision) in MODELS.items():
        if args.only and name != args.only: continue
        folder = DEST / name
        folder.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f'https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true', timeout=60) as response:
            info = json.load(response)
        save_json(folder / 'publisher-manifest.json', info)
        completed = []
        for item in info['siblings']:
            rel = item['rfilename']
            if not selected_file(name, rel): continue
            path = folder / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            size = item.get('size')
            lfs = item.get('lfs', {}).get('sha256')
            def verified():
                if not path.is_file() or (size is not None and path.stat().st_size != size): return False
                if lfs:
                    with path.open('rb') as stream:
                        return hashlib.file_digest(stream, 'sha256').hexdigest() == lfs
                return True
            if not verified():
                print('DOWNLOAD', name, rel, size, flush=True)
                with (folder / 'download.log').open('ab') as log:
                    result = subprocess.run(['curl.exe', '-fL', '--retry', '5', '--retry-delay', '3',
                                             '--speed-time', '60', '--speed-limit', '1024',
                                             '-C', '-', '-o', str(path), f'https://huggingface.co/{repo}/resolve/{revision}/{rel}'], stdout=log, stderr=log)
                if result.returncode or not verified(): raise RuntimeError(f'Incomplete or invalid model download: {name}/{rel}')
            with path.open('rb') as stream: sha = hashlib.file_digest(stream, 'sha256').hexdigest()
            completed.append(dict(file=rel, bytes=path.stat().st_size, sha256=sha))
            save_json(folder / 'verified-downloads.json', dict(repo=repo, revision=revision, files=completed))
            print('VERIFIED', name, rel, flush=True)


if __name__ == '__main__': main()

"""Verify actual local input bytes and bind audition approval to current audio."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

from download_local_models import MODELS, selected_file
from local_bank import SDK_REVISION, local_guard
from pipeline import StateStore, digest, save_json, wav_metrics
from providers import OUT

RUNTIME = Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/tool-cache/local-voices-084')
BANK = OUT / 'local'


def verify_files(folder, files):
    folder = Path(folder).resolve()
    for item in files:
        path = (folder / item['file']).resolve()
        if not path.is_relative_to(folder) or not path.is_file() or digest(path) != item['sha256']:
            raise RuntimeError('Changed or missing pinned input: ' + str(path))


def verify_inputs(models=('vieneu', 'moss', 'whisper')):
    manifests = {}
    for name in models:
        folder = RUNTIME / 'models' / name
        receipt = json.loads((folder / 'verified-downloads.json').read_text())
        publisher = json.loads((folder / 'publisher-manifest.json').read_text())
        repo, revision = MODELS[name]
        if (receipt['repo'], receipt['revision'], publisher['sha']) != (repo, revision, revision):
            raise RuntimeError('Wrong pinned model revision: ' + name)
        expected = {i['rfilename']: i for i in publisher['siblings'] if selected_file(name, i['rfilename'])}
        if {i['file'] for i in receipt['files']} != set(expected):
            raise RuntimeError('Incomplete pinned input receipt: ' + name)
        for item in receipt['files']:
            lfs_sha = expected[item['file']].get('lfs', {}).get('sha256')
            if lfs_sha and lfs_sha != item['sha256']: raise RuntimeError('Publisher hash mismatch: ' + item['file'])
        verify_files(folder, receipt['files'])
        manifests[name] = receipt
    src = RUNTIME / 'VieNeu-TTS'
    git = ['C:/Program Files/Git/cmd/git.exe', '-c', 'safe.directory=' + src.as_posix(), '-C', str(src)]
    head = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
    if head != SDK_REVISION: raise RuntimeError('SDK checkout revision changed')
    subprocess.run(git + ['diff', '--quiet', 'HEAD', '--', 'src/vieneu', 'src/vieneu_utils'], check=True)
    paths = subprocess.check_output(git + ['ls-files', '-z', 'src/vieneu', 'src/vieneu_utils']).decode().split('\0')
    sdk_files = {}
    site = RUNTIME / 'venv/Lib/site-packages'
    for rel in paths:
        if not rel or Path(rel).suffix not in ['.py', '.json']: continue
        original = src / rel
        installed = site / Path(rel).relative_to('src')
        sha = digest(original)
        if not installed.is_file() or digest(installed) != sha: raise RuntimeError('Installed SDK changed: ' + rel)
        sdk_files[rel] = sha
    versions = {d.metadata['Name'].lower(): d.version for d in importlib.metadata.distributions(path=[str(site)])}
    required = {'vieneu':'3.8.3', 'torch':'2.8.0+cu128', 'torchaudio':'2.8.0+cu128', 'transformers':'4.57.6'}
    if any(versions.get(k) != v for k, v in required.items()): raise RuntimeError('Pinned CUDA/SDK dependency version changed')
    synth = dict(sdk_revision=head, sdk_files=sdk_files, dependencies=required,
                 models={k: v for k, v in manifests.items() if k in ['vieneu', 'moss']})
    fingerprint = hashlib.sha256(json.dumps(synth, sort_keys=True).encode()).hexdigest()
    result = dict(fingerprint=fingerprint, synthesis=synth, verifier_models={k:v for k,v in manifests.items() if k not in ['vieneu','moss']})
    frozen = BANK / 'input-verification.json'
    if frozen.exists():
        if json.loads(frozen.read_text())['fingerprint'] != fingerprint:
            raise RuntimeError('Synthesis inputs changed; use a separate bank revision')
    else:
        save_json(frozen, result)
    return result


def validated_audition_results(results, store, voices, fingerprint, legacy=None):
    valid = {}
    for key, result in results.items():
        row = store.data.get(key)
        if not row or not store.ready(key) or result['sha256'] != row['sha256']: continue
        meta = row['metadata']
        if meta.get('voice') != voices.get(meta.get('role')): continue
        if meta.get('text') != result.get('expected'): continue
        if key != f"{meta.get('role')}-{meta.get('context')}-T{meta.get('take')}": continue
        recorded = meta.get('input_fingerprint')
        attestation = (legacy or {}).get(key, {})
        if recorded != fingerprint and not (attestation.get('fingerprint') == fingerprint and attestation.get('sha256') == row['sha256']): continue
        valid[key] = result
    return valid


def verify_recheck_evidence(row):
    meta=row['metadata'];transcription=meta.get('transcription')
    if not isinstance(transcription,dict) or 'phowhisper_medium' not in transcription:return
    folder=Path(row['path']).parent
    sidecar=folder/'local-recheck-medium.json'
    if not sidecar.is_file() or digest(sidecar)!=meta.get('recheck_sha256'):
        raise RuntimeError('Medium recheck evidence changed or missing')
    proof=json.loads(sidecar.read_text());receipt=proof['model_receipt']
    if (receipt.get('repo'),receipt.get('revision'))!=MODELS['phowhisper-medium']:
        raise RuntimeError('Medium recheck model identity changed')
    prior=folder/'local-verification-v2.json'
    if (proof['sha256']!=row['sha256'] or proof['transcription']!=transcription
            or not prior.is_file() or proof['previous_sha256']!=digest(prior)):
        raise RuntimeError('Medium recheck provenance differs')


def verify_completed_recording(row, job, fingerprint, legacy=None):
    verify_recheck_evidence(row)
    meta = row['metadata']
    if meta.get('job') != job: raise RuntimeError('Completed local job recipe changed')
    folder = Path(row['path']).parent
    original = folder / 'original-float.wav'
    attestation = (legacy or {}).get(str(folder.resolve()), {})
    known = meta.get('input_fingerprint') == fingerprint
    request = folder / 'request-started.json'
    if meta.get('request_sha256'):
        if not request.is_file() or digest(request)!=meta['request_sha256']:
            raise RuntimeError('Completed synthesis request changed')
        from local_work import verify_request_text
        verify_request_text(json.loads(request.read_text()),job)
    certified = (attestation.get('fingerprint') == fingerprint and request.is_file()
                 and attestation.get('request_sha256') == digest(request))
    if not known and not certified: raise RuntimeError('Completed recording input identity changed')
    expected = meta.get('original_sha256') or attestation.get('original_sha256')
    if not expected or not original.is_file() or digest(original) != expected:
        raise RuntimeError('Completed recording original audio changed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--certify-existing-pilot', action='store_true')
    args = parser.parse_args()
    local_guard()
    inputs = verify_inputs(('vieneu', 'moss', 'whisper', 'phowhisper'))
    if args.certify_existing_pilot:
        target = BANK / 'legacy-pilot-input-certification.json'
        if target.exists(): raise RuntimeError('Historical certification is immutable')
        auditions = StateStore(BANK / 'auditions')
        certified = {}
        for key, row in auditions.data.items():
            if not auditions.ready(key): raise RuntimeError('Changed pilot audio: ' + key)
            wav_metrics(Path(row['path']).read_bytes())
            certified[key] = dict(fingerprint=inputs['fingerprint'], sha256=row['sha256'])
        attempts = {}
        for path in (BANK / 'generation').glob('*/attempt-*/request-started.json'):
            original = path.parent / 'original-float.wav'
            if original.is_file():
                attempts[str(path.parent.resolve())] = dict(fingerprint=inputs['fingerprint'], request_sha256=digest(path), original_sha256=digest(original))
        save_json(target, dict(reason='Known first local pilot generated this session; input bytes verified after generation. Subsequent requests capture fingerprint before inference.',
                              fingerprint=inputs['fingerprint'], auditions=certified, generation_attempts=attempts))
    print('LOCAL_INPUTS_VERIFIED', inputs['fingerprint'])


if __name__ == '__main__': main()

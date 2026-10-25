"""Explicit user-authorized exceptions for the final saved spoken candidates.

Never relax the general exact-word gate or the audio integrity gates.
"""
import json
from pathlib import Path
from pipeline import digest, save_json, StateStore, wav_metrics
from local_bank import local_guard
from providers import OUT

BANK = OUT/'local'
RECEIPT = BANK/'minor-speech-exceptions.json'
AUTHORIZATION = "if that 170 remaining voiceline has small issues it's fine"


def valid_exception(row, job):
    marker = row['metadata'].get('minor_speech_exception')
    if not marker or not RECEIPT.is_file() or marker.get('receipt_sha256') != digest(RECEIPT):
        return False
    receipt = json.loads(RECEIPT.read_text(encoding='utf-8'))
    entry = receipt['recordings'].get(job['id'])
    return bool(receipt.get('authorization') == AUTHORIZATION and entry and
                entry['job'] == job and entry['sha256'] == row['sha256'] and
                entry['path'] == row['path'] and
                entry['transcription'] == row['metadata'].get('transcription') and
                entry['request_sha256'] == row['metadata'].get('request_sha256') and
                entry['original_sha256'] == row['metadata'].get('original_sha256') and
                digest(BANK/'recording-manifest.json') == receipt['manifest_sha256'])


def main():
    local_guard()
    if RECEIPT.exists(): raise FileExistsError('Exception evidence is immutable')
    from local_work import render_attempt, verify_request_text
    from local_inputs import verify_completed_recording
    state = StateStore(BANK/'generation')
    jobs = {j['id']:j for j in json.loads((BANK/'recording-manifest.json').read_text())['jobs']}
    fingerprint = json.loads((BANK/'input-verification.json').read_text())['fingerprint']
    candidates = json.loads((BANK/'minor-review-candidates.json').read_text(encoding='utf-8'))
    if len(candidates)>170: raise RuntimeError('Exceptions exceed authorized remaining set')
    records = {}; metadata = {}; known = {r['sha256'] for r in state.data.values()}
    for candidate in candidates:
        job = jobs[candidate['id']]
        if job['id'] in state.data: continue
        if job['kind'] != 'dialogue' or candidate['expected'] != job['text']:
            raise RuntimeError('Exception candidate identity differs')
        folder = Path(candidate['folder'])
        if folder.parent != BANK/'generation'/job['id']: raise RuntimeError('Candidate outside job')
        request = json.loads((folder/'request-started.json').read_text())
        verify_request_text(request,job)
        if request['job']!=job or request['input_fingerprint']!=fingerprint:
            raise RuntimeError('Candidate request changed')
        original = folder/'original-float.wav'
        original_sha = digest(original)
        if original_sha != json.loads((folder/'original.json').read_text())['sha256']:
            raise RuntimeError('Candidate original changed')
        path,metrics = render_attempt(None,job['text'],job['casting']['voice'],.8,folder,True,request['seed'])
        sha=digest(path)
        if sha in known: raise RuntimeError('Duplicate candidate performance')
        known.add(sha)
        verification=json.loads((folder/'local-verification-v2.json').read_text())
        medium=folder/'local-recheck-medium.json'
        if medium.exists(): verification=json.loads(medium.read_text())['transcription']
        if verification.get('expected')!=job['text'] or verification.get('prompted') is not False:
            raise RuntimeError('Candidate transcript identity differs')
        if candidate['actual'] not in [verification.get(k) for k in ('whisper','phowhisper','phowhisper_medium')]:
            raise RuntimeError('Reviewed transcript changed')
        meta=dict(job=job,seed=request['seed'],metrics=metrics,request_sha256=digest(folder/'request-started.json'),
                  original_sha256=original_sha,input_fingerprint=fingerprint,transcription=verification,
                  qualification='User accepted minor speech imperfections; exact-word mismatch retained; no native-speaker approval')
        if medium.exists():meta['recheck_sha256']=digest(medium)
        records[job['id']]=dict(job=job,path=str(path.resolve()),sha256=sha,transcription=verification,
                   request_sha256=meta['request_sha256'],original_sha256=original_sha,
                   nearest_transcript=candidate['actual'],similarity=candidate['score'])
        metadata[job['id']]=meta
    save_json(RECEIPT,dict(schema='ccp-084-minor-speech-exceptions/v1',authorization=AUTHORIZATION,
              manifest_sha256=digest(BANK/'recording-manifest.json'),recordings=records,
              exact_word_approval=False,native_speaker_approval=False,audio_integrity_relaxed=False))
    for key,record in records.items():
        metadata[key]['minor_speech_exception']=dict(receipt_sha256=digest(RECEIPT))
        row=dict(path=record['path'],sha256=record['sha256'],metadata=metadata[key])
        verify_completed_recording(row,jobs[key],fingerprint)
        wav_metrics(Path(row['path']).read_bytes())
        if not valid_exception(row,jobs[key]):raise RuntimeError('Exception attestation failed')
        state.complete(key,row['path'],metadata[key])
    print('MINOR_SPEECH_EXCEPTIONS_ADMITTED',len(records),flush=True)


if __name__=='__main__':main()

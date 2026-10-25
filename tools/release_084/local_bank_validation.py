"""Recheck local recordings and exact six-alternative/three-take pool coverage."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from local_bank import local_manifest, local_guard
from local_efforts import performance_matches, verified_performance
from local_inputs import verify_completed_recording
from local_work import validate_saved_wave
from pipeline import StateStore, digest, save_json, wav_metrics
from providers import OUT
from voice_scope import delivery_manifest

BANK=OUT/'local'


def validate_structure(manifest):
    jobs={j['id']:j for j in manifest['jobs']}
    if len(jobs)!=len(manifest['jobs']): raise ValueError('Duplicate recording identity')
    alias_ids=set();aliases=defaultdict(list)
    for alias in manifest['aliases']:
        if alias['id'] in alias_ids: raise ValueError('Duplicate directed-slot identity')
        alias_ids.add(alias['id'])
        job=jobs.get(alias['job'])
        if not job or job['role']!=alias['role'] or job['age'] not in [alias['age'],'ANY']:
            raise ValueError('Unresolved or mismatched slot recording')
        aliases[(alias['role'],alias['age'],alias['event'])].append(alias['job'])
    seen=set();referenced=set()
    expected={(n,take) for n in range(1,7) for take in ['T1','T2','T3']}
    for pool in manifest['pools']:
        key=(pool['role'],pool['age'],pool['event'])
        ids=pool['jobs']
        if key in seen or len(ids)!=18 or len(set(ids))!=18 or aliases.get(key)!=ids:
            raise ValueError('Incomplete or inconsistent response pool: '+str(key))
        if any(k not in jobs for k in ids): raise ValueError('Unresolved pool recording')
        if {(jobs[k]['phrase_number'],jobs[k]['take']) for k in ids}!=expected:
            raise ValueError('Missing alternative/performance in pool: '+str(key))
        seen.add(key);referenced.update(ids)
    if seen!=set(aliases) or referenced!=set(jobs): raise ValueError('Orphan pool, slot or recording')


def coverage(manifest,valid):
    required={j['id'] for j in manifest['jobs']}
    missing=[j['id'] for j in manifest['jobs'] if j['id'] not in valid]
    complete=sum(set(p['jobs'])<=valid for p in manifest['pools'])
    return dict(required_jobs=len(required),verified_jobs=len(valid & required),missing_jobs=missing,
                required_pools=len(manifest['pools']),complete_pools=complete,
                directed_slots=len(manifest['aliases']),technical_coverage_complete=not missing)


def verify_bank(bank=BANK):
    bank=Path(bank)
    manifest=json.loads((bank/'recording-manifest.json').read_text())
    voices={j['role']:j['casting']['voice'] for j in manifest['jobs']}
    source=json.loads((OUT/'recording-manifest.json').read_text())
    if local_manifest(source,voices)!=manifest: raise ValueError('Local manifest differs from retained source recipes')
    validate_structure(manifest)
    fingerprint=json.loads((bank/'input-verification.json').read_text())['fingerprint']
    legacy=json.loads((bank/'legacy-pilot-input-certification.json').read_text()) if (bank/'legacy-pilot-input-certification.json').exists() else {}
    state=StateStore(bank/'generation'); jobs={j['id']:j for j in manifest['jobs']}
    if set(state.data)-set(jobs): raise ValueError('State contains recordings outside current manifest')
    valid=set();known={};recordings={};errors={}
    def inspect_recording(item):
        key,row=item
        try:
            job=jobs[key]
            if not state.ready(key,job): raise ValueError('Missing or changed playback bytes')
            verify_completed_recording(row,job,fingerprint,legacy.get('generation_attempts'))
            validate_saved_wave(Path(row['path']).parent/'original-float.wav')
            metrics=wav_metrics(Path(row['path']).read_bytes())
            if metrics['sample_rate']!=48000: raise ValueError('Playback must be mono 48 kHz PCM16')
            verification=row['metadata'].get('transcription')
            if isinstance(verification,str):
                if job['kind']!='dialogue' or not performance_matches(job,verification): raise ValueError('Historical transcription mismatch')
            elif isinstance(verification,dict):
                if verification.get('prompted') is not False or verification.get('expected')!=job['text']:
                    raise ValueError('Unverified or prompted transcription')
                if not verified_performance(job,verification):
                    from minor_exceptions import valid_exception
                    if not valid_exception(row,job): raise ValueError('Performance screen failed')
            else: raise ValueError('Missing transcription evidence')
            if job['kind']=='nonverbal_effort' and metrics['duration']>(5 if job['event']=='death' else 3):
                raise ValueError('Effort exceeds short-response duration')
            return key,dict(path=row['path'],sha256=row['sha256'],duration=metrics['duration'],
                            original_sha256=digest(Path(row['path']).parent/'original-float.wav')),None
        except (ValueError,RuntimeError,OSError) as error:return key,None,str(error)
    # Read-only bounded I/O; original/job/audio checks are identical. Aggregate
    # in manifest state order so duplicate admission and diagnostics stay stable.
    with ThreadPoolExecutor(max_workers=8) as readers:
        for index,(key,recording,error) in enumerate(readers.map(inspect_recording,state.data.items()),1):
            if error is not None:errors[key]=error
            elif recording['sha256'] in known:errors[key]='Different recording jobs share identical performance bytes'
            else:
                known[recording['sha256']]=key;valid.add(key);recordings[key]=recording
            if index%500==0:print('LOCAL_RECORDINGS_RECHECKED',index,'of',len(state.data),flush=True)
    scoped=delivery_manifest(manifest)
    required={j['id'] for j in scoped['jobs']}
    archived_recordings=len(recordings)
    recordings={k:r for k,r in recordings.items() if k in required}
    valid &= required
    result=coverage(scoped,valid)
    result.update(errors=errors,recordings=recordings,manifest_sha256=digest(bank/'recording-manifest.json'),
                  user_accepted_minor_speech_exceptions=sum(bool(state.data[k]['metadata'].get('minor_speech_exception')) for k in valid),
                  generation_required_jobs=len(manifest['jobs']),archived_accepted_recordings=archived_recordings,
                  delivery_scope_sha256=digest(bank/'delivery-scope.json') if (bank/'delivery-scope.json').exists() else None,
                  input_fingerprint=fingerprint,
                  verified_by_kind=dict(Counter(jobs[k]['kind'] for k in valid)),
                  audible_quality=False,native_speaker_approval=False,native_compilation=False,package=False,
                  note='Technical coverage only; audible quality and engine acceptance are independent gates.')
    result['technical_coverage_complete'] &= not errors
    return result


def main():
    local_guard()
    parser=argparse.ArgumentParser();parser.add_argument('--require-complete',action='store_true');args=parser.parse_args()
    result=verify_bank()
    previous=BANK/'bank-verification.json'
    if previous.exists():
        history=BANK/'bank-verification-history'/(digest(previous)+'.json')
        history.parent.mkdir(parents=True,exist_ok=True)
        if not history.exists():history.write_bytes(previous.read_bytes())
    save_json(BANK/'bank-verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['recordings','missing_jobs','errors']}))
    print('INVALID_RECORDINGS',len(result['errors']),'MISSING_RECORDINGS',len(result['missing_jobs']))
    if result['errors'] or args.require_complete and not result['technical_coverage_complete']:
        raise SystemExit(1)


if __name__=='__main__':main()

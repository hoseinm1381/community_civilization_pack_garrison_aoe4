"""Select tested Northern preset actors; never recast any started production role."""
import json
from local_audition import DEST
from local_bank import local_manifest, local_guard, actor_qualified_roles
from local_inputs import verify_inputs, validated_audition_results
from pipeline import StateStore, digest, save_json
from providers import OUT


def main():
    local_guard()
    inputs = verify_inputs(('vieneu','moss','whisper','phowhisper'))
    path = DEST / 'recording-manifest.json'
    old = json.loads(path.read_text())
    before = {j['role']:j['casting']['voice'] for j in old['jobs']}
    voices = dict(before, GUNNER='Minh Đức', NAVAL_TRANSPORT='Quốc Tuấn')
    changed = {r for r in voices if voices[r] != before[r]}
    started = {r['metadata']['job']['role'] for r in StateStore(DEST/'generation').data.values()}
    for request in (DEST/'generation').glob('*/attempt-*/request-started.json'):
        started.add(json.loads(request.read_text())['job']['role'])
    if changed & started: raise RuntimeError('Cannot recast started production roles: '+str(changed & started))
    legacy = json.loads((DEST/'legacy-pilot-input-certification.json').read_text())
    results = validated_audition_results(json.loads((DEST/'auditions/local-asr.json').read_text()),
              StateStore(DEST/'auditions'), voices, inputs['fingerprint'], legacy['auditions'])
    qualified = actor_qualified_roles(results, voices)
    if set(voices) - qualified: raise RuntimeError('Selected actors lack two distinct exact-word samples per context: '+str(set(voices)-qualified))
    if changed:
        archive = DEST / 'manifest-revisions' / (digest(path)+'.json')
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists(): archive.write_bytes(path.read_bytes())
        save_json(path, local_manifest(json.loads((OUT/'recording-manifest.json').read_text()), voices))
    save_json(DEST/'casting-selected.json',dict(roles=voices, input_fingerprint=inputs['fingerprint'],
              qualified_roles=sorted(qualified), replaced_unstarted_roles=sorted(changed),
              policy='Actor qualification may cite other roles using the identical preset. Two distinct audio hashes must pass each context. Role recordings remain independent; acting and nonverbals remain unqualified.'))
    print('LOCAL_CAST_SELECTED',len(qualified),'roles; recast only unstarted:',sorted(changed))


if __name__ == '__main__': main()

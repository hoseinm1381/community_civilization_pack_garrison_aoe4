"""Apply the explicitly selected XML delta after native source validation."""
import argparse
import os
from pathlib import Path
from common import OUT, ROOT, files, guard, owned, read, sha, write
from pin_final053 import verify as verify_baseline
from verify_active_source_delta_060 import source_rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--handoff',type=Path,required=True)
    ap.add_argument('--validation',type=Path,required=True)
    args=ap.parse_args();guard()
    receipt=owned(OUT/'qualification/source-application-r1.json')
    frozen=verify_baseline();stage=read(owned(args.handoff))
    validation=read(owned(args.validation))
    if validation['status']!='editable_source_names_and_schemas_native_build_verified':
        raise ValueError('A successful isolated source build is required')
    inputs_path=owned(args.validation.parent/'source-inputs.json')
    if sha(inputs_path)!=validation['source_inputs_sha256']:raise ValueError('Validated source input manifest changed')
    inputs=read(inputs_path)
    if inputs['handoff_sha256']!=sha(args.handoff):raise ValueError('Source build used another handoff')
    entries,selection=source_rows(stage,frozen['inputs']['assets'])
    before=frozen['inputs']['assets']
    actual=files(ROOT/'assets',reject_links=True,exclude_release_060=False)
    expected=dict(before)
    for row in selection:
        p=Path(row['staged']);expected[row['relative']]={'sha256':row['sha256'],'bytes':p.stat().st_size}
    prior=read(receipt) if receipt.exists() else None
    if prior and (prior['handoff_sha256']!=sha(args.handoff) or prior['allowlist']!=entries):
        raise ValueError('Existing application receipt belongs to a different source selection')
    # Resume only a recorded partial application, with every file exactly before or after.
    if not prior and actual!=before:raise ValueError('Active source differs from frozen basis')
    if prior:
        if set(actual)-set(expected):raise ValueError('Unexpected active source additions')
        for name in set(before)|set(expected)|set(actual):
            if actual.get(name) not in (before.get(name),expected.get(name)):
                raise ValueError('Unrelated or partially written source: '+name)
        if actual==expected:
            print('Selected source already applied and verified: '+str(receipt));return
    # Read and validate every payload before the first write.
    payloads=[]
    for row in selection:
        target=ROOT/'assets'/row['relative']
        if not target.resolve().is_relative_to((ROOT/'assets').resolve()):raise ValueError('Escaping source path')
        payload=Path(row['staged']).read_bytes()
        import hashlib
        if hashlib.sha256(payload).hexdigest()!=row['sha256']:raise ValueError('Staged source changed')
        payloads.append((target,payload))
    write(receipt,{'status':'application_started','handoff':str(args.handoff),
        'handoff_sha256':sha(args.handoff),'validation_sha256':sha(args.validation),
        'rollback_basis':str(OUT/'baseline/final053/source/assets'),'allowlist':entries})
    for target,payload in payloads:
        if target.is_file() and target.read_bytes()==payload:continue
        guard();target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_name(target.name+f'.{os.getpid()}.060tmp')
        with temporary.open('xb') as stream:stream.write(payload)
        temporary.replace(target)
    for row in selection:
        if sha(ROOT/'assets'/row['relative'])!=row['sha256']:raise ValueError('Applied source differs')
    write(receipt,{'status':'selected_source_applied','handoff':str(args.handoff),
        'handoff_sha256':sha(args.handoff),'validation_sha256':sha(args.validation),
        'rollback_basis':str(OUT/'baseline/final053/source/assets'),'allowlist':entries,
        'modified_existing':sum(e['before_sha256'] is not None for e in entries),
        'added':sum(e['before_sha256'] is None for e in entries),
        'post_build_exact_native_overlay_required':True})
    print(receipt)


if __name__=='__main__':main()

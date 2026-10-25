"""Fresh building and three-LOD weighted-unit rebuilds using retained inputs.

Historical exporters/validators are reused as libraries with isolated 071 output
paths; original receipts remain byte unchanged. Compressed inputs materialize only
into this attempt's short owned staging directory.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import msvcrt
import subprocess
from consolidate import ROOT, EXT, CFG, TX, STORE, AUDIT, physical, key, dump
from resources import ResourceStore, sha


def unit(label, model):
    sys.path.insert(0, str(ROOT/'tools/release_060'))
    import authored_geometry_060 as legacy
    import common
    work = EXT/'staging/r71'/('unit-'+label)
    out = EXT/'output/release_071'/('unit-'+label)
    assert not work.exists() and not out.exists()
    work.mkdir(parents=True)
    specs = (json.loads((TX/'geometry-specs.json').read_text()) if (TX/'geometry-specs.json').exists()
             else json.loads((AUDIT/'retention-proposal-raw.json').read_text())['qualified_authored_geometry_specs'])
    chosen = next(x for x in specs if x['model'] == model)
    spec = dict(chosen['inputs'])
    for field in ('fbx','action','albedo','authored_snapshot','export_receipt','stock_manifest','template_body','template_project'):
        path=Path(spec[field])
        spec[field]=str(path if path.is_absolute() else ROOT/path)
    store = ResourceStore(STORE) if (STORE/'index.json').exists() else ResourceStore(STORE,{})
    snapshot_original=Path(spec['authored_snapshot'])
    if snapshot_original.parent.name in ('v5b','v5c'):
        predecessors=[snapshot_original.parent.parent/'v4/authored-snapshot.json']
        if snapshot_original.parent.name=='v5c':predecessors.append(snapshot_original.parent.parent/'v5b/authored-snapshot.json')
        for original in predecessors:
            logical=key(original)
            if logical in store.index:
                store.materialize_tree([logical],work/'inputs')
            else:
                import shutil
                target=work/'inputs'/logical;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(original,target)
    for field in ('authored_snapshot','stock_manifest','export_receipt','action'):
        original = Path(spec[field])
        logical = key(original)
        if logical in store.index:
            spec[field] = str(store.materialize_tree([logical],work/'inputs')[logical])
    # Retain exact native rig template and original source hashes. These imports
    # do no building until the explicit prepare/cook calls below.
    common.OWNED = (*common.OWNED, work, out)
    legacy.STAGING = EXT/'staging'
    legacy.OUT = out
    original_paths = legacy.paths
    def paths(spec_path):
        loaded = legacy.read(spec_path)
        base = out/'qualification'
        project = work/'Mods'/loaded['project_key']
        return loaded, base, project, project/'project/source'
    legacy.paths = paths
    spec_path = work/'spec.json'
    dump(spec_path,spec)
    print(json.dumps(legacy.prepare(spec_path)),flush=True)
    # The core wrapper creates/qualifies log and output directories before the
    # native process starts. Direct legacy editor launch can exit before logging.
    base=out/'qualification'
    project=work/'Mods'/spec['project_key']
    prep=json.loads((base/'prepare.json').read_text())
    run_root=work/'run'
    command=[CFG['garrison_core'],'essence','build-mod','--editor',CFG['art_editor'],
             '--mod',str(project/'project'/f"{spec['project_key']}.aoe4mod"),'--run-root',str(run_root),'--timeout','900']
    with legacy.NATIVE_LOCK.open('r+b') as lock:
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        try:
            proc=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=960)
        finally:
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    (out/'native-command.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
    state=json.loads((run_root/'run.json').read_text()) if (run_root/'run.json').exists() else {}
    archives=list((run_root/'output').rglob('*.sga'))
    preserved=all(sha(project/n)==digest for n,digest in prep['source_hashes_after'].items())
    record=dict(status='native_cook_completed_pending_readback' if proc.returncode==0 and state.get('status')=='succeeded' and len(archives)==1 and preserved else 'native_cook_failed_preserved',
                prepare_sha256=sha(base/'prepare.json'),source_bytes_preserved=preserved,state=state,
                archives=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in archives])
    dump(base/'cook.json',record)
    assert record['status']=='native_cook_completed_pending_readback', record
    legacy.STAGING=work
    print(json.dumps(legacy.readback(spec_path)),flush=True)
    print(json.dumps(legacy.compare(spec_path)),flush=True)
    record = json.loads((out/'qualification/comparison.json').read_text())
    assert record['status'] == 'authored_three_lod_geometry_qualified'
    if snapshot_original.parent.name in ('v5b','v5c'):
        assert record['appended_panel_prior_snapshot'], 'Ranged special-case comparison was bypassed'
    dump(out/'receipt.json',dict(passed=True,model=model,comparison_sha256=sha(out/'qualification/comparison.json'),
                               original_spec=chosen['spec'], preserved_source=True, native_match_tested=False))


def building(label):
    path = ROOT/'tools/release_070/integration/cook_building.py'
    module_spec = importlib.util.spec_from_file_location('cook_071_building',path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    # The existing helper strictly checks seven lifecycle parts, source hashes,
    # seated roof/terrain proofs, then uses the supported Garrison native cook.
    module.main('garden',ROOT/'art/exports/buildings_070/garden-r5','071-'+label,'071b-'+label)
    receipt = EXT/'output/release_070/integration'/('garden-071-'+label)/'receipt.json'
    dump(EXT/'output/release_071'/('building-'+label+'.json'),dict(passed=True,receipt=str(receipt),sha256=sha(receipt),
                                                              source_export=str(ROOT/'art/exports/buildings_070/garden-r5')))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['unit','building'])
    p.add_argument('--label',default='v1')
    p.add_argument('--model',default='archer2')
    a=p.parse_args()
    assert a.label.replace('-','').isalnum() and len(a.label)<=8
    if a.stage=='unit': unit(a.label,a.model)
    else: building(a.label)

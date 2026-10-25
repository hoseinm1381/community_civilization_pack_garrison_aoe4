"""Verify delivery, clean exact regenerable readbacks, and write release report."""
import shutil
from pathlib import Path
from common import *

def finalize():
    guarded()
    package = read(OUT / 'package-verification.json')
    audit = read(OUT / 'archive-verification.json')
    checks = read(OUT / 'release-checks.json')
    assert package['status'] == audit['status'] == 'passed'
    for key in ('zip', 'sga'): assert sha(package[key]) == package[key + '_sha256']
    from zipfile import ZipFile
    import hashlib
    with ZipFile(package['zip']) as archive:
        assert archive.testzip() is None
        assert archive.namelist().count('garrison.json') == 1
        assert hashlib.sha256(archive.read(KEY + '.sga')).hexdigest() == package['sga_sha256']
    cooked = read(read(OUT / 'cook-pointer.json')['receipt'])
    assert sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    native_footprint = read(read(OUT / 'footprint/current.json')['receipt'])
    assert native_footprint['status'] == 'passed' and native_footprint['native_validated_instances'] == 255
    assert sha(native_footprint['archive']) == native_footprint['sha256']
    # Both outputs can be recreated by supported `sga-archiver unpack` from
    # retained, measured cook/baseline/candidate archives. No input is removed.
    targets = []
    # Retain incomplete or unrelated attempt folders as diagnostic evidence.
    for target in (OUT / 'readback').glob('*'):
        marker = target / '.complete.json'
        if target.is_dir() and marker.is_file():
            record = read(marker)
            known = {read(OUT / 'candidate.json')['baseline_sha256'],
                     package['sga_sha256'], cooked['cook']['sha256']}
            if record.get('sha256') in known: targets.append(target)
    if Path(cooked['readback']).exists(): targets.append(Path(cooked['readback']))
    removed = []
    for target in targets:
        resolved = target.resolve()
        assert resolved.is_relative_to(OUT.resolve()) and resolved != OUT.resolve()
        assert target.parent == OUT / 'readback' or target.name.startswith('readback-cc021-')
        if not target.exists(): continue
        files = {p.relative_to(target).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
                 for p in target.rglob('*') if p.is_file()}
        removed.append({'path': str(target), 'files': files, 'bytes': sum(r['bytes'] for r in files.values())})
        # Literal, resolved, project-owned directory only; never shell across junctions.
        shutil.rmtree(resolved)
    for key in ('zip', 'sga'): assert sha(package[key]) == package[key + '_sha256']
    receipt = {'status': 'passed', 'zip_sha256': package['zip_sha256'], 'sga_sha256': package['sga_sha256'],
        'reclaimed_bytes': sum(t['bytes'] for t in removed), 'targets': removed,
        'restoration': 'Run tools/build_release_021.ps1 -VerifyOnly to regenerate candidate and baseline verification readbacks. Cook readback: sga-archiver unpack the retained cooked archive to its recorded readback path.',
        'retained': ['all editable sources, exports and recipes', 'stock elephant inputs and source texture dependencies',
            'registered Garrison project, short cook project and cooked archive', 'native logs, model reference evidence and worker previews',
            'candidate archive, packages, prior releases and rollback artifacts']}
    history = OUT / 'cleanup-history'
    history.mkdir(exist_ok=True)
    old = OUT / 'cleanup-verification.json'
    if old.exists(): shutil.copy2(old, history / (sha(old) + '.json'))
    write(old, receipt)
    report = f'''# Community Civilization Pack 0.2.1

Two scratch pit traps replace the above-ground stake arrangements. The Ministry
retains its hall and storage wing with stock-inspired worn timber/plaster,
weathering, varied tile surfaces and a larger outdoor yard containing three
full-size static stock worker elephants. Its placement area changes from 8x8
to 16x16, explicitly approved by the user; costs, research and production stay
unchanged. Pit depth is modeled above the terrain plane; terrain is not excavated.

## Delivery

- ZIP: `{package['zip']}` ({package['zip_bytes']:,} bytes).
- ZIP SHA-256: `{package['zip_sha256']}`.
- SGA SHA-256: `{package['sga_sha256']}`.
- GUID: `{GUID}`; key `{KEY}`; strict `garrison.mod/v1`, version **0.2.1**.
- Accepted 0.2.0 remains in `archives/release_020_user_accepted`; user reports
  it good without specifying scenario coverage. The earlier warning was caused
  by a different tuning-pack selection; no gameplay repair was made.

## Sources and rebuilding

Editable root: `{ROOT}`. New blends/textures: `art/authoring/traps_021` and
`art/authoring/buildings_021/ministry`. Matching `art/exports` folders retain FBX
and maps. Recipes: `art/recipes/release_021`. Scripts: `tools/release_021`.
Heavy data and evidence: `{OUT}`. See STORAGE.md for ownership.

Run `tools/build_release_021.ps1` from the editable root for a fresh cook and
release. Use `-VerifyOnly` for existing-package verification. Both require F:
and the seven expected junctions. Authoring regeneration commands and stock donor
hashes are recorded in worker handoffs/recipes; old editable assets are retained.

## Verification

- Fresh Garrison art cook: `{cooked['cook']['sha256']}`; generated mode/Live Reload off.
- Fresh isolated Content Editor source build validated 255 instances:
  `{native_footprint['sha256']}`. Only its measured Ministry actor is integrated.
- Fresh exact-model native reference cook and readback: `integration/reference-cook.json`.
- Archive baseline: {audit['baseline_members']} members; final: {audit['final_members']}.
- Exactly {len(audit['changed'])} existing members changed: nine visual
  model/geometry/material resources and the Ministry actor's footprint scalars;
  {len(audit['added'])} approved texture members added; {audit['untouched_members']} prior members byte-identical.
- The only gameplay exception is the Ministry site footprint x/y (normal and
  campaign) from 8 to 16. All other active source/compiled gameplay, SCAR,
  localization, bindings, stamps and lifecycle RGO owners remain identical to
  0.2.0. A typed native actor comparison proves the exact scalar delta. Normal edition
  and prior editable art are checked against frozen hashes.
- {checks['tests']['tests']} tests; exactly {len(checks['tests']['failures'])} inherited donor-comparison failures,
  no additional failures, skips or errors. Static tuning validation passes.
- ZIP CRC, unique manifest and embedded SGA hash verified before/after cleanup.
- Removed {receipt['reclaimed_bytes']:,} bytes of regenerable readback output;
  rebuild inputs, cook evidence, previews, deliverables and rollback preserved.

## Installation and native test gates

Import the ZIP into Garrison with AoE4 closed. Enable it and select Community
Civilization Pack in **both** Game Mode and Tuning Pack. Choose China, then Vietnam
in the opening selector. Do not select companion_tuning_pack or Vietnam v2.

Test both traps on different terrain/slopes, upgrades, construction, attacks,
destruction and four-second expiry. Test Ministry construction, repair/damage,
research, worker-elephant emergence, yard clearance, enlarged placement near
other buildings and worker paths, two player colours, near/far views, and
unchanged Chinese buildings. All three yard elephants are decorative/static.

Client import, lobby selection and native appearance/matches have not been run
for 0.2.1 by this build. Multiplayer remains unverified. Reimport accepted 0.2.0
with AoE4 closed to roll back.
'''
    (ROOT / 'docs/RELEASE_021_REPORT.md').write_text(report, encoding='utf-8')
    print('RELEASE_021_FINALIZED', package['zip'], receipt['reclaimed_bytes'], flush=True)

if __name__ == '__main__': finalize()

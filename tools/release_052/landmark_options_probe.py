"""Isolated Castle landmark material diagnostic: static-building options bit only.

This emits three RRMaterial replacements for a native A/B package. It does not
compose an archive, cook assets, or change the active stamp/actor chain.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from common import ARCH, BASELINE, OUT, ROOT, SGA051_SHA, guard, rc, sha

sys.path.insert(0, str(ROOT / 'tools/release_010'))
from garrison_shared import model_variants as mv

RUN = OUT / 'landmarks' / 'options-z1'
RECIPE = ROOT / 'art/recipes/release_052/landmarks/options-z1.json'
MEMBERS = (
    'art/scenario/cccastle/imperial_citadel/model.rrmaterial',
    'art/scenario/cc050/imperial_citadel_campaign/model.rrmaterial',
    'art/scenario/cccastle/resistance_hq/model.rrmaterial',
)
OLD = ['16.0', '0.0', '0.0', '8.0']
NEW = ['16.0', '0.0', '1.0', '8.0']


def options(raw: bytes) -> list[dict]:
    result = []
    for material in rc.parse(raw).roots:
        if material.tag != b'GMat':
            continue
        one = rc.pack_document([rc.pack_chunk(
            material.kind, material.tag, material.payload,
            name=material.name, version=material.version)])
        slots = mv.material_slots(one)
        result.append({
            'name': material.decoded_name,
            'descriptor': next(child.payload[4:].decode('utf-8')
                               for child in material.children if child.tag == b'MatD'),
            'options': slots['parameters']['options']['values'],
            'textures': slots['textures'],
        })
    return result


def extract(member: str) -> bytes:
    target = RUN / 'baseline' / member
    assert target.resolve().is_relative_to(RUN.resolve())
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        proc = subprocess.run([str(ARCH), 'extract-member', str(BASELINE), member,
                               str(target)], capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError(f'Archive extraction failed for {member}: {proc.stderr}')
    return target.read_bytes()


def prove(before: bytes, after: bytes) -> dict:
    assert len(before) == len(after)
    old, new = options(before), options(after)
    assert len(old) == len(new) == 2
    assert [x['descriptor'] for x in old] == ['structure', 'structure_collection']
    assert [x['name'] for x in old] == [x['name'] for x in new]
    assert all(x['options'] == OLD for x in old)
    assert all(x['options'] == NEW for x in new)
    assert all(a['textures'] == b['textures'] for a, b in zip(old, new))
    a = [c for c in rc.walk(rc.parse(before).roots) if not c.children]
    b = [c for c in rc.walk(rc.parse(after).roots) if not c.children]
    assert len(a) == len(b)
    changed = []
    for left, right in zip(a, b):
        assert (left.tag, left.decoded_name) == (right.tag, right.decoded_name)
        if left.payload != right.payload:
            assert left.tag == b'PbTP' and left.decoded_name == 'options'
            changed.append({'material_parameter': left.decoded_name,
                            'old_payload_sha256': hashlib.sha256(left.payload).hexdigest(),
                            'new_payload_sha256': hashlib.sha256(right.payload).hexdigest()})
    assert len(changed) == 2
    byte_offsets = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
    assert len(byte_offsets) == 2
    assert all(before[i:i+1] == b'0' and after[i:i+1] == b'1' for i in byte_offsets)
    return {'old_options': OLD, 'new_options': NEW, 'changed_offsets': byte_offsets,
            'changed_leaf_payloads': changed, 'all_other_bytes_identical': True,
            'texture_bindings_identical': True, 'material_names_descriptors_identical': True}


def main() -> None:
    guard()
    assert sha(BASELINE) == SGA051_SHA
    assert not (RUN / 'receipt.json').exists(), 'Preserve completed candidate; verify existing receipt instead'
    rows = []
    for member in MEMBERS:
        before = extract(member)
        after = mv.rewrite_material(before, {}, {'options': NEW})
        proof = prove(before, after)
        target = RUN / 'payload' / member
        assert target.resolve().is_relative_to(RUN.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(after)
        assert target.read_bytes() == after
        rows.append({'member': member, 'file': str(target), 'sha256': sha(target),
                     'bytes': len(after), 'baseline_sha256': hashlib.sha256(before).hexdigest(),
                     'proof': proof})
    result = {
        'schema': 'ccp.release052.landmark-options-z1-probe/v1',
        'status': 'material_only_candidate_pending_native_match',
        'cause_status': 'qualified mismatch; runtime causality unproven',
        'baseline_sga': str(BASELINE), 'baseline_sga_sha256': SGA051_SHA,
        'payloads': rows,
        'preserved': 'actor, stamp, RGO, RGM, RRGeom, textures, gameplay, geometry and owner-colour bindings',
        'native_test': 'Fresh imported match: both completed custom models at 5000 HP; construction outline alone is insufficient.',
    }
    (RUN / 'receipt.json').parent.mkdir(parents=True, exist_ok=True)
    (RUN / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    RECIPE.parent.mkdir(parents=True, exist_ok=True)
    assert not RECIPE.exists()
    RECIPE.write_text(json.dumps({
        'schema': 'ccp.release052.landmark-material-recipe/v1',
        'source': 'frozen 0.5.1 archive',
        'source_art': 'art/authoring/release_051/landmarks and retained Castle editable originals',
        'edit': 'For both native structure material variants, options Float4 Z is changed from 0.0 (English battering ram template) to 1.0 (stock Castle building and accepted monastery).',
        'script': str(Path(__file__)), 'receipt': str(RUN / 'receipt.json'),
        'scope': list(MEMBERS), 'native_match': 'pending',
    }, indent=2) + '\n', encoding='utf-8')
    print('LANDMARK_OPTIONS_Z1_CANDIDATE', len(rows), str(RUN / 'receipt.json'))


if __name__ == '__main__':
    main()

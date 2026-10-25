"""Verify the isolated unit cook and extract bounded model/animator evidence."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import ARCH, OUT, guard, owned, read, sha, write

COOK_RECEIPT = OUT / 'qualification/archer-matched-control-cook.json'
STOCK_RECEIPT = OUT / 'qualification/archer-variant-readback.json'
EXPORT_RECEIPT = OUT / 'qualification/archer-matched-control-export.json'
READBACK = OUT / 'qualification/archer-matched-control-readback'
RECEIPT = OUT / 'qualification/archer-matched-control-readback.json'
BODY = 'art/scenario/garrison/u60a/units/u60a_archer_control/body/model'
ANIM = 'art/scenario/garrison/u60a/units/u60a_archer_control/animator/animator'
BASE = 'attrib/attachments/attachment_lists/garrison/u60a/u60a_archer_control'
EXPECTED = {
    'attrib/u60a.rgd', BASE + '_animator.rgd', BASE + '_body.rgd',
    'attrib/ebps/garrison/u60a/u60a_archer_control.rgd',
    'attrib/sbps/garrison/u60a/u60a_archer_control.rgd',
    *(ANIM + suffix for suffix in ('.rgm', '.rgo', '.rhka', '.rootmotion')),
    'art/scenario/garrison/u60a/units/u60a_archer_control/body/2561275664931702079_packed.rrtex',
    'art/scenario/garrison/u60a/units/u60a_archer_control/body/3993628325125000551_packed.rrtex',
    'art/scenario/garrison/u60a/units/u60a_archer_control/body/albedo.rrtex',
    *(BODY + suffix for suffix in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial')),
    'scar/u60a/blueprints.scar', 'mod.bin', 'mod.rrtex', 'en/en.ucs',
}


def archiver(*args):
    result = subprocess.run([str(ARCH), *map(str, args)], capture_output=True,
                            text=True, errors='replace', timeout=120)
    if result.returncode:
        raise RuntimeError(f'Archiver {args[0]} failed: {result.stderr.strip()}')
    return json.loads(result.stdout)


def main():
    guard()
    owned(RECEIPT); owned(READBACK)
    if RECEIPT.exists() or READBACK.exists():
        raise FileExistsError('Preserve earlier control archive readback')
    cook = read(COOK_RECEIPT)
    export = read(EXPORT_RECEIPT)
    stock = read(STOCK_RECEIPT)
    if cook['status'] != 'isolated_cook_completed_pending_archive_readback':
        raise ValueError('Isolated cook has not completed')
    archive = Path(cook['cook_record']['archive'])
    if sha(archive) != cook['cook_record']['sha256']:
        raise ValueError('Cook archive changed')
    listing = archiver('list', '--verify', archive)
    members = {m['path']: m for m in listing['members']}
    check = listing['archive']['verification']
    if set(members) != EXPECTED or not check['verified'] or check['crc_mismatches'] or check['sha1_mismatches']:
        raise ValueError('Archive member allowlist or CRC/SHA1 verification failed')
    if len(cook['cook_record']['animated_units']) != 1 or cook['cook_record']['animated_units'][0]['animation']['clips']:
        raise ValueError('Unexpected animation replacements or unit count')
    READBACK.mkdir(parents=True)
    extracted = {}
    for label, member in {
        'body-rgm': BODY + '.rgm', 'body-rgo': BODY + '.rgo',
        'body-rrgeom': BODY + '.rrgeom', 'body-rrmaterial': BODY + '.rrmaterial',
        'animator-rgm': ANIM + '.rgm', 'animator-rhka': ANIM + '.rhka',
        'animator-rootmotion': ANIM + '.rootmotion',
        'body-attachment-rgd': BASE + '_body.rgd',
        'animator-attachment-rgd': BASE + '_animator.rgd',
    }.items():
        target = owned(READBACK / (label + Path(member).suffix))
        archiver('extract-member', archive, member, target)
        extracted[label] = {'member': member, 'path': str(target),
                            'sha256': sha(target), 'bytes': target.stat().st_size}
    stock_geom = stock['extracted']['.rrgeom']
    native_archer_rhka = OUT / 'donors/decoded/archer02/dd37508a5894fb1dbf73/source/art/civilizations/common/humans/archetypes/base_archer/base_archer.rhka'
    if not native_archer_rhka.is_file():
        native_archer_rhka = next((OUT / 'donors/decoded/archer02/dd37508a5894fb1dbf73').rglob('base_archer.rhka'))
    result = {
        'schema': 'ccp-060-archer-matched-control-readback/v1',
        'status': 'isolated_prototype_unit_cook_verified_not_consumer_compatible',
        'archive': str(archive), 'archive_sha256': sha(archive), 'archive_bytes': archive.stat().st_size,
        'exact_member_allowlist': sorted(EXPECTED), 'archive_verification': check,
        'source_fbx_sha256': export['files']['model.fbx']['sha256'],
        'source_action_sha256': export['files']['action.json']['sha256'],
        'generated_unit': cook['cook_record']['animated_units'][0],
        'verified_model_outputs': cook['cook_record']['verified_model_outputs'],
        'extracted': extracted,
        'geometry_comparison': {
            'original_archer_rrgeom_sha256': stock_geom['donor_sha256'],
            'compiled_control_rrgeom_sha256': extracted['body-rrgeom']['sha256'],
            'byte_identical': stock_geom['donor_sha256'] == extracted['body-rrgeom']['sha256'],
            'original_archer_rrgeom_bytes': stock_geom['bytes'],
            'compiled_control_rrgeom_bytes': extracted['body-rrgeom']['bytes'],
            'interpretation': 'Different generated three-LOD FBX mesh encoding is expected; stock donor has 988/490/187 vertices, prototype export clones 988-vertex LOD1 into three remapped LODs. Binary difference alone is not a bind failure.'
        },
        'animator_boundary': {
            'generated_spearman_animator_rhka_sha256': extracted['animator-rhka']['sha256'],
            'original_archer_animator_rhka_path': str(native_archer_rhka),
            'original_archer_animator_rhka_sha256': sha(native_archer_rhka),
            'byte_identical': extracted['animator-rhka']['sha256'] == sha(native_archer_rhka),
            'generated_actor_and_squad_prohibited_from_integration': True,
            'original_archer_animator_consumer_compatibility_proven': False,
        },
        'next_gate': 'Decode compiled private body for complete native bind/weight/LOD comparison and prove original Chinese Archer animator model-only consumption; no gameplay integration yet.'
    }
    write(RECEIPT, result)
    print(json.dumps({'archive_sha256': result['archive_sha256'],
                      'model_outputs': len(result['verified_model_outputs']),
                      'geometry_byte_identical': result['geometry_comparison']['byte_identical'],
                      'animator_byte_identical': result['animator_boundary']['byte_identical']}, indent=2))


if __name__ == '__main__':
    main()

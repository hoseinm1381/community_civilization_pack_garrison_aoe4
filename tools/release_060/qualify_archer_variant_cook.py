"""Read back the isolated stock Archer II variant; never integrate it."""
import json
import subprocess
from pathlib import Path

from common import ARCH, OUT, STAGING, guard, owned, read, sha, write

PROJECT = STAGING / 'v/Mods/v60av'
ARCHIVE = PROJECT / 'dist/v60av.sga'
DONOR = OUT / 'donors/decoded/archer02/dd37508a5894fb1dbf73/source/art/civilizations/chinese/humans/chi_ranged_bow_age02'
READBACK = OUT / 'qualification/archer-variant-readback'
RECEIPT = OUT / 'qualification/archer-variant-readback.json'
ART = 'art/scenario/garrison/v60av/v60av_stock/v60av_stock'
EXPECTED = {
    'attrib/v60av.rgd', 'mod.bin', 'mod.rrtex', 'en/en.ucs',
    *(ART + suffix for suffix in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial')),
}


def call(*args):
    result = subprocess.run([str(ARCH), *map(str, args)], capture_output=True,
                            text=True, errors='replace', check=False, timeout=120)
    if result.returncode:
        raise RuntimeError(f'Archiver {args[0]} failed: {result.stderr.strip()}')
    return json.loads(result.stdout)


def main():
    guard()
    owned(RECEIPT); owned(READBACK)
    if RECEIPT.exists():
        # The first readback already extracted exact archive members. Repair only
        # the donor comparison fields after pinning their actual decoded path.
        prior = read(RECEIPT)
        if prior.get('schema') != 'ccp-060-archer-variant-readback/v1' or sha(prior['archive']) != prior['archive_sha256']:
            raise ValueError('Existing readback receipt/archive changed')
        for suffix, row in prior['extracted'].items():
            target = Path(row['path'])
            donor = DONOR / ('chi_ranged_bow_age02' + suffix)
            if sha(target) != row['sha256']:
                raise ValueError(f'Extracted member changed: {target}')
            row['donor_path'] = str(donor) if donor.is_file() else None
            row['donor_sha256'] = sha(donor) if donor.is_file() else None
            row['byte_identical_to_donor'] = target.read_bytes() == donor.read_bytes() if donor.is_file() else None
        write(RECEIPT, prior)
        print(json.dumps({'status': 'donor_comparison_repaired',
                          'rrgeom_identical': prior['extracted']['.rrgeom']['byte_identical_to_donor']}, indent=2))
        return
    project = read(PROJECT / 'mod-project.json')
    if project.get('key') != 'v60av' or len(project.get('cooks', [])) != 1:
        raise ValueError('Unexpected isolated project/cook record')
    cook = project['cooks'][0]
    if Path(cook['archive']).resolve() != ARCHIVE.resolve() or sha(ARCHIVE) != cook['sha256']:
        raise ValueError('Cook archive identity/hash mismatch')
    listing = call('list', '--verify', ARCHIVE)
    paths = {item['path'] for item in listing['members']}
    verification = listing['archive']['verification']
    if paths != EXPECTED or not verification['verified'] or verification['crc_mismatches'] or verification['sha1_mismatches']:
        raise ValueError('Archive allowlist or stored-byte verification failed')
    if any(cook.get(k) for k in ('assets', 'blueprints', 'derived_blueprints', 'animated_units', 'buildings', 'attribute_overrides')):
        raise ValueError('Cook unexpectedly registered a gameplay resource')
    extracted = {}
    READBACK.mkdir(parents=True, exist_ok=True)
    for suffix in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial'):
        member = ART + suffix
        target = owned(READBACK / ('v60av_stock' + suffix))
        if target.exists():
            raise FileExistsError(target)
        call('extract-member', ARCHIVE, member, target)
        donor = DONOR / ('chi_ranged_bow_age02' + suffix)
        extracted[suffix] = {'member': member, 'path': str(target), 'sha256': sha(target),
                             'bytes': target.stat().st_size,
                             'donor_path': str(donor) if donor.is_file() else None,
                             'donor_sha256': sha(donor) if donor.is_file() else None,
                             'byte_identical_to_donor': target.read_bytes() == donor.read_bytes() if donor.is_file() else None}
    result = {
        'schema': 'ccp-060-archer-variant-readback/v1',
        'status': 'isolated_stock_material_variant_archive_verified_not_runtime_activated',
        'archive': str(ARCHIVE), 'archive_sha256': sha(ARCHIVE), 'archive_bytes': ARCHIVE.stat().st_size,
        'source_model': cook['model_variants'][0]['source'],
        'private_art': cook['model_variants'][0]['art'],
        'archive_verification': verification,
        'exact_resource_allowlist': sorted(EXPECTED),
        'no_gameplay_resources': True,
        'extracted': extracted,
        'qualification_limit': 'This proves Garrison cooked a private stock-material variant with verified archive members. It does not prove redesigned weighted geometry export, integration into the original Chinese Archer animator, ZIP import or native match behavior.'
    }
    write(RECEIPT, result)
    print(json.dumps({'status': result['status'], 'archive_sha256': result['archive_sha256'],
                      'rrgeom_identical': extracted['.rrgeom']['byte_identical_to_donor']}, indent=2))


if __name__ == '__main__':
    main()

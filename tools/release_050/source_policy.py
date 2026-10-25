"""Byte-exact frozen 0.4.0 source policy for the 0.5.0 visual rewires."""
from __future__ import annotations

from pathlib import Path

from common import ROOT, OUT, BASELINE, guarded, read, sha, write
from bindings import SOURCE_BASE, identity_records, identity_xml, specs, transform_actor
from reference_contracts import ACTORS

ASSETS = ROOT / 'assets'
FREEZE = OUT / 'baseline/freeze-baseline.json'


def verify():
    guarded()
    frozen = read(FREEZE)
    assert frozen['schema'] == 'community-civilization-pack/release-050-freeze/v1'
    assert frozen['status'] == 'immutable_pre_050_baseline'
    assert sha(BASELINE) == frozen['accepted_release_040']['embedded_sga']['sha256']
    identities = read(OUT / 'integration/registered-identities.json')
    bound = read(OUT / 'integration/source-bindings.json')
    assert identities['status'] == bound['status'] == 'passed'
    entries = identities['entries']
    assert len(entries) == 9 and len({r['pbgid'] for r in entries.values()}) == 9
    cooked_identities = identity_records()
    canonical = specs()
    assert set(entries) == set(canonical)
    for key, expected in canonical.items():
        assert all(entries[key][field] == expected[field]
                   for field in ('key', 'kind', 'source', 'actors', 'derived_name', 'name')), \
            ('Noncanonical private identity', key)
        assert entries[key]['source_xml'] == (
            f'attrib/instances/attachments/attachment_lists/vietnam/release_050/'
            f'{expected["name"]}.xml')
        assert entries[key]['member'] == (
            f'attrib/attachments/attachment_lists/vietnam/release_050/'
            f'{expected["name"]}.rgd')
        assert entries[key]['pbgid'] == cooked_identities[key]['pbgid']
        assert entries[key]['identity_source_sha256'] == cooked_identities[key]['identity_source_sha256']
    previous = {r['path']: r for r in frozen['active_source_assets']['files']}
    current = {}
    for path in ASSETS.rglob('*'):
        assert not path.is_symlink() and not path.is_junction(), path
        if path.is_file():
            current[path.relative_to(ASSETS).as_posix()] = path
    additions = {r['source_xml'] for r in entries.values()}
    assert len(additions) == 9
    assert set(current) - set(previous) == additions, sorted(set(current) - set(previous) ^ additions)
    for row in entries.values():
        expected = identity_xml(row['pbgid'], row['source'].replace('/', '\\'),
                                'Private 0.5.0 Vietnamese Castle visual identity')
        assert current[row['source_xml']].read_bytes() == expected, row['source_xml']
    actor_sources = {r['source'] for r in bound['actors']}
    exact_actor_sources = {f'attrib/instances/ebps/vietnam/{actor}.xml' for actor in ACTORS}
    monastery = 'attrib/instances/ebps/vietnam/vn_building_unit_religious_control_chi.xml'
    assert len(bound['actors']) == len(actor_sources) == len(exact_actor_sources) == 6
    assert actor_sources == exact_actor_sources
    assert {r['source'] for r in bound['actors'] if r['before_sha256'] != r['after_sha256']} == actor_sources - {monastery}
    monastery_row = next(r for r in bound['actors'] if r['source'] == monastery)
    assert monastery_row['changes'] == [{'kind': 'compiled-visual-overlay-only',
                                        'branches': ['default', 'campaign'], 'tiers': [3, 4]}]
    changed = {}
    for rel, record in previous.items():
        now = current[rel]
        if sha(now) == record['sha256']:
            assert rel not in actor_sources or rel == monastery, ('Expected actor visual edit absent', rel)
            continue
        assert rel in actor_sources, ('Unexpected source edit', rel)
        before = SOURCE_BASE / rel
        assert sha(before) == record['sha256'], ('Frozen source mismatch', rel)
        expected, rewrites = transform_actor(rel, before.read_bytes(), entries)
        assert now.read_bytes() == expected, ('Non-allowlisted actor bytes', rel)
        report = next(r for r in bound['actors'] if r['source'] == rel)
        assert report['before_sha256'] == sha(before) and report['after_sha256'] == sha(now)
        assert report['changes'] == rewrites
        changed[rel] = sha(now)
    assert set(changed) == actor_sources - {monastery}
    proof = {'schema': 'ccp.release050.source-policy/v1', 'status': 'passed',
             'freeze_sha256': sha(FREEZE), 'accepted_sga_sha256': sha(BASELINE),
             'frozen_asset_count': len(previous), 'added': sorted(additions),
             'changed': changed, 'untouched_source_bytes_identical': True,
             'compiled_overlay_actor': monastery,
             'native_compile': 'pending', 'native_runtime': 'unverified'}
    write(OUT / 'source-policy.json', proof)
    return proof


if __name__ == '__main__':
    verify()

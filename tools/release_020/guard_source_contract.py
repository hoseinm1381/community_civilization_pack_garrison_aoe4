"""Assert all 11 private source identities and all 10 actor references as one graph."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from common import GUID, OUT, ROOT, STAGING, guarded, read, sha, write
from inventory import SOURCES
from source_policy import CONSUMERS, verify as verify_sources

sys.dont_write_bytecode = True
WORK = OUT / 'integration'


def verify():
    guarded()
    identities = read(WORK / 'registered-identities.json')
    assert len(identities) == len(SOURCES) == 11
    assert {row['key'] for row in identities} == set(SOURCES)
    assert len({row['pbgid'] for row in identities}) == 11
    allowed = {row['source'] for row in identities}
    assert all(row['source'].startswith('attrib/instances/attachments/attachment_lists/vietnam/release_020/vn_020_')
               for row in identities)
    source_proof = verify_sources(allowed)
    frozen = read(OUT / 'baseline-freeze.json')['source_hashes']['assets']
    prior_ids = set()
    for relative in frozen:
        if not relative.startswith('attrib/instances/') or not relative.endswith('.xml'): continue
        prior = ET.parse(STAGING / 'baseline_source/assets' / relative).getroot()
        for node in prior.iter('uniqueid'):
            if node.get('name') == 'pbgid': prior_ids.add(node.get('value'))
    assert not ({str(row['pbgid']) for row in identities} & prior_ids), 'Private PBG ID collides with accepted 0.1.0 source'
    graph = read(OUT / 'inventory/native-graph.json')
    assert set(graph['consumers']) == set(CONSUMERS)
    by_key = {row['key']: row for row in identities}
    for row in identities:
        path = ROOT / 'assets' / row['source']
        raw = path.read_bytes()
        assert b'encoding=\'utf-8\'' in raw.split(b'?>', 1)[0]
        doc = ET.fromstring(raw)
        assert doc.find("./uniqueid[@name='pbgid']").get('value') == str(row['pbgid'])
        assert doc.find("./instance_reference[@name='parent_pbg']").get('value') == SOURCES[row['key']]
        assert row['final_member'] == 'attrib/attachments/attachment_lists/vietnam/release_020/' + row['name'] + '.rgd'
    actors = []
    for name in CONSUMERS:
        rel = f'attrib/instances/ebps/vietnam/{name}.xml'
        before = ET.parse(STAGING / 'baseline_source/assets' / rel).getroot()
        after = ET.parse(ROOT / 'assets' / rel).getroot()
        original_refs = [node.get('value') for node in before.iter('instance_reference')
                         if node.get('name') in ('attachments', 'animator_attachments')]
        final_refs = [(node.get('value'), node.get('mod')) for node in after.iter('instance_reference')
                      if node.get('name') in ('attachments', 'animator_attachments')]
        assert len(original_refs) == len(final_refs)
        expected = []
        for original in original_refs:
            match = next((key for key, ref in SOURCES.items() if ref == original), None)
            expected.append(('attachments\\attachment_lists\\vietnam\\release_020\\' + by_key[match]['name'],
                             GUID.replace('-', '')) if match else (original, None))
        assert final_refs == expected, (name, final_refs, expected)
        assert any(value.startswith(r'attachments\attachment_lists\vietnam\release_020') for value, _ in final_refs)
        actors.append({'name': name, 'source': rel, 'sha256': sha(ROOT / 'assets' / rel),
                       'private_refs': [value for value, mod in final_refs if mod == GUID.replace('-', '')]})
    result = {'status': 'passed', 'identity_sources': sorted(allowed), 'private_pbgids':
              {row['key']: row['pbgid'] for row in identities}, 'actors': actors,
              'source_assets_sha256': source_proof['source_assets_sha256'],
              'compiled_paths_checked_later_by': 'verify_archive.compiled_actor_proof'}
    write(WORK / 'source-graph-guard.json', result)
    print('SOURCE_020_GRAPH_GUARDED', len(actors), len(identities))
    return result


if __name__ == '__main__': verify()

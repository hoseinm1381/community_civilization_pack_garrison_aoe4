"""Read final archive trap materials and independently decode their cooked atlases."""
import json
import subprocess
from pathlib import Path

from common import CONFIG, OUT, read, sha, write
from garrison_shared import model_variants as mv, relic_chunky as rc, rrtex_decoder


def pixel_stats(path):
    output = subprocess.check_output([CONFIG['python'], '-B', str(Path(__file__).with_name('trap_pixels.py')),
                                      str(path)], text=True)
    return json.loads(output)


def audit(before, after):
    candidate = read(OUT / 'candidate.json')
    assert read(after / '.complete.json')['sha256'] == candidate['sha256']
    assert read(before / '.complete.json')['sha256'] == candidate['baseline_sha256']
    rows = {}
    for key, stem in [('exposed_pit', 'art/scenario/cc010/t1'),
                      ('covered_pit', 'art/scenario/cc010/t2')]:
        final = after / stem / 'model.rrmaterial'
        prior = before / stem / 'model.rrmaterial'
        materials = {}
        for path, version in ((prior, 'accepted021'), (final, 'candidate030')):
            slots = []
            for mat in rc.load(path).roots:
                if mat.tag != b'GMat':
                    continue
                one = rc.pack_document([rc.pack_chunk(mat.kind, mat.tag, mat.payload,
                                                      name=mat.name, version=mat.version)])
                parsed = mv.material_slots(one)
                value = parsed['textures']['albedoTexture'].replace('\\', '/').lower()
                assert value.startswith(stem + ('/v021_' if version == 'accepted021' else '/v030_'))
                assert value.endswith('.rrtex')
                assert all((not name or name == '__default' or
                            name.replace('\\', '/').lower().startswith(stem + ('/v021_' if version == 'accepted021' else '/v030_')))
                           for name in parsed['textures'].values())
                slots.append({'material': mat.decoded_name, 'textures': parsed['textures'],
                              'parameters': parsed['parameters'], 'albedo_member': value})
            assert slots and len({row['albedo_member'] for row in slots}) == 1
            materials[version] = slots
        audit_dir = OUT / 'trap-audit' / 'candidate030' / key
        audit_dir.mkdir(parents=True, exist_ok=True)
        albedos = {}
        for version, root in (('accepted021', before), ('candidate030', after)):
            member = materials[version][0]['albedo_member']
            texture = root / member
            dds = audit_dir / (version + '.dds')
            decoded = rrtex_decoder.decode_rrtex(texture, dds, validate_stream=True)
            assert decoded['stream_validation'] == 'validated'
            assert decoded['source']['sha256'] == sha(texture)
            assert decoded['projection']['sha256'] == sha(dds)
            albedos[version] = {'member': member, 'sha256': sha(texture),
                                'decode': decoded, 'pixels': pixel_stats(dds)}
        old, new = albedos['accepted021'], albedos['candidate030']
        assert old['sha256'] != new['sha256'], key
        assert new['pixels']['size'] == [1024, 1024], (key, new['pixels'])
        assert new['pixels']['mean_luma'] >= 65 and new['pixels']['mean_luma'] > old['pixels']['mean_luma'] + 15
        assert new['pixels']['near_black_fraction'] < .01, (key, new['pixels'])
        rows[key] = {'materials': materials, 'albedos': albedos,
                     'new_material_sha256': sha(final), 'old_material_sha256': sha(prior)}
    receipt = {'status': 'passed', 'source': 'final archive readback',
               'candidate_sga_sha256': candidate['sha256'],
               'baseline_sga_sha256': candidate['baseline_sha256'], 'traps': rows,
               'limit': 'Texture and material audit; game lighting and terrain blending require native match'}
    write(OUT / 'trap-audit/receipt.json', receipt)
    return receipt

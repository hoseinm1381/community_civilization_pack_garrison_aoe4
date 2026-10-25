"""Exact in-game author credit update, preserving CSV syntax and links."""
from __future__ import annotations

from common import ROOT, OUT, guarded, sha, write
from bindings import baseline_bytes

RELATIVE = 'locdb/community_civilization_pack_en.csv'


def apply():
    guarded()
    original = baseline_bytes(RELATIVE)
    text = original.decode('utf-8-sig')
    replacements = {
        'Special thanks to ChillyEmpire for his design concept and assistance during development.':
            'Special thanks to chilly5 for his design concept and assistance during development.',
        'Hossein - youtube.com/@aoe4kingdom': 'hosein81 - youtube.com/@aoe4kingdom',
        'ChillyEmpire - youtube.com/@ChillyEmpire': 'chilly5 - youtube.com/@ChillyEmpire',
    }
    updated = text
    for before, after in replacements.items():
        assert updated.count(before) == 1, before
        updated = updated.replace(before, after)
    raw = updated.encode('utf-8')
    target = ROOT / 'assets' / RELATIVE
    assert target.read_bytes() in (original, raw), 'Unrelated localization drift'
    target.write_bytes(raw)
    result = {'status': 'passed', 'source': RELATIVE,
              'baseline_sha256': sha(OUT / 'source-baseline' / RELATIVE),
              'current_sha256': sha(target), 'exact_replacements': replacements,
              'link_targets_preserved': True, 'csv_serialization_preserved': True}
    write(OUT / 'integration/credits.json', result)
    return result


if __name__ == '__main__':
    apply()

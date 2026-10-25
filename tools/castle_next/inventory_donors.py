"""Resolve and decode the five Chinese Castle ordinary-building donors.

Read-only against official archives and the Garrison asset index. All generated
manifests and decoded-static outputs belong to output/castle_next/donors.
"""
from __future__ import annotations
import argparse, json, sqlite3, subprocess, sys
from pathlib import Path
from common import ROOT, OUT, CORE, CFG, guarded, sha, write

INDEX = Path(r'C:\Users\RS\AppData\Local\Garrison\Kit\game-assets.sqlite3')
CONFIG_FILE = Path(r'C:\Users\RS\AppData\Local\Garrison\Kit\game-assets.local.json')
DONORS = {
    'monastery03': 'art/civilizations/chinese/structures/monastery/chi_monastery_control_age03/chi_monastery_control_age03.rgm',
    'monastery04': 'art/civilizations/chinese/structures/monastery/chi_monastery_control_age04/chi_monastery_control_age04.rgm',
    'siege_workshop03': 'art/civilizations/chinese/structures/siege_workshop/chi_siege_workshop_control_age03/chi_siege_workshop_control_age03.rgm',
    'siege_workshop04': 'art/civilizations/chinese/structures/siege_workshop/chi_siege_workshop_control_age04/chi_siege_workshop_control_age04.rgm',
    'keep03': 'art/civilizations/chinese/structures/keep/chi_keep_control_age03/chi_keep_control_age03.rgm',
}

def resolve(logical: str) -> dict:
    uri = 'file:' + INDEX.as_posix() + '?mode=ro'
    db = sqlite3.connect(uri, uri=True)
    try:
        row = db.execute('select archive_path from resolved_assets where lower(logical_path)=?', (logical.lower(),)).fetchone()
    finally:
        db.close()
    if not row:
        raise FileNotFoundError(f'Garrison game index has no exact logical path: {logical}')
    archive = Path(row[0])
    if not archive.is_file():
        raise FileNotFoundError(f'Indexed archive is missing: {archive}')
    return {'archive': str(archive), 'archive_sha256': sha(archive), 'logical_path': logical}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--decode', action='store_true', help='also run bundled Garrison decode-static for each exact model')
    args = ap.parse_args()
    guarded()
    root = OUT / 'donors'
    decoded_root = root / 'decoded'
    root.mkdir(parents=True, exist_ok=True)
    records = {}
    for name, logical in DONORS.items():
        r = resolve(logical)
        r.update({'name': name, 'resolved': True})
        if args.decode:
            target = decoded_root / name
            target.mkdir(parents=True, exist_ok=True)
            cmd = [CORE, 'convert', 'decode-static', '--logical-path', logical, '--config', CONFIG_FILE,
                   '--index', INDEX, '--output-root', target]
            proc = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, encoding='utf-8', errors='replace')
            if proc.returncode:
                r.update({'decode_status': 'blocked', 'decode_exit_code': proc.returncode,
                          'decode_stdout': proc.stdout[-3000:], 'decode_stderr': proc.stderr[-3000:]})
            else:
                manifests = sorted(target.rglob('decoded-static.json'), key=lambda p: p.stat().st_mtime_ns)
                if not manifests:
                    r.update({'decode_status': 'blocked', 'decode_note': 'core returned success without decoded-static.json'})
                else:
                    manifest = manifests[-1]
                    d = json.loads(manifest.read_text(encoding='utf-8'))
                    r.update({'decode_status': d.get('status'), 'decoded_static_manifest': str(manifest),
                              'decoded_static_manifest_sha256': sha(manifest),
                              'decoded_static': d})
                    for field in ('geometry', 'materials', 'textures', 'selectors', 'structure_collection_contract'):
                        if field in d:
                            r[field] = d[field]
        records[name] = r
    report = {'schema': 'community-civilization-pack/castle-next-stock-donors/v1',
              'status': 'resolved' if all(x['resolved'] for x in records.values()) else 'blocked',
              'index': str(INDEX), 'index_sha256': sha(INDEX), 'index_access': 'SQLite URI mode=ro',
              'config': str(CONFIG_FILE), 'config_sha256': sha(CONFIG_FILE),
              'archive_access': 'read-only extract/convert source; no archive mutations', 'donors': records}
    manifest = root / 'donor-manifest.json'
    write(manifest, report)
    print(json.dumps({'status': report['status'], 'manifest': str(manifest),
                      'donors': {k: {'logical_path': v['logical_path'], 'archive': v['archive'],
                                     'archive_sha256': v['archive_sha256'],
                                     'decode_status': v.get('decode_status'),
                                     'decoded_static_manifest': v.get('decoded_static_manifest')}
                                 for k, v in records.items()}}, indent=2))
    return 0 if report['status'] == 'resolved' else 2

if __name__ == '__main__':
    raise SystemExit(main())

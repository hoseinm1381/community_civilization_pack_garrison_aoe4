"""One bounded private-index decode of the cooked Archer geometry control.

The index is task-owned and contains only the 20 verified private archive
members. It does not modify the installed game asset index or native source.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from common import CFG, CORE, OUT, guard, owned, read, sha, write

READBACK = OUT / 'qualification/archer-matched-control-readback.json'
INDEX = OUT / 'qualification/archer-matched-control-index.sqlite3'
CONFIG = OUT / 'qualification/archer-matched-control-index-config.json'
DEST = OUT / 'qualification/archer-matched-control-decoded'
LOG = OUT / 'qualification/archer-matched-control-decode.log'
RECEIPT = OUT / 'qualification/archer-matched-control-decode.json'
ORIGINAL_INDEX = Path.home() / 'AppData/Local/Garrison/Kit/game-assets.sqlite3'
ORIGINAL_CONFIG = Path.home() / 'AppData/Local/Garrison/Kit/game-assets.local.json'
LOGICAL = 'art/scenario/garrison/u60a/units/u60a_archer_control/body/model.rgm'


def make_index(archive, members):
    source = sqlite3.connect('file:' + ORIGINAL_INDEX.as_posix() + '?mode=ro', uri=True)
    target = sqlite3.connect(INDEX)
    try:
        for table in ('metadata', 'archives', 'assets', 'resolved_assets', 'folders', 'object_types'):
            schema = source.execute('select sql from sqlite_master where type=? and name=?', ('table', table)).fetchone()[0]
            target.execute(schema)
        for key, value in source.execute('select key,value from metadata'):
            if key == 'archive_count': value = '1'
            elif key in ('asset_count', 'resolved_asset_count'): value = str(len(members))
            target.execute('insert into metadata(key,value) values(?,?)', (key, value))
        file = archive.stat()
        archive_id = read(OUT / 'qualification/archer-matched-control-cook.json')['temporary_mod_id'].replace('-', '')
        target.execute('insert into archives values(?,?,?,?,?,?,?,?,?,?,?)',
                       (1, 'cardinal', archive.name, str(archive), file.st_size, file.st_mtime_ns,
                        archive_id, '11', '0', 1, len(members)))
        for index, item in enumerate(members, 1):
            path = item['path']
            if not path.startswith('art/'):
                continue
            folder, name = path.rsplit('/', 1)
            extension = Path(name).suffix.lower()
            template = source.execute('select asset_kind,curated_category,civilization,object_class,object_type from resolved_assets where extension=? limit 1', (extension,)).fetchone()
            if template is None:
                template = ('resource', 'Other', 'Shared / Neutral', 'Resource', 'Resource')
            kind, category, civilization, object_class, object_type = template
            raw_name = item['toc'] + ':' + path.replace('/', '\\')
            target.execute('insert into assets(id,archive_id,logical_path,folder,name,extension,asset_kind,curated_category,civilization,object_class,object_type,size,raw_name,verification,storage,encryption,preview_status,preview_path) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                           (index, 1, path, folder, name, extension, kind, category, civilization,
                            object_class, object_type, item['size'], raw_name, item['verification'],
                            item['storage'], item['encryption'], 'not_generated', None))
            target.execute('insert into resolved_assets(id,logical_path,folder,name,extension,asset_kind,curated_category,civilization,object_class,object_type,size,raw_name,preview_status,preview_path,product,archive,archive_path,provider_archive_id,archive_version,product_version,verified,provider_count) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                           (index, path, folder, name, extension, kind, category, civilization,
                            object_class, object_type, item['size'], raw_name, 'not_generated', None,
                            'cardinal', archive.name, str(archive), archive_id, '11', '0', 1, 1))
        target.commit()
    finally:
        source.close(); target.close()


def main():
    guard()
    for path in (INDEX, CONFIG, DEST, LOG, RECEIPT):
        owned(path)
        if path.exists():
            raise FileExistsError(f'Preserve prior decode attempt: {path}')
    prior = read(READBACK)
    archive = Path(prior['archive'])
    if sha(archive) != prior['archive_sha256'] or len(prior['exact_member_allowlist']) != 20:
        raise ValueError('Cooked archive/readback drift')
    # The exact member list and CRC/SHA1 status were pinned in READBACK.
    # Sizes/storage come from a fresh read-only archiver list of the same hash.
    from common import ARCH
    listed = subprocess.run([str(ARCH), 'list', '--verify', str(archive)],
                            capture_output=True, text=True, errors='replace', timeout=120, check=True)
    data = json.loads(listed.stdout)
    if {m['path'] for m in data['members']} != set(prior['exact_member_allowlist']):
        raise ValueError('Archive member drift')
    make_index(archive, data['members'])
    config = json.loads(ORIGINAL_CONFIG.read_text(encoding='utf-8'))
    if config.get('schema') != 'garrison.game-asset-index/v1':
        raise ValueError('Installed game asset config changed')
    config['index_path'] = str(INDEX)
    CONFIG.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    command = [str(CORE), 'convert', 'decode-static', '--logical-path', LOGICAL,
               '--config', str(CONFIG), '--index', str(INDEX), '--output-root', str(DEST)]
    result = subprocess.run(command, capture_output=True, text=True, errors='replace', timeout=300)
    LOG.write_text('COMMAND: ' + ' '.join(command) + '\nEXIT: ' + str(result.returncode)
                   + '\nSTDOUT:\n' + result.stdout + '\nSTDERR:\n' + result.stderr,
                   encoding='utf-8')
    report = {'schema': 'ccp-060-archer-matched-control-decode-probe/v1',
              'status': 'decoded' if result.returncode == 0 else 'failed_diagnostic',
              'archive_sha256': sha(archive), 'readback_receipt_sha256': sha(READBACK),
              'private_index': str(INDEX), 'private_index_sha256': sha(INDEX),
              'private_config': str(CONFIG), 'private_config_sha256': sha(CONFIG),
              'target': LOGICAL, 'output_root': str(DEST), 'exit_code': result.returncode,
              'log': str(LOG), 'log_sha256': sha(LOG)}
    write(RECEIPT, report)
    print('decode_exit=' + str(result.returncode))
    print((result.stdout or result.stderr)[:2000])


if __name__ == '__main__':
    main()

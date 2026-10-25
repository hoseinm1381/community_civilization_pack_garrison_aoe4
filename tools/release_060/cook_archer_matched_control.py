"""Cook the exact-rig Archer body control as a disposable Spearman prototype.

The generated actor and squad are diagnostic only and never become a Vietnam
consumer. All native mutations use the shared first-byte msvcrt lock.
"""
from __future__ import annotations

import json
import msvcrt
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from common import CFG, CORE, NATIVE_LOCK, OUT, STAGING, guard, owned, read, sha, write

LIBRARY = STAGING / 'u'
PROJECT = LIBRARY / 'Mods/u60a'
PROJECT_FILE = PROJECT / 'mod-project.json'
SOURCE = OUT / 'qualification/archer-matched-control-export.json'
VALIDATION = OUT / 'qualification/archer-matched-control-validate.json'
STOCK_VARIANT = OUT / 'qualification/archer-variant-readback.json'
LOGS = OUT / 'qualification/archer-matched-control-cook-logs'
RECEIPT = OUT / 'qualification/archer-matched-control-cook.json'
EDITOR = Path(CFG['art_editor'])


def step(receipt, label, command, timeout):
    log = owned(LOGS / (label + '.log'))
    if log.exists():
        raise FileExistsError(f'Preserve earlier diagnostic: {log}')
    result = subprocess.run([str(x) for x in command], capture_output=True,
                            text=True, errors='replace', timeout=timeout)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text('COMMAND: ' + ' '.join(str(x) for x in command) + '\nEXIT: '
                   + str(result.returncode) + '\nSTDOUT:\n' + result.stdout
                   + '\nSTDERR:\n' + result.stderr, encoding='utf-8')
    receipt['steps'].append({'label': label, 'returncode': result.returncode,
                             'log': str(log), 'log_sha256': sha(log),
                             'at_utc': datetime.now(timezone.utc).isoformat()})
    write(RECEIPT, receipt)
    if result.returncode:
        raise RuntimeError(f'{label} failed ({result.returncode}); inspect {log}')
    return result.stdout


def main():
    guard()
    owned(LIBRARY); owned(RECEIPT)
    if RECEIPT.exists() or PROJECT_FILE.exists():
        raise FileExistsError('Preserve existing control cook attempt; never retry over it')
    source = read(SOURCE)
    validation = read(VALIDATION)
    stock = read(STOCK_VARIANT)
    if validation['status'] != 'passed' or validation['source_receipt_sha256'] != sha(SOURCE):
        raise ValueError('Control source has not passed the installed validator')
    if source['prototype_key'] != 'english-spearman-2' or not source['generated_spearman_actor_must_not_be_integrated']:
        raise ValueError('Unexpected source control identity')
    source_folder = Path(source['folder'])
    for name, item in source['files'].items():
        path = source_folder / name
        if path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
            raise ValueError(f'Source changed: {path}')
    if stock['archive_sha256'] != sha(stock['archive']) or stock['extracted']['.rrgeom']['byte_identical_to_donor'] is not True:
        raise ValueError('Pinned stock-only control is missing/changed')
    if not EDITOR.is_file():
        raise FileNotFoundError(f'Supported editor overlay missing: {EDITOR}')
    receipt = {'schema': 'ccp-060-archer-matched-control-cook/v1',
               'status': 'prepared_not_cooked',
               'source_receipt': str(SOURCE), 'source_receipt_sha256': sha(SOURCE),
               'validation_receipt': str(VALIDATION), 'validation_receipt_sha256': sha(VALIDATION),
               'stock_variant_readback': str(STOCK_VARIANT), 'stock_variant_archive_sha256': stock['archive_sha256'],
               'project': str(PROJECT), 'lock_protocol': 'msvcrt.LK_NBLCK first byte; tools/castle_next/cook.py parity',
               'generated_actor_and_squad_diagnostic_only': True,
               'original_archer_animation_owner_not_replaced': True,
               'steps': []}
    with NATIVE_LOCK.open('r+b') as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            receipt['status'] = 'native_byte_lock_busy_no_mutation'
            receipt['error'] = str(error)
            write(RECEIPT, receipt)
            raise RuntimeError('Shared native byte lock busy; no mutation') from error
        try:
            receipt['status'] = 'byte_lock_held'
            write(RECEIPT, receipt)
            step(receipt, 'create', [CORE, 'mod-project', 'create', '--library', LIBRARY,
                                     '--name', 'u60a'], timeout=120)
            project = read(PROJECT_FILE)
            if project.get('key') != 'u60a' or project.get('game_mode', {}).get('enabled'):
                raise ValueError('Unexpected isolated project created')
            receipt['temporary_mod_id'] = project['mod_id']
            step(receipt, 'unit-add', [CORE, 'mod-project', 'unit-add', '--project', PROJECT,
                                       '--source', source_folder, '--name', 'u60a_archer_control'], timeout=600)
            project = read(PROJECT_FILE)
            if len(project.get('animated_units', [])) > 1:
                raise ValueError('Unit-add registered unexpected extra units')
            step(receipt, 'cook', [CORE, 'mod-project', 'cook', '--project', PROJECT,
                                   '--editor', EDITOR, '--timeout', '1200'], timeout=1300)
            project = read(PROJECT_FILE)
            if len(project.get('cooks', [])) != 1:
                raise ValueError('Cook record count changed unexpectedly')
            receipt['status'] = 'isolated_cook_completed_pending_archive_readback'
            receipt['cook_record'] = project['cooks'][0]
            receipt['project_file_sha256'] = sha(PROJECT_FILE)
            write(RECEIPT, receipt)
            print(json.dumps({'status': receipt['status'],
                              'archive': receipt['cook_record']['archive'],
                              'archive_sha256': receipt['cook_record']['sha256']}, indent=2))
        except BaseException as error:
            receipt['status'] = 'failed_under_byte_lock'
            receipt['error'] = f'{type(error).__name__}: {error}'
            write(RECEIPT, receipt)
            raise
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == '__main__':
    main()

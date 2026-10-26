"""Build/test the current tracked Garrison release without former owner storage.

Run native, then package. Installed tool paths live in workspace.local.json;
all scratch data stays in the owner's one approved temporary directory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
TEMP = Path('F:/aoe_4_temp/Temp_before_github_push')
NAMESPACE = 'b7fcea91257b408fb9e8ae4d8bc402e1'
FORBIDDEN = (
    'F:/aoe_4_temp/Community_civilization_pack_garrison_temp',
    'E:/age of empires 4 mods/01_Custom_Civilizations/Community_Civilization_pack',
)


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def completed_native(root, instances):
    state = json.loads((root/'run.json').read_text())
    if state['status'] != 'succeeded' or state['exit_code'] != 0 or state.get('timed_out'):
        raise ValueError('Native burn did not complete successfully')
    logs = '\n'.join(p.read_bytes().rstrip(b'\0').decode('utf-8', errors='replace')
                     for p in (root/'logs').glob('*') if p.is_file())
    counts = re.findall(r'(\d+) instances validated', logs)
    archives = list((root/'output').rglob('*.sga'))
    if (not counts or int(counts[-1]) != instances or 'EssenceEditor.exe Error:' in logs
            or not re.search(r'Package \[Archive\] created', logs)
            or len(archives) != 1 or archives[0].stat().st_size < 428):
        raise ValueError('Native editor completion/instance diagnostics differ')
    return state


def is_source_input(rel):
    return rel.startswith('assets/') or ('/' not in rel and rel.endswith('.aoe4mod'))


def source_inventory(root):
    result = {p.name for p in root.glob('*.aoe4mod')}
    directories = [root/'assets']
    while directories:
        directory = directories.pop()
        if directory.is_symlink() or directory.is_junction():
            raise ValueError('Source inputs must not depend on linked directories')
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_symlink() or entry.is_junction():
                    raise ValueError('Linked source input is not self-contained: '+entry.path)
                if entry.is_dir(follow_symlinks=False):
                    directories.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    result.add(Path(entry.path).relative_to(root).as_posix())
    return result


def verify_source_snapshot(root, tracked, indexed):
    expected = {k[7:] for k in indexed if k.startswith('source/') and is_source_input(k[7:])}
    current = {rel for rel in tracked if is_source_input(rel)}
    if current != expected or source_inventory(root) != current:
        raise ValueError('Source inventory changed or contains untracked inputs; update the release delta')
    for rel in current:
        if file_sha(root/rel) != indexed['source/'+rel]['sha256']:
            raise ValueError('Update compiled delta before rebuilding changed source: '+rel)
    return len(current)


def deny_former_roots(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = str(Path(os.fsdecode(args[0])).resolve()).replace('\\', '/').removeprefix('//?/').lower()
        if any(path == p.lower() or path.startswith(p.lower()+'/') for p in FORBIDDEN):
            raise PermissionError('Former owner-root access prohibited: '+path)


def run(command, log):
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run(list(map(str, command)), cwd=ROOT, stdout=stream,
                                stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Command failed; inspect '+str(log))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['native', 'package'])
    args = parser.parse_args()
    cfg = json.loads((ROOT/'workspace.local.json').read_text(encoding='utf-8-sig'))
    TEMP.mkdir(exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = str(TEMP)
    tempfile.tempdir = str(TEMP)
    sys.addaudithook(deny_former_roots)
    tracked = subprocess.check_output([cfg['git_path'], '-c', 'safe.directory='+str(ROOT),
                                      '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')
    tracked = list(filter(None, tracked))
    import portable
    from current_package import rebuild, apply_verification_delta
    from store import write_json
    reader = portable.reader()
    try:
        source_count = verify_source_snapshot(ROOT, tracked, reader.doc['files'])
        if args.command == 'native':
            snapshot = {p: file_sha(ROOT/p) for p in source_inventory(ROOT)}
            write_json(TEMP/'native-inputs.json', snapshot)
            run([cfg['garrison_core'], 'essence', 'build-mod', '--editor', cfg['content_editor'],
                 '--mod', ROOT/'community_civilization_pack.aoe4mod', '--run-root', TEMP/'native',
                 '--timeout', '900'], TEMP/'native-cli.log')
            completed_native(TEMP/'native', 658)
            print('NATIVE_CURRENT_SOURCE_VERIFIED', source_count, flush=True)
            return
        state = completed_native(TEMP/'native', 658)
        if Path(state['mod']['path']).resolve() != (ROOT/'community_civilization_pack.aoe4mod').resolve():
            raise ValueError('Native run used another source workspace')
        frozen = json.loads((TEMP/'native-inputs.json').read_text())
        current = {p: file_sha(ROOT/p) for p in source_inventory(ROOT)}
        if not frozen or frozen != current:
            raise ValueError('Source changed after the native burn')
        archives = list((TEMP/'native/output').rglob('*.sga'))
        if len(archives) != 1:
            raise ValueError('Expected exactly one native source archive')
        native = archives[0]
        listing = json.loads(subprocess.check_output([cfg['archive_tool'], 'list', str(native), '--verify']))
        if listing['archive']['name'] != NAMESPACE or not listing['archive']['verification']['verified']:
            raise ValueError('Native archive identity/verification differs')
        readback = TEMP/'native-readback'
        if readback.exists():
            raise FileExistsError('Inspect previous native-readback before retrying')
        readback.mkdir()
        run([cfg['archive_tool'], 'extract', native, readback, '--filter', '.'], TEMP/'native-extract.log')
        policy = reader.doc['milestone']
        expected = apply_verification_delta(json.loads(reader.read(policy['verification'])),
                                             policy.get('verification_delta', {}))
        members = [k for k in expected['member_sha256'] if
                   (k.startswith('attrib/') and '/persia/' in k) or
                   k.startswith('ui/icons/persia/') or k == 'en/en.ucs']
        if len(members) != 309:
            raise ValueError('Persia compiled-resource closure differs')
        for member in members:
            if file_sha(readback/member) != expected['member_sha256'][member]:
                raise ValueError('Fresh native payload differs from stored release: '+member)
        destination = TEMP/'package'
        rebuild(SimpleNamespace(destination=destination, archive_tool=Path(cfg['archive_tool'])), reader)
        output = ROOT/'output/current'
        output.mkdir(parents=True, exist_ok=True)
        names = ['community_civilization_pack.sga', 'community_civilization_pack-0.9.0.zip',
                 'garrison.json', 'START-HERE.txt', 'compact-rebuild-proof.json', 'verification.json']
        for name in names:
            target = output/name
            if target.exists():
                raise FileExistsError('Existing delivery preserved: '+str(target))
        for name in names:
            shutil.move(str(destination/name), str(output/name))
        write_json(output/'github-build-proof.json', dict(version='0.9.0',
            source_inputs=source_count, source_root=str(ROOT), scratch_root=str(TEMP),
            python_open_audit_denied_roots=list(FORBIDDEN),
            subprocess_scope='Explicit repository/temp paths; no OS sandbox or subprocess I/O tracing',
            native_source_compile=True,
            native_duration_seconds=state['duration_seconds'], native_instances=658,
            fresh_native_payloads_matching=members, sga_sha256=expected['sga_sha256'],
            zip_sha256=expected['zip_sha256'], final_members=len(expected['member_sha256']),
            native_game_test=False, full_art_recook=False, new_speech_synthesis=False))
        print('GITHUB_ONLY_BUILD_VERIFIED', output, flush=True)
    finally:
        reader.close()


if __name__ == '__main__':
    main()

"""Read-only comparison of packaged SCAR against this editable project.

Uses an existing SGA-V10 runtime; never builds, extracts, or installs anything.
"""
import argparse
import hashlib
import sys
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path


def normalized(data):
    return '\n'.join(data.decode('utf-8-sig').splitlines()).encode('utf-8')


def compare_runtime(archive, project_root):
    entries = {p.lstrip('/').lower(): p for p in archive.walk.files()}
    mismatches = []
    for source in sorted((project_root / 'assets/scar').rglob('*.scar')):
        relative = source.relative_to(project_root / 'assets').as_posix()
        packed = entries.get(relative.lower())
        if packed is None:
            print('MISSING', relative)
            mismatches.append(relative)
            continue
        expected = normalized(source.read_bytes())
        actual = normalized(archive.readbytes(packed))
        same = expected == actual
        print('MATCH' if same else 'DIFF', relative,
              'source=' + hashlib.sha256(expected).hexdigest(),
              'package=' + hashlib.sha256(actual).hexdigest())
        if not same:
            mismatches.append(relative)
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--runtime', required=True, type=Path,
                        help='Existing runtime containing site-packages and SGA-V10/src.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    from workspace_support import check_storage, configuration
    check_storage(root, configuration())
    runtime_paths = [args.runtime / 'site-packages', args.runtime / 'SGA-V10/src']
    if not all(p.is_dir() for p in runtime_paths):
        parser.error('Runtime is incomplete; no dependencies were installed.')
    sys.path[:0] = [str(p) for p in runtime_paths]
    warnings.filterwarnings('ignore', message='pkg_resources is deprecated as an API.*')
    from relic.sga.core.definitions import Version
    from relic.sga.v10 import EssenceFSHandler

    project = ET.parse(root / 'community_civilization_pack.aoe4mod').getroot()
    expected_guid = next(n.text for n in project if n.tag.rsplit('}', 1)[-1] == 'ID').replace('-', '').lower()
    print('package_sha256=' + hashlib.sha256(args.package.read_bytes()).hexdigest())
    with args.package.open('rb') as stream:
        header = stream.read(12)
        if len(header) != 12 or header[:8] != b'_ARCHIVE':
            parser.error('Not an SGA archive.')
        major, minor = int.from_bytes(header[8:10], 'little'), int.from_bytes(header[10:12], 'little')
        if (major, minor) not in ((10, 0), (11, 0)):
            parser.error(f'Unsupported SGA version {major}.{minor}.')
        EssenceFSHandler.version = Version(major, minor)
        stream.seek(0)
        archive = EssenceFSHandler.read(stream)
        archive_guid = archive.getmeta('essence')['name'].replace('-', '').lower()
        print('archive_id=' + archive_guid)
        if archive_guid != expected_guid:
            print('WRONG_ARCHIVE_ID', archive_guid, 'expected=' + expected_guid)
            return 1
        mismatches = compare_runtime(archive, root)
    print(f'Runtime source comparison: {len(mismatches)} mismatch(es).')
    print('This checks SCAR source only; compiled tuning and native behavior need separate validation.')
    return 1 if mismatches else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'PACKAGE_READ_FAILED {type(error).__name__}: {error}', file=sys.stderr)
        raise SystemExit(2)

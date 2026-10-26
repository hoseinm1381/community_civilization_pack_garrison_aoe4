"""Compare existing tests with frozen source reads, without restoring live files.

The baseline overlay covers Python Path/builtin file reads and Path enumeration;
subprocesses and native APIs still see the current workspace. This is a diagnostic
comparison, not a replacement for preservation hashes or native game testing.
"""
import builtins
import contextlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/persia_port_20261026'
sys.path.insert(0, str(ROOT / 'tests'))


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        elif not item.id().startswith('test_persia_'):
            yield item


def run(baseline=False):
    with zipfile.ZipFile(WORK / 'normal-before.zip') as archive:
        frozen = {(ROOT / name).resolve(): archive.read(name) for name in archive.namelist()
                  if name.startswith('assets/') or name in ('README.md', 'Vietnam_v2.aoe4mod')}
    new = {p.resolve() for p in (ROOT / 'assets').rglob('*') if p.is_file() and p.resolve() not in frozen}
    original_open, original_path_open = builtins.open, Path.open
    original_glob, original_rglob = Path.glob, Path.rglob

    def intercept(file, mode='r', *args, **kwargs):
        if isinstance(file, (str, bytes, Path)) and not any(flag in mode for flag in 'wax+'):
            path = Path(file).resolve()
            if path in frozen:
                data = frozen[path]
                if 'b' in mode:
                    return io.BytesIO(data)
                encoding = kwargs.get('encoding') or (args[1] if len(args) > 1 else None) or 'utf-8'
                return io.TextIOWrapper(io.BytesIO(data), encoding=encoding, newline=kwargs.get('newline'))
        return original_open(file, mode, *args, **kwargs)

    def path_open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        return intercept(self, mode, buffering=buffering, encoding=encoding, errors=errors, newline=newline)

    with contextlib.ExitStack() as stack:
        if baseline:
            stack.enter_context(patch('builtins.open', intercept))
            stack.enter_context(patch.object(Path, 'open', path_open))
            stack.enter_context(patch.object(Path, 'glob', lambda self, pattern, **kw: (p for p in original_glob(self, pattern, **kw) if p.resolve() not in new)))
            stack.enter_context(patch.object(Path, 'rglob', lambda self, pattern, **kw: (p for p in original_rglob(self, pattern, **kw) if p.resolve() not in new)))
        label = 'baseline-overlay' if baseline else 'current-existing'
        with original_open(WORK / (label + '.txt'), 'w', encoding='utf-8') as output:
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                suite = unittest.TestSuite(flatten(unittest.defaultTestLoader.discover(str(ROOT / 'tests'))))
                result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    return {'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
            'skipped': len(result.skipped), 'failed_ids': sorted({test.id() for test, _ in result.failures + result.errors})}


if __name__ == '__main__':
    before, after = run(True), run(False)
    report = {'baseline_overlay': before, 'current': after,
              'new_failed_ids': sorted(set(after['failed_ids']) - set(before['failed_ids'])),
              'resolved_failed_ids': sorted(set(before['failed_ids']) - set(after['failed_ids'])),
              'limitation': 'Python source-read/enumeration overlay; subprocesses and native APIs see current workspace. Historical fixtures are not rewritten.'}
    (WORK / 'historical-suite-comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('baseline_overlay', 'current')}, indent=2))
    print('baseline', {k:v for k,v in before.items() if k!='failed_ids'})
    print('current', {k:v for k,v in after.items() if k!='failed_ids'})

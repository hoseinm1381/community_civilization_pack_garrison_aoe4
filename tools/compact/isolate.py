"""Run a Python workflow with the original owner workspace/history inaccessible.

This test blocks Python file/directory access; native subprocesses receive only
explicit new-workspace paths, and their manifests/logs are independently checked.
"""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--deny-root',action='append',required=True)
    p.add_argument('--proof',type=Path,required=True)
    p.add_argument('command',nargs=argparse.REMAINDER)
    args = p.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        p.error('A Python script and its arguments are required after --')
    denied = [os.path.normcase(os.path.abspath(x)).rstrip('\\/') for x in args.deny_root]
    attempts = []

    def hook(event, values):
        if event not in ('open','os.listdir','os.scandir') or not values or not isinstance(values[0],(str,bytes,os.PathLike)):
            return
        value = os.path.normcase(os.path.abspath(os.fsdecode(values[0]))).removeprefix('\\\\?\\')
        if any(value == base or value.startswith(base+os.sep) for base in denied):
            attempts.append(value)
            raise PermissionError('Original owner workspace access blocked by isolation test: '+value)

    sys.addaudithook(hook)
    sys.argv = command
    runpy.run_path(command[0],run_name='__main__')
    args.proof.parent.mkdir(parents=True,exist_ok=True)
    args.proof.write_text(json.dumps(dict(passed=True,blocked_original_roots=denied,
         attempted_original_accesses=attempts,script=command[0],
         scope='Python file/directory access; native subprocess inputs inspected separately'),indent=2)+'\n')


if __name__ == '__main__':
    main()

"""Reconstruct the accepted package independently of the parallel native burn."""
import json,sys
from pathlib import Path
from types import SimpleNamespace
import portable,github_build
from current_package import rebuild
def main():
 cfg=json.loads((portable.ROOT/'workspace.local.json').read_text());sys.addaudithook(github_build.deny_former_roots)
 r=portable.reader()
 try:rebuild(SimpleNamespace(destination=Path(cfg['temp_root'])/'github106/package',archive_tool=Path(cfg['archive_tool'])),r)
 finally:r.close()
if __name__=='__main__':main()

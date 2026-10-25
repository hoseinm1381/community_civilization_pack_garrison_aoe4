"""Serialize isolated background Blender against the project's native build lock."""
import msvcrt,re
from common import *
if __name__=='__main__':
 guard()
 script=Path(sys.argv[1]).resolve();args=sys.argv[2:]
 lock=Path(CFG['external_root'])/'output/release_020/native-build.lock'
 with lock.open('r+b') as f:
  msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
  try:print(run(re.sub('[^a-zA-Z0-9_.-]','_',script.stem+'-'+('-'.join(args) or 'inspect')),[CFG['blender'],'--background','--python-exit-code','1','--python',script,'--',*args],timeout=1800)[-2500:])
  finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)

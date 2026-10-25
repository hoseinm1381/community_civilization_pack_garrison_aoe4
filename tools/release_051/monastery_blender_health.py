"""Bounded task-owned factory Blender startup probe."""
from __future__ import annotations
import os, subprocess, time
from common import CONFIG, OUT, guarded, write

if __name__=='__main__':
    guarded(); start=time.monotonic()
    config=OUT/'monastery/isolated-blender-config';config.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env['BLENDER_USER_CONFIG']=str(config)
    command=[CONFIG['blender'],'--background','--factory-startup','--disable-autoexec','-t','1','-noaudio','--python-expr',
             'import bpy; print("CCP051_BLENDER_READY", bpy.app.version_string, flush=True)']
    try:
        run=subprocess.run(command,capture_output=True,text=True,timeout=75,env=env)
        result={'status':'passed' if run.returncode==0 and 'CCP051_BLENDER_READY' in run.stdout else 'failed',
                'returncode':run.returncode,'seconds':round(time.monotonic()-start,2),
                'stdout_tail':run.stdout[-2000:],'stderr_tail':run.stderr[-2000:]}
    except subprocess.TimeoutExpired as error:
        result={'status':'timeout','seconds':round(time.monotonic()-start,2),
                'stdout_tail':(error.stdout or b'')[-2000:].decode(errors='replace'),
                'stderr_tail':(error.stderr or b'')[-2000:].decode(errors='replace')}
    write(OUT/'monastery/blender-health-isolated.json',result)
    print(result)

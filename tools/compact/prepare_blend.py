"""Run in a separate Blender background process, with --disable-autoexec.

blender --background --disable-autoexec model.blend --python prepare_blend.py --
    --workspace C:/work/source/workspace.compact.json --destination C:/work/model-portable.blend
"""
import argparse
import json
from pathlib import Path
import sys


def main():
    import bpy
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--destination',type=Path,required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.destination.exists():
        raise FileExistsError('Existing Blender source preserved')
    cfg = json.loads(args.workspace.read_text())
    origins = sorted(cfg['origins'],key=lambda row:-len(row[0]))
    missing = []
    remapped = []
    for datablock in [*bpy.data.images,*bpy.data.libraries]:
        path = getattr(datablock,'filepath','')
        if not path or getattr(datablock,'packed_file',None) or getattr(datablock,'source',None) in ('GENERATED','VIEWER'):
            continue
        value = bpy.path.abspath(path).replace('\\','/')
        for old,new in origins:
            old = old.replace('\\','/').rstrip('/')
            if value.lower().startswith(old.lower()+'/'):
                value = new.replace('\\','/')+value[len(old):]
                break
        if not Path(value).is_file():
            missing.append(dict(name=datablock.name,path=value))
        else:
            datablock.filepath = value
            remapped.append(dict(name=datablock.name,path=value))
    if missing:
        raise ValueError('Unresolved Blender inputs: '+json.dumps(missing))
    args.destination.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.destination))
    args.destination.with_suffix('.paths.json').write_text(json.dumps(dict(remapped=remapped,missing=[]),indent=2)+'\n')
    print('BLENDER_PORTABLE_COPY_VERIFIED',len(remapped))


if __name__ == '__main__':
    main()

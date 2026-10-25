"""Blender background audit of image references without loading geometry or saving scenes."""
import argparse
import json
from pathlib import Path
import sys


def main():
    import bpy
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    cfg = json.loads(a.workspace.read_text())
    source = Path(cfg['source'])
    paths = sorted((source/'art/authoring').rglob('*.blend'))
    missing = []
    checked = 0
    for index,path in enumerate(paths,1):
        with bpy.data.libraries.load(str(path),link=False) as (data,target):
            target.images = data.images
        for image in target.images:
            if image is None or image.packed_file or image.source in ('GENERATED','VIEWER') or not image.filepath:
                continue
            old = image.filepath
            value = str(path.parent/old[2:]) if old.startswith('//') else old
            value = value.replace('\\','/')
            for start,end in sorted(cfg['origins'],key=lambda v:-len(v[0])):
                start = start.replace('\\','/').rstrip('/')
                if value.lower().startswith(start.lower()+'/'):
                    value = end.replace('\\','/')+value[len(start):]
                    break
            checked += 1
            if not Path(value).is_file():
                missing.append(dict(blend=str(path),image=image.name,original=old,resolved=value))
            bpy.data.images.remove(image)
        if index%25 == 0:
            print('BLEND_INPUTS_CHECKED',index,'MISSING',len(missing),flush=True)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(dict(blends=len(paths),external_images=checked,missing=missing,
          geometry_cook=False,scenes_saved=False),indent=2)+'\n')
    print('BLEND_DEPENDENCY_AUDIT',len(paths),len(missing),flush=True)
    if missing:
        raise RuntimeError('Some editable Blender inputs are unresolved; inspect report')


if __name__ == '__main__':
    main()

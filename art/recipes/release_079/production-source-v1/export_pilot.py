"""Isolated Blender: retain old geometry, repair only skeletal contracts/LOD weights."""
import sys,importlib,shutil
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from rig_contract import read_contract,rig_text,fold_weights

def addon(name):
    key=next(k for k in bpy.context.preferences.addons.keys() if k.endswith('.garrison'))
    return importlib.import_module(key+'.'+name)

def main():
    guard();donors=read(OUT/'donors.json');selection={}
    revision=sys.argv[sys.argv.index('--')+1]
    if not __import__('re').fullmatch('pilot-r[0-9]+',revision):raise ValueError('Invalid revision')
    for family in ('buffalo','skirmisher2','skirmisher3','skirmisher4'):
        source=ROOT/'art/authoring/release_076'/family/'r3/model.blend'
        dest=EXPORT/family/revision;art=ART/family/revision
        if dest.exists() or art.exists():raise FileExistsError(dest)
        dest.mkdir(parents=True);art.mkdir(parents=True)
        old=read(ROOT/'output/release_076/art'/family/'r3/export.json')
        assert sha(source)==old['source_sha256']
        bpy.ops.wm.open_mainfile(filepath=str(source))
        meshes=[bpy.data.objects['body_lod'+str(i)] for i in (1,2,3)]
        rig=next(m.object for m in meshes[0].modifiers if m.type=='ARMATURE')
        rig.animation_data_clear();rig.data.pose_position='REST'
        contract=read(OUT/'art'/family/'pilot-r1/export.json')['donor_contract']
        folded=[]
        for lod,obj in enumerate(meshes,1):
            names={g.index:g.name for g in obj.vertex_groups}
            samples=[{names[g.group]:g.weight for g in v.groups} for v in obj.data.vertices]
            before=[tuple(v.co) for v in obj.data.vertices]
            changes=0
            if lod>1:
                values=[fold_weights(ws,contract,lod) for ws in samples]
                changes=sum(a!=b for a,b in zip(samples,values));obj.vertex_groups.clear()
                for i,ws in enumerate(values):
                    for n,w in ws.items():(obj.vertex_groups.get(n) or obj.vertex_groups.new(name=n)).add([i],w,'REPLACE')
            assert before==[tuple(v.co) for v in obj.data.vertices]
            folded.append({'lod':lod,'changed_weight_vertices':changes,'geometry_unchanged':True})
        for p in (ROOT/'art/exports/release_076'/family/'r3').glob('*.png'):shutil.copyfile(p,dest/p.name)
        records=addon('unit_export').skeleton_records(rig)
        addon('unit_export').export_unit_model(rig,meshes,dest/'model.fbx',records,three_lods=False)
        (dest/'model.rig').write_text(rig_text(contract),encoding='utf-8')
        bpy.ops.wm.save_as_mainfile(filepath=str(art/'model.blend'))
        write(OUT/'art'/family/revision/'export.json',{'family':family,'revision':revision,'source':str(art/'model.blend'),'source_sha256':sha(art/'model.blend'),'export':str(dest),'files':{p.name:sha(p) for p in dest.iterdir() if p.is_file()},'lod_triangles':old['lod_triangles'],'folding':folded,'donor_contract':contract,'native_acceptance':False,'purpose':'old geometry diagnostic pilot, not final079 art'})
        selection[family]=revision
    write(RECIPES/'pilot-selection.json',selection)
    print('PILOT_R2_EXPORTED',len(selection))

if __name__=='__main__':main()

"""Freeze current detailed art evidence without promoting it to runtime proof."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3]
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    versions={'garden':('garden-r5','garden-r4',59808),'foundry':('foundry','foundry-r3',149035),'wonder':('wonder-r4','wonder-r4',61358),'university':('university-r6','university-r6',42686)}
    assets={}
    for kind,(folder,review,stock_tris) in versions.items():
        source=ROOT/'art/exports/buildings_070'/folder
        r=json.loads((source/'source-receipt.json').read_text())
        healthy=r['healthy_triangle_count'] if kind=='garden' else r['healthy_triangles']
        for rel,h in r['files_sha256'].items():assert sha(source/rel)==h,(kind,rel)
        assert sorted(r['fbx_model_nodes'])==['garrison_part_%04d'%i for i in range(7)]
        assert r['selector_parts']=={'healthy':[0,1,4,5,6],'heavy_damage':[0,3],'ruins':[2]}
        audit=json.loads((OUT/'detail'/review/'audit.json').read_text())
        assert audit['states']['healthy']['triangles']==healthy
        for p in audit['parts']:assert p['finite'] and p['uv_finite'] and p['uv_inside_atlas'] and not p['zero_area_faces']
        total=healthy+(stock_tris if kind=='university' else 0)
        cap=61358 if kind=='university' else stock_tris
        assert total<=cap
        assets[kind]={'export_directory':str(source),'source_receipt_sha256':sha(source/'source-receipt.json'),'healthy_new_triangles':healthy,'healthy_including_retained_native_main':total,'measured_comparator_triangles':cap,'source_collection':r['input_collection'],'review_directory':str(OUT/'detail'/review),'native_runtime':False}
    master=ROOT/'art/authoring/buildings_070/architecture-final-r4.blend'
    images={p.name:sha(p) for p in (OUT/'final-previews').glob('*.png')}
    assert len(images)>=21
    result={'schema':'ccp-070-final-art-sources/v1','status':'source_geometry_uv_budget_and_viewport_review_complete','user_blockout_approval':'Approve all four for detailed production','final_detailed_user_approval_claimed':False,'editable_master':str(master),'editable_master_sha256':sha(master),'assets':assets,'previews':images,'university_stock_material_preview':'Neutral placeholder in Blender; exact original layered native renderer retained in integration','material_coordinate_note':'Master shader preview and FBX export each explicitly flip top-origin authoring V once; source mesh UV untouched','native_lod_count':1,'lower_detail_sources':'authoring-only LOD1/LOD2 collections; no qualified native distance switching','new_body_owner_mask':'No dynamic mask in supported object-PBR cook; original native outskirts decorations retained','native_two_player_colour_review':False,'native_import_appearance_gameplay_multiplayer':False}
    target=OUT/'final-source-manifest-r2.json'
    if target.exists():raise FileExistsError('Preserve final source manifest; use a new immutable revision')
    target.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('previews','assets')},indent=2))
if __name__=='__main__':main()

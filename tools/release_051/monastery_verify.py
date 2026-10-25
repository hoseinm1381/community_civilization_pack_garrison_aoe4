"""Verify monastery payloads against exact delivered 050 SGA and protected inputs."""
from __future__ import annotations
import subprocess
from pathlib import Path
from common import ROOT, OUT, BASELINE, ARCH, guarded, read, sha, write

def main():
    guarded()
    receipt=read(OUT/'monastery/receipt.json')
    assert receipt['status']=='source_payload_ready_native_reference_pending'
    rows=receipt['payloads']
    assert len(rows)==6 and len({r['member'] for r in rows})==6
    media={r['member']:r for r in read(ROOT/'output/castle_next/integration/building-media.json')['payloads']}
    binding=read(OUT.parent/'release_050/integration/private-bindings.json')['bindings']
    expected={}
    for age in (3,4):
        for extension in ('rgm','rrgeom','rgo'):
            member=f'art/scenario/cccastle/monastery_age{age:02}/model.{extension}'
            expected[member]=media[member]['sha256']
        for extension in ('rgm','rrgeom','rgo','rrmaterial'):
            member=f'art/scenario/cccastle/monastery_detail_age{age:02}/model.{extension}'
            expected[member]=media[member]['sha256']
        for stamp in ('base_default','detail'):
            member=f'art/stamps/cc050/monastery{age:02}_{stamp}.bin'
            original=OUT.parent/'release_050/integration/payload'/member
            expected[member]=sha(original)
        member=f'attrib/attachments/attachment_lists/vietnam/release_050/vn_050_monastery{age:02}_visual.rgd'
        expected[member]=binding[f'monastery{age:02}']['private_sha256']
    assert len(expected)==20
    baseline_files=[]
    for member,digest in sorted(expected.items()):
        target=OUT/'monastery/baseline-members'/member
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            result=subprocess.run([str(ARCH),'extract-member',str(BASELINE),member,str(target)],
                                  capture_output=True,text=True,timeout=45)
            assert result.returncode==0,(member,result.stdout[-1000:],result.stderr[-1000:])
        assert sha(target)==digest,(member,digest,sha(target))
        baseline_files.append({'member':member,'sha256':digest,'bytes':target.stat().st_size})
    for row in rows:
        assert row['member'] in expected
        assert sha(row['file'])==row['sha256'] and Path(row['file']).stat().st_size==row['bytes']
        assert row['sha256']!=expected[row['member']]
    for age in receipt['ages']:
        assert age['selector_proof']['all_mscl_names_qualified']
        assert age['stamp_proof']['only_visual_transform_changed']
        assert age['geometry_proof']['removed_canopy_and_frame_triangles']==784
        assert age['geometry_proof']['retained_shrine_courtyard_lotus_triangles']==684
        assert age['geometry_proof']['native_index_buffer_compacted']
        assert age['geometry_proof']['new_degenerate_triangles']==0
        assert age['retained_native_roof']['sha256']==expected[f'art/scenario/cccastle/monastery_age{age["age"]:02}/model.rrgeom']
        assert age['retained_native_roof']['sha256']==media[f'art/scenario/cccastle/monastery_age{age["age"]:02}/model.rrgeom']['sha256']
        for part in age['source_blends'].values():
            if isinstance(part,dict) and 'file' in part:assert sha(part['file'])==part['sha256']
    preview=read(OUT/'monastery/previews/receipt.json')
    for age in preview['ages']:
        assert {x['view'] for x in age['images']}>=set('healthy-'+x for x in ('iso','front','back','left','right','top','bottom'))
        for row in age['images']:assert sha(row['file'])==row['sha256']
    native=read(OUT/'monastery/native-readback.json')
    assert native['status']=='passed_native_chunk_and_index_readback'
    for age in native['ages']:
        assert age['new_degenerate_triangles']==age['invalid_indices']==0
        assert age['detail_triangles_after']==684 and age['detail_removed_canopy_frame_triangles']==784
    editable=read(OUT/'monastery/editable-assets.json')
    assert editable['status']=='durable_editable_detail_obj_and_native_rebuild_recipe'
    for row in editable['ages']:assert sha(row['editable_detail_obj'])==row['sha256']
    contacts=read(OUT/'monastery/geometry-contacts.json')
    assert contacts['status']=='measured_on_native_roof_and_retained_detail'
    for row in contacts['ages']:
        assert row['retained_detail_contact_gaps']['bell_post_bottom_minus_pad_top_m']==0
        assert row['retained_detail_contact_gaps']['lotus_basin_bottom_minus_plinth_top_m']==0
    result={'status':'passed_source_and_exact_050_baseline_parity',
            'baseline_sga_sha256':sha(BASELINE),'baseline_members':baseline_files,
            'new_payload_members':rows,'no_source_assets_or_older_art_modified_by_this_script':True,
            'native_chunk_readback_sha256':sha(OUT/'monastery/native-readback.json'),
            'measured_geometry_contacts_sha256':sha(OUT/'monastery/geometry-contacts.json'),
            'editable_mesh_receipt_sha256':sha(OUT/'monastery/editable-assets.json'),
            'client_import':'pending','native_match':'pending'}
    write(OUT/'monastery/verification.json',result)
    print('MONASTERY051_VERIFIED',len(baseline_files),len(rows))

if __name__=='__main__':main()

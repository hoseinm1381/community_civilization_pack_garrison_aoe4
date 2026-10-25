"""Verify exact Castle source/export/cook evidence; never claims game acceptance."""
from __future__ import annotations
import json
import struct
from pathlib import Path
from common import ROOT, OUT, WORK, guarded, read, sha, write
from native_support import rc
from lifecycle_modes import truth

def frozen(path,digest):
    assert Path(path).is_file(),path
    assert sha(path)==digest,('Hash mismatch',path)

def main():
    guarded();checks=[]
    budget_path=OUT/'budget/castle-stock-landmark-budget.json'
    budget=read(budget_path)
    assert budget['status'] in ('qualified_static_drawgraph_budget','qualified_conservative_drawgraph_bounds',
                                'qualified_conservative_50percent_cap')
    assert budget['budget']['measured_choices']==14
    if budget['status']=='qualified_conservative_50percent_cap':
        b=budget['budget'];mean=b['target_triangles'];cap=b['maximum_guaranteed_cap']
        minimum=b['guaranteed_target_min'];maximum=b['guaranteed_target_max']
        assert cap<=1.5*b['mean_lower']+1e-6
        assert 0<minimum<=mean<=maximum<=cap
        proof={'mean_lower':b['mean_lower'],'mean_upper':b['mean_upper'],
               'art_target_interval':[minimum,maximum],'chosen_target':mean,
               'guaranteed_cap':cap,'user_maximum_over_stock_average':0.5}
    elif budget['status']=='qualified_conservative_drawgraph_bounds':
        b=budget['budget'];mean=b['target_triangles'];cap=b['maximum_guaranteed_cap']
        minimum=b['guaranteed_target_min'];maximum=b['guaranteed_target_max']
        assert minimum>=.9*b['mean_upper']-1e-6
        assert maximum<=min(1.1*b['mean_lower'],cap)+1e-6
        assert 0<minimum<=mean<=maximum
        proof={'mean_lower':b['mean_lower'],'mean_upper':b['mean_upper'],
               'guaranteed_target_interval':[minimum,maximum],'chosen_target':mean,'guaranteed_cap':cap}
    else:
        assert not budget['blockers']
        mean=budget['budget']['mean'];cap=budget['budget']['maximum_cap']
        assert mean>0 and cap>=mean
        counts=budget['budget']['counts'];assert len(counts)==14 and abs(sum(counts)/14-mean)<1e-6
        minimum=.9*mean;maximum=min(1.1*mean,cap);proof={'mean':mean,'cap':cap}
    checks.append({'gate':'14 stock Castle normal/default compound budget','status':'passed',**proof})
    for key in ('imperial_citadel','resistance_hq'):
        row=read(OUT/'landmarks'/key/'handoff.json')
        frozen(row['source_blend'],row['source_blend_sha256'])
        folder=Path(row['export_directory'])
        for name,digest in row['export_sha256'].items():frozen(folder/name,digest)
        manifest=read(folder/'building.json')
        assert [p['name'] for p in manifest['parts'][:4]]==[f'garrison_part_{i:04}' for i in range(4)]
        assert [p['first_stage'] for p in manifest['parts'][:4]]==[0,20,0,80]
        assert all(p['first_stage']==20 for p in manifest['parts'][4:])
        assert len({p['name'] for p in manifest['parts']})==len(manifest['parts'])
        assert minimum<=row['healthy_triangles']<=maximum
        assert row['ruin_triangles']>0
        assert (folder/'pattern.png').is_file()
        checks.append({'gate':key+' editable/source/export','status':'passed',
                       'healthy_triangles':row['healthy_triangles'],'ruin_triangles':row['ruin_triangles']})
    base=read(OUT/'buildings/model-validation.json')
    assert len(base['models'])==5
    expected={('monastery',3),('monastery',4),('siege_workshop',3),('siege_workshop',4),('keep',3)}
    assert {(r['family'],r['age']) for r in base['models']}==expected
    audits=[]
    for row in base['models']:
        frozen(row['editable_blend'],row['editable_blend_sha256'])
        frozen(row['native_geometry'],row['native_geometry_sha256'])
        donor=read(row['donor_manifest'])
        original=rc.parse(Path(donor['geometry']['source']['path']).read_bytes())
        changed=rc.parse(Path(row['native_geometry']).read_bytes())
        a=list(rc.walk(original.roots));b=list(rc.walk(changed.roots))
        assert len(a)==len(b)
        geob=0;vertices=0;changed_vertices=0
        for old,new in zip(a,b):
            assert (old.tag,old.decoded_name)==(new.tag,new.decoded_name)
            assert len(old.payload)==len(new.payload)
            if old.children:continue
            if old.tag!=b'GEOB' or geob%2:
                assert old.payload==new.payload,(row['name'],old.tag,old.decoded_name)
            else:
                n,_,stride,_=struct.unpack_from('<4I',old.payload)
                assert stride==24 and old.payload[:16]==new.payload[:16]
                for i in range(n):
                    k=16+i*stride
                    assert old.payload[k+6:k+8]==new.payload[k+6:k+8]
                    assert old.payload[k+11:k+12]==new.payload[k+11:k+12]
                    assert old.payload[k+15:k+24]==new.payload[k+15:k+24]
                    changed_vertices+=old.payload[k:k+15]!=new.payload[k:k+15]
                vertices+=n
            if old.tag==b'GEOB':geob+=1
        if row.get('native_model'):
            frozen(row['native_model'],row['native_model_sha256'])
            old=rc.parse(Path(donor['resources']['model']['cache_path']).read_bytes())
            new=rc.parse(Path(row['native_model']).read_bytes())
            before=list(rc.walk(old.roots));after=list(rc.walk(new.roots))
            assert len(before)==len(after)
            for x,y in zip(before,after):
                assert (x.tag,x.decoded_name)==(y.tag,y.decoded_name)
                if not x.children and x.tag!=b'MSD ':assert x.payload==y.payload,(row['name'],x.tag)
        audits.append({'model':row['name'],'vertices':vertices,'changed_vertices':changed_vertices,
                       'native_index_uv_owner_collection_data_preserved':True,
                       'private_model_edits_limited_to_selector_memberships':True})
    checks.append({'gate':'five native donor geometry and selector byte audits','status':'passed','models':audits})
    detail=read(OUT/'buildings/details/details-validation.json')
    assert len(detail['models'])==5
    for row in detail['models']:
        frozen(row['source_blend'],row['source_blend_sha256'])
        folder=Path(row['export_dir'])
        frozen(folder/'model.fbx',row['fbx_sha256']);frozen(folder/'building.json',row['manifest_sha256'])
        for name,digest in row['textures'].items():frozen(folder/(name+'.png'),digest)
    checks.append({'gate':'five staged ordinary building detail exports','status':'passed'})
    for kind,media_name in [('landmarks','landmark-media.json'),('details','building-media.json')]:
        media=read(WORK/media_name)
        assert media['status']=='passed' and media['active_bindings_applied'] is False
        assert len(media['models'])==(2 if kind=='landmarks' else 10)
        for row in media['payloads']:frozen(row['file'],row['sha256'])
        frozen(media['cook']['cook']['archive'],media['cook']['cook']['sha256'])
        reference=read(WORK/(kind+'-reference.json'))
        assert reference['status']=='passed' and len(reference['model_references'])==len(media['models'])
        frozen(reference['archive'],reference['sha256'])
        checks.append({'gate':kind+' fresh art cook and native reference readback','status':'passed',
                       'models':len(media['models']),'reference_archive_sha256':reference['sha256']})
    for row in read(WORK/'landmark-media.json')['models']:
        raw=Path(row['model_file']).read_bytes()
        handoff=read(OUT/'landmarks'/row['key']/'handoff.json')
        healthy=sorted(p['name'] for p in handoff['building']['parts'] if p['first_stage']==20)
        for state in ('healthy','damage_1','damage_2','damage_3','damage_4','damage_5','ruins'):
            expected=(['garrison_part_0002'] if state=='ruins' else
                      ['garrison_part_0000','garrison_part_0003'] if state in ('damage_3','damage_4','damage_5') else
                      sorted(['garrison_part_0000']+healthy))
            assert truth(raw,state)==expected,(row['key'],state)
    checks.append({'gate':'native intact/damage/ruin exclusivity','status':'passed'})
    colour=read(OUT/'owner-colour/verification.json')
    assert colour['status']=='passed_native_shader_mask_and_uv_binding_pending_match'
    assert colour['media_sha256']==sha(WORK/'landmark-media.json')
    checks.append({'gate':'native structure shader, typed owner parameters, mask resources and matching UV0/UV1','status':'passed','report_sha256':sha(OUT/'owner-colour/verification.json')})
    debris=read(OUT/'landmarks/retained-debris-budget.json')
    bounds=[]
    for row in debris['landmarks']:
        source=read(OUT/'landmarks'/row['key']/'handoff.json')
        assert source['healthy_triangles']==row['custom_source_counts']['healthy_triangles']
        assert source['ruin_triangles']==row['custom_source_counts']['ruin_triangles']
        full=row['complete_compound_bounds']
        assert full['healthy_triangles']['upper_if_all_retained_native_debris_drawn']<=cap
        bounds.append({'key':row['key'],'full_compound_bounds':full,'visibility':'native debris state visibility unresolved; conservative bound includes all props'})
    checks.append({'gate':'complete compound triangle cap including retained native debris','status':'passed','models':bounds,'cap':cap})
    result={'schema':'ccp.castle-preparation-checks/v1','status':'passed_offline_and_native_cook',
            'scope':'Isolated asset preparation; this checker never applies bindings. Actual 050 source application is tracked separately under output/release_050.',
            'checks':checks,'native_match':'not tested','client_import':'not performed',
            'active_bindings_applied':False,'release_package_created':False,
            'required_later_gates':[
                {'id':'two_player_colours','status':'native_binding_verified_match_pending','required_before':'release_acceptance'},
                {'id':'native_ruins_selection_and_repair','status':'pending_native_match','required_before':'release_acceptance'},
                {'id':'native_appearance_and_access','status':'pending_native_match','required_before':'release_acceptance'},
                {'id':'package_import_and_lobby','status':'not_performed','required_before':'release_acceptance'}],
            'new_landmark_owner_pattern':'native structure shader, mask resource and UV binding verified; rendered two-colour acceptance remains pending',
            'full_landmark_compound_bounds':bounds,
            'cook_pipeline_limitations':read(WORK/'landmark-media.json')['cook'].get('package_wrapper_status')}
    write(OUT/'verification.json',result)
    print('CASTLE_PREPARATION_CHECKS_PASS',len(checks),'gates; runtime and import pending')

if __name__=='__main__':main()

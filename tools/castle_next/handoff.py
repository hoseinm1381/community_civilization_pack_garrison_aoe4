"""Emit an unapplied integration contract after exact preparation verification."""
from __future__ import annotations
from pathlib import Path
from common import ROOT, OUT, WORK, CFG, RECIPES, guarded, read, sha, write

def main():
    guarded();verification=read(OUT/'verification.json')
    assert verification['status']=='passed_offline_and_native_cook'
    actor_contract=read(OUT.parent/'release_050/integration/reference-040-actors.json')
    lifecycle=read(OUT/'lifecycle/source-contract.json')
    landmark_media=read(WORK/'landmark-media.json')
    building_media=read(WORK/'building-media.json')
    buildings=read(RECIPES/'buildings-source.json')
    artifacts=[];operations=[]
    actor_names={'imperial_citadel':'vn_building_landmark_age2_imperrial_citadel_vit',
                 'resistance_hq':'vn_building_landmark_age2_headquarter_vit'}
    for row in landmark_media['models']:
        key=row['key'];source=read(OUT/'landmarks'/key/'handoff.json')
        contract=next(c for c in lifecycle['actors'] if c['key']==key)
        plans=[]
        for tier in contract['tiers']:
            for stamp in tier['stamps']:
                principals=[v for v in stamp['visuals'] if v['model'].replace('\\','/') in contract['qualified_owners']]
                if not principals:continue
                plans.append({'stock_attachment':tier['reference'],'stock_attachment_sha256':tier['sha256'],
                    'stock_stamp':stamp['member'],'stock_stamp_sha256':stamp['sha256'],
                    'principal_visuals':principals,
                    'intended_private_model':row['model'],
                    'suppress_old_render_only_visual_ids':[v['id'] for v in stamp['visuals'] if v not in principals],
                    'preserve':'all nonvisual stamp objects, functional markers, terrain/pathfinding/placement records, and exact branch lifecycle owner',
                    'branch_owner_check':'Retain exact branch stock RGO and marker bytes; alternate/campaign owners require separate qualified private model variants when different.'})
        operations.append({'kind':'landmark','actor':actor_names[key],'key':key,'applied':False,
            'operation':'Allocate private visual tier lists/stamps through supported identity generation; map only this Vietnamese actor in each branch. Do not install generated prototype actors.',
            'visual_plans':plans,'native_state_contract':str(OUT/'lifecycle/model-contract.json')})
        artifacts.append({'key':key,'kind':'scratch_landmark','source':source,
                          'private_model':row['model'],'prepared_lifecycle_owner':row['native_owner']})
    consumers={'monastery':['vn_building_unit_religious_control_chi'],
               'siege_workshop':['vn_building_unit_siege_control_chi'],
               'keep':['vn_building_defense_keep_chi','vn_building_defense_keep_2_chi']}
    for row in buildings['models']:
        family=next(f for f in consumers if row['key'].startswith(f))
        detail=next(m for m in building_media['models'] if m['kind']=='authored_detail' and
                    m['key']=='detail_'+row['key'][:-2]+'_age'+row['key'][-2:])
        operations.append({'kind':'ordinary_building','key':row['key'],'applied':False,
            'actors':consumers[family],'stock_model':row['stock_model_stem'],
            'private_model':row['private_model_stem'],'detail_model':detail['model'],
            'operation':'Clone exact default/campaign native age attachment and stamp chains to private identities; replace principal model and append nonblocking native detail visual. Rewire only Vietnamese consumers.',
            'preserve':'age requirements, alternate consumers, production and exit markers, selection/site ext, RGO, stock materials/owner masks, native destruction/construction ownership',
            'chinese_isolation':'Never override the shared Chinese stock model, actor, or tier lists.'})
        artifacts.append({'key':row['key'],'kind':'stock_remodel','source':row,'detail_model':detail['model']})
    gates=[
      {'id':'completed_040_baseline','status':'verified_and_frozen','required_before':'integration',
       'criterion':'Verify finished040 delivery/source/art and hashes; freeze that baseline before applying any operations.'},
      {'id':'two_player_colours','status':'native_binding_verified_match_pending','required_before':'release_acceptance',
       'criterion':'Confirm two player colours in a native match; native structure shader, mask resources, typed parameters and UV channels are verified.',
       'scope':['imperial_citadel','resistance_hq'],
       'evidence':str(OUT/'owner-colour/verification.json')},
      {'id':'native_ruins_selection_and_repair','status':'pending_native_match','required_before':'release_acceptance',
       'criterion':'Destroy both landmarks, wait beyond collapse cleanup, select remains, repair with villagers, interrupt/resume, restore, destroy again, check victory accounting.'},
      {'id':'native_appearance_and_access','status':'pending_native_match','required_before':'release_acceptance',
       'criterion':'Check every active tier, actor scales, viewing distances/LODs, two colours, attack and production origins, entrances, overhang adjacency, construction/cancel/repair/destruction and Chinese isolation.'},
      {'id':'package_import_and_lobby','status':'not_performed','required_before':'release_acceptance',
       'criterion':'After later authorized integration/package creation, verify import and explicit tuning/mode lobby selection.'},
    ]
    payloads=landmark_media['payloads']+building_media['payloads']
    assert len({p['member'] for p in payloads})==len(payloads)
    for row in payloads:assert sha(row['file'])==row['sha256']
    dependencies=[]
    for name in ['tools/release_010/integration.py','tools/release_010/integration_codec.py',
                 'tools/release_010/integration_native.py','tools/release_040/lifecycle.py',
                 'tools/release_020/model_ministry_farm_hideout_runner.py',
                 'output/release_010/integration/schema/reflect.db']:
        path=ROOT/name
        dependencies.append({'path':str(path),'sha256':sha(path),'retention':'required read-only rebuild dependency'})
    result={'schema':'community-civilization-pack/castle-next-unapplied-integration/v1',
        'status':'prepared_assets_with_explicit_pending_integration_gates',
        'target_pack_guid':CFG['project_guid'],'target_package_key':CFG['package_key'],
        'active_bindings_applied':False,'version_changed':False,'release_zip_created':False,
        'final_release_archive_created':False,'artifacts':artifacts,'operations':operations,
        'exact_resource_allowlist':payloads,'required_later_gates':gates,
        'scope':'Asset-preparation proposal recorded before applying release050 bindings; actual later application is tracked separately under output/release_050.',
        'owner_colour_verification':read(OUT/'owner-colour/verification.json'),
        'dependencies':dependencies,'accepted_actor_contract':actor_contract,
        'verification':{'path':str(OUT/'verification.json'),'sha256':sha(OUT/'verification.json')},
        'budget':read(OUT/'budget/castle-stock-landmark-budget.json')['budget'],
        'retention':'Preserve blends, textures, exports, recipes, registered sources, donor manifests/native resources, cook archives, readbacks and failure diagnostics. This asset stage creates no release ZIP and performs no release cleanup.'}
    write(RECIPES/'integration-manifest.json',result)
    write(OUT/'handoff.json',{'manifest':str(RECIPES/'integration-manifest.json'),
          'manifest_sha256':sha(RECIPES/'integration-manifest.json'),'status':result['status'],
          'asset_count':len(artifacts),'payload_count':len(payloads),
          'required_later_gates':gates,'active_bindings_applied':False})
    print('CASTLE_UNAPPLIED_HANDOFF',len(artifacts),'assets;',len(payloads),'resources')

if __name__=='__main__':main()

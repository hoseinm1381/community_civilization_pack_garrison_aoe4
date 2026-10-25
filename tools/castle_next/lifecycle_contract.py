"""Isolated persistent landmark entity/source and exact native RGO contract."""
from __future__ import annotations
import argparse
import shutil
import xml.etree.ElementTree as ET
from common import ROOT, OUT, WORK, guarded, read, sha, write
from native_support import native, rc, lifecycle
from lifecycle_modes import truth as model_truth

ACTORS={
    'imperial_citadel':'vn_building_landmark_age2_imperrial_citadel_vit',
    'resistance_hq':'vn_building_landmark_age2_headquarter_vit',
}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--models',action='store_true');args=parser.parse_args()
    guarded();rows=[]
    for key,name in ACTORS.items():
        # Model qualification keeps the original lifecycle owner contract even
        # after authorized 050 visual bindings are applied to active source.
        source_root=ROOT/'assets'
        if args.models:
            freeze_path=OUT.parent/'release_050/baseline/freeze-baseline.json'
            assert freeze_path.is_file(),'Completed040 freeze required for 050 model qualification'
            freeze=read(freeze_path)
            assert freeze['status']=='immutable_pre_050_baseline'
            source_root=OUT.parent/'release_050/source-baseline/assets'
            assert source_root.is_dir(),'Frozen040 source assets are unavailable'
        source=source_root/'attrib/instances/ebps/vietnam'/(name+'.xml')
        if args.models:
            relative=source.relative_to(source_root).as_posix()
            expected=next(r['sha256'] for r in freeze['active_source_assets']['files'] if r['path']==relative)
            assert sha(source)==expected,('Frozen040 actor changed',source)
        target=OUT/'lifecycle/isolated-actors'/(name+'.xml')
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():shutil.copy2(source,target)
        assert sha(source)==sha(target),'Concurrent actor changed: do not refresh preserved copy'
        document=ET.parse(target).getroot()
        flags={}
        for field in ('delete_when_dead','death_seconds','can_repair','destroy_stamps','selection_method','static_selection_bounds'):
            flags[field]=sorted(set(n.get('value','') for n in document.iter() if n.get('name')==field))
        assert flags['delete_when_dead']==['False']
        assert flags['death_seconds']==['-1']
        assert flags['can_repair']==['True']
        assert flags['selection_method']==['obb_adjusted_to_terrain']
        assert any(n.get('value')=='repair' and n.get('name')=='interaction_type' for n in document.iter())
        refs=sorted(set(n.get('value') for n in document.iter('instance_reference')
                        if n.get('name')=='attachments' and n.get('value')))
        tiers=[];owners={}
        for ref in refs:
            path=native.stock('attrib/'+ref.replace('\\','/')+'.rgd')
            fields=list(native.rgd.flatten(native.rgd.read(path.read_bytes()).nodes))
            stamps=[]
            for field,node in fields:
                if node.key=='stamp' and node.value:
                    member=node.value.replace('\\','/')+'.bin'
                    stamp=native.stock(member)
                    visuals=native.active_visuals(native.NativeTree(stamp))
                    stamps.append({'member':member,'sha256':sha(stamp),'visuals':visuals})
                    for visual in visuals:
                        model=visual['model'].replace('\\','/').lower()
                        if model.endswith('.rgm'):model=model[:-4]
                        try:owner=native.stock(model+'.rgo')
                        except Exception as error:
                            owners[model]={'error':str(error)};continue
                        behaviours={c.decoded_name:c for c in rc.walk(rc.load(owner).roots) if c.tag==b'BVBP'}
                        actions={}
                        for action,token in [('bhv_set_lifecycle_ruins',b'set_lifecycle_ruins'),
                                             ('bhv_collapse_ruins',b'act_collapse_to_ruins'),
                                             ('bhv_repair_to_healthy',b'act_repair_to_healthy')]:
                            c=behaviours.get(action)
                            payloads=[p.payload for p in c.children if p.tag==b'BBPD'] if c else []
                            actions[action]=any(token in p for p in payloads)
                        owners[model]={'file':str(owner),'sha256':sha(owner),'actions':actions,
                                       'supports_ruins_repair_graph':all(actions.values())}
            tiers.append({'reference':ref,'file':str(path),'sha256':sha(path),'stamps':stamps})
        compatible=[model for model,info in owners.items() if info.get('supports_ruins_repair_graph')]
        assert compatible,(key,'No exact stock native lifecycle owner qualified',owners)
        row={'key':key,'actor':name,'isolated_actor':str(target),'source_sha256':sha(source),
             'flags':flags,'tiers':tiers,'owners':owners,'qualified_owners':compatible,
             'runtime':'pending native match; selector/lifetime/selection cannot be proven by source alone'}
        if args.models:
            media=read(WORK/'landmark-media.json')
            model=next(m for m in media['models'] if m['key']==key)
            raw=Path(model['model_file']).read_bytes()
            _,pairs=lifecycle._pairs(raw)
            table=[(lifecycle._selector(s),lifecycle._conditions(c)) for s,c in pairs]
            truth={}
            handoff=read(OUT/'landmarks'/key/'handoff.json')
            healthy=sorted(p['name'] for p in handoff['building']['parts'] if p['first_stage']==20)
            for state in ['healthy',*(f'damage_{i}' for i in range(1,6)),'ruins']:
                enabled=model_truth(raw,state)
                expected=(['garrison_part_0002'] if state=='ruins' else
                          ['garrison_part_0000','garrison_part_0003'] if state in ('damage_3','damage_4','damage_5') else
                          sorted(['garrison_part_0000']+healthy))
                assert enabled==expected,(key,state,enabled)
                truth[state]=enabled
            row['model_selector_truth_table']=truth
            row['stock_rgo_retained']=sha(model['rgo_file'])==owners[model['native_owner']]['sha256']
            assert row['stock_rgo_retained']
        rows.append(row)
    result={'schema':'ccp.castle-landmark-lifecycle/v1','status':'passed_static_native_graph',
            'phase':'cooked_model_selectors' if args.models else 'source_native_owner',
            'actors':rows,'native_runtime':'not tested','no_scripted_replacement_entities':True}
    write(OUT/('lifecycle/model-contract.json' if args.models else 'lifecycle/source-contract.json'),result)
    print('CASTLE_LIFECYCLE_STATIC_PASS',len(rows),result['phase'])

if __name__=='__main__':
    from pathlib import Path
    main()

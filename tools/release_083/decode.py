"""Independent native decode of every freshly cooked art family."""
from common import *
import importlib.util
sys.path.append(str(ROOT/'tools/release_079'))
from rig_contract import read_contract,validate_contract
def main(label):
    guard();folder=OUT/'cooks'/label;receipt=read(folder/'receipt.json')
    final='--final' in sys.argv
    if final:
        delivery=OUT/'delivery/final-v2';archive=delivery/'community_civilization_pack.sga'
        assert sha(archive)==read(delivery/'verification.json')['sga_sha256']
        folder=delivery/'native-decode';folder.mkdir(exist_ok=False)
    else:
        archive=Path(receipt['archive']);assert sha(archive)==receipt['archive_sha256']
    spec=importlib.util.spec_from_file_location('index83',ROOT/'tools/release_079/decode_diagnostic.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.INDEX=folder/'private-index.sqlite3';listing=json.loads(run('decode-list',[CFG['archive_tool'],'list',archive,'--verify'],folder))
    if not m.INDEX.exists():m.create_index(archive,listing['members'],listing['archive']['name'])
    config=read(m.ORIGINAL_INDEX.with_name('game-assets.local.json'));config['index_path']=str(m.INDEX)
    empty=folder/'empty-game';(empty/'cardinal/archives').mkdir(parents=True,exist_ok=True);config['game_root']=str(empty);write(folder/'private-config.json',config)
    results={}
    for record in receipt['records']:
        family=record['family'];dest=folder/'decoded'/family
        run('decode-'+family,[CFG['garrison_core'],'convert','decode-static','--logical-path',record['member_root']+'/model.rgm','--config',folder/'private-config.json','--index',m.INDEX,'--output-root',dest],folder,180)
        manifest=next(dest.glob('*/decoded-static.json'));d=read(manifest);source=read(OUT/'art'/family/record['revision']/'export.json')
        assert not d['blockers'] and not d['missing_textures'],(family,d['blockers'],d['missing_textures'])
        counts=[g['triangle_count'] for g in d['geometry']['groups']];assert counts==source['lod_triangles'],(family,counts,source['lod_triangles'])
        assert {g['material'] for g in d['geometry']['groups']}=={'lod1','lod2','lod3'}
        result={'manifest':str(manifest),'sha256':sha(manifest),'triangles':counts,'blockers':d['blockers'],'missing_textures':d['missing_textures'],'source_owner_mask_surface_fraction':source['owner_mask_surface_fraction_by_lod']}
        if family.startswith('skirmisher'):
            model=(delivery/'readback' if final else folder/'readback')/record['member_root']/'model.rgm';validate_contract(read_contract(model.read_bytes()),source['donor_contract'])
            names=[b['name'] for b in d['skeleton']['bones']];assert names==[b['name'] for b in source['donor_contract']['bones']]
            deform=d['animated_asset_import_plan']['layers']['deform'];assert deform['status']=='ready' and deform['weights_status']=='qualified_exact_palette_binding',deform
            diag=deform['weight_diagnostics'];assert diag['zero_weight_vertex_count']==0 and diag['non_unit_weight_sum_vertex_count']==0
            materials=d['material']['materials'];assert len(materials)==3
            patterns=[]
            for mat in materials:
                assert mat['class']=='unit'
                pattern=next(t for block in mat['blocks'] for t in block['textures'] if t['name']=='patternTex');assert pattern['projection_path']
                patterns.append(pattern['projection_path'])
            result.update(bones=len(names),donor_partition_contract=True,weight_diagnostics=diag,pattern_projections=patterns)
        results[family]=result;print('083_DECODED',family,counts,flush=True)
    write(folder/'decoded-proof.json',results)
    write(folder/'verification.json',{'archive':str(archive),'archive_sha256':sha(archive),'all_nine_families_decoded':len(results)==9,'final_owning_archive':final})
if __name__=='__main__':main(sys.argv[1])

"""Check the final dependency delta against the frozen package closure."""
import xml.etree.ElementTree as ET
from common import *
from release import listing

def main():
    guarded();candidate=read(OUT/'candidate.json');audit=read(OUT/'archive-verification.json')
    assert sha(candidate['archive'])==candidate['sha256']==audit['sga_sha256']
    members={x['path'].replace('\\','/').casefold() for x in listing(candidate['archive'])['members']}
    assert {r['member'] for r in candidate['payloads']}==set(audit['changed']+audit['added'])
    for r in candidate['payloads']:assert sha(r['file'])==r['sha256']
    pointer=read(OUT/'native-source/current.json');assert sha(pointer['file'])==pointer['sha256']
    native=read(pointer['file']);assert native['status']=='passed'
    precache=(ROOT/'assets/scar/vietnam/prematch_precache.scar').read_text()
    mode=ET.parse(ROOT/'assets/scar/winconditions/VietnamMode.rdo').getroot()
    cached={n.get('Value') for n in mode.iter('DataProperty') if n.get('Name')=='m_fileName'}
    parents=[]
    for name,proof in native['inherited_trap_parity'].items():
        parent='attrib/ebps/vietnam/'+name+'.rgd';child=parent[:-4]+'_passable.rgd'
        assert parent in members and child in members and proof['all_other_compiled_fields_byte_identical']
        identity=GUID.replace('-','')+':'+name+'_passable'
        assert identity in cached and '"'+identity+'"' in precache
        source=ET.parse(ROOT/('assets/attrib/instances/ebps/vietnam/'+name+'_passable.xml')).getroot()
        refs=[n for n in source.iter('instance_reference')]
        assert len(refs)==2 and all(n.get('mod')==GUID.replace('-','') and n.get('value')=='ebps\\vietnam\\'+name for n in refs)
        parents.append({'parent':parent,'child':child,'precache':identity})
    landmarks=read(OUT/'landmarks/receipt.json')
    assert all(p['proof']['all_nonselector_leaf_payloads_byte_identical'] for p in landmarks['proofs'])
    monastery=read(OUT/'monastery/receipt.json')
    assert all(a['selector_proof']['all_other_050_chunks_byte_identical'] and a['stamp_proof']['only_visual_transform_changed'] and a['geometry_proof']['native_vertex_uv_and_collection_buffers_byte_identical'] for a in monastery['ages'])
    reference=read(OUT/'reference/receipt.json')
    assert reference['status']=='passed' and reference['candidate_sha256']==candidate['sha256']
    for row in reference['model_references']:
        assert all(row['model']+suffix in members for suffix in ('.rgm','.rgo','.rrgeom','.rrmaterial'))
    write(OUT/'dependency-closure.json',{'status':'passed_dependency_delta_against_frozen_050','candidate_sha256':candidate['sha256'],'new_children':parents,'all_new_parent_and_precache_targets_resolved':True,'seven_native_model_resource_quartets_present':True,'art_dependency_fields':'unchanged from frozen 050; selectors, detail indices and stamp transforms only','reference_receipt_sha256':sha(OUT/'reference/receipt.json'),'limit':'Preserves the frozen 050 dependency closure; official engine resources remain external. No import or native rendering claim.'})
    print('DEPENDENCY051_DELTA_VERIFIED',len(parents),len(reference['model_references']))

if __name__=='__main__':main()

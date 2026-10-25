"""Independent delivered readback, baseline/media, script and identity checks."""
from freeze import *
import argparse,collections
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd
def main(label):
    base=Path(CFG['external_root'])/'staging/r72/baseline-native'
    stage=Path(CFG['external_root'])/'staging/r72/ported-source'
    back=base.parent/('assemble-'+label)/'readback'
    original=json.loads((ROOT/'output/release_071/package-post1.json').read_text())
    assert sha(ROOT/'output/release_071/delivery/community_civilization_pack.sga')==original['sga_sha256']
    assert {p.relative_to(base).as_posix():sha(p)for p in files(base)}=={k:v['sha256']for k,v in original['all_members_sha256'].items()}
    media={p.relative_to(base).as_posix():sha(p)for top in ('art','attrib/attachments')for p in files(base/top)}
    assert all(sha(back/k)==v for k,v in media.items())
    scars=[]
    for p in (stage/'assets/scar').rglob('*.scar'):
        packaged=back/p.relative_to(stage/'assets')
        assert packaged.read_text(encoding='utf-8-sig')==p.read_text(encoding='utf-8-sig'),p
        scars.append(p.relative_to(stage).as_posix())
    pbgs=collections.defaultdict(set)
    for p in (back/'attrib').rglob('*.rgd'):
        tree=rgd.read(p.read_bytes())
        for path,node in rgd.flatten(tree.nodes):
            if node.key=='pbgid':pbgs[node.value].add(p.relative_to(back).as_posix())
    collisions={k:sorted(v)for k,v in pbgs.items()if len(v)>1};assert not collisions,collisions
    overlay=json.loads((OUT/('overlay-'+label+'.json')).read_text())
    for row in overlay['actor_visual_edits']:
        assert row['revert_recovers_exact_fresh_bytes']
        assert all(x.get('kind')=='equivalent-private-visual-identity'or x['path'].endswith(('/attachments','/animator_attachments'))for x in row['fields'])
    dump(OUT/'independent-native.json',{'passed':True,'original_071_payload_verified':True,'exact_media_preserved':len(media),'exact_script_readbacks':len(scars),'unique_pbgids':len(pbgs),'pbgid_collisions':collisions,'render_only_actor_edits':len(overlay['actor_visual_edits'])})
    print('Independent native checks passed:',len(media),'media;',len(scars),'scripts;',len(pbgs),'unique PBG IDs')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);main(p.parse_args().label)

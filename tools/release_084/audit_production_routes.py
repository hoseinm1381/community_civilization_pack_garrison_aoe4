"""Trace default construction, production, loadout and tier routes, read-only."""
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys
from pipeline import guard,digest,save_json
from providers import ROOT,OUT


def active_route(category,path,target):
    if not path.startswith('default/'):return False
    if category=='sbps':
        return (target=='ebps' and (
                '/squad_loadout_ext/' in path and path.endswith('/loadout_data/type') or
                '/squad_engineer_ext/' in path and path.endswith('/construction_item/ebp'))) or (
                target=='sbps' and '/squad_upgrade_ext/' in path)
    if category=='ebps':
        return (target=='sbps' and (
                '/spawner_ext/' in path and path.endswith(('/spawn_item/squad','/additional_squads/additional_squad')) or
                path.endswith('/construction_ext/on_construction_squad') or
                '/tier_ext/' in path and path.endswith('/statetree_tier_pgb_upgrade_target_squad'))) or (
                target=='ebps' and '/tier_ext/' in path and path.endswith('/statetree_tier_pgb_upgrade_target_entity'))
    return False


def main():
    guard();cfg=json.loads((ROOT/'workspace.json').read_text())
    sys.path.insert(0,cfg['garrison_extension']);from garrison_shared import rgd
    from speech_inventory import iterate
    folder=OUT/'inventory/production-routes-v3';folder.mkdir(parents=True,exist_ok=True)
    current=json.loads((OUT/'inventory/official-lookup.json').read_text())
    if digest(current['archive'])!=current['sha256']:raise RuntimeError('Official baseline changed')
    listing=json.loads((OUT/'inventory/speaker-closure-v2/official-list.json').read_text())
    official=defaultdict(list)
    for item in listing['members']:
        p=item['path'].split('/')
        if len(p)>2 and p[0]=='attrib':official[(p[1],Path(item['path']).stem)].append(item['path'])
    base=ROOT/'output/release_083/delivery/final-v2/readback';files={};lookup={}
    for cat in ['ebps','sbps']:
        for path in (base/'attrib'/cat).rglob('*.rgd'):
            member=path.relative_to(base).as_posix();files[member]=str(path);lookup[(cat,path.stem)]=member
    donors=json.loads((OUT/'inventory/speaker-closure-v2/audit.json').read_text())['rows']
    for row in donors:
        if digest(row['file'])!=row['sha256']:raise RuntimeError('Changed retained donor')
        files[row['member']]=row['file'];lookup[(row['member'].split('/')[1],Path(row['member']).stem)]=row['member']
    for row in json.loads((folder/'donors.json').read_text()) if (folder/'donors.json').exists() else []:
        if digest(row['file'])!=row['sha256']:raise RuntimeError('Changed production donor')
        files[row['member']]=row['file'];lookup[(row['member'].split('/')[1],Path(row['member']).stem)]=row['member']
    consumers=json.loads((OUT/'inventory/consumers.json').read_text())['rows']
    pending={r['member'] for r in consumers if r['generation_admitted']};seen=set();edges=[];unresolved=[];donor_rows=[]
    while pending:
        wanted=set();next_members=set()
        for member in sorted(pending-seen):
            seen.add(member);doc=rgd.read(Path(files[member]).read_bytes())
            for route,path,node in iterate(doc.nodes):
                if node.kind not in ['List','List2']:continue
                fields={n.key:n.value for n in node.value};target_category=fields.get('$PBGMAP','')
                if not active_route(member.split('/')[1],path,target_category):continue
                name=fields.get('$PBGNAME','')
                if not name:continue
                key=(target_category,name.split(':')[-1].replace('\\','/').split('/')[-1]);target=lookup.get(key)
                if target is None:
                    matches=official.get(key,[])
                    if len(matches)!=1:
                        unresolved.append(dict(member=member,path=path,reference=name,matches=matches));continue
                    target=matches[0];wanted.add(target)
                edges.append(dict(member=member,path=path,route=list(route),target=target,reference=name))
                next_members.add(target)
        if wanted:
            command=[cfg['archive_tool'],'extract',current['archive'],str(folder/'official')]
            for member in sorted(wanted):command+=['--member',member]
            result=json.loads(subprocess.check_output(command));save_json(folder/f'extraction-{len(seen)}.json',result)
            for member in sorted(wanted):
                p=folder/'official'/member;files[member]=str(p);lookup[(member.split('/')[1],p.stem)]=member
                donor_rows.append(dict(member=member,file=str(p),sha256=digest(p)))
            previous=json.loads((folder/'donors.json').read_text()) if (folder/'donors.json').exists() else []
            save_json(folder/'donors.json',list({r['member']:r for r in previous+donor_rows}.values()))
        pending=next_members-seen
        print('DEFAULT_PRODUCTION_ROUTES',len(seen),'resources;',len(wanted),'new donors',flush=True)
    known={r['member'] for r in consumers if r['generation_admitted']}
    extras=sorted(m for m in seen-known if m.startswith('attrib/sbps/'))
    save_json(folder/'audit.json',dict(schema='ccp-084-default-production-routes/v1',
              baseline_sga_sha256=json.loads((OUT/'baseline.json').read_text())['sga_sha256'],
              official_archive_sha256=current['sha256'],resources=sorted(seen),edges=edges,unresolved=unresolved,
              additional_squad_consumers=[dict(member=m,file=files[m],sha256=digest(files[m])) for m in extras],
              active_source_modified=False,scope='Default variant plus starting/incoming admitted squads; campaign-only routes recorded separately.',
              scar_creation_routes=['initialization: private six villagers and scout conversions; buffalo spawn',
                                    'garden: war-elephant spawn; animal channel preserved pending verified human crew']))
    print('PRODUCTION_RECONCILIATION',len(seen),'resources;',len(extras),'additional squad consumers;',len(unresolved),'unresolved',flush=True)


if __name__=='__main__':main()

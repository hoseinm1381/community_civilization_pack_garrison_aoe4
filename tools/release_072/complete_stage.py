"""Extend existing data-only lists for retained private visual identities."""
from port import *
def main():
    receipt=json.loads((OUT/'source-port.json').read_text())
    instances=STAGE/'assets/attrib/instances'
    precache=STAGE/'assets/scar/vietnam/prematch_precache.scar'
    s=translated((NORMAL/'assets/scar/vietnam/prematch_precache.scar').read_bytes(),'assets/scar/vietnam/prematch_precache.scar').decode().replace('\r\n','\n')
    for category,var in [('ebps','entities'),('sbps','squads')]:
        names=sorted(GUID+':'+p.stem for p in (instances/category).rglob('*.xml'))
        table='{\n'+''.join('    "'+v+'",\n'for v in names)+'}'
        s=re.sub(r'local '+var+r' = \{.*?\}',lambda m:'local '+var+' = '+table,s,flags=re.S)
    precache.write_text(s,encoding='utf-8',newline='\n')
    capability=STAGE/'assets/scar/vietnam/tunnel_ability_squads.scar'
    s=translated((NORMAL/'assets/scar/vietnam/tunnel_ability_squads.scar').read_bytes(),'assets/scar/vietnam/tunnel_ability_squads.scar').decode().replace('\r\n','\n');aliases=[]
    for donor,private in receipt['redirects'].items():
        if not private.startswith('sbps\\'):continue
        donorname=donor.rsplit('\\',1)[-1];name=private.rsplit('\\',1)[-1]
        pattern=r'\["'+re.escape(donorname)+r'"\]=\{([^\n]+)\}'
        if re.search(pattern,s):
            aliases.append(f'    ["{name}"]={{"{GUID}:{name}"}},')
    if aliases:s=s.rstrip().removesuffix('}')+'\n-- Equivalent private visual identities inherit their official donor capability.\n'+'\n'.join(aliases)+'\n}\n'
    capability.write_text(s,encoding='utf-8',newline='\n')
    receipt['data_only_script_adaptations']={'precache_all_private_blueprints':True,'tunnel_visual_aliases':aliases}
    receipt['staged_hashes']={p.relative_to(STAGE).as_posix():sha(p)for p in files(STAGE)}
    dump(OUT/'source-port.json',receipt)
    print(json.dumps({'blueprints':len(list((instances/'ebps').rglob('*.xml')))+len(list((instances/'sbps').rglob('*.xml'))),'tunnel_aliases':len(aliases)}))
if __name__=='__main__':main()

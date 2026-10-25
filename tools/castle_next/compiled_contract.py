"""Read accepted native actors and current consumers, without compiling active source."""
from __future__ import annotations
import subprocess
import xml.etree.ElementTree as ET
from common import ROOT, OUT, ARCH, guarded, sha, write
from native_support import rgd

ACTORS=(
 'vn_building_landmark_age2_imperrial_citadel_vit',
 'vn_building_landmark_age2_headquarter_vit',
 'vn_building_unit_religious_control_chi',
 'vn_building_unit_siege_control_chi',
 'vn_building_defense_keep_chi',
 'vn_building_defense_keep_2_chi',
)

def main():
    guarded()
    archive=ROOT/'archives/release_030_user_accepted/community_civilization_pack.sga'
    rows=[];consumers=[]
    for actor in ACTORS:
        member='attrib/ebps/vietnam/'+actor+'.rgd'
        target=OUT/'lifecycle/accepted-compiled'/member
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():subprocess.run([str(ARCH),'extract-member',str(archive),member,str(target)],capture_output=True,check=True)
        fields=dict(rgd.flatten(rgd.read(target.read_bytes()).nodes))
        selected={path:node.value for path,node in fields.items()
                  if (isinstance(node.value,(str,int,float,bool)) and
                      any(part in path for part in ('/health_ext/','/site_ext/','/ui_ext/selection_method',
                                                   '/tier_ext/','/type_ext/')))}
        if 'landmark' in actor:
            for variant in ('default','campaign'):
                assert fields[variant+'/health_ext/delete_when_dead'].value is False
                assert fields[variant+'/health_ext/can_repair'].value is True
                assert fields[variant+'/health_ext/death_seconds'].value==-1
                assert fields[variant+'/site_ext/footprint_scale/x'].value==8
                assert fields[variant+'/site_ext/footprint_scale/y'].value==8
        source=ROOT/'assets/attrib/instances/ebps/vietnam'/(actor+'.xml')
        rows.append({'actor':actor,'member':member,'native_file':str(target),'native_sha256':sha(target),
                     'current_source':str(source),'current_source_sha256':sha(source),
                     'native_fields':selected})
    targets={'ebps\\vietnam\\'+actor:actor for actor in ACTORS}
    for path in sorted((ROOT/'assets/attrib/instances').rglob('*.xml')):
        document=ET.parse(path).getroot()
        hits=[{'actor':targets[n.get('value','').lower()],'field':n.get('name'),'tag':n.tag}
              for n in document.iter() if n.get('value','').lower() in targets]
        if hits:consumers.append({'source':str(path),'sha256':sha(path),'references':hits})
    write(OUT/'lifecycle/compiled-actor-contract.json',{
        'schema':'ccp.castle-accepted-actor-contract/v1','status':'passed',
        'accepted_archive':str(archive),'accepted_archive_sha256':sha(archive),
        'actors':rows,'current_source_consumers':consumers,
        'scope':'Accepted 030 native actor bytes plus separately hashed current source. No040 artifact is treated as final baseline.',
        'native_runtime':'not tested','active_bindings_applied':False})
    print('CASTLE_COMPILED_ACTOR_PASS',len(rows),'actors;',len(consumers),'current source consumers')

if __name__=='__main__':main()

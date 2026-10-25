"""Record current official influence controls without modifying gameplay data."""
import re
import xml.etree.ElementTree as ET
from common import *
sys.path.insert(0, str(ROOT/'tools/release_072/vendor'))
from read_official_members import members, BASE as OFFICIAL

def main():
    guard()
    fields=set(); occurrences=0; styling=[]; ui_mentions=[]
    for name,raw in members('ReferenceAttributes.sga',lambda n:n.endswith('.xml')):
        if name=='districts.xml':
            root=ET.fromstring(raw)
            styling.append({'file':name,'sha256':hashlib.sha256(raw).hexdigest(),
                            'fields':[dict(n.attrib) for n in root.find("group[@name='ui']")]})
        if b'district_generator_ext' not in raw:continue
        root=ET.fromstring(raw)
        for node in root.iter('template_reference'):
            if node.get('value')=='ebpextensions\\district_generator_ext':
                occurrences+=1
                fields.update((n.tag,n.get('name')) for n in node)
    for name,raw in members('UI.sga',lambda n:n.endswith('.xaml')):
        for i,line in enumerate(raw.decode('utf-8',errors='replace').splitlines(),1):
            if re.search(r'district.*(radius|range|boundary)|(radius|range|boundary).*district',line,re.I):
                ui_mentions.append({'file':name,'line':i,'text':line.strip()[:600]})
    report={'status':'omitted_visual_only_contract_unqualified','gameplay_changed':False,
            'official_archives':{n:sha(OFFICIAL/n) for n in ('ReferenceAttributes.sga','UI.sga')},
            'generator_occurrences':occurrences,'generator_fields':sorted(fields),'world_styling':styling,
            'xaml_boundary_mentions':ui_mentions,
            'finding':'Current serialized district generators expose range_metres, not an independent per-building visual radius. Global district styling is not a Vietnam-only per-TC offset contract.',
            'decision':'Preserve all influence generation values and ship the other approved work. Report omitted +/-2m display change explicitly, per user authorization.',
            'limit':'This does not prove the engine has no possible extension route; no supported independent display offset was qualified in the inspected current data.'}
    write(OUT/'influence-audit.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()

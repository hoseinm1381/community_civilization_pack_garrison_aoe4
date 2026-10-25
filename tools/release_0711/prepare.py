"""Generate presentation inputs from actual gameplay requirements/private roster."""
import importlib.util, xml.etree.ElementTree as E, zipfile
from common import *

def inventory():
    sys.path.insert(0,str(ROOT/'tools/release_072/vendor'))
    import extension_audit as audit
    audit.ROOT=ROOT;audit.GUID=CFG['project_guid'].replace('-','')
    official=audit.refresh(OUT/'official-extensions.json')
    local=audit.load_local(ROOT);resolver=audit.Resolver(local,official)
    errors=resolver.audit();assert not errors,errors
    rows=[]
    for key,record in sorted(local.items()):
        assert key.startswith(('ebps\\vietnam\\','sbps\\vietnam\\')),key
        category=key.split('\\')[0]
        ext=('ebpextensions\\ui_ext' if category=='ebps' else 'sbpextensions\\squad_ui_ext')
        variants=[v for v in record if any(i['value']==ext for i in resolver.effective(key,v))]
        if variants:rows.append({'category':category,'key':key,'name':key.split('\\')[-1],'variants':variants})
    assert len({(r['category'],r['name']) for r in rows})==len(rows)
    write(OUT/'badge-inventory.json',{'rows':rows,'official_blueprints':len(official),'local_blueprints':len(local),'inheritance_errors':errors})
    return rows

def main():
    guard();rows=inventory()
    source=ROOT/'assets/attrib/instances/sbps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.xml'
    doc=E.parse(source);caps=[float(n.get('value')) for n in doc.findall('.//float[@name="max_squad_cap"]')]
    assert len(caps)==2 and len(set(caps))==1 and caps[0]>0 and caps[0].is_integer()
    cap=int(caps[0])
    # Native default/campaign requirement is the real training cap, not medic population.
    write(OUT/'cap-source.json',{'source':str(source),'sha256':sha(source),'path':'squad_requirement_ext/requirement_table/required_squad/max_squad_cap','default':cap,'campaign':cap})
    generated='-- Generated from native default/campaign required_squad/max_squad_cap; see cap-source.json.\nVietnamPresentationData = {buffaloCap = '+str(cap)+'}\n'
    (ROOT/'assets/scar/vietnam/presentation_data.scar').write_text(generated,encoding='utf-8')
    text=['-- Private Vietnamese UI badges only. Script-loading API; no population/gameplay changes.',
          'local flag = "images\\\\vietnam_0710\\\\dai_viet_dragon"']
    guid=CFG['project_guid'].replace('-','')
    for cat,exists,getter in [('ebps','EBP_Exists','BP_GetEntityBlueprint'),('sbps','SBP_Exists','BP_GetSquadBlueprint')]:
        text.append('for _, name in ipairs({')
        text.extend('    "'+guid+':'+r['name']+'",' for r in rows if r['category']==cat)
        text.extend(['}) do','    if '+exists+'(name) then',
            '        UI_OverrideUIProperty('+getter+'(name), "flag_icon", flag)','    end','end'])
    (ROOT/'assets/scar/vietnam/presentation_badges.scar').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print('GENERATED',cap,'cap',len(rows),'private badges')

if __name__=='__main__':main()

"""Stage normal-v12 gameplay with identity translation and sparse visual edits.

Never imports old gameplay records. The frozen XML supplies visual references;
compiled-only native resources are admitted separately by build.py.
"""
from freeze import *
import copy,re,xml.etree.ElementTree as E,collections,shutil,csv,io
STAGE=Path(CFG['external_root'])/'staging/r72/ported-source'
def translated(data,name):
    if Path(name).suffix.lower() not in ('.xml','.scar','.rdo','.csv','.locdb','.aoe4mod'):return data
    s=data.decode('utf-8-sig').replace(OLD,GUID).replace(CFG['source_project_guid'],CFG['project_guid'])
    s=s.replace('Vietnam_v2.locdb','community_civilization_pack.locdb')
    if name.endswith('.rdo'):
        parts=[(2806241233,3086805649),(1291310931,1083123067),(2648840072,1303308473),(1718873485,3775054987)]
        for index,(old,new) in enumerate(parts):
            s=re.sub(r'(Name="m_modPart'+str(index)+r'"[^>]*Value=")'+str(old)+r'(")',lambda m:m[1]+str(new)+m[2],s)
        if name=='assets/mod.rdo':s=s.replace('Name="Vietnam_v2"','Name="community_civilization_pack"')
    if name.endswith('VietnamMode.scar'):s=s.replace('20261023-runtime-v12','20261023-runtime-v12-garrison-072')
    if name=='assets/locdb/Vietnam_v2_en.csv':
        rows=list(csv.reader(io.StringIO(s,newline='')));column=rows[0].index('Text')
        for row in rows[1:]:
            if row[0]=='1001':row[column]='Community Civilization Pack'
        out=io.StringIO(newline='');csv.writer(out,lineterminator='\r\n'if'\r\n'in s else'\n').writerows(rows);s=out.getvalue()
        if data.startswith(b'\xef\xbb\xbf'):s='\ufeff'+s
    return s.encode('utf-8')
def renamed(name):
    return name.replace('assets/attrib/Vietnam_v2.xml','assets/attrib/community_civilization_pack.xml').replace('assets/locdb/Vietnam_v2','assets/locdb/community_civilization_pack')
def identity(x):
    return (x.tag,x.get('name'),x.get('value') if x.tag=='template_reference' else None,x.get('List.ItemID'))
def paths(root):
    out={}
    def rec(x,path):
        chain=path+[x];out[id(x)]=chain
        for c in x:rec(c,chain)
    rec(root,[]);return out
def find_chain(root,chain):
    cur=root
    for src in chain[1:]:
        matches=[c for c in cur if identity(c)==identity(src)]
        if not matches and src.tag=='template_reference':
            matches=[c for c in cur if c.tag==src.tag and c.get('name')==src.get('name') and c.get('value')==src.get('value')]
        if len(matches)!=1:return None
        cur=matches[0]
    return cur
def sparse_set(root,chain,leaf,edits,actor):
    cur=root
    for src in chain[1:-1]:
        matches=[c for c in cur if identity(c)==identity(src)]
        if not matches and src.tag=='template_reference':matches=[c for c in cur if c.tag==src.tag and c.get('value')==src.get('value') and c.get('name')==src.get('name')]
        if len(matches)>1:raise ValueError(('Ambiguous visual ancestor',actor,src.attrib))
        if matches:cur=matches[0]
        else:
            # Sparse inherited override; parent-chain IDs are qualified before activation.
            x=E.Element(src.tag,dict(src.attrib));cur.append(x);cur=x
    matches=[c for c in cur if identity(c)==identity(chain[-1])]
    if len(matches)>1:raise ValueError(('Ambiguous visual leaf',actor))
    before=dict(matches[0].attrib) if matches else None
    if matches:
        matches[0].attrib.clear();matches[0].attrib.update(leaf.attrib)
    else:cur.append(copy.deepcopy(leaf))
    if before!=leaf.attrib:edits.append({'actor':actor,'chain':[dict(x.attrib) for x in chain[1:]],'before':before,'after':dict(leaf.attrib)})
def main():
    freeze()
    assert not STAGE.exists(),'Preserve prior staged source'
    STAGE.mkdir(parents=True)
    with zipfile.ZipFile(OUT/'freeze/normal.zip')as normal,zipfile.ZipFile(OUT/'freeze/garrison.zip')as old:
        source={renamed(k):translated(normal.read(k),k)for k in normal.namelist() if k.startswith('assets/')}
        oldxml={k:E.fromstring(old.read(k))for k in old.namelist() if k.startswith('assets/attrib/instances/') and k.endswith('.xml')}
        index={(Path(k).parts[3],Path(k).stem):k for k in source if k.startswith('assets/attrib/instances/')}
        retained={k:t for k,t in oldxml.items() if '/attachments/' in k or '/release_060/' in k or '/release_040/vn_040_market_actor' in k}
        for k in retained:source[k]=old.read(k)
        # Recover only visual indirection to mechanically equivalent private stock identities.
        redirects={}
        for key,t in retained.items():
            if '/attachments/' in key:continue
            parent=t.find("instance_reference[@name='parent_pbg']")
            if parent is not None:
                ref=key.removeprefix('assets/attrib/instances/').removesuffix('.xml').replace('/','\\')
                redirects[parent.get('value')]=ref
        edits=[];unresolved=[];native_deferred=[]
        for key in list(source):
            if not key.startswith('assets/attrib/instances/') or key in retained:continue
            t=E.fromstring(source[key]);cat=Path(key).parts[3];name=Path(key).stem
            if cat not in ('ebps','sbps'):continue
            oldkey=next((k for k in oldxml if Path(k).parts[3]==cat and Path(k).stem==name),None)
            changed=False
            if oldkey:
                ot=oldxml[oldkey];chainmap=paths(ot)
                for x in ot.iter():
                    v=x.get('value','');field=x.get('name','')
                    private_visual=x.tag=='instance_reference' and field in ('attachments','animator_attachments') and v.startswith('attachments\\attachment_lists\\vietnam\\')
                    if private_visual:
                        chain=chainmap[id(x)]
                        if any(c.get('value')=='ebpextensions\\combat_ext'for c in chain) and find_chain(t,chain) is None:
                            native_deferred.append({'actor':name,'visual':v,'reason':'v12 inherits a different native weapon list; transfer by original visual donor after fresh compile'})
                            continue
                        sparse_set(t,chainmap[id(x)],x,edits,name);changed=True
                # Explicit visual scale only; placement and combat geometry come from v12.
                for x in ot.iter('float'):
                    if x.get('name') not in ('animator_scale','entity_scale'):continue
                    target=find_chain(t,chainmap[id(x)])
                    if target is not None and target.get('value')!=x.get('value'):
                        sparse_set(t,chainmap[id(x)],x,edits,name);changed=True
            for x in t.iter('instance_reference'):
                if x.get('name') not in ('ebp','squad','type'):continue
                v=x.get('value')
                if not x.get('mod') and v in redirects:
                    edits.append({'actor':name,'kind':'equivalent-private-visual-identity','before':dict(x.attrib),'after_value':redirects[v]})
                    x.set('value',redirects[v]);x.set('mod',GUID);changed=True
            if changed:
                E.indent(t,space='\t');source[key]=E.tostring(t,encoding='utf-8',xml_declaration=True)+b'\n'
        for k,v in source.items():
            p=STAGE/k;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v)
        # Use the existing independent destination project identity.
        (STAGE/CFG['project_file']).write_bytes(old.read(CFG['project_file']))
        dump(OUT/'source-port.json',{'normal_instances':len(index),'retained_art_definitions':list(retained),'visual_edits':edits,'unresolved':unresolved,'redirects':redirects,'stage':str(STAGE),'native_deferred':native_deferred})
        print(json.dumps({'instances':len(list((STAGE/'assets/attrib/instances').rglob('*.xml'))),'visual_edits':len(edits),'stage':str(STAGE)}))
if __name__=='__main__':main()

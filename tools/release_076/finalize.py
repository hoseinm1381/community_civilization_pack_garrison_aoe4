"""Verify selected immutable inputs and write an art-only overlay manifest/gallery."""
from common import *
import html
def main(label):
 guard();selection=read(RECIPES/'selection.json');cook=OUT/'cooks'/label;receipt=read(cook/'receipt.json');proof=read(cook/'decoded-proof.json')
 assert sha(receipt['archive'])==receipt['archive_sha256']
 assets=[];payloads=[]
 for family,rev in selection.items():
  record=next(r for r in receipt['records'] if r['family']==family);assert record['revision']==rev
  export=OUT/'art'/family/rev/'export.json';e=read(export)
  assert sha(export)==record['export_receipt_sha256'];assert sha(e['source'])==e['source_sha256']
  for name,digest in e['files'].items():assert sha(Path(e['export'])/name)==digest
  d=proof[family];assert not d['blockers'] and not d['missing_textures'];assert sha(d['manifest'])==d['sha256']
  files=[]
  for p in sorted((cook/'readback'/record['member_root']).rglob('*')):
   if p.is_file():files.append({'source':p.relative_to(OUT).as_posix(),'destination':p.relative_to(cook/'readback').as_posix(),'sha256':sha(p)})
  assert files
  payloads.append({'asset':family,'revision':rev,'files':files});assets.append({'asset':family,'revision':rev,'source_export':e,'decode':d})
 failures=[];counts={}
 groups=[('active_source_files',None,read(OUT/'source-freeze.json')),('historical_garrison_files',ROOT,read(ROOT/'output/release_075/baseline/protected.json')),('normal_files',ROOT.parent/'Community_civilization_pack_normal',read(ROOT/'output/release_075/baseline/normal.json'))]
 for key,base,rows in groups:
  counts[key]=len(rows)
  for name,digest in rows.items():
   p=base/name if base else Path(name)
   if not p.exists() or sha(p)!=digest:failures.append(str(p))
 write(OUT/'preservation.json',{'passed':not failures,**counts,'failures':failures});assert not failures,failures
 manifest={'schema':'ccp076-overlay/v1','version':'0.7.6-preparation','cook_label':label,'destination_guid':CFG['project_guid'],'assets':assets,'payloads':payloads,'expected_baseline_members':{},'bindings_status':'deferred_until_explicit_completed_075_baseline','bindings_recipe':str(RECIPES/'bindings.json'),'native_dependencies':read(OUT/'donors.json'),'validation':{'source_qa':read(OUT/'source-qa.json')['status'],'fresh_cook_readback':True,'native_acceptance':False,'supervision_animation':'source_only_disabled'},'integration_policy':'Art media additions only. Select completed baseline and exact SHA256 explicitly; resolve compiled consumers and private lifecycle bindings separately. No final assembly authorized.','inputs':{str(p):sha(p) for folder in (RECIPES,ROOT/'tools/release_076') for p in folder.glob('*') if p.is_file()}}
 write(OUT/'manifest.json',manifest)
 cards=[]
 for family,rev in selection.items():
  img=(OUT/'art'/family/rev/'threequarter.png').as_uri();src=(ART/family/rev/'model.blend').as_uri()
  cards.append(f'<article><h2>{html.escape(family)} · {rev}</h2><img src="{img}"><p><a href="{src}">Editable Blender source</a></p></article>')
 (OUT/'gallery.html').write_text('<!doctype html><meta charset="utf-8"><title>Garrison 0.7.6 asset preparation</title><style>body{font:17px system-ui;background:#161a20;color:#eee;padding:30px}main{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}article{background:#252b34;padding:16px}img{width:100%}a{color:#9edaff}</style><h1>Garrison 0.7.6 · cooked asset preparation</h1><p>10 new assets, three LODs each. Source previews below. Fresh native art cook/readback passed. Final bindings and native gameplay unverified. Buffalo supervision animation is editable source-only. No final release package.</p><main>'+''.join(cards)+'</main>',encoding='utf-8')
 print('MANIFEST_VERIFIED',len(assets),sum(len(p['files']) for p in payloads),counts)
if __name__=='__main__':main(sys.argv[1])

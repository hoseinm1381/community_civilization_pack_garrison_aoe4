"""Private native readback index; adapted from the retained release_060 decoder."""
import sqlite3
from common import *
ORIGINAL_INDEX=Path.home()/"AppData/Local/Garrison/Kit/game-assets.sqlite3"
def create_index(archive: Path, members: list[dict], provider_id: str) -> None:
    source = sqlite3.connect("file:" + ORIGINAL_INDEX.as_posix() + "?mode=ro", uri=True)
    target = sqlite3.connect(INDEX)
    try:
        for table in ("metadata", "archives", "assets", "resolved_assets", "folders", "object_types"):
            schema = source.execute("select sql from sqlite_master where type=? and name=?",
                                    ("table", table)).fetchone()[0]
            target.execute(schema)
        for key, value in source.execute("select key,value from metadata"):
            if key == "archive_count":
                value = "1"
            elif key in ("asset_count", "resolved_asset_count"):
                value = str(len(members))
            target.execute("insert into metadata(key,value) values(?,?)", (key, value))
        file = archive.stat()
        target.execute("insert into archives values(?,?,?,?,?,?,?,?,?,?,?)",
                       (1, "cardinal", archive.name, str(archive), file.st_size, file.st_mtime_ns,
                        provider_id, "11", "0", 1, len(members)))
        for index, item in enumerate(members, 1):
            path = item["path"]
            if not path.startswith("art/"):
                continue
            folder, name = path.rsplit("/", 1)
            extension = Path(name).suffix.lower()
            template = source.execute("select asset_kind,curated_category,civilization,object_class,object_type "
                                      "from resolved_assets where extension=? limit 1", (extension,)).fetchone()
            if template is None:
                template = ("resource", "Other", "Shared / Neutral", "Resource", "Resource")
            kind, category, civilization, object_class, object_type = template
            raw_name = item["toc"] + ":" + path.replace("/", "\\")
            target.execute("insert into assets(id,archive_id,logical_path,folder,name,extension,asset_kind,"
                           "curated_category,civilization,object_class,object_type,size,raw_name,verification,"
                           "storage,encryption,preview_status,preview_path) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (index, 1, path, folder, name, extension, kind, category, civilization,
                            object_class, object_type, item["size"], raw_name, item["verification"],
                            item["storage"], item["encryption"], "not_generated", None))
            target.execute("insert into resolved_assets(id,logical_path,folder,name,extension,asset_kind,"
                           "curated_category,civilization,object_class,object_type,size,raw_name,preview_status,"
                           "preview_path,product,archive,archive_path,provider_archive_id,archive_version,"
                           "product_version,verified,provider_count) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (index, path, folder, name, extension, kind, category, civilization,
                            object_class, object_type, item["size"], raw_name, "not_generated", None,
                            "cardinal", archive.name, str(archive), provider_id, "11", "0", 1, 1))
        target.commit()
    finally:
        source.close()
        target.close()

if __name__=='__main__':
 guard()
 folder=OUT/'cooks'/sys.argv[1];receipt=read(folder/'receipt.json');archive=Path(receipt['archive'])
 assert sha(archive)==receipt['archive_sha256']
 INDEX=folder/'private-index.sqlite3'
 listing=json.loads(run('decode-list',[CFG['archive_tool'],'list',archive,'--verify'],folder))
 if not INDEX.exists():create_index(archive,listing['members'],listing['archive']['name'])
 config=read(ORIGINAL_INDEX.with_name('game-assets.local.json'));config['index_path']=str(INDEX)
 empty=folder/'empty-game';(empty/'cardinal/archives').mkdir(parents=True,exist_ok=True);config['game_root']=str(empty)
 write(folder/'private-config-local.json',config)
 result={}
 for row in receipt['records']:
  family=row['family'];dest=folder/'decoded-local'/family
  if not list(dest.glob('*/decoded-static.json')):run('decode-local-'+family,[CFG['garrison_core'],'convert','decode-static','--logical-path',row['member_root']+'/model.rgm','--config',folder/'private-config-local.json','--index',INDEX,'--output-root',dest],folder,timeout=120)
  manifests=list(dest.glob('*/decoded-static.json'));assert len(manifests)==1
  d=read(manifests[0]);groups=d['geometry']['groups'];expected=read(OUT/'art'/family/row['revision']/'export.json')['lod_triangles']
  actual=[g['triangle_count'] for g in groups]
  assert sorted(actual)==sorted(expected),(family,actual,expected)
  result[family]={'manifest':str(manifests[0]),'sha256':sha(manifests[0]),'triangles':actual,'bones':len(d.get('skeleton',{}).get('bones',[])),'blockers':d.get('blockers',[]),'missing_textures':d.get('missing_textures',[])}
  assert not result[family]['blockers'] and not result[family]['missing_textures'],result[family]
  assert {g['material']:g['triangle_count'] for g in groups}=={'lod'+str(i+1):n for i,n in enumerate(expected)},(family,'LOD material mapping')
  if family=='buffalo' or family.startswith('skirmisher'):
   donor=read(read(OUT/'donors.json')['buffalo' if family=='buffalo' else 'skirmisher2']['manifest'])
   a,b=d['skeleton']['bones'],donor['skeleton']['bones']
   assert [(x['name'],x['parent_name']) for x in a]==[(x['name'],x['parent_name']) for x in b]
   delta=max(abs(u-v) for x,y in zip(a,b) for k in ('translation_xyz','quaternion_xyzw','scale_xyz') for u,v in zip(x['local_reference_transform'][k],y['local_reference_transform'][k]))
   assert delta<1e-4,(family,delta)
   deform=d['animated_asset_import_plan']['layers']['deform'];assert deform['status']=='ready' and deform['weights_status']=='qualified_exact_palette_binding'
   diagnostic=deform['weight_diagnostics'];assert diagnostic['zero_weight_vertex_count']==0 and diagnostic['non_unit_weight_sum_vertex_count']==0
   result[family]['rig_check']={'hierarchy_matches_official':True,'maximum_bind_component_delta':delta,'tolerance':1e-4,'compiled_weights':diagnostic,'native_motion':False}
 write(folder/'decoded-proof.json',result);print('DECODED_GEOMETRY_VERIFIED',len(result))

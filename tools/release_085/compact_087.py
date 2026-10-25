"""Losslessly compact only owned 087 native staging after verified delivery."""
import gzip,hashlib,json,os,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/release_085'
CFG=json.loads((ROOT/'workspace.json').read_text());EXT=Path(CFG['external_root']).resolve()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 proof=json.loads((OUT/'final-v2/verification.json').read_text());assert proof['version']=='0.8.7'
 assert sha(OUT/'final-v2/community_civilization_pack.sga')==proof['sga_sha256']
 assert sha(OUT/'final-v2/community_civilization_pack-0.8.7.zip')==proof['zip_sha256']
 targets=[(EXT/'staging'/name).resolve() for name in ('r87','r87-retry','r87-final')]
 assert all(t.is_relative_to(EXT/'staging') and t.parent==EXT/'staging' and t.name in ('r87','r87-retry','r87-final') for t in targets)
 files=[]
 for t in targets:
  assert not t.is_symlink() and not t.is_junction()
  for current,dirs,names in os.walk(t,followlinks=False):
   cur=Path(current)
   assert not cur.is_symlink() and not cur.is_junction()
   for name in names:
    p=cur/name;assert not p.is_symlink() and not p.is_junction();files.append(p)
 rows={p.relative_to(EXT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}
 bundle=OUT/'087-native-development.zip'
 with zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in files:z.write(p,p.relative_to(EXT).as_posix())
 with zipfile.ZipFile(bundle) as z:
  assert z.testzip() is None and set(z.namelist())==set(rows)
  for rel,row in rows.items():
   with z.open(rel) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
 receipt={'bundle':str(bundle),'bundle_sha256':sha(bundle),'files':rows,'restore':'Extract exact recorded staging/* prefix beneath the owned external root only; source/native diagnostics preserved losslessly.','retired':False}
 record=OUT/'087-native-compaction.json.gz';record.write_bytes(gzip.compress(json.dumps(receipt,indent=2).encode(),mtime=0))
 # Keep the native reference SGA directly usable by developer tools; all other native staging is lossless cold storage.
 native=json.loads((OUT/'087-native-reference.json').read_text());src=Path(native['archive']);saved=OUT/'087-native-reference.sga';assert not saved.exists();saved.write_bytes(src.read_bytes());assert sha(saved)==sha(src)
 native['archive']=str(saved);native['archive_sha256']=sha(saved);native['staging_bundle']=str(bundle)
 (OUT/'087-native-reference.json').write_text(json.dumps(native,indent=2)+'\n',encoding='utf-8')
 for p in files:
  row=rows[p.relative_to(EXT).as_posix()];assert sha(p)==row['sha256'];p.unlink()
 for target in targets:
  for current,dirs,names in os.walk(target,topdown=False,followlinks=False):
   p=Path(current);assert p.resolve().is_relative_to(target);p.rmdir()
 receipt['retired']=True;receipt['logical_bytes_removed']=sum(r['bytes'] for r in rows.values());receipt['new_bundle_bytes']=bundle.stat().st_size;receipt['direct_reference_bytes']=saved.stat().st_size
 record.write_bytes(gzip.compress(json.dumps(receipt,indent=2).encode(),mtime=0))
 assert sha(OUT/'final-v2/community_civilization_pack-0.8.7.zip')==proof['zip_sha256']
 print('087_NATIVE_STAGING_LOSSLESSLY_COMPACTED',receipt['logical_bytes_removed'],bundle.stat().st_size,saved.stat().st_size)
if __name__=='__main__':main()

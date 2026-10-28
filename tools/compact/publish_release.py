"""Publish the verified ZIP after its reviewed source commit is on main.

Uses configured Git credentials in memory; never logs or stores credentials.
Creates a draft, streams the exact artifact, verifies server metadata, publishes.
"""
import argparse,hashlib,http.client,json,subprocess,urllib.request,urllib.error,urllib.parse
from pathlib import Path
REPO='hoseinm1381/community_civilization_pack_garrison_aoe4'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--commit',required=True);p.add_argument('--zip',type=Path,required=True);p.add_argument('--notes',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
 root=Path(__file__).resolve().parents[2];dev=json.loads((root/'development.json').read_text());version=dev['version'];tag='v'+version
 def git(*args):return subprocess.check_output(['git','-c','safe.directory='+str(root),'-C',str(root),*args],text=True).strip()
 if git('rev-parse','HEAD')!=a.commit or git('ls-remote','origin','refs/heads/main').split()[0]!=a.commit:raise ValueError('Exact reviewed commit must already be on remote main')
 with a.zip.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 if h!=dev['zip_sha256']:raise ValueError('Release ZIP differs from accepted package')
 c=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,check=True)
 credentials=dict(line.split('=',1) for line in c.stdout.splitlines() if '=' in line);token=credentials['password']
 headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'ccp-release-tool','X-GitHub-Api-Version':'2022-11-28'}
 def api(path,method='GET',data=None):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+path,method=method,headers=headers,data=None if data is None else json.dumps(data).encode())
  with urllib.request.urlopen(req,timeout=90) as response:return json.load(response)
 try:release=api('/releases/tags/'+tag)
 except urllib.error.HTTPError as e:
  if e.code!=404:raise
  release=api('/releases','POST',{'tag_name':tag,'target_commitish':a.commit,'name':'Community Civilization Pack '+version,'body':a.notes.read_text(),'draft':True,'prerelease':False})
 if release['target_commitish'] not in (a.commit,'main'):raise ValueError('Existing release targets another source revision')
 assets=api('/releases/'+str(release['id'])+'/assets');asset=next((x for x in assets if x['name']==a.zip.name),None)
 if asset is None:
  if not release['draft']:raise ValueError('Refuse adding an unverified file to an existing public release')
  con=http.client.HTTPSConnection('uploads.github.com',timeout=1200)
  path='/repos/'+REPO+'/releases/'+str(release['id'])+'/assets?name='+urllib.parse.quote(a.zip.name)
  con.putrequest('POST',path)
  for key,value in {**headers,'Content-Type':'application/zip','Content-Length':str(a.zip.stat().st_size)}.items():con.putheader(key,value)
  con.endheaders();sent=0;next_progress=64*1024*1024
  with a.zip.open('rb') as stream:
   while chunk:=stream.read(4*1024*1024):
    con.send(chunk);sent+=len(chunk)
    if sent>=next_progress:print('RELEASE_UPLOAD_BYTES',sent,a.zip.stat().st_size,flush=True);next_progress+=64*1024*1024
  response=con.getresponse();raw=response.read();con.close()
  if response.status!=201:raise RuntimeError('Asset upload failed HTTP '+str(response.status)+': '+raw[:300].decode(errors='replace'))
  asset=json.loads(raw)
 if asset['state']!='uploaded' or asset['size']!=a.zip.stat().st_size:raise ValueError('GitHub asset size/state differs')
 digest=asset.get('digest')
 if digest and digest!='sha256:'+h:raise ValueError('GitHub asset digest differs')
 if release['draft']:release=api('/releases/'+str(release['id']),'PATCH',{'draft':False,'make_latest':'true'})
 release=api('/releases/tags/'+tag);asset=next(x for x in release['assets'] if x['name']==a.zip.name)
 if release['draft'] or asset['size']!=a.zip.stat().st_size or asset.get('digest') not in (None,'sha256:'+h):raise ValueError('Published release verification differs')
 receipt={'status':'published','commit':a.commit,'tag':tag,'release_url':release['html_url'],'download_url':asset['browser_download_url'],'asset_id':asset['id'],'bytes':asset['size'],'local_sha256':h,'github_digest':asset.get('digest'),'main_confirmed':True}
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()

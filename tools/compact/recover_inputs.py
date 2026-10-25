"""Restore indexed art inputs from direct packs or nested lossless recovery stores."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import zipfile
from portable import reader, rebase_text
from store import load, write_json, file_sha, safe_path, sha

LINKS = {'art/stock_cache':'stock-cache','art/garrison_library':'garrison-library',
         'output':'output','staging':'staging','cache':'cache','.tools':'tool-cache','archives':'archives'}


def canonical(value, provenance):
    s = value.replace('\\','/').removeprefix('//?/')
    for start,label in [(provenance['source_root'],'source'),(provenance['external_root'],'external')]:
        start = start.replace('\\','/').rstrip('/')
        if s.lower().startswith(start.lower()+'/'):
            tail = s[len(start)+1:]
            if label == 'source':
                for link,target in LINKS.items():
                    if tail.lower().startswith(link.lower()+'/'):
                        return 'external/'+target+'/'+tail[len(link)+1:]
            return label+'/'+tail
    return None


class Recovery:
    def __init__(self,r,workspace):
        self.r = r
        self.cfg = load(workspace)
        self.source = Path(self.cfg['source'])
        self.external = Path(self.cfg['external'])
        self.direct = {k.lower():k for k in r.doc['files']}
        self.indirect = {}
        self.zips = {}
        self.verified_containers = {}
        self.rows = []
        for store in ('resources_071','resources_080'):
            doc = json.loads(r.read('external/'+store+'/index.json'))
            for k,row in doc['files'].items():
                key = ('source/' if k.startswith('E/') else 'external/')+k[2:]
                self.indirect[key.lower()] = (store,row,doc)

    def material(self,key):
        if key.lower() in self.direct:
            actual = self.direct[key.lower()]
            return self.r.read(actual), self.r.doc['files'][actual]['sha256'], 'direct'
        store,row,index = self.indirect[key.lower()]
        if store == 'resources_080':
            blob = index['bundle']
            member = row['member']
        else:
            blob = row['blob']
            member = row.get('member')
        path = self.external/store/blob
        expected = index.get('bundle_sha256') if store == 'resources_080' else self.r.doc['files']['external/'+store+'/'+blob]['sha256']
        if not path.is_file():
            raise ValueError('Restore the verified recovery container first: '+str(path))
        stamp = (path.stat().st_size,path.stat().st_mtime_ns)
        if path not in self.verified_containers:
            if file_sha(path) != expected:
                raise ValueError('Changed recovery container: '+str(path))
            self.verified_containers[path] = stamp
        elif self.verified_containers[path] != stamp:
            raise ValueError('Recovery container changed during use: '+str(path))
        if member is None:
            data = gzip.decompress(path.read_bytes()) if row['codec'] == 'gzip' else path.read_bytes()
        else:
            if path not in self.zips:
                self.zips[path] = zipfile.ZipFile(path)
            data = self.zips[path].read(member)
        if len(data) != row['bytes'] or sha(data) != row['sha256']:
            raise ValueError('Corrupt nested recovery payload: '+key)
        return data,row['sha256'],store

    def recover(self,key):
        data,digest,store = self.material(key)
        parent = self.source.parent if key.startswith('source/') else self.external.parent
        target = safe_path(parent,key)
        allowed = (self.source.resolve(),self.external.resolve())
        if not any(target.resolve().is_relative_to(root) for root in allowed):
            raise ValueError('Recovery escaped configured work roots')
        if target.exists():
            actual = file_sha(target)
            if actual != digest:
                receipt = self.source/'relocation-proof.json'
                recorded = []
                if receipt.is_file():
                    proof = load(receipt)
                    recorded.extend(proof.get('changed_working_recipes',[]))
                    for run in proof.get('runs',[]):
                        recorded.extend(run.get('changed_working_recipes',[]))
                accepted_relocation = any(row.get('before') == digest and row.get('after') == actual and
                    Path(row['path']).resolve() == target.resolve() for row in recorded)
                if not accepted_relocation:
                    raise ValueError('Edited recovery destination preserved: '+str(target))
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:
                f.write(data)
        self.rows.append(dict(key=key,sha256=digest,bytes=len(data),storage=store))
        return target

    def close(self):
        for z in self.zips.values():
            z.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--blend-report',type=Path,help='Restore every unresolved original image path from audit_blends.py')
    p.add_argument('--key',action='append',default=[])
    p.add_argument('--art',action='store_true',help='Restore the verified current Blender/recipe input closure')
    p.add_argument('--proof',type=Path,required=True)
    args = p.parse_args()
    r = reader()
    recovery = Recovery(r,args.workspace)
    try:
        keys = set(args.key)
        if args.art:
            manifest = Path(__file__).resolve().parents[2]/'docs/compact/art-inputs.json'
            keys.update(load(manifest)['keys'])
        if args.blend_report:
            for row in load(args.blend_report)['missing']:
                key = canonical(row['original'],r.doc['provenance'])
                if not key:
                    raise ValueError('Art input is outside recorded roots: '+row['original'])
                keys.add(key)
        unresolved = sorted(k for k in keys if k.lower() not in recovery.direct and k.lower() not in recovery.indirect)
        if unresolved:
            write_json(args.proof,dict(passed=False,unresolved=unresolved))
            raise ValueError('Inputs not present in direct/nested stores; inspect proof')
        for i,key in enumerate(sorted(keys),1):
            recovery.recover(key)
            if i%100 == 0:
                print('ART_INPUTS_RECOVERED',i,flush=True)
        write_json(args.proof,dict(passed=True,files=recovery.rows,unresolved=[]))
        print('ART_INPUT_RECOVERY_VERIFIED',len(keys),flush=True)
    finally:
        recovery.close()
        r.close()


if __name__ == '__main__':
    main()

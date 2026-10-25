"""Pure final inventory policy shared by packaging and focused regressions."""
import hashlib
from pathlib import Path, PurePosixPath

def verify_static_source(receipt,current_policy_hash):
    if receipt.get('source_policy_sha256')!=current_policy_hash:
        raise ValueError('Static validation does not cover the current source policy')

def merge_payloads(groups):
    result={}
    for group in groups:
        for row in group:
            name=row['member'];path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name or str(path)!=name:
                raise ValueError('Unsafe archive path: '+name)
            if name in result:raise ValueError('Duplicate payload ownership: '+name)
            expected='attrib' if name.startswith('attrib/') else 'data'
            if row['toc']!=expected:raise ValueError('Wrong archive mount: '+name)
            with Path(row['file']).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            if actual!=row['sha256']:raise ValueError('Stale payload file: '+name)
            result[name]=dict(row)
    return result

def verify_inventory(before,old_mounts,actual,mounts,payload):
    expected=dict(before);expected.update({k:v['sha256'] for k,v in payload.items()})
    expected_mounts=dict(old_mounts)
    for k,row in payload.items():
        if k in old_mounts and old_mounts[k]!=row['toc']:raise ValueError('Changed existing mount: '+k)
        expected_mounts[k]=row['toc']
    if actual!=expected:raise ValueError('Archive member bytes do not match exact allowlist')
    if mounts!=expected_mounts:raise ValueError('Archive mounts do not match exact allowlist')

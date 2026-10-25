"""Production media allowlist. Animation trials cannot enter this release."""
BUFFALO='art/scenario/garrison/cc076/buffalo/'
def validate_readback(archive_members,readback_members):
    if archive_members!=readback_members:raise ValueError('Readback differs from freshly extracted verified archive')
def validate_cook_input(records,revision,receipt_hash,decoded_triangles,source_triangles):
    if len(records)!=1 or records[0].get('family')!='buffalo' or records[0].get('revision')!=revision or records[0].get('export_receipt_sha256')!=receipt_hash:
        raise ValueError('Cook does not belong to selected immutable source revision')
    if decoded_triangles!=source_triangles:raise ValueError('Decoded LOD geometry differs from source export')
def validate_changes(changed, ministry):
    for name in changed:
        buffalo=name.startswith(BUFFALO) and name.rsplit('.',1)[-1] in ('rgm','rrgeom','rrmaterial','rrtex')
        building=name in ministry and name.startswith('art/') and name.rsplit('.',1)[-1] in ('rgm','rrgeom','rrmaterial','rrtex')
        if not (buffalo or building): raise ValueError('Outside 0.8.1 visual allowlist: '+name)

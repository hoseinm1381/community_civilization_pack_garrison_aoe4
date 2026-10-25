"""Attach generated model, transform and preview evidence to the 051 handoff."""
from common import OUT,guarded,read,sha,write

def main():
    guarded()
    target=OUT/'monastery/receipt.json'
    row=read(target)
    assert row['status']=='source_payload_ready_native_reference_pending' and len(row['payloads'])==6
    native=read(OUT/'monastery/native-readback.json')
    preview=read(OUT/'monastery/previews/receipt.json')
    editable=read(OUT/'monastery/editable-assets.json')
    contacts=read(OUT/'monastery/geometry-contacts.json')
    control=read(OUT/'monastery/decode-control.json')
    assert native['status']=='passed_native_chunk_and_index_readback'
    assert len(preview['ages'])==len(editable['ages'])==2
    row['native_chunk_readback']={'file':str(OUT/'monastery/native-readback.json'),
                                  'sha256':sha(OUT/'monastery/native-readback.json'),
                                  'status':native['status']}
    row['previews']={'file':str(OUT/'monastery/previews/receipt.json'),
                     'sha256':sha(OUT/'monastery/previews/receipt.json'),
                     'views_per_age':[len(a['images']) for a in preview['ages']],
                     'includes':'six orthographic sides, iso, three lifecycle views, stock ground foliage and props',
                     'visibility_limit':'healthy roof is a complete native geometry envelope; exact selectors and materials await native match'}
    row['editable_assets']={'file':str(OUT/'monastery/editable-assets.json'),
                            'sha256':sha(OUT/'monastery/editable-assets.json'),
                            'source_format':'native-local detail OBJ with UVMap and authored component ranges plus retained-index recipe; native body RRGeom exact 050; 050 .blend copies are references only'}
    row['measured_geometry_contacts']={'file':str(OUT/'monastery/geometry-contacts.json'),
                                       'sha256':sha(OUT/'monastery/geometry-contacts.json'),
                                       'status':contacts['status']}
    row['garrison_decode_static_control']={'file':str(OUT/'monastery/decode-control.json'),
                                           'sha256':sha(OUT/'monastery/decode-control.json'),
                                           'finding':'rejected compacted-body candidate and exact frozen-050 private body both report non-finite UV; this decoder path cannot qualify final native load'}
    row['native_reference_cook']='pending integrated candidate build by controller'
    write(target,row)
    print('MONASTERY051_HANDOFF',len(row['payloads']),row['previews']['views_per_age'])

if __name__=='__main__':main()

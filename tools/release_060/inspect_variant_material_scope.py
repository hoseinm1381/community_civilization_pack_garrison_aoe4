"""Read-only contract probe of the installed variant API on multi-atlas units.

The rewritten material exists only in memory. No native files are changed.
"""
import json
import struct
import sys
from pathlib import Path
from common import CFG, OUT, guard, read, sha, write


def main():
    guard();sys.path.insert(0,CFG['garrison_extension'])
    from garrison_shared import model_variants as variants
    from garrison_shared import relic_chunky as rc
    contract=read(OUT/'qualification/nonhumanoid-route-preflight/20261018-stock-rig-contract.json')
    manifests={k:Path(v['donor_manifest']) for k,v in contract['donors'].items()}
    manifests['worker_elephant']=Path(read(OUT/'qualification/nonhumanoid-route-preflight/worker-elephant-stock/report.json')['decoded_manifest'])
    rows={}
    def albedos(document):
        values=[]
        def visit(chunk):
            if chunk.children:
                for child in chunk.children:visit(child)
            elif chunk.tag==b'PbTe':
                count=struct.unpack_from('<I',chunk.payload)[0];pos=4
                for _ in range(count):
                    key,pos=rc.read_lp_string(chunk.payload,pos)
                    value,pos=rc.read_lp_string(chunk.payload,pos)
                    if key=='albedoTexture':values.append(value)
        for chunk in document.roots:visit(chunk)
        return values
    for kind,path in manifests.items():
        manifest=read(path);source=Path(manifest['material']['source']['path'])
        if sha(source)!=manifest['material']['source']['sha256']:raise ValueError('Material source drift')
        raw=source.read_bytes();before=albedos(rc.parse(raw))
        marker=r'art\scenario\cc060_probe\albedo.rrtex'
        slots=variants.material_slots(raw)
        after=(albedos(rc.parse(variants.rewrite_material(raw,{'albedoTexture':marker},{})))
               if 'albedoTexture' in slots['textures'] else [])
        rows[kind]={'manifest':str(path),'manifest_sha256':sha(path),
                    'material_sha256':sha(source),'native_albedo_references':before,
                    'distinct_native_albedos':len(set(before)),
                    'override_albedo_references':after,
                    'override_replaces_every_material':bool(after) and all(x==marker for x in after),
                    'single_slot_override_safe_for_distinct_atlases':bool(before) and len(set(before))<=1,
                    'available_slots':slots}
    report=OUT/'qualification/multi-material-variant-scope.json'
    write(report,{'schema':'ccp-060-installed-variant-material-scope/v1',
                  'status':'read_only_supported_api_probe','models':rows,
                  'limits':'In-memory compiled material contract only, no source changes or native acceptance.'})
    print(json.dumps({k:{'native_albedos':v['distinct_native_albedos'],
                         'global_slot_override':v['override_replaces_every_material']} for k,v in rows.items()},indent=2))


if __name__=='__main__':main()

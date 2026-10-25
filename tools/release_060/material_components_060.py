"""Compose complete native-cooked material components for multi-atlas models.

Garrison's supported variant override is global. Here each chosen GMat is taken
whole from a successful albedo-only native variant. No packed image, shader,
parameter or texture-table payload is authored or hand-patched.
"""
import argparse
import json
import struct
import sys
from pathlib import Path
from common import CFG, OUT, guard, owned, read, sha, write

sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import relic_chunky as rc
from garrison_shared import model_variants


def canonical(chunk, albedo_slot='albedoTexture'):
    if chunk.children:
        payload=tuple(canonical(c,albedo_slot) for c in chunk.children)
    elif chunk.tag==b'PbTe':
        count=struct.unpack_from('<I',chunk.payload)[0];position=4;values=[]
        for _ in range(count):
            key,position=rc.read_lp_string(chunk.payload,position)
            value,position=rc.read_lp_string(chunk.payload,position)
            values.append((key,'<ALBEDO>' if key==albedo_slot else value))
        if position!=len(chunk.payload):raise ValueError('Unsupported texture table suffix')
        payload=tuple(values)
    else:payload=chunk.payload
    return chunk.kind,chunk.tag,chunk.version,chunk.name,payload


def material_roots(document):
    roots={}
    for chunk in document.roots:
        if chunk.tag!=b'GMat':raise ValueError('Unexpected non-material root')
        name=chunk.name.rstrip(b'\0').decode('utf-8')
        if name in roots:raise ValueError('Duplicate native material name')
        roots[name]=chunk
    return roots


def validate_component_texture(raw,name,emitted_member,slot):
    root=material_roots(rc.parse(raw))[name];references=[]
    def visit(chunk):
        if chunk.children:
            for child in chunk.children:visit(child)
        elif chunk.tag==b'PbTe':
            count=struct.unpack_from('<I',chunk.payload)[0];position=4
            for _ in range(count):
                key,position=rc.read_lp_string(chunk.payload,position)
                value,position=rc.read_lp_string(chunk.payload,position)
                if key==slot:references.append(value.replace('\\','/'))
            if position!=len(chunk.payload):raise ValueError('Unsupported texture table suffix')
    visit(root)
    if not references or any(value!=emitted_member for value in references):
        raise ValueError('Composed component does not resolve to its emitted texture')


def merge_texture_payload(payloads,texture):
    member=texture['member']
    for existing,record in payloads.items():
        if existing.casefold()==member.casefold():
            if existing!=member or record['sha256']!=texture['sha256'] or (
                'bytes' in record and 'bytes' in texture and record['bytes']!=texture['bytes']):
                raise ValueError('Conflicting texture output member')
            return
    payloads[member]=texture


def compose(stock_bytes,parts,albedo_slot='albedoTexture'):
    """parts maps exact material name to an entire cooked RRMaterial document."""
    if albedo_slot not in ('albedoTexture','albedoTex'):raise ValueError('Unsupported native albedo slot')
    original=rc.parse(stock_bytes);roots=material_roots(original);selected={}
    if not parts or not set(parts)<=set(roots):raise ValueError('Unknown or empty material selection')
    for name,variant_bytes in parts.items():
        variant=rc.parse(variant_bytes)
        if (variant.version,variant.flags)!=(original.version,original.flags):
            raise ValueError('Material document header drift')
        other=material_roots(variant)
        if tuple(other)!=tuple(roots):raise ValueError('Variant material identities/order changed')
        if tuple(canonical(c,albedo_slot) for c in variant.roots)!=tuple(canonical(c,albedo_slot) for c in original.roots):
            raise ValueError('Variant changed beyond native albedo references')
        selected[roots[name].offset]=other[name].payload
    result=rc.rebuild(original,lambda chunk:selected.get(chunk.offset))
    finished=rc.parse(result)
    if tuple(canonical(c,albedo_slot) for c in finished.roots)!=tuple(canonical(c,albedo_slot) for c in original.roots):
        raise ValueError('Composition altered non-albedo material data')
    for name,chunk in material_roots(finished).items():
        expected=material_roots(rc.parse(parts[name]))[name] if name in parts else roots[name]
        if (chunk.kind,chunk.tag,chunk.version,chunk.name,chunk.payload)!=(expected.kind,expected.tag,expected.version,expected.name,expected.payload):
            raise ValueError('Composed component not exact native source')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',required=True,type=Path)
    args=parser.parse_args();guard();spec=read(owned(args.spec))
    if spec.get('schema')!='ccp-060-native-material-components/v1':raise ValueError('Spec schema')
    stock_path=owned(spec['stock_manifest']);stock=read(stock_path)
    if sha(stock_path)!=spec['stock_manifest_sha256']:raise ValueError('Pinned stock manifest drift')
    original_path=Path(stock['material']['source']['path'])
    if sha(original_path)!=stock['material']['source']['sha256']:raise ValueError('Stock material drift')
    parts={};reports={};texture_payloads={}
    for name,entry in spec['materials'].items():
        verification_path=owned(entry['verification']);report=read(verification_path)
        if (sha(verification_path)!=entry['verification_sha256'] or
            report['status']!='albedo_only_all_other_material_chunks_exact' or
            report['donor_manifest_sha256']!=sha(stock_path) or
            not report['stock_geometry_byte_identical'] or
            not report['normal_metal_owner_pattern_skin_lut_and_other_params_exact']):
            raise ValueError('Successful exact-donor albedo-only native verification required')
        for item in report['extracted'].values():
            if sha(item['path'])!=item['sha256']:raise ValueError('Native component readback drift')
        if any(change['slot']!=spec.get('albedo_slot','albedoTexture') for change in report['changes']):
            raise ValueError('Native source changed a different albedo slot')
        parts[name]=Path(report['extracted']['.rrmaterial']['path']).read_bytes()
        reports[name]=report
        texture=report['extracted']['.rrtex']
        validate_component_texture(parts[name],name,texture['member'],spec.get('albedo_slot','albedoTexture'))
        merge_texture_payload(texture_payloads,texture)
    base=reports[spec['base_material']]
    private=base['extracted'];old=stock['resources']['model'];new=private['.rgm']
    if sha(old['cache_path'])!=old['sha256']:raise ValueError('Stock RGM drift')
    expected=model_variants.rewrite_model_path(Path(old['cache_path']).read_bytes(),
        old['logical_path'].removesuffix('.rgm'),new['member'].removesuffix('.rgm'))
    if expected!=Path(new['path']).read_bytes():raise ValueError('Native RGM changed beyond private path')
    if private['.rrgeom']['sha256']!=stock['geometry']['source']['sha256']:
        raise ValueError('Compatible stock geometry changed')
    output=owned(spec['output']);receipt=owned(spec['receipt'])
    if output.exists() or receipt.exists():raise FileExistsError('Preserve earlier composition')
    raw=compose(original_path.read_bytes(),parts,spec.get('albedo_slot','albedoTexture'))
    for name,report in reports.items():
        validate_component_texture(raw,name,report['extracted']['.rrtex']['member'],spec.get('albedo_slot','albedoTexture'))
    output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(raw)
    payloads=[private[x] for x in ('.rgm','.rgo','.rrgeom')]+list(texture_payloads.values())
    payloads.append({'member':private['.rrmaterial']['member'],'path':str(output),'sha256':sha(output)})
    write(receipt,{'schema':'ccp-060-native-material-component-pair/v1',
        'status':'native_component_sources_composed_no_actor_activation',
        'spec':str(args.spec),'spec_sha256':sha(args.spec),'stock_manifest_sha256':sha(stock_path),
        'payloads':payloads,'model_logical_path':new['member'],
        'materials':spec['materials'],'geometry_scope':'compatible stock remix; native geometry/rig/LODs unchanged',
        'every_component_exact_native_cooked_bytes':True,
        'normal_metal_pattern_skin_lut_and_all_non_albedo_fields_exact':True,
        'native_appearance_and_animation_acceptance':False})
    print(json.dumps({'status':'composed','receipt':str(receipt),'materials':len(parts)},indent=2))


if __name__=='__main__':main()

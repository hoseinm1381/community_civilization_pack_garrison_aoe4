"""Independently compare supported variant RGOs with exact installed stock RGOs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from common import ARCH, OUT, guard, owned, read, sha, write

ARCHIVES={'chinese':'ArtChinese.sga','mongols':'ArtMongols.sga',
          'sultanate_ha_tug':'ArtSultanateHA.sga','sultanate':'ArtSultanate.sga',
          'english':'ArtEnglish.sga','ottoman':'ArtOttoman.sga',
          'common':'ArtCivilizations.sga'}


def verify_one(donor_path,material_path):
    donor=read(owned(donor_path));material=read(owned(material_path))
    if material['donor_manifest_sha256']!=sha(donor_path):raise ValueError('Variant donor differs')
    item=material['extracted']['.rgo']
    if sha(item['path'])!=item['sha256']:raise ValueError('Private variant RGO drift')
    model=donor['resources']['model'];logical=model['logical_path'].removesuffix('.rgm')+'.rgo'
    civilization=logical.split('/')[2]
    archive=Path(model['archive_path']).with_name(ARCHIVES[civilization])
    token=hashlib.sha256(logical.encode()).hexdigest()[:20]
    folder=owned(OUT/'qualification/native-rgo-controls'/token);source=folder/'stock.rgo';receipt=folder/'source.json'
    if receipt.exists():
        old=read(receipt);stat=archive.stat()
        if old['member']!=logical or old['sha256']!=sha(source) or old['archive_bytes']!=stat.st_size or old['archive_mtime_ns']!=stat.st_mtime_ns:
            raise ValueError('Official RGO cache/archive drift')
    else:
        if source.exists():raise FileExistsError('Preserve incomplete official RGO extraction')
        folder.mkdir(parents=True,exist_ok=True)
        command=[str(ARCH),'extract-member',str(archive),logical,str(source)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=120)
        (folder/'extract.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError('Exact native RGO extraction failed: '+logical)
        stat=archive.stat()
        write(receipt,{'member':logical,'archive':str(archive),'archive_bytes':stat.st_size,
            'archive_mtime_ns':stat.st_mtime_ns,'path':str(source),'sha256':sha(source)})
    if source.read_bytes()!=Path(item['path']).read_bytes():
        raise ValueError('Private variant RGO is not byte-identical to exact installed source: '+logical)
    return {'stock_member':logical,'stock_source_receipt':str(receipt),'stock_source_receipt_sha256':sha(receipt),
            'private_rgo':item,'native_rgo_byte_identical':True,
            'donor_manifest_sha256':sha(donor_path),'material_report':str(material_path),'material_report_sha256':sha(material_path)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=Path,required=True,help='JSON rows with donor_manifest/material_verification')
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();guard();target=owned(args.report)
    if target.exists():raise FileExistsError('Preserve previous RGO proof')
    jobs=read(owned(args.jobs));rows=[verify_one(Path(j['donor_manifest']),Path(j['material_verification'])) for j in jobs]
    write(target,{'schema':'ccp-060-original-native-rgo-byte-proof/v1','status':'all_exact_installed_stock_rgos_preserved',
        'jobs':str(args.jobs),'jobs_sha256':sha(args.jobs),'rows':rows,'native_appearance_and_animation_acceptance':False})
    print(json.dumps({'status':'stock_rgos_byte_exact','models':len(rows),'report':str(target)}))


if __name__=='__main__':main()

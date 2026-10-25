"""Activate only qualified 070 visual source identities and monk SCAR.

Content Editor alone does not reproduce the binary private stamp graft. The
release integration recipes remain required after a source build. Never refresh
the frozen 061 source baseline to accept this authorized delta.
"""
from pathlib import Path
import argparse,json,hashlib,sys,shutil,os
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
CFG=configuration(ROOT);OUT=Path(CFG['external_root'])/'output/release_070'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def candidates():
    stage=(ROOT/'staging/release_070/integration').resolve(strict=True)
    garden=json.loads((stage/'garden-binding-draft/receipt.json').read_text())
    others=json.loads((stage/'remaining-binding-draft/receipt.json').read_text())
    result=[]
    for parent,record in ((stage/'garden-binding-draft',garden),(stage/'remaining-binding-draft',others)):
        identities=record['identities']
        actors=[{'source':record['actor_source'],'source_after_sha256':record['actor_source_after_sha256']}] if 'actor_source' in record else record['actors']
        for row in actors:
            p=Path(row['source']);result.append((p,p.relative_to(parent/'assets').as_posix(),row['source_after_sha256']))
        for row in identities:
            p=Path(row['source_xml']);result.append((p,p.relative_to(parent/'assets').as_posix(),row['source_xml_sha256']))
    p=OUT/'monk/prematch_precache.scar';record=json.loads((OUT/'monk/verification.json').read_text())
    result.append((p,'scar/vietnam/prematch_precache.scar',record['overlay_sha256']))
    assert len(result)==14 and len({r[1] for r in result})==14
    assert len([r for r in result if '/ebps/' in r[1]])==4
    assert len([r for r in result if '/attachment_lists/' in r[1]])==9
    return result
def main(combined,apply=False):
    check_storage(ROOT,CFG)
    manifest=json.loads(Path(combined).read_text())
    assert manifest['schema']=='ccp-070-qualified-integration-allowlist/v1'
    assert len(manifest['scoped_compiled_actor_members'])==4
    for row in manifest['payloads']:assert sha(row['file'])==row['sha256']
    baseline=json.loads((OUT/'baseline/freeze.json').read_text())
    assert manifest['baseline_sga_sha256']==baseline['baseline_sga_sha256']
    rows=candidates();allowed={r[1] for r in rows}
    actual={p.relative_to(ROOT/'assets').as_posix():sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()}
    expected={k:v['sha256'] for k,v in baseline['source'].items()}
    # Permit an exact repeat, never drift or any unrelated source delta.
    after=expected|{rel:digest for _,rel,digest in rows}
    assert actual==expected or actual==after,'Active source drift; preserve evidence and investigate'
    for p,rel,digest in rows:assert sha(p)==digest,(p,rel)
    target=OUT/'source-activation'
    if apply:
        target.mkdir(exist_ok=True)
        for p,rel,digest in rows:
            dest=ROOT/'assets'/rel
            backup=target/'before'/rel
            if rel in expected and not backup.exists():
                backup.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(dest,backup)
            if dest.exists() and sha(dest)==digest:continue
            dest.parent.mkdir(parents=True,exist_ok=True)
            tmp=dest.with_name(dest.name+'.070-tmp');shutil.copyfile(p,tmp);os.replace(tmp,dest)
        actual={p.relative_to(ROOT/'assets').as_posix():sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()}
        assert actual==after
        report={'schema':'ccp-070-source-activation/v1','status':'qualified_overlay_applied','baseline_source_files':len(expected),'unchanged_baseline_source_files':sum(actual.get(k)==v for k,v in expected.items()),'modified':[k for k,v in expected.items() if actual[k]!=v],'added':sorted(set(actual)-set(expected)),'source_sha256':actual,'allowed_paths':sorted(allowed),'combined_receipt':str(Path(combined).resolve()),'combined_sha256':sha(combined),'limits':'Native cooks and post-build private stamp graft remain required; not native match proof.'}
        (target/'receipt.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
    else:print(json.dumps({'status':'dry_run_no_source_changes','paths':sorted(allowed)},indent=2))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--combined',required=True);a.add_argument('--apply',action='store_true');v=a.parse_args();main(v.combined,v.apply)

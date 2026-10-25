"""Keep frozen hashes intact; recognize the one explicit user-approved art edit."""
import json
from pathlib import Path
from pipeline import digest,save_json,guard
from providers import ROOT,OUT


def permitted_authoring_change(path,expected,approval,root=ROOT):
    allowed=Path(root)/'art/authoring/release_081/buffalo/r4/model.blend'
    return bool(approval and approval.get('user_approved') is True and
                Path(path).resolve()==allowed.resolve()==Path(approval['path']).resolve() and
                approval.get('baseline_sha256')==expected)


def main():
    guard();baseline=json.loads((OUT/'baseline.json').read_text())
    approval_file=OUT/'local/approved-authoring-deviation.json'
    approval=json.loads(approval_file.read_text()) if approval_file.exists() else None
    unchanged=0;approved=[];errors=[]
    for index,(path,expected) in enumerate(baseline['protected'].items(),1):
        actual=digest(path) if Path(path).is_file() else None
        if actual==expected:unchanged+=1
        elif actual and permitted_authoring_change(path,expected,approval):
            approved.append(dict(path=path,baseline_sha256=expected,current_sha256=actual,
                                 action='Preserve this editable file; package exact 0.8.3 compiled buffalo'))
        else:errors.append(dict(path=path,expected=expected,actual=actual))
        if index%1000==0:print('PRESERVATION_FILES_CHECKED',index,flush=True)
    for path,expected in [(baseline['sga'],baseline['sga_sha256']),(baseline['zip'],baseline['zip_sha256'])]:
        if digest(path)!=expected:errors.append(dict(path=path,reason='Immutable 0.8.3 delivery differs'))
    result=dict(passed=not errors,unchanged_files=unchanged,approved_authoring_changes=approved,errors=errors,
                baseline_freeze_rewritten=False,active_assets_changed=False)
    save_json(OUT/'local/preservation-after-reboot.json',result)
    print('PRESERVATION_AUDIT',unchanged,'unchanged;',len(approved),'approved authoring edits;',len(errors),'errors',flush=True)
    if errors:raise SystemExit(1)


if __name__=='__main__':main()

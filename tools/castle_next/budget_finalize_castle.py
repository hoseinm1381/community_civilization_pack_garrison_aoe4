"""Finalize the already-proved Castle drawgraph bounds under the approved 50% cap.

This performs no extraction, decoding, cooking, or archive writes. It preserves
the strict ±10% diagnostic report and recomputes only the budget decision.
"""
from __future__ import annotations
import copy
from pathlib import Path
from common import OUT, guarded, read, sha, write

def main() -> int:
    guarded()
    report_path=OUT/'budget'/'castle-stock-landmark-budget.json'
    strict_path=OUT/'budget'/'castle-stock-landmark-budget-strict-diagnostic.json'
    alias_path=OUT/'inventory'/'castle-landmark-triangle-budget.json'
    original=read(strict_path) if strict_path.exists() else read(report_path)
    if original.get('schema')!='community-civilization-pack/castle-next-stock-landmark-budget/v1':
        raise RuntimeError('Unexpected stock landmark budget report schema')
    if original.get('budget',{}).get('expected_choices')!=14 or len(original.get('choices',[]))!=14:
        raise RuntimeError('Expected complete 14-choice inventory before finalization')
    if original.get('blockers'):
        raise RuntimeError('Native geometry closure contains blockers; cannot finalize')
    rows=original['choices']
    lower=[r['default']['lower'] for r in rows]
    upper=[r['default']['upper'] for r in rows]
    if any(not isinstance(x,(int,float)) or x<0 for x in lower+upper):
        raise RuntimeError('Missing or invalid per-choice native bounds')
    if any(a>b for a,b in zip(lower,upper)):
        raise RuntimeError('A per-choice lower bound exceeds its upper bound')
    b=original['budget']
    mean_lower=sum(lower)/14; mean_upper=sum(upper)/14
    if abs(mean_lower-b['mean_lower'])>1e-8 or abs(mean_upper-b['mean_upper'])>1e-8:
        raise RuntimeError('Embedded means do not recompute from the 14 native choice bounds')
    strict_sha=sha(strict_path) if strict_path.exists() else sha(report_path)
    if not strict_path.exists():
        write(strict_path,original)
    strict_saved_sha=sha(strict_path)
    user_overstock_limit=0.50
    proved_user_cap=(1.0+user_overstock_limit)*mean_lower
    maximum_guaranteed_cap=min(proved_user_cap,max(lower))
    target=90000
    target_min=int(round(0.90*target)); target_max=int(round(1.10*target))
    if target>maximum_guaranteed_cap or target_max>maximum_guaranteed_cap:
        raise RuntimeError('Approved 90k working range exceeds the proven 50% cap')
    if max(lower)>maximum_guaranteed_cap:
        # Preserve both values; the lower-bound maximum itself is a sampled
        # stock point, while the selected art cap obeys the user overstock cap.
        cap_proof={'sample_lower_maximum':max(lower),'user_overstock_cap':proved_user_cap}
    else:
        cap_proof={'sample_lower_maximum':max(lower),'user_overstock_cap':proved_user_cap}
    final=copy.deepcopy(original)
    final['status']='qualified_conservative_50percent_cap'
    final['qualification']={
        'user_approved_constraint':'It is acceptable for the chosen art target to be no more than 50% above the stock arithmetic-average landmark triangle count.',
        'proof':'Each actual stock choice count is at least its decoded lower bound, so the true stock mean is at least mean_lower. The selected target and its complete ±10% art working range are below 1.5×mean_lower; therefore the chosen target does not exceed the user-approved 50% overstock ceiling for the unknown true mean.',
        'budget_bounds_reused_without_new_decode':True,
        'choice_count':14,
        'strict_diagnostic_report':str(strict_path),
        'strict_diagnostic_sha256':strict_saved_sha,
        'pre_finalization_report_sha256':strict_sha,
        'user_overstock_limit_fraction':user_overstock_limit,
        'proved_user_cap_from_mean_lower':proved_user_cap,
        'maximum_guaranteed_cap':maximum_guaranteed_cap,
        'working_range_guaranteed_within_cap':True,
    }
    final['budget'].update({
        'mean':None,
        'mean_lower':mean_lower,
        'mean_upper':mean_upper,
        'exact_mean':None if lower!=upper else mean_lower,
        'user_overstock_limit_fraction':user_overstock_limit,
        'user_cap_from_mean_lower':proved_user_cap,
        'maximum_guaranteed_cap':maximum_guaranteed_cap,
        'target_triangles':target,
        'guaranteed_target_min':target_min,
        'guaranteed_target_max':target_max,
        'strict_10_percent_mean_interval':{'minimum':b.get('guaranteed_target_min'),'maximum':b.get('guaranteed_target_max'),'status':'empty_under_strict_rule'},
    })
    final['metric'] += ' Budget acceptance applies the explicit user-approved 50% overstock cap; exact stock arithmetic mean remains unknown within reported bounds.'
    write(report_path,final)
    alias={
        'schema':'community-civilization-pack/castle-next-landmark-triangle-budget/v1',
        'proof_status':final['status'],
        'mean_target_triangles':target,
        'maximum':maximum_guaranteed_cap,
        'guaranteed_target_min':target_min,
        'guaranteed_target_max':target_max,
        'guaranteed_target_interval':[target_min,target_max],
        'mean_lower':mean_lower,
        'mean_upper':mean_upper,
        'exact_mean':None,
        'user_overstock_limit_fraction':user_overstock_limit,
        'user_cap_from_mean_lower':proved_user_cap,
        'source_report':str(report_path),
        'source_report_sha256':sha(report_path),
        'strict_diagnostic_report':str(strict_path),
        'strict_diagnostic_sha256':strict_saved_sha,
        'criterion':'Fourteen exact Castle-age actors; complete default/skirmish native drawgraph bounds; selected target and ±10% working range satisfy the user-approved 50% overstock cap.',
    }
    write(alias_path,alias)
    print(f'qualified: {final["status"]}')
    print(f'budget report: {report_path}')
    print(f'strict diagnostic: {strict_path}')
    print(f'landmark alias: {alias_path}')
    print(f'mean bounds: {mean_lower:.2f}..{mean_upper:.2f}; exact mean remains unknown')
    print(f'target: {target}; working range: {target_min:.0f}..{target_max:.0f}; max cap: {maximum_guaranteed_cap:.2f}')
    return 0

if __name__=='__main__': raise SystemExit(main())

"""Interactive-turn worker, serial and bounded; no scheduling or billing changes."""
import json,sys
from batching import main as generate
from pipeline import guard,save_json,StateStore
from providers import OUT,ProviderError
from budget import account_for
from salvage import main as salvage

def choose_role(queue,attempts,totals):
    roles={j['role'] for j in queue}
    return min(roles,key=lambda role:(min(attempts.get(j['id'],0) for j in queue if j['role']==role),totals[role],role))


def main(secrets):
    guard();network_stops=0;credit_stops=0;queue=[];status=dict(status='no_eligible_jobs')
    for chunk in range(100):
        salvage()
        jobs=json.loads((OUT/'recording-manifest.json').read_text())['jobs'];state=StateStore(OUT/'generation')
        attempts_file=OUT/'generation/attempts.json';attempts=json.loads(attempts_file.read_text()) if attempts_file.exists() else {}
        totals={j['role']:sum(k['role']==j['role'] for k in jobs) for j in jobs}
        queue=[j for j in jobs if j['casting']['provider']==secrets['production_provider'] and not state.ready(j['id'],j) and attempts.get(j['id'],0)<3]
        if not queue:break
        target=choose_role(queue,attempts,totals)
        generate(dict(secrets,production_role=target),max_batches=8,max_seconds=90)
        status=json.loads((OUT/'generation/status.json').read_text())
        if (OUT/'generation/STOP_AFTER_BATCH').exists():break
        jobs=json.loads((OUT/'recording-manifest.json').read_text())['jobs'];state=StateStore(OUT/'generation')
        attempts=json.loads((OUT/'generation/attempts.json').read_text())
        queue=[j for j in jobs if j['casting']['provider']==secrets['production_provider'] and not state.ready(j['id'],j) and attempts.get(j['id'],0)<3]
        if not queue:break
        if status['status']=='provider_stopped':
            if status.get('category')!='credits_exhausted':break
            credit_stops+=1
            if credit_stops>2:break
            try:account_for(secrets,100)
            except ProviderError:break
        else:credit_stops=0
        if status['status']=='network_stopped':
            network_stops+=1
            if network_stops>=3:break
        else:network_stops=0
    save_json(OUT/'generation/worker-finished.json',dict(last_status=status,chunks=chunk+1,queue_remaining=len(queue)))
    print('084_WORKER_FINISHED',status['status'],len(queue),flush=True)

if __name__=='__main__':main(json.load(sys.stdin))

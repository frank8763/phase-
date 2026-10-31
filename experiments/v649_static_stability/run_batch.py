"""Host orchestrator: every simulator process still runs through run_phase.sh."""
import argparse,fcntl,json,subprocess,time,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('plan');p.add_argument('--name',required=True);p.add_argument('--budget',type=float,required=True);a=p.parse_args()
repo=Path(__file__).resolve().parents[2];runs=repo/'runs/v649_static_stability';runs.mkdir(exist_ok=True)
lock=(runs/'batch.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
out=runs/a.name;out.mkdir();plan=json.loads(Path(a.plan).read_text());(out/'PLAN.json').write_text(json.dumps(plan,indent=2));rows=[];start=time.monotonic()
for case in plan['cases']:
 remaining=a.budget-(time.monotonic()-start)
 if remaining<case.get('minimum_remaining_s',5):break
 cmd=[str(repo/'run_phase.sh'),'experiments/v649_static_stability/run_static.py','--name',case['name'],'--seed',str(case['seed']),'--scene',case['scene'],'--conditions',case.get('conditions','circle_memory'),'--wall-seconds',str(min(900,max(1,int(remaining)-2)))]
 if case.get('preflight_only'):cmd+=['--preflight-only']
 begin=time.monotonic()
 with(out/(case['name']+'.console')).open('w')as stream:
  try:r=subprocess.run(cmd,cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=min(905,remaining));code=r.returncode
  except subprocess.TimeoutExpired:code=124
 completion=runs/case['name']/'paired/completion.json';preflight=runs/case['name']/'paired/PREFLIGHT.json'
 record={'case':case,'returncode':code,'wall_s':time.monotonic()-begin,'completion':json.loads(completion.read_text())if completion.exists()else None,'preflight':json.loads(preflight.read_text())if preflight.exists()else None}
 rows.append(record);(out/'RESULTS.json').write_text(json.dumps(rows,indent=2));print(case['name'],code,record['preflight'],flush=True)
(out/'BATCH_COMPLETION.json').write_text(json.dumps({'cases_planned':len(plan['cases']),'cases_attempted':len(rows),'elapsed_s':time.monotonic()-start,'execution_budget_s':a.budget,'unattempted_names':[c['name']for c in plan['cases'][len(rows):]]},indent=2))

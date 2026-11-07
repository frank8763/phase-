"""Operational continuation of the exact frozen Nav2 queue, with new output paths."""
import json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OLD=R/'runs/v858_nav2_verified';OUT=OLD/'v859_steering';sys.path.insert(0,str(R/'experiments/v858_nav2_verified'))
import campaign as base
original_verify=base.verify
def verify():
 original_verify()
 import hashlib
 for p,h in json.loads((HERE/'SOURCE_FREEZE.json').read_text())['files'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,'ENTRY_FROZEN_SOURCE_CHANGED '+p
base.verify=verify;base.OUT=OUT
original_run=base.run_task
original_popen=subprocess.Popen
def entry_popen(args,*a,**kw):
 args=list(args)
 for i,s in enumerate(args):
  if str(s)=='experiments/v858_nav2_verified/native_worker.py':args[i]=str((HERE/'native_entry.py').relative_to(R))
 return original_popen(args,*a,**kw)
subprocess.Popen=entry_popen
def run_task(task):
 return original_run(dict(task,output=str(OUT/task['id'])))
base.run_task=run_task
def confirm_t0(tasks):
 rows=[]
 for t in tasks:
  verify();assert time.time()<base.END-300
  with(OUT/(t['id']+'.t0.console')).open('w')as f:p=subprocess.run([str(R/'run_phase.sh'),'experiments/v858_nav2_verified/preflight.py',str(base.task_path(t))],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=90)
  r=json.loads((OLD/'preflights'/(t['id']+'.RESULT.json')).read_text());rows.append(dict(id=t['id'],result=r,returncode=p.returncode));base.dump(OUT/'CONFIRMATION_PREFLIGHTS.json',dict(passed=len(rows)==24 and all(x['result']['passed']for x in rows),rows=rows,native_integrations=0));assert p.returncode==0 and r['passed'],'CONFIRMATION_T0_FAILED'
base.confirm_t0=confirm_t0
if __name__=='__main__':
 assert json.loads((OUT/'QUALIFICATION_INDEPENDENT_AUDIT.json').read_text())['passed']
 base.main()

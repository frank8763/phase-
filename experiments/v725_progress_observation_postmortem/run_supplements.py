"""One 600s zero-integration diagnostic window; do not resume navigation."""
import json,os,subprocess,sys,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;window=repo/'runs/v725_offline_window.json';assert not window.exists()
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time();deadline=begun+600
state=dict(started_unix=begun,absolute_deadline_unix=deadline,limit_s=600,round_closed=False,new_initializations=0,new_integrations=0,training_updates=0)
def write():window.write_text(json.dumps(state,indent=2)+'\n')
write();rows=[]
try:
 for name in ['audit_recovery_selection.py','audit_route_commitment.py','audit_projection_learning.py','audit_all_tail_geometry.py','audit_shadow_mode.py','audit_field_discovery.py']:
  assert time.time()+123<deadline,'NO_REMAINING_OFFLINE_BUDGET'
  log=repo/'runs'/('v725_'+name+'.console')
  with log.open('x')as stream:r=subprocess.run([sys.executable,'-B',str(own/'supplement.py'),name],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=120)
  rows.append(dict(script=name,exit_code=r.returncode));state['records']=rows;write()
  assert r.returncode==(1 if name=='audit_field_discovery.py'else 0),'SUPPLEMENTAL_AUDIT_EXCEPTION_OR_CHECK_FAILURE'
 state['status']='ALL_FIXED_SAVED_EVIDENCE_CHECKS_EXECUTED'
finally:
 state.update(round_closed=True,elapsed_s=time.time()-begun,records=rows);write()
print(json.dumps(state))

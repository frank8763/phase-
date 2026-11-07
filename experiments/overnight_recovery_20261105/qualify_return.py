"""Exercise real supervisor with recorded nominal inputs; synthetic admission never proves safety."""
import importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v830_ranked_return_development'
for d in [repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1',own]:sys.path.insert(0,str(d))
from recovery_supervisor import RecoverySupervisor
import recovery_supervisor as module
from audit_ranked_return import audit
base=repo/'runs/v828_goal_dynamic_confirmation/main_slot02/paired';source=base/'geometry_memory';q=repo/'runs/overnight_recovery_20261105/qualification';pair=q/'return_rejection_seam/paired';pair.mkdir(parents=True)
for p in base.iterdir():
 if p.name!='geometry_memory':(pair/p.name).symlink_to(p,target_is_directory=p.is_dir())
cell=pair/'geometry_memory';cell.mkdir()
for p in source.iterdir():
 if p.name!='control_decisions.jsonl':(cell/p.name).symlink_to(p,target_is_directory=p.is_dir())
decisions=[json.loads(s)for s in(source/'control_decisions.jsonl').open()]
original=[x for x in decisions if x.get('candidate_role')=='BACKUP_RETURN'and x['stage']=='NOMINAL'];emissions=[]
module.emit=lambda cell,name,row:emissions.append((name,row))
goal=np.array([4.,-2.]);tests=[]
for n in original:
 rows=[]
 for c in n['candidates']:
  if c['reason']is not None:continue
  z=np.load(source/'nominal_forecasts'/c['nominal_saved_forecast']);rows.append((c['score'],np.asarray(c['first_command']),z['poses'].copy(),c['minimum_clearance_m'],c['self_domain_margin_m']))
 rows.sort(key=lambda x:x[0],reverse=True);assert rows
 z=np.load(source/'nominal_forecasts'/next(c['nominal_saved_forecast']for c in n['candidates']if c['reason']is None))
 class Predictor:
  prediction_steps=0;last_diagnostics=n['candidates'];ranked_safe_candidates=rows
  def select(self,*args):return rows[0][1].copy(),dict(n['summary'])
 class Reserve:
  cache={'created_step':n['old_created_step']};cursor=n['old_native_cursor'];last_handover_attempt={'status':'NO_APPENDABLE_BACKUP'}
  def check_current_contract(self,*args):pass
  def try_handover(self,*args,**kwargs):self.calls+=1;return None
 r=Reserve();r.calls=0;s=RecoverySupervisor(cell);s.path=np.c_[z['reference'],np.ones(len(z['reference']))];s.index=0;s.first_step=n['step']-n['backup_age_public_steps']
 env=SimpleNamespace(goal_xy=goal,inner=SimpleNamespace(wheel_base=.3,max_steer=.6981317007977318),data=object())
 current=z['initial_pose'];answer=s._try_return_impl(env,None,None,r,Predictor(),current,z['last_command'],n['step']);assert answer is None
 eligible={tuple(c[1])for c in rows if np.linalg.norm(current[:2]-goal)-np.linalg.norm(c[2][-1,:2]-goal)>=.02}
 assert r.calls==len(eligible)
 tests.append(dict(step=n['step'],eligible_distinct=len(eligible),attempts=r.calls))
reconstructed=[x for x in decisions if x.get('candidate_role')!='BACKUP_RETURN']+[r for name,r in emissions if name=='control_decisions.jsonl']
(cell/'control_decisions.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in reconstructed))
result=audit(pair);assert result['status']=='RANKED_RETURN_INDEPENDENT_PASS'
# Remove one interior selection row: the actual independent auditor must fail.
selection=next(i for i,x in enumerate(reconstructed)if x.get('stage')=='RETURN_SELECTION')
(cell/'control_decisions.jsonl').write_text(''.join(json.dumps(x)+'\n'for i,x in enumerate(reconstructed)if i!=selection))
try:audit(pair)
except(AssertionError,IndexError):negative=True
else:negative=False
assert negative,'TAMPERED_RETURN_ORDER_NOT_REJECTED'
(cell/'control_decisions.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in reconstructed));audit(pair)
# Positive state-machine path with a clearly labeled fake backend, no scientific certificate claimed.
n=original[-1];rows=rows;emissions.clear();r=Reserve();r.calls=0
def synthetic_accept(data,command,*args,**kwargs):
 r.calls+=1;return {'handover_certificate':'SYNTHETIC_INTERFACE_ONLY','reserve_total_native_ticks':328}
r.try_handover=synthetic_accept
s=RecoverySupervisor(cell);s.path=np.c_[z['reference'],np.ones(len(z['reference']))];s.index=0;s.first_step=n['step']-n['backup_age_public_steps']
answer=s._try_return_impl(env,None,None,r,Predictor(),current,z['last_command'],n['step'])
assert answer is not None and r.calls==1 and answer[1]['return_nominal_rank']>0 and s.successes==1
assert answer[1]['predicted_end_pose']!=n['summary']['predicted_end_pose']
report=dict(passed=True,recorded_return_seams=tests,independent_reconstruction_passed=True,missing_order_negative_rejected=negative,synthetic_success_path_interface_passed=True,synthetic_backend_explicitly_not_native_feasibility=True,models=0,integrations=0)
(q/'RETURN_SEARCH_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

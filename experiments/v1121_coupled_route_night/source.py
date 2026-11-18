"""Complete propagated executable source; geometric proposal is guidance only."""
import sys,json,math,time,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(R/'experiments/v1118_coupled_live_qualification'));from runtime import Engine as CalibratedEngine,Predictor,initial,python_replay,remaining_rows
sys.path.insert(0,str(C));from solver import Solver
from bindings import REQUIRED,ref,PARAMETERS
import numpy as np
import kernel
COUNTS={'cpp_native':0,'python_native':0,'optimizer_cpp_native':0}
class SourceRefusal(Exception):pass
class Engine(CalibratedEngine):
 def simulate(self,*args,**kwargs):
  self.in_call=True;result=super().simulate(*args,**kwargs);self.in_call=False;return result

def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def requests(rows):
 return np.vstack([np.tile([v,0. if mode or v==0. else v*math.tan(target)/.6,0.],(int(n),1))for target,v,n,mode in rows])
def final_gate(x,ss,uu,rows):
 rr=requests(rows);a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[:,:3]);low=float(np.minimum(a,b).min());cc,upper=kernel.checks(ss,uu,rr,x['packet'],x['setup'],np.array(x['goal']),low,REQUIRED);cursor=0;anchors=[];ready=True;mode_bound=True
 for target,v,n,mode in rows:
  n=int(n)
  if mode:
   # Multiple adjacent mode rows share the same physical anchor.
   anchor=ss[cursor,:3];a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(anchor[None,:]);raw=float(min(a[0],b[0]));lower=raw-.02-math.hypot(.44,.375)*.1;phase=ss[cursor:cursor+n+1];distance=float(np.linalg.norm(phase[:,:2]-anchor[:2],axis=1).max());angle=float(abs(np.arctan2(np.sin(phase[:,2]-anchor[2]),np.cos(phase[:,2]-anchor[2]))).max());okay=lower>=REQUIRED and distance<=.02 and angle<=.1 and abs(phase[:,3]).max()+.002<=.01;mode_bound&=okay;ready&=bool(abs(phase[-10:,6]-target).max()<=.005 and abs(phase[-10:,7]).max()<=.015 and abs(phase[-10:,3:6]).max()<=.003);anchors.append({'native':cursor,'raw_envelope_lower':lower,'passed':bool(okay)})
  cursor+=n
 cc.update(coupled_mode_envelopes=bool(mode_bound),parked_ready=bool(ready),full2200tail=bool(np.array_equal(rr[-2200:],np.zeros((2200,3)))))
 return {'passed':bool(all(cc.values())),'checks':{k:bool(v)for k,v in cc.items()},'minimum_raw_m':low,'goal_upper_m':upper,'mode_envelopes':anchors,'native':len(rr),'states_sha256':digest(ss),'controls_sha256':digest(uu)},rr

def deterministic_admission(exit,calls):
 return exit.get('status')!='FIXED_BUDGET_STOP'or calls>=1700

def solve(x,path,gear,seed=None):
 solver=Solver(x,np.array(path),gear,initial_guess=seed);begun=time.monotonic()
 try:best,iterations=solver.solve();ss,uu,rows,events=solver.simulate(best['z'],reserved_final=True)
 except AssertionError as error:
  if str(error)=='SOURCE_BUDGET_CAP':raise SourceRefusal('SOURCE_BUDGET_CAP')
  raise
 finally:COUNTS['optimizer_cpp_native']+=solver.native;COUNTS['optimizer_partial_work_unknown']=bool(solver.in_call)
 proof,rr=final_gate(x,ss,uu,rows);proof['checks']['registered_initial_mode_headroom']=all(r['raw_envelope_lower']>=REQUIRED+float(x.get('mode_reserve',.001))-1e-10 for r in proof['mode_envelopes']);proof['checks']['deterministic_work_or_feasible']=deterministic_admission(solver.optimizer_exit,solver.calls);proof['passed']=bool(all(proof['checks'].values()))
 return {'passed':proof['passed'],'proof':proof,'rows':rows,'states':ss,'controls':uu,'requests':rr,'selected_z':best['z'].tolist(),'guide_diagnostics':best['constraints'],'optimizer_exit':solver.optimizer_exit,'iterations':iterations,'optimizer_cpp_native':solver.native,'optimizer_calls':solver.calls,'solve_wall_s':time.monotonic()-begun,'geometric_guide_is_not_hard_cusp_contract':True}

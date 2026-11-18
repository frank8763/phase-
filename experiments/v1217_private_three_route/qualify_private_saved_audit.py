"""Reuse completed private-executor trace; only corrected independent audit binding."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('PRIVATE_SAVED_AUDIT_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import fcntl,types

def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 old=science();q=old.q;np=q.np
 # Preserve exact original real import collision plus all generic-name decoys.
 poison={'admission':load('admission',R/'runtime/mk-mini/experiments/phase_rpccr_p0b57_v1/admission.py')}
 for name in ['goal_entry','current_goal_source','candidate_search','connection','live_entry','audit_admission']:
  m=types.ModuleType(name);m.__file__='synthetic_wrong_'+name;sys.modules[name]=m;poison[name]=m
 core=load('phase_v1217_independent_core',R/'experiments/v1204_goal_audit_worker/audit_goal.py');auditor=load('phase_v1217_independent_admission',C/'audit_admission.py')
 out=O/'PRIVATE_GOAL_INTERFACE';b=core.load_bundle(out);p=R/'runs/v858_nav2_verified/v1210/main_WEST_EAST';x=read(p/'LIVE_GOAL_INPUT.json')
 with np.load(p/'LIVE_GOAL_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 start=time.monotonic();base=core.verify(x,table,b,True);admission=auditor.verify_bundle(x,table,b,time.monotonic()+90)
 with np.load(R/'runs/v1214_shadow_route_integration/GOAL_INTERFACE_original_WE/EXECUTED.npz')as z:maximum=max(float(abs(z[k]-b['trace'][k]).max())for k in z.files)
 assert maximum<=1e-8 and all(sys.modules[n]is m for n,m in poison.items())
 dump(out/'INDEPENDENT_CORE_AUDIT.json',base);dump(out/'INDEPENDENT_ADMISSION_AUDIT.json',admission)
 answer=b['result'];result=dict(passed=True,scope='actual new private executor completed under old cached imports; corrected audit reuses exact trace without rerunning search',trace_error_vs_qualified_V1214=maximum,real_legacy_admission_preloaded=True,other_generic_names_poisoned=True,core_audit=base,admission_audit=admission,native=answer['native'],admission_python_native=answer['admission_python_native'],generation_cpp_native=answer['analytical_cpp_native'],interface_and_shadow_python_native=2*answer['native'],models=0,new_mujoco_native=0,wall_s=time.monotonic()-start,prior_failed_audit_record='PRIVATE_GOAL_PRE_AUDIT_IMPORT_FIX.json')
 dump(O/'PRIVATE_GOAL_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()

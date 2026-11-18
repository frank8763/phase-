"""Actual new goal entry on analytical interfaces plus independent saved auditors."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('GOAL_ENTRY_QUALIFICATION_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1214_shadow_route_integration'
sys.path.insert(0,str(R/'experiments/v1213_fixed_work_shadow'))
import goal_entry
from goal_entry import q,np
import importlib.util,copy,json,time,fcntl,signal,traceback
spec=importlib.util.spec_from_file_location('v1214_analytical_interface',R/'experiments/v1203_goal_entry_handoff/qualify_entry.py');legacy=importlib.util.module_from_spec(spec);sys.modules[spec.name]=legacy;spec.loader.exec_module(legacy)
sys.path.insert(0,str(R/'experiments/v1204_goal_audit_worker'))
from audit_goal import load_bundle,verify
sys.path.insert(0,str(C))
from audit_admission import verify_bundle,verify_source

def main():
 assert not(O/'GOAL_INTEGRATION_QUALIFICATION.json').exists()
 assert json.loads((R/'runs/v1213_fixed_work_shadow/FIXED_QUALIFICATION/COMPLETION.json').read_text())['passed']
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert q.sha(R/'REVIEW_PENDING')==q.GUARD
 start=time.monotonic();end=start+600;results=[];negatives=[];error=None
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('GOAL_INTERFACE600')));signal.setitimer(signal.ITIMER_REAL,600)
 frozen={str(p.relative_to(R)):q.sha(p)for p in [C/'qualify_goal_integration.py',C/'audit_admission.py',* (R/'experiments/v1213_fixed_work_shadow').glob('*.py')]}
 q.dump(C/'GOAL_INTEGRATION_FREEZE.json',dict(files=frozen,software_only=True))
 try:
  saved=[]
  for name,version,task in [('original_WE','v1210','main_WEST_EAST'),('slot01','v1209','main_slot01'),('slot02','v1209','main_slot02')]:
   p=R/'runs/v858_nav2_verified'/version/task;x=json.loads((p/'LIVE_GOAL_INPUT.json').read_text())
   with np.load(p/'LIVE_GOAL_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
   out=O/('GOAL_INTERFACE_'+name);out.mkdir()
   v=legacy.AnalyticalInterface(x);v._live_load=True;v.predictor.steering_load_episode=True
   answer=goal_entry.execute(v,x['setup'],x,table,min(end-10,time.monotonic()+150),lambda:time.monotonic()<end-10,lambda owner:owner.packet(),lambda p:q.dump(O/'GOAL_INTERFACE_PROGRESS.json',dict(case=name,**p)),out)
   b=load_bundle(out);core=verify(x,table,b,True);admission=verify_bundle(x,table,b,min(end-5,time.monotonic()+60))
   q.dump(out/'INDEPENDENT_CORE_AUDIT.json',core);q.dump(out/'INDEPENDENT_ADMISSION_AUDIT.json',admission)
   results.append(dict(case=name,passed=True,native=answer['native'],feedback_raw=answer['proof']['minimum_raw_m'],shadow_raw=answer['shadow_proof']['minimum_raw_m'],generation_cpp=answer['analytical_cpp_native'],admission_python=answer['admission_python_native'],interface_and_shadow_python=2*answer['native'],core_cpp=core['analytical_cpp_native'],admission_cpp=admission['analytical_cpp_native'],models=0,new_mujoco_native=0))
   saved.append((x,table,b));q.dump(O/'GOAL_INTERFACE_RESULTS.json',results)
  x,table,b=saved[0];origin=b['result']['generations'][0]['origin'];so=copy.deepcopy(origin);ref=b['initial_ref']['states']
  for name,mutate in [('reset_shadow',lambda s:s['admission'].update(shadow_memory_reset=True)),('shadow_state',lambda s:s['admission']['shadow_origin']['state'].__setitem__(0,s['admission']['shadow_origin']['state'][0]+.01)),('offset',lambda s:s['admission'].update(offset=1)),('false_shadow_clearance',lambda s:s['admission']['continuous_shadow_proof'].update(minimum_raw_m=s['admission']['continuous_shadow_proof']['minimum_raw_m']+.1))]:
   bad=copy.deepcopy(b['initial']);mutate(bad)
   try:verify_source(x,table,origin,so,0,bad,ref,min(end-5,time.monotonic()+30))
   except AssertionError as exc:negatives.append(dict(case=name,rejected=True,reason=str(exc)))
   else:raise AssertionError('BAD_ADMISSION_RECORD_ACCEPTED '+name)
 except BaseException as exc:
  error=dict(error=repr(exc),traceback=traceback.format_exc(),partial_analytical_counts_unknown=True);q.dump(O/'GOAL_INTEGRATION_ERROR.json',error)
 finally:
  signal.setitimer(signal.ITIMER_REAL,0)
  result=dict(closed=True,passed=len(results)==3 and len(negatives)==4 and error is None,cases=results,negatives=negatives,error=error,wall_s=time.monotonic()-start,source_unchanged=all(q.sha(R/n)==h for n,h in frozen.items()),models=0,new_mujoco_native=0,scope='analytical interface only; unchanged core + new independent C++ admission audits, no actual vehicle')
  q.dump(O/'GOAL_INTEGRATION_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()

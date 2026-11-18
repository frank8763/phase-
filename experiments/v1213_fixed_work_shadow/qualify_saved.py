"""Fixed saved-handoff regression and independent C++ feedback/shadow readback."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('SOFTWARE_QUALIFICATION_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1213_fixed_work_shadow/FIXED_QUALIFICATION'
from current_goal_source import q,np,generate
from admission import preview,check_arrays
from connection import endpoint
import copy,json,time,fcntl,signal,traceback

def read(p):return json.loads(p.read_text())
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();deadline=start+600
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert q.sha(R/'REVIEW_PENDING')==q.GUARD
 files={}
 for p in [*C.glob('*.py'),C/'PROTOCOL.md']:
  files[str(p.relative_to(R))]=q.sha(p)
 for module in list(sys.modules.values()):
  p=getattr(module,'__file__',None)
  if p and Path(p).resolve().is_relative_to(R)and Path(p).suffix=='.py':files[str(Path(p).resolve().relative_to(R))]=q.sha(Path(p))
 cases=[('original_WE','v1210','main_WEST_EAST'),('slot01','v1209','main_slot01'),('slot02','v1209','main_slot02')]
 loaded=[]
 for name,version,task in cases:
  p=R/'runs/v858_nav2_verified'/version/task;g=p/'CURRENT_GOAL_ENTRY';x=read(p/'LIVE_GOAL_INPUT.json');h=read(g/'HANDOFF_PACKET.json');offset=h['native_offset'];origin=h['origin']
  with np.load(p/'LIVE_GOAL_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
  with np.load(g/'EXECUTED.npz')as z:trace={k:z[k].copy()for k in z.files}
  loaded.append((name,p,g,x,table,h,trace))
  for f in [p/'LIVE_GOAL_INPUT.json',p/'LIVE_GOAL_TABLE.npz',g/'HANDOFF_PACKET.json',g/'EXECUTED.npz',g/'ONWARD_SELECTION.json',g/'ONWARD_REFERENCE.npz']:files[str(f.relative_to(R))]=q.sha(f)
 q.dump(C/'SOURCE_FREEZE.json',dict(files=files,cases=cases,software_only=True))
 q.dump(O/'ROUND_WINDOW.json',dict(software_only=True,models_authorized=False,started_unix=time.time(),hard_stop_monotonic=deadline,wall_cap_s=600))
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SOFTWARE_QUALIFICATION600')));signal.setitimer(signal.ITIMER_REAL,600)
 results=[];error=None;cpp_total=py_total=0
 try:
  for name,p,g,x,table,h,trace in loaded:
   out=O/name;out.mkdir();offset=h['native_offset'];origin=h['origin'];initial=dict(q.initial(x['packet']),steering_load_episode=True)
   engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);ss,uu,mm=engine.simulate(initial,[q.accelerator.row(float(v),float(w))for v,w,_ in trace['requests'][:offset]])
   err=float(abs(ss-trace['shadow'][:offset+1]).max());assert err<=1e-8;so=endpoint(initial,ss,mm,True)
   if name=='original_WE':
    with np.load(g/'ONWARD_REFERENCE.npz')as z:target=z['states'][-1,:3].copy()
    red=check_arrays(x,table,origin,offset,trace['states'][offset:],trace['controls'][offset:],trace['memory'][offset:],trace['requests'][offset:],trace['shadow'][offset:],target)
    assert not red['passed']and red['feedback_proof']['passed']and not red['continuous_shadow_proof']['passed'];q.dump(out/'RED_ORIGINAL.json',red)
   plan=generate(x,table,origin,offset,min(deadline-10,time.monotonic()+130),onward_only=True,shadow_origin=so)
   cpp_total+=plan['analytical_cpp_native'];py_total+=plan['admission_python_native']
   q.dump(out/'SELECTION.json',{k:v for k,v in plan.items()if k not in['states','controls','memory']})
   assert plan['passed'],'NO_ADMISSIBLE_SOURCE '+name
   np.savez_compressed(out/'REFERENCE.npz',**{k:plan[k]for k in['states','controls','memory']})
   proof,arrays=preview(x,table,origin,so,offset,plan,min(deadline-5,time.monotonic()+30));py_total+=proof['python_native'];assert proof['passed']
   np.savez_compressed(out/'PREVIEW.npz',**arrays);q.dump(out/'ADMISSION.json',proof)
   rows=[q.accelerator.row(float(v),float(w))for v,w,_ in arrays['requests']]
   cs,cu,cm=engine.simulate(origin,rows);ss,su,sm=engine.simulate(so,rows)
   error_max=max(float(abs(cs-arrays['states']).max()),float(abs(cu-arrays['controls']).max()),float(abs(cm-arrays['memory']).max()),float(abs(ss-arrays['shadow']).max()))
   assert error_max<=1e-8,'INDEPENDENT_CPP_FEEDBACK_SHADOW'
   cpp_total+=engine.native
   result=dict(case=name,passed=True,source_native=len(plan['controls']),complete_preview_native=proof['native'],feedback_raw=proof['feedback_proof']['minimum_raw_m'],shadow_raw=proof['continuous_shadow_proof']['minimum_raw_m'],feedback_terminal_raw=proof['feedback_proof']['terminal_cycle_raw_m'],shadow_terminal_raw=proof['continuous_shadow_proof']['terminal_cycle_raw_m'],independent_cpp_python_error=error_max,carried_shadow_prefix_error=err,shadow_memory_reset=False,models=0,new_mujoco_native=0)
   results.append(result);q.dump(O/'RESULTS.json',results)
  # Fail closed on missing shadow origin and expired candidate generation.
  name,p,g,x,table,h,t=loaded[0]
  try:generate(x,table,h['origin'],h['native_offset'],time.monotonic()+1,onward_only=True)
  except AssertionError as e:assert 'CONTINUOUS_SHADOW_ORIGIN_REQUIRED'in str(e)
  else:raise AssertionError('MISSING_SHADOW_ACCEPTED')
  expired=generate(x,table,h['origin'],h['native_offset'],time.monotonic()-1,onward_only=True,shadow_origin=so)
  assert not expired['passed']and expired['analytical_cpp_native']==0 and expired['admission_python_native']==0
 except BaseException as exc:
  error=dict(error=repr(exc),traceback=traceback.format_exc(),partial_analytical_counts_unknown=True);q.dump(O/'ERROR.json',error)
 finally:
  signal.setitimer(signal.ITIMER_REAL,0)
  summary=dict(closed=True,passed=len(results)==3 and error is None,cases=results,error=error,analytical_cpp_native_completed=cpp_total,analytical_python_native_completed=py_total,partial_counts_unknown=error is not None,models=0,new_mujoco_native=0,source_unchanged=all(q.sha(R/n)==h for n,h in files.items()),guard_original=q.sha(R/'REVIEW_PENDING')==q.GUARD,wall_s=time.monotonic()-start,scope='saved actual handoffs; future analytical feedback/shadow only, not new physical arrival')
  q.dump(O/'COMPLETION.json',summary);print(json.dumps(summary))
if __name__=='__main__':main()

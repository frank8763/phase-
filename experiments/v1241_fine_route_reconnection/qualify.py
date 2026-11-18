"""Saved actual full-state executor, independently audited; zero vehicle models."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_VEHICLE_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import json,time,importlib.util,copy,fcntl,os,traceback
from package_loader import get_goal_entry
e=get_goal_entry();q=e.q;np=e.np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def main(case):
 os.sched_setaffinity(0,{2});os.sched_setscheduler(0,os.SCHED_IDLE,os.sched_param(0))
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 mapping=dict(slot12=('v1237/main_slot12','LIVE_GOAL'),slot10=('v1230/main_slot10','LIVE_GOAL'),slot09=('v1230/main_slot09','LIVE_GOAL'),oldNS=('v1220/regression_main_NORTH_SOUTH','ROUTE'))
 folder,kind=mapping[case];raw=R/'runs/v858_nav2_verified'/folder;x=read(raw/('ROUTE_RECOVERY_INPUT.json'if kind=='ROUTE'else'LIVE_GOAL_INPUT.json'))
 with np.load(raw/('ROUTE_JOINT_TABLE.npz'if kind=='ROUTE'else'LIVE_GOAL_TABLE.npz'))as z:table={k:z[k].copy()for k in z.files}
 helper=load('v1241_analytical_interface',R/'experiments/v1203_goal_entry_handoff/qualify_entry.py');v=helper.AnalyticalInterface(x)
 out=O/('ENTRY_'+case);out.mkdir();start=time.monotonic()
 try:
  answer=e.execute(v,x['setup'],x,table,time.monotonic()+420,lambda:True,lambda v:v.packet(),lambda p:q.dump(out/'PROGRESS.json',p),out)
  core=load('v1241_independent_core',R/'experiments/v1204_goal_audit_worker/audit_goal.py');bundle=core.load_bundle(out);base=core.verify(x,table,bundle,False)
  admission=load('v1241_independent_admission',R/'experiments/v1227_terminal_contract_capture/audit_admission.py').verify_bundle(x,table,bundle,time.monotonic()+100)
  terminal=load('v1241_terminal',R/'experiments/v1227_terminal_contract_capture/audit_terminal.py')
  rec=read(out/'TERMINAL_PREVIEW.json');trace=bundle['trace'];offset=rec['offset']
  org=dict(rec['origin'],state=trace['states'][offset],last_ctrl=trace['memory'][offset,:4],integral=trace['memory'][offset,4])
  eng=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);initial=dict(q.initial(x['packet']),steering_load_episode=False)
  sh,_,mm=eng.simulate(initial,[q.accelerator.row(float(a),float(b))for a,b,_ in trace['requests'][:offset]])
  so=dict(rec['shadow_origin'],state=sh[-1],last_ctrl=mm[-1,:4],integral=mm[-1,4])
  with np.load(out/'TERMINAL_PREVIEW.npz')as z:ta={k:z[k].copy()for k in z.files}
  term=terminal.verify(x,table,org,so,offset,bundle['initial_ref']['states'][-1,:3],rec,ta)
  unchanged=None
  if case!='slot12':
   old=R/'runs/v1234_retained_search_fallback'/('ENTRY_'+case+'_completed')
   for name in ['INITIAL_REFERENCE.npz','EXECUTED.npz','TERMINAL_PREVIEW.npz']:
    with np.load(out/name)as a,np.load(old/name)as b:
     assert set(a.files)==set(b.files)and all(np.array_equal(a[k],b[k])for k in a.files),'ORIGINAL_SUCCESS_ARRAY_CHANGED'
   unchanged=True
  result=dict(passed=True,case=case,models=0,physical_native=0,native=answer['native'],feedback_raw=answer['proof']['minimum_raw_m'],shadow_raw=answer['shadow_proof']['minimum_raw_m'],goal_upper_m=answer['proof']['goal_upper_m'],core_audit=base,admission_audit=admission,terminal_audit=term,old_success_arrays_exact=unchanged,
   analytical_cpp_native=answer['analytical_cpp_native']+base['analytical_cpp_native']+admission['analytical_cpp_native']+eng.native+term['analytical_cpp_native'],analytical_python_native=2*answer['native']+answer['admission_python_native'],wall_s=time.monotonic()-start)
  q.dump(O/('QUALIFICATION_'+case+'.json'),result);print(json.dumps({k:v for k,v in result.items()if k not in ['core_audit','admission_audit','terminal_audit']}))
 except BaseException as exc:
  q.dump(out/'ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),models=0,physical_native=0,analytical_inflight_unknown=True));raise
if __name__=='__main__':main(sys.argv[1])

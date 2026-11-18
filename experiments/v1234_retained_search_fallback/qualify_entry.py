"""Full actual new executor via analytical interface and independent audits."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import importlib.util,json,time,fcntl,copy,traceback
from package_loader import get_goal_entry
entry=get_goal_entry();q=entry.q;np=entry.np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def main(case):
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 mapping=dict(slot10=('v1230/main_slot10','LIVE_GOAL'),slot09=('v1230/main_slot09','LIVE_GOAL'),oldNS=('v1220/regression_main_NORTH_SOUTH','ROUTE'))
 folder,kind=mapping[case];raw=R/'runs/v858_nav2_verified'/folder
 x=read(raw/('ROUTE_RECOVERY_INPUT.json'if kind=='ROUTE'else'LIVE_GOAL_INPUT.json'))
 with np.load(raw/('ROUTE_JOINT_TABLE.npz'if kind=='ROUTE'else'LIVE_GOAL_TABLE.npz'))as z:table={k:z[k].copy()for k in z.files}
 helper=load('v1234_analytical_interface',R/'experiments/v1203_goal_entry_handoff/qualify_entry.py');v=helper.AnalyticalInterface(x);out=O/('ENTRY_'+case+'_completed');out.mkdir();start=time.monotonic()
 try:
  answer=entry.execute(v,x['setup'],x,table,time.monotonic()+180,lambda:True,lambda v:v.packet(),lambda p:q.dump(out/'PROGRESS.json',p),out)
  core=load('v1234_goal_core_auditor',R/'experiments/v1204_goal_audit_worker/audit_goal.py');bundle=core.load_bundle(out);base=core.verify(x,table,bundle,False)
  admission=load('v1234_independent_admission',R/'experiments/v1227_terminal_contract_capture/audit_admission.py').verify_bundle(x,table,bundle,time.monotonic()+100)
  negatives=[]
  for name,mutate in [('clock',lambda p:p.update(sim_time=p['sim_time']+.01)),('position',lambda p:p['body'].__setitem__(0,p['body'][0]+.01)),('lateral',lambda p:p.update(body_lateral=p['body_lateral']+.001)),('memory',lambda p:p['controller_memory']['last_ctrl'].__setitem__(0,p['controller_memory']['last_ctrl'][0]+.001))]:
   packet=copy.deepcopy(x['packet']);mutate(packet)
   try:entry.bind_current(x,packet,False)
   except AssertionError:negatives.append(name)
   else:raise AssertionError('STALE_CURRENT_STATE_ACCEPTED '+name)
  q.dump(out/'CORE_AUDIT.json',base);q.dump(out/'ADMISSION_AUDIT.json',admission)
  result=dict(passed=True,full_actual_executor=True,case=case,native=answer['native'],feedback_raw=answer['proof']['minimum_raw_m'],shadow_raw=answer['shadow_proof']['minimum_raw_m'],goal_upper_m=answer['proof']['goal_upper_m'],negative_cases=negatives,core_audit=base,admission_audit=admission,analytical_cpp_native=answer['analytical_cpp_native']+base['analytical_cpp_native']+admission['analytical_cpp_native'],analytical_python_native=2*answer['native']+answer['admission_python_native'],models=0,new_mujoco_native=0,wall_s=time.monotonic()-start)
  q.dump(O/('ENTRY_'+case+'_QUALIFICATION.json'),result);print(json.dumps({k:v for k,v in result.items()if k not in ['core_audit','admission_audit']}))
 except BaseException as e:q.dump(out/'ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,unfinished_analytical_unknown=True));raise
if __name__=='__main__':main(sys.argv[1])

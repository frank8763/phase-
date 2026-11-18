"""Finite analytical replay of the actual saved terminal branch; zero vehicles."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import importlib.util,json,copy,math,time,fcntl
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name/'TERMINAL_SAVED_COMPONENT_02';O.mkdir(exist_ok=False)
sys.path.insert(0,str(C));from package_loader import get_goal_entry
e=get_goal_entry();q=e.q;np=e.np
read=lambda p:json.loads(p.read_text())
def main():
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=R/'runs/v858_nav2_verified/v1225/repair_main_NORTH_SOUTH';g=p/'CURRENT_GOAL_ENTRY';x=read(p/'LIVE_GOAL_INPUT.json');setup=x['setup'];packet=copy.deepcopy(x['packet'])
 with np.load(g/'EXECUTED.npz')as z:old={k:z[k].copy()for k in z.files}
 with np.load(g/'INITIAL_REFERENCE.npz')as z:ref=z['states'].copy()
 with np.load(p/'physics/NATIVE_TRACE.npz')as z:trace={k:z[k].copy()for k in ['qpos','qvel']}
 with np.load(p/'LIVE_GOAL_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 n=len(ref)-1;k=x['packet']['native_tick']+n;state=old['states'][n];mem=old['memory'][n]
 packet.update(native_tick=k,sim_time=.01*k,body=[*state[:4],state[5]],body_lateral=state[4],controller_memory=dict(last_ctrl=mem[:4].tolist(),integral=float(mem[4])))
 packet['steering'].update(native_tick=k,position=trace['qpos'][k-1,setup['steering_qpos_addresses']].tolist(),velocity=trace['qvel'][k-1,setup['steering_qvel_addresses']].tolist())
 actual=dict(q.initial(packet),steering_load_episode=True);assert abs(actual['state']-state).max()<1e-8
 engine=q.accelerator.Engine(setup,q.model.parameters()['coefficients']);org=dict(q.initial(x['packet']),steering_load_episode=False)
 ss,uu,mm=engine.simulate(org,[q.accelerator.row(float(v),float(w))for v,w,_ in old['requests'][:n]])
 assert abs(ss[-1]-old['shadow'][n]).max()<1e-8
 shadow=dict(state=ss[-1],last_ctrl=mm[-1,:4],integral=mm[-1,4],coupled_episode=False,steering_motion_active=False,steering_load_episode=True)
 target=ref[-1,:3]
 terminal=e.terminal_preview(x,table,actual,shadow,n,target,time.monotonic()+30)
 record,arrays=terminal;q.dump(O/'RECORD.json',record);np.savez_compressed(O/'ARRAYS.npz',**arrays)
 spec=importlib.util.spec_from_file_location('v1227_independent_terminal',C/'audit_terminal.py');auditor=importlib.util.module_from_spec(spec);spec.loader.exec_module(auditor)
 audited=auditor.verify(x,table,actual,shadow,n,target,record,arrays)
 bad={k:v.copy()for k,v in arrays.items()};bad['controls'][0,0]+=.01
 try:auditor.verify(x,table,actual,shadow,n,target,record,bad)
 except AssertionError:pass
 else:raise AssertionError('TAMPERED_TERMINAL_CONTROL_ACCEPTED')
 audited.update(models=0,new_mujoco_native=0,real_saved_terminal_origin=True,continuous_shadow_not_reset=True,old_whole_prefix_still_refused=True,negative_control_rejected=True,analytical_python_native=record['python_native'])
 q.dump(O/'QUALIFICATION.json',audited);print(json.dumps(audited))
if __name__=='__main__':main()

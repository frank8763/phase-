"""Finite analytical replay of the actual saved terminal branch; zero vehicles."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import importlib.util,json,copy,math,time,fcntl
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name/'attempt02';O.mkdir(exist_ok=False)
sys.path.insert(0,str(R/'experiments/v1224_ns_current_source'));from package_loader import get_goal_entry
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
 target=ref[-1,:3];out=[]
 for name,limit in [('original_capture_12mm',.012),('existing_terminal_contract_25mm',.025)]:
  plant=q.model.Predictor(setup,copy.deepcopy(actual));sh=q.model.Predictor(setup,copy.deepcopy(shadow));states=[plant.state.copy()];shadows=[sh.state.copy()];ctrl=[];memory=[mem.copy()];requests=[];capture=0;reason=None;proof=sp=None;rawmax=np.zeros(2)
  def step(v,w):
   nonlocal rawmax
   s,u=plant.step(float(v),float(w),False);sp,_=sh.step(float(v),float(w),False)
   states.append(s.copy());shadows.append(sp.copy());ctrl.append(u.copy());memory.append(np.r_[plant.adapter.last,plant.adapter.integral]);requests.append([v,w,0.])
   d=s[:3]-target
   pe=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2])))]);rawmax=np.maximum(rawmax,pe)
   assert(pe<=[.04,.035]).all(),'ACTUAL_REFERENCE_REFUSED'
  try:
   for _ in range(600):
    if np.linalg.norm(plant.state[:2]-target[:2])<=limit:break
    v,w,status=q.capture.request(plant.state,target);assert status=='CAPTURING',status;step(v,w);capture+=1
   else:raise AssertionError('CAPTURE_NATIVE_CAP')
   for _ in range(2200):step(0.,0.)
   combined={key:np.concatenate([old[key][:n+1 if key in ['states','shadow','memory']else n],np.asarray(value)[1:]if key in ['states','shadow','memory']else np.asarray(value)])for key,value in [('states',states),('shadow',shadows),('controls',ctrl),('memory',memory),('requests',requests)]}
   geom=q.Geometry(x,table);proof=q.proof(geom,x,combined['states'],combined['controls'],combined['requests'],combined['memory']);sp=q.proof(geom,x,combined['shadow'],combined['controls'],combined['requests'],combined['memory'])
   assert proof['passed']and sp['passed'],'COMPLETE_ACTUAL_AND_SHADOW_PROOF'
   assert np.linalg.norm(plant.state[:2]-target[:2])<=.025,'FINAL_TERMINAL_DISTANCE'
   np.savez_compressed(O/(name+'.npz'),**combined)
  except AssertionError as error:reason=str(error)
  result=dict(case=name,passed=reason is None,reason=reason,capture_native=capture,total_analytical_native=len(ctrl),maximum_pose_error_m_rad=rawmax,final_state=plant.state,final_distance_m=float(np.linalg.norm(plant.state[:2]-target[:2])),proof=proof,shadow_proof=sp)
  out.append(result);q.dump(O/(name+'.json'),result)
 assert out[0]['reason']=='ACTUAL_REFERENCE_REFUSED','ORIGINAL_BUG_NOT_REPRODUCED'
 assert out[1]['passed'],'REPAIR_NOT_QUALIFIED'
 result=dict(passed=True,original_failure_reproduced=True,original_all_safety_terminal_gates_unchanged=True,actual_saved_terminal_packet=packet,origin=actual,continuous_shadow_origin=shadow,results=out,analytical_cpp_native=engine.native,analytical_python_native=sum(t['total_analytical_native']for t in out)*2,models=0,new_mujoco_native=0)
 q.dump(O/'REPRODUCTION.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['actual_saved_terminal_packet','origin','continuous_shadow_origin','results']}))
if __name__=='__main__':main()

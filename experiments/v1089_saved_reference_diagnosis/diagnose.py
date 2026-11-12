"""Bounded exact saved-root planning reproduction, no physics/model allowed."""
import sys,json,time,signal,traceback,copy,importlib.abc,math,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1089_saved_reference_diagnosis';P=R/'runs/v858_nav2_verified/v1089/main_west_east';CORE=R/'experiments/rpccr_execution_core'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL_SAVED_DIAGNOSIS '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(CORE))
import numpy as np
from prediction import Predictor,initial
from kernel import PARAMETERS
from braking_reserve import signed
import live_reference as live
def main():
 assert not(O/'CLAIM.json').exists();(O/'CLAIM.json').write_text(json.dumps(dict(started_unix=time.time(),models=0,integrations=0,wall_limit_s=120,unchanged_static_search_expansions=5000))+'\n')
 def halt(*_):raise TimeoutError('BOUNDED_SAVED_REFERENCE_DIAGNOSIS')
 signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,120);start=time.monotonic()
 try:
  setup=json.loads((P/'physics/SETUP.json').read_text());meta=json.loads((P/'INITIAL_METADATA.json').read_text());cmd=np.array(json.loads((P/'physics/BODY_COMMANDS.json').read_text()));engine=Predictor(setup,initial(meta['packet']),PARAMETERS);engine.adapter.__class__=signed.Adapter;engine.adapter.last=np.zeros(4);engine.adapter.integral=0.;error=0.
  with np.load(P/'physics/NATIVE_TRACE.npz')as trace:
   for c,u in zip(cmd,trace['ctrl'][:,setup['actuator_ids']]):error=max(error,float(abs(engine.adapter.compute(*c[[1,2,3,4,5]])-u).max()))
   assert error<=1e-10;n=len(cmd);q=trace['qpos'][-1];v=trace['qvel'][-1];a=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));packet=copy.deepcopy(meta['packet']);packet.update(body=[float(q[0]),float(q[1]),a,float(v[0]*math.cos(a)+v[1]*math.sin(a)),float(v[5])],native_tick=n,sim_time=float(trace['time'][-1]),dynamic_discovered=True,body_measured_at=0.,sent_at=0.,speed_episode=False);packet['steering'].update(position=q[setup['steering_qpos_addresses']].tolist(),velocity=v[setup['steering_qvel_addresses']].tolist(),native_tick=n,measured_at=0.);packet['controller_memory'].update(last_ctrl=engine.adapter.last.tolist(),integral=float(engine.adapter.integral))
  result=json.loads((P/'RESULT.json').read_text());assert n==result['recovery_origin_native']==20160 and np.max(abs(np.array(packet['body'])-result['physical']['final_body']))<=1e-8
  (O/'ACTUAL_SAVED_INPUT.json').write_text(json.dumps(dict(setup=setup,packet=packet,goal=setup['case']['goal_xy'],maximum_control_reconstruction_error=error),indent=2)+'\n')
  planner=live.static_planner(O);plan=planner.construct(setup,packet,None,setup['case']['goal_xy'],wall_s=30.,max_expansions=5000)
  full=bool(plan['passed']and plan.get('functional_goal_source',False));summary={k:v for k,v in plan.items()if k not in ['state_path','predicted_actuator_controls','planned_body_requests']};answer=dict(closed=True,diagnosis_complete=True,old_failure_reproduced=not full,original_full_reference_gate_passed=full,root_native=n,actual_input_and_ctrl_reconstructed=True,maximum_control_reconstruction_error=error,unchanged_original_static_search=summary,models=0,integrations=0,no_model_restart=True,wall_s=time.monotonic()-start)
 except BaseException as e:answer=dict(closed=True,diagnosis_complete=False,error=repr(e),traceback=traceback.format_exc(),models=0,integrations=0,no_model_restart=True)
 finally:signal.setitimer(signal.ITIMER_REAL,0)
 (O/'COMPLETION.json').write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n');print(json.dumps(answer),flush=True)
if __name__=='__main__':main()

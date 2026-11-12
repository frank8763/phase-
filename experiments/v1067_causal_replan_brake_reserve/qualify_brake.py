"""Replay saved metadata, never integrate a model or issue actuator commands."""
import importlib.abc,sys,json,math,time
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL_ONLY '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C));from brake_reserve import Reserve
raw=R/'runs/v858_nav2_verified/v1065/A_main_east_west';setup=json.loads((raw/'physics/SETUP.json').read_text());z=dict(np.load(raw/'physics/NATIVE_TRACE.npz'));commands=np.asarray(json.loads((raw/'physics/BODY_COMMANDS.json').read_text()));p=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);memories=[np.zeros(5)]
for row in commands:p.adapter.compute(row[1],row[2],row[3],row[4],row[5]);memories.append(np.r_[p.adapter.last,p.adapter.integral])
meta=json.loads((raw/'INITIAL_METADATA.json').read_text());reserve=Reserve(setup)
def packet(n):
 if not n:return meta['packet']
 q=z['qpos'][n-1];v=z['qvel'][n-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));now=time.monotonic();return dict(body=[q[0],q[1],yaw,v[0]*math.cos(yaw)+v[1]*math.sin(yaw),v[5]],native_tick=n,sim_time=float(z['time'][n-1]),body_measured_at=now,sent_at=now,dynamic_discovered=False,steering=dict(position=q[setup['steering_qpos_addresses']].tolist(),velocity=v[setup['steering_qvel_addresses']].tolist(),native_tick=n,measured_at=now),controller_memory=dict(last_ctrl=memories[n][:4].tolist(),integral=float(memories[n][4])))
bad=packet(len(commands));origin=initial(bad);low=reserve.stop(origin['state'],np.r_[origin['last_ctrl'],origin['integral']]);saved=json.loads((R/'runs/v1066_actual_route_diagnosis/EW_BRAKE_REPRODUCTION.json').read_text());assert abs(low-saved['minimum_raw_m'])<=1e-10 and low<REQUIRED,'ORIGINAL_BAD_STOP_NOT_REPRODUCED'
first=None;count=0;begun=time.monotonic()
for n in range(0,len(commands)-5,5):
 pp=packet(n);proof=reserve.check(pp,commands[n:n+5][:,[1,2,5]]);count+=1
 if not proof['passed']:
  first=dict(native=n,packet=pp,proof=proof);break
assert first is not None and first['native']<14195 and first['proof']['current_stop_passed'],'PREEMPTIVE_STATIC_STOP_NOT_AVAILABLE'
# Independently regenerate the selected current stop with the original Python.
pp=first['packet'];engine=Predictor(setup,initial(pp),PARAMETERS);states=[engine.state.copy()];controls=[]
for _ in range(2200):s,u=engine.step(0.,0.,False);states.append(s);controls.append(u)
states=np.array(states);a,b=ref._old.Geometry(setup['known'],None).clearances(states[:,:3]);minimum=float(a.min());assert minimum>=REQUIRED and abs(minimum-first['proof']['current_stop_minimum_raw_m'])<=1e-10;assert abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03
dump(O/'EW_PREEMPTIVE_STOP_INPUT.json',dict(setup=setup,packet=pp,requests=[[0.,0.,False]]*2200,complete_state_path=states.tolist(),predicted_actuator_controls=np.array(controls).tolist(),models=0,integrations=0))
result=dict(passed=True,original_failure_retained=True,original_unsafe_prediction_rejected=True,original_static_raw_m=low,first_preemption_native=first['native'],old_discovery_native=14195,native_lead=14195-first['native'],current_full_2200_stop_raw_m=minimum,hard_gate_unchanged=REQUIRED,preview_checks=count,wall_s=time.monotonic()-begun,prototype_only_not_physical_validation=True,models=0,integrations=0);dump(O/'EW_BRAKE_RESERVE_QUALIFICATION.json',result);print(json.dumps(result),flush=True)

"""Read exact V974 saved states only; no model, prediction, controls or replay."""
import hashlib,importlib.abc,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];P=R/'runs/v858_nav2_verified/v974/main_we';O=R/'runs/v976_saved_recovery_diagnosis'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','torch','vehicle','factory','physical'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())
setup=json.loads((P/'physics/SETUP.json').read_text());rows=json.loads((P/'RECOVERY_CORRIDORS.json').read_text());native=json.loads((P/'RESULT.json').read_text())
with np.load(P/'physics/NATIVE_TRACE.npz')as f:
 q=f['qpos'];v=f['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));body=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
 enc=np.c_[q[:,setup['steering_qpos_addresses']],v[:,setup['steering_qvel_addresses']]]
sys.path.insert(0,str(R/'experiments/v968_rpp_closed_loop_night'))
from corridor_audit import tracking
reports=[]
for row in rows:
 p=row.get('proposal',{});item=dict(completed=row['passed'],proposal_status=p.get('status'),entry_tick=row['entry_packet']['native_tick'],proposal={k:value for k,value in p.items()if k not in ['path','certificate','search']},fault=row.get('fault',{}).get('error'))
 if row['passed']:
  path=p['path'];start=row['install_packet']['native_tick'];end=row['end_packet']['native_tick'];actual=body[start-1:end];metric=tracking(path,actual)
  k=math.atan2(math.sin(path[1][2]-path[0][2]),math.cos(path[1][2]-path[0][2]))/.1
  wheel=enc[start-1,:2];t=np.tan(wheel);measured=[t[0]/(.6+.27*t[0]),t[1]/(.6-.27*t[1])]
  item.update(install_tick=start,end_tick=end,tracking=metric,first_reference_curvature=k,actual_initial_wheel_angles=wheel.tolist(),actual_initial_curvatures=measured,initial_body=row['install_packet']['body'],final_body=row['end_packet']['body'],actual_segment_travel_m=float(np.linalg.norm(np.diff(actual[:,:2],axis=0),axis=1).sum()),goal_improvement_m=float(np.linalg.norm(actual[0,:2]-[4.,-2.])-np.linalg.norm(actual[-1,:2]-[4.,-2.])))
 reports.append(item)
travel=float(np.linalg.norm(np.diff(q[:,:2],axis=0),axis=1).sum());result=dict(models=0,integrations=0,new_predictions=0,new_controls=0,new_replay=0,original_failure_regraded=False,
    actual_native=native['actual_native'],own_control_replay_native=native['replay_native'],minimum_actual_clearance_m=native['minimum_actual_clearance_m'],bad_contacts=native['bad_contacts'],goal_distance_m=native['goal_distance_m'],actual_travel_m=travel,first_actor_detection=native['first_actor_detection'],actual_travel_after_detection_m=native['actual_travel_after_detection_m'],recoveries=reports,
    binding=json.loads((P/'physics/SELECTED_NATIVE_BINDING.json').read_text()),source_sha={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in[P/'RECOVERY_CORRIDORS.json',P/'RESULT.json',P/'physics/NATIVE_TRACE.npz']})
(O/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:value for k,value in result.items()if k not in ['source_sha','binding']},indent=2))

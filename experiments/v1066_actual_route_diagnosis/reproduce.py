"""Zero-model diagnosis of two actual V1065 stopping boundaries; never actuates."""
import importlib.abc,sys,json,gzip,time,math,traceback
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('DIAGNOSIS_ZERO_MODEL_ONLY '+name)
sys.meta_path.insert(0,NoModel())
R=Path(__file__).resolve().parents[2];C=R/'experiments/v1065_preflight_metadata_continuation';O=R/'runs/v1066_actual_route_diagnosis';sys.path.insert(0,str(C))
from kernel import *
O=R/'runs/v1066_actual_route_diagnosis'
pin_threads()
from fresh import finite_plan
from handoff import prepare
raw=R/'runs/v858_nav2_verified/v1065';report=dict(models=0,integrations=0,old_results_unchanged=True)
x=json.loads((raw/'A_main_north_south/refresh/epoch00/INPUT.json').read_text())
try:prepare(x['setup'],x['packet'],x['source'],x['goal'],x['actions'],x['elapsed'])
except AssertionError as e:
 tb=e.__traceback__
 while tb.tb_next:tb=tb.tb_next
 v=tb.tb_frame.f_locals;bounds=np.asarray(v['bounds']);static=np.asarray(v['static']);cross=np.asarray(v['cross']);j=int(np.argmax(bounds));lower=np.minimum(static,(np.asarray(v['body'])-np.asarray(v['support'])[j:j+len(cross)]-.1).max(axis=1));worst=int(np.argmin(lower));report['north_south']=dict(reproduced=True,error=str(e),required_raw_m=REQUIRED,best_any_launch_lower_m=float(bounds.max()),minimum_static_cross_m=float(static.min()),static_below_gate_native_count=int((static<REQUIRED).sum()),static_worst_cross_native=int(np.argmin(static)),best_launch_slot=j,goal_upper_m=float(v['upper']),cross_native=len(cross)-1,original_elapsed=x['elapsed'],original_source_native=x['source']['source_native_tick'],best_launch_worst_cross_native=worst,best_launch_worst_pose=cross[worst,:3].tolist(),best_launch_worst_time_phase_s=float((j+worst)*.01%(2*math.pi/.32)))
else:raise AssertionError('NS_ORIGINAL_FAILURE_NOT_REPRODUCED')
out=raw/'A_main_east_west';setup=json.loads((out/'physics/SETUP.json').read_text());z=dict(np.load(out/'physics/NATIVE_TRACE.npz'));commands=np.asarray(json.loads((out/'physics/BODY_COMMANDS.json').read_text()));predictor=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS)
for row in commands:predictor.adapter.compute(row[1],row[2],row[3],row[4],row[5])
q=z['qpos'][-1];v=z['qvel'][-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));now=time.monotonic();n=len(commands);p=dict(body=[q[0],q[1],yaw,v[0]*math.cos(yaw)+v[1]*math.sin(yaw),v[5]],native_tick=n,sim_time=float(z['time'][-1]),body_measured_at=now,sent_at=now,dynamic_discovered=True,steering=dict(position=q[setup['steering_qpos_addresses']].tolist(),velocity=v[setup['steering_qvel_addresses']].tolist(),native_tick=n,measured_at=now),controller_memory=dict(last_ctrl=predictor.adapter.last.tolist(),integral=float(predictor.adapter.integral)))
e=json.loads((out/'CAUSAL_EVIDENCE.json').read_text());norm=load('v1066_saved_public_support',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');support=norm.PeriodicSupport()
for row in e['periodic_constraints']:support.update(row['time'],row['native_tick'],row['support'])
source=dict(source_native_tick=n,source_age_s=0.,decision_at=now,periodic=support.snapshot());dump(O/'EW_SAVED_ACTUAL_INPUT.json',dict(setup=setup,packet=p,source=source,scope='ACTUAL_RECORDED_FIRST_DISCOVERY_STATE_RECONSTRUCTED_WITHOUT_MODEL'));plan=finite_plan(setup,p,source,np.zeros((2200,3)),'SAVED_ACTUAL_EW_DISCOVERY_BRAKE_REPRODUCTION');assert not plan['passed'],'EW_ORIGINAL_FAILURE_NOT_REPRODUCED';ss=np.array(plan['state_path']);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[:,:3]);report['east_west']=dict(reproduced=True,checks=plan['checks'],required_raw_m=REQUIRED,minimum_static_m=float(a.min()),minimum_dynamic_full_cycle_m=float(b.min()),minimum_raw_m=plan['minimum_raw_m'],initial_prediction_state=ss[0].tolist(),maximum_body_components=np.max(abs(ss[:,3:6]),axis=0).tolist(),first_discovery_native=n,complete328_stop_predicted=bool(abs(ss[328,3:6]).max()<=.03),actual_executed_braking_native=0)
dump(O/'EW_BRAKE_REPRODUCTION.json',plan);dump(O/'DIAGNOSIS.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))

"""Zero-model entry and historical-prefix qualification; never replays a plant."""
import ast,importlib.abc,sys,copy,time,json,math
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from fresh import finite_plan,actions_from_requests,choose_seed
from execute import ProcessJob
checks_={}
for name in ['worker','fresh','source_job','atomic','handoff','execute']:
 ast.parse((C/(name+'.py')).read_text());load('v1056_q_'+name,C/(name+'.py'))
checks_['actual_entry_modules_import_without_model']=True
assert ProcessJob.__init__.__globals__['C']==C;checks_['producer_namespace']=True
meta=json.loads((O/'WEST_EAST_T0_METADATA.json').read_text());static=json.loads((O/'WEST_EAST_STATIC_SOURCE.json').read_text());requests=np.array(static['plan']['planned_body_requests']);plan=finite_plan(meta['setup'],meta['packet'],None,requests,'QUALIFICATION_ONLY');assert plan['passed'];checks_['fresh_static_complete_profile_regenerated']=True
# Old actual trace is an offline held sample only. The online worker cannot
# access it, and it is never used as vehicle commands or state restoration.
h=R/'runs/v1047_day_relay_20261111/inputs/history/physics';z=dict(np.load(h/'NATIVE_TRACE.npz'));setup=json.loads((h/'SETUP.json').read_text());old=np.array(json.loads((h/'BODY_COMMANDS.json').read_text()));count=14540;assert np.array_equal(old[:count][:,[1,2,5]],requests[:count]);ss=np.array(plan['state_path'])[1:count+1];q=z['qpos'][:count];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));head=yaw-ss[:,2];steer=np.array([virtual(row)for row in q[:,setup['steering_qpos_addresses']]]);errors=[float(np.linalg.norm(q[:,:2]-ss[:,:2],axis=1).max()),float(abs(np.arctan2(np.sin(head),np.cos(head))).max()),float(abs(steer-ss[:,6]).max())];assert np.all(np.array(errors)<=np.array([.04,.035,.015]));checks_['offline_old_prefix_control_identity_and_all_three_tracking_gates']=True
worker=(C/'worker.py').read_text();assert all(s not in worker for s in ['NATIVE_TRACE.npz','BODY_COMMANDS.json','history_files','SELECTED_PLAN.json']);checks_['worker_has_no_historical_commands_or_state_restore']=True
# Check warm proposal from the established actual parked input, not a new MJB.
x=json.loads((R/'runs/v1055_atomic_publication_execution/INPUT_SOURCE.json').read_text());warm=json.loads((C/'RECOVERY_WARM_SEED.json').read_text())['actions'];seed=choose_seed(x['setup'],x['packet'],x['source'],x['goal'],requests,14540,4500,warm);assert seed['mode']=='STAGED_STRAIGHT';checks_['developed_warm_controls_endpoint_requalified']=True
ss,uu,rr,mm=predict(x['setup'],x['packet'],warm,tail=False);oldmod=load('v1056_prev_kernel',R/'experiments/v1055_atomic_publication_execution/kernel.py');a,b,c,d=oldmod.predict(x['setup'],x['packet'],warm,tail=False);assert all(np.array_equal(i,j)for i,j in [(ss,a),(uu,b),(rr,c),(mm,d)]);checks_['classic_predictor_and_controls_bitwise_V1055']=True
# Explicit-speed compression must preserve both curvature and every input.
actions=actions_from_requests(requests);a,b,rr,d=predict(meta['setup'],meta['packet'],actions,tail=False);assert np.max(abs(rr-requests))<1e-15;assert np.max(abs(a-np.array(plan['state_path'])))<1e-12;checks_['request_compression_roundtrip']=True
for case in ['WEST_EAST','NORTH_SOUTH','EAST_WEST']:
 xcase=json.loads((O/(case+'_STATIC_SOURCE.json')).read_text());assert bool(xcase['passed'])==(case!='EAST_WEST')
checks_['east_west_initial_rejection_kept']=True
# The first phase is explicitly WE fresh main/repeat. Other routes require
# further source qualification; no six-task physical gate is claimed.
checks_['fresh_component_not_three_route_acceptance']=True
result=dict(passed=True,checks=checks_,old_prefix_offline_max_errors=errors,models=0,integrations=0,metadata_proxy_not_new_mjb=True,physical_scope='WEST_EAST fresh t0 main and conditional complete repeat only',remaining_routes_not_ready=['NORTH_SOUTH dynamic handoff','EAST_WEST initial certificate']);dump(O/'ENTRY_QUALIFICATION.json',result);print(json.dumps(result))

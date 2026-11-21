"""New production event/source qualification only; no model or physical steps."""
import ast
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoPhysical(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('ORDERED_EVENT_NO_PHYSICAL_IMPORT:'+name)

def main():
 assert sys.argv[1:]==['--entry-check']and os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 assert not(O/'ENTRY_QUALIFICATION.json').exists();os.chdir(R);sys.meta_path.insert(0,NoPhysical());calls=[]
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:
   calls.append(frame.f_code.co_name);raise AssertionError('ORDERED_EVENT_ZERO_MODEL_CONSTRUCTOR_OR_STEP')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==5
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  session=exact('v1422_production_sessions',C/'session.py');owner=exact('v1422_production_owner',C/'event_owner.py');canonical=exact('v1422_production_canonical',C/'canonical_owner.py')
  assert Path(canonical.transaction_module.owner.OwnerRequest.__init__.__code__.co_filename).resolve()==C/'event_owner.py'
  import numpy as np
  io=exact('v1422_original_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');old=R/'runs/v1417_complete_timed_witness/model';current=json.loads((old/'CURRENT_INPUT.json').read_text());origin=current['origin'];body=origin['body'];tick=origin['native_tick'];now=time.monotonic();run_id='v1422_SOFTWARE_SOURCE_FIXTURE_NOT_ACTUAL';segment=current['next_segment']
  wire=dict(schema=1,run_id=run_id,sequence=0,sampled_at=now,body=body,ranges_m=[3.]*32,native_tick=tick,sim_time=origin['sim_time'],sensor_frame=dict(native_tick=tick,time=origin['sim_time'],xy=body[:2],yaw=body[2],sampled_at=now))
  v=SimpleNamespace(count=tick,d=SimpleNamespace(time=origin['sim_time'],qpos=np.asarray(body[:3]),qvel=np.asarray([body[3]*math.cos(body[2]),body[3]*math.sin(body[2]),0.,0.,0.,body[4]]),ctrl=np.zeros(4),mocap_pos=np.zeros((0,3)),mocap_quat=np.zeros((0,4))),adapter=SimpleNamespace(last=np.asarray(origin['controller_memory']['last_ctrl']),integral=origin['controller_memory']['integral'],parked_target=None,_steering_motion_active=False),commands=[[now,0.,0.,0.,0.,False]for _ in range(tick)],rows=[None]*tick,contacts=[None]*(tick+1),audit=SimpleNamespace(native_count=tick),bad=0)
  v.body=lambda:body;v.steering_sample=lambda:np.asarray([*origin['steering']['position'],*origin['steering']['velocity']])
  feedback=dict(native_tick=tick,sim_time=wire['sim_time'],body=body,encoders=v.steering_sample().tolist(),last_ctrl=v.adapter.last.tolist(),integral=v.adapter.integral,parked_target=None,steering_motion_active=False,gear_memory=current['gear_memory'])
  envelope=dict(kind='ROUTE_ACTUAL_FRAME',wire=wire,feedback=feedback,evidence_state_sha256=owner.measured_identity(v));tracker=SimpleNamespace(snapshot=lambda:copy.deepcopy(current['causal_snapshot']));geometry=current['event_geometry'];negatives=[]
  def reject(name,fn):
   try:fn()
   except (AssertionError,KeyError,ValueError):negatives.append(name)
   else:raise AssertionError('ORDERED_EVENT_NEGATIVE_ACCEPTED:'+name)
  def make(*,kind='ORDERED_ROUTE_FIRST_SEGMENT_CHECK',brake=None,prior=1,segments=None):
   return session.prepare_request(envelope,segment,geometry,tracker,run_id=run_id,event_index=1,brake_start=tick-200 if brake is None else brake,now=now,event_kind=kind,plan_index=1,ordered_segments=[segment]if segments is None else segments,completed_bridge_events=prior)
  packet=make();assert packet['request']['event']['kind']=='ORDERED_ROUTE_FIRST_SEGMENT_CHECK'and session.event.validate_request(packet['request'])==200
  reject('ordered199',lambda:make(brake=tick-199));reject('ordered_without_prior_completed_bridge',lambda:make(prior=0));reject('ordered_wrong_first_segment',lambda:make(segments=[dict(segment,gear=1)]));reject('cusp249_unchanged',lambda:make(kind='CUSP_NEXT_SEGMENT_CHECK',brake=tick-249))
  cusp=make(kind='CUSP_NEXT_SEGMENT_CHECK',brake=tick-250);assert session.event.validate_request(cusp['request'])==250
  assert owner.stop_evidence(v,packet['request'])['required_native']==200
  v.commands[-1][1]=.1;reject('nonzero_applied_stop_tail',lambda:owner.stop_evidence(v,packet['request']));v.commands[-1][1]=0.
  wrong=copy.deepcopy(packet);wrong['request']['stop_requirement_native']=199;reject('tampered_event_stop_requirement',lambda:session.Session(wrong))
  folder=O/'owner_fixture';folder.mkdir();(folder/'cusp_requests').mkdir();path=folder/'cusp_requests/event0001.json';io.atomic(path,packet)
  notice=dict(kind='BRIDGE_CERTIFICATE_REQUEST_FILE',run_id=run_id,event_index=1,request_sha256=packet['request']['request_sha256'],path=str(path.relative_to(R)),file_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
  modes=SimpleNamespace(snapshot=lambda count:copy.deepcopy(current['mode_history']));gear=SimpleNamespace(**current['gear_memory'])
  bound=owner.OwnerRequest(notice,output=folder,vehicle=v,mode_memory=modes,gear=gear,run_id=run_id,last_event_index=0,now=time.monotonic())
  assert bound.current['stop_evidence']['required_native']==200 and bound.current['geometry_kind']==current['geometry_kind']and bound.current['method_spec']==current['method_spec']
  assert bound.current['causal_snapshot_sha256']==current['causal_snapshot_sha256']
  assert not calls
  io.atomic(O/'OWNER_CURRENT_BINDING.json',dict(passed=True,models=0,fixture_not_actual_sensor_or_plant=True,current_input_sha256=bound.current['input_sha256'],event_kind=packet['request']['event']['kind'],method=bound.current['method_spec'],stop_evidence=bound.current['stop_evidence']))
  result=dict(passed=True,models=0,analytical_native=0,physical_native=0,scientific_revision=5,actual_cpu=[2],original_writeguard=True,constructor_step_profile_guard=True,fixture_not_actual_sensor_or_plant=True,ordered200_and_original_cusp250_distinct=True,full_current_snapshot_method_owner_binding_pass=True,negative_cases=negatives,actual_execution_unexecuted=True,physical_admission=False,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*')if p.is_file()})
  io.atomic(O/'ENTRY_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()

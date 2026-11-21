"""Single pure mathematical/source qualification, no actual or model execution."""
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
import signal
import sys
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def save(p,v):
 raw=json.dumps(v,indent=2,allow_nan=False)+'\n';assert len(raw.encode())<=2*1024**2
 t=p.with_suffix(p.suffix+'.pending');t.write_text(raw);t.replace(p)
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','jax','jaxlib','torch','rclpy','vehicle','factory'}:raise AssertionError('PRIEST_MATH_ONLY_FORBIDDEN_IMPORT:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[4]and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 claim=O/'MATH_ENTRY_ONCE_CLAIM.json'
 with claim.open('x')as f:json.dump(dict(started_unix=time.time(),scope='PURE_MATH_SOURCE_ONLY',models=0),f)
 start=time.monotonic();end=min(start+90,start+1795395600-time.time())
 def limit(*_):raise TimeoutError('PRIEST_MATH_SOURCE_90S_OR_ROOT')
 signal.signal(signal.SIGALRM,limit);signal.setitimer(signal.ITIMER_REAL,max(.01,end-start))
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def profile(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','coupled_control.py','vehicle_control.py','kernel.py'}and frame.f_code.co_name in {'__init__','step','compute'}:raise AssertionError('PRIEST_MATH_ONLY_MODEL_OR_ALLOCATOR_CALL')
 sys.setprofile(profile)
 result=dict(passed=False,closed=False,scope='PURE_MATH_SOURCE_AND_SOFTWARE_INTERFACE_ONLY',software_fixture_not_actual=True,models=0,physical_native=0,optimizer_calls=0,Allocator_recomputations=0,ownreplay_native=0,author_modules_imported=False,actual_positive_capture_unexecuted=True,model_response_unexecuted=True,whole_route_passed=False)
 negatives=[];completed=[];sources={}
 def rejected(label,fn):
  try:fn()
  except (AssertionError,RuntimeError,ValueError,FileNotFoundError):negatives.append(label);return
  raise AssertionError('PRIEST_MATH_NEGATIVE_ACCEPTED:'+label)
 try:
  parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent_before=parent_path.read_bytes();parent=json.loads(parent_before);assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==7
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   sources=json.loads((R/'runs/v1479_retirement_scope_binding/SOURCE_FREEZE.json').read_text())['files']
   for p in C.iterdir():
    if p.is_file():sources[str(p.relative_to(R))]=sha(p)
   cap=R/'runs/v1484_baseline_disposition_priest';acq=json.loads((cap/'ACQUISITION.json').read_text())
   for p in [cap/'ACQUISITION.json',cap/'TREE.json',*(cap/'upstream'/row['path']for row in acq['records']if 'path'in row)]:sources[str(p.relative_to(R))]=sha(p)
   identity=exact('v1485_math_identity',C/'core_identity.py');prepared=identity.PreparedCore(source_manifest=sources);assert prepared.hot_identity()==digest(prepared.value);prepared.verify_closure_sources();completed.append('real_prepared_source_core_map_identity')
   poly=exact('v1485_math_polynomial',C/'polynomial.py');boundary=exact('v1485_math_causal_boundary',C/'causal_boundary.py');output=exact('v1485_math_output',C/'candidate_output.py');policy=exact('v1485_math_same_policy',C/'response_policy.py');capture=exact('v1485_math_current_capture',C/'current_input.py')
   linear=[.1*i for i in range(11)];quad=[(i*(i-1))/(10*9)for i in range(11)]
   for t in [0.,.25,2.,7.,10.]:
    x,v,a=poly.evaluate(linear,t,10.);assert max(abs(x-.1*t),abs(v-.1),abs(a))<1e-12
    y,vy,ay=poly.evaluate(quad,t,10.);assert max(abs(y-(t/10)**2),abs(vy-.02*t),abs(ay-.02))<1e-12
   assert poly.sample([0.]*11,[0.]*11,time_s=0.,gear=1)['tangent_heading_rad']is None
   assert abs(abs(poly.sample(linear,[0.]*11,time_s=1.,gear=-1)['tangent_heading_rad'])-math.pi)<1e-12;completed.append('independent_linear_quadratic_derivatives_reverse_singular')
   def state(t,vx=0.):return dict(time=t,qpos=[.3,0.,0.,1.,0.,0.,0.],qvel=[vx,0.,0.,0.,0.,0.],ctrl=[0.]*4,mocap_pos=[],mocap_quat=[])
   cold=boundary.initial_hint(state(0.),None,native_tick=0);assert cold['zero_substitution_used']and not cold['measured_instantaneous_acceleration']and cold['instantaneous_error_bound']is None
   secant=boundary.initial_hint(state(.02,.002),state(.01,.001),native_tick=2);assert abs(secant['acceleration_hint_world'][0]-.1)<1e-12 and secant['previous_native']==1
   rejected('future_previous_state',lambda:boundary.initial_hint(state(.02),state(.03),native_tick=2))
   assert boundary.initial_hint(state(.01,.01),None,native_tick=1)['acceleration_hint_world']is None;completed.append('causal_secant_and_explicit_canonical_rest_target')
   origin=dict(body=[.3,0.,0.,0.,0.],body_lateral=0.,native_tick=0,sim_time=0.,steering=dict(position=[0.,0.],velocity=[0.,0.]),controller_memory=dict(last_ctrl=[0.]*4,integral=0.),parked_target=None,steering_motion_active=False,coupled_episode=False)
   full=state(0.);hint=boundary.initial_hint(full,None,native_tick=0)
   current=dict(run_id='SOFTWARE_ONLY_NOT_ACTUAL',origin=origin,fullstate_sha256=digest(full),fixed_origin_native=0,fixed_origin_sim_time=0.,rear_pose_world=[0.,0.,0.],rear_velocity_world=[0.,0.],author_initial_boundary_hint=hint,core_identity_sha256=prepared.identity_sha256,core_identity=prepared.value,gear_memory=dict(gear=0,brake_start=None,last_tick=-1),next_segment=dict(gear=1,poses=[[0.,0.,0.],[1.,0.,0.]]));current['input_sha256']=digest(current)
   initial=capture.author_initial_state(current);assert initial['role']=='POLYNOMIAL_BOUNDARY_APPROXIMATION_ONLY'and not initial['instantaneous_actual_acceleration_is_known']
   # x=t^3/1000 has exact zero initial velocity/acceleration; this is a
   # mathematical output fixture, not a prior physical/model trajectory.
   cubic=[i*(i-1)*(i-2)/(10*9*8)for i in range(11)]
   reply=dict(kind='PRIEST_AUTHOR_POLYNOMIAL_PROPOSAL',schema=1,run_id=current['run_id'],input_sha256=current['input_sha256'],core_identity_sha256=current['core_identity_sha256'],origin_native=0,origin_sim_time=0.,horizon_s=10.,coordinate_frame='REAR_AXLE_WORLD_XY',gear=1,coefficients_x=cubic,coefficients_y=[0.]*11,optimizer_accounting=dict(optimizer_calls=None,iterations_completed=None,mathematical_candidate_evaluations=None,inflight_unknown=False,author_core_source_sha256=prepared.value['author_members'][0]['sha256']))
   proposal=output.bind(current,reply);assert output.reference_at(proposal,native_tick=1000)['sim_time']==10.
   bad=copy.deepcopy(reply);bad['input_sha256']='0'*64;rejected('changed_current_identity',lambda:output.bind(current,bad));bad=copy.deepcopy(reply);bad['coefficients_x'][0]=1.;rejected('wrong_initial_rear_position',lambda:output.bind(current,bad));completed.append('proposal_current_boundary_fixed_clock_binding')
   rejected('actual_capture_missing_authority',lambda:capture.capture(None,None,None,prepared=prepared,authority=dict(scope='PRIEST_CURRENT_POLYNOMIAL_INPUT',models_authorized=False),lock=lock,next_segment={}))
   rejected('actual_command_unqualified',lambda:output.actual_command(proposal))
   # Goal-near software rest enters exactly200 tail requests; each preview
   # proof is applied once on a separate pure original GearHandoff instance.
   near=copy.deepcopy(current);near['next_segment']['poses'][-1]=[.01,0.,0.];near.pop('input_sha256');near['input_sha256']=digest(near)
   r=copy.deepcopy(reply);r['input_sha256']=near['input_sha256'];p=output.bind(near,r);method=policy.Policy(near,p);gate=policy.gear_source.GearHandoff()
   for tick in range(200):
    packet=copy.deepcopy(origin);packet.update(native_tick=tick,sim_time=.01*tick)
    row=method.select(packet,source_kind='PRIVATE_CURRENT_RESPONSE_PACKET');assert row['phase']=='FINAL_TAIL'and row['raw_request']==[0.,0.,False]
    vr,wr,g=gate.select(*row['raw_request'][:2],native_tick=tick,body=packet['body'],last_ctrl=packet['controller_memory']['last_ctrl'],encoders=[0.]*4);assert [vr,wr,False]==row['expected_request_after_original_gear']
    after=copy.deepcopy(packet);after.update(native_tick=tick+1,sim_time=.01*(tick+1));method.observe_applied(before_native=tick,gear_handoff=g,gear_memory_after=dict(gear=gate.gear,brake_start=gate.brake_start,last_tick=gate.last_tick),after_packet=after)
   assert method.complete;completed.append('same_policy_exact200tail_and_original_gear_once_math_only')
   # New wrapper keeps the fixed polynomial clock while the unchanged gear
   # guard waits. No physical state is advanced by these software packets.
   rev=copy.deepcopy(current);rev['next_segment']=dict(gear=-1,poses=[[0.,0.,0.],[-1.,0.,0.]]);rev['gear_memory']=dict(gear=1,brake_start=None,last_tick=-1);rev.pop('input_sha256');rev['input_sha256']=digest(rev)
   rr=copy.deepcopy(reply);rr.update(input_sha256=rev['input_sha256'],gear=-1,coefficients_x=[-x for x in cubic]);rp=output.bind(rev,rr);method=policy.Policy(rev,rp);gate=policy.gear_source.GearHandoff();gate.gear=1;first_brake=None;released=None;last_raw=None
   for tick in range(500):
    packet=copy.deepcopy(origin);packet.update(native_tick=tick,sim_time=.01*tick)
    row=method.select(packet,source_kind='PRIVATE_CURRENT_RESPONSE_PACKET')
    if tick%5 and last_raw is not None:assert row['raw_request']==last_raw,'POLICY_5NATIVE_HOLD_CHANGED'
    last_raw=row['raw_request']
    vr,wr,g=gate.select(*row['raw_request'][:2],native_tick=tick,body=packet['body'],last_ctrl=packet['controller_memory']['last_ctrl'],encoders=[0.]*4)
    assert [vr,wr,False]==row['expected_request_after_original_gear']
    if g['brake_start']is not None and first_brake is None:first_brake=g['brake_start']
    after=copy.deepcopy(packet);after.update(native_tick=tick+1,sim_time=.01*(tick+1));method.observe_applied(before_native=tick,gear_handoff=g,gear_memory_after=dict(gear=gate.gear,brake_start=gate.brake_start,last_tick=gate.last_tick),after_packet=after)
    if g['released']:released=tick;break
   assert first_brake is not None and released-first_brake==200 and method.origin==0 and method.tail_start is None
   completed.append('new_wrapper_5native_hold_and200gear_release_without_clock_reset')
   rejected('twist_no_inplace_rotation',lambda:policy.contract.twist(0.,.01));rejected('twist_no_curvature_clipping',lambda:policy.contract.twist(.1,.1))
   assert parent_path.read_bytes()==parent_before
   result.update(passed=True,completed=completed,negative_cases=negatives,all_qualified_work_mathematical_or_source_only=True,source_unchanged=all(sha(R/p)==h for p,h in sources.items()))
 except BaseException as exc:result.update(first_error=repr(exc),traceback=traceback.format_exc(),completed=completed,negative_cases=negatives)
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);signal.setitimer(signal.ITIMER_REAL,0)
  result.update(closed=True,wall_s=time.monotonic()-start)
  save(O/'MATH_SOURCE_QUALIFICATION.json',result)
  if not sources:sources={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()}
  save(O/'SOURCE_FREEZE.json',dict(files=sources,entry_passed=result['passed'],scope='MATH_SOURCE_ONLY_NOT_NUMERICAL_RESPONSE_OR_ACTUAL',models=0,actual_positive_capture_qualified=False,physical_admission=False))
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())

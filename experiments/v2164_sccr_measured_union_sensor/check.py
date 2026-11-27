"""Three new saved-input union integrations, no replay/renderer/policy/physical audit."""
from pathlib import Path
import os,time,json,copy,sys,importlib.util,traceback,types
import numpy as np
from union import *
S=R/'runs'/Path(__file__).resolve().parent.name;OLD=R/'runs/v2144_sccr_depth_resource_units/components/SCCR/actual'
assert os.sched_getaffinity(0)=={0}and not(S/'RESULT.json').exists()
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def read(p):return json.loads(Path(p).read_bytes())
result=dict(passed=False,models=0,NLP=0,policy_deserializations=0,policy_inferences=0,actual_fresh_sensor_acquisitions=0,renderer_constructors=0,physics=0,replay=0,physical_audit=0,formal_tasks=0)
assembler=load('exact_186_assembly',R/'experiments/v2155_sccr_full_observation_assembly/assemble.py')
try:
 phase3=R/'runtime/mk-mini/training/envs/mkmini_real_indoor_phase3_depth_astar_sac_env.py';extract=functions(phase3,['_get_depth_features'],np)._get_depth_features
 known=read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json');setup=read(OLD/'physics/SETUP.json');assert setup['actor']['mocap_id']==0 and setup['actor']['radius_m']==.1
 original_shim=types.ModuleType(SHIM);prior=sys.modules.get(SHIM);sys.modules[SHIM]=original_shim;cases=[];inputs={}
 full=OLD/'FULL_STATE_NPLUS1.npz'
 with np.load(full)as arrays:mocap=arrays['mocap_pos'][[0,5,10]].copy()
 for index,k in enumerate([0,5,10]):
  origin=OLD/f'cycle_{index:06d}_origin.json';receipt=read(origin)['receipt'];p=receipt['packet'];assert p['native_tick']==k
  rawfile=OLD/f'SCCR_DEPTH_{k:06d}.npz'
  with np.load(rawfile)as arrays:raw=arrays['depth'].copy()
  calls=[]
  class SavedRenderer:
   def update_scene(self,*a,**kw):calls.append('update')
   def enable_depth_rendering(self):calls.append('enable')
   def render(self):calls.append('saved_frame');return raw.copy()
   def disable_depth_rendering(self):calls.append('disable')
  features=extract(SimpleNamespace(depth_camera_id=0,depth_feature_dim=24,depth_max_range=5.,renderer=SavedRenderer(),data=None,depth_camera_name='d435i_depth_camera'))
  assert calls==['update','enable','saved_frame','disable']
  saved=read(OLD/f'SCCR_DEPTH_{k:06d}.json');assert features.tolist()==saved['packet']['depth24']
  current=dict(native=k,sim_time=p['sim_time'],body=p['body'])
  world=dict(native=k,sim_time=p['sim_time'],bounds=[-5.,5.],rectangles=known['known_rectangles'],circles=known['known_circles']+[[float(mocap[index,0,0]),float(mocap[index,0,1]),.1]])
  route=dict(goal_xy=[4.,-2.],path_world=[[-4.,-2.],[-3.,-2.],[4.,-2.]],wp_index=1)
  packet=collect_saved_fixture(np,current,world,features,route,[0.,0.],proof=dict(saved_receipt_sha256=sha(origin),saved_depth_sha256=sha(rawfile),not_fresh_capture=True))
  assert sys.modules[SHIM]is original_shim
  obs,parts=assembler.build(np,packet,lambda a:np.array([0.,0.],np.float32),developer_fixture=True)
  assert obs.shape==(186,)and np.isfinite(obs).all()and parts['explicit_base_provider_calls']==1
  delivered=[consume_fixture(packet,name)for name in METHODS];assert all(digest(q)==digest(packet)for q in delivered)
  delivered[0]['core_lidar36_raw_m'][0]=0.;assert delivered[1]==packet
  cases.append(dict(native=k,complete186_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),sensor_packet_sha256=digest(packet),all_ten_equal=True,policy_provider_explicit_stub=True,original_ray_blocks=[36,32,15,32,15],ranges_m=[5.,3.,3.5,3.,3.],rendered_depth24_from_saved_actual=True))
  for file in [origin,rawfile,OLD/f'SCCR_DEPTH_{k:06d}.json']:inputs[str(file.relative_to(R))]=sha(file)
 negative=[]
 def reject(name,fn):
  try:fn()
  except(AssertionError,KeyError,ValueError):negative.append(name)
  else:raise AssertionError('UNION_NEGATIVE_ACCEPTED:'+name)
 reject('live_mode_before_qualification',lambda:collect_saved_fixture(np,current,world,features,route,[0.,0.],proof={},actual_mode=True))
 bad=copy.deepcopy(world);bad['native']+=5;reject('stale_private_geometry',lambda:collect_saved_fixture(np,current,bad,features,route,[0.,0.],proof={}))
 bad=copy.deepcopy(current);bad['sim_time']+=.001;reject('future_measured_time',lambda:collect_saved_fixture(np,bad,world,features,route,[0.,0.],proof={}))
 reject('short_depth_no_padding',lambda:collect_saved_fixture(np,current,world,features[:23],route,[0.,0.],proof={}))
 bad=dict(packet,actor_phase=1.);reject('private_truth_packet',lambda:consume_fixture(bad,'SCCR'))
 reject('foreign_method',lambda:consume_fixture(packet,'OTHER'))
 # A stale legacy origin must materially change this exact sensor/goal result.
 stale=copy.deepcopy(current);stale['body'][0]+=1.;changed=collect_saved_fixture(np,stale,world,features,route,[0.,0.],proof={})
 assert changed['core_lidar36_raw_m']!=packet['core_lidar36_raw_m'],'MEASURED_ORIGIN_NOT_USED'
 changed_obs,_=assembler.build(np,changed,lambda a:np.zeros(2,np.float32),developer_fixture=True);assert not np.array_equal(changed_obs,obs)
 try:
  with sensors(np):raise RuntimeError('forced_scope_exit')
 except RuntimeError:pass
 assert sys.modules[SHIM]is original_shim
 if prior is None:sys.modules.pop(SHIM,None)
 else:sys.modules[SHIM]=prior
 for p in [full,phase3,P6,P14,P7,P17,BASE,R/'experiments/v2155_sccr_full_observation_assembly/assemble.py',Path(__file__),Path(__file__).with_name('union.py')]:inputs[str(p.relative_to(R))]=sha(p)
 result.update(passed=True,closed=True,saved_actual_input_integrations=cases,negative_cases=negative,stale_origin_counterexample_detected=True,resident_module_restored_even_exception=True,actual_full_union_not_qualified=True,full_SCCR_not_qualified=True,policy_provider_is_fixture_only=True,private_geometry_excluded_from_consumer=True,all_ten_methods_same_sensors=True,input_and_source_SHA256=inputs,next='live private geometry/current receipt binding then two frozen policies/risk fusion under new source')
except BaseException as e:result.update(closed=True,error=repr(e),traceback=traceback.format_exc())
raw=json.dumps(result,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<128*1024;(S/'RESULT.json').write_bytes(raw);print(json.dumps({k:v for k,v in result.items()if k not in ['input_and_source_SHA256','saved_actual_input_integrations']}));raise SystemExit(0 if result['passed']else 1)

"""Independent C++ reconstruction of accepted feedback/shadow previews."""
from pathlib import Path
import copy,math,sys,time
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
from current_state_tools import q,np
sys.path.insert(0,str(R/'experiments/v1198_control_space_connection'))
import importlib.util
_spec=importlib.util.spec_from_file_location('phase_v1222_independent_connection',R/'experiments/v1198_control_space_connection/connection.py')
_connection=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=_connection;_spec.loader.exec_module(_connection)
endpoint=_connection.endpoint;OffsetGeometry=_connection.OffsetGeometry


def close(a,b,label):
 a=np.asarray(a);b=np.asarray(b)
 assert a.shape==b.shape and np.isfinite(a).all()and np.isfinite(b).all(),label+'_SHAPE'
 assert not a.size or float(abs(a-b).max())<=1e-8,label


def origin_equal(record,origin,label):
 for key in ['state','last_ctrl']:close(record[key],origin[key],label+'_'+key)
 assert abs(record['integral']-origin['integral'])<=1e-8,label+'_integral'
 assert record['steering_load_episode']is origin['steering_load_episode'],label+'_mode'
 assert not record.get('coupled_episode',False)and not record.get('steering_motion_active',False)


def verify_source(x,table,origin,shadow_origin,offset,selection,reference,deadline):
 record=selection['admission'];assert record['passed']and record['shadow_memory_reset']is False and record['offset']==offset,'ADMISSION_SCOPE_OR_CLOCK'
 origin_equal(record['origin'],origin,'ADMISSION_MEASURED_ORIGIN');origin_equal(record['shadow_origin'],shadow_origin,'ADMISSION_CONTINUOUS_SHADOW_ORIGIN')
 engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);current=copy.deepcopy(origin)
 states=[np.asarray(origin['state']).copy()];controls=[];memory=[np.r_[origin['last_ctrl'],origin['integral']]];requests=[];refmap=[]
 def step(v,w,ref):
  nonlocal current
  assert time.monotonic()<deadline,'INDEPENDENT_ADMISSION_AUDIT_DEADLINE'
  ss,uu,mm=engine.simulate(current,[q.accelerator.row(float(v),float(w))])
  states.append(ss[-1]);controls.append(uu[-1]);memory.append(mm[-1]);requests.append([float(v),float(w),0.]);refmap.append(ref)
  current=endpoint(current,ss,mm,v>=.005)
 i=0
 for target,speed,count,mode in selection['rows']:
  assert not mode and speed in[0.,.12]and type(count)is int and count>0
  for _ in range(count):
   if speed==0.:v=w=0.
   else:v,w,_=q.tracking.request(current['state'],reference[i],float(target),float(speed))
   step(v,w,reference[i+1]);i+=1
 assert i==len(reference)-1
 target=reference[-1,:3];capture=0
 if np.linalg.norm(current['state'][:2]-target[:2])>.025:
  for _ in range(600):
   v,w,status=q.capture.request(current['state'],target)
   if status=='CAPTURED':break
   assert status=='CAPTURING','INDEPENDENT_PREVIEW_CAPTURE'
   step(v,w,reference[-1]);capture+=1
  else:raise AssertionError('INDEPENDENT_CAPTURE_CAP')
 for _ in range(2200):step(0.,0.,reference[-1])
 states=np.asarray(states);controls=np.asarray(controls);memory=np.asarray(memory);requests=np.asarray(requests)
 shadow,_,_=engine.simulate(shadow_origin,[q.accelerator.row(float(v),float(w))for v,w,_ in requests])
 geometry=OffsetGeometry(q.Geometry(x,table),offset);local=copy.deepcopy(x);local['packet']['controller_memory']['last_ctrl']=np.asarray(origin['last_ctrl']).tolist()
 pp=q.proof(geometry,local,states,controls,requests,memory);sp=q.proof(geometry,local,shadow,controls,requests,memory)
 assert pp['passed']and sp['passed'],'INDEPENDENT_FEEDBACK_OR_SHADOW_PROOF'
 for recorded,rebuild in [(record['feedback_proof'],pp),(record['continuous_shadow_proof'],sp)]:
  assert recorded['passed']and recorded['checks']==rebuild['checks']
  for key in ['minimum_raw_m','terminal_cycle_raw_m','goal_upper_m']:assert abs(recorded[key]-rebuild[key])<=1e-8,'ADMISSION_PROOF_RECORD_'+key
 d=states-shadow;response=np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2]))),abs(d[:,6])]
 assert(response<=[.04,.035,.015]).all()
 # Executor starts monitoring after the first preview step, matching its saved maxima.
 close(record['maximum_response_error'],response[1:].max(0),'ADMISSION_RESPONSE_MAX')
 d=states[1:]-np.asarray(refmap);pose=np.c_[np.linalg.norm(d[:,:2],axis=1),abs(np.arctan2(np.sin(d[:,2]),np.cos(d[:,2])))];assert(pose<=[.04,.035]).all();close(record['maximum_reference_error'],pose.max(0),'ADMISSION_REFERENCE_MAX')
 assert record['native']==len(requests)and record['capture_native']==capture
 distance=float(np.linalg.norm(states[-1,:2]-target[:2]));angle=states[-1,2]-target[2];yaw=abs(math.atan2(math.sin(angle),math.cos(angle)))
 assert distance<=.025 and yaw<=.1
 assert abs(record['terminal_reference_distance_m']-distance)<=1e-8 and abs(record['terminal_reference_yaw_rad']-yaw)<=1e-8
 return dict(passed=True,native=len(requests),feedback_raw_m=pp['minimum_raw_m'],shadow_raw_m=sp['minimum_raw_m'],analytical_cpp_native=engine.native,models=0,new_mujoco_native=0,offset=offset)


def verify_bundle(x,table,b,deadline):
 origin=dict(q.initial(x['packet']),steering_load_episode=bool(b['result']['generations'][0]['origin']['steering_load_episode']))
 trace=b['trace'];engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);all_shadow,_,all_memory=engine.simulate(origin,[q.accelerator.row(float(v),float(w))for v,w,_ in trace['requests']]);close(all_shadow,trace['shadow'],'ADMISSION_ACTUAL_GLOBAL_SHADOW')
 results=[]
 for k,generation in enumerate(b['result']['generations']):
  offset=generation['offset'];selection=b['initial'if k==0 else'onward'];ref=b['initial_ref'if k==0 else'onward_ref']['states']
  so=dict(state=all_shadow[offset],last_ctrl=all_memory[offset,:4],integral=float(all_memory[offset,4]),coupled_episode=False,steering_motion_active=False,steering_load_episode=bool(generation['origin']['steering_load_episode']))
  results.append(verify_source(x,table,generation['origin'],so,offset,selection,ref,deadline))
 return dict(passed=True,generations=results,analytical_cpp_native=engine.native+sum(z['analytical_cpp_native']for z in results),models=0,new_mujoco_native=0)

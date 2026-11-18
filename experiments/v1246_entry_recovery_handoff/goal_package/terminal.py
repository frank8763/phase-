"""Preview the current measured terminal correction plus complete stop tail."""
import copy,math,time
from .candidate_search import q,np,PreviewGeometry

def preview(x,table,origin,shadow_origin,offset,target,deadline):
 plant=q.model.Predictor(x['setup'],copy.deepcopy(origin));shadow=q.model.Predictor(x['setup'],copy.deepcopy(shadow_origin))
 states=[plant.state.copy()];sh=[shadow.state.copy()];controls=[];memory=[np.r_[plant.adapter.last,plant.adapter.integral]];requests=[];capture=0
 maximum=np.zeros(3);posemax=np.zeros(2)
 def step(v,w):
  nonlocal maximum,posemax
  assert time.monotonic()<deadline,'TERMINAL_PREVIEW_DEADLINE'
  s,u=plant.step(float(v),float(w),False);sp,_=shadow.step(float(v),float(w),False)
  states.append(s.copy());sh.append(sp.copy());controls.append(u.copy());memory.append(np.r_[plant.adapter.last,plant.adapter.integral]);requests.append([float(v),float(w),0.])
  d=s-sp;response=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2]))),abs(d[6])]);maximum=np.maximum(maximum,response)
  d=s[:3]-target[:3];pose=np.array([np.linalg.norm(d[:2]),abs(math.atan2(math.sin(d[2]),math.cos(d[2])))]);posemax=np.maximum(posemax,pose)
  assert(response<=[.04,.035,.015]).all(),'TERMINAL_PREVIEW_RESPONSE'
  assert(pose<=[.04,.035]).all(),'TERMINAL_PREVIEW_REFERENCE'
 for _ in range(600):
  if np.linalg.norm(plant.state[:2]-target[:2])<=.025:break
  v,w,status=q.capture.request(plant.state,target);assert status=='CAPTURING','NO_FORWARD_TERMINAL_CAPTURE';step(v,w);capture+=1
 else:raise AssertionError('TERMINAL_PREVIEW_CAPTURE_CAP')
 for _ in range(2200):step(0.,0.)
 arrays={k:np.asarray(v)for k,v in dict(states=states,shadow=sh,controls=controls,memory=memory,requests=requests).items()}
 local=copy.deepcopy(x);local['packet']['controller_memory']['last_ctrl']=np.asarray(origin['last_ctrl']).tolist();geometry=PreviewGeometry(q.Geometry(x,table),offset)
 proof=q.proof(geometry,local,arrays['states'],arrays['controls'],arrays['requests'],arrays['memory']);sp=q.proof(geometry,local,arrays['shadow'],arrays['controls'],arrays['requests'],arrays['memory'])
 assert proof['passed']and sp['passed'],'TERMINAL_PREVIEW_COMPLETE_PROOF'
 assert np.linalg.norm(plant.state[:2]-target[:2])<=.025,'TERMINAL_PREVIEW_FINAL_POSITION'
 result=dict(passed=True,offset=offset,origin=origin,shadow_origin=shadow_origin,capture_native=capture,native=len(controls),python_native=2*len(controls),proof=proof,shadow_proof=sp,maximum_response_error=maximum,maximum_reference_error=posemax,terminal_position_contract_m=.025,extra_12mm_objective=False)
 return result,arrays

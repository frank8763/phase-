"""One coefficient on fixed first200 left samples; no vehicle/model imports."""
import importlib.abc,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1044_curvature_speed_prediction'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1043_speed_predictor_identification'))
from analyze import read,PARAMETERS,initial
sys.path.insert(0,str(C));from model import Predictor,virtual
s,p,plan,q,yaw,v,lat,u=read('left');delta=np.asarray([virtual(a)for a in q[:,s['steering_qpos_addresses']]]);prev=np.r_[p['body'][3],v[:-1]];feature=u[:200,2:].mean(axis=1)*(np.tan(delta[:200])/.6)**2;residual=v[:200]-PARAMETERS['speed_discrete'][0]*prev[:200]-PARAMETERS['speed_discrete'][1]*u[:200,2:].mean(axis=1);coef=float(feature@residual/(feature@feature));assert -.02<coef<0
parameters=dict(PARAMETERS,curvature_speed_coefficient=coef,curvature_speed_domain_m_s=.08,training_task='V1032_left_native_1_to_200',new_independent_response_qualified=False);rows={}
for task in ['straight','left']:
 setup,packet,plan,q,yaw,v,lat,u=read(task);engine=Predictor(setup,initial(packet),parameters);states=[];ctrl=[]
 for request in plan['planned_body_requests'][:len(q)]:a,b=engine.step(*request);states.append(a);ctrl.append(b)
 states=np.asarray(states);pos=np.linalg.norm(states[:,:2]-q[:,:2],axis=1);heading=abs(np.arctan2(np.sin(states[:,2]-yaw),np.cos(states[:,2]-yaw)));steer=np.asarray([virtual(a)for a in q[:,setup['steering_qpos_addresses']]]);err=abs(states[:,6]-steer);rows[task]=dict(native=len(q),maximum_position_m=float(pos.max()),maximum_heading_rad=float(heading.max()),maximum_steering_rad=float(err.max()),original_response_gates=bool(pos.max()<=.01 and heading.max()<=.008 and err.max()<=.015),new_physical_qualification=False)
(C/'PARAMETERS.json').write_text(json.dumps(parameters,indent=2)+'\n');out=dict(passed=all(r['original_response_gates']for r in rows.values()),models=0,integrations=0,coefficient=coef,results=rows,training_samples=200,independent_heldout_task=False,old_left_remainder_is_contiguous_holdout=True,old_failed_result_unchanged=True);(O/'SAVED_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

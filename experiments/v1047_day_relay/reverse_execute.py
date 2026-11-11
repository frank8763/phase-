"""Fixed reverse responses with the same physical prediction-error gates."""
import math,time
import numpy as np
from kernel import virtual

def execute(v,plan,end):
 states=np.asarray(plan['state_path']);requests=np.asarray(plan['planned_body_requests']);assert plan['passed']and states.shape==(701,8)and requests.shape==(700,3);assert np.all(requests[:500,0]==-.03)and np.all(requests[500:]==0.)and np.all(requests[:,2]==0.);assert np.max(abs(requests[:,1]))<=.03*.758770385+1e-10
 assert np.linalg.norm(np.asarray(v.body()[:3])-states[0,:3])<=1e-8;maximum=np.zeros(3);last=[]
 for i,request in enumerate(requests):
  assert time.time()<end-60,'ABSOLUTE_STOP_RESERVE';v.step(*request);b=np.asarray(v.body());d=b[2]-states[i+1,2];error=np.array([np.linalg.norm(b[:2]-states[i+1,:2]),abs(math.atan2(math.sin(d),math.cos(d))),abs(virtual(v.steering_sample()[:2])-states[i+1,6])]);maximum=np.maximum(maximum,error);assert abs(b[3])<=.13 and abs(b[4])<=.16,'BODY_CAP';assert np.all(error<=[.01,.008,.015]),'HELDOUT_NATIVE_RESPONSE_ERROR';last.append(b)
 assert np.linalg.norm(np.asarray(last[-50:])[:,3:5],axis=1).max()<=.03,'FULL_STOP_NOT_OBSERVED';distance=float(np.linalg.norm(np.asarray(v.body()[:2])-states[0,:2]));assert distance>=.10,'NO_REVERSE_RESPONSE'
 return dict(passed=True,native_steps=700,maximum_position_m=float(maximum[0]),maximum_heading_rad=float(maximum[1]),maximum_virtual_steering_rad=float(maximum[2]),actual_displacement_m=distance,full_200_stop=True)

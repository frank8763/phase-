"""Two-phase publication: allocate before snapshot, select an immutable view.

All geometry and control values are inherited from the unchanged qualified
proposal. State/control arrays stay read-only. Serialization is deferred until
parked and is absent from the publication-to-first-command path.
"""
from dataclasses import dataclass
import math,time
import numpy as np
from handoff import parked,source_check,contained,refresh_module,PERIOD,REQUIRED,virtual,MAX_HOLD
@dataclass(frozen=True)
class Buffers:
 proposal:dict
 prefix_states:np.ndarray
 prefix_controls:np.ndarray
 prefix_requests:np.ndarray
 wait_states:np.ndarray
 wait_controls:np.ndarray
 cross_states:np.ndarray
 cross_controls:np.ndarray
 cross_requests:np.ndarray
 launch_bounds:np.ndarray
 wait_candidates:np.ndarray
 planes:tuple
 checkpoint:int
def allocate(proposal):
 arrays=[np.asarray(proposal[k],float)for k in ['prefix_states','prefix_controls','prefix_requests','wait_states','wait_controls','cross_states','cross_controls','cross_requests','launch_bounds']];waits=np.arange(1,math.ceil(PERIOD/.01)+1)
 for value in [*arrays,waits]:value.setflags(write=False)
 checkpoint=None;tick=0;had_move=False
 for action in proposal['prefix']:
  tick+=action['ticks'];had_move=had_move or action['kind']=='move'
  if action['kind']=='wait'and action['ticks']>=200 and had_move:checkpoint=tick;break
 planes=[]
 for values in proposal['source_planes']:
  h=np.asarray(values,float);h.setflags(write=False);planes.append(h)
 assert len(arrays[0])==len(arrays[2])+1 and len(arrays[5])==len(arrays[7])+1
 return Buffers(proposal,*arrays,waits,tuple(planes),-1 if checkpoint is None else checkpoint)
@dataclass(frozen=True)
class Published:
 buffers:Buffers
 wait:int
 packet:dict
 source:dict
 age:float
 minimum:float
 @property
 def native_steps(self):return len(self.buffers.prefix_requests)+self.wait+len(self.buffers.cross_requests)
 @property
 def checkpoint(self):return self.native_steps if self.buffers.checkpoint<0 else self.buffers.checkpoint
 def request(self,index):
  assert 0<=index<self.native_steps
  n=len(self.buffers.prefix_requests)
  if index<n:return self.buffers.prefix_requests[index]
  if index<n+self.wait:return ZERO
  return self.buffers.cross_requests[index-n-self.wait]
 def state(self,index):
  assert 0<=index<=self.native_steps
  n=len(self.buffers.prefix_requests)
  if index<=n:return self.buffers.prefix_states[index]
  if index<=n+self.wait:return self.buffers.wait_states[index-n]
  return self.buffers.cross_states[index-n-self.wait]
 def record(self):
  p=self.buffers.proposal;n=len(self.buffers.prefix_requests);states=np.vstack([self.buffers.prefix_states,self.buffers.wait_states[1:self.wait+1],self.buffers.cross_states[1:]]);controls=np.vstack([self.buffers.prefix_controls,self.buffers.wait_controls[:self.wait],self.buffers.cross_controls]);requests=np.vstack([self.buffers.prefix_requests,np.zeros((self.wait,3)),self.buffers.cross_requests]);actions=p['prefix']+[dict(kind='wait',gear=0,target=0.,ticks=self.wait)]+p['suffix']
  return dict(passed=True,actions=actions,state_path=states.tolist(),predicted_actuator_controls=controls.tolist(),planned_body_requests=requests.tolist(),next_checkpoint_native=self.checkpoint,phase_wait_ticks=self.wait,minimum_raw_m=self.minimum,published_packet=self.packet,publication_age_s=self.age,publication_source=self.source,planning_packet=p['packet'],planning_source=p['source'],terminal_goal_upper_m=float(np.linalg.norm(states[-1,:2]-p['goal']))+.08,retained_suffix_audit=dict(passed=True,contract='PARKED_REFRESH_RETAINED_MOVING_SUFFIX',moving_fallback_not_brake_only=True),proposal_wall_s=p['wall_s'])
ZERO=np.zeros(3);ZERO.setflags(write=False)
def publish(buffers,packet,source,now):
 parked(packet);refresh_module.validate_measured_packet(packet,now);source_check(packet,source);base=buffers.proposal['packet'];assert 0<=packet['native_tick']-base['native_tick']<=MAX_HOLD,'PROPOSAL_EXPIRED'
 assert len(source['periodic']['vertices'])==len(buffers.planes),'SOURCE_DIMENSION'
 for vertices,plane in zip(source['periodic']['vertices'],buffers.planes):assert (np.asarray(vertices)@plane[:,:3].T-plane[:,3]).max()<=1e-8,'SOURCE_DOMAIN_EXPANDED'
 b=np.array(base['body']);q=np.array(packet['body']);d=q[2]-b[2];assert np.linalg.norm(q[:2]-b[:2])<=.001 and abs(math.atan2(math.sin(d),math.cos(d)))<=.001,'HOLD_POSE_DRIFT';assert abs(virtual(packet['steering']['position'])-virtual(base['steering']['position']))<=.001,'HOLD_STEERING_DRIFT';assert np.max(abs(np.array(packet['controller_memory']['last_ctrl'])-base['controller_memory']['last_ctrl']))<=1e-10,'HOLD_MEMORY_CHANGED'
 n=len(buffers.prefix_requests);phase=(packet['sim_time']+(n+buffers.wait_candidates)*.01)%PERIOD;indices=np.minimum((phase/.01).astype(int),len(buffers.launch_bounds)-1);bounds=buffers.launch_bounds[indices];choice=int(np.argmax(bounds));lower=float(bounds[choice]);assert lower>=REQUIRED+1e-7,'NO_CURRENT_LAUNCH_INTERVAL'
 return Published(buffers,int(buffers.wait_candidates[choice]),packet,source,now-packet['body_measured_at'],min(lower,buffers.proposal['minimum_prefix_raw_m']))

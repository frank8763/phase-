"""Finite constant-velocity observational support witness, no simulation."""
import gzip,hashlib,importlib.util,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
REPO=Path(__file__).resolve().parents[2];OWN=Path(__file__).parent
sys.path.insert(0,str(REPO/'experiments/v715_submaximum_free_certificate'))
from free_certificate import Certificate,SPEED
sys.path.insert(1,str(REPO/'experiments/v712_joint_field_continuation'))
from exact_footprint import pose_values
root=REPO/'runs/v716_observation_ambiguity';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
begun=time.time();window=dict(started_unix=begun,absolute_deadline_unix=begun+180,limit_s=180,round_closed=False)
write(root/'ROUND_WINDOW.json',window)
def stop(*_):raise TimeoutError('V716_180S_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,stop);signal.alarm(180);status='RUNNING'
try:
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});freeze=read(OWN/'SOURCE_FREEZE.json');assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
 pair=REPO/'runs/v712_joint_field_continuation/main01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json')
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
 last=packets[-1];T=last['time'];origin=np.array(protocol['start_qpos'][:2]);ego=np.array(last['xy']);yaw=last['yaw']
 offset=np.arange(-18,19)/10.;xx,yy=np.meshgrid(offset,offset,indexing='ij');centres=np.c_[xx.ravel(),yy.ravel()]+ego
 vaxis=np.arange(-4,5)*.03;vx,vy=np.meshgrid(vaxis,vaxis,indexing='ij');velocities=np.c_[vx.ravel(),vy.ravel()]
 pos=np.repeat(centres,len(velocities),axis=0);vel=np.tile(velocities,(len(centres),1));initial=pos-T*vel;final=pos+3.28*vel
 mask=(np.linalg.norm(initial-origin,axis=1)>=3.)&np.all((initial>=-4.9)&(initial<=4.9)&(final>=-4.9)&(final<=4.9),axis=1)
 # Necessary possible threat by distance to the two relative straight segments.
 direction=np.array([math.cos(yaw),math.sin(yaw)]);harm=np.full(len(pos),np.inf)
 for begin,end,ego_start,ego_velocity in [(0.,1.6,ego,direction*.30/1.6),(1.6,3.28,ego+.30*direction,np.zeros(2))]:
  relative=pos+begin*vel-ego_start;speed=vel-ego_velocity;duration=end-begin;den=np.sum(speed*speed,axis=1);tau=np.clip(-np.sum(relative*speed,axis=1)/np.maximum(den,1e-30),0,duration);harm=np.minimum(harm,np.linalg.norm(relative+tau[:,None]*speed,axis=1))
 mask &= harm<=math.hypot(.44,.375)+.10+.155
 pos,vel=pos[mask],vel[mask];generated=int(len(pos));history=[]
 for packet in packets:
  if not len(pos):break
  certificate=Certificate(packet,origin);past=pos+(packet['time']-T)*vel;lower=certificate.point_lower(past,np.full(len(pos),packet['time']));keep=lower<=0.
  pos,vel=pos[keep],vel[keep];history.append(dict(step=packet['step'],remaining=int(len(pos))));write(root/'ACTIVE.json',history[-1])
 # Whole-trajectory static clearance, with temporal interpolation remainder.
 times=np.linspace(0,T+3.28,math.ceil((T+3.28)/.05)+1);dt=float(times[1]-times[0]);physical=[]
 for i,(p,v)in enumerate(zip(pos,vel)):
  c=p+(times[:,None]-T)*v;clear=np.min(5.-abs(c),axis=1)
  for x,y,hx,hy in protocol['known_rectangles']:clear=np.minimum(clear,np.linalg.norm(np.maximum(abs(c-[x,y])-[hx,hy],0),axis=1))
  for x,y,r in protocol['known_circles']:clear=np.minimum(clear,np.linalg.norm(c-[x,y],axis=1)-r)
  if float(np.min(clear))-.5*dt*float(np.linalg.norm(v))>=.10:physical.append(i)
 pos,vel=pos[physical],vel[physical]
 # Frozen float32 known-map ray march precomputed once.
 spec=importlib.util.spec_from_file_location('v716_frozen_sensor',REPO/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py');sensor=importlib.util.module_from_spec(spec);spec.loader.exec_module(sensor)
 all_points=[];known_distances=[];observed=[];clips=[];sample_d=[];d=0.
 while d<=3.:sample_d.append(d);d+=.08
 sample_d=np.array(sample_d);known_compatible=True
 for packet in packets:
  angles=np.r_[np.arange(32)*2*np.pi/32,np.linspace(-np.deg2rad(35),np.deg2rad(35),15)]+packet['yaw'];env=SimpleNamespace(robot_xy=np.array(packet['xy'],np.float32),map_min=-5.,map_max=5.,rect_obstacles=np.asarray(protocol['known_rectangles'],np.float32),circle_obstacles=np.asarray(protocol['known_circles'],np.float32))
  known=np.array([sensor.ray_cast_distance(env,float(a),max_range=3.,step=.08)for a in angles]);z=np.r_[packet['lidar'],packet['depth']]*3.;b=np.r_[np.full(32,.06),np.full(15,.09)];directions=np.array([[math.cos(a),math.sin(a)]for a in angles],np.float32)
  points=env.robot_xy[None,None,:]+sample_d.astype(np.float32)[None,:,None]*directions[:,None,:]
  all_points.append(points.astype(float));known_distances.append(known);observed.append(z);clips.append(b);known_compatible &= bool(np.all((z==3.)|(np.abs(z-known)<=b+1e-5)))
 assert known_compatible,'FROZEN_KNOWN_RAW_SUPPORT_MISMATCH'
 points=np.array(all_points);known=np.array(known_distances);z=np.array(observed);b=np.array(clips);witness=None;tested=0
 field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.empty((0,4)),circles=np.empty((0,3)),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-100.,upper=100.))
 for p,v in zip(pos,vel):
  tested+=1;centers=np.array([p+(packet['time']-T)*v for packet in packets]).astype(np.float32).astype(float)
  hit=np.sum((points-centers[:,None,None,:])**2,axis=-1)<=float(np.float32(.10))**2
  first=np.where(hit.any(axis=2),sample_d[hit.argmax(axis=2)],3.);latent=np.minimum(known,first);compatible=(z==3.)|(np.abs(z-latent)<=b+1e-5)
  if not bool(compatible.all()):continue
  tau=np.arange(329)*.01;poses=np.repeat([[*ego,yaw]],329,axis=0);poses[:,:2]+=np.minimum(tau/1.6,1.)[:,None]*.30*direction;values=[]
  for pose,t in zip(poses,tau):field.circles=np.array([[*(p+t*v),.10]]);values.append(float(pose_values(field,[pose])[0]))
  if min(values)>=.155:continue
  witness=dict(position_at_last_frame=p.tolist(),velocity=v.tolist(),initial_position=(p-T*v).tolist(),minimum_fixed_future_body_clearance_m=min(values),minimum_clearance_time_s=float(tau[int(np.argmin(values))]),necessary_dropout_returns=int(np.sum((z==3.)&(latent+b<3.-1e-5))),all_nonmaximum_returns_within_original_clip=True,acceleration=0.,physical_known_geometry_continuous_margin_at_least_m=.10,scope='Tracker velocity/acceleration uncertainty class, not necessarily original sinusoidal amplitude-limited trajectory.')
  break
 status='COMPATIBLE_HARMFUL_AFFINE_WITNESS_FOUND'if witness else'NO_WITNESS_IN_LOCKED_AFFINE_FAMILY'
 result=dict(status=status,generated_initially_possible_threats=generated,history_filter=history,remaining_after_prefix=len(physical)if False else sum(x['remaining']for x in history[-1:]),physically_admissible_candidates=len(pos),exact_observation_tests=tested,known_only_observations_compatible=known_compatible,witness=witness,new_initializations=0,new_integrations=0,training_updates=0,interpretation='A witness proves support ambiguity for this fixed future interpolation under the declared tracker class; no witness only limits this finite affine family, not arbitrary trajectories or algorithms.')
 write(root/'RESULT.json',result)
except BaseException as error:
 status='STOPPED_EXCEPTION';write(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-begun);write(root/'ROUND_WINDOW.json',window);write(root/'COMPLETION.json',dict(status=status,round_closed=True,new_initializations=0,new_integrations=0));print(json.dumps(dict(status=status,elapsed_s=window['elapsed_s'])))

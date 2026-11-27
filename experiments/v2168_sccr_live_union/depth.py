"""Exact original feature extraction, explicit new live-camera binding, no policy."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,math,os,time
from context import R,C,O,SOURCE,read,sha,digest,load
ORIGINAL=R/'runtime/mk-mini/training/envs/mkmini_real_indoor_phase3_depth_astar_sac_env.py'
CAMERA='d435i_depth_camera';LEGACY='d435i_depth'
METHODS=['RP-CCR','DWA','TEB','RPP','MPPI','SVG-MPPI','SCCR','PRIEST','PSF','PCBF']
def extractor(np):
 f=next(n for n in ast.walk(ast.parse(ORIGINAL.read_text()))if isinstance(n,ast.FunctionDef)and n.name=='_get_depth_features');s=dict(np=np);exec(compile(ast.Module(body=[f],type_ignores=[]),str(ORIGINAL),'exec'),s);return s[f.name]
def validate_packet(p,k,producer):
 assert set(p)=={'schema','native','sim_time','own_body','depth24','actual_render_available','producer_sha256','physical_authority','packet_sha256'}
 clean=dict(p);assert clean.pop('packet_sha256')==digest(clean)
 assert p['schema']=='ACTUAL_SHARED_DEPTH24_V1'and type(p['native'])is int and p['native']==k and abs(p['sim_time']-.01*k)<=1e-8
 assert p['actual_render_available']is True and p['physical_authority']is False and p['producer_sha256']==producer
 assert len(p['own_body'])==5 and len(p['depth24'])==24 and all(type(x)in(int,float)and math.isfinite(x)for x in p['own_body']+p['depth24'])
 assert all(0<=x<=1 for x in p['depth24']);return copy.deepcopy(p['depth24'])
def saved_features(np,frame):
 class Saved:
  def update_scene(self,*a,**kw):pass
  def enable_depth_rendering(self):pass
  def render(self):return frame.copy()
  def disable_depth_rendering(self):pass
 e=SimpleNamespace(depth_camera_id=0,depth_feature_dim=24,depth_max_range=5.,renderer=Saved(),data=None,depth_camera_name=CAMERA)
 return extractor(np)(e)
def independent(np,a):
 a=np.nan_to_num(a,nan=5.,posinf=5.,neginf=0.);a=np.clip(a,0.,5.);h,w=a.shape;edges=np.linspace(0,w,9).astype(int);v=[]
 for f in [.3,.5,.7]:
  r=int(h*f)
  for x,y in zip(edges[:-1],edges[1:]):v.append(float(np.mean(a[max(0,r-3):min(h,r+4),x:y]))/5.)
 return np.asarray(v,dtype=np.float32)
class Sampler:
 def __init__(self,v,np,save,quota,source,out):
  assert os.sched_getaffinity(0)=={2};a=read(O/'PILOT_ADMISSION.json');assert a['models_authorized']and a['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'
  assert source[str(ORIGINAL.relative_to(R))]==sha(ORIGINAL)and source[str((C/'depth.py').relative_to(R))]==sha(C/'depth.py')
  import mujoco as mj
  self.v=v;self.np=np;self.save=save;self.quota=quota;self.out=out;self.last=-1;self.frames=0;self.producer=sha(C/'depth.py');self.fn=extractor(np)
  self.id=int(mj.mj_name2id(v.m,mj.mjtObj.mjOBJ_CAMERA,CAMERA));legacy=int(mj.mj_name2id(v.m,mj.mjtObj.mjOBJ_CAMERA,LEGACY));assert self.id>=0 and legacy<0,'SCCR_DEPTH_CAMERA_BINDING_REFUSED'
  self.renderer=mj.Renderer(v.m,height=64,width=64)
  try:save('SCCR_ACTUAL_CAMERA_BINDING.json',dict(actual_camera_name=CAMERA,camera_id=self.id,legacy_lookup_name=LEGACY,legacy_camera_id=legacy,explicit_new_alias=True,no_model_rename=True,camera_pos=v.m.cam_pos[self.id].tolist(),camera_quat=v.m.cam_quat[self.id].tolist(),camera_fovy=float(v.m.cam_fovy[self.id]),explicit_renderer_constructors=1,internal_factory_renderer_constructors=None,renderer_backend=os.environ.get('MUJOCO_GL'),explicit_learned_policy_calls=0,factory_internal_policy_calls=None))
  except BaseException:
   self.renderer.close();raise
 def capture(self,receipt):
  np=self.np;v=self.v;k=v.count;assert k in [0,5,10]and k>self.last
  assert receipt['packet']['native_tick']==k and receipt['packet']['sim_time']==float(v.d.time)
  keys=['qpos','qvel','ctrl','mocap_pos','mocap_quat'];before={n:np.asarray(getattr(v.d,n)).copy()for n in keys};stamp=float(v.d.time);calls=[];raws=[];failure=[];renderer=self.renderer
  class Spy:
   def update_scene(self,data,camera):
    assert data is v.d and camera==CAMERA;calls.append('update_scene');renderer.update_scene(data,camera=camera)
   def enable_depth_rendering(self):calls.append('enable_depth');renderer.enable_depth_rendering()
   def render(self):
    calls.append('render')
    try:a=renderer.render();raws.append(a.copy());return a
    except BaseException as e:failure.append(repr(e));raise
   def disable_depth_rendering(self):calls.append('disable_depth');renderer.disable_depth_rendering()
  env=SimpleNamespace(depth_camera_id=self.id,depth_feature_dim=24,depth_max_range=5.,renderer=Spy(),data=v.d,depth_camera_name=CAMERA)
  features=self.fn(env)
  assert not failure and calls==['update_scene','enable_depth','render','disable_depth']and len(raws)==1,'SCCR_DEPTH_ACTUAL_RENDER_UNAVAILABLE'
  raw=raws[0];assert raw.shape==(64,64)and np.isfinite(raw).all(),'SCCR_DEPTH_INVALID_ACTUAL_FRAME'
  assert np.array_equal(features,independent(np,raw))and all(np.array_equal(before[n],getattr(v.d,n))for n in keys)and float(v.d.time)==stamp,'SCCR_DEPTH_READ_MUTATED_STATE_OR_FEATURES'
  filename=f'SCCR_DEPTH_{k:06d}.npz';self.quota.save_npz(self.out/filename,dict(depth=raw),np)
  packet=dict(schema='ACTUAL_SHARED_DEPTH24_V1',native=k,sim_time=stamp,own_body=receipt['packet']['body'],depth24=features.tolist(),actual_render_available=True,producer_sha256=self.producer,physical_authority=False);packet['packet_sha256']=digest(packet)
  delivered=[validate_packet(packet,k,self.producer)for _ in METHODS];assert all(x==features.tolist()for x in delivered)
  self.save(f'SCCR_DEPTH_{k:06d}.json',dict(packet=packet,receipt=receipt,raw_frame=filename,raw_frame_sha256=sha(self.out/filename),dtype=str(raw.dtype),shape=list(raw.shape),actual_render_calls=1,all_ten_method_consumers=METHODS,all_ten_equal_depth_block=True,state_qpos_qvel_ctrl_mocap_time_unchanged=True,original_function_sha256=sha(ORIGINAL),explicit_camera_binding=CAMERA,original_camera_binding=LEGACY,original_full_SCCR_qualified=False))
  self.last=k;self.frames+=1
 def close(self):self.renderer.close()
def audit_saved(np,out,k,source):
 z=read(out/f'SCCR_DEPTH_{k:06d}.json');p=z['packet'];validate_packet(p,k,source[str((C/'depth.py').relative_to(R))]);assert z['raw_frame_sha256']==sha(out/z['raw_frame'])and z['original_function_sha256']==sha(ORIGINAL)
 original=load('SCCR_independent_saved_observation',C/'observation.py').verify(z['receipt'],k,.01*k)
 assert p['own_body']==original['body']and p['sim_time']==original['sim_time']
 with np.load(out/z['raw_frame'])as f:a=f['depth'].copy()
 assert a.shape==(64,64)and np.isfinite(a).all()and z['shape']==[64,64]and z['dtype']==str(a.dtype)
 assert np.array_equal(saved_features(np,a),independent(np,a))and np.array_equal(saved_features(np,a),np.asarray(p['depth24'],np.float32))
 assert z['actual_render_calls']==1 and z['state_qpos_qvel_ctrl_mocap_time_unchanged']and z['all_ten_method_consumers']==METHODS
 return dict(native=k,passed=True)

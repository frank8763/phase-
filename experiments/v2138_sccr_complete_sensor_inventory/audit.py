"""Static observation provenance and exact original depth extraction, no renderer."""
from pathlib import Path
import ast, hashlib, json, os, resource, time, traceback, types

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
ROOT=R/'runtime/mk-mini'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def resident(p):return sum(x.stat().st_blocks*512 for x in p.rglob('*') if x.is_file() and not x.is_symlink())
def allowance():
 return resident(R/'runs/v2132_remaining_method_qualification')+resident(R/'runs/v2136_priest_initial_admission')+resident(S)<2*1024**2 and resident(S)<256*1024
def put(n,z):
 b=json.dumps(z,indent=2,allow_nan=False).encode()+b'\n';assert len(b)<128*1024 and allowance()
 p=S/n;assert not p.exists();p.write_bytes(b);assert allowance()
def source(p):
 pins[str(p.relative_to(R))]=sha(p);return ast.parse(p.read_text())
def chain(p,k):
 t=source(p);c=next(n for n in t.body if isinstance(n,ast.ClassDef)and n.name==k)
 row=dict(path=str(p.relative_to(R)),class_name=k,observation_methods=[dict(name=n.name,line=n.lineno)for n in c.body if isinstance(n,ast.FunctionDef)and n.name in ['_get_obs','_get_depth_features','_make_obs','_base_action','_build_phase6_obs','_build_phase7_obs','_phase17c_build_obs']]);rows=[row]
 for base in c.bases:
  if not isinstance(base,ast.Name):continue
  options=[]
  for n in ast.walk(t):
   if not isinstance(n,ast.ImportFrom)or not n.module:continue
   for a in n.names:
    p2=ROOT/(n.module.replace('.','/')+'.py')
    if(a.asname or a.name)==base.id and p2.exists():options.append((n.lineno,p2,a.name))
  if options:
   _,p2,k2=sorted(options)[0];rows.extend(chain(p2,k2))
 return rows

def main():
 global pins
 assert os.sched_getaffinity(0)=={4};resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(110,120))
 S.mkdir(exist_ok=False);pins={};start=time.monotonic();put('ONCE.json',dict(pid=os.getpid(),unix=time.time(),scope='SOFTWARE_ONLY_NO_MODEL_RENDERER_OR_POLICY'))
 result=dict(passed=False,closed=False,model_initializations=0,actual_sensor_acquisitions=0,renderer_constructors=0,policy_deserializations=0,policy_inferences=0,optimizer_calls=0,physics=0,replay=0,formal_tasks=0)
 try:
  import numpy as np
  outer=chain(ROOT/'training/phase17_fusion_safety_sac_nav/envs/mkmini_phase17c_lidar_camera_fusion_env.py','MkMiniPhase17CLidarCameraFusionEnv')
  inner=chain(ROOT/'training/phase7_camera_depth/envs/mkmini_phase7_depth_camera_aux_env.py','MkMiniPhase7DepthCameraAuxEnv')
  p=ROOT/'training/envs/mkmini_real_indoor_phase3_depth_astar_sac_env.py';t=source(p)
  f=next(n for n in ast.walk(t)if isinstance(n,ast.FunctionDef)and n.name=='_get_depth_features')
  space=dict(np=np);exec(compile(ast.Module(body=[f],type_ignores=[]),str(p),'exec'),space);fn=space[f.name]
  init=next(n for n in ast.walk(t)if isinstance(n,ast.FunctionDef)and n.name=='__init__');init_text=ast.unparse(init)
  assert 'height=64'in init_text and 'width=64'in init_text and 'self.depth_max_range = 5.0'in init_text
  inner_providers=[x for x in inner if any(m['name']=='_get_obs'for m in x['observation_methods'])]
  assert inner_providers[0]['path']==str(p.relative_to(R))
  class FixtureRenderer:
   def __init__(self,frame,fail=False):self.frame=frame;self.fail=fail;self.render_calls=0
   def update_scene(self,data,camera):assert camera=='d435i_depth'
   def enable_depth_rendering(self):pass
   def render(self):
    self.render_calls+=1
    if self.fail:raise RuntimeError('EXPLICIT_SYNTHETIC_RENDER_FAILURE')
    return self.frame.copy()
   def disable_depth_rendering(self):pass
  def independent(frame):
   a=np.array(frame,copy=True)
   if a.ndim==3:a=a[:,:,0]
   a[np.isnan(a)|np.isposinf(a)]=5.;a[np.isneginf(a)]=0.;a=np.maximum(0.,np.minimum(5.,a))
   h,w=a.shape;out=[];edges=[int(x)for x in np.linspace(0,w,9)]
   for fraction in [.3,.5,.7]:
    r=int(h*fraction)
    for lo,hi in zip(edges[:-1],edges[1:]):
     block=a[max(0,r-3):min(h,r+4),lo:hi];out.append(float(np.mean(block))/5. if block.size else 1.)
   return np.array(out,dtype=np.float32)
  ramp=(np.arange(4096,dtype=np.float64).reshape(64,64)%97)/16.
  corrupt=ramp.copy();corrupt[18,0]=np.nan;corrupt[30,8]=np.inf;corrupt[44,32]=-np.inf
  cases=[('constant',np.full((64,64),2.5),False,False),('ramp',ramp,False,False),('nonfinite',corrupt,False,False),('three_channel',np.stack([ramp,ramp+1,ramp+2],axis=2),False,False),('missing_camera',ramp,True,False),('render_failure',ramp,False,True)]
  tested=[]
  for name,frame,missing,fail in cases:
   renderer=FixtureRenderer(frame,fail);env=types.SimpleNamespace(depth_camera_id=-1 if missing else 0,depth_feature_dim=24,depth_max_range=5.,renderer=renderer,data=None,depth_camera_name='d435i_depth')
   got=fn(env);expected=np.ones(24,dtype=np.float32)if missing or fail else independent(frame)
   assert got.shape==(24,)and got.dtype==np.float32 and np.array_equal(got,expected),name
   tested.append(dict(name=name,passed=True,synthetic_renderer_calls=renderer.render_calls,actual_renderer_calls=0,source_fallback_used=missing or fail,feature_sha256=hashlib.sha256(got.tobytes()).hexdigest(),maximum_reference_error=float(np.max(abs(got-expected)))))
  layout=[('core_36_lidar',0,36),('goal_waypoint_and_previous_action',36,42),('rendered_depth_24',42,66),('phase6_32_lidar',66,98),('phase6_goal_camera',98,103),('phase6_lidar_safety',103,107),('phase7_ray_depth_and_summary',107,127),('original_base_policy_action',127,129),('phase17_32_lidar',129,161),('phase17_goal_camera',161,166),('phase17_ray_depth_and_summary',166,186)]
  assert sum(b-a for _,a,b in layout)==186
  weights={}
  for label,n in [('Phase6','training/phase6_clean/confirmed/phase6_v1_lidar_main_camera_goal_55k_confirmed.zip'),('Phase20','training/phase20_unknown_obstacle_adaptation/checkpoints/stage_b_randomized/phase20_stage_b_325000_steps.zip')]:
   p=ROOT/n;assert p.is_file();pins[str(p.relative_to(R))]=sha(p);weights[label]=dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),deserialized=False)
  assert all(sha(R/n)==h for n,h in pins.items())
  result.update(passed=True,outer_class_chain=outer,inner_class_chain=inner,original_depth_AST_sha256=hashlib.sha256(ast.dump(f,include_attributes=False).encode()).hexdigest(),layout=[dict(name=n,start=a,end=b)for n,a,b in layout],depth_feature_cases=tested,original_appended_camera_depth_dims=50,additional_core_rendered_depth_dims=24,total_direct_camera_depth_feature_dims=74,original_full186_builder_qualified=False,physical_sensor_noise_sampling_qualified=False,all_ten_method_equal_sensor_group_status='DRAFT_REQUIRES_PHYSICAL_PRODUCER_AND_METHOD_CAPABILITY_QUALIFICATION',frozen_policy_metadata=weights,input_SHA256=pins,all_original_inputs_unchanged=True)
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc(),input_SHA256=pins)
 result.update(closed=True,wall_s=time.monotonic()-start,source_SHA256={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()});put('RESULT.json',result)
 print(json.dumps({k:v for k,v in result.items()if k not in ['outer_class_chain','inner_class_chain','input_SHA256','source_SHA256','layout','traceback']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())

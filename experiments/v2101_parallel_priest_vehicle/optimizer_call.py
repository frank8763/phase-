"""Exact prospective author call graph. No author imports or launch on import."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
R=Path(__file__).resolve().parents[2]
OLD=R/'experiments/v1485_priest_current_polynomial_seam'

def exact(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def run(request,*,current,kernel,jnp,jax,np,budget,authority):
 # A future isolated worker supplies already-authorized modules. No default
 # entry point can create this missing scope or import JAX to manufacture it.
 admission=R/'runs/v2101_parallel_priest_vehicle/vehicle/actual/PRIEST_OPTIMIZER_ADMISSION.json'
 assert admission.is_file(),'PRIEST_OPTIMIZER_TARGET_NOT_ADMITTED'
 admitted=json.loads(admission.read_text());assert admitted==authority and authority['scope']=='PRIEST_OPTIMIZER_ONLY'
 assert authority['models_authorized']is False and authority['request_sha256']==request['request_sha256']and authority['input_sha256']==current['input_sha256']
 clean=dict(request);identity=clean.pop('request_sha256');assert digest(clean)==identity
 assert request['input_sha256']==current['input_sha256']and request['origin_native']==current['fixed_origin_native']and request['origin_sim_time']==current['fixed_origin_sim_time']
 assert kernel.author_sha256==request['port_identity']['author_sha256']and kernel.ported_sha256==request['port_identity']['ported_sha256']
 assert authority['kernel_source_sha256']==kernel.ported_sha256
 assert request['constructor_kwargs']['num_batch']==110 and request['constructor_kwargs']['maxiter_cem']==12
 def sync(value):
  # Completion is declared only after all dispatched device values are ready.
  return jax.tree_util.tree_map(lambda x:x.block_until_ready()if hasattr(x,'block_until_ready')else x,value)
 def call(stage,fn):
  budget.begin(stage)
  try:result=sync(fn());budget.complete(stage);return result
  except BaseException as e:budget.failure(e);raise
 state=np.random.get_state()
 try:
  np.random.seed(request['numpy_seed'])
  def construct():
   value=kernel.module.batch_crowd_nav(**request['constructor_kwargs'])
   sync([v for v in vars(value).values()if hasattr(v,'block_until_ready')])
   return value
  prob=call('CONSTRUCTOR',construct)
  assert prob.maxitet_proj==13 and prob.initial_up_sampling==30 and prob.ellite_num_const==80 and prob.num_sample_warm==55
  path=request['path'];xw=jnp.asarray(path['x_waypoint']);yw=jnp.asarray(path['y_waypoint']);arc=jnp.asarray(path['arc_vec']);dx=jnp.asarray(path['x_diff']);dy=jnp.asarray(path['y_diff'])
  initial=jnp.asarray(request['initial_state']);key=jax.random.PRNGKey(request['jax_key'])
  static=request['static_points_world'];dynamic=request['dynamic_points_world'];num=request['constructor_kwargs']['num']
  # Use causal full-period disk as stationary proposal enclosure, not actor
  # position/velocity; absent dynamic forecast remains shape(0,num).
  sx=jnp.asarray([p[0]for p in static]);sy=jnp.asarray([p[1]for p in static]);order=jnp.argsort((sx-initial[0])**2+(sy-initial[1])**2)
  xs=jnp.repeat(sx[order,None],num,axis=1);ys=jnp.repeat(sy[order,None],num,axis=1)
  xd=jnp.repeat(jnp.asarray([p[0]for p in dynamic]).reshape(len(dynamic),1),num,axis=1);yd=jnp.repeat(jnp.asarray([p[1]for p in dynamic]).reshape(len(dynamic),1),num,axis=1)
  warm=call('WARM_GUESS',lambda:prob.compute_warm_traj(initial,.1,xw,yw,arc,dx,dy))
  guess=call('INITIAL_GUESS',lambda:prob.compute_traj_guess(initial,xs,ys,xd,yd,.1,xw,yw,arc,*warm,dx,dy))
  solx,soly,x,y,vx,vy,ax,ay,mean,cov,xfin,yfin=guess
  lamx=jnp.zeros((110,prob.nvar));lamy=jnp.zeros((110,prob.nvar))
  result=call('CEM',lambda:prob.compute_cem(key,initial,xfin,yfin,lamx,lamy,xs,ys,xs[:20],ys[:20],xd,yd,solx,soly,x,y,vx,vy,ax,ay,xw,yw,arc,mean,cov))
  _,_,cx,cy,*_=result;cx=[float(v)for v in cx];cy=[float(v)for v in cy]
  assert len(cx)==len(cy)==11 and all(math.isfinite(v)for v in cx+cy)
  reply=dict(kind='PRIEST_AUTHOR_POLYNOMIAL_PROPOSAL',schema=1,run_id=current['run_id'],input_sha256=current['input_sha256'],core_identity_sha256=current['core_identity_sha256'],origin_native=current['fixed_origin_native'],origin_sim_time=current['fixed_origin_sim_time'],horizon_s=10.,coordinate_frame='REAR_AXLE_WORLD_XY',gear=request['gear'],coefficients_x=cx,coefficients_y=cy,optimizer_accounting=dict(optimizer_calls=1,iterations_completed=12,mathematical_candidate_evaluations=None,inflight_unknown=False,author_core_source_sha256=kernel.author_sha256))
  candidate=exact('v1487_frozen_proposal_boundary',OLD/'candidate_output.py').bind(current,reply)
  return dict(candidate=candidate,optimizer_request_sha256=identity,ported_source_sha256=kernel.ported_sha256,work_accounting=budget.counts.copy(),proposal_only=True,complete_response_witness_passed=False,physical_admission=False)
 finally:np.random.set_state(state)

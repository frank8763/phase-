"""One fixed saved-input qualification. Model creation and integration forbidden."""
import ast,fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import MethodType,SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V791_NO_MODELS_OR_INTEGRATIONS_IN_QUALIFICATION')
for name in ['MjModel','MjSpec','MjData','mj_forward','mj_step','mj_step1','mj_step2']:setattr(mujoco,name,forbidden)
from exact_footprint import pose_values
from motion_tracker import install_time_gate
from reference_audit_geometry import reference_field
from route_commitment import route_check
from future_guide import route_world
from union_belief import future_cells
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v791_coherent_global_reference/pre_navigation';root.mkdir(parents=True,exist_ok=False)
def dump(name,value):(root/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False,default=lambda x:x.item()if isinstance(x,np.generic)else x.tolist()if isinstance(x,np.ndarray)else (_ for _ in()).throw(TypeError(type(x).__name__)))+'\n')
started=time.time();deadline=min(started+600,read(repo/'RPCCR_GLOBAL_DYNAMIC_DAY_AUTHORIZATION_20261104.json')['absolute_deadline_unix']);status='RUNNING';os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V791_QUALIFICATION_ABSOLUTE_STOP')));signal.alarm(max(1,math.floor(deadline-started)))
try:
 assert(repo/'REVIEW_PENDING').exists();lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/p)==h for p,h in freeze['files'].items())
 oldown=repo/'experiments/v790_persistent_body_global';oldtext=(oldown/'run_static.py').read_text().replace('v790_persistent_body_global','v791_coherent_global_reference').replace('V790_PERSISTENT_NORM_CERTIFICATE','V791_COHERENT_GLOBAL_REFERENCE');newtext=(own/'run_static.py').read_text();assert newtext==oldtext.replace('keep=route_check(field,path,index,current,rows,step,last_plan)','keep=route_check(route_field,path,index,current,rows,step,last_plan)'),'UNREGISTERED_RUNNER_CHANGE'
 core=['motion_tracker.py','geometry_predictor.py','joint_admission.py','reserved_recovery.py','discovery_brake.py','retained_reentry.py','recovery_supervisor.py','future_guide.py','control_contract.py','recursive_domain.py','risk_domain.py','persistent_norm.py','renewal_state.py','free_certificate.py','self_geometry.py','dynamic_actor.py','contact_contract.py']
 core_checks={n:sha(oldown/n)==sha(own/n)for n in core if(oldown/n).exists()};assert all(core_checks.values())and len(core_checks)>=14
 tree=ast.parse(newtext);calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)];ref=[n for n in calls if isinstance(n.func,ast.Name)and n.func.id=='route_check'];assert len(ref)==1 and ast.unparse(ref[0].args[0])=='route_field'
 prediction=[n for n in calls if isinstance(n.func,ast.Attribute)and n.func.attr=='select'and ast.unparse(n.func.value)=='predictor'];assert prediction and all(ast.unparse(n.args[1])=='field'for n in prediction)
 admission=[n for n in calls if isinstance(n.func,ast.Name)and n.func.id=='admit_ranked'];assert len(admission)==1 and any(isinstance(n,ast.Name)and n.id=='field'for n in admission[0].args)
 pair=repo/'runs/v790_persistent_body_global/main_slot01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');trace=read(cell/'trace.json');routes={x['step']:x for x in map(json.loads,(cell/'route_revalidation.jsonl').read_text().splitlines())};records=[];old_error=0.;new_error=0.;packet_count=0
 for line in(cell/'motion_estimate.jsonl').open():
  state=json.loads(line);step=state['step'];packet_count+=1
  if step not in routes:continue
  assert state['center']is None,'REGISTERED_SAVED_INPUT_NOT_UNSEEN';r=routes[step];path=np.asarray(r['reference_path']);index=r['index'];poses=path[index:min(len(path),index+26),:3]
  base=reference_field(protocol,state);oldfield=reference_field(protocol,state);oldfield.pose_values=MethodType(pose_values,oldfield);install_time_gate(oldfield,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);old=float(oldfield.pose_values(poses).min());old_error=max(old_error,abs(old-r['current_route_minimum_m']));assert abs(old-r['current_route_minimum_m'])<=1e-8
  base.pose_values=MethodType(pose_values,base);new=route_check(base,path,index,np.asarray(trace[step-1]['pose']),trace[:step],step,r['last_plan']);independent=float(pose_values(reference_field(protocol,state),poses).min());new_error=max(new_error,abs(new['current_route_minimum_m']-independent));assert new_error<=1e-12 and new['current_route_invalid']==bool(independent<.155-1e-6)and new['authorizes_control']is False and new['future_native_gate_unchanged']is True and new['validation_basis']=='SAME_AS_GLOBAL_SEARCH_FIELD'
  records.append(dict(step=step,old_minimum_m=old,new_minimum_m=independent,old_invalid=r['current_route_invalid'],new_invalid=new['current_route_invalid'],control_or_tail_changed=False))
 assert len(records)==398 and packet_count==527;removed=sum(x['old_invalid']and not x['new_invalid']for x in records);assert removed>0
 # Original tracked blank-course state: independent geometry must match the
 # unchanged causal projection, never a privileged true trajectory.
 tracked_pair=repo/'runs/v697_rpccr_dynamic_initialization/v700_repeat_slot01/paired';sp=read(tracked_pair/'STATIC_PROTOCOL.json');tracked=None
 for line in(tracked_pair/'geometry_memory/motion_estimate.jsonl').open():
  s=json.loads(line)
  if s['center']is not None:tracked=s;break
 assert tracked is not None
 cases=[tracked,dict(center=[.8,-.3],position_lower=[.7,-.4],position_upper=[.9,-.2],velocity_lower=[-.04,-.06],velocity_upper=[.06,.02],current_outer_rectangle=[.8,-.3,.2,.2],hidden_world_geometry_used=False)]
 rng=np.random.default_rng(791);probe=np.c_[rng.uniform(-4.,4.,(1000,2)),rng.uniform(-np.pi,np.pi,1000)];projection_errors=[]
 for s in cases:
  world=dict(rectangles=[*sp['known_rectangles'],s['current_outer_rectangle']],circles=sp['known_circles'],sensor_points=[]);projected,meta=route_world(world,s);f=reference_field(sp,s);assert np.max(abs(np.asarray(projected['rectangles'])-f.rectangles))<=1e-12 and meta['status']=='CAUSAL_GLOBAL_OUTER_PROJECTION'and not meta['hidden_world_geometry_used']
  left=pose_values(f,probe);other=SimpleNamespace(**vars(f));other.rectangles=np.asarray(projected['rectangles']);right=pose_values(other,probe);projection_errors.append(float(np.max(abs(left-right))));assert projection_errors[-1]<=1e-12
  if'outer_state_cells'in s:
   lo,hi=future_cells(s['outer_state_cells'],np.linspace(0,6.56,657));assert max(float(np.max(np.asarray(meta['projected_center_lower'])-lo)),float(np.max(hi-np.asarray(meta['projected_center_upper']))))<=1e-7
 assert all(sha(repo/p)==h for p,h in freeze['files'].items());status='REFERENCE_EXECUTION_CONTRACT_QUALIFIED';dump('RECORDS.json',records);dump('RESULT.json',dict(status=status,old_checkpoint_minimum_max_error=old_error,new_reference_minimum_max_error=new_error,all398_old_route_checks_reconstructed=True,old_invalid=sum(x['old_invalid']for x in records),new_invalid=sum(x['new_invalid']for x in records),proposal_only_replan_triggers_removed=removed,physical_core_identical=core_checks,only_registered_runner_call_changed=True,actual_execution_field_retained=True,tracked_and_synthetic_projection_max_errors=projection_errors,new_models=0,new_integrations=0,new_predictions=0,new_navigation=0))
except BaseException as e:status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:signal.alarm(0);dump('ROUND_WINDOW.json',dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=True,status=status,elapsed_s=time.time()-started))
print(status)

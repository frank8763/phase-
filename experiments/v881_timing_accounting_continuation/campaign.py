"""Finite offline sequence; frozen software gates, exact17:00 stop and no online decisions."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v881_timing_accounting_continuation';sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import authorized,digest,resolve,DEADLINE
from handshake import require,file_sha,verify_sources
from audit import repeat_check

def read(p):return json.loads(p.read_text())
def dump(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');t.replace(p)
class FunctionalStop(Exception):pass
class FatalStop(Exception):pass
class LimitStop(Exception):pass

def halt(p):
 if p and p.poll()is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()

def capacity():
 size=0
 for base in [R/'runs/v856_nav2_foundation',R/'runs/v866_margin_qualification',R/'runs/v867_margin_navigation',R/'runs/v858_nav2_verified/v867',R/'runs/v874_daytime_20261108',R/'runs/v858_nav2_verified/v874',R/'runs/v875_euclidean_daytime',R/'runs/v858_nav2_verified/v875',R/'runs/v876_terminal_region_daytime',R/'runs/v858_nav2_verified/v876',R/'runs/v877_controller_daytime',R/'runs/v858_nav2_verified/v877',R/'runs/v878_software_scan_continuation',R/'runs/v858_nav2_verified/v878',R/'runs/v879_ros_entry_continuation',R/'runs/v858_nav2_verified/v879',R/'runs/v880_reference_controller_grid',R/'runs/v858_nav2_verified/v880',R/'runs/v881_timing_accounting_continuation',R/'runs/v858_nav2_verified/v881']:
  if base.exists():size+=sum(p.lstat().st_size for p in base.rglob('*')if p.is_file()and not p.is_symlink())
 if size>1750*1024**2:raise LimitStop('TEMP_BUDGET_RESERVE_REQUIRED_FOR_FINAL_ARCHIVE')
 if DEADLINE-time.time()<300:raise LimitStop('INSUFFICIENT_300S_REMAINING')
 return size

def independent_classify(task):
 p=Path(task['output']);a=read(p/'INDEPENDENT_AUDIT.json');n=read(p/'RESULT.json');ros=read(p/'ROS_RESULT.json');checks=a.get('checks',{});startup=a.get('startup_checks',{})
 physical=bool(checks)and all(v for k,v in checks.items()if k!='genuine_ros_observations')
 fresh=bool(startup)and all(v for k,v in startup.items()if k not in ['command_stream_present','original_physical_evidence'])
 fresh=fresh and ros.get('odometry_messages',0)>0 and ros.get('maximum_observation_age_s',float('inf'))is not None and ros['maximum_observation_age_s']<=.2
 healthy=physical and fresh and n.get('status')=='NATIVE_COMPLETE'and not n.get('error')and not ros.get('error')
 if not healthy:raise FatalStop('SAFETY_STATE_SENSOR_MODEL_INTERFACE_OR_EVIDENCE_FAILURE')
 if not a['passed']:raise FunctionalStop('SAFE_COMPLETE_NAVIGATION_FUNCTIONAL_FAILURE')
 return a,n,ros

def main():
 receipt=read(O/'AUTHORIZATION.json');freeze=file_sha(C/'SOURCE_FREEZE.json');require(receipt['deadline_unix']==DEADLINE and receipt['source_freeze_sha256']==freeze,'ROOT_NOT_FROZEN');verify_sources(R,C/'SOURCE_FREEZE.json');guard=(R/'REVIEW_PENDING').read_bytes();require(hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66','GUARD_CHANGED')
 lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(O/'CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),deadline_unix=DEADLINE,freeze_sha256=freeze),f)
 signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(LimitStop('OUTER_ABSOLUTE_STOP')))
 templates=read(C/'TASKS.json');rows=[];pref=[];software=[];branches=[];selected=None;child=None;status='RUNNING';error=None
 def run_sub(cmd,console,limit):
  nonlocal child
  with console.open('w')as f:
   child=subprocess.Popen(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
   dump(O/'ACTIVE_CHILD.json',dict(pid=child.pid,args=cmd,started_unix=time.time()))
   try:child.wait(timeout=min(limit,max(.01,DEADLINE-3-time.time())))
   except BaseException:halt(child);raise
  code=child.returncode;child=None;return code
 def qualify(v):
  p=O/'software'/v
  if(p/'QUALIFICATION.json').exists():return read(p/'QUALIFICATION.json')['passed']
  p.mkdir(parents=True,exist_ok=True);rs=[];passed=True
  for name in ['fine_we','fine_ns','fine_ew','fine_ns_checkpoint']:
   capacity();verify_sources(R,C/'SOURCE_FREEZE.json');code=run_sub([sys.executable,'-B',str(C/'software_one.py'),v,name],p/(name+'.console'),75);q=p/name
   if not(q/'ROS_RESULT.json').exists():passed=False;rs.append(dict(name=name,passed=False,error='NO_SOFTWARE_RESULT',returncode=code));break
   result=read(q/'ROS_RESULT.json');planned=bool(result.get('qualified_initial_plan'))
   if planned and json.loads((C/(v+'.yaml')).read_text())['controller_server']['ros__parameters']['FollowPath']['plugin']=='nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController':
    ac=run_sub([sys.executable,'-B',str(C/'software_audit.py'),v,name],p/(name+'_audit.console'),45);g=read(q/'GEOMETRY_FAST_AUDIT.json')if(q/'GEOMETRY_FAST_AUDIT.json').exists()else{};planned=ac==0 and g.get('reference_lethal_raster_samples',999)==0 and g.get('minimum_full_body_known_geometric_clearance_m',-1)>=.15
    # Fixed-speed ideal arcs remain diagnostic; the REAL current controller's collision-checked stream is the operational gate.
   elif planned:planned=all(x.get('passed')and x.get('wall_s',999)<=.75 for x in read(q/'ROUTER_REQUESTS.json'))
   proxy_rows=read(q/'ROUTER_REQUESTS.json')if(q/'ROUTER_REQUESTS.json').exists()else[]
   commands=read(q/'COMMANDS.json').get('cmd_vel',[])if(q/'COMMANDS.json').exists()else[]
   controller_ok=result.get('qualified_initial_control')is True and any(abs(x[1])>=.005 for x in commands)
   planned=planned and controller_ok and bool(proxy_rows)and all(x.get('passed')and x.get('wall_s',999)<=.75 for x in proxy_rows)
   diagnostic=name=='fine_ns_checkpoint'
   rs.append(dict(name=name,passed=planned,required_for_gate=not diagnostic,ros_passed=result['passed'],error=result.get('error'),action_error_code=result.get('action_error_code')))
   if diagnostic:continue
   if not planned:passed=False;break
  value=dict(passed=passed,models=0,integrations=0,variant=v,rows=rs,unexecuted_probes=4-len(rs),source_freeze_sha256=freeze,at=time.time());dump(p/'QUALIFICATION.json',value);software.append(value);dump(O/'SOFTWARE_RESULTS.json',software);return passed
 def launch(template,t0=False):
  nonlocal child
  capacity();verify_sources(R,C/'SOURCE_FREEZE.json');require((R/'REVIEW_PENDING').read_bytes()==guard,'GUARD_NOT_RESTORED');task=resolve(template,selected);auth=dict(receipt,run_id=task['run_id'],task_sha256=digest(task));authorized(task,auth,time.time(),freeze);prefix=('t0_'if t0 else'nav_')+task['task_id'];tp=O/(prefix+'.task.json');ap=O/(prefix+'.authorization.json');dump(tp,task);dump(ap,auth);dump(O/'ACTIVE.json',dict(kind='PREFLIGHT'if t0 else'NAVIGATION',task=task,started_unix=time.time(),deadline_unix=DEADLINE))
  if t0 and not task['dynamic']and task['role']=='development':
   source=R/'runs/v858_nav2_verified/v878/preflights'/task['task_id'].replace('B_','A_',1)
   result=read(source/'RESULT.json');setup=read(source/'physics/SETUP.json');require(result['passed']and result['native_integrations']==0 and setup['case']['id']==task['case_id']and setup['seed']==task['seed']and setup['dynamic']is False,'REUSED_T0_CONTRACT_MISMATCH');require((source/'INITIAL_SCAN.json').is_file(),'ORIGINAL_TRUE_SCAN_MISSING')
   pref.append(dict(task_id=task['task_id'],attempted_new_model=False,reused_true_t0=True,source=str(source),source_result_sha256=file_sha(source/'RESULT.json'),source_scan_sha256=file_sha(source/'INITIAL_SCAN.json'),model_initialization_attempted=False,model_initialization_completed=False,native_integrations=0,passed=True,result=result));dump(O/'PREFLIGHTS.json',pref);return
  if t0:
   row=dict(task_id=task['task_id'],attempted=True,model_initialization_attempted=None,native_integrations=0);pref.append(row);dump(O/'PREFLIGHTS.json',pref)
   try:
    (R/'REVIEW_PENDING').unlink();code=run_sub([str(R/'run_phase.sh'),str((C/'preflight.py').relative_to(R)),str(tp),str(ap)],O/(prefix+'.console'),80)
   finally:halt(child);(R/'REVIEW_PENDING').write_bytes(guard)
   p=R/'runs/v858_nav2_verified/v881/preflights'/task['task_id'];r=read(p/'RESULT.json')if(p/'RESULT.json').exists()else{};row.update(result=r,passed=code==0 and r.get('passed')is True,model_initialization_attempted=r.get('environment_initialization_attempted'),model_initialization_completed=r.get('environment_initialization_completed'));dump(O/'PREFLIGHTS.json',pref)
   if not row['passed']:raise FatalStop('TRUE_T0_MODEL_SENSOR_OR_INITIAL_CLEARANCE_FAILURE')
   require((p/'INITIAL_SCAN.json').is_file(),'REAL_INITIAL_SCAN_MISSING');return
  row=dict(task_id=task['task_id'],role=task['role'],variant=task['resolved_variant'],case_id=task['case_id'],stage=task['stage'],output=task['output'],started_unix=time.time(),actual_native=None,replay_native=None,private_native=None);rows.append(row);dump(O/'RESULTS.json',rows)
  code=run_sub([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],O/(prefix+'.console'),250);p=Path(task['output']);n=read(p/'RESULT.json')if(p/'RESULT.json').exists()else{};a=read(p/'INDEPENDENT_AUDIT.json')if(p/'INDEPENDENT_AUDIT.json').exists()else{};row.update(returncode=code,passed=a.get('passed')is True,actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),goal_m=n.get('goal_distance_m'),minimum_clearance_m=n.get('minimum_actual_clearance_m'),model_initialization_completed=n.get('environment_initialization_completed'),closed_unix=time.time());dump(O/'RESULTS.json',rows);verify_sources(R,C/'SOURCE_FREEZE.json')
  independent_classify(task)
  if task['stage'].endswith('repeat'):
   baseline=next(t for t in templates if t['role']=='development'and t['variant']==template['variant']and t['stage']==task['stage'].replace('repeat','main')and t['case_id']==task['case_id'])if task['role']=='development'else next(t for t in templates if t['role']=='confirmation'and t['slot']==task['slot']);comparison=repeat_check(resolve(baseline,selected)['output'],p);dump(p/'NAVIGATION_REPEAT_COMPARISON.json',comparison)
   if not comparison['passed']:raise FatalStop('MODEL_INITIAL_STATE_OR_REPEAT_MISMATCH')
  return task
 try:
  for variant in ['A','B','C','D']:
   b=dict(variant=variant,status='SOFTWARE_QUALIFYING');branches.append(b);dump(O/'BRANCHES.json',branches)
   if not qualify(variant):b['status']='SOFTWARE_GATE_FAILED';dump(O/'BRANCHES.json',branches);continue
   try:
    bt=[t for t in templates if t['role']=='development'and t['variant']==variant]
    for dynamic in [False,True]:
     group=[t for t in bt if t['dynamic']==dynamic];mains=[t for t in group if t['stage'].endswith('main')]
     for t in mains:launch(t,True)
     for t in group:launch(t)
     if not dynamic:dump(O/(variant+'_STATIC_GATE.json'),dict(passed=True,source_freeze_sha256=freeze,variant=variant,at=time.time()))
    selected=variant;b['status']='THREE_STATIC_DYNAMIC_AND_FULL_RERUNS_PASSED';dump(O/'SELECTED.json',dict(passed=True,variant=selected,source_freeze_sha256=freeze,at=time.time()));dump(O/'DEVELOPMENT_GATE.json',dict(passed=True,variant=selected,at=time.time()));break
   except FunctionalStop as e:b.update(status='FUNCTIONAL_FAILED',error=str(e));dump(O/'BRANCHES.json',branches);continue
  dump(O/'BRANCHES.json',branches)
  if selected is None:status='NO_PREREGISTERED_CANDIDATE_PASSED';return 1
  conf=[t for t in templates if t['role']=='confirmation'];failures=0;outcomes=[]
  for t in conf:launch(t,True)
  for t in conf:
   try:launch(t);outcomes.append(dict(slot=t['slot'],case_id=t['case_id'],direction=t['initial_direction'],passed=True))
   except FunctionalStop:failures+=1;outcomes.append(dict(slot=t['slot'],case_id=t['case_id'],direction=t['initial_direction'],passed=False))
   dump(O/'CONFIRMATION_OUTCOMES.json',outcomes)
   if failures>=2:status='CONFIRMATION_SECOND_FUNCTIONAL_FAILURE';return 1
  require(len(outcomes)==24,'INCOMPLETE_DENOMINATOR');threshold=sum(x['passed']for x in outcomes)>=23 and all(sum(x['passed']for x in outcomes if x['case_id']==case)>=7 for case in {x['case_id']for x in outcomes})and all(sum(x['passed']for x in outcomes if x['direction']==direction)>=11 for direction in [-1,1])
  if not threshold:status='CONFIRMATION_THRESHOLD_FAILED';return 1
  for t in [t for t in templates if t['role']=='confirmation_repeat']:
   if not outcomes[t['slot']-1]['passed']:status='FIXED_REPEAT_BASELINE_FAILED_NO_REPLACEMENT';return 1
   launch(t)
  dump(O/'CONFIRMATION_GATE.json',dict(passed=True,attempted_new_main=24,successful_new_main=sum(x['passed']for x in outcomes),fixed_full_repeats=3,source_freeze_sha256=freeze,selected=selected,at=time.time()));status='FINITE_DYNAMIC_ACCEPTANCE_PASSED'
  alternative='MPPI_'+selected
  if qualify(alternative):
   for t in [t for t in templates if t['role']=='comparison']:
    launch(t,True)
    try:launch(t)
    except FunctionalStop:pass
  for ab in ['no_direction','smoothed']:
   v=selected+'_'+ab
   if not qualify(v):continue
   for t in [t for t in templates if t['role']=='ablation'and t['ablation']==ab]:
    launch(t,True)
    try:launch(t)
    except FunctionalStop:pass
  status='FINITE_DYNAMIC_ACCEPTANCE_AND_REGISTERED_COMPARISON_ABLATIONS_CLOSED'
 except LimitStop as e:status='HARD_TIME_OR_STORAGE_LIMIT_STOP';error=dict(error=repr(e),traceback=traceback.format_exc())
 except FunctionalStop as e:status='DEPENDENT_FUNCTIONAL_GATE_FAILED';error=dict(error=repr(e),traceback=traceback.format_exc())
 except BaseException as e:status='FATAL_SAFETY_SOURCE_INTERFACE_OR_EVIDENCE_STOP';error=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  halt(child);(R/'REVIEW_PENDING').write_bytes(guard);summary=dict(status=status,closed=True,error=error,selected=selected,branches=branches,software=software,attempted_navigation=len(rows),unexecuted_registered_navigation=len(templates)-len(rows),actual_native=sum(x['actual_native']for x in rows)if all(x.get('actual_native')is not None for x in rows)else None,replay_native=sum(x['replay_native']for x in rows)if all(x.get('replay_native')is not None for x in rows)else None,private_native=sum(x['private_native']for x in rows)if all(x.get('private_native')is not None for x in rows)else None,rows=rows,preflights=pref,new24_attempted=len([x for x in rows if x['role']=='confirmation']),dynamic_acceptance_passed=(O/'CONFIRMATION_GATE.json').exists(),training=0,real_robot=0,guard_restored=True,deadline_unix=DEADLINE,closed_unix=time.time());dump(O/'COMPLETION.json',summary);window=read(O/'ROUND_WINDOW.json');window.update(closed=True,status=status,closed_unix=time.time());dump(O/'ROUND_WINDOW.json',window)
  state=read(R/'CURRENT_EXPERIMENT.json');state.update(status='REVIEW_PENDING',current_active=False,active_pid=None,execution_window_closed=True);state['v881_timing_accounting_continuation']=dict(status=status,models_authorized=False,closed=True,deadline_unix=DEADLINE,completion='runs/v881_timing_accounting_continuation/COMPLETION.json');dump(R/'CURRENT_EXPERIMENT.json',state)
  try:
   with(O/'finalize.console').open('w')as f:
    result=subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180)
   dump(O/'FINALIZE_PROCESS.json',dict(returncode=result.returncode,models=0,integrations=0))
  except BaseException as e:dump(O/'FINALIZE_ERROR.json',dict(error=repr(e),models=0))
  print(json.dumps({k:v for k,v in summary.items()if k not in ['rows','preflights','software','branches']}),flush=True)
 return 0 if summary['dynamic_acceptance_passed']else 1
if __name__=='__main__':sys.exit(main())

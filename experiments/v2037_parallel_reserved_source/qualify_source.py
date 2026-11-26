"""One shared source proof for exactly two reserved original common cases."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,subprocess,sys,time,traceback,types
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;P=R/'runs/v2032_mppi_first_common_parallel'
CASES=[('common_09__RPP','v2038_rpp09_reserved_census','RPP',9,2),('common_02__MPPI','v2039_mppi02_reserved_census','MPPI',2,6)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=Path(p);x=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and 'inherit_freeze_path'in x:
  parent=R/x['inherit_freeze_path'];assert sha(parent)==x['inherit_freeze_sha256'];f=read(parent)['files'];assert all(n not in f or f[n]==h for n,h in x['files'].items());x=dict(x,files=dict(f,**x['files']))
 return x
def put(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def main():
 os.sched_setaffinity(0,{5});assert not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0));files={};result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,controller_constructors=0,optimizer_queries=0,physics=0,replay=0)
 try:
  assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(P/'POST_ROUND_STORAGE_BARRIER.json')['passed'];files.update(read(P/'SOURCE_FREEZE.json')['files']);prior=files.copy()
  for n,h in read(S/'PRIOR_CLOSED_BOUNDARIES.json')['proof_paths_SHA256'].items():assert sha(R/n)==h
  baseline=read(S/'QUIESCENT_BASELINE.json');census=load('new_reserved_global_census_source',C/'reserved_census.py');assert census.global_admission()['joint_peak_bytes']==baseline['joint_peak_bytes']
  proof_lanes=[];arithmetic=[];registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');base=R/'experiments/v2032_mppi_first_common_parallel'
  for rid,version,method,case,cpu in CASES:
   code=R/'experiments'/version;out=S/'lanes'/rid;task=read(out/'PILOT_TASK.json');shared=registry['tasks'][case-1]['task']
   for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction']:assert task[k]==shared[k]
   assert task['method']==method and task['common_task_id']==f'common_{case:02d}'and task['maximum_control_native']==57600 and task['native_limit']==60000 and task['stop_native']==2200
   assert read(out/'SOFTWARE_CHECK_PROOF.json')['passed']and len(read(out/'SOFTWARE_CHECK_PROOF.json')['navigation_branch_tests'])==4
   same=[]
   for n in ['capture.py','error_stop.py','resources.py','work.py','history_binding.py','response.py','evidence_service.py','generic_audit.py','observation.py']:
    expected=(base/n).read_text().replace(base.name,version)
    if method=='RPP':expected=expected.replace('MPPI','RPP').replace('mppi','rpp').replace('==[6]','==[2]')
    assert(code/n).read_text()==expected,'NUMERICAL_OR_CAPTURE_BODY_CHANGED:'+version+':'+n;same.append(n)
   assert(code/'reserved_census.py').read_bytes()==(C/'reserved_census.py').read_bytes()
   # Real method entry with no case authority refuses before model import.
   env=dict(os.environ,PHASE_REPO=str(R),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
   p=subprocess.run(['taskset','-c',str(cpu),'/usr/bin/python3','-B',str(code/'run_phase.py')],cwd=R,env=env,capture_output=True,timeout=10);assert p.returncode!=0 and (method+'_INDEPENDENT_PHASE_NOT_ADMITTED').encode()in p.stderr
   # Execute production namespace construction and actual write-isolation probe.
   entry=load('new_namespace_'+method,code/'run_phase.py');scratch=out/'namespace_software';scratch.mkdir();cmd=entry.namespace(code/'pilot_entry.py',scratch);i=next(i for i,x in enumerate(cmd)if x.endswith('/envs/mk_mujoco/bin/python'))
   other=S/'lanes'/('common_02__MPPI'if method=='RPP'else'common_09__RPP')
   script="import pathlib,os,json;out=pathlib.Path("+repr(str(scratch))+");out.joinpath('PASS').write_text('software');bad=[]\nfor p in [pathlib.Path("+repr(str(other/'FORBIDDEN_WRITE'))+"),pathlib.Path("+repr(str(code/'FORBIDDEN_WRITE'))+")]:\n try:p.write_text('forbidden')\n except OSError:bad.append(str(p))\n else:raise AssertionError('CROSS_LANE_OR_SOURCE_WRITABLE')\nassert os.sched_getaffinity(0)=={"+str(cpu)+"}and len(bad)==2;print(json.dumps(dict(passed=True,CPU="+str(cpu)+",blocked=bad,models=0)))"
   p=subprocess.run(['taskset','-c',str(cpu),*cmd[:i],cmd[i],'-B','-c',script],cwd=R,env=env,capture_output=True,timeout=20);assert p.returncode==0,p.stderr.decode();namespace=json.loads(p.stdout)
   # Exact model-free native CLI: no source aliases/admission -> no DLL/solver.
   ros=load('original_ROS_namespace_'+method,R/'experiments/v856_nav2_foundation/ros_environment.py');cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(code/'native_worker.py')]);j=cmd.index('--bind');cmd[j]='--ro-bind';env=ros.environment();env.pop('LD_PRELOAD',None);env.update(CUDA_VISIBLE_DEVICES='',ROS_LOG_DIR='/tmp/source_reserved');p=subprocess.run(['taskset','-c',str(cpu),*cmd],cwd=R,env=env,capture_output=True,timeout=20);(out/'NATIVE_SOURCE_REFUSAL.console').write_bytes(p.stdout+p.stderr);label=(method+'_CLOSED ').encode();closed=[json.loads(x[len(label):])for x in p.stdout.splitlines()if x.startswith(label)];assert p.returncode==1 and len(closed)==1 and closed[0]['constructors']==closed[0]['query_attempts']==0
   # Exercise real census function with explicit synthetic du snapshots only.
   module_tree=ast.parse((C/'reserved_census.py').read_text());fn=next(x for x in module_tree.body if isinstance(x,ast.FunctionDef)and x.name=='measure');own=[0];mode=[False]
   def du(*args,**kwargs):
    if mode[0]:raise subprocess.CalledProcessError(1,args[0])
    return str(own[0])+'\t'+str(R/task['output'])+'\n'
   space=dict(global_admission=lambda **kw:dict(joint_peak_bytes=baseline['joint_peak_bytes']),read=lambda p:baseline,S=S,R=R,Path=Path,os=os,subprocess=types.SimpleNamespace(check_output=du))
   exec(compile(ast.Module(body=[fn],type_ignores=[]),str(C/'reserved_census.py'),'exec'),space);os.sched_setaffinity(0,{cpu})
   for value in [0,1*1024**2,100*1024**2,223*1024**2,224*1024**2]:
    own[0]=value;measured,upper=space['measure'](Path(task['output']),read(out/'LIMITS_DRAFT.json'));assert measured==value;pending=224*1024**2-value;assert upper+pending+(272+512)*1024**2<=baseline['joint_peak_bytes']
   mode[0]=True
   try:space['measure'](Path(task['output']),read(out/'LIMITS_DRAFT.json'))
   except subprocess.CalledProcessError:missing_refused=True
   else:raise AssertionError('LOCAL_CENSUS_ERROR_SILENTLY_IGNORED')
   os.sched_setaffinity(0,{5});arithmetic.append(dict(method=method,synthetic_capacity_states=5,own_scope_scan_errors_fail_closed=missing_refused,global_tree_never_scanned=True))
   # Verify raw module paths before any declaration is frozen.
   missing=[]
   for p in code.glob('*.py'):
    tree=ast.parse(p.read_text())
    for n in ast.walk(tree):
     if isinstance(n,ast.BinOp)and isinstance(n.op,ast.Div)and isinstance(n.left,ast.Name)and n.left.id=='R'and isinstance(n.right,ast.Constant)and isinstance(n.right.value,str):
      name=n.right.value
      if name.startswith(('runs/','experiments/','runtime/'))and not(R/name).exists()and 'PARALLEL_METHOD_EVENTS'not in name:missing.append((p.name,name))
   assert not missing,missing
   proof_lanes.append(dict(method=method,task=task['common_task_id'],CPU=cpu,original_safety_modules_same=same,namespace=namespace,unadmitted_real_CLI_zero_models_DLL_constructors=True))
  # MPPI load-order change is exact: preload the SAME plugin LOCAL, then seed.
  m=(R/'experiments/v2039_mppi02_reserved_census/rng_binding.py').read_text();assert "plugin=ctypes.CDLL(str(plugin_path),mode=os.RTLD_NOW|os.RTLD_LOCAL)"in m and m.index('plugin=ctypes.CDLL')<m.index("core=ctypes.CDLL('/opt/ros/jazzy/lib/libmppi_controller.so'")
  deps=subprocess.check_output(['readelf','-d',str(R/'runs/v931_deadband_consistent_mppi/install/lib/libphase_deadband_mppi.so')],text=True);assert 'Shared library: [libmppi_controller.so]'in deps
  for folder in [C]+[R/'experiments'/x[1]for x in CASES]:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in list(S.glob('*.json'))+[P/'POST_ROUND_STORAGE_BARRIER.json']+[R/'runs/v1990_rpp_unexecuted_output_audit/rounds/common_08__RPP/POST_ROUND_STORAGE_BARRIER.json']:
   if p.name!='SOURCE_ONCE.json':files[str(p.relative_to(R))]=sha(p)
  for rid,version,method,case,cpu in CASES:
   out=S/'lanes'/rid
   for p in out.glob('*.json'):files[str(p.relative_to(R))]=sha(p)
   files.update(read(out/'NATIVE_DEPENDENCIES.json').get('repo_dependency_files',{}))
  assert all(sha(R/n)==h for n,h in files.items())
  proof=dict(passed=True,lanes=proof_lanes,reserved_census_real_function_synthetic_capacity_checks=arithmetic,quiescent_baseline_sha256=sha(S/'QUIESCENT_BASELINE.json'),original_closed_failures_not_repeated_or_upgraded=True,old_globaldu_race_replaced_by_precharged_algebraic_upper_bound=True,missing_local_files_still_fail_closed=True,MPPI_actual_plugin_preload_seed_probe_still_required_before_formal_claim=True,original120_denominator_and_task_fields_retained=True,source_only=True,models=0,actual_algorithm_DLLs=0,actual_constructors=0,actual_optimizer_queries=0)
  put(S/'SOFTWARE_CHECK_PROOF.json',proof);files[str((S/'SOFTWARE_CHECK_PROOF.json').relative_to(R))]=sha(S/'SOFTWARE_CHECK_PROOF.json');assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False));put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(source_members_seen=len(files),models_authorized=False))
 finally:os.sched_setaffinity(0,{5});result['closed']=True;put(S/'SOURCE_QUALIFICATION.json',result);put(S/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())

"""One prospective source delta, zero numerical constructors or integration."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,subprocess,sys,time,traceback,types
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;P=R/'runs/v2042_mppi_core_preload_exact_proof'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=Path(p);x=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and 'inherit_freeze_path'in x:
  q=R/x['inherit_freeze_path'];assert sha(q)==x['inherit_freeze_sha256'];b=read(q)['files'];assert all(n not in b or b[n]==h for n,h in x['files'].items());x=dict(x,files=dict(b,**x['files']))
 return x
def put(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def storage_fixture():
 f=S/'storage_software';f.mkdir();plan=dict(methods={'RPP':[]},prior_closed_barriers={});prior=f/'prior.json';put(prior,dict(passed=True));plan['prior_closed_barriers']['RPP']=dict(prior_path=str(prior.relative_to(R)),sha256=sha(prior))
 for i in range(3):
  O=f/('fixture_'+str(i));O.mkdir();plan['methods']['RPP'].append(dict(root=str(O.relative_to(R)),method='RPP',round_id=O.name))
 put(f/'PLAN_LOCKED.json',plan);mod=load('retained_storage_real_function_fixture',C/'queue_storage.py');mod.S=f
 old=sys.modules.get('reserved_census');sys.modules['reserved_census']=types.SimpleNamespace(global_admission=lambda **kw:dict(joint_peak_bytes=read(S/'QUIESCENT_BASELINE.json')['joint_peak_bytes']))
 try:
  first=R/plan['methods']['RPP'][0]['root'];mod.admit(first);(first/'actual').mkdir();(first/'actual/synthetic_bytes').write_bytes(b'x'*4096);put(first/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True));put(first/'OWNED_CHILD.json',dict(pid=0,start_ticks='0'))
  second=R/plan['methods']['RPP'][1]['root'];mod.admit(second);assert read(f/'RETENTION_STATE.json')['prior_closed_actual_allocated_bytes']>=4096
  (second/'actual').mkdir();(second/'actual/synthetic_bytes').write_bytes(b'x'*4096);put(second/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True));put(second/'OWNED_CHILD.json',dict(pid=0,start_ticks='0'));state=read(f/'RETENTION_STATE.json');state['prior_closed_actual_allocated_bytes']=144*1024**2;put(f/'RETENTION_STATE.json',state)
  third=R/plan['methods']['RPP'][2]['root']
  try:mod.admit(third)
  except AssertionError as e:assert 'RETAINED_CLOSED_CASE_RESERVATION_EXHAUSTED'in str(e)
  else:raise AssertionError('RETAINED_BOUND_NOT_ENFORCED')
  assert not(third/'STORAGE_ADMISSION.json').exists()and not(third/'PILOT_ONCE_CLAIM.json').exists()
 finally:
  if old is None:sys.modules.pop('reserved_census',None)
  else:sys.modules['reserved_census']=old
 return dict(passed=True,first_and_second_admission_function_passed=True,retention_exhaustion_rejected_before_formal_claim=True,models=0)
def main():
 os.sched_setaffinity(0,{5});assert not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0));result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,controller_constructors=0,optimizer_queries=0,physics=0,replay=0)
 try:
  assert read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];inherited=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in inherited.items());files=dict(inherited)
  transform=load('exact_prospective_transform',C/'transform.py');plan=read(S/'PLAN_LOCKED.json');registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');baseline=read(S/'QUIESCENT_BASELINE.json');assert sum(map(len,plan['methods'].values()))==13
  census=load('production_reserved_capacity',C/'reserved_census.py');assert census.global_admission()['joint_peak_bytes']==baseline['joint_peak_bytes'];laneproof=[]
  # Reuse completed original proofs; no old model/audit/replay is repeated.
  for method,prior in plan['prior_closed_barriers'].items():
   q=R/prior['prior_path'];assert sha(q)==prior['sha256']and read(q)['passed'];O=q.parent;completion=read(O/'COMPLETION.json');assert completion['closed']and completion['independent_audit']['passed']and completion['actual_native']==completion['own_replay_native'];identity=read(O/'OWNED_CHILD.json');p=Path('/proc',str(identity['pid']));assert not p.exists()or p.joinpath('stat').read_text().split(') ',1)[1].split()[19]!=identity['start_ticks'];files[str(q.relative_to(R))]=sha(q)
  interface=read(S/'MPPI_RUNTIME_INTERFACE_PROOF.json');q=R/interface['actual_prior_probe_path'];assert sha(q)==interface['actual_prior_probe_sha256']and read(q)['passed'];files[str(q.relative_to(R))]=sha(q)
  for method,rows in plan['methods'].items():
   code=R/'experiments'/transform.VERSIONS[method];old=R/'experiments'/transform.PARENTS[method];same=[]
   for p in code.glob('*.py'):
    ast.parse(p.read_text())
    if p.name in ['reserved_census.py','queue_storage.py']:assert p.read_bytes()==(C/p.name).read_bytes()
    else:assert p.read_text()==transform.transform((old/p.name).read_text(),p.name,method),'UNDECLARED_BODY_CHANGE:'+p.name;same.append(p.name)
   for row in rows:
    O=R/row['root'];task=read(O/'PILOT_TASK.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']==row['task'])
    for k in original:
     if k not in ['task_id','output','run_id','run_root']:assert task[k]==original[k],(method,row['task'],k)
    assert task['task_id']==row['round_id']and task['common_task_id']==row['task']and task['method']==method and task['maximum_control_native']==57600 and task['stop_native']==2200 and task['native_limit']==60000
    assert not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'actual').exists()
    for p in O.glob('*.json'):files[str(p.relative_to(R))]=sha(p)
   cpu=rows[0]['CPU'];env=dict(os.environ,PHASE_COMMON_ASSIGNMENT=rows[0]['round_id'],PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1');p=subprocess.run(['taskset','-c',str(cpu),'/usr/bin/python3','-B',str(code/'run_phase.py')],cwd=R,env=env,capture_output=True,timeout=10);assert p.returncode!=0 and(method+'_INDEPENDENT_PHASE_NOT_ADMITTED').encode()in p.stderr
   ns=load('prospective_'+method+'_readonly_namespace',code/'run_phase.py');scratch=S/('namespace_'+method);scratch.mkdir();cmd=ns.namespace(code/'pilot_entry.py',scratch);i=next(i for i,x in enumerate(cmd)if x.endswith('/envs/mk_mujoco/bin/python'));other=R/plan['methods']['MPPI'if method=='RPP'else'RPP'][0]['root']
   script="from pathlib import Path;import os;assert os.sched_getaffinity(0)=={"+str(cpu)+"};Path("+repr(str(scratch/'PASS'))+").write_text('software')\nfor p in [Path("+repr(str(other/'FORBIDDEN'))+"),Path("+repr(str(code/'FORBIDDEN'))+")]:\n try:p.write_text('forbidden')\n except OSError:pass\n else:raise AssertionError('CROSS_LANE_SOURCE_WRITABLE')"
   p=subprocess.run(['taskset','-c',str(cpu),*cmd[:i],cmd[i],'-B','-c',script],cwd=R,env=env,capture_output=True,timeout=20);assert p.returncode==0,p.stderr.decode()
   # Actual production measurement AST, synthetic du only, both capacities.
   fn=next(x for x in ast.parse((C/'reserved_census.py').read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='measure');own=[0];bad=[False]
   def du(*args,**kw):
    if bad[0]:raise subprocess.CalledProcessError(1,args[0])
    return str(own[0]).encode()
   g=dict(global_admission=lambda **kw:dict(joint_peak_bytes=baseline['joint_peak_bytes']),read=lambda p:baseline if p.name=='QUIESCENT_BASELINE.json'else plan,S=S,R=R,Path=Path,os=os,subprocess=types.SimpleNamespace(check_output=du),MIB=1024**2);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(C/'reserved_census.py'),'exec'),g);os.sched_setaffinity(0,{cpu})
   for value in [0,1,100*1024**2,224*1024**2]:
    own[0]=value;measured,upper=g['measure'](R/rows[0]['root']/'actual',dict(maximum_task_evidence_bytes=224*1024**2));assert measured==value and upper+(224*1024**2-value)+(272+512)*1024**2==baseline['joint_peak_bytes']
   bad[0]=True
   try:g['measure'](R/rows[0]['root']/'actual',dict(maximum_task_evidence_bytes=224*1024**2))
   except subprocess.CalledProcessError:pass
   else:raise AssertionError('LOCAL_DU_ERROR_SILENCED')
   os.sched_setaffinity(0,{5});laneproof.append(dict(method=method,original_cases=len(rows),CPU=cpu,exact_declared_namespace_source_task_only_transform=same,real_unadmitted_CLI_refused=True,namespace_crosslane_source_writes_refused=True,synthetic_capacity_states=4,local_du_errors_fail_closed=True))
  retention=storage_fixture();proof=dict(passed=True,lanes=laneproof,retention_real_function_fixture=retention,original120_tasks_and_all_previous_failures_preserved=True,joint_peak_bytes=baseline['joint_peak_bytes'],no_optimistic_cleanup_credit=True,no_global_live_du=True,MPPI_runtime_interface_reused_exact_original_core_helper=True,zero_old_or_new_numerical_requalification=True,models=0,algorithm_DLLs=0,controller_constructors=0,optimizer_queries=0,physics=0,replay=0);put(S/'SOFTWARE_CHECK_PROOF.json',proof)
  for folder in [C]+[R/'experiments'/v for v in transform.VERSIONS.values()]:
   for p in folder.iterdir():
    if p.is_file():files[str(p.relative_to(R))]=sha(p)
  for p in S.glob('*.json'):
   if p.name!='SOURCE_ONCE.json':files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if inherited.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False));put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:os.sched_setaffinity(0,{5});result['closed']=True;put(S/'SOURCE_QUALIFICATION.json',result);put(S/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())

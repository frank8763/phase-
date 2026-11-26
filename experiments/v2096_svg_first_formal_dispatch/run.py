from pathlib import Path
import hashlib,importlib.util,json,os,signal,subprocess,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;S=R/'runs/v2095_svg_common_full_route';H=R/'experiments/v2095_svg_common_full_route/evidence.py';RID='common_01__SVGMPPI';CASE=S/'rounds'/RID
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<128*1024;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def command(stage,args,cap):
 put(D/'PROGRESS.json',dict(stage=stage,unix=time.time()));p=None;i=None
 try:
  with(D/(stage+'.console')).open('xb')as f:
   p=subprocess.Popen(['taskset','-c','5',*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PHASE_COMMON_ASSIGNMENT=RID,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdout=f,stderr=subprocess.STDOUT,start_new_session=True);i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],stage=stage);put(D/'ACTIVE_STAGE.json',i);return p.wait(timeout=cap)
 finally:
  if p is not None and p.poll()is None:
   assert Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]==i['start_ticks'];os.killpg(i['pgid'],signal.SIGTERM)
   try:p.wait(timeout=20)
   except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(D/'ONCE.json').exists()and not(CASE/'PILOT_ONCE_CLAIM.json').exists()and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];helper=load('SVG_final_case_source_exact_inventory',H);files=helper.read(S/'SOURCE_FREEZE.json')['files'];assert all(helper.sha(R/n)==h for n,h in files.items());ctx=load('SVG_actual_cases_final_storage_gate',R/'experiments/v2095_svg_common_full_route/context.py')
 start=time.monotonic();now=time.time();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();put(D/'ONCE.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],boot_id=boot,unix=now,finite_wait_s=4*7200,one_original_formal_case=True,formal_common_tasks=1));result=dict(closed=False,pipeline_passed=False,component_passed=None,whole_navigation_passed=None,formal_common_tasks=1,component_started=False,first_error=None)
 try:
  ctx.predecessors_closed();assert not(D/'STOP').exists(),'USER_STOP'
  assert all(helper.sha(R/n)==h for n,h in files.items());result['component_started']=True;result['owner_returncode']=command('owner',['/usr/bin/python3','-B',str(R/'experiments/v2095_svg_common_full_route/owner.py')],5425);assert read(CASE/'COMPLETION.json')['closed']
  for stage,args,cap in [('archive',['archive',RID],120),('ref',['ref',RID],15),('remote',['deliver',RID],620)]:assert command(stage,['/usr/bin/python3','-B',str(H),*args],cap)==0,'SVG_COMPONENT_EVIDENCE_STAGE_FAILED:'+stage
  T=S/'runtime_archives'/RID;assert read(T/'FULL_REMOTE_VERIFIED.json')['passed']and read(T/'TRANSPORT_CLEANUP.json')['passed'];x=read(CASE/'COMPLETION.json');paths=[CASE/'COMPLETION.json',T/'ARCHIVE_INDEX.json',T/'FULL_REMOTE_VERIFIED.json',T/'TRANSPORT_CLEANUP.json'];machine=CASE/'actual/RESULT.json'
  if machine.exists():paths.append(machine)
  put(CASE/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,formal_task_passed=x['passed'],whole_navigation_passed=x['whole_navigation_passed'],formal_common_tasks=1,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},all_originals_retained=True,models_authorized=False));result.update(pipeline_passed=True,formal_task_passed=x['passed'],whole_navigation_passed=x['whole_navigation_passed'])
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(D/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())

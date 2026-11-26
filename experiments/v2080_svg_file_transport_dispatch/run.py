from pathlib import Path
import hashlib,importlib.util,json,os,signal,subprocess,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;S=R/'runs/v2079_svg_file_bound_transport';H=R/'experiments/v2079_svg_file_bound_transport/evidence.py';RID='svg_vehicle_stop'
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
   p=subprocess.Popen(['taskset','-c','5',*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdout=f,stderr=subprocess.STDOUT,start_new_session=True);i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],stage=stage);put(D/'ACTIVE_STAGE.json',i);return p.wait(timeout=cap)
 finally:
  if p is not None and p.poll()is None:
   assert Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]==i['start_ticks'];os.killpg(i['pgid'],signal.SIGTERM)
   try:p.wait(timeout=20)
   except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(D/'ONCE.json').exists()and not(S/'PILOT_ONCE_CLAIM.json').exists()and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];helper=load('SVG_final_case_source_exact_inventory',H);files=helper.read(S/'SOURCE_FREEZE.json')['files'];assert all(helper.sha(R/n)==h for n,h in files.items());ctx=load('SVG_actual_cases_final_storage_gate',R/'experiments/v2079_svg_file_bound_transport/context.py')
 start=time.monotonic();now=time.time();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();put(D/'ONCE.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],boot_id=boot,unix=now,finite_wait_s=4*7200,one_original_vehicle_component=True,formal_common_tasks=0));result=dict(closed=False,pipeline_passed=False,component_passed=None,whole_navigation_passed=False,formal_common_tasks=0,component_started=False,first_error=None)
 try:
  checkpoint=0
  while True:
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.monotonic()-start<4*7200 and time.time()-now<4*7200,'SVG_WAIT_BOOT_OR_TECHNICAL_STOP';assert not(D/'STOP').exists(),'USER_STOP'
   try:
    if ctx.queue_closed():break
   except FileNotFoundError:pass
   except BlockingIOError:pass
   except AssertionError as e:
    assert str(e)in{'PRIOR_CASE_EVIDENCE_BARRIER_PENDING','PRIOR_NUMERICAL_OWNER_STILL_LIVE','FINAL_CASE_QUIESCENT_RETIREMENT_PENDING','FINAL_CASE_STORAGE_STATE_PENDING'},'FATAL_CASE_GATE:'+str(e)
   if time.monotonic()-checkpoint>=900:
    roots=R/'runs/v2045_remaining_parallel_source/rounds';state=[]
    for n in range(3,13):
     o=roots/f'common_{n:02d}__MPPI';state.append(dict(round=o.name,actual_closed=(o/'COMPLETION.json').exists(),barrier_closed=(o/'POST_ROUND_STORAGE_BARRIER.json').exists()))
    put(D/'PROGRESS.json',dict(stage='WAIT_CANONICAL_CASE_BARRIERS_AND_FINAL_QUIESCENT_STORAGE',cases=state,unix=time.time(),models_started=False));checkpoint=time.monotonic()
   time.sleep(15)
  assert all(helper.sha(R/n)==h for n,h in files.items());result['component_started']=True;result['owner_returncode']=command('owner',['/usr/bin/python3','-B',str(R/'experiments/v2079_svg_file_bound_transport/owner.py')],5425);assert read(S/'COMPLETION.json')['closed']
  for stage,args,cap in [('archive',['archive',RID],120),('ref',['ref',RID],15),('remote',['deliver',RID],620)]:assert command(stage,['/usr/bin/python3','-B',str(H),*args],cap)==0,'SVG_COMPONENT_EVIDENCE_STAGE_FAILED:'+stage
  T=S/'runtime_archives'/RID;assert read(T/'FULL_REMOTE_VERIFIED.json')['passed']and read(T/'TRANSPORT_CLEANUP.json')['passed'];x=read(S/'COMPLETION.json');paths=[S/'COMPLETION.json',T/'ARCHIVE_INDEX.json',T/'FULL_REMOTE_VERIFIED.json',T/'TRANSPORT_CLEANUP.json'];machine=S/'actual/RESULT.json'
  if machine.exists():paths.append(machine)
  put(S/'POST_COMPONENT_STORAGE_BARRIER.json',dict(passed=True,component_passed=x['passed'],whole_navigation_passed=False,formal_common_tasks=0,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},all_originals_retained=True,models_authorized=False));result.update(pipeline_passed=True,component_passed=x['passed'])
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(D/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())

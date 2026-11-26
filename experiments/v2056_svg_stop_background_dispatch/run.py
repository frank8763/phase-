"""Finite background sequencing of an already source-qualified SVG component."""
from pathlib import Path
import hashlib,importlib.util,json,os,signal,subprocess,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;S=R/'runs/v2055_svg_vehicle_stop_component';H=R/'experiments/v2055_svg_vehicle_stop_component/evidence.py';RID='svg_vehicle_stop'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<=128*1024;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
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
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(D/'ONCE.json').exists()and not(S/'PILOT_ONCE_CLAIM.json').exists()and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];helper=load('SVG_source_exact_inventory',H);files=helper.read(S/'SOURCE_FREEZE.json')['files'];assert all(helper.sha(R/n)==h for n,h in files.items())
 start=time.monotonic();now=time.time();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();put(D/'ONCE.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],boot_id=boot,unix=now,finite_wait_s=7*7200,one_component_only=True,formal_common_tasks=0));result=dict(closed=False,pipeline_passed=False,component_passed=None,whole_navigation_passed=False,formal_common_tasks=0,first_error=None,component_started=False)
 try:
  checkpoint=0
  while True:
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.monotonic()-start<7*7200 and time.time()-now<7*7200,'SVG_WAIT_BOOT_OR_TECHNICAL_STOP';assert not(D/'STOP').exists(),'USER_STOP'
   prior=R/'runs/v2051_mppi_remaining_seven_resume/RESULT.json'
   if prior.exists():
    x=read(prior);assert x['closed']and x['pipeline_passed'],'MPPI_QUEUE_FAILED_NO_NEW_MODEL';break
   owner=read(S/'WAIT_QUEUE_OWNER_BINDING.json');p=Path('/proc',str(owner['campaign_pid']),'stat');assert p.exists()and p.read_text().split(') ',1)[1].split()[19]==owner['campaign_start_ticks'],'MPPI_QUEUE_OWNER_MISSING_OR_CHANGED_NO_NEW_MODEL'
   if time.monotonic()-checkpoint>=900:
    put(D/'PROGRESS.json',dict(stage='WAIT_MPPI_HEALTHY_CLOSED_BARRIERS',MPPI_progress=read(R/'runs/v2051_mppi_remaining_seven_resume/PROGRESS.json'),unix=time.time(),models_started=False));checkpoint=time.monotonic()
   time.sleep(15)
  assert all(helper.sha(R/n)==h for n,h in files.items());result['component_started']=True;result['owner_returncode']=command('owner',['/usr/bin/python3','-B',str(R/'experiments/v2055_svg_vehicle_stop_component/owner.py')],5425);assert read(S/'COMPLETION.json')['closed']
  for stage,args,cap in [('archive',['archive',RID],120),('ref',['ref',RID],15),('remote',['deliver',RID],620)]:assert command(stage,['/usr/bin/python3','-B',str(H),*args],cap)==0,'SVG_COMPONENT_EVIDENCE_STAGE_FAILED:'+stage
  T=S/'runtime_archives'/RID;assert read(T/'FULL_REMOTE_VERIFIED.json')['passed']and read(T/'TRANSPORT_CLEANUP.json')['passed'];x=read(S/'COMPLETION.json');paths=[S/'COMPLETION.json',T/'ARCHIVE_INDEX.json',T/'FULL_REMOTE_VERIFIED.json',T/'TRANSPORT_CLEANUP.json'];machine=S/'actual/RESULT.json'
  if machine.exists():paths.append(machine)
  put(S/'POST_COMPONENT_STORAGE_BARRIER.json',dict(passed=True,component_passed=x['passed'],whole_navigation_passed=False,formal_common_tasks=0,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},all_originals_retained=True,models_authorized=False));result.update(pipeline_passed=True,component_passed=x['passed'])
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(D/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())

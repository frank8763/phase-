"""Finite detached CPU4/6 components while the existing CPU2/7 queue runs."""
from pathlib import Path
import concurrent.futures,fcntl,json,os,signal,subprocess,time,traceback
from common import R,C,S,read,put,sha
def worker(label,cpu,cap):
 import namespace
 script=C/('worker_filters.py'if label=='filters'else'worker_priest.py');out=S/label;argv=namespace.command(script,out)
 with(S/(label+'.console')).open('xb')as log:
  p=subprocess.Popen(['taskset','-c',str(cpu),'nice','-n','19',*argv],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  identity=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],cpu=cpu,boot_id=BOOT);put(S/(label+'_IDENTITY.json'),identity);start=time.monotonic()
  try:
   while p.poll()is None:
    assert time.monotonic()-start<cap and time.time()<END and time.monotonic()<MONO_END and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT
    assert not(S/'STOP').exists()and(S/(label+'.console')).stat().st_size<=1024**2
    time.sleep(.2)
   return dict(returncode=p.returncode,result=read(out/'RESULT.json')if(out/'RESULT.json').exists()else None)
  except BaseException as x:return dict(error=repr(x),traceback=traceback.format_exc(),result=read(out/'RESULT.json')if(out/'RESULT.json').exists()else None)
  finally:
   if p.poll()is None:
    assert Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]==identity['start_ticks'];os.killpg(identity['pgid'],signal.SIGTERM)
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);p.wait(timeout=5)
def stage(name,args,cap):
 with(S/(name+'.console')).open('xb')as log:
  p=subprocess.run(['/usr/bin/python3','-B',str(C/'evidence.py'),*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,timeout=cap)
 return p.returncode
def main():
 global END,MONO_END,BOOT
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));lock=(S/'owner.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(S/'ONCE.json').exists()and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
 files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());auth=read(S/'AUTHORIZATION.json')
 BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip();END=min(time.time()+1050,auth['absolute_end_unix']-650);MONO_END=time.monotonic()+END-time.time()
 assert END-time.time()>900;put(S/'ONCE.json',dict(pid=os.getpid(),boot_id=BOOT,unix=time.time(),maximum_component_s=1050,models_authorized=False))
 for kind in ['filters','priest']:(S/kind).mkdir(exist_ok=False)
 put(S/'COMPONENT_ADMISSION.json',dict(scope='EXPLICIT_NON_PHASE_IMPLEMENTATION_COMPONENTS',models_authorized=False,source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),absolute_end_unix=END,hard_stop_monotonic=MONO_END,boot_id=BOOT))
 outputs={};error=None
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
   pending={k:pool.submit(worker,k,cpu,cap)for k,cpu,cap in [('filters',6,920),('priest',4,120)]}
   for k,v in pending.items():outputs[k]=v.result()
 except BaseException as x:error=dict(error=repr(x),traceback=traceback.format_exc())
 passed=error is None and len(outputs)==2 and all(x.get('returncode')==0 and x.get('result',{}).get('all_frozen_source_SHA_after')for x in outputs.values())
 put(S/'COMPLETION.json',dict(closed=True,passed=passed,components=outputs,error=error,models=0,physics=0,replay=0,new_formal_tasks=0,not_Phase_vehicle_qualified=True))
 result=dict(closed=True,finite_component_pipeline_passed=False,numerical_completion=passed,models=0,new_formal_tasks=0)
 try:
  assert stage('runtime_archive',['archive','components'],120)==0
  assert stage('runtime_ref',['ref','components'],15)==0
  assert stage('runtime_delivery',['deliver','components'],620)==0
  T=S/'runtime_archives/components';assert read(T/'FULL_REMOTE_VERIFIED.json')['passed']and read(T/'TRANSPORT_CLEANUP.json')['passed']
  put(S/'POST_COMPONENT_STORAGE_BARRIER.json',dict(passed=True,full_remote_SHA=True,source_commit=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit'],no_physical_admission=True,runtime_proof_sha256=sha(T/'FULL_REMOTE_VERIFIED.json')))
  result.update(finite_component_pipeline_passed=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 put(S/'PIPELINE_RESULT.json',result);print(json.dumps(result))
if __name__=='__main__':main()

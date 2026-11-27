"""Bounded detached software/ideal-NLP lane, never an additional vehicle owner."""
import os,fcntl,time,signal,subprocess,json,traceback
from common import R,C,S,read,put,sha

def stage(label,args,cap):
 with(S/(label+'.console')).open('xb')as f:return subprocess.run(['/usr/bin/python3','-B',str(C/'evidence.py'),*args],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=cap).returncode

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));lock=(S/'owner.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(S/'ONCE.json').exists()and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
 from reservation import admission
 admission();auth=read(S/'AUTHORIZATION.json');boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip();end=min(time.time()+1000,auth['absolute_end_unix']-650);mono=time.monotonic()+end-time.time();assert end-time.time()>900
 put(S/'ONCE.json',dict(pid=os.getpid(),unix=time.time(),models_authorized=False));put(S/'COMPONENT_ADMISSION.json',dict(scope=auth['scope'],models_authorized=False,source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),boot_id=boot,absolute_end_unix=end,hard_stop_monotonic=mono));(S/'math').mkdir()
 from namespace import command
 result=None;error=None;p=None
 try:
  with(S/'math.console').open('xb')as f:
   p=subprocess.Popen(['taskset','-c','6','nice','-n','19',*command(C/'worker.py',S/'math')],cwd=R,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1'),stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
   from pathlib import Path
   ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19];put(S/'WORKER_IDENTITY.json',dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=ticks,boot_id=boot,cpu=6));start=time.monotonic()
   while p.poll()is None:
    assert time.monotonic()-start<920 and time.time()<end and time.monotonic()<mono and not(S/'STOP').exists()and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot
    admission();time.sleep(.2)
   result=read(S/'math/RESULT.json')if(S/'math/RESULT.json').exists()else None;assert p.returncode==0 and result['all_frozen_source_SHA_after']
 except BaseException as x:error=dict(error=repr(x),traceback=traceback.format_exc())
 finally:
  if p is not None and p.poll()is None:
   assert Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]==ticks;os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
 put(S/'COMPLETION.json',dict(closed=True,passed=error is None,error=error,component=result,models=0,physics=0,replay=0,new_formal_tasks=0,not_Phase_vehicle_qualified=True))
 value=dict(closed=True,finite_component_pipeline_passed=False,scientific_navigation_passed=None,models=0,new_formal_tasks=0)
 try:
  assert stage('runtime_archive',['archive','components'],120)==0;assert stage('runtime_ref',['ref','components'],15)==0;assert stage('runtime_delivery',['deliver','components'],620)==0
  D=S/'runtime_archives/components';assert read(D/'FULL_REMOTE_VERIFIED.json')['passed']and read(D/'TRANSPORT_CLEANUP.json')['passed']
  put(S/'POST_COMPONENT_STORAGE_BARRIER.json',dict(passed=True,runtime_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),full_remote_SHA=True,no_physical_admission=True));value['finite_component_pipeline_passed']=True
 except BaseException as x:value.update(error=repr(x),traceback=traceback.format_exc())
 put(S/'PIPELINE_RESULT.json',value);print(json.dumps(value))
if __name__=='__main__':main()

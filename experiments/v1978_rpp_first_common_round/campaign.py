"""Detached one-round pipeline; no Codex heartbeat or automatic successor."""
import hashlib,json,os,signal,subprocess,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;D=R/'experiments/v1980_rpp_common_runtime_recovery'
read=lambda p:json.loads(p.read_text())
def put(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(O/'BACKGROUND_ONCE_CLAIM.json').exists()and not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'COMPLETION.json').exists()
 assert read(O/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
 start=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split()
 with(O/'BACKGROUND_ONCE_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),pgid=os.getpgid(0),start_ticks=stat[19],boot_id=boot,started_unix=time.time(),pipeline_technical_cap_s=7200,first_case_only=True,automatic_successor=False),f)
 process=None;result=dict(closed=False,pipeline_passed=False,scientific_navigation_passed=None,first_error=None,stages=[])
 def alarm(*a):raise TimeoutError('ONE_ROUND_PIPELINE_TECHNICAL_CAP')
 signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,7200)
 try:
  stages=[('OWNER',C/'owner.py',[]),('REVIEW',D/'review.py',[]),('ARCHIVE',D/'finalize.py',[]),('REF_ONLY',D/'deliver.py',['--source-sync']),('REMOTE',D/'deliver.py',[]),('BARRIER',D/'review.py',['--barrier'])]
  for name,path,args in stages:
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.monotonic()-start<7200
   with(O/('pipeline_'+name.lower()+'.console')).open('xb')as log:
    process=subprocess.Popen(['/usr/bin/python3','-B',str(path),*args],cwd=R,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES=''))
    put(O/'BACKGROUND_STAGE.json',dict(stage=name,pid=process.pid,unix=time.time(),models_authorized=name=='OWNER'))
    code=process.wait()
   result['stages'].append(dict(stage=name,returncode=code))
   if name=='OWNER':assert read(O/'COMPLETION.json')['closed']and read(O/'COMPLETION.json')['review_restored']and read(O/'COMPLETION.json')['lock_idle']
   else:assert code==0,'PIPELINE_STAGE_FAILED:'+name
   process=None
  result.update(pipeline_passed=True,scientific_navigation_passed=read(O/'RUNTIME_CLOSED_REVIEW.json')['qualified_whole_navigation_passed'])
 except BaseException as e:
  result['first_error']=dict(error=repr(e),traceback=traceback.format_exc())
  # Only our identity-bound physical group is terminated on pipeline anomaly.
  p=O/'OWNED_CHILD.json'
  if p.exists():
   identity=read(p);stat=Path('/proc',str(identity['pid']),'stat')
   if stat.exists()and stat.read_text().split(') ',1)[1].split()[19]==identity['start_ticks']and identity['boot_id']==boot:
    os.killpg(identity['pgid'],signal.SIGTERM)
  if process is not None and process.poll()is None:
   try:process.wait(timeout=30)
   except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-start,automatic_successor=False);put(O/'BACKGROUND_RESULT.json',result)
 print(json.dumps(result),flush=True);return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())

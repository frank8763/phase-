"""CPU2+6 current vehicle and CPU4 nonlinear filters, simultaneous bounded jobs."""
import concurrent.futures,os,subprocess,time,json,selectors,signal,traceback
from pathlib import Path
from context import R,C,SOURCE,O,read,put,sha,load,predecessors_closed

def stop_nested_vehicle():
 p=O/'OWNED_CHILD.json'
 if not p.exists():return
 i=read(p);f=Path('/proc',str(i['pid']),'stat')
 if not f.exists()or f.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']:return
 assert i['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and os.getpgid(i['pid'])==i['pgid']
 os.killpg(i['pgid'],signal.SIGTERM)
 end=time.monotonic()+20
 while f.exists()and time.monotonic()<end:time.sleep(.1)
 if f.exists()and f.read_text().split(') ',1)[1].split()[19]==i['start_ticks']:os.killpg(i['pgid'],signal.SIGKILL)

def worker(kind):
 out=SOURCE/'filter_output';cpu=4 if kind=='FILTERS'else 5;start=time.monotonic();p=None;i=None;total=0;answer=dict(closed=False,passed=False,kind=kind,models=None if kind=='VEHICLE'else 0)
 env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 cmd=[str(C/'owner.py')]if kind=='VEHICLE'else load('FILTER_only_output_namespace',C/'filter_namespace.py').command(C/'filter_worker.py',out)
 if kind=='VEHICLE':cmd=['/usr/bin/python3','-B',*cmd]
 try:
  p=subprocess.Popen(['taskset','-c',str(cpu),'nice','-n','19','ionice','-c','3',*cmd],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],CPU=cpu);put(SOURCE/(kind+'_OWNED_CHILD.json'),i);sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
  with(SOURCE/(kind+'.console')).open('xb')as log:
   while sel.get_map():
    assert time.monotonic()-start<(5425 if kind=='VEHICLE'else 180),'PARALLEL_COMPONENT_WALL_STOP'
    if kind=='FILTERS':assert sum(x.stat().st_blocks*512 for x in out.rglob('*')if x.is_file())<=1024**2
    for key,_ in sel.select(.2):
     data=os.read(key.fileobj.fileno(),16384)
     if not data:sel.unregister(key.fileobj);continue
     total+=len(data);assert total<=128*1024,'PARALLEL_OWNER_CONSOLE_CAP';log.write(data);log.flush()
  p.wait(timeout=5);machine=O/'COMPLETION.json'if kind=='VEHICLE'else out/'RESULT.json';m=read(machine);answer.update(passed=p.returncode==0 and m['passed'],returncode=p.returncode,machine_result_path=str(machine.relative_to(R)),machine_result_sha256=sha(machine),machine_passed=m['passed'])
 except BaseException as e:answer.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if p is not None and p.poll()is None:
   assert Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19]==i['start_ticks'];os.killpg(i['pgid'],signal.SIGTERM)
   try:p.wait(timeout=20)
   except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
  if kind=='VEHICLE':stop_nested_vehicle()
  answer.update(closed=True,wall_s=time.monotonic()-start);put(SOURCE/(kind+'_PARALLEL_COMPLETION.json'),answer)
 return answer

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(SOURCE/'PARALLEL_ONCE.json').exists()and not(O/'PILOT_ONCE_CLAIM.json').exists()and not(SOURCE/'filter_output/ONCE.json').exists();assert read(SOURCE/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];predecessors_closed()
 source=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in source.items())
 now=time.time();mono=time.monotonic();put(SOURCE/'PARALLEL_ONCE.json',dict(pid=os.getpid(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),unix=now,vehicle_component=True,formal_trials=0,vehicleCPU=2,PRIEST_CPU=6,filterCPU=4,ownerCPU=5));put(SOURCE/'FILTERS_ADMISSION.json',dict(scope='PSF_PCBF_NONLINEAR_SOLVER_COMPONENT',models_authorized=False,source_freeze_sha256=sha(SOURCE/'SOURCE_FREEZE.json'),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=now+170,hard_stop_monotonic=mono+170))
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  jobs={k:pool.submit(worker,k)for k in ['VEHICLE','FILTERS']};results={k:v.result()for k,v in jobs.items()}
 result=dict(closed=True,passed=all(x['passed']for x in results.values()),components=results,formal_trials=0,whole_navigation_passed=False,all_source_SHA_after=all(sha(R/n)==h for n,h in source.items()),wall_s=time.monotonic()-mono);put(SOURCE/'COMPLETION.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())

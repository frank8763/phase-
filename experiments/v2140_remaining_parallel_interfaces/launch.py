"""Detached bounded concurrent SOFTWARE workers; no automatic method trials."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
def put(p,z):
 assert not p.exists();p.write_text(json.dumps(z,indent=2)+'\n')
def identity(p,cpu):return dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=BOOT,CPU=cpu)
def gone(i):
 p=Path('/proc',str(i['pid']),'stat');return not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
def main():
 global BOOT
 assert os.sched_getaffinity(0)=={5};S.mkdir(exist_ok=True);assert not(S/'ONCE.json').exists();BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip();put(S/'ONCE.json',dict(pid=os.getpid(),boot_id=BOOT,unix=time.time(),scope='THREE_CONCURRENT_SOFTWARE_PREPARATIONS',models_authorized=False));workers=[];start=time.monotonic();result=dict(closed=False,method_results={})
 try:
  for method,cpu in [('PSF',0),('SCCR',1),('PRIEST',3)]:
   log=(S/(method+'.console')).open('xb');p=subprocess.Popen(['taskset','-c',str(cpu),'nice','-n','19','ionice','-c','3','/usr/bin/python3','-B',str(C/'work.py'),method],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);i=identity(p,cpu);put(S/(method+'.IDENTITY.json'),i);workers.append((method,p,i,log))
  while any(p.poll()is None for _,p,_,_ in workers):
   assert time.monotonic()-start<120 and not(S/'STOP').exists()and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT
   assert sum(p.stat().st_blocks*512 for p in S.rglob('*')if p.is_file())<=1024**2;time.sleep(.2)
  for method,p,i,log in workers:
   path=S/method/'RESULT.json';r=json.loads(path.read_text())if path.exists()else dict(passed=False,error='WORKER_RESULT_MISSING');result['method_results'][method]=dict(returncode=p.returncode,passed=r['passed'],result_path=str(path.relative_to(R)),scope=r.get('scope'),initial_geometry_feasible=r.get('initial_geometry_feasible'))
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
 finally:
  for method,p,i,log in workers:
   if p.poll()is None:
    assert not gone(i);os.killpg(i['pgid'],signal.SIGTERM)
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
   log.close()
 result.update(closed=True,wall_s=time.monotonic()-start,models=0,optimizer_calls=0,physics=0,replay=0,formal_tasks=0,all_owned_workers_exited=all(gone(i)for _,_,i,_ in workers),original_physical_owner_untouched=True);put(S/'RESULT.json',result);print(json.dumps(result))
if __name__=='__main__':main()
